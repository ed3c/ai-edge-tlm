from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RECEIPT = ROOT / "docs/research/receipts/p0-source-closure.exact-v2.json"


def git_blob_sha1(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data, usedforsecurity=False).hexdigest()


def test_p0_v2_receipt_binds_exact_git_blobs() -> None:
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    assert receipt["schema"] == "ai-edge-tlm/p0-source-closure-exact-receipt/v2"
    assert receipt["superseded_state"] == "STALE_LOCAL_CANDIDATE_DIGESTS"
    for item in receipt["files"]:
        path = ROOT / item["path"]
        assert path.is_file(), item["path"]
        assert item["git_object_format"] == "sha1"
        assert git_blob_sha1(path) == item["git_blob"], item["path"]
