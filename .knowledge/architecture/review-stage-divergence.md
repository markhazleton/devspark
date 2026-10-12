# Review-Stage Divergence

This document enumerates per-stage behavior differences across the five review
prompts (`clarify`, `analyze`, `critic`, `pr-review`, `address-pr-review`) and
tracks any commands that resist the thin-skill model.

## Status

**No divergent stages declared at this time.**

The shared review-resolution contract is sufficient for all five stages. Each stage continues to render its own
prose recommendations, but the structured `findings[]` block conforms to a
single shape with the fields documented in
`tests/test_review_resolution_contract.py`.

## Thin-Skill Validation

The thin-skill model — each command's `.github/skills/devspark-<command>/SKILL.md` routing straight to
`templates/commands/<command>.md` — was validated against the commands carrying the most prose
business logic:

| Command              | Verdict | Notes |
|----------------------|---------|-------|
| `address-pr-review`  | Sufficient | Skill points to `templates/commands/address-pr-review.md`; commit-isolation prose remains in the canonical command file. |
| `commit-audit`       | Sufficient | Skill points to canonical file; commit-mining logic is owned by `scripts/*/commit-audit-context.*`. |

No command requires bespoke prose duplicated in a skill. Consumer skills resolve the canonical command
body through the existing three-tier override chain.

## Divergence Marker Convention

If a future review stage introduces a documented divergence, mark the
relevant command template body with:

```html
<!-- DIVERGENT: <one-line reason> -->
```

Then add a row to the table below. The contract test
`tests/test_review_stage_divergence_contract.py` will fail if a
prompt declares `<!-- DIVERGENT: ... -->` without an entry here.

| Stage | Marker text | Ticket | Resolution plan |
|-------|-------------|--------|-----------------|
| *none* | *n/a* | *n/a* | *n/a* |
