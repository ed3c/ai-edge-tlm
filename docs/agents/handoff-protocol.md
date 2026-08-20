# Phase handoff protocol

Every phase emits a Context Capsule:

```json
{
  "task_id": "...",
  "exact_subject": "repository@commit",
  "inputs_consumed": [],
  "decisions": [],
  "changed_paths": [],
  "contracts_produced": [],
  "positive_gates": [],
  "negative_controls": [],
  "evidence_lane": "STATIC|LOCAL|LIVE_DEVICE|PRIVATE|HUMAN",
  "residual_states": [],
  "blockers": [],
  "rollback_subject": "...",
  "next_authority": "..."
}
```

A successor starts only when its start dependencies are readable. It completes only when its completion dependencies have same-subject receipts in the required lane. These edge classes must not be collapsed.
