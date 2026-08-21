# P3B Shadow checkpoint

Outcome: `CONTINUE_WITH_WARNINGS_L1`.

Closed in the static/local slice:

- provider SDK values remain behind the session protocol;
- prompt profiles bind exact OS/model revisions;
- sessions cannot be reused across request owners;
- tool output remains a P2 proposal without execution authority;
- context-window and provider failures are typed;
- fallback is embedded and network-disabled;
- Swift/Linux is not promoted to Xcode/iOS or physical-device evidence.

Residual states:

- Xcode/iOS SDK integration: `NOT_EXERCISED`;
- Foundation Models availability on supported device/region: `NOT_EXERCISED`;
- signing, provisioning and Apple terms: `HUMAN_ADMIT_REQUIRED`;
- latency, privacy, quality, energy and thermal: `NOT_EXERCISED`.

Additional reconciliations before publication:

- provider streaming is represented by `AsyncThrowingStream`, not a pre-materialized result array;
- prewarm and stream exceptions are converted to typed `InferenceEvent` failures with an explicit embedded fallback;
- a pre-cancelled request does not enter the provider;
- the adapter no longer relies on unchecked Sendable conformance.

## Toolchain harness reconciliation

A clean SwiftPM rebuild on the shared workspace exposed an index-store race and a stale build-database assertion. The local evidence command now uses an isolated disposable scratch directory, one build job, and an enabled index store. This closes the test-harness race only; it does not add Xcode, iOS SDK, simulator, or device evidence.
