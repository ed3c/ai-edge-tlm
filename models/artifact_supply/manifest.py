from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
import hashlib
import json
import re
from typing import Any

from .errors import ManifestError, TermsNotAdmitted

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{1,127}$")


class ArtifactFormat(StrEnum):
    LITERTLM = "LITERTLM"
    TASK = "TASK"
    COREML_PACKAGE = "COREML_PACKAGE"
    ONNX = "ONNX"
    OTHER = "OTHER"


class LicensePlane(StrEnum):
    SOURCE_CODE = "SOURCE_CODE"
    MODEL_WEIGHTS = "MODEL_WEIGHTS"
    DATASET = "DATASET"
    SERVICE = "SERVICE"
    SDK_STORE = "SDK_STORE"
    TRADEMARK = "TRADEMARK"
    EXPORT_CONTROL = "EXPORT_CONTROL"
    UNKNOWN = "UNKNOWN"


class TermsState(StrEnum):
    NOT_REQUIRED = "NOT_REQUIRED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    HUMAN_ADMIT_REQUIRED = "HUMAN_ADMIT_REQUIRED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


@dataclass(frozen=True, slots=True)
class ModelManifest:
    logical_id: str
    version: str
    release_sequence: int
    artifact_format: ArtifactFormat
    artifact_size: int
    artifact_sha256: str
    tokenizer_sha256: str
    runtime_id: str
    min_runtime_version: str
    license_plane: LicensePlane
    terms_state: TermsState
    source_revision: str
    notice_entries: tuple[str, ...] = field(default_factory=tuple)
    schema: str = "ai-edge-tlm/model-manifest/v1"

    def validate(self, *, allow_synthetic_not_required: bool = False) -> None:
        if self.schema != "ai-edge-tlm/model-manifest/v1":
            raise ManifestError("unsupported manifest schema")
        if not _ID.fullmatch(self.logical_id):
            raise ManifestError("invalid logical_id")
        if not self.version or len(self.version) > 64:
            raise ManifestError("invalid version")
        if self.release_sequence < 0:
            raise ManifestError("negative release sequence")
        if self.artifact_size <= 0:
            raise ManifestError("artifact_size must be positive")
        if not _SHA256.fullmatch(self.artifact_sha256):
            raise ManifestError("invalid artifact sha256")
        if not _SHA256.fullmatch(self.tokenizer_sha256):
            raise ManifestError("invalid tokenizer sha256")
        if not _ID.fullmatch(self.runtime_id):
            raise ManifestError("invalid runtime_id")
        if not self.min_runtime_version:
            raise ManifestError("missing minimum runtime version")
        if not self.source_revision or len(self.source_revision) > 256:
            raise ManifestError("invalid source revision")
        lowered = self.source_revision.casefold()
        if "docs.google.com" in lowered or "drive.google.com" in lowered or "sheets.google.com" in lowered:
            raise ManifestError("private workspace location is forbidden")
        if self.license_plane == LicensePlane.MODEL_WEIGHTS:
            if self.terms_state != TermsState.ACCEPTED:
                raise TermsNotAdmitted("model-weight terms require explicit ACCEPTED state")
        elif self.terms_state in {TermsState.REVIEW_REQUIRED, TermsState.HUMAN_ADMIT_REQUIRED, TermsState.REJECTED}:
            raise TermsNotAdmitted("terms state is not admitted")
        elif self.terms_state == TermsState.NOT_REQUIRED and not allow_synthetic_not_required:
            raise TermsNotAdmitted("NOT_REQUIRED is limited to explicitly admitted synthetic fixtures")

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "ModelManifest":
        try:
            return cls(
                logical_id=value["logical_id"],
                version=value["version"],
                release_sequence=value["release_sequence"],
                artifact_format=ArtifactFormat(value["artifact_format"]),
                artifact_size=value["artifact_size"],
                artifact_sha256=value["artifact_sha256"],
                tokenizer_sha256=value["tokenizer_sha256"],
                runtime_id=value["runtime_id"],
                min_runtime_version=value["min_runtime_version"],
                license_plane=LicensePlane(value["license_plane"]),
                terms_state=TermsState(value["terms_state"]),
                source_revision=value["source_revision"],
                notice_entries=tuple(value.get("notice_entries", ())),
                schema=value.get("schema", "ai-edge-tlm/model-manifest/v1"),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ManifestError("malformed model manifest") from exc

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["artifact_format"] = self.artifact_format.value
        value["license_plane"] = self.license_plane.value
        value["terms_state"] = self.terms_state.value
        value["notice_entries"] = list(self.notice_entries)
        return value

    def canonical_bytes(self) -> bytes:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

    @property
    def manifest_sha256(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()

    @property
    def logical_version(self) -> str:
        return f"{self.logical_id}@{self.version}"
