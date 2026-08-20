from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from time import time


class RequestState(StrEnum):
    RECEIVED = "RECEIVED"
    CAPABILITY_PROBED = "CAPABILITY_PROBED"
    POLICY_EVALUATED = "POLICY_EVALUATED"
    PROVIDER_SELECTED = "PROVIDER_SELECTED"
    MODEL_READY = "MODEL_READY"
    SKILL_METADATA_MATCHED = "SKILL_METADATA_MATCHED"
    SKILL_LOADED = "SKILL_LOADED"
    PLAN_COMPILED = "PLAN_COMPILED"
    EXECUTING = "EXECUTING"
    VALIDATING = "VALIDATING"
    FALLBACK_EVALUATED = "FALLBACK_EVALUATED"
    SUCCEEDED = "SUCCEEDED"
    DEGRADED = "DEGRADED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


_ALLOWED: dict[RequestState, set[RequestState]] = {
    RequestState.RECEIVED: {RequestState.CAPABILITY_PROBED},
    RequestState.CAPABILITY_PROBED: {RequestState.POLICY_EVALUATED, RequestState.FALLBACK_EVALUATED},
    RequestState.POLICY_EVALUATED: {RequestState.PROVIDER_SELECTED, RequestState.REJECTED},
    RequestState.PROVIDER_SELECTED: {RequestState.MODEL_READY, RequestState.FALLBACK_EVALUATED},
    RequestState.MODEL_READY: {RequestState.SKILL_METADATA_MATCHED, RequestState.FALLBACK_EVALUATED},
    RequestState.SKILL_METADATA_MATCHED: {RequestState.SKILL_LOADED, RequestState.PLAN_COMPILED},
    RequestState.SKILL_LOADED: {RequestState.PLAN_COMPILED, RequestState.FALLBACK_EVALUATED},
    RequestState.PLAN_COMPILED: {RequestState.EXECUTING},
    RequestState.EXECUTING: {RequestState.VALIDATING, RequestState.FALLBACK_EVALUATED},
    RequestState.VALIDATING: {RequestState.SUCCEEDED, RequestState.FALLBACK_EVALUATED},
    RequestState.FALLBACK_EVALUATED: {RequestState.DEGRADED, RequestState.FAILED, RequestState.PROVIDER_SELECTED},
    RequestState.SUCCEEDED: set(),
    RequestState.DEGRADED: set(),
    RequestState.REJECTED: set(),
    RequestState.FAILED: set(),
}


@dataclass(frozen=True)
class TransitionReceipt:
    previous: RequestState
    current: RequestState
    reason: str
    timestamp_unix: float


class RequestStateMachine:
    def __init__(self) -> None:
        self.state = RequestState.RECEIVED
        self.receipts: list[TransitionReceipt] = []

    def transition(self, next_state: RequestState, reason: str) -> TransitionReceipt:
        if next_state not in _ALLOWED[self.state]:
            raise ValueError(f"invalid transition {self.state} -> {next_state}")
        receipt = TransitionReceipt(self.state, next_state, reason, time())
        self.state = next_state
        self.receipts.append(receipt)
        return receipt
