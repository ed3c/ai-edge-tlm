from __future__ import annotations

from typing import Any

from .manifest import ModelManifest


def generate_notice(manifest: ModelManifest) -> str:
    lines = [
        f"Model logical id: {manifest.logical_id}",
        f"Version: {manifest.version}",
        f"Source revision: {manifest.source_revision}",
        f"License plane: {manifest.license_plane.value}",
        f"Terms state: {manifest.terms_state.value}",
        f"Artifact SHA-256: {manifest.artifact_sha256}",
        f"Tokenizer SHA-256: {manifest.tokenizer_sha256}",
    ]
    lines.extend(f"Notice: {entry}" for entry in manifest.notice_entries)
    return "\n".join(lines) + "\n"


def generate_sbom_entry(manifest: ModelManifest) -> dict[str, Any]:
    return {
        "schema": "ai-edge-tlm/model-sbom-entry/v1",
        "logical_id": manifest.logical_id,
        "version": manifest.version,
        "artifact_format": manifest.artifact_format.value,
        "artifact_sha256": manifest.artifact_sha256,
        "tokenizer_sha256": manifest.tokenizer_sha256,
        "manifest_sha256": manifest.manifest_sha256,
        "runtime_id": manifest.runtime_id,
        "min_runtime_version": manifest.min_runtime_version,
        "license_plane": manifest.license_plane.value,
        "terms_state": manifest.terms_state.value,
        "source_revision": manifest.source_revision,
    }
