from __future__ import annotations

import re
import threading
from typing import Any, Callable

from .errors import PolicyError, ReplayError
from .types import ToolAdmission, ToolDecision, ToolDefinition, ToolEffect, ToolProposal, ToolResult

_NAME = re.compile(r"^[a-z][a-z0-9_.-]{0,127}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class ToolBroker:
    def __init__(self, definitions: list[ToolDefinition]) -> None:
        self._definitions = {item.tool_name: item for item in definitions}
        if len(self._definitions) != len(definitions):
            raise ValueError("duplicate tool definition")
        for definition in definitions:
            if not _NAME.fullmatch(definition.tool_name):
                raise ValueError("invalid tool name")
            if set(definition.required_arguments) & set(definition.optional_arguments):
                raise ValueError("tool argument cannot be both required and optional")
        self._executed: set[str] = set()
        self._lock = threading.RLock()

    def admit(
        self,
        proposal: ToolProposal,
        *,
        authority: frozenset[str] = frozenset(),
        confirmed: bool = False,
        idempotency_key: str | None = None,
    ) -> ToolAdmission:
        if not proposal.proposal_id.strip() or len(proposal.proposal_id) > 128:
            return ToolAdmission(proposal.proposal_id, ToolDecision.DENY, "invalid proposal id", ToolEffect.PURE)
        if not _SHA256.fullmatch(proposal.model_output_digest):
            return ToolAdmission(proposal.proposal_id, ToolDecision.DENY, "invalid model output digest", ToolEffect.PURE)
        definition = self._definitions.get(proposal.tool_name)
        if definition is None:
            return ToolAdmission(proposal.proposal_id, ToolDecision.DENY, "unknown tool", ToolEffect.PURE)
        error = self._validate_arguments(definition, proposal.arguments)
        if error:
            return ToolAdmission(proposal.proposal_id, ToolDecision.DENY, error, definition.effect)
        if definition.effect != ToolEffect.PURE and proposal.tool_name not in authority:
            return ToolAdmission(proposal.proposal_id, ToolDecision.DENY, "host authority missing", definition.effect)
        if definition.requires_confirmation and not confirmed:
            return ToolAdmission(proposal.proposal_id, ToolDecision.REQUIRE_CONFIRMATION, "user confirmation required", definition.effect)
        if definition.idempotency_required and not idempotency_key:
            return ToolAdmission(proposal.proposal_id, ToolDecision.DENY, "idempotency key required", definition.effect)
        if idempotency_key is not None and (not idempotency_key.strip() or len(idempotency_key) > 256):
            return ToolAdmission(proposal.proposal_id, ToolDecision.DENY, "invalid idempotency key", definition.effect)
        return ToolAdmission(proposal.proposal_id, ToolDecision.ALLOW, "host policy admitted", definition.effect, idempotency_key)

    def execute(self, admission: ToolAdmission, handler: Callable[[], Any]) -> ToolResult:
        if admission.decision != ToolDecision.ALLOW:
            raise PolicyError("tool execution requires ALLOW admission")
        replay_key = admission.idempotency_key or admission.proposal_id
        with self._lock:
            if replay_key in self._executed:
                raise ReplayError("tool execution replay")
            # Reserve before invoking a side effect. A failed/uncertain handler is not retried
            # under the same identity without a separate host reconciliation decision.
            self._executed.add(replay_key)
        try:
            return ToolResult(admission.proposal_id, "SUCCEEDED", output=handler())
        except Exception as exc:  # noqa: BLE001 - typed boundary
            return ToolResult(admission.proposal_id, "FAILED", error_code=type(exc).__name__)

    @staticmethod
    def _validate_arguments(definition: ToolDefinition, arguments: Any) -> str | None:
        if not isinstance(arguments, dict):
            return "arguments must be an object"
        allowed = set(definition.required_arguments) | set(definition.optional_arguments)
        if set(arguments) - allowed:
            return "unknown argument"
        for name, expected in definition.required_arguments.items():
            if name not in arguments:
                return f"missing argument: {name}"
            if type(arguments[name]) is not expected:
                return f"invalid argument type: {name}"
        for name, expected in definition.optional_arguments.items():
            if name in arguments and type(arguments[name]) is not expected:
                return f"invalid argument type: {name}"
        return None
