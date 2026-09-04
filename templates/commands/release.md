---
description: Validate code, tests, knowledge, and task linkage, then seal and archive a DevSpark release
scripts:
  sh: .devspark/scripts/bash/release-context.sh $ARGUMENTS --json
  ps: .devspark/scripts/powershell/release-context.ps1 $ARGUMENTS -Json
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Lifecycle Authority

Release is the only DevSpark command that writes to `.archive/`.

Implementation updates code, tests, `.knowledge`, governance when applicable,
and task linkage inside the work package. Verification and PR review may validate
that state, but every work product remains in `.devspark.work/` until this
command runs.

Release performs the final validation and then moves each eligible completed
work package intact to `.archive/YYYY-MM-DD/<topic>/`. Git remains the durable
history; `.archive/` is a short-term, human-only safety buffer and is never an
input to a DevSpark command.

## Release Eligibility

A work package is release-eligible only when all of the following are true:

- Its spec or quickfix status is complete.
- Every task is complete.
- Every task has a populated `code_ref`, `test_ref`, and `knowledge_ref`, or an
  explicit `n/a — <reason>` for a category that does not apply.
- Every governance-changing task has a populated `governance_ref`; other tasks
  may use an explained `n/a`.
- Referenced code, test, knowledge, and governance files exist.
- Referenced tests pass using the repository's native test command.
- Touched knowledge entities and governance decisions report evidence status.
  Missing evidence is a strong warning, not an automatic release blocker;
  unsupported claims must not be described as verified.
- Generated ontology output is current.
- Permanent code and knowledge contain no references back to work-package,
  task, plan, review-thread, or archive artifacts.

Incomplete or invalid packages remain unchanged in `.devspark.work/` and are
reported as release blockers. Completion or verification alone never archives
anything.

## Procedure

1. Run `{SCRIPT}` and parse the JSON result.
2. Confirm `CONSTITUTION_PATH` exists.
3. Inspect every `RELEASE_ELIGIBLE_WORK_PACKAGES` and
   `RELEASE_ELIGIBLE_QUICKFIXES` candidate, plus each completed item under
   `.devspark.work/release-candidates/`. Treat the script result as a pre-scan,
   not proof of validity.
4. Resolve every task linkage. Strip any `::symbol` or `#fragment` only when
   checking the containing file; preserve the full reference in the work
   package.
5. Run every test named by `test_ref`, plus the repository's required release
   validation suite. An explained `n/a` is allowed only for tasks that cannot
   reasonably have a test.
6. Validate `.knowledge` and governance, including generated `_derived.yaml`
   files and evidence references. Run the ontology generator in `--check` mode
   when available.
7. Search permanent content for forbidden references to ephemeral artifacts.
8. If any candidate fails, leave it in `.devspark.work/`, do not update the
   version, and report exact blockers.
9. Update `.devspark/VERSION` only after all release validation passes.
10. Move each validated package and staged release candidate to
    `.archive/YYYY-MM-DD/<topic>/` using
    `archive_devspark_work_path` from `scripts/bash/common.sh` or
    `Move-DevSparkWorkPathToArchive` from `scripts/powershell/common.ps1`.
11. Do not read, list, enumerate, glob, or summarize `.archive/` after the move.
12. Draft release notes from Git commits, merged PRs, and the validated current
    truth—not from `.archive/`.

## Output

Return:

- Current version and next version
- Validation commands and results
- Packages released and archive destinations written
- Packages retained in `.devspark.work/` and their blockers
- Code, test, knowledge, governance, or linkage failures
- Release-note summary

The successful terminal state is: validated release work is archived by this
command, incomplete work remains in `.devspark.work/`, and no other DevSpark
command has written to `.archive/`.
