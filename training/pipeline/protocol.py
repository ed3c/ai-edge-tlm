from __future__ import annotations
from dataclasses import dataclass, asdict
from enum import StrEnum
import hashlib, json, random
from typing import Mapping, Sequence

class ProtocolError(RuntimeError): pass
class LeakageError(ProtocolError): pass
class IdentityError(ProtocolError): pass
class ReceiptError(ProtocolError): pass

@dataclass(frozen=True,slots=True)
class Identity:
    kind:str; name:str; revision:str; digest:str
    def __post_init__(self):
        if not self.kind or not self.name or not self.revision or len(self.digest)<8: raise IdentityError("incomplete identity")

@dataclass(frozen=True,slots=True)
class SyntheticExample:
    example_id:str; utterance:str; function_name:str; arguments:Mapping[str,object]; language:str; noise_tag:str; template_revision:str; teacher_identity:Identity
    def canonical_digest(self)->str:
        return hashlib.sha256(json.dumps({"id":self.example_id,"utterance":self.utterance,"function":self.function_name,"arguments":self.arguments,"language":self.language,"noise":self.noise_tag,"template_revision":self.template_revision,"teacher":asdict(self.teacher_identity)},sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

@dataclass(frozen=True,slots=True)
class DatasetSplit:
    train:tuple[SyntheticExample,...]; eval:tuple[SyntheticExample,...]; lineage_digest:str

class SyntheticDatasetBuilder:
    def __init__(self,*,template_revision:str,teacher_identity:Identity,seed:int):
        if not template_revision: raise ValueError("template revision required")
        self.template_revision=template_revision; self.teacher_identity=teacher_identity; self.seed=seed
    def build(self,intents:Sequence[tuple[str,Mapping[str,object]]],variants:Sequence[str])->tuple[SyntheticExample,...]:
        rng=random.Random(self.seed); rows=[]
        for index,(fn,args) in enumerate(intents):
            for variant in variants:
                utterance=variant.format(function=fn,**{k:str(v) for k,v in args.items()})
                rows.append(SyntheticExample(f"syn-{index:03d}-{hashlib.sha256(utterance.encode()).hexdigest()[:10]}",utterance,fn,dict(args),"en","synthetic",self.template_revision,self.teacher_identity))
        rng.shuffle(rows); return tuple(rows)
    def split(self,rows:Sequence[SyntheticExample],*,eval_fraction:float=.25)->DatasetSplit:
        if not 0<eval_fraction<1: raise ValueError("invalid eval fraction")
        ordered=sorted(rows,key=lambda r:hashlib.sha256(f"{self.seed}|{r.example_id}".encode()).hexdigest()); cut=max(1,int(round(len(ordered)*(1-eval_fraction))))
        train=tuple(ordered[:cut]); evaluation=tuple(ordered[cut:]); detect_leakage(train,evaluation)
        return DatasetSplit(train,evaluation,hashlib.sha256("|".join(r.canonical_digest() for r in ordered).encode()).hexdigest())

def normalize(value:str)->str:return " ".join(value.casefold().split())
def detect_leakage(train,evaluation):
    if {r.example_id for r in train}&{r.example_id for r in evaluation}: raise LeakageError("example id leakage")
    if {normalize(r.utterance) for r in train}&{normalize(r.utterance) for r in evaluation}: raise LeakageError("utterance leakage")

class PredictionStage(StrEnum): BASELINE="BASELINE"; SOURCE_SFT="SOURCE_SFT"; CONVERTED="CONVERTED"; DEVICE="DEVICE"
@dataclass(frozen=True,slots=True)
class PredictionRecord:
    example_id:str; function_name:str|None; arguments:Mapping[str,object]|None; valid_json:bool; schema_valid:bool; stage:PredictionStage; model_identity:Identity; runtime_identity:Identity|None=None
@dataclass(frozen=True,slots=True)
class FunctionMetrics:
    function_name:str; total:int; correct:int; invalid_json:int; invalid_schema:int
    @property
    def accuracy(self):return 0.0 if self.total==0 else self.correct/self.total
@dataclass(frozen=True,slots=True)
class EvaluationReport:
    stage:PredictionStage; per_function:tuple[FunctionMetrics,...]; total:int; correct:int; invalid_json:int; invalid_schema:int; model_identity:Identity
    @property
    def accuracy(self):return 0.0 if self.total==0 else self.correct/self.total

def evaluate(expected,predictions):
    if len(expected)!=len(predictions): raise ProtocolError("prediction cardinality mismatch")
    by_id={p.example_id:p for p in predictions}; stages={p.stage for p in predictions}; models={p.model_identity for p in predictions}
    if len(stages)!=1 or len(models)!=1: raise IdentityError("mixed stage/model identities")
    stats={};total=correct=bad_json=bad_schema=0
    for row in expected:
        p=by_id.get(row.example_id)
        if not p: raise ProtocolError("missing prediction")
        total+=1; s=stats.setdefault(row.function_name,[0,0,0,0]);s[0]+=1
        if not p.valid_json: bad_json+=1;s[2]+=1;continue
        if not p.schema_valid: bad_schema+=1;s[3]+=1;continue
        if p.function_name==row.function_name and dict(p.arguments or {})==dict(row.arguments): correct+=1;s[1]+=1
    return EvaluationReport(next(iter(stages)),tuple(FunctionMetrics(k,*v) for k,v in sorted(stats.items())),total,correct,bad_json,bad_schema,next(iter(models)))

@dataclass(frozen=True,slots=True)
class ConversionParityReceipt:
    source_model:Identity; converted_model:Identity; compared:int; matched:int; threshold:float; state:str

def conversion_parity(source,converted,*,threshold:float):
    if len(source)!=len(converted) or not source: raise ProtocolError("parity cardinality")
    sm={p.model_identity for p in source};cm={p.model_identity for p in converted}
    if len(sm)!=1 or len(cm)!=1: raise IdentityError("mixed model identity")
    by_id={p.example_id:p for p in converted};matched=0
    for s in source:
        c=by_id.get(s.example_id)
        if not c: raise ProtocolError("missing converted prediction")
        if (s.function_name,dict(s.arguments or {}),s.valid_json,s.schema_valid)==(c.function_name,dict(c.arguments or {}),c.valid_json,c.schema_valid):matched+=1
    return ConversionParityReceipt(next(iter(sm)),next(iter(cm)),len(source),matched,threshold,"PASS" if matched/len(source)>=threshold else "FAIL")

REQUIRED_DEVICE_FIELDS={"commit_sha","tree_sha","device_model","os_build","runtime_id","runtime_revision","model_sha256","tokenizer_sha256","quantization","requested_backend","observed_backend","ttft_ms","prefill_tps","decode_tps","peak_rss_mb","energy_sample","thermal_sample","fixture_digest"}
def validate_device_receipt(value):
    missing=sorted(REQUIRED_DEVICE_FIELDS-set(value))
    if missing: raise ReceiptError(f"missing device receipt fields: {missing}")
    for key in ("commit_sha","tree_sha","model_sha256","tokenizer_sha256","fixture_digest"):
        if not isinstance(value[key],str) or len(value[key])<40: raise ReceiptError(f"invalid {key}")
    if value["observed_backend"] not in {"CPU","GPU","NPU","ANE"}: raise ReceiptError("invalid observed backend")
    if value.get("result_origin")=="SOURCE_BENCHMARK": raise ReceiptError("source benchmark cannot be stored as local device result")

def assert_public_fixture(value:str):
    lowered=value.casefold(); forbidden=("docs"+".google.com","drive"+".google.com","@"+"gmail.com","access_"+"token","api_"+"key","private_"+"key","bearer ")
    if any(token in lowered for token in forbidden): raise ProtocolError("private/user/secret material in public fixture")
