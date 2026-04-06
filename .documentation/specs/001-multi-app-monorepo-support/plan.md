# Implementation Plan: Multi-Application Monorepo Support

**Branch**: `feature/monorepo-multi-app-support` | **Date**: 2026-04-06 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/.documentation/specs/001-multi-app-monorepo-support/spec.md`

## Summary

Add explicit multi-application monorepo support to DevSpark without breaking the current single-app
model. The implementation centers on an authoritative repository app registry, app-aware resolution for
constitutions, prompts, scripts, templates, and specs, plus dependency-aware scope reporting for review
and planning workflows.

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
**Constraints**: Must preserve single-app compatibility, maintain Bash and PowerShell parity, and avoid hidden app inference  
**Scale/Scope**: All packaged prompts, quickstarts, helper scripts, and relevant CLI flows must support the same multi-app model

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The source repository constitution in `.documentation/memory/constitution.md` is currently a template,
not an enforceable project-specific constitution. For this plan, the effective gates are therefore the
product principles already established in the repository content and requested by the feature:

- Backward compatibility for existing single-app repositories is mandatory
- The solution must be explicit and reviewable rather than inference-heavy
- The first release must prefer conventions over highly flexible configuration
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
- convention-based app paths derived from app id
- repository constitution plus additive app constitution overlay
- explicit app selection and explicit repo-scope execution
- app-aware prompt, script, and template resolution
- app-scoped artifact directories
- direct downstream dependency reporting from declared dependencies

Deferred from v1:

- app-local `app.json` manifests
- app-specific user override layers
- inferred dependency discovery from code or build metadata
- complex non-conventional layouts unless explicitly justified

### Workstream 1 - Configuration and Resolution Model

Objective: establish the source of truth and resolution order.

Deliverables:

- Repository registry schema in `.documentation/devspark.json`
- Validation rules for apps, profiles, dependencies, and override settings
- App-aware resolution contract for constitutions, prompts, scripts, and templates
- Constitution composition semantics: repo rules first, app overlay second
- Repo-scope versus app-scope execution rules
- Scope-selection decision table for ambiguous and cross-app changes
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
- Direct downstream impacts are reported for shared changes

### Workstream 2 - Script and Prompt Propagation

Objective: carry explicit app context through runtime workflows.

Deliverables:

- Common app selection and validation helpers for Bash and PowerShell
- App-aware spec directory discovery and branch-scoped feature creation behavior
- Prompt templates updated to use app-aware paths and scope reporting
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
- `templates/commands/specify.md`
- `templates/commands/plan.md`
- `templates/commands/tasks.md`
- `templates/commands/implement.md`
- `templates/commands/pr-review.md`
- `templates/commands/quickfix.md`
- `templates/commands/site-audit.md`
- `templates/commands/release.md`

Exit criteria:

- Commands can execute in repo scope or explicit app scope
- Generated artifacts land in the correct app or repo directory
- Missing or ambiguous app context fails clearly

### Workstream 3 - Packaging, Quickstarts, and CLI

Objective: make the new model installable and understandable.

Deliverables:

- Updated release package generation and shim content
- Quickstart guidance for single-app and multi-app installs
- CLI support for initializing or upgrading repos that opt into multi-app mode
- Example layout and migration guidance

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
- Upgrade paths do not overwrite user-owned app overlays

### Workstream 4 - Validation, Fixtures, and Hardening

Objective: prevent silent failure and prove the model on representative monorepos.

Deliverables:

- Fixture repositories or fixture directory trees for representative app mixes
- Validation for malformed registry state and dependency cycles
- Regression checks for current single-app behavior
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
- Approve the resolution order
- Approve the decision that app scope is explicit, not inferred
- Approve the v1 decision to omit app-local manifests
- Approve the v1 decision to omit app-specific user overrides
- Approve the scope-selection decision table

Output:

- Approved design baseline for implementation

### Phase 1 - Implement core resolution primitives

Tasks:

- Add registry loading and validation
- Add app-aware helper functions to Bash and PowerShell platform layers
- Define standard scope object or equivalent runtime representation
- Implement direct downstream dependency reporting from declared dependencies

Output:

- Shared primitives used by workflows and CLI

### Phase 2 - Convert prompts and scripts

Tasks:

- Update workflows to accept and propagate app context
- Route specs, plans, and tasks to app-specific directories when needed
- Add scope summaries to outputs

Output:

- End-to-end app-aware workflows in source templates and scripts

### Phase 3 - Update install and upgrade surfaces

Tasks:

- Update release packaging and shim generation
- Update quickstarts and docs
- Update CLI init and upgrade behavior

Output:

- Consistent install, upgrade, and execution model

### Phase 4 - Validate and harden

Tasks:

- Validate with mixed-platform monorepo examples
- Run regression checks against single-app flows
- Refine error messages and migration guidance

Output:

- Leadership-ready implementation confidence

## Recommended Testing Strategy

- Add representative fixture configurations for:
  - single-app repository
  - multi-app API-only repository
  - mixed-platform repository with runtime APIs, admin API, admin web, client web, and QA harness
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
| Bash and PowerShell behavior diverges | Medium | High | Implement shared rules first and verify parity at each phase |
| CLI and prompt-template behavior drift apart | Medium | High | Use the registry contract as a single source of truth |

## Leadership Review Focus Areas

- Is the repository registry the right authority model?
- Is explicit app scope the right tradeoff versus convenience inference?
- Is the simplified v1 boundary acceptable?
- Is direct downstream dependency reporting sufficient for the first delivery?
- Is the proposed phased rollout acceptable for product and adoption timelines?

## Recommended Next Implementation Slice

Start with Workstream 1 only: introduce the repository registry contract, app-aware resolution order,
validation helpers in the platform layers, the scope-selection rules, and direct downstream dependency
reporting. Do not begin per-command rewrites until the leadership team approves the authority model,
composition semantics, and scope propagation rules.
