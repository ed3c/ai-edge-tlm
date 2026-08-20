# Security policy

## Report a vulnerability

Use GitHub's private vulnerability reporting when enabled. Do not disclose working exploits, credentials, private model URLs, signing keys, or user data in public issues.

## Threat model

The initial threat model covers untrusted model files, untrusted skill bundles, prompt injection, malformed tool calls, WebView bridge abuse, origin confusion, secret exfiltration, cross-session state leakage, dependency substitution, downgrade attacks, replayed side effects, and false evidence promotion.

## Required controls

- content-address model and skill artifacts;
- verify declared source, digest, version, license state, and rollback identity;
- deny network, native bridge, filesystem, sensor, and secret access by default;
- separate model proposals from host authorization;
- bind side effects to idempotency identity and explicit approval policy;
- enforce CSP, origin allowlists, bounded execution, and bridge allowlists for WebViews;
- redact prompts and outputs according to data classification;
- never place secrets in prompts, repository files, logs, issue bodies, receipts, or model manifests;
- destroy or isolate session/KV state according to lifecycle policy;
- retain append-only security and decision receipts without private payloads.
