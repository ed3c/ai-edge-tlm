from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_candidate_receipt_does_not_promote_policy_tests() -> None:
    receipt = json.loads((ROOT / "skills/receipts/p5-candidate.json").read_text(encoding="utf-8"))
    assert receipt["parent_subject"] == "e86822f6917b3cee05602731d5899e5e8fbe7594"
    assert receipt["evidence"]["LIVE_DEVICE"] == "NOT_EXERCISED"
    assert receipt["evidence"]["REMOTE_CODE_TRUST"] == "HUMAN_ADMIT_REQUIRED"
    assert receipt["evidence"]["WEBVIEW_EXPLOIT_RESISTANCE"] == "NOT_EXERCISED"
    assert receipt["evidence"]["SECRET_CARRIER"] == "PRIVATE_NOT_EXERCISED"


def test_malicious_fixtures_are_data_not_executable_code() -> None:
    fixture = json.loads((ROOT / "skills/fixtures/malicious-scenarios.json").read_text(encoding="utf-8"))
    assert fixture["evidence_lane"] == "LOCAL"
    assert "secret-echo" in fixture["scenarios"]
    assert not list((ROOT / "skills/fixtures").rglob("*.js"))
    assert not list((ROOT / "skills/fixtures").rglob("*.html"))


def test_public_skill_tree_contains_no_private_workspace_or_secret_values() -> None:
    forbidden = (
        "docs" + ".google.com/",
        "drive" + ".google.com/",
        "sheets" + ".google.com/",
        "BEGIN " + "PRIVATE KEY",
    )
    for path in (ROOT / "skills").rglob("*"):
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
            text = path.read_text(encoding="utf-8")
            for value in forbidden:
                assert value not in text, f"forbidden public value in {path}"


def test_runtime_module_surface_is_closed_and_importable_from_clean_tree() -> None:
    expected = {
        "__init__.py",
        "broker.py",
        "errors.py",
        "integrity.py",
        "registry.py",
        "sandbox.py",
        "types.py",
    }
    actual = {
        path.name
        for path in (ROOT / "skills/runtime").glob("*.py")
        if path.is_file()
    }
    assert actual == expected
    import skills.runtime as runtime

    assert runtime.SkillRegistry is not None
    assert runtime.SandboxRunner is not None
