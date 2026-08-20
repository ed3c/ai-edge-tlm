from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class SkillRegistry:
    """Metadata-only registry. Execution bytes are loaded only after policy admission."""

    def __init__(self) -> None:
        self._skills: dict[str, dict[str, Any]] = {}
        self._aliases: dict[str, str] = {}

    def add(self, manifest: dict[str, Any]) -> None:
        skill_id = manifest["skill_id"]
        if skill_id in self._skills:
            raise ValueError(f"duplicate skill: {skill_id}")
        self._skills[skill_id] = manifest
        for alias in manifest.get("aliases", []):
            key = alias.casefold()
            if key in self._aliases:
                raise ValueError(f"duplicate skill alias: {alias}")
            self._aliases[key] = skill_id

    def load_directory(self, path: Path) -> None:
        for file in sorted(path.glob("*.json")):
            self.add(json.loads(file.read_text(encoding="utf-8")))

    def resolve(self, requested: str) -> dict[str, Any] | None:
        if requested in self._skills:
            return self._skills[requested]
        mapped = self._aliases.get(requested.casefold())
        return self._skills.get(mapped) if mapped else None
