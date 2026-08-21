# Public/private control-plane boundary

## Contract

Public repository state contains technical contracts and evidence only. The private CodexDoc control plane may contain product intent, roadmap, private prompt lineage, restricted source packets, private data decisions and Google Workspace links. The two planes meet only through a trusted signed-in carrier that emits a bounded Context Capsule.

```text
public task + exact repository subject
→ inspect resolver-key presence without reading values
→ signed-in carrier retrieves private source out of band
→ classify requested fields
→ copy only allowlisted technical values
→ reject URLs/secrets/oversize/stale/cross-task data
→ bind task + subject + expiry + digest
→ admit capsule or return ABSENT/REJECTED
```

## Public invariants

1. `CDX-AI-EDGE-001` is the only public context identity.
2. Public code may name resolver environment keys but never expose their values.
3. The repository implementation performs no Google Drive network retrieval.
4. Capsule fields are closed and allowlisted; unknown fields fail closed.
5. Capsules are bound to one task, one exact repository SHA, an expiry and a canonical digest.
6. A digest is integrity metadata, not a signature or authorization proof.
7. Private source truth and Drive ACL correctness remain `PRIVATE`; merge/terms/release remain `HUMAN`.

## Classification

Allowed technical fields:

- architecture decisions;
- technical constraints;
- non-goals;
- public source IDs;
- prompt contract ID;
- required evidence lanes.

Never capsule:

- Google Workspace URLs or resolver values;
- credentials, tokens, cookies, signing/private keys;
- commercial intent, product positioning or roadmap;
- raw prompt history;
- private datasets, user data or private source bytes;
- model-access grants;
- legal, merge, release or store approvals.

## Evidence ceiling

Local deterministic tests prove classification, DLP, size, digest, task/subject and expiry behavior for exact code. They do not prove a signed-in connector retrieved the correct private document, that Drive ACLs are correct, or that a Human authorized disclosure.
