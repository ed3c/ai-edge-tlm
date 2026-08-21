from __future__ import annotations

import hashlib
import json
import re
from urllib.parse import urlparse
from typing import Any, Mapping

from .errors import IntegrityError
from .types import SkillMetadata, SkillPackageRef, TrustState

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SKILL_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
_VERSION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,63}$")


def canonical_manifest_bytes(manifest: Mapping[str, Any]) -> bytes:
    try:
        return json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise IntegrityError("skill manifest is not canonical JSON") from exc


def canonical_manifest_digest(manifest: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_manifest_bytes(manifest)).hexdigest()


class PackageVerifier:
    """Verifies immutable package identity without granting execution trust."""

    def __init__(self, allowed_origins: set[str] | frozenset[str]) -> None:
        self.allowed_origins = frozenset(self.origin(value) for value in allowed_origins)

    @staticmethod
    def origin(uri: str) -> str:
        parsed = urlparse(uri)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise IntegrityError("skill source must use an absolute credential-free HTTPS origin")
        port = f":{parsed.port}" if parsed.port else ""
        return f"{parsed.scheme}://{parsed.hostname.casefold()}{port}"

    def verify(self, metadata: SkillMetadata, manifest: Mapping[str, Any], source_bytes: bytes) -> SkillPackageRef:
        if self.origin(metadata.source_uri) not in self.allowed_origins:
            raise IntegrityError("skill origin is not allowlisted")
        if not _SKILL_ID.fullmatch(metadata.skill_id):
            raise IntegrityError("invalid skill id")
        if not _VERSION.fullmatch(metadata.version):
            raise IntegrityError("invalid skill version")
        if not metadata.description.strip() or len(metadata.description.encode("utf-8")) > 2_048:
            raise IntegrityError("invalid skill description")
        if not _SHA256.fullmatch(metadata.source_sha256) or not _SHA256.fullmatch(metadata.manifest_sha256):
            raise IntegrityError("invalid skill digest")
        if len(source_bytes) == 0:
            raise IntegrityError("skill package is empty")
        source_digest = hashlib.sha256(source_bytes).hexdigest()
        if source_digest != metadata.source_sha256:
            raise IntegrityError("skill package digest mismatch")
        manifest_digest = canonical_manifest_digest(manifest)
        if manifest_digest != metadata.manifest_sha256:
            raise IntegrityError("skill manifest digest mismatch")
        expected = {
            "skill_id": metadata.skill_id,
            "version": metadata.version,
            "description": metadata.description,
            "source_uri": metadata.source_uri,
            "source_sha256": metadata.source_sha256,
            "required_tools": list(metadata.required_tools),
        }
        if dict(manifest) != expected:
            raise IntegrityError("manifest content does not match signed metadata")
        return SkillPackageRef(
            skill_id=metadata.skill_id,
            version=metadata.version,
            source_uri=metadata.source_uri,
            source_sha256=metadata.source_sha256,
            manifest_sha256=metadata.manifest_sha256,
            trust_state=TrustState.UNTRUSTED,
            required_tools=metadata.required_tools,
        )
