import pytest
from training.pipeline.protocol import *
TEACHER=Identity("service","teacher","2026-08","digest-teacher");MODEL_A=Identity("model","tiny","base","digest-model-a");MODEL_B=Identity("model","tiny","converted","digest-model-b")
def rows():
    b=SyntheticDatasetBuilder(template_revision="tmpl-v1",teacher_identity=TEACHER,seed=7);data=b.build([("add_event",{"title":"demo"}),("open_map",{"query":"cafe"})],["please {function}","run {function}"]);return b,data

def test_synthetic_pipeline_is_deterministic_and_split_lineage_stable():
    b,a=rows();b2,a2=rows();assert [r.canonical_digest() for r in a]==[r.canonical_digest() for r in a2];assert b.split(a).lineage_digest==b2.split(a2).lineage_digest

def test_leakage_detector_rejects_id_and_normalized_text_overlap():
    b,a=rows();r=a[0]
    with pytest.raises(LeakageError):detect_leakage([r],[r])
    clone=SyntheticExample("other",f"  {r.utterance.upper()}  ",r.function_name,r.arguments,r.language,r.noise_tag,r.template_revision,r.teacher_identity)
    with pytest.raises(LeakageError):detect_leakage([r],[clone])

def test_per_function_metrics_count_invalid_json_and_schema():
    b,a=rows();expected=a[:3];preds=[PredictionRecord(expected[0].example_id,expected[0].function_name,expected[0].arguments,True,True,PredictionStage.BASELINE,MODEL_A),PredictionRecord(expected[1].example_id,None,None,False,False,PredictionStage.BASELINE,MODEL_A),PredictionRecord(expected[2].example_id,expected[2].function_name,{},True,False,PredictionStage.BASELINE,MODEL_A)];r=evaluate(expected,preds);assert (r.total,r.correct,r.invalid_json,r.invalid_schema)==(3,1,1,1)

def test_mixed_model_identity_is_rejected():
    b,a=rows();e=a[:2];p=[PredictionRecord(e[0].example_id,e[0].function_name,e[0].arguments,True,True,PredictionStage.BASELINE,MODEL_A),PredictionRecord(e[1].example_id,e[1].function_name,e[1].arguments,True,True,PredictionStage.BASELINE,MODEL_B)]
    with pytest.raises(IdentityError):evaluate(e,p)

def test_conversion_parity_threshold_has_typed_pass_fail():
    b,a=rows();e=a[:2];s=[PredictionRecord(r.example_id,r.function_name,r.arguments,True,True,PredictionStage.SOURCE_SFT,MODEL_A) for r in e];c=[PredictionRecord(r.example_id,r.function_name,r.arguments,True,True,PredictionStage.CONVERTED,MODEL_B) for r in e];assert conversion_parity(s,c,threshold=1).state=="PASS";c[1]=PredictionRecord(e[1].example_id,None,None,False,False,PredictionStage.CONVERTED,MODEL_B);assert conversion_parity(s,c,threshold=1).state=="FAIL"

def test_device_receipt_requires_exact_identity_and_observed_backend():
    v={k:"x"*64 for k in REQUIRED_DEVICE_FIELDS};v.update({"observed_backend":"GPU","requested_backend":"NPU","ttft_ms":10,"prefill_tps":100,"decode_tps":30,"peak_rss_mb":500,"energy_sample":"sample","thermal_sample":"sample","device_model":"pixel","os_build":"build","runtime_id":"litert-lm","runtime_revision":"r","quantization":"int4"});validate_device_receipt(v);b=dict(v);b.pop("observed_backend")
    with pytest.raises(ReceiptError):validate_device_receipt(b)
    s=dict(v);s["result_origin"]="SOURCE_BENCHMARK"
    with pytest.raises(ReceiptError):validate_device_receipt(s)

def test_public_fixture_rejects_private_or_secret_material():
    assert_public_fixture('{"utterance":"synthetic only"}')
    with pytest.raises(ProtocolError):assert_public_fixture('access_'+'token=secret')
    with pytest.raises(ProtocolError):assert_public_fixture('https://'+'docs'+'.google.com/document/d/private')
