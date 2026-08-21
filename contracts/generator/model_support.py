from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

PRIMITIVES = {"string", "integer", "number", "boolean", "json", "json_object", "string_map"}


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def pretty_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def kebab(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "-", name).lower()


def type_key(t: Any) -> str:
    if isinstance(t, str):
        return t
    if "ref" in t:
        return f"ref:{t['ref']}"
    if "array" in t:
        return f"array:{type_key(t['array'])}"
    raise ValueError(f"unsupported type: {t!r}")


def load_model(root: Path) -> dict[str, Any]:
    manifest_path = root / "contracts/model/v1.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    enums = json.loads((root / manifest["enums_path"]).read_text(encoding="utf-8"))
    records: dict[str, Any] = {}
    record_groups: dict[str, list[str]] = {}
    for fragment in manifest["record_fragments"]:
        data = json.loads((root / fragment["path"]).read_text(encoding="utf-8"))
        overlap = set(records).intersection(data)
        if overlap:
            raise ValueError(f"duplicate records across fragments: {sorted(overlap)}")
        records.update(data)
        record_groups[fragment["group"]] = list(data)
    examples = json.loads((root / manifest["examples_path"]).read_text(encoding="utf-8"))
    spec = {
        "schema": manifest["schema"],
        "version": manifest["version"],
        "wire_namespace": manifest["wire_namespace"],
        "package": manifest["package"],
        "roots": manifest["roots"],
        "enums": enums,
        "records": records,
        "examples": examples,
        "record_groups": record_groups,
    }
    validate_model(spec)
    return spec


def validate_model(spec: dict[str, Any]) -> None:
    if spec.get("schema") != "ai-edge-tlm/contract-model/v1":
        raise ValueError("unsupported model schema")
    enums, records = spec.get("enums"), spec.get("records")
    if not isinstance(enums, dict) or not isinstance(records, dict):
        raise ValueError("enums and records must be objects")
    names = set(enums) | set(records)
    if len(names) != len(enums) + len(records):
        raise ValueError("enum and record names must not overlap")
    for name, values in enums.items():
        if not re.fullmatch(r"[A-Z][A-Za-z0-9]*", name):
            raise ValueError(f"invalid enum name {name}")
        if not isinstance(values, list) or not values or len(values) != len(set(values)):
            raise ValueError(f"enum {name} requires unique values")

    def check_type(t: Any) -> None:
        if isinstance(t, str):
            if t not in PRIMITIVES:
                raise ValueError(f"unknown primitive {t}")
        elif isinstance(t, dict) and set(t) == {"ref"}:
            if t["ref"] not in names:
                raise ValueError(f"unknown ref {t['ref']}")
        elif isinstance(t, dict) and "array" in t:
            check_type(t["array"])
        else:
            raise ValueError(f"invalid type {t!r}")

    grouped: set[str] = set()
    for group, group_names in spec.get("record_groups", {}).items():
        if not group or not isinstance(group_names, list):
            raise ValueError("record groups must be named lists")
        grouped.update(group_names)
    if grouped != set(records):
        raise ValueError("record groups must cover every record exactly once")

    for name, record in records.items():
        if not re.fullmatch(r"[A-Z][A-Za-z0-9]*", name):
            raise ValueError(f"invalid record name {name}")
        fields = record.get("fields")
        if not isinstance(fields, list) or not fields:
            raise ValueError(f"record {name} requires fields")
        field_names = [f.get("name") for f in fields]
        if len(field_names) != len(set(field_names)):
            raise ValueError(f"record {name} has duplicate fields")
        for field in fields:
            if not re.fullmatch(r"[a-z][a-z0-9_]*", str(field.get("name"))):
                raise ValueError(f"record {name} has invalid field name")
            check_type(field.get("type"))

    roots = spec.get("roots", [])
    if any(root not in records for root in roots):
        raise ValueError("every root must be a record")
    examples = spec.get("examples")
    if not isinstance(examples, dict) or set(examples) != set(roots):
        raise ValueError("examples must contain exactly one fixture for every root")
    if any(not isinstance(value, dict) for value in examples.values()):
        raise ValueError("every root example must be an object")


def compatibility_signature(spec: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": "ai-edge-tlm/compatibility-lock/v1",
        "version": spec["version"],
        "roots": list(spec["roots"]),
        "enums": {name: list(values) for name, values in spec["enums"].items()},
        "records": {
            name: {
                "required": [f["name"] for f in record["fields"] if f.get("required", True)],
                "fields": {f["name"]: type_key(f["type"]) for f in record["fields"]},
                "consts": {f["name"]: f["const"] for f in record["fields"] if "const" in f},
            }
            for name, record in spec["records"].items()
        },
    }


def compatibility_failures(spec: dict[str, Any], lock: dict[str, Any]) -> list[str]:
    current = compatibility_signature(spec)
    failures: list[str] = []
    for name, old_values in lock["enums"].items():
        values = current["enums"].get(name)
        if values is None:
            failures.append(f"removed enum {name}")
        elif values[: len(old_values)] != old_values:
            failures.append(f"enum {name} removed/reordered existing values")
    for name, old in lock["records"].items():
        new = current["records"].get(name)
        if new is None:
            failures.append(f"removed record {name}")
            continue
        for field in old["required"]:
            if field not in new["required"]:
                failures.append(f"required field {name}.{field} removed or made optional")
        for field, old_type in old["fields"].items():
            if field not in new["fields"]:
                failures.append(f"field {name}.{field} removed")
            elif new["fields"][field] != old_type:
                failures.append(f"field {name}.{field} type changed")
        for field, value in old.get("consts", {}).items():
            if new.get("consts", {}).get(field) != value:
                failures.append(f"const {name}.{field} changed")
    return failures
