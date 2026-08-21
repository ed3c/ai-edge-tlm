from __future__ import annotations

from dataclasses import replace
from io import BytesIO
import hashlib
import json
from pathlib import Path

import pytest

from models.artifact_supply import ArtifactFormat, LicensePlane, ModelArtifactStore, ModelManifest, TermsState
from models.artifact_supply.errors import ActivationInterrupted, CompatibilityError, DowngradeError, IntegrityError, TermsNotAdmitted

ROOT = Path(__file__).resolve().parents[2]


def payload(label: bytes) -> bytes:
    return b"LRTLM\x00" + label * 16


def manifest(data: bytes, tokenizer: bytes, *, version: str = "1.0.0", sequence: int = 1, terms: TermsState = TermsState.ACCEPTED) -> ModelManifest:
    return ModelManifest(
        logical_id="calendar-function-model",
        version=version,
        release_sequence=sequence,
        artifact_format=ArtifactFormat.LITERTLM,
        artifact_size=len(data),
        artifact_sha256=hashlib.sha256(data).hexdigest(),
        tokenizer_sha256=hashlib.sha256(tokenizer).hexdigest(),
        runtime_id="litert-lm",
        min_runtime_version="0.16.0",
        license_plane=LicensePlane.MODEL_WEIGHTS,
        terms_state=terms,
        source_revision="public-model-revision-1",
        notice_entries=("Synthetic test bytes only",),
    )


def admit(store: ModelArtifactStore, m: ModelManifest, data: bytes, tokenizer: bytes, **kwargs):
    return store.admit(m, BytesIO(data), BytesIO(tokenizer), runtime_id="litert-lm", runtime_version="0.16.0", **kwargs)


def test_valid_synthetic_artifact_activates_and_receipt_binds_identity(tmp_path: Path) -> None:
    data, tokenizer = payload(b"a"), b"tokenizer-a"
    m = manifest(data, tokenizer)
    store = ModelArtifactStore(tmp_path)
    receipt = admit(store, m, data, tokenizer)
    active = store.active_manifest(m.logical_id)
    assert active is not None
    assert active["artifact_sha256"] == m.artifact_sha256
    assert active["tokenizer_sha256"] == m.tokenizer_sha256
    assert active["manifest_sha256"] == m.manifest_sha256
    assert receipt.previous_artifact_sha256 is None
    object_dir = tmp_path / "objects" / m.artifact_sha256
    assert (object_dir / "artifact.bin").read_bytes() == data
    assert "Synthetic test bytes only" in (object_dir / "NOTICE.txt").read_text(encoding="utf-8")
    assert json.loads((object_dir / "sbom.json").read_text(encoding="utf-8"))["manifest_sha256"] == m.manifest_sha256


def test_wrong_digest_size_tokenizer_runtime_and_format_fail(tmp_path: Path) -> None:
    data, tokenizer = payload(b"b"), b"tokenizer-b"
    m = manifest(data, tokenizer)
    store = ModelArtifactStore(tmp_path)
    with pytest.raises(IntegrityError):
        admit(store, replace(m, artifact_sha256="0" * 64), data, tokenizer)
    with pytest.raises(IntegrityError):
        admit(store, replace(m, artifact_size=len(data) + 1), data, tokenizer)
    with pytest.raises(IntegrityError):
        admit(store, replace(m, tokenizer_sha256="1" * 64), data, tokenizer)
    with pytest.raises(CompatibilityError):
        store.admit(m, BytesIO(data), BytesIO(tokenizer), runtime_id="other-runtime", runtime_version="0.16.0")
    with pytest.raises(CompatibilityError):
        store.admit(m, BytesIO(data), BytesIO(tokenizer), runtime_id="litert-lm", runtime_version="0.15.0")
    with pytest.raises(IntegrityError):
        admit(store, replace(m, artifact_format=ArtifactFormat.TASK), data, tokenizer)


