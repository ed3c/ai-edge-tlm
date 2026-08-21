from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import hashlib
import json
import time
from typing import Callable, Mapping, Protocol

class OrchestrationError(RuntimeError): pass
class PlanValidationError(OrchestrationError): pass
class StaleSubjectError(OrchestrationError): pass
class ReplayError(OrchestrationError): pass

class NodeState(StrEnum):
    PENDING="PENDING"; READY="READY"; RUNNING="RUNNING"; SUCCEEDED="SUCCEEDED"; FAILED="FAILED"; COMPENSATING="COMPENSATING"; COMPENSATED="COMPENSATED"; CANCELLED="CANCELLED"
class Effect(StrEnum):
    PURE="PURE"; READ_LOCAL="READ_LOCAL"; WRITE_LOCAL="WRITE_LOCAL"; EXTERNAL_SIDE_EFFECT="EXTERNAL_SIDE_EFFECT"

@dataclass(frozen=True,slots=True)
class Subject:
    kind:str; identity:str; digest:str
    def __post_init__(self):
        if not self.kind or not self.identity or len(self.digest)<8: raise ValueError("invalid subject")

@dataclass(frozen=True,slots=True)
class NodeSpec:
    node_id:str; provider_id:str; depends_on:tuple[str,...]=(); effect:Effect=Effect.PURE; effect_key:str|None=None; timeout_ms:int=1000; max_attempts:int=1; fallback_provider_ids:tuple[str,...]=(); compensation_node_id:str|None=None; expected_subject:Subject|None=None
    def __post_init__(self):
        if not self.node_id or not self.provider_id: raise ValueError("node/provider id required")
        if self.timeout_ms<=0 or self.max_attempts<=0: raise ValueError("positive bounds required")
        if self.effect is Effect.EXTERNAL_SIDE_EFFECT and not self.effect_key: raise ValueError("external side effects require effect_key")

@dataclass(frozen=True,slots=True)
class ExecutionPlan:
    request_id:str; trace_id:str; nodes:tuple[NodeSpec,...]; max_nodes:int=32; max_depth:int=8
@dataclass(frozen=True,slots=True)
class ProviderResult:
    output:object|None; provider_subject:Subject; tool_proposal:object|None=None
class Provider(Protocol):
    subject:Subject
    def run(self,*,request_id:str,node:NodeSpec,operation_id:str,attempt:int)->ProviderResult: ...
class ToolBroker(Protocol):
    def admit(self,proposal:object,*,operation_id:str)->bool: ...
@dataclass(frozen=True,slots=True)
class NodeReceipt:
    node_id:str; state:NodeState; provider_id:str; operation_id:str; attempts:int; provider_subject:Subject|None; error:str|None=None; compensated_by:str|None=None
@dataclass(frozen=True,slots=True)
class TerminalReceipt:
    request_id:str; trace_id:str; plan_digest:str; terminal_state:str; node_receipts:tuple[NodeReceipt,...]; subjects:tuple[Subject,...]

class CancellationToken:
    def __init__(self): self._cancelled=False
    def cancel(self): self._cancelled=True
    @property
    def cancelled(self): return self._cancelled

class PlanValidator:
    def validate(self,plan:ExecutionPlan)->tuple[str,...]:
        if not plan.request_id or not plan.trace_id: raise PlanValidationError("request and trace id required")
        if len(plan.nodes)==0 or len(plan.nodes)>plan.max_nodes: raise PlanValidationError("node budget exceeded")
        ids=[n.node_id for n in plan.nodes]
        if len(ids)!=len(set(ids)): raise PlanValidationError("duplicate node id")
        node_map={n.node_id:n for n in plan.nodes}
        for n in plan.nodes:
            missing=[d for d in n.depends_on if d not in node_map]
            if missing: raise PlanValidationError(f"missing dependency: {missing}")
        effects=[n.effect_key for n in plan.nodes if n.effect is Effect.EXTERNAL_SIDE_EFFECT]
        if len(effects)!=len(set(effects)): raise PlanValidationError("duplicate external effect identity")
        visiting=set(); visited=set(); order=[]; depth_cache={}
        def visit(node_id):
            if node_id in visiting: raise PlanValidationError("cycle detected")
            if node_id in visited: return depth_cache[node_id]
            visiting.add(node_id); node=node_map[node_id]
            depth=1+max((visit(d) for d in node.depends_on),default=0)
            if depth>plan.max_depth: raise PlanValidationError("depth budget exceeded")
            visiting.remove(node_id); visited.add(node_id); depth_cache[node_id]=depth; order.append(node_id); return depth
        for node_id in sorted(node_map): visit(node_id)
        return tuple(order)

