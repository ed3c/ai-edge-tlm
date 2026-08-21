from __future__ import annotations
import json
from pathlib import Path
import pytest
from apps.convergence.reference_harness import CollisionError, DeviceReceipt, ExactInputLedger, Lifecycle, ReceiptError, ReferencePolicy, golden_scenario
from core.dag.engine import DeterministicExecutor, Effect, ExecutionPlan, NodeSpec, ProviderResult, Subject

ROOT=Path(__file__).resolve().parents[2]
LEDGER=ROOT/'apps/convergence/exact-inputs.json'
GOLDEN=ROOT/'apps/convergence/golden/reference-scenario.json'

def test_exact_input_ledger_and_selected_blobs():
    ledger=ExactInputLedger.read(LEDGER); ledger.validate()
    first=ledger.value['selected_blobs'][0]
    ledger.admit_copy(source_head=first['head'],source_path=first['path'],blob=first['blob'])
    with pytest.raises(ReceiptError): ledger.admit_copy(source_head=first['head'],source_path='unlisted',blob=first['blob'])

def test_collision_fails_closed():
    value=json.loads(LEDGER.read_text())
    x=dict(value['selected_blobs'][0]); x['id']='COLLISION'; x['blob']='f'*40
    value['selected_blobs'].append(x)
    with pytest.raises(CollisionError): ExactInputLedger(value).validate()

def test_golden_scenario_matches_shared_fixture():
    assert golden_scenario()==json.loads(GOLDEN.read_text())

def test_offline_network_fails_closed():
    with pytest.raises(Exception): ReferencePolicy.validate_offline(allow_network=True,provider_requires_network=False)
    with pytest.raises(Exception): ReferencePolicy.validate_offline(allow_network=False,provider_requires_network=True)

def test_tool_proposal_requires_host_admission():
    assert ReferencePolicy.admit_tool(proposal_tool='delete_all',allowed_tools={'save_note'},confirmed=True,effect='WRITE_LOCAL')=='DENY'
    assert ReferencePolicy.admit_tool(proposal_tool='save_note',allowed_tools={'save_note'},confirmed=False,effect='WRITE_LOCAL')=='REQUIRE_CONFIRMATION'
    assert ReferencePolicy.admit_tool(proposal_tool='save_note',allowed_tools={'save_note'},confirmed=True,effect='WRITE_LOCAL')=='ALLOW'

def test_requested_backend_is_not_observed_backend():
    ReferencePolicy.validate_observed_backend(requested='NPU',observed='CPU',runtime_supported={'CPU'})
    with pytest.raises(ReceiptError): ReferencePolicy.validate_observed_backend(requested='NPU',observed='NPU',runtime_supported={'CPU'})

def test_device_receipt_requires_exact_identity():
    ok=DeviceReceipt('a'*40,'Android 16','Pixel-test','embedded.fake','litert-lm@v0.14.0','b'*64,'CPU')
    ok.validate()
    with pytest.raises(ReceiptError): DeviceReceipt('x','iOS','device','provider','runtime','b'*64,'GPU').validate()

def test_lifecycle_cancel_cleans_sessions_and_sandbox():
    state=Lifecycle(); state.start(); state.open_sandbox(); state.cancel_and_cleanup()
    assert state.cancelled and state.active_sessions==0 and state.sandbox_residue==0

class Broker:
    def admit(self,proposal,*,operation_id): return proposal=={'allowed':True}
class Provider:
    def __init__(self,identity): self.subject=Subject('provider',identity,'a'*8)
    def run(self,*,request_id,node,operation_id,attempt): return ProviderResult({'ok':True},self.subject,{'allowed':True} if node.node_id=='tool' else None)

def test_two_stage_host_owned_dag():
    subject=Subject('provider','embedded.fake','a'*8)
    plan=ExecutionPlan('req','trace',(
        NodeSpec('classify','embedded.fake',expected_subject=subject),
        NodeSpec('tool','embedded.fake',depends_on=('classify',),effect=Effect.WRITE_LOCAL,expected_subject=subject),
    ))
    receipt=DeterministicExecutor({'embedded.fake':Provider('embedded.fake')},Broker(),now_ms=lambda:1).execute(plan,deadline_ms=10)
    assert receipt.terminal_state=='SUCCEEDED'
    assert [r.node_id for r in receipt.node_receipts]==['classify','tool']
