# Foundation publication manifest — issue #15

This manifest prevents the local candidate scaffold from becoming one oversized PR that steals path ownership from later molecular atoms.

## Include in #15

```text
.github/workflows/validate.yml
.gitignore
AGENTS.md
ARCHITECTURE.md
CONTRIBUTING.md
LICENSE
Makefile
NOTICE
README.md
SECURITY.md
THIRD_PARTY_NOTICES.md
pyproject.toml
src/edge_tlm/**              # reference validator/policy/state-machine harness only
tests/**                     # foundation harness tests + self-contained fixtures only
docs/architecture/**
docs/agents/handoff-protocol.md
docs/agents/phase-prompts.md
docs/agents/worker-launch-index.md
docs/agents/packets/foundation-15.task.json
docs/governance/evidence-policy.md
docs/governance/local-handoff.md
docs/governance/stacked-pr-index.md
docs/governance/technology-selection.md
docs/governance/preimplementation-readiness.md
docs/governance/shadow-foundation-checkpoint.md
docs/governance/foundation-publication-manifest.md
```

## Exclude from #15

```text
contracts/**                              # #3
bindings/**                               # #3
docs/research/**                          # #2
public/private resolver implementation    # #7
adapters/**                               # #4/#5/#6/#8
models/**                                 # #9
skills/**                                 # #10
core/**                                   # #11
training/**                               # #12
eval/**                                   # #12
apps/**                                   # #13
private Google Workspace URLs/values      # never public
model weights/private datasets/secrets    # never public
```

Empty or explanatory directory README files under excluded implementation domains should stay out of #15 unless the Tech Lead explicitly reclassifies them as shared architecture SSOT and proves no future writer lease collision.

## Candidate-only files

`contracts/**`, provider README stubs, `models/README.md`, `skills/README.md`, `training/README.md`, and `eval/README.md` exist in the local candidate as design aids. Their existence is not authority to publish them in #15. Each must move with its owning issue or be deleted/re-derived by that worker.
