# Pre-implementation readiness

## Current verdict

```text
REMOTE_SUBJECT        0008d99873f815b23f0bea0c9fca989a20b0637e
FOUNDATION_BRANCH     foundation/domain-decoupled-core-v0
REMOTE_VS_MAIN        IDENTICAL / ahead 0 / behind 0
LOCAL_CANDIDATE       executable Foundation present outside GitHub subject
LOCAL_PYTEST          PASS / 16
LOCAL_VALIDATE        PASS / self-contained Foundation gate
LOCAL_PUBLIC_BOUNDARY PASS
NEGATIVE_CONTROLS     PASS / private URL, multi-ACTIVE handoff, cyclic DAG all turned red
SHADOW_CHECKPOINT     RECONCILE_BEFORE_NEXT_STEP_L2
NEXT_TRANSITION       #15 exact-subject publication
```

## Why L2, not PASS

The local candidate and the GitHub branch are different subjects. Local green tests cannot authorize a repository worker to build on bytes that are not present at the remote commit.

The Shadow FIRST_GREEN review also exposed and fixed two false-green mechanisms before handoff:

1. Foundation validation depended on future-owned `contracts/**`, which would disappear under the correct #15 writer lease.
2. The public-boundary scanner compared exclusion names against absolute path components, so a workspace under `/mnt/data` skipped the entire repository.

Both defects are now regression-tested locally. Their fixes still require exact-head rerun after publication.

See `docs/governance/shadow-foundation-checkpoint.md` for the full delta/evidence record.

## Readiness conditions for #15

Before mutation:
- rebind exact main/foundation base;
- use `docs/agents/packets/foundation-15.task.json` as the task contract;
- stage only paths in `foundation-publication-manifest.md`;
- do not stage P0/P1/P2/provider/model/skill/training/eval/app paths;
- public/private scan must contain no Google Workspace URL/value or private text;
- commit, push and PR creation remain separate repository authorities.

After the exact-head mutation:
- rerun `edge-tlmctl validate`;
- rerun `edge-tlmctl audit-public-boundary`;
- rerun `pytest -q`;
- execute the private-URL, multi-ACTIVE-handoff and cyclic-DAG planted controls;
- re-read changed paths from GitHub;
- run Shadow `FIRST_GREEN`, `BEFORE_COMMIT`, and `BEFORE_PR_OR_PUBLICATION` as applicable to the actual operation order;
- update the molecular Stack index from live heads and receipts.

Only then may P0/P1 sibling workers be admitted.
