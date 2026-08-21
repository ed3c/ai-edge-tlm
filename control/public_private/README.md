# Public/private control-plane boundary

Issue: `#7`  
Branch: `control/public-private-boundary`  
Parent subject: `e959201574b9548758e9d173b02e214c9e8531e7`

This module defines the public contract for resolving private CodexDoc context without putting private locations, credentials, strategy, roadmap, prompt history, datasets, or user data into Git or model context.

```text
PUBLIC_TASK_BOUND
→ RESOLVER_PRESENCE_INSPECTED
→ SIGNED_IN_CARRIER_REQUIRED
→ PRIVATE_SOURCE_READ_OUT_OF_BAND
→ REQUEST_FIELDS_CLASSIFIED
→ BOUNDED_CAPSULE_BUILT
→ DLP_AND_SIZE_GATES
→ TASK_SUBJECT_EXPIRY_VERIFIED
→ CAPSULE_ADMITTED | ABSENT | REJECTED
```

The implementation deliberately does not fetch Google Workspace content. A signed-in connector/runtime owns retrieval. This repository receives only an allowlisted, bounded Context Capsule bound to an exact task and repository subject.

## Public values

Public code may contain:

- opaque context ID `CDX-AI-EDGE-001`;
- environment-variable **names** for resolver locations;
- allowlisted technical capsule field names;
- carrier presence state and evidence metadata.

It may not contain resolver values, Workspace URLs, credentials, secret material, commercial roadmap, raw prompt history, private datasets, source-packet bytes, user data, or model-access grants.

## Validation

```bash
pytest -q tests/p1
edge-tlmctl audit-public-boundary
pytest -q
```

A green P1 result proves the public contract and deterministic DLP/capsule behavior for exact bytes. It does not prove Drive ACLs, signed-in connector authorization, private-document truth, or Human approval.
