# Implementation Plan: Multi-Application Monorepo Support

**Branch**: `feature/monorepo-multi-app-support` | **Date**: 2026-04-06 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/.documentation/specs/001-multi-app-monorepo-support/spec.md`

## Summary

Add explicit multi-application monorepo support to DevSpark without breaking the current single-app
model. The implementation centers on an authoritative repository app registry, app-aware resolution for
constitutions, prompts, scripts, templates, and specs, plus dependency-aware scope reporting for review
and planning workflows. The installation boundary remains unchanged: DevSpark deploys only `.devspark/`
and agent shims, while all repo-level and app-level `.documentation/` directories remain repository-owned.

The core design constraint is backward compatibility. Single-app repositories must continue to work
unchanged. Multi-app behavior must be opt-in, explicit, and visible in workflow output.

Guiding philosophies for this implementation:

- Simple over complex
- Explicit over implied

## Technical Context

**Language/Version**: Python 3.11+ for CLI, Bash and PowerShell for helper scripts, Markdown prompt templates  
**Primary Dependencies**: typer, rich, httpx, existing DevSpark Bash and PowerShell script stacks  
**Storage**: File-based configuration under `.documentation/` and `.devspark/`  
**Testing**: Script validation, fixture-based repository tests, lint and markdown validation, targeted CLI verification  
**Target Platform**: macOS, Linux, and Windows repository environments  
**Project Type**: Prompt framework, CLI bootstrapper, and cross-platform script toolkit  
**Performance Goals**: Resolution and validation overhead should remain negligible relative to current command startup  
**Constraints**: Must preserve single-app compatibility, maintain Bash and PowerShell parity, avoid hidden app inference, and never install or mutate repo-owned `.documentation/` content  
**Scale/Scope**: All packaged prompts, quickstarts, helper scripts, and relevant CLI flows must support the same multi-app model

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The source repository constitution in `.documentation/memory/constitution.md` is currently a template,
not an enforceable project-specific constitution. For this plan, the effective gates are therefore the
product principles already established in the repository content and requested by the feature:

- Backward compatibility for existing single-app repositories is mandatory
- The solution must be explicit and reviewable rather than inference-heavy
- The first release must prefer conventions over highly flexible configuration
- Installation and upgrade flows must preserve the existing ownership boundary: `.devspark/` is managed
  by DevSpark, `.documentation/` is managed by the repository
- Packaging, quickstarts, and CLI behavior must stay aligned with source templates
- Bash and PowerShell script behavior must remain functionally equivalent

Gate status: pass for planning, subject to leadership approval of the operating model in the spec.

## Project Structure

### Documentation (this feature)

```text
.documentation/specs/001-multi-app-monorepo-support/
├── spec.md
└── plan.md
```

### Source Code (repository root)

```text
.github/
└── workflows/
    └── scripts/
        └── create-release-packages.sh

quickstart/
├── devspark_quickstart_claudecode.md
├── devspark_quickstart_copilot.md
├── devspark_quickstart_cursor.md
└── devspark_quickstart_generic.md

scripts/
├── bash/
│   ├── common.sh
│   ├── platform.sh
│   ├── create-new-feature.sh
│   ├── setup-plan.sh
│   ├── get-pr-context.sh
│   ├── quickfix-context.sh
│   ├── release-context.sh
│   ├── repo-story-context.sh
│   └── site-audit.sh
└── powershell/
    ├── common.ps1
    ├── platform.ps1
    ├── create-new-feature.ps1
    ├── setup-plan.ps1
    ├── get-pr-context.ps1
    ├── quickfix-context.ps1
    ├── release-context.ps1
    ├── repo-story-context.ps1
    └── site-audit.ps1

src/
└── devspark_cli/
    └── __init__.py

