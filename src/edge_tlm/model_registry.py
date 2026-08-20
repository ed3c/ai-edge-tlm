from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


class ModelRegistry:
    def __init__(self) -> None:
        self._manifests: dict[str, dict[str, Any]] = {}

    def load_directory(self, path: Path) -> None:
        for file in sorted(path.glob("*.json")):
            manifest = json.loads(file.read_text(encoding="utf-8"))
            model_id = manifest["model_id"]
            if model_id in self._manifests:
                raise ValueError(f"duplicate model id: {model_id}")
            self._manifests[model_id] = manifest

    def get(self, model_id: str) -> dict[str, Any]:
        try:
            return self._manifests[model_id]
        except KeyError as exc:
            raise KeyError(f"unknown model: {model_id}") from exc

    @staticmethod
    def verify_file(path: Path, expected_sha256: str) -> bool:
        if expected_sha256 == "OS_MANAGED":
            return False
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest() == expected_sha256
