from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
RESEARCH = ROOT / "docs" / "research"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
PUBLIC_WORKSPACE = re.compile(r"https://(?:docs|drive)\.google\.com/", re.IGNORECASE)
ALLOWED_SOURCE_STATES = {"IMMUTABLE", "ROLLING", "SOURCE_PACKET_REQUIRED"}
ALLOWED_CLAIM_STATES = {"CORROBORATED", "CORRECTED", "PARTIAL", "OPEN", "SOURCE_PACKET_REQUIRED", "REVIEW_REQUIRED"}
ALLOWED_LICENSE_PLANES = {"SOURCE_CODE", "MODEL_WEIGHTS", "DATASET", "SERVICE", "SDK_STORE", "TRADEMARK", "EXPORT_CONTROL"}


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_digest(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def unique_ids(items: list[dict[str, Any]], label: str) -> list[str]:
    failures: list[str] = []
    ids = [item.get("id") for item in items]
    if any(not isinstance(item_id, str) or not item_id for item_id in ids):
        failures.append(f"{label} ids must be non-empty strings")
    if len(set(ids)) != len(ids):
        failures.append(f"{label} ids must be unique")
    return failures


def validate_sources(register: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    sources = register.get("sources")
    if not isinstance(sources, list) or not sources:
        return ["source register requires a non-empty sources list"]
    failures.extend(unique_ids(sources, "source"))
    as_of = date.fromisoformat(register["as_of_date"])
    max_age = int(register.get("max_rolling_age_days", 0))
    for source in sources:
        source_id = source.get("id")
        state = source.get("identity_state")
        if state not in ALLOWED_SOURCE_STATES:
            failures.append(f"{source_id}: invalid identity_state {state!r}")
        text = json.dumps(source, sort_keys=True)
        if PUBLIC_WORKSPACE.search(text):
            failures.append(f"{source_id}: private Google Workspace URL is forbidden")
        if state == "IMMUTABLE":
            revision = str(source.get("revision", ""))
            if not SHA40.fullmatch(revision):
                failures.append(f"{source_id}: immutable Git source requires SHA-40 revision")
            if revision not in str(source.get("url", "")):
                failures.append(f"{source_id}: immutable URL must contain its exact revision")
        elif state == "ROLLING":
            try:
                retrieved = date.fromisoformat(source["retrieved_at"])
            except Exception:
                failures.append(f"{source_id}: rolling source requires ISO retrieved_at")
                continue
            age = (as_of - retrieved).days
            if age < 0 or age > max_age:
                failures.append(f"{source_id}: rolling source is stale for this register ({age} days)")
        elif state == "SOURCE_PACKET_REQUIRED":
            if source.get("url") != "UNAVAILABLE" or source.get("revision") != "UNAVAILABLE":
                failures.append(f"{source_id}: absent source packet must use explicit UNAVAILABLE identity")
    return failures


def validate_claims(ledger: dict[str, Any], source_register: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    claims = ledger.get("claims")
    if not isinstance(claims, list) or not claims:
        return ["claim ledger requires a non-empty claims list"]
    failures.extend(unique_ids(claims, "claim"))
    sources = {source["id"]: source for source in source_register["sources"]}
    for claim in claims:
        claim_id = claim.get("id")
        status = claim.get("status")
        if status not in ALLOWED_CLAIM_STATES:
            failures.append(f"{claim_id}: invalid claim status {status!r}")
        source_ids = claim.get("source_ids")
        if not isinstance(source_ids, list) or not source_ids:
            failures.append(f"{claim_id}: source_ids must be non-empty")
            continue
        missing = [source_id for source_id in source_ids if source_id not in sources]
        if missing:
            failures.append(f"{claim_id}: unknown source ids {missing}")
            continue
        admitted_primary = [
            sources[source_id]
            for source_id in source_ids
            if sources[source_id].get("primary") and sources[source_id].get("identity_state") != "SOURCE_PACKET_REQUIRED"
        ]
        if status in {"CORROBORATED", "CORRECTED"} and not admitted_primary:
            failures.append(f"{claim_id}: {status} requires an admitted primary source")
        if status == "CORROBORATED" and all(sources[source_id].get("identity_state") == "SOURCE_PACKET_REQUIRED" for source_id in source_ids):
            failures.append(f"{claim_id}: missing source packet cannot self-promote to CORROBORATED")
        if not str(claim.get("evidence_ceiling", "")).strip():
            failures.append(f"{claim_id}: evidence_ceiling is required")
        if not str(claim.get("falsifier", "")).strip():
            failures.append(f"{claim_id}: falsifier is required")
    return failures


def validate_licenses(register: dict[str, Any], source_register: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    entries = register.get("entries")
    if not isinstance(entries, list) or not entries:
        return ["license register requires a non-empty entries list"]
    failures.extend(unique_ids(entries, "license"))
    source_ids = {source["id"] for source in source_register["sources"]}
    for entry in entries:
        entry_id = entry.get("id")
        plane = entry.get("plane")
        if plane not in ALLOWED_LICENSE_PLANES:
            failures.append(f"{entry_id}: invalid license plane {plane!r}")
        if entry.get("source_id") not in source_ids:
            failures.append(f"{entry_id}: source_id is not registered")
        if plane == "MODEL_WEIGHTS" and entry.get("license_id") == "Apache-2.0":
            failures.append(f"{entry_id}: model weights may not inherit the runtime source-code license")
        if entry.get("state") in {"HUMAN_ADMIT_REQUIRED", "REVIEW_REQUIRED", "RESEARCH_ONLY"} and entry.get("commercial_default"):
            failures.append(f"{entry_id}: restricted/unadmitted entry cannot be a commercial default")
        if "FASTVLM" in str(entry_id).upper() and plane == "MODEL_WEIGHTS":
            if entry.get("state") != "RESEARCH_ONLY" or entry.get("commercial_default"):
                failures.append(f"{entry_id}: FastVLM released weights must remain research-only")
        if entry.get("human_acceptance_required") and entry.get("state") == "TECHNICALLY_ADMISSIBLE":
            failures.append(f"{entry_id}: Human acceptance requirement cannot be hidden by technical admission")
    return failures


def validate_selection(selection: dict[str, Any], license_register: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    components = selection.get("components")
    if not isinstance(components, list) or not components:
        return ["technology selection requires components"]
    fastvlm = [item for item in components if item.get("component") == "FastVLM released weights"]
    if len(fastvlm) != 1 or fastvlm[0].get("default_state") != "REJECT_COMMERCIAL_DEFAULT":
        failures.append("FastVLM released weights must be explicitly rejected as a commercial default")
    return failures


def validate_all() -> tuple[list[str], dict[str, Any]]:
    source_register = load(RESEARCH / "source-register.json")
    claim_ledger = load(RESEARCH / "claim-ledger.json")
    license_register = load(RESEARCH / "license-register.json")
    selection = load(RESEARCH / "technology-selection.json")
    failures: list[str] = []
    failures.extend(validate_sources(source_register))
    failures.extend(validate_claims(claim_ledger, source_register))
    failures.extend(validate_licenses(license_register, source_register))
    failures.extend(validate_selection(selection, license_register))
    receipt = {
        "schema": "ai-edge-tlm/p0-source-closure-receipt/v1",
        "foundation_subject": source_register.get("foundation_subject"),
        "as_of_date": source_register.get("as_of_date"),
        "state": "PASS" if not failures else "FAIL",
        "counts": {
            "sources": len(source_register.get("sources", [])),
            "claims": len(claim_ledger.get("claims", [])),
            "license_entries": len(license_register.get("entries", [])),
            "technology_components": len(selection.get("components", [])),
        },
        "digests": {
            "source_register_sha256": canonical_digest(source_register),
            "claim_ledger_sha256": canonical_digest(claim_ledger),
            "license_register_sha256": canonical_digest(license_register),
            "technology_selection_sha256": canonical_digest(selection),
        },
        "residual_states": [
            "SOURCE_PACKET_REQUIRED: original article/video/PDF identity",
            "ROLLING_RECHECK_REQUIRED: Apple/Google SDK documentation",
            "HUMAN_ADMIT_REQUIRED: model/SDK/store terms",
            "NOT_EXERCISED: native/device/model-quality/privacy/thermal lanes",
        ],
        "p2_start_output": "READABLE" if not failures else "BLOCKED",
        "failures": failures,
    }
    return failures, receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args(argv)
    failures, receipt = validate_all()
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if failures:
        print("FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 2
    print(
        "PASS: immutable/rolling source identity, claim applicability, license-plane separation, "
        "commercial-default controls, and P2 start output"
    )
    print(json.dumps(receipt["counts"], sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
