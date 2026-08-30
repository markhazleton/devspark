---
description: Sweep DevSpark v4 current truth and archive verified ephemeral work packages
scripts:
  sh: .devspark/scripts/bash/harvest.sh $ARGUMENTS --json
  ps: .devspark/scripts/powershell/harvest.ps1 $ARGUMENTS -Json
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## DevSpark v4 Override

Harvest validates that durable knowledge has been assimilated into current
truth, then moves ephemeral work packages whose purpose is complete to
human-only `.archive/YYYY-MM-DD/<topic>/` storage.

When any later section conflicts with this section, this v4 section wins.

- Work packages live only under `.devspark.work/`.
- Permanent truth lives under code, `.knowledge/`, and active governance files.
- Git is the durable historical record for committed states.
- `.archive/YYYY-MM-DD/<topic>/` is a short-term safety buffer for recently finalized or
  abandoned local work state; it is not durable knowledge.
- No DevSpark command may read, list, enumerate, or glob `.archive/`.
- Do not preserve completed specs, plans, tasks, reviews, or run logs as
  durable repository documents.
- Move the whole package intact under a dated folder, for example
  `.devspark.work/specs/001-x` becomes `.archive/YYYY-MM-DD/001-x/`.

## Procedure

1. Run `{SCRIPT}` and parse the JSON result.
2. For each `archive_candidates` entry, verify all completed tasks have valid
   `code_ref` and `knowledge_ref` values or explicit `n/a` reasons.
3. Confirm referenced code and knowledge files exist.
4. Confirm touched knowledge and decision files contain evidence.
5. Search permanent files for references to the candidate work-package ID,
   task IDs, spec IDs, or planning artifact paths.
6. If every check passes, move the candidate package intact from
   `.devspark.work/` to `.archive/YYYY-MM-DD/<topic>/`. Use the current date
   for `YYYY-MM-DD` and the package, quickfix, or review identifier as
   `<topic>`. When invoking shell helpers, use
   `archive_devspark_work_path` from
   `scripts/bash/common.sh` or `Move-DevSparkWorkPathToArchive` from
   `scripts/powershell/common.ps1`.
7. If any check fails, leave the package in place and report the blocker.

## Output

Return:

- Work packages inspected
- Packages archived after verification
- Packages blocked and why
- Current-truth warnings, especially missing `fallback_reason` on inspection
  evidence

The correct terminal state after successful harvest is no verified package left
under `.devspark.work/`; recently finalized work is retained under the
`.archive/YYYY-MM-DD/<topic>/` folder. A human later decides what, if anything,
to delete from `.archive/`.
