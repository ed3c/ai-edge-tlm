from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
ADAPTER = ROOT / "adapters/android/system-genai/src/main/kotlin/io/ed3c/aiedge/adapters/android/systemgenai/AndroidSystemAdapter.kt"
PACKET = ROOT / "adapters/android/system-genai/task-packets/p3a-android-system-v1.task.json"
RECEIPT = ROOT / "adapters/android/system-genai/receipts/p3a-candidate.json"


def test_packet_and_candidate_receipt_preserve_evidence_ceiling() -> None:
    packet = json.loads(PACKET.read_text(encoding="utf-8"))
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    assert packet["parent"]["commit"] == "e86822f6917b3cee05602731d5899e5e8fbe7594"
    assert receipt["parent_subject"] == packet["parent"]["commit"]
    assert receipt["evidence"]["LIVE_DEVICE"] == "NOT_EXERCISED"
    assert receipt["evidence"]["ANDROID_GRADLE"] == "NOT_EXERCISED"
    assert receipt["evidence"]["SDK_TERMS"] == "HUMAN_ADMIT_REQUIRED"


def test_no_provider_sdk_type_or_network_fallback_leaks() -> None:
    source = ADAPTER.read_text(encoding="utf-8")
    forbidden = [r"import\s+android\.", r"import\s+androidx\.", r"import\s+com\.google\.", r"ProviderKind\.CLOUD"]
    for pattern in forbidden:
        assert re.search(pattern, source) is None, pattern
    assert "FallbackTarget.EMBEDDED_TLM" in source
    assert "networkAllowed: Boolean = false" in source
    assert "ToolProposal" in source
    assert "ToolAdmission" not in source


def test_task_packet_is_the_only_preimplementation_file() -> None:
    assert PACKET.is_file()
    assert ADAPTER.is_file()
    assert RECEIPT.is_file()


@pytest.mark.skipif(os.environ.get("AI_EDGE_RUN_NATIVE_TOOLCHAINS") != "1", reason="explicit LOCAL Kotlin/JVM lane")
def test_kotlin_fake_provider_vertical_slice() -> None:
    subprocess.run([str(ROOT / "tests/p3a/run_kotlin_tests.sh")], cwd=ROOT, check=True)
