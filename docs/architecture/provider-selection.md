# Provider selection

Provider selection is deterministic over explicit facts.

## Inputs

- task and required modalities;
- offline and privacy requirements;
- system-provider availability;
- model/artifact admission state;
- memory/storage limits;
- latency target;
- requested tool/schema capability;
- runtime maturity policy;
- current thermal and battery policy;
- product-approved fallback chain.

## Default order

1. A system provider for general tasks when available and sufficient.
2. An embedded specialized TLM for private schemas, stable behavior, unsupported system devices, or product-owned model versions.
3. A larger embedded SLM only when memory/thermal policy admits it.
4. An explicit cloud provider only when the request and product policy allow network egress.
5. Typed failure or degraded non-AI behavior.

The selector must explain every rejection and selected fallback. Silent provider changes are forbidden.
