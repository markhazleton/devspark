# DevSpark Constitution

## Core Principles

### I. Backward Compatibility (NON-NEGOTIABLE)

Existing single-application repositories must continue to work without restructure or behavior changes.
New capabilities are additive; they must never force migration on repositories that do not opt in.

**Repository layout at a framework-version boundary (amended v1.5.0):** A new framework version MAY
define a new canonical repository layout. When it does, ALL of the following MUST hold:

- The new *capabilities* (schemas, registries, indexes, classifiers) remain additive: with no
  configuration and without adopting the new layout, classification and generation behavior equals
  the prior version's behavior.
- Adopting the new layout is an explicit, human-run, opt-in migration — a documented migration path
  and/or a fresh reinstall. It is NEVER performed automatically by install or upgrade.
- The migration preserves the constitution and all human-authored knowledge and is reversible via
  version control.

A framework-version boundary is the ONLY place a canonical-layout change may be introduced, and only
under these conditions. Within a version, existing repositories continue to work without restructure.

**Entity-ontology superset (amended v4.1.0):** `.knowledge/entities/<id>/` is an
additional, opt-in knowledge layout alongside the existing flat type-folder layout introduced in
v4.0.0. It satisfies the framework-version-boundary conditions above: repositories that do not adopt
`entities/` see no change in classification or generation behavior; adoption is via the explicit,
human-run `scripts/migrate-knowledge-to-entities.py`; and moves are performed with `git mv`,
reversible via version control.

### II. Explicit Over Implied (NON-NEGOTIABLE)

Application scope, review scope, and governance scope must be declared explicitly.
DevSpark must not silently infer scope from working directory, branch naming, or heuristic detection.
Ambiguous context must produce a clear error, not a guess.

### III. Ownership Boundary (NON-NEGOTIABLE)

`.devspark/` is the installed framework payload and the only directory DevSpark installs, upgrades, or
removes. All other repository roots are repository-owned work product. As of v1.5.0 the repository-owned
roots are:

- `.devspark.work/` — DevSpark-generated work products (specs, quickfixes, pr-reviews, audits,
  metrics, telemetry, DevSpark configuration).
- `.knowledge/` — long-term knowledge for both agents and users: current authoritative technical and
  governance truth, plus published user-facing guidance under `.knowledge/guides/`. `.documentation/`
  is a legacy, pre-v6 location for the latter — no longer written to; the four-root migration folds
  any remaining content into `.knowledge/guides/`.
- `.archive/` — the landing place for all old work products, grouped by release. This source
  repository authors the product website under `site/src/` and generates `site/_site/`.

**Retiring `.devspark.work/` planning artifacts (amended v5.0.0):** completed specs, quickfixes, and
governance proposals under `.devspark.work/` are archived, not deleted. `/devspark-release`,
`/devspark-constitution`, and `/devspark-evolve-constitution` move a finished
artifact to `.archive/{YYYY-MM-DD}/` (preserving its relative path minus the `.devspark.work/`
prefix) instead of removing it outright — this preserves short-lived value that hasn't yet made it
into a commit, without requiring one. `.archive/` is write-only from every DevSpark command's
perspective: no command reads, lists, or globs it after moving content there, under any
circumstance. Purging `.archive/` is a human action only, on no schedule any DevSpark command
enforces. This applies only to `.devspark.work/` work products; `.knowledge/`
content is never archived — it is corrected in place or deleted, with Git as its sole history.

Install and upgrade flows must never add, remove, or modify files under `.devspark.work/`, `.knowledge/`,
or `.archive/` (at repo or app level). DevSpark commands MAY generate or update files under
`.devspark.work/` and `.knowledge/` at runtime, subject to the runtime-write rules below.

Runtime tooling MAY write under a gitignored subtree of a repository-owned root (for example,
`.devspark.work/telemetry/`) provided **all** of the following hold:

- the destination subtree is covered by `.gitignore`;
- the path is overridable via an environment variable (e.g., `DEVSPARK_TELEMETRY_PATH`,
  `DEVSPARK_RUNS_PATH`);
- the writer is fail-soft on I/O errors and never blocks the developer's workflow;
- the `.gitignore` rule covering the subtree MUST exist in the default branch (`main`) **before**
  any run artifacts are first generated in that subtree (commit ordering constraint — prevents
  accidental tracking of runtime output when the ignore rule and artifacts land in the same PR).

