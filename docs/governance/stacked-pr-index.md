# Molecular Stack and issue index

This index follows the `C/K/A/E/X/D` vocabulary from `skills-shared/git-town-stacked-pr-worker`. It records **planned** branch topology before publication. A branch/PR does not become buildable merely because it exists; exact-head gates and blockers decide that.

| Atom | Issue | Class | True prerequisites | Path/resource lease | Evidence lane | Completion gate | Current state |
|---|---|---|---|---|---|---|---|
| C0/K0/D0 | [#15](https://github.com/ed3c/ai-edge-tlm/issues/15) | root | `main@0008d99873f815b23f0bea0c9fca989a20b0637e` | root harness, architecture SSOT, reference validators/tests, generic agent docs | LOCAL/CLOUD | exact-head `validate`, boundary audit, `pytest`, negative controls, Shadow FIRST_GREEN | OPEN; local candidate only |
| C1 | [#2](https://github.com/ed3c/ai-edge-tlm/issues/2) | sibling after root | #15 admitted | `docs/research/**`, source/claim/license validators | SOURCE/STATIC | source register + claim ledger + stale/unsupported mutation | BLOCKED_BY_#15 |
| C2 | [#7](https://github.com/ed3c/ai-edge-tlm/issues/7) | sibling after root | #15 admitted | public/private boundary surfaces | LOCAL/PRIVATE | leak canary + bounded context-capsule contract | BLOCKED_BY_#15 |
| C3 | [#3](https://github.com/ed3c/ai-edge-tlm/issues/3) | child/convergence | #2 + #7 | `contracts/**`, generated Kotlin/Swift bindings | LOCAL | schema/generator/golden/mutation gates | BLOCKED_BY_#2_#7 |
| A4 | [#4](https://github.com/ed3c/ai-edge-tlm/issues/4) | sibling | #3 | `adapters/android/system-genai/**` | LIVE_DEVICE | Gradle + supported/unavailable/fallback device receipts | BLOCKED_BY_#3 |
| A5 | [#5](https://github.com/ed3c/ai-edge-tlm/issues/5) | sibling | #3 | `adapters/apple/foundation-models/**` | LIVE_DEVICE | Xcode + supported device + OS/model revision | BLOCKED_BY_#3 |
| A6 | [#6](https://github.com/ed3c/ai-edge-tlm/issues/6) | sibling | #3 + #9 + admitted runtime source | `adapters/android/litert-lm/**` | LOCAL/LIVE_DEVICE | runtime/model/backend + failure/device receipts | BLOCKED |
| A7 | [#8](https://github.com/ed3c/ai-edge-tlm/issues/8) | sibling | #3 + #9 + runtime maturity gate | `adapters/apple/litert-lm/**` | LOCAL/LIVE_DEVICE | preview/stable + runtime/backend/device receipts | BLOCKED |
| A8 | [#9](https://github.com/ed3c/ai-edge-tlm/issues/9) | sibling | #2 + #3 + #7 | `models/**` | LOCAL/HUMAN_TERMS | digest/terms/activation/rollback | BLOCKED |
| A9 | [#10](https://github.com/ed3c/ai-edge-tlm/issues/10) | sibling | #3 + #7 | `skills/**` | LOCAL | malicious-skill/sandbox/secret/replay controls | BLOCKED |
| K10 | [#11](https://github.com/ed3c/ai-edge-tlm/issues/11) | child | #3 + #10; adapters are integrated-completion dependencies | `core/**` | LOCAL + integrated LIVE | bounded DAG + idempotency/failure gates + adapter receipts | BLOCKED |
| E11 | [#12](https://github.com/ed3c/ai-edge-tlm/issues/12) | sibling | #2 + #3 + #9 | `training/**`, `eval/**` | LOCAL/LIVE_DEVICE | lineage/parity/held-out/device benchmark | BLOCKED |
| X12 | [#13](https://github.com/ed3c/ai-edge-tlm/issues/13) | convergence | #3/#4/#5/#6/#8/#9/#10/#11/#12 required receipts | `apps/android-reference/**`, `apps/ios-reference/**`, convergence receipts | LIVE_DEVICE | Android+iOS E2E + offline/privacy/lifecycle/rollback | BLOCKED |
| D13 | [#14](https://github.com/ed3c/ai-edge-tlm/issues/14) | handoff | #13 | aggregate README/AGENTS + Stack/handoff docs | LOCAL/HUMAN | live provider readback + queue validation + Human boundary | BLOCKED |

## Start vs completion edges

A start edge closes when the prerequisite is readable and its writer lease is free. A completion edge closes only when the prerequisite's own exact-subject receipt exists in the required evidence lane. These are independent edges over the same work graph.

## Publication law

Open heads are mutable and never count as durable evidence. When publication begins, re-read Issues, branches and PR heads from GitHub, bind each atom to exact changed paths and gates, reject stale receipts after any rebase/sync, and preserve blockers/`NOT_EXERCISED` states. P8 is the only multi-parent implementation convergence; P9 is the aggregate documentation/handoff owner.
