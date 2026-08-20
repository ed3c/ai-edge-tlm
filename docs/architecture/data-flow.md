# Data flow and ownership

| Data | Producer | Owner | Consumers | Persistence | Egress |
|---|---|---|---|---|---|
| `InferenceRequest` | app/domain | request scope | policy, selector, provider | optional redacted trace | none by default |
| `CapabilityProfile` | platform probes | app runtime | selector, telemetry | device-local cache | aggregate only |
| model manifest | release pipeline | model registry | downloader, provider | public/repo | public metadata |
| model weights | authorized host | model store | embedded provider | app/private storage | no redistribution by default |
| skill metadata | signed source | skill registry | router | app storage | public metadata |
| skill execution bytes | signed source | sandbox | WebView/native broker | bounded cache | origin policy |
| tool proposal | model | orchestrator | policy, validator | receipt metadata | no raw secrets |
| side-effect receipt | tool broker | audit store | orchestrator, review | append-only | redacted |
| private CodexDoc capsule | signed-in connector | session | planning Agent | ephemeral | never public repo |

KV cache and transcripts remain provider/session scoped. Cross-session reuse is opt-in and must declare deletion, isolation, and sensitivity policy.
