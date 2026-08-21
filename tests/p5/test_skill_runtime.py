from __future__ import annotations

from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import time

import pytest

from skills.runtime import PackageVerifier, SandboxRunner, SkillRegistry, ToolBroker, canonical_manifest_digest
from skills.runtime.errors import IntegrityError, ReplayError
from skills.runtime.types import (
    SandboxExecutionRequest,
    SandboxPolicy,
    SandboxState,
    SkillMetadata,
    ToolDecision,
    ToolDefinition,
    ToolEffect,
    ToolProposal,
)

ROOT = Path(__file__).resolve().parents[2]
ORIGIN = "https://skills.example.test"


def _success_executor(payload, secret, instance):
    (instance / "temp.js").write_text("executable residue", encoding="utf-8")
    return {"result": payload["title"]}


def _slow_executor(payload, secret, instance):
    (instance / "leftover.js").write_text("x", encoding="utf-8")
    time.sleep(1)
    return {"result": "late"}


def _crash_executor(payload, secret, instance):
    raise RuntimeError("boom")


def _echo_executor(payload, secret, instance):
    return {"result": secret}


def _malformed_executor(payload, secret, instance):
    return {"other": 1}


def _oversized_executor(payload, secret, instance):
    return {"result": "x" * 1000}


def skill(skill_id: str, description: str, source: bytes = b"package", *, version: str = "1.0.0"):
    source_uri = f"{ORIGIN}/{skill_id}/{version}"
    source_digest = hashlib.sha256(source).hexdigest()
    manifest = {
        "skill_id": skill_id,
        "version": version,
        "description": description,
        "source_uri": source_uri,
        "source_sha256": source_digest,
        "required_tools": ["calendar.create"],
    }
    metadata = SkillMetadata(skill_id, version, description, source_uri, source_digest, canonical_manifest_digest(manifest), ("calendar.create",))
    return metadata, manifest, source


def admitted_registry() -> tuple[SkillRegistry, object]:
    registry = SkillRegistry(PackageVerifier({ORIGIN}))
    metadata, manifest, source = skill("calendar-helper", "create and manage calendar events")
    verified_ref = registry.register(metadata, manifest, source, "Call calendar.create only as a proposal.")
    ref = registry.admit_trust(metadata.skill_id, metadata.version, verified_ref, policy_decision_id="host-policy-calendar-v1")
    return registry, ref


def strict_policy(**overrides):
    base = dict(
        allowed_origins=frozenset({ORIGIN}),
        allowed_network_origins=frozenset(),
        allowed_bridges=frozenset({"render.text"}),
        allow_storage=False,
        allow_camera=False,
        allow_microphone=False,
        max_input_bytes=512,
        max_output_bytes=512,
        timeout_ms=100,
        require_strict_csp=True,
    )
    base.update(overrides)
    return SandboxPolicy(**base)


def request(ref, execution_id="exec-1", **overrides):
    base = dict(
        execution_id=execution_id,
        skill_ref=ref,
        script_name="index.html",
        payload={"title": "sync"},
        csp="default-src 'none'; script-src 'self'",
        requested_bridges=("render.text",),
        secret_handle="secret-handle-1",
    )
    base.update(overrides)
    return SandboxExecutionRequest(**base)


def test_metadata_routing_is_deterministic_and_ambiguous_ties_fail_closed() -> None:
    registry = SkillRegistry(PackageVerifier({ORIGIN}))
    for skill_id, description in (("map-food", "find nearby food places"), ("food-map", "find nearby food places")):
        metadata, manifest, source = skill(skill_id, description, source=skill_id.encode())
        verified = registry.register(metadata, manifest, source, "instructions")
        registry.admit_trust(metadata.skill_id, metadata.version, verified, policy_decision_id=f"host-policy-{skill_id}")
    decision = registry.route("find nearby food places")
    assert decision.ambiguous is True
    assert decision.selected_skill_id is None
    assert decision.candidate_skill_ids == tuple(sorted(decision.candidate_skill_ids))
    index = registry.prompt_index()
    assert "instructions" not in index
    assert "find nearby food places" in index


def test_full_instructions_require_integrity_and_explicit_host_trust() -> None:
    registry = SkillRegistry(PackageVerifier({ORIGIN}))
    metadata, manifest, source = skill("calendar-helper", "create and manage calendar events")
    verified = registry.register(metadata, manifest, source, "Call calendar.create only as a proposal.")
    assert verified.trust_state.value == "UNTRUSTED"
    assert registry.prompt_index() == ""
    with pytest.raises(IntegrityError):
        registry.load_instructions(verified.skill_id, verified.version, verified)
    ref = registry.admit_trust(verified.skill_id, verified.version, verified, policy_decision_id="host-policy-calendar-v1")
    assert ref.trust_state.value == "TRUSTED"
    assert registry.load_instructions(ref.skill_id, ref.version, ref).startswith("Call")
    with pytest.raises(IntegrityError):
        registry.load_instructions(ref.skill_id, ref.version, replace(ref, source_sha256="0" * 64))

    tamper_metadata, tamper_manifest, tamper_source = skill("tamper", "tamper check")
    with pytest.raises(IntegrityError):
        registry.register(tamper_metadata, tamper_manifest, tamper_source + b"changed", "instructions")
    with pytest.raises(IntegrityError):
        registry.register(tamper_metadata, {**tamper_manifest, "description": "changed"}, tamper_source, "instructions")


