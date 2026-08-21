# Skill registry, tool broker, and sandbox policy

The host loads metadata first, routes deterministically, verifies immutable package identity as `UNTRUSTED`, requires an explicit host trust decision for that exact digest, and only then exposes full instructions. Model output is a `ToolProposal`; only host policy can create a `ToolAdmission`.

```text
metadata index -> deterministic route -> integrity + origin admission
               -> instruction load -> tool proposal -> host admission
               -> sandbox policy -> isolated execution -> typed result -> cleanup
```

The process runner is a deterministic policy harness, not a production WebView implementation or exploit-resistance proof.
