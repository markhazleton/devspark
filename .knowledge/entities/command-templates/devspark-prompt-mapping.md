---
source_of_truth:
- templates/commands
- tests/test_atomic_prompt_frontmatter_contract.py
last_verified: '2026-09-26'
---
# DevSpark Prompt Inventory and Lifecycle Map

The canonical product surface is the 30 prompt files under
`templates/commands/`. Every command has both an agent shim and a prompt shim.
This document maps each command against the current-truth philosophy in
`.knowledge/entities/current-truth-ontology/devspark-philosophy.md`.

The prompt set groups into three phases:

- **Plan & build** (specify, clarify, plan, tasks, checklist, analyze, critic)
  produces the ephemeral spec package and pins `context_resolved`.
- **Implementation** (implement) applies the delta to code, tests, knowledge,
  and governance in one pass, populates task linkage, and never archives.
- **Validation** (pr-review, site-audit, release) validates and enforces
  knowledge/code linkage and consistency. PR review is the primary assimilation
  trigger; release is the only command that sweeps `.devspark.work/`.

## Governance

| Command | Current role |
|---|---|
| `constitution` | Creates or updates `.knowledge/governance/constitution.md`, the current governing contract, and archives its own resolved drafts and applied proposals. |
| `discover-constitution` | Derives a proposed constitution from current code and conventions, then hands the proposal to `constitution`. |
| `evolve-constitution` | Proposes amendments from current evidence; approved changes update the current constitution and affected decisions in place. Archives its own rejected proposals. |

## Specification and design

| Command | Current role |
|---|---|
| `specify` | Classifies a request as one-off fix, quick spec, or full spec and creates the corresponding temporary work package. |
| `clarify` | Resolves material product ambiguity in an existing spec before technical planning. |
| `plan` | Produces technical design artifacts and does the expensive multi-hop ontology traversal, pinning the result as `context_resolved` (including each touched entity's `constrained_by` decisions). |
| `tasks` | Produces dependency-ordered work with `code_ref`, `test_ref`, `knowledge_ref`, and applicable `governance_ref` placeholders. |
| `checklist` | Evaluates requirements quality and persists the current result at `gates/checklist.md`. |
| `analyze` | Checks artifact consistency and gates on resolution validity: every `context_resolved` reference must resolve against the current index (hard stop). Writes `gates/analyze.md`. |
| `critic` | Performs adversarial design and production-risk review and judges `context_resolved` sufficiency (not a hard stop) at `gates/critic.md`. |
| `quickfix` | Creates and completes a minimal branch-linked work record for a bounded change while preserving the same linkage and release boundary. |

## Implementation and evidence

| Command | Current role |
|---|---|
| `implement` | Carries the heaviest discipline: one-hop-only retrieval from `context_resolved`, test-first evidence with `fallback_reason` fallback, and task linkage. Applies code, tests, knowledge, and governance together and leaves the package live in `.devspark.work/`. Never archives. |
| `verify` | The evidence-execution engine: runs cited proof modes and records the `test_ref` pointer implement consumes for `verified_by: execution` evidence. Does not change task state or archive work. |

## Pull-request delivery

| Command | Current role |
|---|---|
| `create-pr` | Creates or refreshes a spec- or quickfix-aware pull request after confirmation and exposes linkage and gate state. |
| `update-pr` | Refreshes an existing pull-request description from the current branch delta. |
| `pr-review` | The primary assimilation trigger. Validates the PR diff against governance, behavior, tests, knowledge, the closed reference graph, evidence, and task linkage, gating on engine `--check` for touched entities. |
| `address-pr-review` | Applies review fixes to code, tests, and knowledge while keeping temporary review state out of commits. |

## Release

| Command | Current role |
|---|---|
| `release` | Re-checks linkage, updates the version, and is the sole command that sweeps completed and linkage-verified specs and quickfixes, routine work-product retention, and orphaned in-flight state from `.devspark.work/` into `.archive/`. |

## Current-truth utilities

| Command | Current role |
|---|---|
| `next` | Detects current Git, package, gate, PR, and review state and recommends one next command without running it. It creates no work record. |
| `explain` | Topic-scoped: detects and remediates knowledge drift in one interactive run using deterministic concept ranking and DELTA/KNOW findings, and writes the correction or drafts the missing typed node after one explicit confirmation. The only command that can record human verification of a pinned claim. |
| `discover-knowledge` | Builds or refreshes source-grounded entities, migrates older layouts, and regenerates the knowledge index. |
| `site-audit` | Repo-wide and synchronic: runs the accuracy pass (re-runs execution evidence, judges inspection evidence) and scans `contradiction_scopes` for human review. Reports remain temporary work. |
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
- `release` is the only command that sweeps `.devspark.work/` into `.archive/`;
  `constitution` and `evolve-constitution` archive only their own resolved
  proposals. No command reads `.archive/`.
- Every knowledge entry point resolves the single engine,
  `build_knowledge_index.py`, through `resolve_knowledge_engine` /
  `Resolve-KnowledgeEngine`.
