# Android system GenAI adapter

This module is a provider-private boundary over the P2 contracts. The first vertical slice is deliberately SDK-free: a fake provider exercises capability revisioning, streaming, cancellation, tool proposals, typed failures, and explicit embedded-TLM fallback.

## State machine

```text
OBSERVED -> PROBED -> AVAILABLE | UNAVAILABLE | STALE
AVAILABLE -> STARTED -> STREAMING -> COMPLETED | CANCELLED | FAILED
UNAVAILABLE | STALE | FAILED -> EMBEDDED_TLM | FAIL_CLOSED
```

`CLOUD` is not a fallback target. Provider output may produce a `ToolProposal`, but this adapter never executes it.

## Evidence ceiling

The Kotlin/JVM compile and fake-provider tests prove mapping semantics only. Android Gradle, ML Kit/AICore availability, physical-device behavior, latency, privacy, provider model revision, SDK terms, and store readiness remain `NOT_EXERCISED` or `HUMAN_ADMIT_REQUIRED`.
