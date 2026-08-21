from __future__ import annotations
from dataclasses import dataclass
import json
import re
from pathlib import Path
from typing import Iterable

_HEX40 = re.compile(r"^[0-9a-f]{40}$")
class ConvergenceError(RuntimeError): pass
class CollisionError(ConvergenceError): pass
class ReceiptError(ConvergenceError): pass
@dataclass(frozen=True, slots=True)
class BlobRef:
    source_id: str; head: str; path: str; blob: str
class ExactInputLedger:
    def __init__(self, value: dict): self.value = value
    @classmethod
    def read(cls, path: Path) -> "ExactInputLedger": return cls(json.loads(path.read_text(encoding="utf-8")))
    def validate(self) -> None:
        if self.value.get("schema") != "ai-edge-tlm/p8-exact-input-index/v1": raise ReceiptError("wrong schema")
        ids=set()
        for item in self.value.get("inputs",[]):
            if item["id"] in ids: raise ReceiptError("duplicate input id")
            ids.add(item["id"])
            if not _HEX40.fullmatch(item["head"]) or not _HEX40.fullmatch(item["receipt_blob"]): raise ReceiptError("invalid exact input identity")
        required={"P1","P2","P3A","P3B","P3C","P3D","P4","P5","P6","P7"}
        if ids != required: raise ReceiptError(f"input set mismatch: {sorted(ids)}")
        seen={}
        for item in self.value.get("selected_blobs",[]):
            if not _HEX40.fullmatch(item["head"]) or not _HEX40.fullmatch(item["blob"]): raise ReceiptError("invalid selected blob identity")
            old=seen.setdefault(item["path"],item["blob"])
            if old != item["blob"]: raise CollisionError(item["path"])
    def admit_copy(self, *, source_head: str, source_path: str, blob: str) -> None:
        allowed={(x["head"],x["path"],x["blob"]) for x in self.value["selected_blobs"]}
        if (source_head,source_path,blob) not in allowed: raise ReceiptError("unlisted convergence source")
@dataclass(frozen=True, slots=True)
class DeviceReceipt:
    app_commit: str; os: str; device: str; provider: str; runtime: str; model_sha256: str; observed_backend: str; skill_digest: str|None=None
    def validate(self) -> None:
        if not _HEX40.fullmatch(self.app_commit): raise ReceiptError("app commit required")
        for value in (self.os,self.device,self.provider,self.runtime,self.observed_backend):
            if not value.strip(): raise ReceiptError("device receipt field missing")
        if not re.fullmatch(r"[0-9a-f]{64}",self.model_sha256): raise ReceiptError("model digest required")
@dataclass(slots=True)
class Lifecycle:
    active_sessions:int=0; sandbox_residue:int=0; cancelled:bool=False
    def start(self): self.active_sessions+=1
    def open_sandbox(self): self.sandbox_residue+=1
    def cancel_and_cleanup(self): self.cancelled=True; self.active_sessions=0; self.sandbox_residue=0
class ReferencePolicy:
    @staticmethod
    def select_provider(*, system_available: bool, system_requires_network: bool, embedded_available: bool) -> str:
        if system_available and not system_requires_network: return "system.fake"
        if embedded_available: return "embedded.fake"
        raise ConvergenceError("no offline provider")
    @staticmethod
    def admit_tool(*, proposal_tool: str, allowed_tools: Iterable[str], confirmed: bool, effect: str) -> str:
        if proposal_tool not in set(allowed_tools): return "DENY"
        if effect != "PURE" and not confirmed: return "REQUIRE_CONFIRMATION"
        return "ALLOW"
    @staticmethod
    def validate_offline(*, allow_network: bool, provider_requires_network: bool) -> None:
        if allow_network or provider_requires_network: raise ConvergenceError("undeclared network egress")
    @staticmethod
    def validate_observed_backend(*, requested: str, observed: str, runtime_supported: set[str]) -> None:
        if observed not in runtime_supported: raise ReceiptError("unsupported observed backend")
        if not requested or not observed: raise ReceiptError("backend identity missing")
def golden_scenario() -> dict[str, object]:
    provider=ReferencePolicy.select_provider(system_available=False,system_requires_network=False,embedded_available=True)
    ReferencePolicy.validate_offline(allow_network=False,provider_requires_network=False)
    decision=ReferencePolicy.admit_tool(proposal_tool="save_note",allowed_tools={"save_note"},confirmed=True,effect="WRITE_LOCAL")
    ReferencePolicy.validate_observed_backend(requested="NPU",observed="CPU",runtime_supported={"CPU"})
    return {"network_allowed":False,"observed_backend":"CPU","provider":provider,"route":"EMBEDDED","tool_decision":decision,"tool_effect":"WRITE_LOCAL","tool_name":"save_note"}
