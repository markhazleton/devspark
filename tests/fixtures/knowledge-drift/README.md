# Knowledge Drift Detection — Fixture Layout

Committed, offline, deterministic fixtures for the knowledge-drift-detection test suite. No
fixture here depends on network access or this repository's own Git history — Git-scope fixtures
build a throwaway local repository at test time via `tests/knowledge_drift_test_helpers.py`.

- `legacy/` — legacy string-item knowledge documents (no `knowledge_drift` opt-in involved).
- `mixed/` — documents containing both legacy string claims and object-form source claims.
- `source/` — plain source files referenced by source claims in other fixture documents.
- `profiles/` — per-comparison-profile fixtures (`python-token-v1`, `exact-text-v1`, `binary-v1`).
- `region/` — named-region resolution and region-widening fixtures.
- `line-ending/` — cross-platform (CRLF/LF) canonicalization identity fixtures.
- `binary/` — binary-content exact-byte comparison fixtures.
- `corruptions/` — test-only self-test-control corruption variants (never shipped to consumers).
- `git-scope/` — seed content for Git-backed base/head routine-scope test repositories.
- `performance-corpus/` — the fixed offline corpus used by the bounded performance contract.

Runtime self-test controls (the positive/negative pair every `--detect-drift` invocation checks
before publishing findings) are **not** here — those ship with the framework under
`templates/knowledge-drift/self-test/` so every installed repository receives them.
