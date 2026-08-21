from __future__ import annotations

import re
from enum import StrEnum
from typing import Any


class Classification(StrEnum):
    PUBLIC_TECHNICAL = "PUBLIC_TECHNICAL"
    PRIVATE = "PRIVATE"
    SECRET = "SECRET"
    HUMAN = "HUMAN"
    UNKNOWN = "UNKNOWN"


CAPSULE_ALLOWLIST = frozenset(
    {
        "architecture_decisions",
        "technical_constraints",
        "non_goals",
        "source_ids",
        "prompt_contract_id",
        "required_evidence_lanes",
    }
)
PRIVATE_FIELDS = frozenset(
    {
        "commercial_intent",
        "product_positioning",
        "roadmap",
        "prompt_history",
        "private_dataset",
        "user_data",
        "private_source_packet",
        "workspace_url",
        "control_plane_uri",
        "ledger_uri",
        "model_access_grant",
    }
)
HUMAN_FIELDS = frozenset(
    {
        "legal_acceptance",
        "terms_acceptance",
        "merge_approval",
        "release_approval",
        "store_publication",
        "production_rollback",
    }
)
SECRET_FRAGMENTS = (
    "token",
    "password",
    "secret",
    "cookie",
    "credential",
    "private_key",
    "signing_key",
    "api_key",
)
WORKSPACE_URL = re.compile(r"https://(?:docs|drive)\.google\.com/", re.IGNORECASE)
SECRET_VALUE_PATTERNS = (
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{8,}", re.IGNORECASE),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
)


def normalize_field(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")


def classify_field(name: str) -> Classification:
    normalized = normalize_field(name)
    if any(fragment in normalized for fragment in SECRET_FRAGMENTS):
        return Classification.SECRET
    if normalized in HUMAN_FIELDS:
        return Classification.HUMAN
    if normalized in PRIVATE_FIELDS:
        return Classification.PRIVATE
    if normalized in CAPSULE_ALLOWLIST:
        return Classification.PUBLIC_TECHNICAL
    return Classification.UNKNOWN


def _walk(value: Any, path: str = "$"):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from _walk(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk(item, f"{path}[{index}]")
    elif isinstance(value, str):
        yield path, value


def find_forbidden_values(value: Any) -> list[str]:
    failures: list[str] = []
    for path, text in _walk(value):
        if WORKSPACE_URL.search(text):
            failures.append(f"{path}: private Workspace URL")
        for pattern in SECRET_VALUE_PATTERNS:
            if pattern.search(text):
                failures.append(f"{path}: secret-like value")
                break
    return failures
