# Source, claim, and license closure

Issue: `#2`  
Branch: `evidence/source-closure`  
Parent subject: `e959201574b9548758e9d173b02e214c9e8531e7`

This directory converts the user-supplied architecture cards and current primary sources into three separate, machine-checked planes:

```text
source identity
→ claim applicability/status
→ license/terms plane
→ evidence ceiling
→ downstream start output
```

A source URL, permissive code license, model card, benchmark table, or successful validator does not prove implementation, device performance, legal acceptance, or commercial permission for a model artifact.

## State machine

```text
SOURCE_PACKET_BOUND
→ IMMUTABLE_REPOSITORIES_PINNED
→ ROLLING_DOCS_TIMESTAMPED
→ CLAIMS_CLASSIFIED
→ LICENSE_PLANES_SEPARATED
→ NEGATIVE_CONTROLS_EXERCISED
→ P2_START_OUTPUT_READABLE
```

Residual states remain explicit:

- the original article/video/PDF identity is `SOURCE_PACKET_REQUIRED`;
- rolling Apple/Google SDK documentation must be rechecked at adapter implementation time;
- Gemma/model/SDK/store terms remain `HUMAN_ADMIT_REQUIRED` or `REVIEW_REQUIRED`;
- physical device, model quality, conversion parity, privacy and thermal lanes are not exercised by P0.

## Files

- `source-register.json`: immutable repository revisions and timestamped rolling documents.
- `claim-ledger.json`: one entry for every supplied architecture card.
- `license-register.json`: source-code, model-weight and SDK/store planes kept separate.
- `technology-selection.json`: admitted default, optional, review-only and rejected-commercial-default choices.
- `scripts/validate_evidence.py`: deterministic semantic gate and receipt generator.
- `shadow-checkpoint.md`: Shadow Architect findings and evidence boundary.

## Validation

```bash
python docs/research/scripts/validate_evidence.py
pytest -q tests/p0
edge-tlmctl audit-public-boundary
```

The validator performs no network access. A pass proves internal consistency for these exact bytes; it does not refresh rolling sources.
