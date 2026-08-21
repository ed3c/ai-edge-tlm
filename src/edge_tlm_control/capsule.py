from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Mapping, Sequence

from .classification import CAPSULE_ALLOWLIST, Classification, classify_field, find_forbidden_values

CONTEXT_ID = "CDX-AI-EDGE-001"
MAX_CAPSULE_BYTES = 4096
MAX_TTL_SECONDS = 3600
MAX_LIST_ITEMS = 32
MAX_STRING_BYTES = 2048


class CapsuleError(ValueError):
    pass


@dataclass(frozen=True)
class ContextRequest:
    context_id: str
    task_id: str
    repository_subject: str
    requested_fields: tuple[str, ...]
    max_bytes: int = MAX_CAPSULE_BYTES
    ttl_seconds: int = 900

    @classmethod
    def create(
        cls,
        *,
        task_id: str,
        repository_subject: str,
        requested_fields: Sequence[str],
        context_id: str = CONTEXT_ID,
        max_bytes: int = MAX_CAPSULE_BYTES,
        ttl_seconds: int = 900,
    ) -> "ContextRequest":
        return cls(context_id, task_id, repository_subject, tuple(requested_fields), max_bytes, ttl_seconds)


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest_without_sha(capsule: Mapping[str, Any]) -> str:
    body = dict(capsule)
    body.pop("sha256", None)
    return hashlib.sha256(_canonical(body)).hexdigest()


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _parse_iso(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise CapsuleError("timestamp must include a timezone")
    return parsed.astimezone(UTC)


def _validate_scalar(field: str, value: Any) -> str | list[str]:
    if isinstance(value, str):
        if len(value.encode("utf-8")) > MAX_STRING_BYTES:
            raise CapsuleError(f"{field}: string exceeds {MAX_STRING_BYTES} bytes")
        return value
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        if len(value) > MAX_LIST_ITEMS:
            raise CapsuleError(f"{field}: list exceeds {MAX_LIST_ITEMS} items")
        for item in value:
            if len(item.encode("utf-8")) > MAX_STRING_BYTES:
                raise CapsuleError(f"{field}: list item exceeds {MAX_STRING_BYTES} bytes")
        return list(value)
    raise CapsuleError(f"{field}: only string or list[string] values are allowed")


def _validate_request(request: ContextRequest) -> None:
    if request.context_id != CONTEXT_ID:
        raise CapsuleError("unknown context_id")
    if not request.task_id or len(request.task_id) > 128:
        raise CapsuleError("task_id must be 1..128 characters")
    if len(request.repository_subject) != 40 or any(ch not in "0123456789abcdef" for ch in request.repository_subject):
        raise CapsuleError("repository_subject must be a lowercase SHA-40")
    if not request.requested_fields:
        raise CapsuleError("requested_fields must be non-empty")
    if len(set(request.requested_fields)) != len(request.requested_fields):
        raise CapsuleError("requested_fields must be unique")
    for field in request.requested_fields:
        if classify_field(field) is not Classification.PUBLIC_TECHNICAL:
            raise CapsuleError(f"{field}: field is not capsule-allowlisted")
    if request.max_bytes < 256 or request.max_bytes > MAX_CAPSULE_BYTES:
        raise CapsuleError(f"max_bytes must be between 256 and {MAX_CAPSULE_BYTES}")
    if request.ttl_seconds < 1 or request.ttl_seconds > MAX_TTL_SECONDS:
        raise CapsuleError(f"ttl_seconds must be between 1 and {MAX_TTL_SECONDS}")


def build_capsule(
    private_context: Mapping[str, Any],
    request: ContextRequest,
    *,
    issued_at: datetime | None = None,
) -> dict[str, Any]:
    _validate_request(request)
    issued = issued_at or datetime.now(UTC)
    expires = issued + timedelta(seconds=request.ttl_seconds)
    selected: dict[str, Any] = {}
    for field in request.requested_fields:
        if field not in private_context:
            continue
        selected[field] = _validate_scalar(field, private_context[field])
    forbidden = find_forbidden_values(selected)
    if forbidden:
        raise CapsuleError("DLP rejected capsule: " + "; ".join(forbidden))
    capsule: dict[str, Any] = {
        "schema": "ai-edge-tlm/context-capsule/v1",
        "context_id": request.context_id,
        "task_id": request.task_id,
        "repository_subject": request.repository_subject,
        "issued_at": _iso(issued),
        "expires_at": _iso(expires),
        "fields": selected,
    }
    capsule["sha256"] = _digest_without_sha(capsule)
    if len(_canonical(capsule)) > request.max_bytes:
        raise CapsuleError("capsule exceeds request max_bytes")
    return capsule


def verify_capsule(
    capsule: Mapping[str, Any],
    *,
    expected_task_id: str,
    expected_repository_subject: str,
    now: datetime | None = None,
    max_bytes: int = MAX_CAPSULE_BYTES,
) -> dict[str, Any]:
    if max_bytes < 256 or max_bytes > MAX_CAPSULE_BYTES:
        raise CapsuleError(f"max_bytes must be between 256 and {MAX_CAPSULE_BYTES}")
    required = {"schema", "context_id", "task_id", "repository_subject", "issued_at", "expires_at", "fields", "sha256"}
    if set(capsule) != required:
        raise CapsuleError("capsule keys do not match the closed schema")
    if capsule.get("schema") != "ai-edge-tlm/context-capsule/v1" or capsule.get("context_id") != CONTEXT_ID:
        raise CapsuleError("unsupported capsule schema or context")
    if capsule.get("task_id") != expected_task_id:
        raise CapsuleError("cross-task capsule rejected")
    if capsule.get("repository_subject") != expected_repository_subject:
        raise CapsuleError("stale or wrong-subject capsule rejected")
    fields = capsule.get("fields")
    if not isinstance(fields, dict):
        raise CapsuleError("fields must be an object")
    if not set(fields).issubset(CAPSULE_ALLOWLIST):
        raise CapsuleError("capsule contains an unallowlisted field")
    for field, value in fields.items():
        _validate_scalar(field, value)
    forbidden = find_forbidden_values(fields)
    if forbidden:
        raise CapsuleError("DLP rejected capsule: " + "; ".join(forbidden))
    if len(_canonical(capsule)) > max_bytes:
        raise CapsuleError("capsule exceeds verifier max_bytes")
    if capsule.get("sha256") != _digest_without_sha(capsule):
        raise CapsuleError("capsule digest mismatch")
    issued = _parse_iso(str(capsule["issued_at"]))
    expires = _parse_iso(str(capsule["expires_at"]))
    instant = (now or datetime.now(UTC)).astimezone(UTC)
    if expires <= issued or (expires - issued).total_seconds() > MAX_TTL_SECONDS:
        raise CapsuleError("capsule TTL is invalid")
    if instant < issued or instant >= expires:
        raise CapsuleError("capsule is not active")
    return dict(capsule)
