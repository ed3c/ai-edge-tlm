# Shadow Architect checkpoint — Foundation pre-publication

Subject under review:

```text
repository       ed3c/ai-edge-tlm
remote base      0008d99873f815b23f0bea0c9fca989a20b0637e
foundation head  foundation/domain-decoupled-core-v0
remote relation  identical to main before Foundation publication
local candidate  /mnt/data/ai-edge-tlm-foundation
```

## Outcome

```text
RECONCILE_BEFORE_NEXT_STEP_L2
```

The local Foundation candidate is implementation-ready, but it is not yet a repository exact-head subject. No downstream Worker may treat local candidate evidence as GitHub completion evidence.

## Material deltas found by Shadow Monitor

### S-01 — exact-subject drift

**Class:** `EVIDENCE_DELTA` / `STATE_DELTA`

The remote Foundation branch contains the bootstrap subject while the executable candidate exists only locally.

**Status:** OPEN until publication + exact-head readback.

**Falsifier:** GitHub compare/readback must show the Foundation bytes on the declared head, followed by gates rerun against that exact head.

### S-02 — missing root molecular atom

**Class:** `OWNERSHIP_DELTA` / `PROCEDURAL_GROUNDING_DELTA`

The Epic originally acted as a conceptual root but did not own a reviewable implementation lease.

**Resolution:** issue #15 now owns the Foundation root and explicitly excludes all later workstream paths.

**Status:** RESOLVED_IN_PLAN.

### S-03 — Foundation gate depended on future P2 contracts

**Class:** `LIFECYCLE_DELTA` / `EVIDENCE_DELTA`

The first candidate `edge-tlmctl validate` read `contracts/schema/**` and `contracts/examples/**`, while #15 correctly excluded `contracts/**` for P2 (#3). Publishing the proper #15 lease would therefore have broken its own gate.

**Resolution:** Foundation validation is self-contained under `tests/fixtures/**` plus the #15 task packet. P2 retains exclusive ownership of real domain schemas/bindings.

**Status:** RESOLVED_LOCAL; exact-head rerun required after publication.

### S-04 — public-boundary verifier could never inspect `/mnt/data` workspace

**Class:** `EVIDENCE_DELTA` / `FAILURE_SURFACE_DELTA`

The auditor originally excluded any absolute path containing a component named `data`. Because the working tree lives under `/mnt/data`, every public file was skipped, producing a false green. A planted Google Workspace URL exposed the failure.

**Resolution:** exclusions are now evaluated against repo-relative path parts; regression tests cover a repository physically located below `/mnt/data`; the repo-local `data/` directory remains intentionally excluded as runtime receipt storage.

**Status:** RESOLVED_LOCAL; exact-head rerun required after publication.

## FIRST_GREEN evidence

Positive gates on the restored local candidate:

```text
PYTHONPATH=src python -m edge_tlm.cli validate
PASS: foundation packet, DAG semantics, handoff cardinality, and required SSOT surfaces

PYTHONPATH=src python -m edge_tlm.cli audit-public-boundary
PASS: no committed private Google Workspace URLs or CodexDoc URI values

PYTHONPATH=src python -m pytest -q
16 passed
```

Planted negative controls:

```text
private Google Workspace URL       -> FAIL as required
second ACTIVE Local Handoff item   -> FAIL as required
cyclic Foundation DAG              -> FAIL as required
```

After restoring the fixtures, all positive gates returned green again.

## What the green tests do not prove

They do not prove:

- that these bytes exist on the declared GitHub head;
- P0 source/article/PDF truth or license applicability;
- P1 private Drive ACL correctness or resolver authorization;
- P2 JSON domain-contract/binding compatibility;
- Android/iOS native buildability;
- AICore/ML Kit, Apple Foundation Models, or LiteRT-LM runtime availability;
- runtime-observed CPU/GPU/NPU/ANE backend selection;
- model quality, conversion parity, privacy, energy, thermal or device matrix results;
- production WebView exploit resistance;
- model/service/store terms acceptance;
- PR review, merge, release, store publication, signing or provisioning.

## Next admissible transition

Only #15 may move next.

```text
explicit repository mutation authority
+ exact base rebind
+ #15 path manifest
+ no excluded workstream bytes
→ Foundation commit
→ exact-head gates
→ Shadow BEFORE_COMMIT / BEFORE_PR_OR_PUBLICATION
→ GitHub changed-path readback
→ exact-head Foundation receipt
→ admit P0 (#2) and P1 (#7) as path-disjoint siblings
```

Until the exact-head receipt exists, P0/P1 remain `BLOCKED_BY_#15` and the current Shadow result remains L2.