class DeterministicExecutor:
    def __init__(self,providers:Mapping[str,Provider],tool_broker:ToolBroker,*,now_ms:Callable[[],int]|None=None):
        self.providers=dict(providers); self.tool_broker=tool_broker; self.now_ms=now_ms or (lambda:int(time.time()*1000)); self._completed_effects=set()
    def execute(self,plan:ExecutionPlan,*,deadline_ms:int,cancellation:CancellationToken|None=None)->TerminalReceipt:
        cancellation=cancellation or CancellationToken(); order=PlanValidator().validate(plan); node_map={n.node_id:n for n in plan.nodes}; receipts={}; subjects={}; failed=False
        for node_id in order:
            node=node_map[node_id]
            if cancellation.cancelled:
                receipts[node_id]=NodeReceipt(node_id,NodeState.CANCELLED,node.provider_id,self._operation_id(plan.request_id,node),0,None,"cancelled"); failed=True; break
            if self.now_ms()>deadline_ms:
                receipts[node_id]=NodeReceipt(node_id,NodeState.FAILED,node.provider_id,self._operation_id(plan.request_id,node),0,None,"deadline exceeded"); failed=True; break
            if any(receipts[d].state is not NodeState.SUCCEEDED for d in node.depends_on):
                receipts[node_id]=NodeReceipt(node_id,NodeState.FAILED,node.provider_id,self._operation_id(plan.request_id,node),0,None,"dependency failed"); failed=True; break
            receipt=self._run_node(plan,node,deadline_ms,cancellation); receipts[node_id]=receipt
            if receipt.provider_subject:
                s=receipt.provider_subject; subjects[(s.kind,s.identity,s.digest)]=s
            if receipt.state is not NodeState.SUCCEEDED:
                failed=True; self._compensate(plan,node_map,receipts,node); break
        terminal="FAILED" if failed else "SUCCEEDED"
        return TerminalReceipt(plan.request_id,plan.trace_id,self._plan_digest(plan),terminal,tuple(receipts[k] for k in order if k in receipts),tuple(sorted(subjects.values(),key=lambda s:(s.kind,s.identity,s.digest))))
    def _run_node(self,plan,node,deadline_ms,cancellation):
        operation_id=self._operation_id(plan.request_id,node)
        if node.effect is Effect.EXTERNAL_SIDE_EFFECT and operation_id in self._completed_effects: raise ReplayError(f"effect replay: {operation_id}")
        attempts=0; last_error="no provider"
        for provider_id in (node.provider_id,)+node.fallback_provider_ids:
            provider=self.providers.get(provider_id)
            if provider is None: last_error=f"provider unavailable: {provider_id}"; continue
            for attempt in range(1,node.max_attempts+1):
                attempts+=1
                if cancellation.cancelled: return NodeReceipt(node.node_id,NodeState.CANCELLED,provider_id,operation_id,attempts,None,"cancelled")
                if self.now_ms()>deadline_ms: return NodeReceipt(node.node_id,NodeState.FAILED,provider_id,operation_id,attempts,None,"deadline exceeded")
                try:
                    result=provider.run(request_id=plan.request_id,node=node,operation_id=operation_id,attempt=attempt)
                    if node.expected_subject and result.provider_subject!=node.expected_subject: raise StaleSubjectError("provider subject drift")
                    if result.tool_proposal is not None and not self.tool_broker.admit(result.tool_proposal,operation_id=operation_id): raise OrchestrationError("tool proposal denied")
                    if node.effect is Effect.EXTERNAL_SIDE_EFFECT: self._completed_effects.add(operation_id)
                    return NodeReceipt(node.node_id,NodeState.SUCCEEDED,provider_id,operation_id,attempts,result.provider_subject)
                except StaleSubjectError: raise
                except Exception as exc: last_error=f"{type(exc).__name__}: {exc}"
        return NodeReceipt(node.node_id,NodeState.FAILED,node.provider_id,operation_id,attempts,None,last_error)
    def _compensate(self,plan,node_map,receipts,failed_node):
        for done_id in reversed(list(receipts)):
            receipt=receipts[done_id]
            if receipt.state is not NodeState.SUCCEEDED: continue
            spec=node_map[done_id]; comp_id=spec.compensation_node_id
            if not comp_id: continue
            comp=node_map.get(comp_id); provider=None if comp is None else self.providers.get(comp.provider_id)
            if comp is None or provider is None:
                receipts[done_id]=NodeReceipt(done_id,NodeState.FAILED,receipt.provider_id,receipt.operation_id,receipt.attempts,receipt.provider_subject,"missing compensation"); continue
            try:
                provider.run(request_id=plan.request_id,node=comp,operation_id=self._operation_id(plan.request_id,comp),attempt=1)
                receipts[done_id]=NodeReceipt(done_id,NodeState.COMPENSATED,receipt.provider_id,receipt.operation_id,receipt.attempts,receipt.provider_subject,compensated_by=comp_id)
            except Exception as exc:
                receipts[done_id]=NodeReceipt(done_id,NodeState.FAILED,receipt.provider_id,receipt.operation_id,receipt.attempts,receipt.provider_subject,f"compensation failed: {exc}",compensated_by=comp_id)
    @staticmethod
    def _operation_id(request_id,node): return hashlib.sha256(f"{request_id}|{node.node_id}|{node.effect.value}|{node.effect_key or '-'}".encode()).hexdigest()
    @staticmethod
    def _plan_digest(plan):
        value={"request_id":plan.request_id,"trace_id":plan.trace_id,"nodes":[{"id":n.node_id,"provider":n.provider_id,"deps":list(n.depends_on),"effect":n.effect.value,"effect_key":n.effect_key,"timeout_ms":n.timeout_ms,"attempts":n.max_attempts,"fallback":list(n.fallback_provider_ids),"subject":None if n.expected_subject is None else {"kind":n.expected_subject.kind,"identity":n.expected_subject.identity,"digest":n.expected_subject.digest}} for n in plan.nodes]}
        return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",", ":")).encode()).hexdigest()
