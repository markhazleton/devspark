# DevSpark Constitution

## Core Principles

### I. Backward Compatibility (NON-NEGOTIABLE)

Existing single-application repositories must continue to work without restructure or behavior changes.
New capabilities are additive; they must never force migration on repositories that do not opt in.

### II. Explicit Over Implied (NON-NEGOTIABLE)

Application scope, review scope, and governance scope must be declared explicitly.
DevSpark must not silently infer scope from working directory, branch naming, or heuristic detection.
Ambiguous context must produce a clear error, not a guess.

### III. Ownership Boundary (NON-NEGOTIABLE)

`.devspark/` is the installed framework payload and the only directory DevSpark installs, upgrades, or
removes. `.documentation/` directories at repo and app level are repository-owned work product.
Install and upgrade flows must never add, remove, or modify files under any `.documentation/` directory.

Runtime tooling MAY write under a gitignored subtree of `.documentation/` (for example,
`.documentation/telemetry/`) provided **all** of the following hold:

- the destination subtree is covered by `.gitignore`;
- the path is overridable via an environment variable (e.g., `DEVSPARK_TELEMETRY_PATH`,
  `DEVSPARK_RUNS_PATH`);
- the writer is fail-soft on I/O errors and never blocks the developer's workflow;
- the `.gitignore` rule covering the subtree MUST exist in the default branch (`main`) **before**
  any run artifacts are first generated in that subtree (commit ordering constraint — prevents
  accidental tracking of runtime output when the ignore rule and artifacts land in the same PR).

Install and upgrade flows are still strictly forbidden from touching any path under `.documentation/`.

### IV. Governance Authority

Repository-wide governance is authoritative over all applications.
Application-level governance may extend or strengthen repo-wide rules but must never weaken mandatory
repo-wide rules. Constitution violations are showstopper severity in reviews.

### V. Simplicity

Prefer conventions over configuration. Prefer simple resolution models over flexible ones.
Complexity must be justified and tracked. Reject abstractions that serve only one use case.

### VI. Platform Parity

Bash and PowerShell script behavior must remain functionally equivalent.
Packaged templates, quickstarts, and CLI behavior must stay aligned with source templates.

### VII. PR Review Artifact Commit Discipline (MUST)

The PR review file (`.documentation/specs/pr-review/pr-NNN.md`) MUST be committed in isolation.
A commit that touches the review file must not include production code, tests, or other docs.
Code fixes and review-file updates must land in separate commits so revision diffs remain auditable.
Violations are MEDIUM severity process findings in PR review.

## Additional Constraints

- Python 3.11+ for CLI code, typed with typer/rich/click
- Markdown linted via markdownlint-cli2
- Scripts in both PowerShell and Bash; context scripts support GitHub, AzDO, and GitLab
- Never overwrite `.documentation/` user artifacts during CLI operations

## Development Workflow

- All PRs and reviews must verify compliance with this constitution
- Complexity additions require documented justification and a rejected-simpler-alternative rationale
- Features must be spec-driven: specify first, plan second, implement third
- Cross-cutting changes require leadership approval before implementation begins

## Governance

This constitution supersedes all other development practices in the DevSpark repository.
Amendments require: documentation of the change, leadership approval, and a migration plan for any
affected workflows or repositories.

**Version**: 1.2.0 | **Ratified**: 2026-04-06 | **Last Amended**: 2026-04-18
