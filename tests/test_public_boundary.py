from copy import deepcopy

from edge_tlm.cli import audit_public_boundary, validate_foundation, validate_handoff_queue, validate_task_packet


def test_foundation_examples_pass():
    assert validate_foundation() == 0


def test_public_boundary_passes():
    assert audit_public_boundary() == 0


def test_public_boundary_detects_private_workspace_url_under_mnt_data(tmp_path):
    # Regression: the real workspace lives under /mnt/data. Exclusions must be
    # evaluated against repo-relative paths, not absolute path components.
    (tmp_path / "README.md").write_text(
        "private=" + "https://" + "docs.google.com/document/d/SHADOW_CANARY\n",
        encoding="utf-8",
    )
    assert audit_public_boundary(tmp_path) == 2


def test_public_boundary_ignores_repo_local_data_directory(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    (data / "receipt.md").write_text(
        "private=" + "https://" + "docs.google.com/document/d/LOCAL_RUNTIME_ONLY\n",
        encoding="utf-8",
    )
    assert audit_public_boundary(tmp_path) == 0


def test_multi_active_handoff_fails_closed():
    queue = {
        "items": [
            {"id": "a", "status": "ACTIVE", "entry_condition": "x", "runtime_lane": "local", "receipt": "r", "exit_condition": "x"},
            {"id": "b", "status": "ACTIVE", "entry_condition": "x", "runtime_lane": "local", "receipt": "r", "exit_condition": "x"},
        ]
    }
    assert any("exactly one ACTIVE" in failure for failure in validate_handoff_queue(queue))


def test_task_packet_private_url_and_placeholder_fail_closed():
    packet = {
        "task_id": "t",
        "repository": "ed3c/ai-edge-tlm",
        "issue_url": "https://github.com/ed3c/ai-edge-tlm/issues/15",
        "role": "builder",
        "base_commit": "0" * 40,
        "base_branch": "main",
        "head_branch": "x",
        "goal": "x",
        "non_goals": ["x"],
        "allowed_paths": ["README.md"],
        "excluded_paths": [],
        "positive_gates": ["pytest -q"],
        "negative_controls": ["canary"],
        "evidence_lane": "LOCAL",
        "context_id": "CDX-AI-EDGE-001",
        "rollback_subject": "0" * 40,
        "shadow_mode": "MONITOR",
        "human_owned_operations": ["merge"],
        "current_state": "READY",
    }
    bad_url = deepcopy(packet)
    bad_url["goal"] = "read " + "https://" + "docs.google.com/document/d/private"
    assert any("private Google Workspace URL" in failure for failure in validate_task_packet(bad_url))
    bad_placeholder = deepcopy(packet)
    bad_placeholder["head_branch"] = "<HEAD_BRANCH>"
    assert any("unresolved" in failure for failure in validate_task_packet(bad_placeholder))
