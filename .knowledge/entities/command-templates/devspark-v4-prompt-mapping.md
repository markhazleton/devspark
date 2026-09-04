# DevSpark Prompt Inventory and Lifecycle Map

The canonical product surface is the 30 prompt files under
`templates/commands/`. This document describes their current roles and artifact
boundaries.

## Governance

| Command | Current role |
|---|---|
| `constitution` | Creates or updates `.knowledge/governance/constitution.md`, the current governing contract. |
| `discover-constitution` | Derives a proposed constitution from current code and conventions, then hands the proposal to `constitution`. |
| `evolve-constitution` | Proposes amendments from current evidence; approved changes update the current constitution and affected decisions in place. |

## Specification and design

| Command | Current role |
|---|---|
| `specify` | Classifies a request as one-off fix, quick spec, or full spec and creates the corresponding temporary work package. |
| `clarify` | Resolves material product ambiguity in an existing spec before technical planning. |
| `plan` | Produces technical design artifacts and records bounded `context_resolved` knowledge and governance context. |
| `tasks` | Produces dependency-ordered work with `code_ref`, `test_ref`, `knowledge_ref`, and applicable `governance_ref` placeholders. |
| `checklist` | Evaluates requirements quality and persists the current result at `gates/checklist.md`. |
| `analyze` | Checks artifact consistency and validates resolved ontology references at `gates/analyze.md`. |
| `critic` | Performs adversarial design and production-risk review at `gates/critic.md`. |
| `quickfix` | Creates and completes a minimal branch-linked work record for a bounded change while preserving the same linkage and release boundary. |

## Implementation and evidence

| Command | Current role |
|---|---|
| `implement` | Applies tasks to code and tests, updates current knowledge and governance, fills linkage, and leaves the package in `.devspark.work/`. |
| `verify` | Runs focused behavioral and evidence checks. It does not change task state or archive work. |

## Pull-request delivery

| Command | Current role |
|---|---|
| `create-pr` | Creates or refreshes a spec- or quickfix-aware pull request after confirmation and exposes linkage and gate state. |
| `update-pr` | Refreshes an existing pull-request description from the current branch delta. |
| `pr-review` | Validates the pull-request delta against governance, behavior, tests, knowledge, ontology, and task linkage. |
| `address-pr-review` | Applies review fixes to code, tests, and knowledge while keeping temporary review state out of commits. |

## Release

| Command | Current role |
|---|---|
| `release` | Revalidates completed packages, updates the version, and is the sole command that moves eligible work from `.devspark.work/` to `.archive/`. |

## Current-truth utilities

| Command | Current role |
|---|---|
| `next` | Detects current Git, package, gate, PR, and review state and recommends or safely dispatches one next command. It creates no work record. |
| `explain` | Explains one existing topic from code and tests, checks matching knowledge with DELTA/KNOW findings, and confirms before writing proposals. |
| `discover-knowledge` | Builds or refreshes source-grounded entities and generated ontology content. |
| `site-audit` | Audits repository-wide code, tests, knowledge, evidence, and lifecycle boundaries. Reports remain temporary work. |
| `fix-score` | Repairs concrete score blockers while preserving behavioral intent and scoring rules. |

## External tracking and repository analysis

| Command | Current role |
|---|---|
| `taskstoissues` | Copies dependency-ordered tasks into GitHub issues for the repository matching the configured remote. Issues are an external execution surface, not current-truth documents. |
| `repo-story` | Produces a temporary narrative from Git commit data for stakeholder and onboarding use. |
| `commit-audit` | Evaluates Git commit data for delivery, hygiene, and engineering signals. |

## Customization and multi-app operations

| Command | Current role |
|---|---|
| `personalize` | Creates repository-owned, per-user command overrides under `.knowledge/overrides/<git-user>/commands/`. |
| `add-application` | Registers an application and initializes its app-local knowledge and work roots. |
| `list-applications` | Displays registered applications, profiles, dependencies, and document roots without writing files. |
| `validate-registry` | Validates the application registry, references, cycles, paths, and app-local manifests without writing files. |

## Artifact rules

- Canonical prompt bodies live in `templates/commands/`.
- Atomic prompts and agent integrations are thin resolvers; they do not duplicate
  lifecycle prose.
- Framework stock files install under `.devspark/`.
- Repository current truth and overrides live under `.knowledge/`.
- Temporary workflow artifacts live under `.devspark.work/` until release.
- Only `release` writes `.archive/`; no command reads it.
