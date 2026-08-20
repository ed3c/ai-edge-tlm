from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from .dag import DagError, topological_order


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = ROOT / "tests" / "fixtures"
FOUNDATION_TASK = ROOT / "docs" / "agents" / "packets" / "foundation-15.task.json"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
UNRESOLVED = re.compile(r"<[^>]+>")


def _load(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_handoff_queue(queue: dict) -> list[str]:
    failures: list[str] = []
    items = queue.get("items")
    if not isinstance(items, list) or not items:
        return ["handoff queue requires a non-empty items list"]
    active = [item for item in items if item.get("status") == "ACTIVE"]
    if len(active) != 1:
        failures.append(f"handoff queue requires exactly one ACTIVE item, found {len(active)}")
    ids = [item.get("id") for item in items]
    if None in ids or len(set(ids)) != len(ids):
        failures.append("handoff item ids must be unique and non-empty")
    allowed = {"ACTIVE", "BLOCKED_BY_PREDECESSOR", "PASS", "FAIL", "HUMAN_ADMIT_REQUIRED"}
    for item in items:
        if item.get("status") not in allowed:
            failures.append(f"invalid handoff status for {item.get('id')!r}: {item.get('status')!r}")
        for key in ("entry_condition", "runtime_lane", "receipt", "exit_condition"):
            value = item.get(key)
            if not isinstance(value, str) or not value.strip():
                failures.append(f"handoff item {item.get('id')!r} missing {key}")
    return failures


def validate_task_packet(packet: dict) -> list[str]:
    failures: list[str] = []
    required = {
        "task_id",
        "repository",
        "issue_url",
        "role",
        "base_commit",
        "base_branch",
        "head_branch",
        "goal",
        "non_goals",
        "allowed_paths",
        "excluded_paths",
        "positive_gates",
        "negative_controls",
        "evidence_lane",
        "context_id",
        "rollback_subject",
        "shadow_mode",
        "human_owned_operations",
        "current_state",
    }
    missing = sorted(required - packet.keys())
    if missing:
        failures.append(f"task packet missing fields: {', '.join(missing)}")
    if not SHA40.fullmatch(str(packet.get("base_commit", ""))):
        failures.append("task packet base_commit must be an immutable SHA-40")
    if not SHA40.fullmatch(str(packet.get("rollback_subject", ""))):
        failures.append("task packet rollback_subject must be an immutable SHA-40")
    if not packet.get("allowed_paths"):
        failures.append("task packet allowed_paths must be non-empty")
    if not packet.get("negative_controls"):
        failures.append("task packet negative_controls must be non-empty")
    serialized = json.dumps(packet, sort_keys=True)
    if UNRESOLVED.search(serialized):
        failures.append("task packet contains unresolved angle-bracket placeholders")
    if re.search(r"https://(?:docs|drive)\.google\.com/", serialized, re.IGNORECASE):
        failures.append("task packet contains a private Google Workspace URL")
    return failures


def validate_foundation() -> int:
    failures: list[str] = []
    required_paths = [
        ROOT / "README.md",
        ROOT / "AGENTS.md",
        ROOT / "ARCHITECTURE.md",
        ROOT / "docs" / "governance" / "evidence-policy.md",
        ROOT / "docs" / "governance" / "stacked-pr-index.md",
        ROOT / "docs" / "agents" / "handoff-protocol.md",
        FOUNDATION_TASK,
        FIXTURE_DIR / "foundation-pipeline.json",
        FIXTURE_DIR / "foundation-handoff.json",
    ]
    for path in required_paths:
        if not path.is_file():
            failures.append(f"required foundation path is absent: {path.relative_to(ROOT)}")

    if not failures:
        packet = _load(FOUNDATION_TASK)
        if not isinstance(packet, dict):
            failures.append("foundation task packet must be a JSON object")
        else:
            failures.extend(validate_task_packet(packet))

        pipeline = _load(FIXTURE_DIR / "foundation-pipeline.json")
        if not isinstance(pipeline, dict) or not isinstance(pipeline.get("nodes"), list):
            failures.append("foundation pipeline fixture is malformed")
        else:
            try:
                order = topological_order(pipeline["nodes"])
                outputs = pipeline.get("outputs", [])
                if not isinstance(outputs, list) or not set(outputs).issubset(order):
                    failures.append("foundation pipeline outputs are not reachable nodes")
            except DagError as exc:
                failures.append(f"foundation pipeline DAG: {exc}")

        queue = _load(FIXTURE_DIR / "foundation-handoff.json")
        if not isinstance(queue, dict):
            failures.append("foundation handoff fixture must be a JSON object")
        else:
            failures.extend(validate_handoff_queue(queue))

    if failures:
        print("FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 2
    print("PASS: foundation packet, DAG semantics, handoff cardinality, and required SSOT surfaces")
    return 0


# Compatibility alias for early local candidate callers. P2 owns real domain-contract validation.
def validate_contracts() -> int:
    return validate_foundation()


def audit_public_boundary(root: Path | None = None) -> int:
    scan_root = ROOT if root is None else root.resolve()
    failures: list[str] = []
    allowed_suffixes = {".md", ".json", ".toml", ".yml", ".yaml", ".py", ".txt"}
    url_pattern = re.compile(r"https://(?:docs|drive)\.google\.com/", re.IGNORECASE)
    assignment_pattern = re.compile(r"CODEXDOC_(?:CONTROL_PLANE|LEDGER)_URI\s*=\s*https?://", re.IGNORECASE)
    excluded = {".git", ".venv", "data"}
    for path in scan_root.rglob("*"):
        if not path.is_file() or path.suffix not in allowed_suffixes:
            continue
        relative = path.relative_to(scan_root)
        if any(part in excluded for part in relative.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if url_pattern.search(text):
            failures.append(f"private Google Workspace URL pattern: {relative}")
        if assignment_pattern.search(text):
            failures.append(f"committed CodexDoc URI value: {relative}")
    if failures:
        print("FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 2
    print("PASS: no committed private Google Workspace URLs or CodexDoc URI values")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="edge-tlmctl")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate")
    sub.add_parser("audit-public-boundary")
    dag_parser = sub.add_parser("dag-order")
    dag_parser.add_argument("path", type=Path)
    args = parser.parse_args(argv)
    if args.command == "validate":
        return validate_foundation()
    if args.command == "audit-public-boundary":
        return audit_public_boundary()
    if args.command == "dag-order":
        data = _load(args.path)
        print("\n".join(topological_order(data["nodes"])))
        return 0
    return 64


if __name__ == "__main__":
    sys.exit(main())