def test_terms_are_explicit_and_not_inferred(tmp_path: Path) -> None:
    data, tokenizer = payload(b"c"), b"tokenizer-c"
    store = ModelArtifactStore(tmp_path)
    for state in (TermsState.REVIEW_REQUIRED, TermsState.HUMAN_ADMIT_REQUIRED, TermsState.REJECTED, TermsState.NOT_REQUIRED):
        with pytest.raises(TermsNotAdmitted):
            admit(store, manifest(data, tokenizer, terms=state), data, tokenizer)


def test_interrupted_activation_keeps_previous_pointer_and_cleans_quarantine(tmp_path: Path) -> None:
    first, tok1 = payload(b"d"), b"tokenizer-d"
    second, tok2 = payload(b"e"), b"tokenizer-e"
    store = ModelArtifactStore(tmp_path)
    m1 = manifest(first, tok1, version="1.0.0", sequence=1)
    admit(store, m1, first, tok1)
    before = store.active_manifest(m1.logical_id)
    m2 = manifest(second, tok2, version="1.1.0", sequence=2)
    with pytest.raises(ActivationInterrupted):
        admit(store, m2, second, tok2, interrupt_before_pointer=True)
    assert store.active_manifest(m1.logical_id) == before
    assert list((tmp_path / "quarantine").iterdir()) == []


def test_downgrade_duplicate_version_and_rollback(tmp_path: Path) -> None:
    first, tok1 = payload(b"f"), b"tokenizer-f"
    second, tok2 = payload(b"g"), b"tokenizer-g"
    store = ModelArtifactStore(tmp_path)
    m1 = manifest(first, tok1, version="1.0.0", sequence=1)
    m2 = manifest(second, tok2, version="2.0.0", sequence=2)
    admit(store, m1, first, tok1)
    admit(store, m2, second, tok2)
    with pytest.raises(DowngradeError):
        admit(store, replace(m1, version="0.9.0", release_sequence=0), first, tok1)
    altered = payload(b"h")
    with pytest.raises(DowngradeError):
        admit(store, manifest(altered, tok1, version="2.0.0", sequence=2), altered, tok1)
    rollback = store.rollback(m1.logical_id)
    assert rollback.from_artifact_sha256 == m2.artifact_sha256
    assert rollback.to_artifact_sha256 == m1.artifact_sha256
    assert store.active_manifest(m1.logical_id)["artifact_sha256"] == m1.artifact_sha256


def test_existing_content_addressed_object_is_reverified_before_reuse(tmp_path: Path) -> None:
    data, tokenizer = payload(b"z"), b"tokenizer-z"
    m = manifest(data, tokenizer)
    store = ModelArtifactStore(tmp_path)
    admit(store, m, data, tokenizer)
    (tmp_path / "objects" / m.artifact_sha256 / "artifact.bin").write_bytes(b"corrupt")
    with pytest.raises(IntegrityError):
        admit(store, m, data, tokenizer)


def test_public_tree_contains_no_model_bytes_or_access_material() -> None:
    forbidden_suffixes = {".litertlm", ".safetensors", ".gguf", ".onnx", ".task", ".bin"}
    for path in (ROOT / "models").rglob("*"):
        if path.is_file():
            if "__pycache__" in path.parts or path.suffix == ".pyc":
                continue
            assert path.suffix.casefold() not in forbidden_suffixes, path
            assert path.stat().st_size < 1_000_000, path
            text = path.read_text(encoding="utf-8")
            assert "hf_" + "token" not in text.casefold()
            assert "docs" + ".google.com/" not in text
            assert "drive" + ".google.com/" not in text


def test_candidate_receipt_keeps_quality_and_human_lanes_open() -> None:
    receipt = json.loads((ROOT / "models/receipts/p4-candidate.json").read_text(encoding="utf-8"))
    assert receipt["evidence"]["MODEL_QUALITY"] == "NOT_EXERCISED"
    assert receipt["evidence"]["HUMAN_TERMS"] == "HUMAN_ADMIT_REQUIRED"
