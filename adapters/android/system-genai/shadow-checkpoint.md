# P3A Shadow Architect checkpoint

Outcome: `CONTINUE_WITH_WARNINGS_L1`.

Closed in the first vertical slice:

- capability observations are bound to OS, system-model, and API revisions;
- stale or expired observations fail closed;
- unavailable and failed system-model paths select only embedded TLM or fail-closed;
- model tool output is emitted as `ToolProposal` and never executed;
- cancellation and typed errors preserve request and trace identity;
- no Android/Google SDK type enters P2 contract values.

Residual evidence:

- Android Gradle and exact SDK artifact: `NOT_EXERCISED`;
- physical supported device and system model: `NOT_EXERCISED`;
- latency, quality, privacy, power, and thermal behavior: `NOT_EXERCISED`;
- SDK/store terms and signing: `HUMAN_ADMIT_REQUIRED`.

Additional reconciliations before publication:

- the capability cache uses an atomic reference rather than unsynchronized mutable state;
- a token cancelled before execution emits a typed cancellation without entering the provider;
- spawned provider/session work remains outside this static slice and requires Android-owned lifecycle evidence.
