from __future__ import annotations

from dataclasses import dataclass, replace
import re
import threading
from typing import Any, Mapping

from .errors import IntegrityError, RoutingError
from .integrity import PackageVerifier
from .types import RouteDecision, SkillMetadata, SkillPackageRef, TrustState

_TOKEN = re.compile(r"[a-z0-9]+")


def _tokens(value: str) -> tuple[str, ...]:
    return tuple(_TOKEN.findall(value.casefold()))


@dataclass(frozen=True, slots=True)
class _StoredSkill:
    metadata: SkillMetadata
    ref: SkillPackageRef
    instructions: str
    trust_decision_id: str | None = None


class SkillRegistry:
    def __init__(self, verifier: PackageVerifier, *, max_index_skills: int = 32, max_index_chars: int = 8_192) -> None:
        if max_index_skills <= 0 or max_index_chars <= 0:
            raise ValueError("skill index budgets must be positive")
        self.verifier = verifier
        self.max_index_skills = max_index_skills
        self.max_index_chars = max_index_chars
        self._skills: dict[tuple[str, str], _StoredSkill] = {}
        self._lock = threading.RLock()

    def register(self, metadata: SkillMetadata, manifest: Mapping[str, Any], source_bytes: bytes, instructions: str) -> SkillPackageRef:
        if not instructions.strip():
            raise IntegrityError("skill instructions are empty")
        if len(instructions.encode("utf-8")) > 128_000:
            raise IntegrityError("skill instructions exceed package budget")
        ref = self.verifier.verify(metadata, manifest, source_bytes)
        key = (metadata.skill_id, metadata.version)
        with self._lock:
            existing = self._skills.get(key)
            if existing is not None:
                if existing.ref.source_sha256 != ref.source_sha256 or existing.ref.manifest_sha256 != ref.manifest_sha256 or existing.instructions != instructions:
                    raise IntegrityError("immutable skill version mutated")
                return existing.ref
            self._skills[key] = _StoredSkill(metadata, ref, instructions)
            return ref

    def admit_trust(self, skill_id: str, version: str, expected_ref: SkillPackageRef, *, policy_decision_id: str) -> SkillPackageRef:
        if not policy_decision_id.strip() or len(policy_decision_id) > 128:
            raise IntegrityError("explicit host trust decision id is required")
        key = (skill_id, version)
        with self._lock:
            stored = self._skills.get(key)
            if stored is None:
                raise RoutingError("skill not registered")
            if (
                stored.ref.skill_id != expected_ref.skill_id
                or stored.ref.version != expected_ref.version
                or stored.ref.source_sha256 != expected_ref.source_sha256
                or stored.ref.manifest_sha256 != expected_ref.manifest_sha256
                or expected_ref.trust_state != TrustState.UNTRUSTED
            ):
                raise IntegrityError("trust decision does not bind the verified package")
            trusted = replace(stored.ref, trust_state=TrustState.TRUSTED)
            self._skills[key] = replace(stored, ref=trusted, trust_decision_id=policy_decision_id)
            return trusted

    def prompt_index(self) -> str:
        with self._lock:
            admitted = [item for item in self._skills.values() if item.ref.trust_state == TrustState.TRUSTED]
            rows = [
                f"- {stored.metadata.skill_id}@{stored.metadata.version}: {stored.metadata.description}"
                for stored in sorted(admitted, key=lambda item: (item.metadata.skill_id, item.metadata.version))[: self.max_index_skills]
            ]
        value = "\n".join(rows)
        if len(value.encode("utf-8")) > self.max_index_chars:
            raise RoutingError("metadata prompt index exceeds byte budget")
        return value

    def route(self, query: str) -> RouteDecision:
        query_tokens = set(_tokens(query))
        with self._lock:
            admitted = tuple(item for item in self._skills.values() if item.ref.trust_state == TrustState.TRUSTED)
        scores: dict[str, int] = {}
        for stored in admitted:
            skill_tokens = set(_tokens(stored.metadata.skill_id.replace("-", " ")))
            description_tokens = set(_tokens(stored.metadata.description))
            score = 3 * len(query_tokens & skill_tokens) + len(query_tokens & description_tokens)
            current = scores.get(stored.metadata.skill_id)
            scores[stored.metadata.skill_id] = max(score, current or 0)
        ranked = sorted(scores, key=lambda skill_id: (-scores[skill_id], skill_id))
        if not ranked or scores[ranked[0]] == 0:
            return RouteDecision(query, None, tuple(), False, scores)
        top_score = scores[ranked[0]]
        top = tuple(skill_id for skill_id in ranked if scores[skill_id] == top_score)
        if len(top) > 1:
            return RouteDecision(query, None, top, True, scores)
        return RouteDecision(query, top[0], tuple(ranked), False, scores)

    def load_instructions(self, skill_id: str, version: str, admitted_ref: SkillPackageRef) -> str:
        with self._lock:
            stored = self._skills.get((skill_id, version))
            if stored is None:
                raise RoutingError("skill not registered")
            if stored.ref.trust_state != TrustState.TRUSTED or not stored.trust_decision_id:
                raise IntegrityError("skill trust has not been admitted by host policy")
            if admitted_ref != stored.ref:
                raise IntegrityError("skill reference is not the admitted immutable package")
            return stored.instructions
