import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "adapters/android/litert-lm/src/main/kotlin/io/ed3c/aiedge/adapters/android/litertlm/AndroidLiteRtLmAdapter.kt"
PIN = ROOT / "adapters/android/litert-lm/receipts/p3c-source-pin.json"

def test_source_pin_keeps_maturity_and_backend_evidence_separate():
    value = json.loads(PIN.read_text())
    assert value["selected_release"] == "v0.14.0"
    assert value["api_maturity"]["kotlin"] == "STABLE"
    assert value["api_maturity"]["swift"] == "EARLY_PREVIEW"
    assert value["release_integrity_state"] == "REVIEW_REQUIRED"
    assert value["backend_support"]["ios"] == ["CPU", "GPU"]

def test_provider_types_do_not_cross_p2_boundary_and_tools_are_proposals():
    text = SRC.read_text()
    assert "com.google.ai.edge.litertlm" not in text
    assert "ToolProposal(" in text
    assert "ToolAdmission" not in text
    assert "ProviderKind.CLOUD" not in text

def test_requested_backend_not_equal_to_observed_evidence_by_construction():
    text = SRC.read_text()
    assert "val requestedBackend: BackendKind" in text
    assert "val selectedBackend: BackendKind" in text
    assert "val observedBackend: BackendKind" in text
    assert "session.observedBackend" in text
