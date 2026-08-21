# P8 Shadow Architect checkpoint

Outcome: CONTINUE_WITH_WARNINGS_L1

- Exact sibling heads are immutable read-only inputs; no sibling PR merge is required.
- Host glue owns policy/routing only and imports P2 contracts, not provider SDK types.
- Requested backend is never treated as observed-backend evidence.
- System/embedded provider routing is explicit; cloud/network fallback is not implicit.
- ToolProposal cannot become an effect without host admission.
- Static/local gates cannot close Android Gradle, Xcode/iOS, physical-device, quality, privacy, power, thermal, terms, signing, store, merge, or release lanes.
