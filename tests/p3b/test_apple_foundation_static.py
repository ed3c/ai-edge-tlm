from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "adapters/apple/foundation-models"
SOURCE_DIR = PACKAGE / "Sources/AppleFoundationAdapter"
PACKET = PACKAGE / "task-packets/p3b-apple-foundation-v1.task.json"
RECEIPT = PACKAGE / "receipts/p3b-candidate.json"


def test_packet_and_receipt_preserve_evidence_ceiling() -> None:
    packet = json.loads(PACKET.read_text(encoding="utf-8"))
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    assert packet["parent"]["commit"] == "e86822f6917b3cee05602731d5899e5e8fbe7594"
    assert receipt["parent_subject"] == packet["parent"]["commit"]
    assert receipt["evidence"]["LIVE_DEVICE"] == "NOT_EXERCISED"
    assert receipt["evidence"]["XCODE_IOS"] == "NOT_EXERCISED"
    assert receipt["evidence"]["SDK_TERMS"] == "HUMAN_ADMIT_REQUIRED"


def test_no_foundation_models_sdk_type_or_cloud_fallback_leaks() -> None:
    source = "\n".join(path.read_text(encoding="utf-8") for path in sorted(SOURCE_DIR.glob("*.swift")))
    forbidden = [r"import\s+FoundationModels", r"ProviderKind\.cloud", r"ToolAdmission\("]
    for pattern in forbidden:
        assert re.search(pattern, source) is None, pattern
    assert 'FallbackDecision(reason:' in source
    assert 'networkAllowed: Bool = false' in source
    assert 'ToolProposal(' in source


def test_prompt_profile_and_session_isolation_are_explicit() -> None:
    source = "\n".join(path.read_text(encoding="utf-8") for path in sorted(SOURCE_DIR.glob("*.swift")))
    assert "systemModelRevision" in source
    assert "SessionIsolationRegistry" in source
    assert "sessionOwnershipConflict" in source
    assert "context window exceeded" in source


@pytest.mark.skipif(os.environ.get("AI_EDGE_RUN_NATIVE_TOOLCHAINS") != "1", reason="explicit LOCAL Swift/Linux lane")
def test_swift_fake_session_vertical_slice() -> None:
    # Keep the local evidence lane deterministic and avoid index-store races on
    # shared/container filesystems. The scratch directory is disposable and
    # never becomes repository evidence.
    with tempfile.TemporaryDirectory(prefix="ai-edge-p3b-swift-") as scratch:
        subprocess.run(
            [
                "swift",
                "test",
                "--package-path",
                str(PACKAGE),
                "--scratch-path",
                scratch,
                "--enable-index-store",
                "--jobs",
                "1",
            ],
            cwd=ROOT,
            check=True,
            timeout=180,
        )
