from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

PRIVATE_URL = re.compile(r"https://(?:docs|drive)\.google\.com/", re.IGNORECASE)
RESOLVER_VALUE = re.compile(r"CODEXDOC_(?:CONTROL_PLANE|LEDGER)_URI\s*=\s*https?://", re.IGNORECASE)
SECRET_SHAPES = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{30,}\b"),
)


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def semantic_sha256(path: Path, mode: str) -> str:
    data = path.read_bytes()
    if mode == "canonical-json":
        data = canonical_json_bytes(json.loads(data))
    elif mode != "raw-bytes":
        raise ValueError(f"unsupported semantic mode: {mode}")
    return hashlib.sha256(data).hexdigest()


def git_blob_sha1(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data, usedforsecurity=False).hexdigest()


def public_text_failures(paths: list[Path]) -> list[str]:
    failures: list[str] = []
    for path in paths:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if PRIVATE_URL.search(text):
            failures.append(f"private Workspace URL: {path}")
        if RESOLVER_VALUE.search(text):
            failures.append(f"resolver URI value: {path}")
        for pattern in SECRET_SHAPES:
            if pattern.search(text):
                failures.append(f"secret-like value: {path}")
    return failures


def evidence_lane_satisfies(actual: str, required: str) -> bool:
    """Evidence lanes are independent; no lane is promoted into another."""
    return actual == required


def _resolve_pointer(document: Any, pointer: str) -> Any:
    if pointer in ("", "#"):
        return document
    if not pointer.startswith("#/"):
        raise ValueError(f"unsupported JSON pointer: {pointer}")
    value = document
    for token in pointer[2:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        value = value[token]
    return value


def _resolve_ref(ref: str, document: dict[str, Any], store: dict[str, dict[str, Any]]) -> tuple[Any, dict[str, Any]]:
    if ref.startswith("#"):
        return _resolve_pointer(document, ref), document
    uri, separator, fragment = ref.partition("#")
    target = store.get(uri)
    if target is None:
        raise ValueError(f"unknown schema resource: {uri}")
    pointer = f"#{fragment}" if separator else "#"
    return _resolve_pointer(target, pointer), target


def load_schema_store(root: Path) -> dict[str, dict[str, Any]]:
    store: dict[str, dict[str, Any]] = {}
    for path in sorted((root / "contracts/schema").rglob("*.json")):
        document = json.loads(path.read_text(encoding="utf-8"))
        uri = document.get("$id")
        if isinstance(uri, str):
            if uri in store:
                raise ValueError(f"duplicate schema $id: {uri}")
            store[uri] = document
    return store


def validate_instance(instance: Any, schema: Any, document: dict[str, Any], store: dict[str, dict[str, Any]] | None = None, path: str = "$") -> list[str]:
    """Validate the closed Draft 2020-12 subset emitted by this generator."""
    store = store or {document.get("$id", ""): document}
    failures: list[str] = []
    if schema is True:
        return failures
    if schema is False:
        return [f"{path}: schema is false"]
    if "$ref" in schema:
        try:
            target, target_document = _resolve_ref(schema["$ref"], document, store)
        except (KeyError, TypeError, ValueError) as exc:
            return [f"{path}: unresolved ref {schema['$ref']}: {exc}"]
        return validate_instance(instance, target, target_document, store, path)
    if "const" in schema and instance != schema["const"]:
        failures.append(f"{path}: expected const {schema['const']!r}")
    if "enum" in schema and instance not in schema["enum"]:
        failures.append(f"{path}: {instance!r} not in enum")
    kind = schema.get("type")
    valid_type = True
    if kind == "object": valid_type = isinstance(instance, dict)
    elif kind == "array": valid_type = isinstance(instance, list)
    elif kind == "string": valid_type = isinstance(instance, str)
    elif kind == "integer": valid_type = isinstance(instance, int) and not isinstance(instance, bool)
    elif kind == "number": valid_type = isinstance(instance, (int, float)) and not isinstance(instance, bool) and math.isfinite(float(instance))
    elif kind == "boolean": valid_type = isinstance(instance, bool)
    if kind and not valid_type:
        return failures + [f"{path}: expected {kind}"]
    if isinstance(instance, dict):
        for key in schema.get("required", []):
            if key not in instance: failures.append(f"{path}: missing required property {key}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in instance:
                if key not in properties: failures.append(f"{path}: unknown property {key}")
        for key, value in instance.items():
            if key in properties:
                failures.extend(validate_instance(value, properties[key], document, store, f"{path}.{key}"))
            elif isinstance(schema.get("additionalProperties"), dict):
                failures.extend(validate_instance(value, schema["additionalProperties"], document, store, f"{path}.{key}"))
    if isinstance(instance, list):
        if len(instance) < schema.get("minItems", 0): failures.append(f"{path}: too few items")
        if "maxItems" in schema and len(instance) > schema["maxItems"]: failures.append(f"{path}: too many items")
        if schema.get("uniqueItems"):
            rendered = [canonical_json_bytes(item) for item in instance]
            if len(rendered) != len(set(rendered)): failures.append(f"{path}: duplicate items")
        if "items" in schema:
            for index, item in enumerate(instance):
                failures.extend(validate_instance(item, schema["items"], document, store, f"{path}[{index}]"))
    if isinstance(instance, str):
        if len(instance) < schema.get("minLength", 0): failures.append(f"{path}: string too short")
        if "maxLength" in schema and len(instance) > schema["maxLength"]: failures.append(f"{path}: string too long")
        if "pattern" in schema and re.search(schema["pattern"], instance) is None: failures.append(f"{path}: pattern mismatch")
    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]: failures.append(f"{path}: below minimum")
        if "maximum" in schema and instance > schema["maximum"]: failures.append(f"{path}: above maximum")
    return failures


def parent_identity_failures(root: Path, packet: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    provenance = json.loads((root / "contracts/input-snapshots/p1/provenance.json").read_text(encoding="utf-8"))
    snapshot_by_source = {item["source_path"]: item for item in provenance["files"]}
    for lane, items in packet["input_contracts"].items():
        for item in items:
            if lane == "p0":
                path = root / item["path"]
            else:
                snap = snapshot_by_source.get(item["path"])
                if snap is None:
                    failures.append(f"P1 source path not snapshotted: {item['path']}")
                    continue
                path = root / snap["snapshot_path"]
                if provenance["source_ref"] != item["ref"]:
                    failures.append(f"P1 source ref drift for {item['path']}")
            if not path.is_file():
                failures.append(f"missing parent input: {path.relative_to(root)}")
                continue
            if git_blob_sha1(path) != item["git_blob_sha1"]: failures.append(f"Git blob drift: {item['path']}")
            if semantic_sha256(path, item["semantic_mode"]) != item["semantic_sha256"]: failures.append(f"semantic digest drift: {item['path']}")
    return failures
