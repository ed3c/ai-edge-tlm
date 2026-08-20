# Shadow Architect checkpoint — Foundation publication

## Immutable implementation subject

```text
repository             ed3c/ai-edge-tlm
base                   0008d99873f815b23f0bea0c9fca989a20b0637e
implementation commit  51cb2c917a1da54ace87dcef9f4a75bf6504ffac
implementation tree    fc17337b94626c1b8f4c8b83dfbf543bc3134dfd
pull request           #16 / draft / unmerged
changed paths          43 / #15 publication lease
provider workflow      validate #1 / success
```

The open branch head is mutable and must be read live. The immutable implementation commit/tree above is the Foundation evidence subject; subsequent documentation-only reconciliation cannot erase that receipt.

## Outcome

```text
CONTINUE_WITH_WARNINGS_L1
```

Foundation implementation/publication gates are closed. Warnings identify downstream evidence lanes that remain absent or unexercised; they do not block P0/P1 start.

## Material deltas and disposition

### S-01 — exact-subject drift

**Class:** `EVIDENCE_DELTA` / `STATE_DELTA`

The executable candidate originally existed only under `/mnt/data` while the remote branch was the bootstrap commit.

**Disposition:** `CLOSED_FOR_IMPLEMENTATION_COMMIT`.

A fresh 43-path local Git index produced tree `fc17337b94626c1b8f4c8b83dfbf543bc3134dfd`, exactly matching the pushed commit tree. GitHub changed-path readback and provider CI closed the cloud publication lane for this root atom.

### S-02 — missing root molecular atom

**Class:** `OWNERSHIP_DELTA` / `PROCEDURAL_GROUNDING_DELTA`

**Disposition:** `CLOSED`.

Issue #15 owns the Foundation root and explicitly excludes later workstream paths.

### S-03 — Foundation gate depended on future P2 contracts

**Class:** `LIFECYCLE_DELTA` / `EVIDENCE_DELTA`

**Disposition:** `CLOSED`.

Foundation validation is self-contained under `tests/fixtures/**` plus the #15 packet. P2 retains exclusive domain-contract ownership.

### S-04 — public-boundary verifier skipped `/mnt/data`

**Class:** `EVIDENCE_DELTA` / `FAILURE_SURFACE_DELTA`

**Disposition:** `CLOSED`.

Exclusions use repository-relative paths; `/mnt/data` regression coverage and a planted private Workspace URL prove the scanner reaches the repository.

### S-05 — post-publication SSOT remained pre-publication

**Class:** `STATE_DELTA` / `EVIDENCE_DELTA`

After PR/CI creation, readiness/Stack documents still described Foundation as local-only and P0/P1 as blocked.

**Disposition:** `RECONCILED_IN_FOLLOW_UP`.

Public SSOT now records the immutable implementation receipt, draft PR/CI state, mutable-open-head rule, and P0/P1 `START_READY` state without embedding a self-referential follow-up commit SHA.

## Exact-subject evidence

Positive gates:

```text
edge-tlmctl validate                 PASS
edge-tlmctl audit-public-boundary    PASS
pytest -q                            16 passed
GitHub workflow validate #1          SUCCESS
```

Planted controls:

```text
private Google Workspace URL        FAIL as required
second ACTIVE Local Handoff item     FAIL as required
cyclic Foundation DAG               FAIL as required
```

All fixtures were restored and positive gates returned green.

## What the green tests do not prove

They do not prove P0 source truth, P1 private ACL/authorization, P2 native contract bindings, Android/iOS buildability, provider/device/backend availability, model quality/conversion parity, privacy/energy/thermal results, production sandbox exploit resistance, terms acceptance, merge, release, signing, or store publication.

## Next admissible transitions

```text
live Foundation PR head readback
→ synchronize untouched P0/P1 child branches to the exact parent
→ launch P0 #2 and P1 #7 as path-disjoint Workers
→ receive bounded Context Capsules and owning-lane receipts
→ admit P2 start when required outputs are readable
→ retain P2 completion blockers until P0/P1 receipts validate
```

Merge and every release/terms/secret/store transition remain Human-owned.
