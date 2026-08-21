# P5 Shadow Architect checkpoint

Outcome: `CONTINUE_WITH_WARNINGS_L1`.

Closed in the first vertical slice:

- the prompt index contains metadata only;
- full instructions load only after exact origin, manifest, and package digest admission;
- overlapping descriptions produce deterministic candidates and fail ambiguous ties closed;
- model proposals cannot execute tools without host schema, authority, confirmation, and idempotency checks;
- origin, CSP, network, storage, bridge, camera, microphone, input/output size, replay, timeout, and secret-handle policies fail closed;
- timeout/crash paths terminate the instance and remove executable residue;
- receipts omit payloads and secret handles.

Residual evidence:

- native Android/iOS bridge and WebView implementation: `NOT_EXERCISED`;
- OS/WebView exploit resistance: `NOT_EXERCISED`;
- signed-in secret carrier: `PRIVATE_NOT_EXERCISED`;
- remote-skill trust and store release: `HUMAN_ADMIT_REQUIRED`.

Additional reconciliations before publication:

- package digest/origin verification returns `UNTRUSTED`; only an explicit host policy decision can promote the exact package to `TRUSTED`;
- registry, tool replay, and sandbox replay state use synchronized guards;
- script traversal, credential-bearing origins, noncanonical JSON, and invalid model-output digests fail closed;
- multiprocessing uses `spawn`, and timed-out-worker queue teardown cannot block cleanup;
- the process harness remains a policy test double, not an OS/WebView security boundary.

## Clean-publication reconciliation

A clean-tree replay rejected an earlier mixed module list whose package initializer depended on files outside the proposed publication denominator. The canonical P5 surface is now one process-isolated runtime (`integrity`, `registry`, `broker`, `sandbox`, `types`, `errors`) plus a closed module-surface test. Duplicate thread-based policy/executor prototypes are excluded from publication.
