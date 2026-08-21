import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def test_exact_input_subjects_and_blocked_embedded_integrations():
    x=json.loads((ROOT/'core/receipts/p6-input-subjects.json').read_text())
    assert x['p5']['commit']=='5ff71da2926b4691b5e0ad8dc672fa1bcc1bce5e'
    assert x['p3c_integration'].startswith('BLOCKED') and x['p3d_integration'].startswith('BLOCKED')

def test_core_does_not_import_provider_sdk_or_cloud_fallback():
    t=(ROOT/'core/dag/engine.py').read_text()
    assert 'com.google' not in t and 'FoundationModels' not in t and 'LiteRT' not in t
