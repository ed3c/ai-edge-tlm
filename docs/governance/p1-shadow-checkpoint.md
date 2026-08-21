# P1 Shadow Architect checkpoint

## Checkpoint

`BEFORE_COMMIT = CONTINUE_WITH_WARNINGS_L1`

## Material deltas found

1. **AUTHORITY_DELTA** — the first conceptual flow implied that a public Agent could follow a private URI. The implementation can inspect resolver-key presence only; retrieval belongs to a signed-in carrier.
2. **DATA_EGRESS_DELTA** — unrestricted private document text would over-share and create stale-context risk. The capsule now has a six-field closed allowlist, byte limit, TTL, task identity and exact repository subject.
3. **EVIDENCE_DELTA** — a SHA-256 digest was at risk of being read as authorization. It is explicitly integrity metadata only; carrier authentication, private ACL and Human disclosure authority remain separate lanes.
4. **LIFECYCLE_DELTA** — capsules previously had no expiry or replay boundary. Cross-task, wrong-subject, expired, future-issued and tampered capsules fail closed.
5. **SECRET_DELTA** — private URLs and secret-like values are rejected recursively before a capsule can be emitted or accepted.

## What green does not prove

A P1 pass does not prove private file location values, Drive ACL correctness, signed-in connector authorization, private-document truth, Human disclosure approval, network isolation outside this module, or absence of unknown secret formats. Those remain `PRIVATE`, `HUMAN_ADMIT_REQUIRED`, or downstream threat-model work.
