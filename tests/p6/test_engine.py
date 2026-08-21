from __future__ import annotations
import pytest
from core.dag.engine import *
S1=Subject("provider","p1","digest-1111"); S2=Subject("provider","p2","digest-2222")
class FakeProvider:
    def __init__(self,subject=S1,failures=0,proposal=None): self.subject=subject;self.failures=failures;self.proposal=proposal;self.calls=[]
    def run(self,*,request_id,node,operation_id,attempt):
        self.calls.append((node.node_id,operation_id,attempt))
        if len(self.calls)<=self.failures: raise RuntimeError("boom")
        return ProviderResult({"ok":True},self.subject,self.proposal)
class Broker:
    def __init__(self,allow=True): self.allow=allow;self.calls=[]
    def admit(self,proposal,*,operation_id): self.calls.append((proposal,operation_id));return self.allow
def plan(*nodes,max_nodes=32,max_depth=8): return ExecutionPlan("req","trace",tuple(nodes),max_nodes,max_depth)

def test_valid_dag_is_deterministic():
    p=FakeProvider();x=DeterministicExecutor({"p":p},Broker(),now_ms=lambda:1).execute(plan(NodeSpec("a","p"),NodeSpec("b","p",("a",))),deadline_ms=100)
    assert x.terminal_state=="SUCCEEDED" and [r.node_id for r in x.node_receipts]==["a","b"] and len(x.plan_digest)==64

def test_cycle_and_missing_dependency_fail():
    with pytest.raises(PlanValidationError): PlanValidator().validate(plan(NodeSpec("a","p",("b",)),NodeSpec("b","p",("a",))))
    with pytest.raises(PlanValidationError): PlanValidator().validate(plan(NodeSpec("a","p",("missing",))))

def test_node_depth_and_duplicate_effect_budgets_fail():
    with pytest.raises(PlanValidationError): PlanValidator().validate(plan(NodeSpec("a","p"),NodeSpec("b","p",("a",)),max_depth=1))
    with pytest.raises(PlanValidationError): PlanValidator().validate(plan(NodeSpec("a","p",effect=Effect.EXTERNAL_SIDE_EFFECT,effect_key="x"),NodeSpec("b","p",effect=Effect.EXTERNAL_SIDE_EFFECT,effect_key="x")))

def test_retry_reuses_stable_operation_identity():
    p=FakeProvider(failures=1);x=DeterministicExecutor({"p":p},Broker(),now_ms=lambda:1).execute(plan(NodeSpec("a","p",effect=Effect.EXTERNAL_SIDE_EFFECT,effect_key="send",max_attempts=2)),deadline_ms=100)
    assert x.terminal_state=="SUCCEEDED" and p.calls[0][1]==p.calls[1][1]

def test_replay_of_completed_external_effect_fails_closed():
    p=FakeProvider();e=DeterministicExecutor({"p":p},Broker(),now_ms=lambda:1);pl=plan(NodeSpec("a","p",effect=Effect.EXTERNAL_SIDE_EFFECT,effect_key="send"));assert e.execute(pl,deadline_ms=100).terminal_state=="SUCCEEDED"
    with pytest.raises(ReplayError): e.execute(pl,deadline_ms=100)

def test_explicit_fallback_only_after_primary_fails():
    primary=FakeProvider(failures=2);backup=FakeProvider(subject=S2);x=DeterministicExecutor({"p":primary,"b":backup},Broker(),now_ms=lambda:1).execute(plan(NodeSpec("a","p",max_attempts=1,fallback_provider_ids=("b",),expected_subject=S2)),deadline_ms=100)
    assert x.terminal_state=="SUCCEEDED" and x.node_receipts[0].provider_id=="b"

def test_stale_provider_subject_rejected():
    with pytest.raises(StaleSubjectError): DeterministicExecutor({"p":FakeProvider(subject=S2)},Broker(),now_ms=lambda:1).execute(plan(NodeSpec("a","p",expected_subject=S1)),deadline_ms=100)

def test_tool_proposal_requires_broker_admission():
    broker=Broker(False);x=DeterministicExecutor({"p":FakeProvider(proposal={"tool":"x"})},broker,now_ms=lambda:1).execute(plan(NodeSpec("a","p")),deadline_ms=100)
    assert x.terminal_state=="FAILED" and broker.calls

def test_pre_cancel_and_deadline_fail_without_provider_call():
    p=FakeProvider();token=CancellationToken();token.cancel();e=DeterministicExecutor({"p":p},Broker(),now_ms=lambda:10);assert e.execute(plan(NodeSpec("a","p")),deadline_ms=100,cancellation=token).terminal_state=="FAILED" and not p.calls
    p2=FakeProvider();e2=DeterministicExecutor({"p":p2},Broker(),now_ms=lambda:101);assert e2.execute(plan(NodeSpec("a","p")),deadline_ms=100).terminal_state=="FAILED" and not p2.calls

def test_missing_provider_fails_closed_no_cloud_magic():
    x=DeterministicExecutor({},Broker(),now_ms=lambda:1).execute(plan(NodeSpec("a","missing")),deadline_ms=100);assert x.terminal_state=="FAILED" and "provider unavailable" in x.node_receipts[0].error

def test_compensation_runs_for_prior_success_after_later_failure():
    ok=FakeProvider();bad=FakeProvider(failures=10);comp=FakeProvider(subject=S2);e=DeterministicExecutor({"ok":ok,"bad":bad,"comp":comp},Broker(),now_ms=lambda:1)
    x=e.execute(plan(NodeSpec("a","ok",compensation_node_id="undo-a"),NodeSpec("b","bad",("a",)),NodeSpec("undo-a","comp",("b",))),deadline_ms=100);rec={r.node_id:r for r in x.node_receipts};assert x.terminal_state=="FAILED" and rec["a"].state==NodeState.COMPENSATED
