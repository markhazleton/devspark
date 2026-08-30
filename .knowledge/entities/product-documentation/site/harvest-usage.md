# DevSpark Harvest Usage

`/devspark.harvest` is the v4 cleanup command for current-truth repositories.
It verifies assimilation and moves temporary work state to human-only
`.archive/YYYY-MM-DD/<topic>/` storage.

## Purpose

Harvest checks whether in-flight work packages under `.devspark.work/` have
finished their job:

1. The code delta landed.
2. The `.knowledge` and governance delta landed when required.
3. Completed tasks have `code_ref` and `knowledge_ref` linkage, or explicit
   `n/a` values with reasons.
4. Permanent files do not reference the temporary package, task IDs, plans, or
   review-thread artifacts.

When those checks pass, the package is moved intact to `.archive/YYYY-MM-DD/<topic>/`.
Git remains the durable history for committed states; the human-only archive keeps
recent local work recoverable in the short term.

## Usage

```text
/devspark.harvest
/devspark.harvest --scope=work
/devspark.harvest --scope=knowledge
```

## Expected Output

Harvest reports:

- Work packages inspected
- Packages archived after verification
- Archive root used
- Packages left in place with blockers
- Missing evidence or missing `fallback_reason` warnings
- Permanent-reference violations that must be fixed before archival

## Rules

- Do not preserve completed specs, plans, tasks, or review outputs as durable
  documentation.
- Do not reference `.archive/` paths from permanent code, `.knowledge`, or
  governance.
- Do not read, list, enumerate, or glob `.archive/`.
- Do not rewrite code comments to mention spec IDs, task IDs, or work-package
  IDs.
- Do update `.knowledge` and governance in place before archiving temporary
  work.

## Repair

If harvest refuses to archive a package, fix the reported blocker and run
`/devspark.verify` again. Then rerun `/devspark.harvest`.

If installed framework files are stale or missing, rerun the matching
quickstart prompt for your agent.
