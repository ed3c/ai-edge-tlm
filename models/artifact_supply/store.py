from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import threading
import uuid
from typing import BinaryIO

from .errors import ActivationInterrupted, CompatibilityError, DowngradeError, IntegrityError
from .manifest import ArtifactFormat, ModelManifest
from .notice import generate_notice, generate_sbom_entry


def _version_tuple(value: str) -> tuple[int, ...]:
    parts = value.split(".")
    try:
        return tuple(int(part) for part in parts)
    except ValueError as exc:
        raise CompatibilityError(f"runtime version is not numeric: {value}") from exc


def _atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


@dataclass(frozen=True, slots=True)
class AdmissionReceipt:
    logical_id: str
    version: str
    release_sequence: int
    artifact_sha256: str
    tokenizer_sha256: str
    manifest_sha256: str
    active_pointer: str
    previous_artifact_sha256: str | None
    state: str = "ACTIVATED"


@dataclass(frozen=True, slots=True)
class RollbackReceipt:
    logical_id: str
    from_artifact_sha256: str
    to_artifact_sha256: str
    state: str = "ROLLED_BACK"


class ModelArtifactStore:
    """Content-addressed local model store with quarantine and atomic activation."""

    def __init__(self, root: Path, *, max_artifact_bytes: int = 2_000_000_000) -> None:
        self.root = Path(root)
        self.max_artifact_bytes = max_artifact_bytes
        self.quarantine = self.root / "quarantine"
        self.objects = self.root / "objects"
        self.active = self.root / "active"
        self.history = self.root / "history"
        self.receipts = self.root / "receipts"
        for directory in (self.quarantine, self.objects, self.active, self.history, self.receipts):
            directory.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

    def admit(
        self,
        manifest: ModelManifest,
        artifact: BinaryIO,
        tokenizer: BinaryIO,
        *,
        runtime_id: str,
        runtime_version: str,
        allow_synthetic_not_required: bool = False,
        interrupt_before_pointer: bool = False,
    ) -> AdmissionReceipt:
        manifest.validate(allow_synthetic_not_required=allow_synthetic_not_required)
        if runtime_id != manifest.runtime_id:
            raise CompatibilityError("runtime id mismatch")
        if _version_tuple(runtime_version) < _version_tuple(manifest.min_runtime_version):
            raise CompatibilityError("runtime version is below manifest minimum")

        with self._lock:
            current = self.active_manifest(manifest.logical_id)
            if current is not None:
                if manifest.release_sequence < current["release_sequence"]:
                    raise DowngradeError("release sequence downgrade")
                if manifest.logical_version == f"{current['logical_id']}@{current['version']}" and manifest.artifact_sha256 != current["artifact_sha256"]:
                    raise DowngradeError("logical version already exists with different bytes")

            token = uuid.uuid4().hex
            qdir = self.quarantine / token
            qdir.mkdir(parents=False, exist_ok=False)
            artifact_path = qdir / "artifact.bin"
            tokenizer_path = qdir / "tokenizer.bin"
            try:
                artifact_size, artifact_digest = self._copy_and_hash(artifact, artifact_path)
                tokenizer_size, tokenizer_digest = self._copy_and_hash(tokenizer, tokenizer_path)
                if artifact_size != manifest.artifact_size:
                    raise IntegrityError("artifact size mismatch")
                if artifact_digest != manifest.artifact_sha256:
                    raise IntegrityError("artifact digest mismatch")
                if tokenizer_size == 0 or tokenizer_digest != manifest.tokenizer_sha256:
                    raise IntegrityError("tokenizer digest mismatch")
                self._validate_format(manifest.artifact_format, artifact_path)

                object_dir = self.objects / manifest.artifact_sha256
                if not object_dir.exists():
                    staged = self.objects / f".{manifest.artifact_sha256}.{token}.tmp"
                    staged.mkdir(parents=False, exist_ok=False)
                    shutil.copyfile(artifact_path, staged / "artifact.bin")
                    shutil.copyfile(tokenizer_path, staged / "tokenizer.bin")
                    (staged / "manifest.json").write_bytes(manifest.canonical_bytes() + b"\n")
                    (staged / "NOTICE.txt").write_text(generate_notice(manifest), encoding="utf-8")
                    _atomic_json(staged / "sbom.json", generate_sbom_entry(manifest))
                    os.replace(staged, object_dir)
                else:
                    self._verify_object(object_dir, manifest)

                previous_digest = current["artifact_sha256"] if current else None
                if interrupt_before_pointer:
                    raise ActivationInterrupted("simulated interruption before active pointer")

                pointer = {
                    "schema": "ai-edge-tlm/model-active-pointer/v1",
                    "logical_id": manifest.logical_id,
                    "version": manifest.version,
                    "release_sequence": manifest.release_sequence,
                    "artifact_sha256": manifest.artifact_sha256,
                    "tokenizer_sha256": manifest.tokenizer_sha256,
                    "manifest_sha256": manifest.manifest_sha256,
                    "object_path": f"objects/{manifest.artifact_sha256}",
                    "previous_artifact_sha256": previous_digest,
                }
                active_path = self.active / f"{manifest.logical_id}.json"
                history_path = self.history / f"{manifest.logical_id}.json"
                receipt_path = self.receipts / f"admit-{manifest.logical_id}-{manifest.artifact_sha256[:12]}.json"
                history_before = self._history_entries(manifest.logical_id)
                receipt = AdmissionReceipt(
                    logical_id=manifest.logical_id,
                    version=manifest.version,
                    release_sequence=manifest.release_sequence,
                    artifact_sha256=manifest.artifact_sha256,
                    tokenizer_sha256=manifest.tokenizer_sha256,
                    manifest_sha256=manifest.manifest_sha256,
                    active_pointer=str(active_path),
                    previous_artifact_sha256=previous_digest,
                )
                try:
                    _atomic_json(active_path, pointer)
                    _atomic_json(history_path, [*history_before, pointer])
                    _atomic_json(receipt_path, asdict(receipt))
                except Exception:
                    if current is None:
                        active_path.unlink(missing_ok=True)
                    else:
                        _atomic_json(active_path, current)
                    if history_before:
                        _atomic_json(history_path, history_before)
                    else:
                        history_path.unlink(missing_ok=True)
                    receipt_path.unlink(missing_ok=True)
                    raise
                return receipt
            finally:
                shutil.rmtree(qdir, ignore_errors=True)

    def rollback(self, logical_id: str) -> RollbackReceipt:
        with self._lock:
            entries = self._history_entries(logical_id)
            if len(entries) < 2:
                raise DowngradeError("no previous admitted artifact")
            current = entries[-1]
            previous = entries[-2]
            previous_object = self.objects / previous["artifact_sha256"]
            if not previous_object.is_dir():
                raise IntegrityError("rollback object is missing")
            stored_manifest = ModelManifest.from_dict(json.loads((previous_object / "manifest.json").read_text(encoding="utf-8")))
            self._verify_object(previous_object, stored_manifest)
            active_path = self.active / f"{logical_id}.json"
            history_path = self.history / f"{logical_id}.json"
            receipt_path = self.receipts / f"rollback-{logical_id}-{current['artifact_sha256'][:12]}.json"
            updated_entries = [*entries, {**previous, "rollback_from": current["artifact_sha256"]}]
            receipt = RollbackReceipt(logical_id, current["artifact_sha256"], previous["artifact_sha256"])
            try:
                _atomic_json(active_path, previous)
                _atomic_json(history_path, updated_entries)
                _atomic_json(receipt_path, asdict(receipt))
            except Exception:
                _atomic_json(active_path, current)
                _atomic_json(history_path, entries)
                receipt_path.unlink(missing_ok=True)
                raise
            return receipt

    def active_manifest(self, logical_id: str) -> dict[str, object] | None:
        path = self.active / f"{logical_id}.json"
        if not path.is_file():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _hash_file(path: Path) -> tuple[int, str]:
        digest = hashlib.sha256()
        total = 0
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(64 * 1024), b""):
                total += len(chunk)
                digest.update(chunk)
        return total, digest.hexdigest()

    def _verify_object(self, object_dir: Path, manifest: ModelManifest) -> None:
        required = [object_dir / "artifact.bin", object_dir / "tokenizer.bin", object_dir / "manifest.json", object_dir / "NOTICE.txt", object_dir / "sbom.json"]
        if any(not path.is_file() for path in required):
            raise IntegrityError("existing object is incomplete")
        stored = json.loads((object_dir / "manifest.json").read_text(encoding="utf-8"))
        if stored != manifest.to_dict():
            raise IntegrityError("existing object identity conflict")
        artifact_size, artifact_digest = self._hash_file(object_dir / "artifact.bin")
        tokenizer_size, tokenizer_digest = self._hash_file(object_dir / "tokenizer.bin")
        if artifact_size != manifest.artifact_size or artifact_digest != manifest.artifact_sha256:
            raise IntegrityError("stored artifact identity conflict")
        if tokenizer_size == 0 or tokenizer_digest != manifest.tokenizer_sha256:
            raise IntegrityError("stored tokenizer identity conflict")
        self._validate_format(manifest.artifact_format, object_dir / "artifact.bin")
        sbom = json.loads((object_dir / "sbom.json").read_text(encoding="utf-8"))
        if sbom.get("manifest_sha256") != manifest.manifest_sha256:
            raise IntegrityError("stored SBOM identity conflict")

    def _copy_and_hash(self, source: BinaryIO, target: Path) -> tuple[int, str]:
        digest = hashlib.sha256()
        total = 0
        with target.open("wb") as handle:
            while True:
                chunk = source.read(64 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > self.max_artifact_bytes:
                    raise IntegrityError("artifact exceeds configured size limit")
                digest.update(chunk)
                handle.write(chunk)
            handle.flush()
            os.fsync(handle.fileno())
        return total, digest.hexdigest()

    @staticmethod
    def _validate_format(artifact_format: ArtifactFormat, path: Path) -> None:
        with path.open("rb") as handle:
            prefix = handle.read(8)
        if artifact_format == ArtifactFormat.LITERTLM and not prefix.startswith(b"LRTLM\x00"):
            raise IntegrityError("invalid synthetic LiteRT-LM magic")
        if artifact_format == ArtifactFormat.TASK and not prefix.startswith(b"TASK\x00"):
            raise IntegrityError("invalid synthetic task magic")

    def _append_history(self, logical_id: str, pointer: dict[str, object]) -> None:
        entries = self._history_entries(logical_id)
        entries.append(pointer)
        _atomic_json(self.history / f"{logical_id}.json", entries)

    def _history_entries(self, logical_id: str) -> list[dict[str, object]]:
        path = self.history / f"{logical_id}.json"
        if not path.is_file():
            return []
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, list):
            raise IntegrityError("history ledger is malformed")
        return value
