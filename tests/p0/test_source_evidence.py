from __future__ import annotations

import importlib.util
import json
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = ROOT / "docs" / "research" / "scripts" / "validate_evidence.py"
SPEC = importlib.util.spec_from_file_location("p0_validator", VALIDATOR_PATH)
assert SPEC and SPEC.loader
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


def load(name: str):
    return json.loads((ROOT / "docs" / "research" / name).read_text(encoding="utf-8"))


def test_p0_registers_pass():
    failures, receipt = validator.validate_all()
    assert failures == []
    assert receipt["state"] == "PASS"
    assert receipt["p2_start_output"] == "READABLE"
    assert receipt["counts"]["claims"] >= 23


def test_stale_rolling_source_fails_closed():
    register = load("source-register.json")
    candidate = deepcopy(register)
    rolling = next(source for source in candidate["sources"] if source["identity_state"] == "ROLLING")
    rolling["retrieved_at"] = "2020-01-01"
    failures = validator.validate_sources(candidate)
    assert any("stale" in failure for failure in failures)


def test_wrong_subject_immutable_source_fails_closed():
    register = load("source-register.json")
    candidate = deepcopy(register)
    source = next(source for source in candidate["sources"] if source["identity_state"] == "IMMUTABLE")
    source["revision"] = "main"
    failures = validator.validate_sources(candidate)
    assert any("SHA-40" in failure for failure in failures)


def test_missing_source_packet_cannot_self_promote():
    sources = load("source-register.json")
    ledger = load("claim-ledger.json")
    candidate = deepcopy(ledger)
    candidate["claims"][0]["status"] = "CORROBORATED"
    candidate["claims"][0]["source_ids"] = ["SRC-USER-ARTICLE-PACKET"]
    failures = validator.validate_claims(candidate, sources)
    assert any("admitted primary" in failure or "self-promote" in failure for failure in failures)


def test_model_weights_cannot_inherit_apache_license():
    sources = load("source-register.json")
    licenses = load("license-register.json")
    candidate = deepcopy(licenses)
    entry = next(entry for entry in candidate["entries"] if entry["plane"] == "MODEL_WEIGHTS")
    entry["license_id"] = "Apache-2.0"
    failures = validator.validate_licenses(candidate, sources)
    assert any("may not inherit" in failure for failure in failures)


def test_fastvlm_weights_cannot_be_commercial_default():
    sources = load("source-register.json")
    licenses = load("license-register.json")
    candidate = deepcopy(licenses)
    entry = next(entry for entry in candidate["entries"] if entry["id"] == "LIC-FASTVLM-WEIGHTS")
    entry["commercial_default"] = True
    failures = validator.validate_licenses(candidate, sources)
    assert any("commercial default" in failure or "research-only" in failure for failure in failures)


def test_private_workspace_url_is_rejected_without_literal_public_url():
    register = load("source-register.json")
    candidate = deepcopy(register)
    candidate["sources"][0]["url"] = "https://" + "docs.google.com/document/d/P0_CANARY"
    failures = validator.validate_sources(candidate)
    assert any("private Google Workspace" in failure for failure in failures)


def test_receipt_digests_are_deterministic():
    failures_a, receipt_a = validator.validate_all()
    failures_b, receipt_b = validator.validate_all()
    assert failures_a == failures_b == []
    assert receipt_a["digests"] == receipt_b["digests"]
