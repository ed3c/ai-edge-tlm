# Original article / talk source packet

## Current state

`SOURCE_PACKET_REQUIRED`

The issue contains detailed cards and timestamp references but no canonical article, video, transcript, PDF URL, file digest, speaker/event identity, or immutable source bytes. P0 preserves each card ID in `claim-ledger.json` but refuses to promote talk-specific numbers or quotes to corroborated facts solely from the supplied narrative.

## Unblock contract

Supply at least one of:

1. canonical public article/video URL plus publication/event identity;
2. attached PDF/transcript with SHA-256 and page/line or timestamp locations;
3. immutable repository/document revision that contains the cited material.

After admission, re-run source extraction and update only the claims supported by the exact source. Existing corrections based on newer official documentation remain separate rather than being overwritten.
