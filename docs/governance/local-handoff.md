# Local Handoff Execution Queue

The live queue is stored in GitHub issue bodies after the cloud/static foundation reaches a physical-host boundary. The repository contains only a schema and template.

Each item must bind:

```text
entry condition
→ exact repository commit and artifact digests
→ named host/runtime capabilities
→ concrete argv, cwd, timeout
→ durable redacted receipt
→ exact exit condition
→ next item
```

The first queue is local static replay; later queues cover Android build/device, Apple build/device, model conversion/evaluation, and release convergence. Exactly one item is active. A queue-schema PASS proves only the continuation contract, not execution.
