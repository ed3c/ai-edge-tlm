# P4 Shadow Architect checkpoint

Outcome: `CONTINUE_WITH_WARNINGS_L1`.

Closed in the first vertical slice:

- artifacts enter quarantine and are streamed through bounded size and digest checks;
- tokenizer, format, runtime id, and minimum runtime version are independently checked;
- model-weight terms require explicit `ACCEPTED`; source-code license cannot authorize weights;
- active state changes only through an atomic pointer replacement;
- interruption before pointer replacement leaves the prior active model unchanged;
- duplicate logical versions with different bytes and release-sequence downgrades fail closed;
- rollback references a previously admitted content-addressed object;
- no weight, token, or private location is committed.

Residual evidence:

- authorized remote download and credential carrier: `PRIVATE_NOT_EXERCISED`;
- model/SDK/store terms acceptance: `HUMAN_ADMIT_REQUIRED`;
- device compatibility, model quality, safety, privacy, energy, and thermal behavior: `NOT_EXERCISED`.

Additional reconciliations before publication:

- an already-present content-addressed object is fully rehashed before reuse;
- active pointer, history, and receipt writes restore the previous state when an in-process write fails;
- process-crash durability across multiple files still requires the later local-runtime recovery/journal lane.
