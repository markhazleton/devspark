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

Release is the only DevSpark command that moves work out of `.devspark.work/`.
It is the sole command that sweeps completed, linkage-verified specs and
quickfixes, routine work-product retention, and orphaned in-flight state into
`.archive/`. The only other writers of `.archive/` are `/devspark.constitution`
and `/devspark.evolve-constitution`, and only for their own resolved
constitution proposals.

Verify before archive is a two-stage gate. `/devspark.implement` verifies the
delta and populates each task's linkage, then deliberately leaves the package
live in `.devspark.work/`. Release re-checks that linkage and performs the move.
A verified package may stay unarchived across more than one release window;
that is normal, not a stall.

Release moves each eligible package intact (plan, tasks, checklists, gates,
`context_resolved`) to `.archive/YYYY-MM-DD/`, preserving its path relative to
`.devspark.work/`. Git remains the durable history. `.archive/` is write-only:
no DevSpark command reads, lists, enumerates, or globs it, and only a human
purges it or copies a file back out.

## Release Eligibility

A work package is release-eligible only when all of the following are true:

- Its spec or quickfix status is complete. Stalled or incomplete records never
  move.
- Every task is complete.
- Every task has a populated `code_ref` and `knowledge_ref`, plus `test_ref`,
  or an explicit `n/a — <reason>` for a category that does not apply.
- Every governance-changing task has a populated `governance_ref`; other tasks
  may use an explained `n/a`.
- Referenced code, test, knowledge, and governance files still exist. A
  `code_ref` that went stale after a later refactor is a blocker to repair, not
  a reason to skip the check.
- Referenced tests pass using the repository's native test command.
- Every touched knowledge entity and decision cites at least one piece of
  evidence. Missing evidence is a blocker (engine `missing-evidence` error).
  Code-only evidence without `fallback_reason` is a warning only.
- The knowledge engine's `--check` passes: `index.json` and `coverage.json`
  are current and there are no gating errors.
- Permanent code and knowledge contain no references back to work-package,
  task, plan, review-thread, or archive artifacts, and no code comment names a
  spec ID, task ID, or plan identifier.

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
4. Resolve every task linkage. The pre-scan already blocks packages whose
   concrete refs do not resolve and lists them in `UNRESOLVED_LINKAGE_REFS`
   (`<package>: <ref>`); report each as a blocker to repair. Strip any
   `::symbol` or `#fragment` only when checking the containing file; preserve
   the full reference in the work package.
5. Run every test named by `test_ref`, plus the repository's required release
   validation suite. An explained `n/a` is allowed only for tasks that cannot
   reasonably have a test.
6. Validate `.knowledge` and governance with the knowledge engine named by
   `KNOWLEDGE_ENGINE.engine` (resolved by `resolve_knowledge_engine`):
   `python <engine> --check`. If `KNOWLEDGE_ENGINE.legacy_copies` is non-empty,
   report it as an upgrade task; never run a legacy copy.
7. Search permanent content for forbidden references to ephemeral artifacts.
8. If any candidate fails, leave it in `.devspark.work/`, do not update the
   version, and report exact blockers.
9. Update `.devspark/VERSION` only after all release validation passes.
10. Move each validated package and staged release candidate to
    `.archive/YYYY-MM-DD/<path relative to .devspark.work>/` using
    `archive_devspark_work_path` from `scripts/bash/common.sh` or
    `Move-DevSparkWorkPathToArchive` from `scripts/powershell/common.ps1`.
11. Sweep routine work products whose retention purpose has ended (PR reviews
    and review state for merged or closed PRs, site audits, commit audits,
    repo stories) and orphaned in-flight state with the same helper. Never
    sweep a stalled or incomplete spec or quickfix.
12. Do not read, list, enumerate, glob, or summarize `.archive/` after the move.
13. Draft release notes from Git commits, merged PRs, and the validated current
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
command, incomplete work remains in `.devspark.work/`, and no command read
`.archive/`.
