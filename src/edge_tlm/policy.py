from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Iterable


class PolicyDecision(StrEnum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    NO_PROVIDER = "NO_PROVIDER"


@dataclass(frozen=True)
class Requirements:
    offline_required: bool
    privacy: str
    side_effects_allowed: bool
    required_modalities: frozenset[str] = frozenset({"text"})
    preferred_provider: str | None = None


@dataclass(frozen=True)
class ProviderCandidate:
    provider_id: str
    available: bool
    local: bool
    modalities: frozenset[str]
    maturity: str
    priority: int


@dataclass(frozen=True)
class Selection:
    decision: PolicyDecision
    provider: ProviderCandidate | None
    rejected: tuple[str, ...]


def select_provider(requirements: Requirements, candidates: Iterable[ProviderCandidate]) -> Selection:
    rejected: list[str] = []
    admitted: list[ProviderCandidate] = []
    for candidate in candidates:
        if not candidate.available:
            rejected.append(f"{candidate.provider_id}: unavailable")
            continue
        if requirements.offline_required and not candidate.local:
            rejected.append(f"{candidate.provider_id}: violates offline requirement")
            continue
        if requirements.privacy in {"local-only", "sensitive"} and not candidate.local:
            rejected.append(f"{candidate.provider_id}: violates privacy requirement")
            continue
        if not requirements.required_modalities.issubset(candidate.modalities):
            rejected.append(f"{candidate.provider_id}: missing modality")
            continue
        admitted.append(candidate)

    if not admitted:
        return Selection(PolicyDecision.NO_PROVIDER, None, tuple(rejected))

    admitted.sort(key=lambda item: (item.provider_id != requirements.preferred_provider, item.priority, item.provider_id))
    return Selection(PolicyDecision.ALLOW, admitted[0], tuple(rejected))
