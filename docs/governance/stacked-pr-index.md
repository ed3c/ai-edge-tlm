# Molecular Stack and issue index

This index follows the `C/K/A/E/X/D` vocabulary from `skills-shared/git-town-stacked-pr-worker`. Open heads are mutable; exact-head status must be refreshed from GitHub before mutation, review, synchronization, or completion admission.

## Foundation receipt

```text
C0/K0/D0 implementation commit  51cb2c917a1da54ace87dcef9f4a75bf6504ffac
implementation tree             fc17337b94626c1b8f4c8b83dfbf543bc3134dfd
PR                              #16 draft / unmerged
changed paths                   43
CI                              validate #1 success
Shadow                          CONTINUE_WITH_WARNINGS_L1
```

| Atom | Issue | Class | True prerequisites | Path/resource lease | Evidence lane | Completion gate | Current state |
|---|---|---|---|---|---|---|---|
| C0/K0/D0 | [#15](https://github.com/ed3c/ai-edge-tlm/issues/15) | root | `main@0008d99873f815b23f0bea0c9fca989a20b0637e` | root harness, architecture SSOT, reference validators/tests, generic agent docs | LOCAL/CLOUD | exact tree replay + `validate` + boundary audit + `pytest` + controls + CI + Shadow | IMPLEMENTED_UNMERGED / PR_16 |
| C1 | [#2](https://github.com/ed3c/ai-edge-tlm/issues/2) | sibling after root | live #15 head | `docs/research/**`, P0 source/claim/license validators | SOURCE/STATIC | source register + claim ledger + stale/unsupported/wrong-subject controls | START_READY / `evidence/source-closure` |
| C2 | [#7](https://github.com/ed3c/ai-edge-tlm/issues/7) | sibling after root | live #15 head | public/private boundary interfaces/docs/tests | LOCAL/PRIVATE | leak/capsule/stale/private-authority controls | START_READY / `control/public-private-boundary` |
| C3 | [#3](https://github.com/ed3c/ai-edge-tlm/issues/3) | child/convergence | readable #2 + #7 outputs; completion requires their receipts | `contracts/**`, generated Kotlin/Swift bindings | LOCAL | schema/generator/golden/mutation gates | BLOCKED_BY_P0_P1_OUTPUTS |
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

A start edge closes when the prerequisite is readable and its writer lease is free. A completion edge closes only when the prerequisite's exact-subject receipt exists in the required evidence lane. P0/P1 are start-ready; nothing in the Foundation receipt marks either workstream complete.

## Publication law

Before any Worker mutation, re-read the parent/head refs from GitHub and reject stale branch packets. Any parent movement invalidates child exact-head receipts and requires fresh gates. P8 is the only multi-parent implementation convergence; P9 is the aggregate documentation/handoff owner. Merge/release remain Human-owned.
