from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Mapping


class TrustState(StrEnum):
    TRUSTED = "TRUSTED"
    UNTRUSTED = "UNTRUSTED"
    REJECTED = "REJECTED"


class ToolEffect(StrEnum):
    PURE = "PURE"
    READ_LOCAL = "READ_LOCAL"
    WRITE_LOCAL = "WRITE_LOCAL"
    EXTERNAL_SIDE_EFFECT = "EXTERNAL_SIDE_EFFECT"


class ToolDecision(StrEnum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_CONFIRMATION = "REQUIRE_CONFIRMATION"


class SandboxState(StrEnum):
    SUCCEEDED = "SUCCEEDED"
    DENIED = "DENIED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True, slots=True)
class SkillMetadata:
    skill_id: str
    version: str
    description: str
    source_uri: str
    source_sha256: str
    manifest_sha256: str
    required_tools: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class SkillPackageRef:
    skill_id: str
    version: str
    source_uri: str
    source_sha256: str
    manifest_sha256: str
    trust_state: TrustState
    required_tools: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RouteDecision:
    query: str
    selected_skill_id: str | None
    candidate_skill_ids: tuple[str, ...]
    ambiguous: bool
    scores: Mapping[str, int]


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    tool_name: str
    effect: ToolEffect
    required_arguments: Mapping[str, type]
    optional_arguments: Mapping[str, type] = field(default_factory=dict)
    requires_confirmation: bool = False
    idempotency_required: bool = False


@dataclass(frozen=True, slots=True)
class ToolProposal:
    proposal_id: str
    tool_name: str
    arguments: Mapping[str, Any]
    model_output_digest: str


@dataclass(frozen=True, slots=True)
class ToolAdmission:
    proposal_id: str
    decision: ToolDecision
    policy_reason: str
    admitted_effect: ToolEffect
    idempotency_key: str | None = None


@dataclass(frozen=True, slots=True)
class ToolResult:
    proposal_id: str
    state: str
    output: Any = None
    error_code: str | None = None


@dataclass(frozen=True, slots=True)
class SandboxPolicy:
    allowed_origins: frozenset[str]
    allowed_network_origins: frozenset[str] = frozenset()
    allowed_bridges: frozenset[str] = frozenset()
    allow_storage: bool = False
    allow_camera: bool = False
    allow_microphone: bool = False
    max_input_bytes: int = 64_000
    max_output_bytes: int = 256_000
    timeout_ms: int = 1_000
    require_strict_csp: bool = True


@dataclass(frozen=True, slots=True)
class SandboxExecutionRequest:
    execution_id: str
    skill_ref: SkillPackageRef
    script_name: str
    payload: Mapping[str, Any]
    csp: str
    requested_network_origins: tuple[str, ...] = ()
    requested_bridges: tuple[str, ...] = ()
    request_storage: bool = False
    request_camera: bool = False
    request_microphone: bool = False
    secret_handle: str | None = None


@dataclass(frozen=True, slots=True)
class SandboxExecutionResult:
    execution_id: str
    skill_id: str
    source_sha256: str
    state: SandboxState
    output: Any = None
    error_code: str | None = None
    cleanup_complete: bool = False
