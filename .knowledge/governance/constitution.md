# DevSpark v4 Constitution

## Core Principles

### I. Current Truth Over Lifecycle History

The repository must describe what is true now: current code, current
knowledge, and current governance. Historical planning artifacts are not durable
repository knowledge. Completed work packages remain in `.devspark.work/` after
implementation and verification. Only a release may move them to the
write-only `.archive/YYYY-MM-DD/` retention folder (preserving their path
relative to `.devspark.work/`); they are never promoted into permanent
documentation and never influence current behavior once archived.

Git is the durable source for previous states. Permanent DevSpark files must not
preserve lifecycle traces that are only useful for reconstructing how a change
was produced. The `.archive/` folder is a safety buffer for recently finalized
work, especially uncommitted or between-release state; it is not a source of
current truth.

### II. Evidence Required

Every knowledge object and every governance decision must include evidence that
lets a reviewer or agent verify the claim.

Execution evidence is preferred when a test can reasonably assert the claim.
Inspection evidence is allowed when execution evidence is not practical, but it
must state whether a test was attempted and why inspection is the fallback.

Claims with no evidence are invalid and fail the knowledge engine. Code-only
evidence without a fallback reason is a warning, surfaced by audit and PR
review, and never blocks: degree questions get warnings, existence questions get
gates.

### III. Closed Permanent Reference Graph

Permanent files may reference current code, current knowledge, current
governance, and stable external references. Permanent files must not reference
work-package IDs, task IDs, old planning artifacts, review-thread files, release
snapshots, archive folders, or other ephemeral repository artifacts.

The inverse direction is allowed while work is in progress: an ephemeral work
package may point to the permanent files it changes. Those references remain in
`.devspark.work/` through implementation, verification, and review, then move
with the package into `.archive/YYYY-MM-DD/` storage at release, where they go
inert. They must not be referenced by permanent files, and no code comment may
name a spec ID, task ID, or plan identifier.

No DevSpark command may read, list, enumerate, glob, summarize, or otherwise use
`.archive/` as input. Release is the sole DevSpark command permitted to sweep
verified work packages, work-product retention, and orphaned in-flight state
from `.devspark.work/` into `.archive/YYYY-MM-DD/`. `/devspark.constitution` and
`/devspark.evolve-constitution` may archive only their own resolved proposals.
Any purge, inspection, or recovery is human-only.

### IV. Verify, Then Release

No work package may be archived until its delta is verified as landed in code,
tests, knowledge, and governance when those areas were touched. Verification
does not archive the package; it remains in `.devspark.work/` until release.

Every completed task in an in-flight package must have populated `code_ref`,
`test_ref`, and `knowledge_ref` values, or an explicit `n/a` value with a reason.
Verification must check that referenced files exist. Release reruns the required
checks and moves eligible packages intact to `.archive/YYYY-MM-DD/`. A verified
package may stay unarchived across more than one release window.

### V. One Decision Per Topic

Governance decisions are current topic files, not sequential historical records.
Each decision topic has exactly one current file. If a decision changes, edit
that topic file in place. If a decision becomes moot because the governed
system no longer exists, remove it from current truth.

Decision files are keyed by topic, never by sequence, and must declare the
entities they constrain in `constrains`. Each constrained entity lists the
decision back in its own `constrained_by`; the knowledge engine validates the
reciprocal pair. Current knowledge carries no lifecycle state (`status`,
`lifecycle`, `supersedes`, `superseded-by`, `replaced`, `obsolete`).

### VI. Explicit Over Implied

Application scope, review scope, governance scope, and current-truth scope must
be declared explicitly. DevSpark must not silently infer scope from working
directory, branch naming, or heuristics when ambiguity would affect behavior.

Ambiguous context must produce a clear error.

### VII. Ownership Boundary

The installed DevSpark framework payload is framework-managed. Current
knowledge, governance, and in-flight work-package state are repository-owned.

Install and upgrade flows must avoid overwriting repository-owned current truth
unless the user explicitly requests a migration or overwrite operation.

### VIII. Platform Parity

Bash and PowerShell scripts must remain functionally equivalent. A change to
one script set requires the corresponding change in the other script set in the
same change.

Install, upgrade, packaging, and shim-generation behavior must deliver both
script sets regardless of the developer's current operating system.

### IX. Genuine Fix Discipline

Fix, review, audit, analysis, and verification workflows must state the
behavioral intent of a finding before accepting metric movement as proof.

Lower lint counts, lower complexity, higher coverage, cleaner scores, or other
metric changes are supporting evidence only. They do not resolve a finding
unless the observable behavior, user outcome, contract obligation, safety
property, or operational guarantee that motivated the finding is repaired or
preserved.

### X. Backward-Compatible Migration

DevSpark v4 migration must be deliberate and inspectable. Migration tooling
must support dry-run review, conflict reporting, and explicit force behavior
before overwriting generated targets or repository-owned knowledge.

Migrations of repository-owned knowledge must preserve authored content,
including comments. When a rewrite would lose authored content or two sources
disagree (for example, a decision's legacy `governs` and current
`constrains`), the migration reports a conflict and leaves the file unchanged
until the user passes explicit force.

Historical lifecycle folders may be archived only after current truth has been
created and verified. Archival is a working-tree safety operation; Git remains
the source for committed past states.

## Development Workflow

The v4 workflow produces temporary work packages for planning and implementation.
Implementation applies code, test, and knowledge deltas together, records task
linkage, updates evidence, and runs current-truth validation. The package stays
in `.devspark.work/` through verification and review. Release validates the
landed delta and is the only workflow that moves it to
`.archive/YYYY-MM-DD/` storage.

PR review is the primary assimilation trigger. It validates the permanent
record introduced by the diff: evidence, current-truth graph integrity, no
ephemeral references, and governance constraints for touched entities.

Every knowledge entry point resolves one knowledge engine,
`build_knowledge_index.py`, so the repository never has two answers to what the
knowledge index looks like.

Repository-wide audits validate the current state rather than reconstructing
past lifecycle narratives.

## Governance

This constitution supersedes other DevSpark development practices. Amendments
must update the current constitution and any conflicting current decisions in
place.

**Version**: 4.3.0 | **Ratified**: 2026-08-30 | **Last Amended**: 2026-09-27
