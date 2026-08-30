# Review-Stage Divergence

This document enumerates per-stage behavior differences across the five review
prompts (`clarify`, `analyze`, `critic`, `pr-review`, `address-pr-review`) and
tracks any commands that resist the thin-shim model.

## Status

**No divergent stages declared at this time.**

The shared review-resolution contract emitted by Phase 8 (T050–T055) is
sufficient for all five stages. Each stage continues to render its own
prose recommendations, but the structured `findings[]` block conforms to a
single shape with the fields documented in
`tests/test_review_resolution_contract.py`.

## Thin-Shim Spike

The thin-shim model under `templates/prompts/atomic/<command>.md` was
validated against the three commands carrying the most prose business logic:

| Command              | Verdict | Notes |
|----------------------|---------|-------|
| `address-pr-review`  | Sufficient | Shim points to `templates/commands/address-pr-review.md`; commit-isolation prose remains in the canonical command file. |
| `harvest`            | Sufficient | Shim points to canonical file; work-package cleanup context is owned by `scripts/*/harvest.*`, not the prompt. |
| `commit-audit`       | Sufficient | Shim points to canonical file; commit-mining logic is owned by `scripts/*/release-history-context.*`. |

No command requires bespoke prose duplicated under `templates/prompts/atomic/`.
The prompt adapter resolves the shim id, then forwards execution to the
canonical command body via the existing 3-tier override chain.

## Divergence Marker Convention

If a future review stage introduces a documented divergence, mark the
relevant atomic prompt body with:

```html
<!-- DIVERGENT: <one-line reason> -->
```

Then add a row to the table below. The contract test
`tests/test_review_stage_divergence_contract.py` will fail if a
prompt declares `<!-- DIVERGENT: ... -->` without an entry here.

| Stage | Marker text | Ticket | Resolution plan |
|-------|-------------|--------|-----------------|
| *none* | *n/a* | *n/a* | *n/a* |
