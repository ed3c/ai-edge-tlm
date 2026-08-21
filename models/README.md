# Model artifact supply chain

This module owns model metadata and local content-addressed lifecycle behavior. It never stores model weights, access tokens, signed URLs, or private source locations in Git.

```text
source stream -> quarantine -> digest/size/format/tokenizer/runtime/terms checks
              -> immutable object -> atomic active pointer -> rollback ledger
```

Artifact identity, legal/terms admission, runtime compatibility, device compatibility, model quality, and release authority are separate evidence states.
