---
description: Address open PR review findings while keeping ephemeral review state out of commits
handoffs:
  - label: Re-Review Updated PR
    agent: devspark.pr-review
    prompt: Run /devspark.pr-review UPDATE for this PR after fixes are committed
scripts:
  sh: .devspark/scripts/bash/address-pr-review.sh --pr-id $ARGUMENTS --json
  ps: .devspark/scripts/powershell/address-pr-review.ps1 -PrId $ARGUMENTS -Json
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## DevSpark v4 Override

This command fixes review findings against current truth. When any later
section conflicts with this section, the v4 section wins.

- Resolve findings by changing code, `.knowledge`, or governance as needed.
- Do not introduce permanent references to the review thread or ephemeral work
  package.
- Never commit `.devspark.work` review-thread updates.
- Re-run current-truth validation before marking findings resolved.

## Overview

This command is the **author-side companion** to `/devspark.pr-review`. It helps you address open findings in `/.devspark.work/pr-reviews/pr-{PR_ID}.md` while keeping the permanent commit history focused on real fixes:

1. Commit code, test, documentation, and `.knowledge` fixes.
2. Update the local review work file only as ephemeral status.
3. Run `/devspark.pr-review UPDATE` for a fresh review pass.

**IMPORTANT**: `.devspark.work` is temporary work state and must not be staged.

## Genuine Fix Discipline

Apply `templates/command-preamble-contract.md` §9 while resolving each PR review
finding. A finding is not resolved when the proof only moves a metric and leaves
the behavior named by `intent_cue` unchanged.

## Prerequisites

- Existing PR review file at `/.devspark.work/pr-reviews/pr-{PR_ID}.md`
- Git repository with the PR source branch checked out
- PowerShell 7+ (`pwsh`) on Windows, or Bash on macOS/Linux, for the gate helper script

## Definition of Done

Done when: every selected finding is fixed and committed (Phase 4), the local review file is updated without staging it (Phase 5), and the handoff message is printed (Phase 6). If validation (Phase 3) can't be made to pass, stop and report which finding is blocking — don't keep retrying silently.

## Outline

### Phase 0 — Load context

> **Script Resolution**: Before running `{SCRIPT}`, apply the 2-tier override check — if `.knowledge/overrides/scripts/powershell/address-pr-review.ps1` (PowerShell) or `.knowledge/overrides/scripts/bash/address-pr-review.sh` (Bash) exists on disk, run that file instead, preserving all arguments. Team overrides in `.knowledge/overrides/scripts/` always take priority over `.devspark/scripts/`.

1. Run `{SCRIPT}` with the PR id and JSON output enabled (`-PrId {PR_ID} -Json` on PowerShell, `--pr-id {PR_ID} --json` on Bash).
2. Fail fast if `/.devspark.work/pr-reviews/pr-{PR_ID}.md` is missing.
3. Parse open findings from checklist lines matching:
   - `- [ ] **C-##**`
   - `- [ ] **H-##**`
   - `- [ ] **M-##**`
   - `- [ ] **L-##**`
   - `- [ ] **CON-##**`
4. Confirm current branch equals the PR source branch. Refuse if mismatched.
5. Capture `git status --short`.
6. **Refuse to proceed** if any staged path matches `.devspark.work/pr-reviews/pr-*.md`.

If no open findings remain, print: `Nothing to address.` and stop.

### Phase 1 — Plan

1. Render open findings as a checklist with severity badges.
2. Ask which findings to address this iteration (`all` allowed). **Autonomy override**: if `--auto` (or a standing autonomy instruction) is in effect, skip the ask and select `all` open findings except any `C-NN` (Critical) finding whose fix is ambiguous enough to need a human judgment call — flag those specifically and proceed with the rest.
3. Build an internal todo list with one item per selected finding.

### Phase 2 — Fix loop (per finding)

For each selected finding:

1. Read the cited file/lines and confirm the issue.
2. Apply the recommended fix, or propose an alternative and show the diff.
3. Stage **only** code paths touched by that fix.
4. Never run `git add .`.
5. Never stage `/.devspark.work/pr-reviews/pr-{PR_ID}.md` during this phase.

### Phase 3 — Validate

1. Re-run the **locked pytest scope** from the review file `Stats` table (reuse the same command; do not pick a new scope).
2. Re-run project-specific validators explicitly recorded in the review file.
3. If any validation fails, return to Phase 2.
4. Do not continue until validations pass.

### Phase 4 — Commit code fixes

1. Run gate script with code-only mode before commit (`-Gate code-only` on PowerShell, `--gate code-only` on Bash).
2. If the gate fails, **abort** and print offending staged paths.
3. Review staged diff and commit with:

```text
fix(pr-{PR_ID}): address {M-02,M-04,M-05}
```

1. Capture the resulting short hash as `{FIX_SHA}`.

### Phase 5 — Update the review file

For each fixed finding:

1. Flip `- [ ]` to `- [x]`.
2. Append `— *Fixed in {FIX_SHA}: {one-line how}*` to the finding heading line.
3. Do **not** change finding IDs, descriptions, or broken/fix code blocks.

Then update metadata:

1. Bump revision in the header table (`Rev N -> Rev N+1`).
2. Update `Stats` with current churn/test counts/commit snapshot.
3. Append a new row to `Revision Log` for this iteration.
4. Do not stage the review file. It remains local `.devspark.work` state.

### Phase 6 — Handoff

1. Print the new fix commit hash.
2. Suggest focused re-review:

```text
Run `/devspark.pr-review UPDATE {PR_URL}` to trigger a focused re-review.
```

## Guidelines

### Commit Discipline (MUST)

- No `.devspark.work` path may be staged or committed.
- Review-file updates are local work state until superseded by GitHub PR
  comments, refreshed review output, or deletion after assimilation.
- Do not run `git add .`.

### Gate Execution (MUST)

- Use the helper script as the source of truth for the code-only staging gate.
- If a gate exits non-zero, stop and resolve staging before retrying.

### Edit Scope (MUST)

In review files, limit edits to:

- finding checkbox state
- heading-line fixed-in suffix
- revision metadata (`Revision`, `Stats`, `Revision Log`)

Everything else is immutable during addressing.

## Context

$ARGUMENTS

## Shared Review Resolution Contract Output

When emitting findings (review observations, issues, recommendations), structure each entry to include the shared resolution contract fields so downstream tools (/devspark.address-pr-review, telemetry, harvest) can act on them deterministically:

```yaml
findings:
  - finding_id: <stable-id-unique-within-this-command-output>   # e.g., analyze-001, clarify-002
    severity: critical | high | medium | low
    description: <1-3 sentence problem statement>
    intent_cue: <behavioral intent that must be repaired or preserved>
    recommended_action: <machine-actionable next step>
    execution_mode: auto | selective | manual
    status: open                                                  # set to `resolved` after remediation
    outcome: ""                                                  # populated post-resolution by address-pr-review
```

`finding_id` MUST be stable across re-runs when the underlying issue is unchanged. `intent_cue` MUST name the behavior, contract, safety property, or user outcome the finding protects before metric-focused remediation. `execution_mode` MUST be one of: `auto` (safe to apply automatically), `selective` (apply with reviewer approval), `manual` (requires human implementation). The `status` and `outcome` fields are written by `/devspark.address-pr-review` (FR-028).
