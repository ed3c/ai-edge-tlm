# Worker launch index

The Tech Lead owns this routing table. A new ChatGPT/Codex session may start only when its launch-state predicate is true and the exact base commit is inserted into the worker packet immediately before launch.

| Worker | Issue | Planned branch | Writable lease | Launch predicate | Current state |
|---|---|---|---|---|---|
| FOUNDATION | [#15](https://github.com/ed3c/ai-edge-tlm/issues/15) | `foundation/domain-decoupled-core-v0` | #15 owned root surfaces only | explicit commit/publication authority + exact base bound | READY_EXCEPT_PUBLICATION_AUTHORITY |
| P0 | [#2](https://github.com/ed3c/ai-edge-tlm/issues/2) | `evidence/source-closure` | `docs/research/**` | #15 exact-head foundation admitted | BLOCKED |
| P1 | [#7](https://github.com/ed3c/ai-edge-tlm/issues/7) | `control/public-private-boundary` | public/private boundary surfaces | #15 admitted | BLOCKED |
| P2 | [#3](https://github.com/ed3c/ai-edge-tlm/issues/3) | `contracts/cross-platform-v1` | `contracts/**`, generated bindings | #2/#7 required outputs readable; completion waits receipts | BLOCKED |
| P3A | [#4](https://github.com/ed3c/ai-edge-tlm/issues/4) | `adapter/android-system-genai` | `adapters/android/system-genai/**` | #3 frozen contract readable | BLOCKED |
| P3B | [#5](https://github.com/ed3c/ai-edge-tlm/issues/5) | `adapter/apple-foundation-models` | `adapters/apple/foundation-models/**` | #3 frozen contract readable | BLOCKED |
| P3C | [#6](https://github.com/ed3c/ai-edge-tlm/issues/6) | `adapter/android-litert-lm` | `adapters/android/litert-lm/**` | #3 readable + #9 admitted artifact/runtime inputs | BLOCKED |
| P3D | [#8](https://github.com/ed3c/ai-edge-tlm/issues/8) | `adapter/apple-litert-lm` | `adapters/apple/litert-lm/**` | #3 readable + #9 + maturity gate | BLOCKED |
| P4 | [#9](https://github.com/ed3c/ai-edge-tlm/issues/9) | `model/supply-chain` | `models/**` | #2/#3/#7 required public contracts readable | BLOCKED |
| P5 | [#10](https://github.com/ed3c/ai-edge-tlm/issues/10) | `skill/runtime-sandbox` | `skills/**` | #3/#7 contracts readable | BLOCKED |
| P6 | [#11](https://github.com/ed3c/ai-edge-tlm/issues/11) | `core/deterministic-orchestrator` | `core/**` | #3/#10 readable; fake-provider start allowed | BLOCKED |
| P7 | [#12](https://github.com/ed3c/ai-edge-tlm/issues/12) | `eval/tlm-training-conversion` | `training/**`, `eval/**` | #2/#3/#9 admitted | BLOCKED |
| P8 | [#13](https://github.com/ed3c/ai-edge-tlm/issues/13) | `integration/mobile-reference` | `apps/**` | all selected scenario parents completion-ready | BLOCKED |
| P9 | [#14](https://github.com/ed3c/ai-edge-tlm/issues/14) | `delivery/convergence-handoff` | aggregate delivery docs only | #13 exact-head convergence + live provider readback | BLOCKED |

## Launch packet compiler

Before opening a new session, replace every placeholder below from live GitHub/receipt readback; unresolved placeholders are a hard stop.

```text
ROLE=<phase role from phase-prompts.md>
REPOSITORY=ed3c/ai-edge-tlm
ISSUE_URL=<exact issue>
BASE_COMMIT=<40-char immutable SHA>
BASE_BRANCH=<exact parent branch>
HEAD_BRANCH=<planned branch>
ALLOWED_PATHS=<non-overlapping lease>
EXCLUDED_PATHS=<all other active leases + private paths>
START_DEPENDENCIES=<readability receipts>
COMPLETION_DEPENDENCIES=<lane-bound exact-subject receipts>
POSITIVE_GATES=<commands/oracles>
NEGATIVE_CONTROLS=<planted defects>
EVIDENCE_LANE=<required lane>
ROLLBACK_SUBJECT=<immutable SHA/artifact>
CODEXDOC_CONTEXT_ID=CDX-AI-EDGE-001
HUMAN_OWNED_OPERATIONS=<explicit list>
```

The private resolver may supply a bounded Context Capsule for `CDX-AI-EDGE-001`; it must not inject private URLs or secrets into files written under the public path lease.
