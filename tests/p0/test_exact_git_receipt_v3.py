from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
RECEIPT = ROOT / "docs/research/receipts/p0-source-closure.exact-v3.json"


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data, usedforsecurity=False).hexdigest()


def canonical_json_sha256(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def test_p0_v3_binds_semantics_and_exact_git_bytes() -> None:
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    assert receipt["schema"] == "ai-edge-tlm/p0-source-closure-exact-receipt/v3"
    for item in receipt["files"]:
        path = ROOT / item["path"]
        data = path.read_bytes()
        assert git_blob_sha1(data) == item["git_object"]["value"], item["path"]
        assert item["semantic_digest"]["mode"] == "canonical-json"
        assert canonical_json_sha256(json.loads(data)) == item["semantic_digest"]["value"], item["path"]
