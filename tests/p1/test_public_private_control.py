from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime, timedelta

import pytest

from edge_tlm_control.capsule import CapsuleError, ContextRequest, build_capsule, verify_capsule
from edge_tlm_control.classification import Classification, classify_field
from edge_tlm_control.resolver import inspect_resolver_presence

SUBJECT = "e959201574b9548758e9d173b02e214c9e8531e7"
NOW = datetime(2026, 8, 21, 3, 0, tzinfo=UTC)


def request(**overrides):
    values = {
        "task_id": "P1-07",
        "repository_subject": SUBJECT,
        "requested_fields": ["architecture_decisions", "technical_constraints", "source_ids"],
        "ttl_seconds": 600,
    }
    values.update(overrides)
    return ContextRequest.create(**values)


def private_context():
    return {
        "architecture_decisions": ["Use host-owned bounded DAG orchestration."],
        "technical_constraints": ["No private URI values in Git."],
        "source_ids": ["SRC-LITERT-LM-README"],
        "roadmap": ["private future plan"],
        "api_token": "not-for-capsule",
    }


def test_build_and_verify_allowlisted_capsule():
    capsule = build_capsule(private_context(), request(), issued_at=NOW)
    verified = verify_capsule(capsule, expected_task_id="P1-07", expected_repository_subject=SUBJECT, now=NOW + timedelta(seconds=1))
    assert set(verified["fields"]) == {"architecture_decisions", "technical_constraints", "source_ids"}
    assert "roadmap" not in verified["fields"]
    assert "api_token" not in verified["fields"]


def test_private_secret_and_human_fields_are_classified_separately():
    assert classify_field("roadmap") is Classification.PRIVATE
    assert classify_field("api_token") is Classification.SECRET
    assert classify_field("merge_approval") is Classification.HUMAN
    assert classify_field("technical_constraints") is Classification.PUBLIC_TECHNICAL


def test_cross_task_capsule_is_rejected():
    capsule = build_capsule(private_context(), request(), issued_at=NOW)
    with pytest.raises(CapsuleError, match="cross-task"):
        verify_capsule(capsule, expected_task_id="P2-03", expected_repository_subject=SUBJECT, now=NOW + timedelta(seconds=1))


def test_wrong_subject_capsule_is_rejected():
    capsule = build_capsule(private_context(), request(), issued_at=NOW)
    with pytest.raises(CapsuleError, match="wrong-subject"):
        verify_capsule(capsule, expected_task_id="P1-07", expected_repository_subject="0" * 40, now=NOW + timedelta(seconds=1))


def test_expired_capsule_is_rejected():
    capsule = build_capsule(private_context(), request(ttl_seconds=10), issued_at=NOW)
    with pytest.raises(CapsuleError, match="not active"):
        verify_capsule(capsule, expected_task_id="P1-07", expected_repository_subject=SUBJECT, now=NOW + timedelta(seconds=11))


def test_workspace_url_is_rejected_without_committing_literal_private_url():
    candidate = private_context()
    candidate["technical_constraints"] = ["https://" + "docs.google.com/document/d/P1_CANARY"]
    with pytest.raises(CapsuleError, match="Workspace URL"):
        build_capsule(candidate, request(), issued_at=NOW)


def test_secret_like_value_is_rejected():
    candidate = private_context()
    candidate["technical_constraints"] = ["Bearer abcdefghijklmnopqrstuvwxyz"]
    with pytest.raises(CapsuleError, match="secret-like"):
        build_capsule(candidate, request(), issued_at=NOW)


def test_unallowlisted_requested_field_is_rejected():
    with pytest.raises(CapsuleError, match="not capsule-allowlisted"):
        build_capsule(private_context(), request(requested_fields=["roadmap"]), issued_at=NOW)


def test_oversized_capsule_is_rejected():
    candidate = private_context()
    candidate["technical_constraints"] = ["x" * 1800, "y" * 1800]
    with pytest.raises(CapsuleError, match="max_bytes"):
        build_capsule(candidate, request(max_bytes=512), issued_at=NOW)


def test_tampered_capsule_digest_is_rejected():
    capsule = build_capsule(private_context(), request(), issued_at=NOW)
    tampered = deepcopy(capsule)
    tampered["fields"]["source_ids"] = ["SRC-TAMPERED"]
    with pytest.raises(CapsuleError, match="digest mismatch"):
        verify_capsule(tampered, expected_task_id="P1-07", expected_repository_subject=SUBJECT, now=NOW + timedelta(seconds=1))


def test_resolver_presence_never_returns_values():
    control_value = "https://" + "docs.google.com/document/d/PRIVATE"
    ledger_value = "https://" + "docs.google.com/spreadsheets/d/PRIVATE"
    result = inspect_resolver_presence({
        "CODEXDOC_CONTROL_PLANE_URI": control_value,
        "CODEXDOC_LEDGER_URI": ledger_value,
    }).as_public_dict()
    serialized = repr(result)
    assert result["state"] == "READY_FOR_SIGNED_IN_CARRIER"
    assert control_value not in serialized
    assert ledger_value not in serialized


def test_missing_resolver_is_absent_not_inferred():
    result = inspect_resolver_presence({}).as_public_dict()
    assert result["state"] == "ABSENT"
    assert result["present_keys"] == []
