# Contributing

1. Open or select a task packet with exact scope, allowed paths, dependencies, gates, negative controls, and evidence boundary.
2. Use a feature branch and one writer per active path lease.
3. Add or update contracts before platform-specific implementation.
4. Add a test that can fail for the defect or capability being introduced.
5. Run `edge-tlmctl validate`, `edge-tlmctl audit-public-boundary`, and `pytest -q`.
6. Keep model weights, private datasets, private Google Workspace URLs, credentials, and commercial roadmap text out of the repository.
7. State `NOT_IMPLEMENTED` and `NOT_EXERCISED` explicitly rather than smoothing gaps into completion.

PR publication, merge, releases, store submissions, model-term acceptance, and secrets remain Human-owned.
