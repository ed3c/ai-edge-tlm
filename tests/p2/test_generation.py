from __future__ import annotations

import copy
import json
from pathlib import Path

from contracts.generator.generate import (
    ROOT,
    check_outputs,
    compatibility_failures,
    load_model,
    render_outputs,
    scan_for_provider_leak,
)


def test_generated_files_match_the_deterministic_generator() -> None:
    spec = load_model(ROOT)
    outputs = render_outputs(spec, ROOT)
    assert check_outputs(ROOT, outputs) == []
    assert scan_for_provider_leak(outputs) == []


def test_generated_drift_is_detected(tmp_path: Path) -> None:
    outputs = render_outputs(load_model(ROOT), ROOT)
    for path, content in outputs.items():
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    victim = tmp_path / "bindings/kotlin/README.md"
    victim.write_text(victim.read_text(encoding="utf-8") + "drift\n", encoding="utf-8")
    assert "generated drift: bindings/kotlin/README.md" in check_outputs(tmp_path, outputs)


def test_breaking_required_field_and_enum_mutations_fail() -> None:
    spec = load_model(ROOT)
    lock = json.loads((ROOT / "contracts/compatibility/v1.lock.json").read_text(encoding="utf-8"))
    removed = copy.deepcopy(spec)
    removed["records"]["InferenceRequest"]["fields"] = [
        field for field in removed["records"]["InferenceRequest"]["fields"]
        if field["name"] != "request_id"
    ]
    assert any("InferenceRequest.request_id" in item for item in compatibility_failures(removed, lock))
    reordered = copy.deepcopy(spec)
    reordered["enums"]["EvidenceLane"][:2] = reversed(reordered["enums"]["EvidenceLane"][:2])
    assert any("EvidenceLane" in item for item in compatibility_failures(reordered, lock))


def test_provider_sdk_type_leakage_is_detected() -> None:
    outputs = render_outputs(load_model(ROOT), ROOT)
    mutated = dict(outputs)
    path = next(item for item in mutated if item.endswith("BaseContracts.kt"))
    mutated[path] += "\nval leaked: com.google.ai.edge.litertlm.Engine? = null\n"
    assert any("com.google." in item for item in scan_for_provider_leak(mutated))