Install and upgrade flows are still strictly forbidden from touching any path under a repository-owned
root (`.devspark.work/`, `.knowledge/`, `.archive/`).

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

The PR review file (`.devspark.work/pr-review/pr-NNN.md`) MUST be committed in isolation.
A commit that touches the review file must not include production code, tests, or other docs.
Code fixes and review-file updates must land in separate commits so revision diffs remain auditable.
Violations are MEDIUM severity process findings in PR review.

### VIII. Markdown Quality (MUST)

All markdown files committed to the repository MUST pass `npx markdownlint-cli2 "**/*.md"`
with zero errors against the project `.markdownlint-cli2.jsonc` configuration.

**MUST requirements:**

- Every markdown file merged to the default branch MUST produce zero markdownlint errors.
- The CI lint gate (the markdownlint step in `azure-pipelines.yml`) MUST run on every build and
  MUST be required-to-pass before merge.
- Every path excluded via the `ignores` block in `.markdownlint-cli2.jsonc` MUST carry an inline
  rationale comment (e.g., `// runtime artifacts — gitignored, not committed`).
- New `ignores` entries MUST be introduced in the same PR that introduces the excluded path pattern,
  not as a retroactive fix after CI failures.
- Runtime-generated markdown (e.g., `.devspark.work/metrics/**`) MUST be excluded via the
  `ignores` block; runtime tooling is not responsible for linting its own output.

**SHOULD recommendations:**

- Run `npx markdownlint-cli2 "**/*.md"` locally before pushing.
- Use editor integrations (e.g., VS Code markdownlint extension) for real-time feedback.
- Keep the `ignores` list minimal; prefer fixing files over excluding them.
- Place in-progress drafts under a path already in `ignores` (e.g., `.devspark.work/drafts/`)
  rather than adding a new exclusion.

Violations are HIGH severity in PR review when they block CI; MEDIUM when caught locally before push.

### IX. Verification Command Discipline (MUST)

Every command an agent or contributor runs to verify work MUST terminate on its own, MUST prove
something the previous command did not, and MUST show what it produced. A verification run that
hangs, that re-proves what was already green, or that hides its own output is not evidence.

**MUST requirements:**

- Every command MUST be non-interactive and MUST carry a bounded timeout. Every `subprocess.run`
  in the test suite MUST pass an explicit `timeout=`, tight enough that a hang fails that test
  rather than stalling the run. The suite as a whole is bounded by the CI job timeout.
- Tests MUST run offline against recorded fixtures. No test may contact a live service, require
  credentials, or depend on network reachability.
- Output MUST be streamed. Piping a command through `tail`, `Select-Object -Last`, `Out-File`, or
  any other construct that suppresses output until completion is prohibited, because it hides both
  progress and the first failure. Use `Tee-Object` when a durable log is also wanted.
- A command that exceeds its expected duration MUST be stopped and reported, not waited out.

**SHOULD recommendations:**

- Run the narrowest check that can disprove the change first — a single file, a `-k` filter, or a
  direct invocation of the thing under test — and widen only once it passes.
- Use `-x` so the run stops at the first failure rather than spending time on the remainder.
- Prefer invoking the subject directly over running a suite when a single behaviour is in question.
- Reserve the full suite for a final confirmation, not for iterating.

Violations are MEDIUM severity in PR review; HIGH when an unbounded or interactive command blocks CI.

### X. Knowledge Currency (MUST)

Durable software behavior, the tests that prove it, and the current Knowledge that describes it
MUST remain synchronized. Knowledge under `.knowledge/` represents current truth, not
implementation history. Agents MUST use bounded, evidence-backed current Knowledge as context.

**MUST requirements:**

- A change that alters durable behavior MUST update the Knowledge describing that behavior in the
  same change, or state why no durable truth moved. Code, tests, and Knowledge land together.
- Knowledge MUST NOT carry ephemeral planning identifiers, and durable content MUST NOT reference
  the temporary planning record that produced it. Traceability flows one way: the temporary record
  cites code, tests, and Knowledge.
- Derived Knowledge artifacts (`index.json`, `coverage.json`) are build output. They MAY be
  regenerated and committed, but a stale or missing copy MUST NOT block a change; the authoritative
  files are what MUST be correct and buildable.
