# P3C Shadow Architect checkpoint

Outcome: `CONTINUE_WITH_WARNINGS_L1`.

Closed locally:

- only P4-admitted `LITERTLM` model refs with accepted model-weight terms are accepted;
- model/tokenizer digests are independently checked;
- UI-thread load is rejected;
- requested, selected, and runtime-observed backend are separate values;
- unsupported accelerated backend falls back explicitly to CPU or fails closed;
- provider output becomes P2 `ToolProposal`, never a host execution decision;
- cancellation before runtime open does not enter the runtime;
- current upstream source maturity and release-integrity warning are explicit data.

Residual:

- Android Gradle and exact Maven SDK artifact: `NOT_EXERCISED`;
- LiteRT-LM binary/source reproducibility: `REVIEW_REQUIRED`;
- physical CPU/GPU/NPU backend: `NOT_EXERCISED`;
- model quality, latency, privacy, power, thermal: `NOT_EXERCISED`;
- SDK/model/store terms and release: `HUMAN_ADMIT_REQUIRED`.