def test_host_tool_broker_controls_authority_confirmation_and_replay() -> None:
    broker = ToolBroker([
        ToolDefinition("math.add", ToolEffect.PURE, {"a": int, "b": int}),
        ToolDefinition("calendar.create", ToolEffect.EXTERNAL_SIDE_EFFECT, {"title": str}, requires_confirmation=True, idempotency_required=True),
    ])
    invalid_digest = ToolProposal("bad-digest", "math.add", {"a": 1, "b": 2}, "not-a-digest")
    assert broker.admit(invalid_digest).decision == ToolDecision.DENY
    bool_as_int = ToolProposal("bool-int", "math.add", {"a": True, "b": 2}, "c" * 64)
    assert broker.admit(bool_as_int).decision == ToolDecision.DENY

    pure = ToolProposal("p1", "math.add", {"a": 1, "b": 2}, "a" * 64)
    admission = broker.admit(pure)
    assert admission.decision == ToolDecision.ALLOW
    assert broker.execute(admission, lambda: 3).output == 3
    with pytest.raises(ReplayError):
        broker.execute(admission, lambda: 3)

    side = ToolProposal("p2", "calendar.create", {"title": "sync"}, "b" * 64)
    assert broker.admit(side).decision == ToolDecision.DENY
    assert broker.admit(side, authority=frozenset({"calendar.create"})).decision == ToolDecision.REQUIRE_CONFIRMATION
    assert broker.admit(side, authority=frozenset({"calendar.create"}), confirmed=True).decision == ToolDecision.DENY
    allowed = broker.admit(side, authority=frozenset({"calendar.create"}), confirmed=True, idempotency_key="idem-1")
    assert allowed.decision == ToolDecision.ALLOW


def test_sandbox_policy_rejects_origin_network_storage_bridge_hardware_and_weak_csp(tmp_path: Path) -> None:
    registry, ref = admitted_registry()
    runner = SandboxRunner(strict_policy(), instance_root=tmp_path / "instances")
    cases = [
        replace(request(ref, "o1"), skill_ref=replace(ref, source_uri="https://evil.example/skill")),
        request(ref, "o2", requested_network_origins=("https://api.example",)),
        request(ref, "o3", request_storage=True),
        request(ref, "o4", requested_bridges=("native.shell",)),
        request(ref, "o5", request_camera=True),
        request(ref, "o6", request_microphone=True),
        request(ref, "o7", csp="default-src *; script-src 'unsafe-eval'"),
        request(ref, "o8", payload={"secret": "secret-handle-1"}),
        request(ref, "o9", script_name="../escape.js"),
    ]
    for item in cases:
        with pytest.raises(Exception):
            runner.run(item, lambda payload, secret, instance: {"result": "never"})
    runner.close()


def test_success_timeout_crash_secret_echo_malformed_oversize_replay_and_cleanup(tmp_path: Path) -> None:
    registry, ref = admitted_registry()
    runner = SandboxRunner(strict_policy(timeout_ms=5000, max_output_bytes=64), instance_root=tmp_path / "instances")

    result = runner.run(request(ref, "s1"), _success_executor)
    assert result.state == SandboxState.SUCCEEDED
    assert result.output == "sync"
    assert result.cleanup_complete is True
    assert list((tmp_path / "instances").iterdir()) == []
    assert "secret-handle-1" not in json.dumps(asdict(result), sort_keys=True)
    with pytest.raises(ReplayError):
        runner.run(request(ref, "s1"), _success_executor)

    timeout_runner = SandboxRunner(strict_policy(timeout_ms=100, max_output_bytes=64), instance_root=tmp_path / "timeout-instances")
    timeout = timeout_runner.run(request(ref, "s2"), _slow_executor)
    assert timeout.state == SandboxState.TIMED_OUT
    assert timeout.cleanup_complete is True
    assert list((tmp_path / "timeout-instances").iterdir()) == []
    timeout_runner.close()

    crash = runner.run(request(ref, "s3"), _crash_executor)
    assert crash.state == SandboxState.FAILED
    assert crash.cleanup_complete is True

    echo = runner.run(request(ref, "s4"), _echo_executor)
    assert echo.state == SandboxState.FAILED
    assert echo.error_code == "PolicyError"

    malformed = runner.run(request(ref, "s5"), _malformed_executor)
    assert malformed.state == SandboxState.FAILED

    oversized = runner.run(request(ref, "s6"), _oversized_executor)
    assert oversized.state == SandboxState.FAILED
    runner.close()


def test_candidate_receipt_keeps_native_and_human_lanes_open() -> None:
    receipt = json.loads((ROOT / "skills/receipts/p5-candidate.json").read_text(encoding="utf-8"))
    assert receipt["evidence"]["LIVE_DEVICE"] == "NOT_EXERCISED"
    assert receipt["evidence"]["REMOTE_CODE_TRUST"] == "HUMAN_ADMIT_REQUIRED"
    assert receipt["evidence"]["WEBVIEW_EXPLOIT_RESISTANCE"] == "NOT_EXERCISED"
    assert receipt["evidence"]["SECRET_CARRIER"] == "PRIVATE_NOT_EXERCISED"


def test_public_skill_tree_has_no_secret_or_private_workspace_values() -> None:
    for path in (ROOT / "skills").rglob("*"):
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
            text = path.read_text(encoding="utf-8")
            assert "docs" + ".google.com/" not in text
            assert "drive" + ".google.com/" not in text
            assert "BEGIN " + "PRIVATE KEY" not in text