templates/
├── commands/
│   ├── specify.md
│   ├── plan.md
│   ├── tasks.md
│   ├── implement.md
│   ├── pr-review.md
│   ├── quickfix.md
│   ├── harvest.md
│   ├── release.md
│   ├── site-audit.md
│   ├── critic.md
│   ├── constitution.md
│   └── upgrade.md
└── *.md / vscode-settings.json
```

**Structure Decision**: This feature spans source templates, runtime helper scripts, packaging, quickstart
guidance, and the optional CLI installer. It should be implemented as a cross-cutting product change,
not as an isolated documentation update.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Cross-cutting change across prompts, scripts, packaging, and CLI | Multi-app support cannot be real unless all resolution paths align | A docs-only or scripts-only change would produce inconsistent behavior |
| Explicit app registry and profile model | Mixed-platform monorepos need deterministic app identity and inheritance | Folder-based inference is brittle and not reviewable |

## Delivery Strategy

Implement this in four workstreams with hard gates between them. Do not start packaging or quickstart
changes until the core resolution model is stable.

### V1 Boundary

The first release is intentionally constrained.

Included in v1:

- authoritative repository registry in `.documentation/devspark.json`
- convention-based app paths derived from the registered app path
- repository-level `.documentation/` plus optional app-local `{app.path}/.documentation/` folders
- limited multi-app command support through `/devspark.add-application` and `/devspark.list-applications`
- repository constitution plus additive app constitution overlay
- explicit app selection and explicit repo-scope execution
- app-aware prompt, script, and template resolution
- app-scoped artifact directories
- installation and upgrade behavior that only manages `.devspark/` and agent shims
- direct downstream dependency reporting from declared dependencies

Deferred from v1:

- app-local `app.json` manifests
- app-specific user override layers
- inferred dependency discovery from code or build metadata
- complex non-conventional layouts unless explicitly justified
- broader app lifecycle commands such as remove, rename, move, or split application workflows

### Workstream 1 - Configuration and Resolution Model

Objective: establish the source of truth and resolution order.

Deliverables:

- Repository registry schema in `.documentation/devspark.json`
- On-disk ownership model that separates managed `.devspark/` installation content from repo-owned
  repo-level and app-level `.documentation/` content
- Validation rules for apps, profiles, dependencies, and override settings
- Command contracts for `/devspark.add-application` and `/devspark.list-applications`
- App-aware resolution contract for constitutions, prompts, scripts, and templates
- Constitution composition semantics: repo rules first, app overlay second
- Repo-scope versus app-scope execution rules
- Scope-selection decision table for ambiguous and cross-app changes
- Pull request scope contract for `single-app`, `cross-app`, and `repo-scope` review flows
- Scope report format for workflow output
- Direct downstream impact report from declared dependencies

Primary code surfaces:

- `scripts/bash/common.sh`
- `scripts/bash/platform.sh`
- `scripts/powershell/platform.ps1`
- `src/devspark_cli/__init__.py`
- `templates/commands/*.md`

Exit criteria:

- Single-app mode remains the default path
- Multi-app mode is opt-in and validated
- Resolution order is documented and testable
- The ownership boundary is explicit and preserved in runtime, packaging, and CLI behavior
- Direct downstream impacts are reported for shared changes
- Pull request scope rules are explicit and testable against changed paths and declared app metadata
- Add and list application workflows are defined without expanding into a larger app-management surface

### Workstream 2 - Script and Prompt Propagation

Objective: carry explicit app context through runtime workflows.

Deliverables:

- Common app selection and validation helpers for Bash and PowerShell
- App-aware spec directory discovery and branch-scoped feature creation behavior using repo-level
  `.documentation/` for repo scope and `{app.path}/.documentation/` for app scope
- Prompt templates updated to use app-aware paths and scope reporting
- Pull request declaration and review behavior for `single-app`, `cross-app`, and `repo-scope`
- Validation that compares declared pull request scope with changed paths and shared path policy
- `/devspark.add-application` flow that updates the root registry and optionally scaffolds the app-local
  documentation root when explicitly requested
- `/devspark.list-applications` flow that renders registry data in a human-readable, read-only form
- Fallback behavior for repo-scoped workflows
- Enforcement of the scope-selection rules defined in Workstream 1

Primary code surfaces:

- `scripts/bash/create-new-feature.sh`
- `scripts/bash/setup-plan.sh`
- `scripts/bash/get-pr-context.sh`
- `scripts/bash/quickfix-context.sh`
- `scripts/bash/release-context.sh`
- `scripts/bash/repo-story-context.sh`
- `scripts/bash/site-audit.sh`
- PowerShell equivalents
- `templates/commands/pr-review.md`
- `templates/commands/add-application.md`
- `templates/commands/list-applications.md`
- `templates/commands/specify.md`
- `templates/commands/plan.md`
- `templates/commands/tasks.md`
- `templates/commands/implement.md`
- `templates/commands/quickfix.md`
- `templates/commands/site-audit.md`
- `templates/commands/release.md`

Exit criteria:

- Commands can execute in repo scope or explicit app scope
- Generated artifacts land in the correct app or repo directory
- No workflow writes app-scoped artifacts into managed `.devspark/` or into synthetic nested folders under
  the repo root `.documentation/`
- Single-app pull requests fail or require reclassification when changed paths show undeclared multi-app
  scope
- Cross-app and repo-scope pull requests emit declared scope, detected scope, and impacted app summaries
- Add-application updates the registry safely and never mutates `.devspark/`
- List-applications remains read-only and reflects the authoritative registry accurately
- Missing or ambiguous app context fails clearly

### Workstream 3 - Packaging, Quickstarts, and CLI

Objective: make the new model installable and understandable.

Deliverables:

- Updated release package generation and shim content
- Quickstart guidance for single-app and multi-app installs
- CLI support for initializing or upgrading repos that opt into multi-app mode
- Example layout and migration guidance
- Explicit install and upgrade rules stating that DevSpark deploys only `.devspark/` and agent shims and
  never adds, removes, or updates files inside repo-owned `.documentation/` directories
- Packaging and docs for only the limited multi-app command set: add application and list applications

Primary code surfaces:

- `.github/workflows/scripts/create-release-packages.sh`
- `quickstart/devspark_quickstart_copilot.md`
- `quickstart/devspark_quickstart_claudecode.md`
- `quickstart/devspark_quickstart_cursor.md`
- `quickstart/devspark_quickstart_generic.md`
- `README.md`
- `templates/README.md`
- `src/devspark_cli/__init__.py`

Exit criteria:

- Installed packages use the same resolution model as source templates
- Quickstarts explain when to use repo-wide scope versus app scope
- Upgrade paths do not overwrite user-owned repo-level or app-level `.documentation/` content
- The shipped command set stays limited to add and list application workflows for multi-app management

### Workstream 4 - Validation, Fixtures, and Hardening

Objective: prevent silent failure and prove the model on representative monorepos.

Deliverables:

- Fixture repositories or fixture directory trees for representative app mixes
- Validation for malformed registry state and dependency cycles
- Regression checks for current single-app behavior
- Regression checks that verify install and upgrade flows do not add, remove, or rewrite repo-owned
  `.documentation/` files
- Regression checks for single-app, cross-app, and repo-scope pull request validation behavior
- Regression checks for add-application validation and list-applications output behavior
- Hardening of deferred features only if leadership expands scope after v1 approval

Primary code surfaces:

- Script validation logic in Bash and PowerShell
- CLI validation paths
- Example or fixture content under repository test assets if introduced

Exit criteria:

- Known-bad registry configurations fail fast
- Single-app regression checks pass

## Phase Plan

### Phase 0 - Finalize the design contract

Tasks:

- Approve the authority model for `.documentation/devspark.json`
- Approve the ownership model: `.devspark/` is installed content, repo-level and app-level
  `.documentation/` directories are repository-owned content
- Approve the resolution order
- Approve the decision that app scope is explicit, not inferred
- Approve the v1 decision to omit app-local manifests
- Approve the v1 decision to omit app-specific user overrides
- Approve the scope-selection decision table
- Approve the pull request scope policy: single-app by default, cross-app allowed by declaration,
  repo-scope required for intentionally shared changes
- Approve the limited multi-app command set: add application and list applications only

Output:

- Approved design baseline for implementation

### Phase 1 - Implement core resolution primitives

Tasks:

- Add registry loading and validation
- Add app-aware helper functions to Bash and PowerShell platform layers
- Define standard scope object or equivalent runtime representation
- Define repo-scope versus app-scope documentation root resolution
- Define pull request scope object and shared-path policy for single-app pull requests
- Define add-application input contract, validation behavior, and optional scaffolding policy
- Define list-applications output contract
- Implement direct downstream dependency reporting from declared dependencies

Output:

- Shared primitives used by workflows and CLI

### Phase 2 - Convert prompts and scripts

Tasks:

- Update workflows to accept and propagate app context
- Route specs, plans, and tasks to repo-level `.documentation/` for repo scope and to
  `{app.path}/.documentation/` for app scope when needed
- Update PR review flows to validate declared scope versus changed paths and dependency data
- Implement add-application and list-applications command flows
- Add scope summaries to outputs

Output:

- End-to-end app-aware workflows in source templates and scripts

### Phase 3 - Update install and upgrade surfaces

Tasks:

- Update release packaging and shim generation
- Update quickstarts and docs
- Update CLI init and upgrade behavior without mutating repo-owned `.documentation/` content

Output:

- Consistent install, upgrade, and execution model

### Phase 4 - Validate and harden

Tasks:

- Validate with mixed-platform monorepo examples
- Run regression checks against single-app flows
- Validate that installer and upgrade flows never add, remove, or rewrite repo-owned `.documentation/`
  content in repo scope or app scope
- Validate pull request behavior for single-app, cross-app, and repo-scope examples
- Validate add-application and list-applications behavior against representative registries
- Refine error messages and migration guidance

Output:

- Leadership-ready implementation confidence

## Recommended Testing Strategy

- Add representative fixture configurations for:
  - single-app repository
  - multi-app API-only repository
  - mixed-platform repository with runtime APIs, admin API, admin web, client web, and QA harness
- Validate ownership boundary behavior for:
  - repo-level `.documentation/` remains untouched by install and upgrade
  - app-level `{app.path}/.documentation/` remains untouched by install and upgrade
- Validate registry parsing and failure modes for:
  - duplicate ids
  - unknown profile references
  - unknown dependency ids
  - cyclic dependencies
  - invalid explicit overrides
- Validate resolution behavior for:
  - repo-wide workflow
  - explicit app workflow
  - app without local constitution
  - app with local script override only
  - ambiguous root execution without app context
  - shared contract change that must run in repo scope
- Validate application command behavior for:
  - add-application with valid new app metadata
  - add-application rejecting duplicate ids and invalid paths
  - add-application optional scaffolding without touching `.devspark/`
  - list-applications rendering registry contents without mutation
- Validate pull request scope behavior for:
  - declared single-app pull request touching one app plus approved shared paths
  - declared single-app pull request touching a second app path and failing validation
  - declared cross-app pull request listing all touched apps
  - declared repo-scope pull request for shared contract or platform changes
- Validate dependency reporting behavior for:
  - direct downstream apps declared in the registry
  - missing dependency declarations treated as config gaps
- Validate packaging and quickstart consistency so shipped content matches source expectations

## Key Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Partial rollout updates docs but not runtime behavior | High | High | Sequence packaging and docs only after runtime resolution is implemented |
| App-specific overrides proliferate and drift | Medium | High | Favor profile inheritance and validate override usage |
| Scope ambiguity confuses users | High | High | Make app selection explicit and print scope in outputs |
| Undeclared multi-app pull requests are reviewed as local changes | High | High | Require explicit PR scope declaration and validate against changed paths |
| Multi-app command surface grows faster than the model matures | Medium | Medium | Limit v1 to add and list application workflows only |
| Bash and PowerShell behavior diverges | Medium | High | Implement shared rules first and verify parity at each phase |
| CLI and prompt-template behavior drift apart | Medium | High | Use the registry contract as a single source of truth |

## Leadership Review Focus Areas

- Is the repository registry the right authority model?
- Is explicit app scope the right tradeoff versus convenience inference?
- Is the simplified v1 boundary acceptable?
- Is direct downstream dependency reporting sufficient for the first delivery?
- Is the pull request scope policy strict enough to protect against undeclared cross-app changes without
  making legitimate multi-app work too painful?
- Is optional app-local documentation scaffolding during add-application the right v1 boundary?
- Is the proposed phased rollout acceptable for product and adoption timelines?

## Recommended Next Implementation Slice

Start with Workstream 1 only: introduce the repository registry contract, app-aware resolution order,
validation helpers in the platform layers, the scope-selection rules, and direct downstream dependency
reporting. Do not begin per-command rewrites until the leadership team approves the authority model,
composition semantics, and scope propagation rules.
