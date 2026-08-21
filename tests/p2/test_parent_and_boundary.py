from __future__ import annotations

import copy
import json
from pathlib import Path

from contracts.generator.contract_checks import (
    evidence_lane_satisfies,
    parent_identity_failures,
    public_text_failures,
)
from contracts.generator.generate import ROOT


def packet() -> dict:
    return json.loads((ROOT / "contracts/task-packets/p2-cross-platform-v1.task.json").read_text(encoding="utf-8"))


def test_exact_parent_semantics_and_git_blob_identities_match() -> None:
    assert parent_identity_failures(ROOT, packet()) == []


def test_wrong_parent_blob_and_ref_fail_convergence() -> None:
    mutated = copy.deepcopy(packet())
    mutated["input_contracts"]["p0"][0]["git_blob_sha1"] = "0" * 40
    mutated["input_contracts"]["p1"][0]["ref"] = "0" * 40
    failures = parent_identity_failures(ROOT, mutated)
    assert any("Git blob drift" in f for f in failures)
    assert any("source ref drift" in f for f in failures)


def test_private_workspace_url_resolver_value_and_secret_fail_public_contract_gate(tmp_path: Path) -> None:
    private_url = tmp_path / "private.md"
    private_url.write_text("https://" + "docs.google.com/" + "document/d/private", encoding="utf-8")
    resolver = tmp_path / "resolver.txt"
    resolver.write_text("CODEXDOC_CONTROL_PLANE_URI" + "=" + "https://example.invalid", encoding="utf-8")
    secret = tmp_path / "secret.txt"
    secret.write_text("ghp_abcdefghijklmnopqrstuvwxyz1234567890", encoding="utf-8")
    failures = public_text_failures([private_url, resolver, secret])
    assert any("private Workspace URL" in f for f in failures)
    assert any("resolver URI value" in f for f in failures)
    assert any("secret-like value" in f for f in failures)


def test_evidence_lanes_cannot_be_laundered() -> None:
    lanes = ["SOURCE", "STATIC", "LOCAL", "LIVE_DEVICE", "PRIVATE", "HUMAN"]
    for actual in lanes:
        for required in lanes:
            assert evidence_lane_satisfies(actual, required) is (actual == required)
    assert not evidence_lane_satisfies("STATIC", "LIVE_DEVICE")
    assert not evidence_lane_satisfies("LOCAL", "PRIVATE")
    assert not evidence_lane_satisfies("LIVE_DEVICE", "HUMAN")
