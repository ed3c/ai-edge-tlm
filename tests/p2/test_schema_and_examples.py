from __future__ import annotations

import copy
import json
import re

import pytest

from contracts.generator.contract_checks import load_schema_store, validate_instance
from contracts.generator.generate import ROOT, load_model


def kebab(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "-", name).lower()


def test_all_root_examples_validate_with_dependency_free_fail_closed_validator() -> None:
    spec = load_model(ROOT)
    store = load_schema_store(ROOT)
    for root_name in spec["roots"]:
        wrapper = json.loads((ROOT / f"contracts/schema/{kebab(root_name)}.schema.json").read_text(encoding="utf-8"))
        example = json.loads((ROOT / f"contracts/examples/{kebab(root_name)}.json").read_text(encoding="utf-8"))
        assert validate_instance(example, wrapper, wrapper, store) == [], root_name


def test_all_schemas_are_valid_draft_2020_12_when_reference_validator_is_available() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    referencing = pytest.importorskip("referencing")
    store = load_schema_store(ROOT)
    registry = referencing.Registry().with_resources(
        (uri, referencing.Resource.from_contents(document)) for uri, document in store.items()
    )
    for document in store.values():
        jsonschema.Draft202012Validator.check_schema(document)
    for root_name in load_model(ROOT)["roots"]:
        wrapper = json.loads((ROOT / f"contracts/schema/{kebab(root_name)}.schema.json").read_text(encoding="utf-8"))
        example = json.loads((ROOT / f"contracts/examples/{kebab(root_name)}.json").read_text(encoding="utf-8"))
        assert list(jsonschema.Draft202012Validator(wrapper, registry=registry).iter_errors(example)) == []


def test_unknown_property_and_unversioned_envelope_fail_closed() -> None:
    store = load_schema_store(ROOT)
    wrapper = json.loads((ROOT / "contracts/schema/inference-request.schema.json").read_text(encoding="utf-8"))
    example = json.loads((ROOT / "contracts/examples/inference-request.json").read_text(encoding="utf-8"))

    unknown = copy.deepcopy(example)
    unknown["provider_native_session"] = "forbidden"
    assert any("unknown property" in failure for failure in validate_instance(unknown, wrapper, wrapper, store))

    wrong_version = copy.deepcopy(example)
    wrong_version["schema"] = "ai-edge-tlm/inference-request/v2"
    assert any("expected const" in failure for failure in validate_instance(wrong_version, wrapper, wrapper, store))


def test_requested_backend_does_not_rewrite_observed_backend() -> None:
    receipt = json.loads((ROOT / "contracts/examples/benchmark-receipt.json").read_text(encoding="utf-8"))
    assert receipt["requested_backend"] == "NPU"
    assert receipt["observed_backend"] == "UNKNOWN"
    assert receipt["state"] == "NOT_EXERCISED"