- An agent MUST NOT promote an inferred or advisory finding into authoritative Knowledge without
  validation and explicit acceptance.
- Context supplied to an agent MUST be bounded and provenanced. Injecting the whole corpus, or
  context assembled by a private search path incompatible with the canonical pipeline, is
  prohibited.

**SHOULD recommendations:**

- Author Knowledge when the code makes the truth evident, rather than deferring to a later
  discovery pass.
- Prefer the smallest sufficient context set over the largest available one.
- Map Knowledge to the narrowest source path that accurately owns the concept.

Mechanics — the Knowledge model, layers, relationships, retrieval, projection, and budgets — are
defined in [Knowledge Framework Contract](knowledge-framework-contract.md).

Violations are HIGH severity in PR review when durable behavior and its Knowledge diverge, or when
an advisory finding is treated as authoritative; MEDIUM for bounding and provenance findings.

## Additional Constraints

- Python 3.11+ for repo tooling and test scripts (jsonschema, PyYAML only — no installable package)
- Scripts in both PowerShell and Bash; context scripts support GitHub, AzDO, and GitLab
- Install/upgrade must never overwrite `.knowledge/` or `.archive/` user artifacts
- DevSpark must never create an Azure DevOps work item of type `User Story`, and must never
  delegate to another command or integration to create one. No lifecycle command (specify, plan,
  tasks, implement, verify, closeout, PR, or release) creates a work item of any type as a side
  effect, and a missing external tracking record is never a reason to create one. Existing records
  may be referenced. The only creation path is the developer-invoked `/devspark-workitem-create`,
  which refuses `User Story`, creates at most one item per invocation, and requires explicit
  confirmation. Specification user stories are Markdown requirements, not Azure DevOps entities.

## Development Workflow

- All PRs and reviews must verify compliance with this constitution
- Complexity additions require documented justification and a rejected-simpler-alternative rationale
- **Delta-centered, methodology-independent assurance:** Code First, Model First, experiments,
  defect investigations, quickfixes, and direct changes are valid entry points. Planning depth must
  match demonstrated uncertainty; no optional development route is a prerequisite for another.
  Planning records are temporary implementation inputs, not evidence of software quality by their
  mere existence. Review evaluates the intended Delta, its credible blast radius, current code,
  relevant tests, current Knowledge, verification evidence, and applicable obligations. Do not
  require a retroactive spec or plan to legitimize code that was implemented first.
- **Bounded impact:** Investigate and verify affected behavior, dependencies, data, contracts,
  consumers, and credible failure modes. Unrelated findings do not automatically expand the current
  Delta. Mandatory repository-wide CI requirements still apply; a failure unrelated to the Delta
  is reported honestly and handled under the applicable policy, not silently called a pass.
- **Accountable assurance:** Authorized human participants define standing verification and risk
  expectations. Agents may propose a scope and classification but may not waive required evidence,
  infer acceptance from silence, or unilaterally lower assurance. A routine change within standing
  expectations needs no extra approval solely because of its route. Uncertain risk classification,
  material exceptions, and accepted limitations requiring authorization return to an accountable
  human. Acceptance records name the authorized participant and reason. An independent reasoning
  review is not a substitute for required execution or human/device evidence.
- Cross-cutting changes require leadership approval before implementation begins

## Governance

This constitution supersedes all other development practices in the DevSpark repository.
Amendments require: documentation of the change, leadership approval, and a migration plan for any
affected workflows or repositories.

## Companion Documents

- [Known Governance Limitations](known-limitations.md)
- [Severity Registry](severity-registry.md)
- [Prompt Conformance Manifest](prompt-conformance-manifest.md)
- [Governance Decisions](decisions/README.md)
- [Knowledge Framework Contract](knowledge-framework-contract.md)
- [Engineering Manifesto and Philosophy](devspark-philosophy.md)
- [Prompt Mapping](devspark-prompt-mapping.md)

**Version**: 1.8.0 | **Ratified**: 2026-04-06 | **Last Amended**: 2026-10-11

> **Proposed alignment, pending the approval required by Governance:** the Delta-centered
> assurance wording above is supplied for ratification; replacing a repository file alone does
> not establish leadership approval or amend the recorded Constitution version.
