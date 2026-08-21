import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
PIN=ROOT/'adapters/apple/litert-lm/receipts/p3d-source-pin.json'
SRC=ROOT/'adapters/apple/litert-lm/Sources/AppleLiteRtLmAdapter/AppleLiteRtLmAdapter.swift'

def test_preview_and_backend_ceiling():
    x=json.loads(PIN.read_text())
    assert x['swift_api_maturity']=='EARLY_PREVIEW'
    assert x['release_integrity_state']=='REVIEW_REQUIRED'
    assert x['ios_backend_support']==['CPU','GPU']
    assert x['forbidden_claim'].startswith('ANE_OR_NPU')

def test_no_provider_sdk_type_crosses_contract_boundary():
    t=SRC.read_text()
    assert 'import LiteRTLM' not in t
    assert 'ProviderKind.cloud' not in t
    assert 'ToolAdmission' not in t
    assert 'swiftMaturity == .preview' in t
