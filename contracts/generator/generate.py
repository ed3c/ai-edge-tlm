from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from .model_support import (
    canonical_json,
    compact_json,
    compatibility_failures,
    compatibility_signature,
    kebab,
    load_model,
    pretty_json,
    sha256_bytes,
    sha256_text,
    validate_model,
)
from .render_kotlin import render_kotlin_outputs
from .render_schema import render_schema_outputs
from .render_swift import render_swift_outputs

ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = ROOT / "contracts/model/v1.json"
FORBIDDEN_PROVIDER_TOKENS = (
    "android.os.",
    "android.app.",
    "com.google.",
    "FoundationModels.",
    "LanguageModelSession",
    "LiteRtLm",
    "LiteRTLM",
    "SwiftUI.",
    "UIKit.",
    "MLKit",
    "AICoreClient",
)
GENERATED_PREFIXES = (
    "contracts/schema/",
    "contracts/examples/",
    "bindings/kotlin/",
    "bindings/swift/",
)
GENERATED_EXACT = {
    "contracts/compatibility/v1.lock.json",
    "contracts/generated-manifest.json",
}


def model_source_paths(root: Path = ROOT) -> list[Path]:
    manifest = json.loads((root / "contracts/model/v1.json").read_text(encoding="utf-8"))
    relative = [
        Path("contracts/model/v1.json"),
        Path(manifest["enums_path"]),
        Path(manifest["examples_path"]),
        *(Path(item["path"]) for item in manifest["record_fragments"]),
    ]
    return [root / path for path in relative]


def generator_source_paths(root: Path = ROOT) -> list[Path]:
    return sorted((root / "contracts/generator").glob("*.py"))


def _base_outputs(spec: dict[str, Any]) -> dict[str, str]:
    outputs: dict[str, str] = {}
    outputs.update(render_schema_outputs(spec))
    outputs.update(render_kotlin_outputs(spec))
    outputs.update(render_swift_outputs(spec))
    outputs["contracts/compatibility/v1.lock.json"] = compact_json(compatibility_signature(spec))
    for root_name, fixture in spec["examples"].items():
        outputs[f"contracts/examples/{kebab(root_name)}.json"] = pretty_json(fixture)
    return outputs


def render_outputs(spec: dict[str, Any], root: Path = ROOT) -> dict[str, str]:
    validate_model(spec)
    outputs = _base_outputs(spec)
    manifest = {
        "schema": "ai-edge-tlm/generated-manifest/v2",
        "model_semantic_sha256": sha256_bytes(canonical_json(spec)),
        "model_sources": {
            str(path.relative_to(root)): sha256_bytes(path.read_bytes())
            for path in model_source_paths(root)
        },
        "generator_sources": {
            str(path.relative_to(root)): sha256_bytes(path.read_bytes())
            for path in generator_source_paths(root)
        },
        "generated_files": {path: sha256_text(content) for path, content in sorted(outputs.items())},
    }
    outputs["contracts/generated-manifest.json"] = pretty_json(manifest)
    return outputs


def _actual_generated_paths(root: Path) -> set[str]:
    paths: set[str] = set()
    for prefix in GENERATED_PREFIXES:
        directory = root / prefix
        if not directory.exists():
            continue
        for path in directory.rglob("*"):
            if path.is_file() and ".build" not in path.parts and "__pycache__" not in path.parts:
                paths.add(str(path.relative_to(root)))
    for path in GENERATED_EXACT:
        if (root / path).is_file():
            paths.add(path)
    return paths


def write_outputs(root: Path, outputs: dict[str, str]) -> None:
    expected = set(outputs)
    for stale in sorted(_actual_generated_paths(root) - expected):
        (root / stale).unlink()
    for path, content in outputs.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    for build_dir in (root / "bindings/swift").glob(".build"):
        shutil.rmtree(build_dir, ignore_errors=True)


def check_outputs(root: Path, outputs: dict[str, str]) -> list[str]:
    failures: list[str] = []
    expected = set(outputs)
    for path, content in outputs.items():
        target = root / path
        if not target.is_file():
            failures.append(f"missing generated file: {path}")
        elif target.read_text(encoding="utf-8") != content:
            failures.append(f"generated drift: {path}")
    for stale in sorted(_actual_generated_paths(root) - expected):
        failures.append(f"stale generated file: {stale}")
    return failures


def scan_for_provider_leak(outputs: dict[str, str]) -> list[str]:
    failures: list[str] = []
    for path, content in outputs.items():
        for token in FORBIDDEN_PROVIDER_TOKENS:
            if token in content:
                failures.append(f"provider SDK token {token!r} leaked into {path}")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    spec = load_model(root)
    outputs = render_outputs(spec, root)
    failures = check_outputs(root, outputs) if args.check else []
    if failures:
        print("FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 2
    if args.check:
        print(f"PASS: {len(outputs)} generated files match deterministic output")
    else:
        write_outputs(root, outputs)
        print(f"WROTE: {len(outputs)} deterministic generated files")
    return 0


__all__ = [
    "MODEL_PATH",
    "ROOT",
    "check_outputs",
    "compatibility_failures",
    "load_model",
    "render_outputs",
    "scan_for_provider_leak",
    "validate_model",
]


if __name__ == "__main__":
    raise SystemExit(main())
