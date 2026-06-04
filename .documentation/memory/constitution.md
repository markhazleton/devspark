# DevSpark Constitution

<!--
  Sync Impact Report — v1.2.0 → v1.3.0 (2026-04-30)
  Amendment: CAP-2026-001 (APPROVED 2026-04-30)
  Bump type: MINOR — new named principle §VIII added
  Modified principles: none renamed
  Added sections: §VIII Markdown Quality (MUST)
  Removed sections: none (Additional Constraints bullet "Markdown linted via
    markdownlint-cli2" promoted into §VIII and removed from bullet list)
  Templates checked:
    ✅ templates/plan-template.md     — no lint references; no update needed
    ✅ templates/spec-template.md     — no lint references; no update needed
    ✅ templates/tasks-template.md    — no lint references; no update needed
    ✅ CONTRIBUTING.md                — added §VIII compliance note
    ✅ .markdownlint-cli2.jsonc       — ignores entries already carry rationale comments
  Follow-up TODOs: none
-->

<!--
  Sync Impact Report — v1.3.0 → v1.4.0 (2026-05-22)
  Amendment: CAP-2026-002 (APPROVED 2026-05-22)
  Bump type: MINOR — §VI promoted from convention to enforced MUST
  Modified principles: §VI Platform Parity — added MUST marker, explicit
    same-commit parity rule, install-both-sets requirement, and HIGH severity
    violation classification
  Added sections: none
  Removed sections: none (Additional Constraints bullet "Scripts in both
    PowerShell and Bash" now covered by §VI MUST and left as-is for brevity)
  Templates checked:
    ✅ quickstart/devspark_quickstart_copilot.md    — already updated (this PR)
    ✅ quickstart/devspark_quickstart_claudecode.md — already updated (this PR)
    ✅ quickstart/devspark_quickstart_cursor.md     — already updated (this PR)
    ✅ quickstart/devspark_quickstart_codex.md      — already updated (this PR)
    ✅ quickstart/devspark_quickstart_generic.md    — already updated (this PR)
    ✅ templates/commands/upgrade.md                — already updated (this PR)
    ✅ templates/commands/address-pr-review.md      — sh variant fixed (this PR)
  Follow-up TODOs:
    - Add §VI parity check to test_script_parity_contract.py (verify every .sh
      has a matching .ps1 and vice versa)
-->

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

### VI. Platform Parity (MUST)

Bash and PowerShell scripts must remain functionally equivalent.
A change to any script in `scripts/bash/` MUST have a corresponding change in
`scripts/powershell/` in the same commit, and vice versa — no script may be
updated in one language without a matching update in the other.
Install and upgrade flows MUST always deliver **both** script sets
(`scripts/bash/` and `scripts/powershell/`) regardless of the developer's
current OS. A repo that has only one set installed is considered broken.
Packaged templates, quickstarts, and CLI behavior must stay aligned with source templates.

Violations are HIGH severity in PR review.

### VII. PR Review Artifact Commit Discipline (MUST)

The PR review file (`.documentation/specs/pr-review/pr-NNN.md`) MUST be committed in isolation.
A commit that touches the review file must not include production code, tests, or other docs.
Code fixes and review-file updates must land in separate commits so revision diffs remain auditable.
Violations are MEDIUM severity process findings in PR review.

### VIII. Markdown Quality (MUST)

All markdown files committed to the repository MUST pass `npx markdownlint-cli2 "**/*.md"`
with zero errors against the project `.markdownlint-cli2.jsonc` configuration.

**MUST requirements:**

- Every markdown file merged to the default branch MUST produce zero markdownlint errors.
- The CI lint job (`.github/workflows/lint.yml`) MUST run on every push and pull request and
  MUST be required-to-pass before merge.
- Every path excluded via the `ignores` block in `.markdownlint-cli2.jsonc` MUST carry an inline
  rationale comment (e.g., `// runtime artifacts — gitignored, not committed`).
- New `ignores` entries MUST be introduced in the same PR that introduces the excluded path pattern,
  not as a retroactive fix after CI failures.
- Runtime-generated markdown (e.g., `.documentation/devspark/runs/**`) MUST be excluded via the
  `ignores` block; runtime tooling is not responsible for linting its own output.

**SHOULD recommendations:**

- Run `npx markdownlint-cli2 "**/*.md"` locally before pushing.
- Use editor integrations (e.g., VS Code markdownlint extension) for real-time feedback.
- Keep the `ignores` list minimal; prefer fixing files over excluding them.
- Place in-progress drafts under a path already in `ignores` (e.g., `.documentation/drafts/`)
  rather than adding a new exclusion.

Violations are HIGH severity in PR review when they block CI; MEDIUM when caught locally before push.

## Additional Constraints

- Python 3.11+ for CLI code, typed with typer/rich/click
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

## Companion Documents

- [Known Governance Limitations](known-limitations.md)
- [Severity Registry](severity-registry.md)
- [Prompt Conformance Manifest](prompt-conformance-manifest.md)

**Version**: 1.4.0 | **Ratified**: 2026-04-06 | **Last Amended**: 2026-05-22
