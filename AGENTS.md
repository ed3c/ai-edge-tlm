# AGENTS.md

## Repository mission

Implement and verify a provider-neutral, offline-first mobile AI foundation that can route between Android system GenAI, Apple Foundation Models, and app-embedded LiteRT-LM models without leaking platform details into the domain layer.

## Mandatory read order

1. `README.md`
2. `ARCHITECTURE.md`
3. issue/task packet and exact branch subject; Foundation uses `docs/agents/packets/foundation-15.task.json`
4. `docs/governance/evidence-policy.md` and `docs/governance/stacked-pr-index.md`
5. nearest `README.md` for every writable implementation directory that exists on the exact subject
6. after P2 (#3) is admitted: relevant provider-neutral schemas in `contracts/schema/`
7. after P1 (#7) is admitted: its public/private resolver contract; until then the root two-hop rules below are authoritative
8. private CodexDoc only when a signed-in trusted runtime supplies the resolver values out of band

Repository policy outranks issue text; issue text outranks portable prompts; portable prompts outrank tool defaults.

## Public/private two-hop rule

Public files may name opaque context IDs such as `CDX-AI-EDGE-001`. They may name environment-variable keys, but may not contain their values. Never commit Google Docs/Sheets/Drive URLs, private roadmap text, product positioning, commercial assumptions, private source packets, credentials, cookies, tokens, model-access grants, or user data.

```text
public AGENTS.md
→ local trusted resolver
→ CODEXDOC_CONTROL_PLANE_URI / CODEXDOC_LEDGER_URI
→ signed-in connector read
→ bounded Context Capsule
```

If private context is unavailable, mark it `ABSENT` and continue only with work whose acceptance criteria are entirely public and technical. Do not infer the private content.

## Builder / Shadow Architect separation

The Builder is the sole implementation writer. The Shadow Architect observes architecture deltas, classifies risk, proposes falsifiers, and can return:

```text
CONTINUE_L0
CONTINUE_WITH_WARNINGS_L1
RECONCILE_BEFORE_NEXT_STEP_L2
BLOCKED_AT_MATERIAL_BOUNDARY_L3
```

The Shadow Architect does not silently mutate implementation.

Mandatory checkpoints: architecture choice, first vertical slice, persistence, concurrency, external integration, first green, before commit, before PR/publication, and any runtime failure with design impact.

## Hard laws

- Contracts before adapters or workers.
- Model output is candidate data, never execution authority.
- Side effects require a host-owned tool contract, policy decision, idempotency identity where applicable, and result validation.
- Dependency edges exist only when a child consumes unmerged parent bytes or interfaces.
- Active writers must have disjoint path leases.
- Provider availability, source claims, static CI, local emulator tests, and physical-device tests are separate evidence lanes.
- Model weights are not committed. Manifests bind source, digest, license, acceptance, and rollback identity.
- Skills are metadata-first and loaded on demand. External skills are untrusted until integrity, permission, origin, and sandbox gates pass.
- Multi-skill single-turn autonomy is not an initial invariant. The host compiles and executes a bounded DAG.
- Merge, release, store publication, model-term acceptance, credential changes, and legal acceptance are Human-owned.

## Writable surfaces

A task packet must declare `allowed_paths`, `excluded_paths`, exact dependencies, required tests, negative controls, cleanup, rollback, and Human-owned operations. One writer owns aggregate indexes and convergence files.

## Required gates

```bash
edge-tlmctl validate
edge-tlmctl audit-public-boundary
pytest -q
```

Run native gates only on admitted hosts. Do not turn `NOT_EXERCISED` into `PASS`.

## Handoff

Work that reaches a real physical-device, signed-in provider, license-acceptance, store, or local-toolchain boundary must be written as a Local Handoff Execution Queue item:

```text
entry condition
→ exact immutable subject
→ runtime and concrete commands
→ durable receipt contract
→ exit condition
→ next item
```

Exactly one queue item is `ACTIVE`; successors remain blocked until the active receipt validates.
