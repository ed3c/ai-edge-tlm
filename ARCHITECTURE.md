# Architecture

## Invariants

1. The domain layer depends on contracts, not Android, Apple, LiteRT-LM, model brands, or store services.
2. Provider selection is a deterministic host decision over explicit capability, policy, task, privacy, latency, memory, and availability inputs.
3. The selected model may propose a tool call; only the tool broker can admit execution.
4. All externally sourced model and skill artifacts are content-addressed and versioned.
5. Every fallback is explicit and observable. Silent cloud fallback is forbidden.
6. Session/KV-cache ownership is provider-local and cannot leak data across request or user boundaries.
7. Public repository content contains no private control-plane URL or secret.

## Layers

```text
Application/UI
  ↓
Domain contracts and use cases
  ↓
Capability + policy + provider selection
  ↓
Deterministic orchestration and tool broker
  ↓
Provider adapters
  ├─ Android system GenAI
  ├─ Apple Foundation Models
  ├─ LiteRT-LM Android
  ├─ LiteRT-LM Apple
  └─ optional custom provider
  ↓
Model/session/hardware runtime
```

## System SLM vs embedded TLM

System providers are preferred for general tasks when their capability is present and product requirements permit OS-version dependence. Embedded TLMs are preferred for stable cross-platform contracts, private schemas, specialized function calling, offline behavior on unsupported system-model devices, and product-owned model versioning.

The boundary is capability-driven rather than parameter-count-driven. Parameter ranges are planning hints, not invariants.

## Chained specialists

A complex flow is represented as a host-owned DAG of typed steps. Each step declares input/output schema, provider/model requirement, side-effect class, timeout, retry policy, and failure edge. A tiny model does not receive authority to invent an unbounded chain.

## Compatibility policy

- `.litertlm` is the primary embedded LLM container for LiteRT-LM.
- MediaPipe `.task` remains a compatibility concern for existing or non-LiteRT-LM flows; migration is gated by the specific API and artifact.
- iOS LiteRT-LM initially targets CPU/GPU (Metal). NPU/ANE support is not assumed.
- Swift LiteRT-LM is isolated behind an adapter until the selected version and API reach the repository's stability threshold.
- Apple system models and app-embedded LiteRT-LM are separate providers even if a future adapter offers a common session API.

## Failure model

Failures are typed as capability unavailable, policy denied, artifact invalid, model load failed, generation failed, schema invalid, tool denied, tool failed, validation failed, exhausted fallback, or cancelled. Transport success alone is not task success.
