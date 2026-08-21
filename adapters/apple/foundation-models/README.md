# Apple Foundation Models system adapter

This module is the provider-private boundary over the P2 Swift contracts. The first vertical slice is deliberately `FoundationModels`-SDK-free: a fake session exercises availability revisions, versioned prompt profiles, prewarm/session lifecycle, streaming, cancellation, tool proposals, context failures, request-owner isolation and explicit embedded-TLM fallback.

## State machine

```text
OBSERVED -> PROBED -> AVAILABLE | UNAVAILABLE | STALE
AVAILABLE + PROMPT_PROFILE_MATCH -> PREWARMED -> STREAMING
STREAMING -> COMPLETED | CANCELLED | DEGRADED | FAILED
UNAVAILABLE | STALE | DEGRADED | FAILED -> APPLE_LITERT | FAIL_CLOSED
```

Provider output may create a P2 `ToolProposal`; this module never creates a `ToolAdmission` or executes a native effect.

## Evidence ceiling

Swift/Linux package tests prove adapter semantics only. `FoundationModels` SDK compilation, Xcode/iOS build, supported physical-device and region availability, system-model revision, signing/provisioning, output quality, privacy, energy and thermal behavior remain `NOT_EXERCISED` or `HUMAN_ADMIT_REQUIRED`.
