# Android LiteRT-LM embedded adapter

Provider-private boundary for app-embedded `.litertlm` models. The first slice is SDK-independent and uses a fake runtime to verify artifact admission, background loading, backend observation, streaming, cancellation, tool-proposal-only behavior, and fail-closed fallback.

State machine:

```text
ADMITTED_ARTIFACT -> LOAD_REQUESTED -> LOADING -> READY
READY -> STREAMING -> COMPLETED | CANCELLED | FAILED
UNSUPPORTED_BACKEND -> EXPLICIT_CPU_FALLBACK | FAIL_CLOSED
OOM / STALE_ARTIFACT / DIGEST_MISMATCH -> FAIL_CLOSED
```

The adapter reports `requestedBackend`, `selectedBackend`, and runtime `observedBackend` separately. It never treats requested NPU as NPU evidence and never executes a model tool proposal.

Current source pin records LiteRT-LM `v0.14.0` with Kotlin marked Stable upstream, Swift Early Preview, and a release-integrity warning. Static/local tests do not prove Android Gradle or physical-device behavior.
