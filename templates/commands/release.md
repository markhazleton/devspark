---
description: Seal a DevSpark release by validating current truth, versioning, release notes, and archived lifecycle cleanup
scripts:
  sh: .devspark/scripts/bash/release-context.sh $ARGUMENTS --json
  ps: .devspark/scripts/powershell/release-context.ps1 $ARGUMENTS -Json
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## DevSpark v4 Override

Release seals current truth. It moves verified specs, quickfixes, review
records, run logs, and other completed lifecycle artifacts from `.devspark.work`
to a human-only `.archive/YYYY-MM-DD/<topic>/` folder. Git remains the durable history
store; the archive is a short-term safety buffer, not current truth.

When any later section conflicts with this section, this v4 section wins.

- Read version context from `.devspark/VERSION`.
- Validate `.knowledge` and governance before changing the version stamp.
- Fail if `.devspark.work/specs/` contains completed work packages whose
  `code_ref` and `knowledge_ref` linkage has not been verified.
- Move verified work packages to `.archive/YYYY-MM-DD/<topic>/` after
  confirming their code, knowledge, and governance deltas landed.
- Generate release notes from Git history and current truth, not from obsolete
  spec folders.
- Never reference `.archive/` paths from permanent code, `.knowledge`, or
  governance files.
- Never read, list, enumerate, or glob `.archive/` under any circumstance.

## Procedure

1. Run `{SCRIPT}` and parse the JSON result.
2. Confirm `CONSTITUTION_PATH` exists.
3. Confirm every entity under `.knowledge/entities/` has `_entity.yaml`,
   evidence, and matching generated `_derived.yaml`.
4. Confirm every decision under `.knowledge/governance/decisions/` has
   frontmatter with `id`, `status: current`, `governs`, `evidence`, and
   `last_verified`.
5. Search permanent content for references to in-flight work package IDs, task
   IDs, old spec folders, review-thread files, or previous lifecycle snapshots.
   Any match outside explicit governance rules is a release blocker.
6. Run the repository's validation suite.
7. Update `.devspark/VERSION` only after validation passes.
8. Move verified `.devspark.work` packages to `.archive/YYYY-MM-DD/<topic>/`.
   Use the current date for `YYYY-MM-DD` and the package, quickfix, or review
   identifier as `<topic>`. When invoking shell helpers, use
   `archive_devspark_work_path` from
   `scripts/bash/common.sh` or `Move-DevSparkWorkPathToArchive` from
   `scripts/powershell/common.ps1`.
9. Draft release notes from Git commits, merged PRs, and current-truth changes.

## Output

Return:

- Current version and next version
- Validation commands run and results
- In-flight work-package status
- Archive destinations used for verified work packages
- Current-truth blockers, if any
- Release-note summary

Do not keep lifecycle artifacts under `.devspark.work/` after verification. If
a verified work package has completed its purpose, move it to the
`.archive/YYYY-MM-DD/<topic>/` folder and report the destination. A human later
decides what, if anything, to delete from `.archive/`.
