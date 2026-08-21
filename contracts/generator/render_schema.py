from __future__ import annotations

from typing import Any

from .model_support import kebab, pretty_json

BASE = "https://github.com/ed3c/ai-edge-tlm/contracts/schema"


def _locations(spec: dict[str, Any]) -> dict[str, str]:
    result = {name: f"{BASE}/defs/enums.schema.json#/$defs/{name}" for name in spec["enums"]}
    for group, names in spec["record_groups"].items():
        for name in names:
            result[name] = f"{BASE}/defs/{group}.schema.json#/$defs/{name}"
    return result


def _type_schema(t: Any, locations: dict[str, str]) -> Any:
    if isinstance(t, str):
        return {
            "string": {"type": "string"},
            "integer": {"type": "integer"},
            "number": {"type": "number"},
            "boolean": {"type": "boolean"},
            "json": True,
            "json_object": {"type": "object", "additionalProperties": True},
            "string_map": {"type": "object", "additionalProperties": {"type": "string"}},
        }[t]
    if "ref" in t:
        return {"$ref": locations[t["ref"]]}
    schema = {"type": "array", "items": _type_schema(t["array"], locations)}
    for key in ("minItems", "maxItems", "uniqueItems"):
        if key in t:
            schema[key] = t[key]
    return schema


def _apply_constraints(schema: Any, field: dict[str, Any]) -> Any:
    if schema is True:
        return {"const": field["const"]} if "const" in field else schema
    result = dict(schema)
    for key in ("const", "pattern", "minimum", "maximum", "minLength", "maxLength"):
        if key in field:
            result[key] = field[key]
    return result


def _record_definition(record: dict[str, Any], locations: dict[str, str]) -> dict[str, Any]:
    properties: dict[str, Any] = {}
    required: list[str] = []
    for field in record["fields"]:
        properties[field["name"]] = _apply_constraints(_type_schema(field["type"], locations), field)
        if field.get("required", True):
            required.append(field["name"])
    return {
        "type": "object",
        "description": record["description"],
        "additionalProperties": False,
        "properties": properties,
        "required": required,
    }


def render_schema_outputs(spec: dict[str, Any]) -> dict[str, str]:
    locations = _locations(spec)
    outputs: dict[str, str] = {}
    enum_doc = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{BASE}/defs/enums.schema.json",
        "title": "AI Edge TLM v1 enums",
        "$defs": {name: {"type": "string", "enum": values} for name, values in spec["enums"].items()},
    }
    outputs["contracts/schema/defs/enums.schema.json"] = pretty_json(enum_doc)
    for group, names in spec["record_groups"].items():
        doc = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": f"{BASE}/defs/{group}.schema.json",
            "title": f"AI Edge TLM v1 {group} records",
            "$defs": {name: _record_definition(spec["records"][name], locations) for name in names},
        }
        outputs[f"contracts/schema/defs/{group}.schema.json"] = pretty_json(doc)
    index = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{BASE}/contracts-v1.schema.json",
        "title": "AI Edge TLM cross-platform contracts v1",
        "$defs": {name: {"$ref": uri} for name, uri in locations.items()},
    }
    outputs["contracts/schema/contracts-v1.schema.json"] = pretty_json(index)
    for root in spec["roots"]:
        wrapper = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": f"{BASE}/{kebab(root)}.schema.json",
            "title": root,
            "$ref": locations[root],
        }
        outputs[f"contracts/schema/{kebab(root)}.schema.json"] = pretty_json(wrapper)
    return outputs
