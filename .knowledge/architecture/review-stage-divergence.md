---
id: architecture-review-stage-divergence
type: architecture
title: "Review-Stage Divergence"
appliesTo:
  - templates/commands/clarify.md
  - templates/commands/analyze.md
  - templates/commands/critic.md
  - templates/commands/pr-review.md
  - templates/commands/address-pr-review.md
  - scripts/pr-review-state.py
  - scripts/pr-review-validate.py
  - scripts/bash/address-pr-review.sh
  - scripts/powershell/address-pr-review.ps1
  - templates/pr-review-state-contract.md
  - tests/test_review_resolution_contract.py
  - tests/test_review_stage_divergence_contract.py
  - tests/test_address_pr_review_contract.py
  - tests/test_pr_review_state_contract.py
  - tests/test_pr_review_validate_contract.py
source_of_truth:
  - scripts/pr-review-state.py
  - scripts/pr-review-validate.py
  - scripts/bash/address-pr-review.sh
  - scripts/powershell/address-pr-review.ps1
  - templates/pr-review-state-contract.md
  - tests/test_pr_review_state_contract.py
  - tests/test_address_pr_review_contract.py
  - tests/test_pr_review_validate_contract.py
last_verified: 2026-10-14
---

<!-- markdownlint-disable MD025 -->

# Review-Stage Divergence

This document records the PR-specific extension while keeping the shared review-resolution
contract unchanged for `clarify`, `analyze`, and `critic`.

## Status

## PR finding lifecycle

PR review owns the canonical finding record, and address-PR-review owns author remediation and
submission to independent verification. The structured state is additive and stored in the existing
review Markdown frontmatter. `scripts/pr-review-state.py` owns normalization, transitions,
compatibility projections, derived views, and guarded writes; `scripts/pr-review-validate.py`
checks that those views remain consistent. The two shell helpers share modern inspection and retain
fixture-pinned, read-only legacy parsing when Python or PyYAML is unavailable.

This extension does not change shared finding fields or lifecycle semantics in Clarify, Analyze, or
Critic. Author remediation remains pending until an independent permitted reviewer evaluates the
original concern and correction. Review counts, action/detail views, applicable conditions, and the
local recommendation are derived from the canonical record. A local recommendation is not a hosted
approval vote or merge authorization.

Generated Action Items, Findings Detail, Current Review State, and Approval Decision sections are
delimited by the PR review-state markers and replaced from the record. Narrative, risk analysis,
observations, and evidence outside those markers remain reviewer-owned.

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

| Stage | Marker text | Reason |
|-------|-------------|--------|
| PR review and address-PR-review | `pr-review-state` | PR closeout requires an independent-verification lifecycle and derived report views; other stages retain the shared contract unchanged. |
