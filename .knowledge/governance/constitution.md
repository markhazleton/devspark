# DevSpark v4 Constitution

## Core Principles

### I. Current Truth Over Lifecycle History

The repository must describe what is true now: current code, current
knowledge, and current governance. Historical planning artifacts are not durable
repository knowledge. Completed or abandoned work packages are deleted after
verification, not archived into a permanent documentation structure.

Git is the durable source for previous states. Permanent DevSpark files must not
preserve lifecycle traces that are only useful for reconstructing how a change
was produced.

### II. Evidence Required

Every knowledge object and every governance decision must include evidence that
lets a reviewer or agent verify the claim.

Execution evidence is preferred when a test can reasonably assert the claim.
Inspection evidence is allowed when execution evidence is not practical, but it
must state whether a test was attempted and why inspection is the fallback.

Claims with no evidence are invalid. Code-only evidence without a fallback
reason is a warning.

### III. Closed Permanent Reference Graph

Permanent files may reference current code, current knowledge, current
governance, and stable external references. Permanent files must not reference
work-package IDs, task IDs, old planning artifacts, review-thread files, release
snapshots, archive folders, or other ephemeral repository artifacts.

The inverse direction is allowed while work is in progress: an ephemeral work
package may point to the permanent files it changes. Those references disappear
when the package is verified and deleted.

### IV. Verify Before Delete

No work package may be deleted until its delta is verified as landed in code,
knowledge, and governance when those areas were touched.

Every completed task in an in-flight package must have populated `code_ref` and
`knowledge_ref` values, or an explicit `n/a` value with a reason. Verification
must check that referenced files exist before deletion.

### V. One Decision Per Topic

Governance decisions are current topic files, not sequential historical records.
Each decision topic has exactly one current file. If a decision changes, edit
that topic file in place. If a decision becomes moot because the governed
system no longer exists, delete it.

Decision files must declare the entities they constrain. Entity-derived metadata
is generated from those declarations and must not be hand-maintained.

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
before overwriting generated targets.

Historical lifecycle folders may be removed only after current truth has been
created and verified. Deletion is a working-tree operation; Git remains the
source for past states.

## Development Workflow

The v4 workflow produces temporary work packages for planning and implementation.
Implementation applies code and knowledge deltas together, records task linkage,
updates evidence, runs current-truth validation, and then verifies before
deleting the package.

PR review validates the permanent record introduced by the diff: evidence,
current-truth graph integrity, no ephemeral references, and governance
constraints for touched entities.

Repository-wide audits validate the current state rather than reconstructing
past lifecycle narratives.

## Governance

This constitution supersedes other DevSpark development practices. Amendments
must update the current constitution and any conflicting current decisions in
place.

**Version**: 4.0.0 | **Ratified**: 2026-08-30 | **Last Amended**: 2026-08-30
