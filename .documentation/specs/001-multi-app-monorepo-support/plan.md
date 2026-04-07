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
**Performance Goals**: Resolution and validation under 500ms for up to 20 apps; less than 100ms added latency per command
**Constraints**: Must preserve single-app compatibility, maintain Bash and PowerShell parity, avoid hidden app inference, and never install or mutate repo-owned `.documentation/` content
**Scale/Scope**: All packaged prompts, quickstarts, helper scripts, and relevant CLI flows must support the same multi-app model; tested with fixtures up to 20 registered applications

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Checked against the DevSpark Constitution v1.0.0 at `.documentation/memory/constitution.md`:

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Backward Compatibility (NON-NEGOTIABLE) | Pass | Single-app repos require no changes; multi-app is opt-in |
| II. Explicit Over Implied (NON-NEGOTIABLE) | Pass | App scope is always declared, never inferred |
| III. Ownership Boundary (NON-NEGOTIABLE) | Pass | Install/upgrade only touches `.devspark/`; `.documentation/` is repo-owned |
| IV. Governance Authority | Pass | Repo constitution is always loaded first; app overlay may not weaken mandatory rules |
| V. Simplicity | Conditional | Profile inheritance adds complexity; justified by the alternative (full per-app duplication) |
| VI. Platform Parity | Pass | All Bash scripts have PowerShell equivalents; parity validated by fixture tests |

Gate status: **Pass** — proceed to design, subject to leadership approval of v1 scope.

## Omitted Plan Template Artifacts

The standard plan template specifies `research.md`, `data-model.md`, `quickstart.md`, and `contracts/`.
These are omitted for this feature with rationale:

| Artifact | Reason Omitted |
|----------|---------------|
| `research.md` | No external technology selection required; the feature extends existing DevSpark internals |
| `data-model.md` | The data model is a JSON configuration schema, fully documented in "Registry Schema" below |
| `quickstart.md` | Multi-app quickstart guidance is part of Workstream 3 deliverables (updates to existing quickstart files) |
| `contracts/` | The resolution contracts and scope contracts are defined inline in this plan; no separate API contracts |

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
    ├── __init__.py
    ├── registry.py            # new — Pydantic models, validation, app.json loading
    ├── scope.py               # new — scope object, PR scope, dependency reporting
    ├── resolution.py          # new — constitution/prompt/script/template resolution
    ├── inference.py           # new — dependency inference from imports/build config
    └── commands.py            # new — add-application, list-applications, validate-registry

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
│   ├── upgrade.md
│   ├── add-application.md       # new
│   ├── list-applications.md     # new
│   └── validate-registry.md    # new (Added 2026-04-07)
├── rationale-template.md        # new
└── *.md / vscode-settings.json
```

**Structure Decision**: This feature spans source templates, runtime helper scripts, packaging, quickstart
guidance, and the optional CLI installer. It is implemented as a cross-cutting product change,
not an isolated documentation update.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Cross-cutting change across prompts, scripts, packaging, and CLI | Multi-app support cannot be real unless all resolution paths align | A docs-only or scripts-only change would produce inconsistent behavior |
| Explicit app registry and profile model | Mixed-platform monorepos need deterministic app identity and inheritance | Folder-based inference is brittle and not reviewable |
| Profile inheritance with tags/rules/hints | Applications sharing the same class need shared rule sets | Full per-app duplication makes upgrades expensive and audits impossible |

## Design: Operating Model

DevSpark treats a repository as a shared control plane with optional application overlays rather than a
single project root.

Authority model:

- `.documentation/devspark.json` is the authoritative repository registry
- `.devspark/` is the only DevSpark installation payload; `.documentation/` directories are repo-owned
  work product and are never modified by install or upgrade flows
- Repository governance remains authoritative over all applications
- Application governance may extend or strengthen repo governance, but it may not weaken mandatory
  repo-level rules
- v1 supports optional app-local manifests (`{app.path}/app.json`) for app-specific overrides (tags,
  hints, local rules); the registry remains authoritative for identity fields (id, path, kind, owner,
  dependencies) *(Updated 2026-04-07: leadership decision Q1)*
- v1 prefers convention-based paths over repeated per-app path declarations
- v1 uses one repo-level `.documentation/` plus optional application-local `{app.path}/.documentation/`
  directories instead of nesting application state under the repo-level `.documentation/`

### Recommended On-Disk Layout

```text
.devspark/
├── defaults/
├── scripts/
└── templates/

.documentation/
├── memory/
│   └── constitution.md
├── commands/
├── scripts/
├── templates/
├── specs/
├── devspark.json
└── {git-user}/commands/

apps/
├── runtime-api-a/
│   ├── app.json                    # optional app-local manifest (tags, hints, local rules)
│   └── .documentation/
│       ├── memory/constitution.md
│       ├── commands/
│       ├── scripts/
│       ├── templates/
│       └── specs/
├── runtime-api-b/
│   ├── app.json
│   └── .documentation/
├── admin-api/
│   ├── app.json
│   └── .documentation/
├── admin-web/
│   ├── app.json
│   └── .documentation/
├── client-web/
│   ├── app.json
│   └── .documentation/
└── qa-harness/
    ├── app.json
    └── .documentation/
```

In this model:

- the repo root `.documentation/` holds repo-scoped governance, registry, shared overrides, and repo-wide
  specifications
- each application may define its own `{app.path}/.documentation/` folder for app-scoped governance,
  overrides, and specs
- DevSpark resolves and consumes these folders, but it does not install, update, or remove them

## Design: Resolution Model

### Terminology Convention

- **Overlay**: Additive composition of constitutions. An app constitution is *overlaid* on the repo
  constitution. The repo rules remain authoritative; the overlay may extend or strengthen but never weaken.
- **Override**: File-level replacement in the prompt, script, and template resolution chains. A file at a
  higher-priority tier *overrides* the same-named file at a lower tier. Resolution uses exact filename
  matching only — no glob patterns, no partial matches. If no exact match exists at a tier, that tier is
  skipped.

### Constitution Resolution

1. Load the repository constitution from `.documentation/memory/constitution.md`
2. Load the application constitution from `{app.path}/.documentation/memory/constitution.md` if it exists
3. Compose the effective governance by adding application-specific rules on top of repo-wide rules
4. Run keyword-based weakening detection (see spec: Constitution Weakening Detection)
5. Emit CONFLICT warnings for detected weakening; do not silently pass
6. Error if a governance-requiring workflow cannot resolve a repository constitution

### Prompt Resolution (v1)

1. Application team override from `{app.path}/.documentation/commands/`
2. Repository user override from `.documentation/{git-user}/commands/`
3. Repository team override from `.documentation/commands/`
4. Stock DevSpark default from `.devspark/defaults/`

### Script Resolution (v1)

1. Application team override from `{app.path}/.documentation/scripts/`
2. Repository team override from `.documentation/scripts/`
3. Stock DevSpark default from `.devspark/scripts/`

### Template Resolution (v1)

1. Application team override from `{app.path}/.documentation/templates/`
2. Repository team override from `.documentation/templates/`
3. Stock DevSpark default from `.devspark/templates/`

This ordering keeps v1 simple, preserves the current repo-user customization model, and avoids
introducing a new app-user override layer before the base model is proven.

## Design: Scope Selection Rules

DevSpark uses explicit, deterministic scope selection. It does not guess silently.

| Change Type | Required Scope | Expected Behavior |
|-------------|----------------|------------------|
| Application-owned code change | Explicit app scope | Run in that app's scope and write artifacts under that app |
| Shared library used by one app | Explicit app scope | Run in the owning app's scope and include downstream dependency note if declared |
| Shared library used by multiple apps | Repo scope | Require repo-scoped workflow and list impacted apps |
| Shared API contract change | Repo scope | Require repo-scoped workflow and include direct downstream consumers |
| Infrastructure or platform change affecting multiple apps | Repo scope | Require repo-scoped workflow and identify impacted apps |
| Documentation-only repo change | Repo scope | Run without app selection |
| Root-level execution with a provided app id | Explicit app scope | Use the declared app and print resolved scope |
| Root-level execution with no app id and multiple candidate apps | Error | Refuse to guess and require explicit scope |

### Pull Request Scope Contract

Three modes:

- **`single-app`**: Declare one primary application. Changed files must touch only that app's path plus
  approved shared paths. Reviewed using repo governance + primary app context.
- **`cross-app`**: Declare one primary application + all affected applications + reason the work cannot
  be cleanly split. Reviewed using repo governance + all declared app contexts + dependency report.
- **`repo-scope`**: No primary application required. Used for shared contracts, shared libraries consumed
  by multiple apps, infrastructure changes. Reviewed using repo governance + impacted app listing.

Validation rules:

- A `single-app` PR that touches a second registered app path triggers a scope mismatch warning
- A `cross-app` PR must name all touched registered app paths
- Review output always reports: declared scope, detected scope, mismatches, and downstream app impact

### Dependency Reporting *(Updated 2026-04-07: leadership decision Q2)*

v1 reports both declared and inferred dependencies:

- Report the primary scope
- Report directly impacted downstream applications from the declared dependency graph
- Report inferred dependencies from source imports and build configuration files, clearly labeled
  as "inferred" and separate from declared dependencies (see "Design: Dependency Inference")
- Treat missing dependency declarations as configuration gaps shown in scope reports
- Inferred dependencies that match declared dependencies are deduplicated

## Design: Registry Schema

### Registry Location and Validation

The authoritative registry lives at `.documentation/devspark.json`. Validation is performed using:

- **Python (CLI)**: Pydantic v2 model with field validators for types, uniqueness, path existence,
  reference resolution, and cycle detection
- **Bash**: `jq`-based validation for field presence and type checks; cycle detection deferred to Python
- **PowerShell**: `ConvertFrom-Json` with manual property checks; cycle detection deferred to Python

Schema version is checked on load. If `version` does not match the expected value, DevSpark emits a
clear error with migration guidance.

### Schema Shape

```json
{
  "version": 1,
  "mode": "multi-app",
  "profiles": {
    "repo-default": {
      "description": "Mandatory repository-wide governance and workflow defaults",
      "tags": {},
      "rules": ["All apps must pass repo-wide lint checks"],
      "hints": {}
    },
    "api-profile": {
      "description": "Contract-first API rules, backward compatibility, observability, and performance",
      "tags": { "runtime-class": "api" },
      "rules": ["API changes must include contract tests", "Breaking changes require deprecation cycle"],
      "hints": { "test-runner": "pytest", "review-depth": "thorough" }
    },
    "admin-profile": {
      "description": "Administrative auditability, authorization rigor, and change traceability",
      "tags": { "access-model": "role-based" },
      "rules": ["Admin operations must be audit-logged"],
      "hints": {}
    },
    "web-profile": {
      "description": "Accessibility, browser support, frontend testing, and UX telemetry",
      "tags": { "runtime-class": "web" },
      "rules": ["WCAG 2.1 AA compliance required"],
      "hints": { "test-runner": "vitest" }
    },
    "qa-profile": {
      "description": "Environment-safe test execution, fixture isolation, and diagnostic capture",
      "tags": { "runtime-class": "qa" },
      "rules": ["QA harness must not mutate production data"],
      "hints": { "review-depth": "standard" }
    }
  },
  "apps": []
}
```

### Application Definition Shape

```json
{
  "id": "admin-web",
  "name": "Admin Configuration UI",
  "path": "apps/admin-web",
  "kind": "web-admin",
  "purpose": "Internal configuration and operational administration",
  "runtime": "react",
  "owner": "platform-admin",
  "criticality": "medium",
  "deployable": true,
  "inherits": ["repo-default", "web-profile", "admin-profile"],
  "dependsOn": ["admin-api"],
  "tags": ["internal", "admin", "react"],
  "platforms": ["web"],
  "overrides": {}
}
```

Shared libraries use `"deployable": false`:

```json
{
  "id": "shared-auth",
  "name": "Shared Authentication Library",
  "path": "libs/shared-auth",
  "kind": "library",
  "purpose": "Authentication contracts and utilities shared across APIs",
  "runtime": "dotnet",
  "owner": "platform-security",
  "criticality": "high",
  "deployable": false,
  "inherits": ["repo-default"],
  "dependsOn": [],
  "tags": ["shared", "security"],
  "platforms": [],
  "overrides": {}
}
```

### Validation Rules

- `id` MUST be unique, lowercase, and path-safe
- `path` MUST point to a directory inside the repository
- `inherits` entries MUST resolve to declared profiles
- `dependsOn` entries MUST resolve to declared app ids
- Cyclic dependencies MUST be rejected
- `overrides` MAY be omitted; if present they MUST resolve inside the repository
- Governance-requiring workflows MUST always resolve a repository constitution
- `kind: "library"` entries with `deployable: false` MUST NOT be valid targets for deployment workflows
- `{app.path}/app.json`, if present, MUST conform to the app-local manifest schema (tags, hints,
  rules only); identity fields are ignored with a validation warning *(Added 2026-04-07)*

### Standard v1 Conventions

These paths are derived from the registered app path:

- App documentation root: `{app.path}/.documentation/`
- App-local manifest: `{app.path}/app.json` (optional) *(Added 2026-04-07)*
- Constitution: `{app.path}/.documentation/memory/constitution.md`
- Commands: `{app.path}/.documentation/commands/`
- Scripts: `{app.path}/.documentation/scripts/`
- Templates: `{app.path}/.documentation/templates/`
- Specs: `{app.path}/.documentation/specs/`

### Example Full Registry

```json
{
  "version": 1,
  "mode": "multi-app",
  "profiles": {
    "repo-default": {
      "description": "Mandatory repository-wide governance and workflow defaults",
      "tags": {},
      "rules": ["All apps must pass repo-wide lint checks"],
      "hints": {}
    },
    "api-profile": {
      "description": "Contract-first API rules, backward compatibility, observability",
      "tags": { "runtime-class": "api" },
      "rules": ["API changes must include contract tests"],
      "hints": { "test-runner": "pytest", "review-depth": "thorough" }
    },
    "admin-profile": {
      "description": "Administrative auditability and authorization rigor",
      "tags": { "access-model": "role-based" },
      "rules": ["Admin operations must be audit-logged"],
      "hints": {}
    },
    "web-profile": {
      "description": "Accessibility, browser support, frontend testing",
      "tags": { "runtime-class": "web" },
      "rules": ["WCAG 2.1 AA compliance required"],
      "hints": { "test-runner": "vitest" }
    },
    "qa-profile": {
      "description": "Environment-safe test execution and fixture isolation",
      "tags": { "runtime-class": "qa" },
      "rules": ["QA harness must not mutate production data"],
      "hints": { "review-depth": "standard" }
    }
  },
  "apps": [
    {
      "id": "runtime-api-a",
      "name": "Runtime API A",
      "path": "apps/runtime-api-a",
      "kind": "runtime-api",
      "purpose": "Primary production runtime API",
      "runtime": "dotnet",
      "owner": "runtime-platform",
      "criticality": "high",
      "deployable": true,
      "inherits": ["repo-default", "api-profile"],
      "dependsOn": []
    },
    {
      "id": "runtime-api-b",
      "name": "Runtime API B",
      "path": "apps/runtime-api-b",
      "kind": "runtime-api",
      "purpose": "Secondary production runtime API",
      "runtime": "dotnet",
      "owner": "runtime-platform",
      "criticality": "high",
      "deployable": true,
      "inherits": ["repo-default", "api-profile"],
      "dependsOn": []
    },
    {
      "id": "shared-auth",
      "name": "Shared Authentication Library",
      "path": "libs/shared-auth",
      "kind": "library",
      "purpose": "Authentication contracts shared across APIs",
      "runtime": "dotnet",
      "owner": "platform-security",
      "criticality": "high",
      "deployable": false,
      "inherits": ["repo-default"],
      "dependsOn": []
    },
    {
      "id": "admin-api",
      "name": "Admin and Maintenance API",
      "path": "apps/admin-api",
      "kind": "admin-api",
      "purpose": "Administrative and maintenance operations",
      "runtime": "dotnet",
      "owner": "platform-admin",
      "criticality": "high",
      "deployable": true,
      "inherits": ["repo-default", "api-profile", "admin-profile"],
      "dependsOn": ["runtime-api-a", "runtime-api-b", "shared-auth"]
    },
    {
      "id": "admin-web",
      "name": "Admin Configuration Application",
      "path": "apps/admin-web",
      "kind": "web-admin",
      "purpose": "Internal operational and configuration interface",
      "runtime": "react",
      "owner": "platform-admin",
      "criticality": "medium",
      "deployable": true,
      "inherits": ["repo-default", "web-profile", "admin-profile"],
      "dependsOn": ["admin-api"]
    },
    {
      "id": "client-web",
      "name": "Client Facing Application",
      "path": "apps/client-web",
      "kind": "web-client",
      "purpose": "External user-facing application",
      "runtime": "react",
      "owner": "client-experience",
      "criticality": "high",
      "deployable": true,
      "inherits": ["repo-default", "web-profile"],
      "dependsOn": ["runtime-api-a", "runtime-api-b", "shared-auth"]
    },
    {
      "id": "qa-harness",
      "name": "Runtime API Test Harness",
      "path": "apps/qa-harness",
      "kind": "qa-harness",
      "purpose": "Quality assurance execution against runtime APIs",
      "runtime": "node",
      "owner": "quality-engineering",
      "criticality": "medium",
      "deployable": false,
      "inherits": ["repo-default", "qa-profile"],
      "dependsOn": ["runtime-api-a", "runtime-api-b", "admin-api"]
    }
  ]
}
```

## Design: App Context Propagation

App context must propagate through the entire workflow chain. A command that targets `admin-web` must
pass that scope to all invoked scripts, all generated artifacts, and all review or planning steps.

For multi-app repositories, scope propagation distinguishes between two documentation levels:

- Repo scope uses the repository root `.documentation/`
- App scope uses the selected application's `{app.path}/.documentation/`

DevSpark must never remap app-scoped artifacts into nested folders under the repo root `.documentation/`
when the application has its own documentation root.

## Design: Multi-App Command Surface

v1 introduces three new commands: *(Updated 2026-04-07: validate-registry added per leadership decision Q3)*

### `/devspark.add-application`

- Collects required app metadata: id, name, path, kind, purpose, owner, criticality, inherited profiles,
  and dependencies
- Validates: duplicate ids, invalid paths, invalid profile references, invalid dependency references
- Updates the authoritative root registry at `.documentation/devspark.json`
- Always scaffolds `{app.path}/.documentation/` with standard subdirectories
  *(Updated 2026-04-07: scaffolding is always performed, no --scaffold flag per leadership decision Q5)*
- Never installs or modifies `.devspark/`

### `/devspark.list-applications`

- Reads the authoritative root registry
- Displays registered apps in a human-readable table: id, path, kind, owner, criticality, dependencies,
  effective documentation root
- Read-only; no file mutations

### `/devspark.validate-registry` *(Added 2026-04-07: leadership decision Q3)*

- Standalone validation command for `.documentation/devspark.json`
- Checks: JSON schema validity, unique ids, path existence, profile reference resolution, dependency
  reference resolution, cyclic dependency detection, and app-local manifest (`app.json`) consistency
- Produces structured validation output: list of errors, warnings, and pass/fail status
- Read-only; no file mutations
- Usable in CI pipelines as a pre-merge check

## Design: App-Local Manifest (`app.json`) *(Added 2026-04-07: leadership decision Q1)*

### Purpose

Allow application teams to declare app-specific overrides (tags, hints, local rules) close to their
code without requiring every change to go through the centralized registry file.

### Schema

```json
{
  "tags": { "deploy-target": "k8s-east", "feature-flags": "enabled" },
  "hints": { "test-runner": "jest", "review-depth": "thorough" },
  "rules": ["All API responses must include correlation-id header"]
}
```

### Merge Behavior

The app-local manifest is merged **after** profile composition and **before** final resolution:

1. Load registry entry for the app (id, path, kind, owner, dependencies, inherits, overrides)
2. Compose inherited profiles (tags/rules/hints from the `inherits` chain)
3. Apply registry-level `overrides` field
4. Load `{app.path}/app.json` if it exists
5. Merge app.json content: tags overwrite (last-writer-wins), rules accumulate (additive),
   hints overwrite (last-writer-wins)
6. Run weakening detection on the final effective rule set against repo-wide mandatory rules

### Constraints

- `app.json` MUST NOT contain identity fields (id, path, kind, owner, dependencies, inherits) —
  these are registry-only; if present they are ignored with a validation warning
- `app.json` rules MUST NOT weaken mandatory repo-wide rules (same weakening detection as
  constitution overlays)
- Missing `app.json` is valid — the app uses only registry + profile composition
- `/devspark.validate-registry` checks `app.json` files for schema conformance and
  weakening conflicts

## Design: Dependency Inference *(Added 2026-04-07: leadership decision Q2)*

### Purpose

Supplement declared `dependsOn` entries with basic inference from source code and build configuration
so that scope reports surface undeclared cross-app dependencies.

### Inference Sources

| Source Type | Files Scanned | What Is Matched |
|-------------|--------------|-----------------|
| Source imports | `*.py`, `*.ts`, `*.js`, `*.cs`, `*.java` | Import/require paths containing another registered app's `path` segment |
| Build config | `package.json`, `pyproject.toml`, `*.csproj` | Project references, workspace references, or dependency entries pointing to another registered app path |

### Inference Rules

1. For each registered app, extract its `path` value (e.g., `apps/admin-api`)
2. Scan source and build files in the current app's `path` directory
3. Match references that contain another registered app's path segment
4. Report matched references as **inferred** dependencies, distinct from **declared** dependencies

### Reporting

Scope reports include two dependency sections:

```text
Declared dependencies: admin-api, shared-auth
Inferred dependencies: runtime-api-a (from apps/admin-web/src/api-client.ts import)
```

### Constraints

- Inference is best-effort and clearly labeled; it does not trigger hard failures
- Inferred dependencies that match declared dependencies are deduplicated (shown only in declared)
- Inference scanning respects `.gitignore` patterns to avoid scanning build artifacts
- Performance: inference is scoped to the primary app's directory tree, not the entire repo
- Inference runs only when a scope report is generated (not on every registry load)

## Design: Rationale Capture Pattern

### Purpose

Surface decision context at the top of every generated artifact so reviewers understand intent without
reverse-engineering the document body. This is a documentation-layer enhancement: no runtime validation,
no blocking gates, no schema enforcement.

### Standard Rationale Block

Every spec, plan, and tasks artifact renders this block immediately after the document header metadata:

```markdown
## Rationale Summary

### Core Problem
[What problem are we solving?]

### Decision Summary
[What was decided and why (1–3 sentences max)?]

### Key Drivers
- [Business driver]
- [Technical constraint]
- [User/operational impact]

### Source Inputs
- [Spec / ticket / discussion reference]
- [System constraints or prior patterns]
- [Relevant data or telemetry insights]

### Tradeoffs Considered
- Option A: [why not chosen]
- Option B: [why not chosen]
- Selected: [why chosen]

### Architectural Impact
- [What changes in system behavior or structure]
- [Backward compatibility considerations]
- [Dependencies introduced or avoided]

### Reviewer Guidance
[What should reviewers focus on?]
```

### Population Rules by Command

| Command | Source | Rationale Sections Populated |
|---------|--------|-----------------------------|
| `/devspark.specify` | User feature description | All seven sections synthesized from user input |
| `/devspark.plan` | spec.md + research.md | Carry forward from spec; augment with technical tradeoffs, research findings, architecture decisions |
| `/devspark.tasks` | plan.md + spec.md | Carry forward Core Problem, Decision Summary, Key Drivers; set Reviewer Guidance to task-specific focus (ordering, dependencies, MVP scope) |
| `/devspark.critic` | spec.md + plan.md + tasks.md | Validate presence and consistency across all three; flag gaps and drift |

### Critic Enforcement Rules

`/devspark.critic` adds a **Rationale & Traceability Risks** category to its risk detection framework:

- **Missing Rationale Summary** in any artifact → HIGH severity
- **Rationale drift** (Core Problem or Decision Summary contradicts between spec/plan/tasks) → CRITICAL severity
- **Missing tradeoffs** for major architecture decisions → HIGH severity
- **Placeholder or unfilled rationale sections** → HIGH severity

The Architecture Red Flags checklist in the critic report adds:

- [ ] Missing or incomplete Rationale Summary in spec.md
- [ ] Missing or incomplete Rationale Summary in plan.md
- [ ] Missing or incomplete Rationale Summary in tasks.md
- [ ] Rationale drift between spec and plan (Core Problem mismatch)
- [ ] Tradeoffs not documented for major architecture decisions

### Template Changes Required

The following template files need the Rationale Summary block injected:

| Template | Block Placement | Sections Included |
|----------|----------------|-------------------|
| `templates/spec-template.md` | After header metadata, before User Scenarios | All seven sections |
| `templates/plan-template.md` | After header metadata, before Summary | All seven sections (spec-aware placeholders) |
| `templates/tasks-template.md` | After header metadata, before Format section | Core Problem, Decision Summary, Key Drivers, Reviewer Guidance |

A standalone `templates/rationale-template.md` provides the canonical block for reference.

### Command Instruction Changes Required

| Command File | Change |
|-------------|--------|
| `templates/commands/specify.md` | Add step to populate Rationale Summary from user description |
| `templates/commands/plan.md` | Add step to carry forward and augment rationale from spec |
| `templates/commands/tasks.md` | Add step to carry forward rationale from plan |
| `templates/commands/critic.md` | Add Rationale & Traceability Risks category; add rationale red flags to checklist |

### Backward Compatibility

This pattern is purely additive:

- Existing artifacts without the block continue to work
- No workflow produces an error for missing rationale
- The critic reports missing rationale as a risk, not a gate failure
- Single-app and multi-app repositories both benefit

### Deferred Enhancements

- **Machine-readable variant**: JSON rationale object for diff-based comparison and automated governance
- **Rationale drift detection**: Automated spec-vs-plan-vs-tasks consistency checking beyond critic
- **Critic enforcement rules**: Fail builds if rationale is weak or missing (governance gate)

## Delivery Strategy

### V1 Split: v1a and v1b

This feature is delivered in two gated milestones to reduce merge conflict risk and enable earlier
feedback on the core model before building the full workflow surface.

#### v1a — Registry, Resolution, and Backward Compatibility

Scope:

- Authoritative repository registry in `.documentation/devspark.json`
- Optional app-local manifests (`{app.path}/app.json`) for app-specific overrides *(Added 2026-04-07)*
- Pydantic-based schema validation (Python), jq-based checks (Bash), ConvertFrom-Json checks (PowerShell)
- Convention-based app paths derived from the registered app path
- Repository constitution plus additive app constitution overlay with weakening detection
- Explicit app selection and explicit repo-scope execution
- App-aware resolution for constitutions, prompts, scripts, and templates
- App-scoped artifact directories (specs/plans/tasks at `{app.path}/.documentation/specs/`)
- Declared dependency reporting plus basic dependency inference from source imports and build
  configuration files *(Updated 2026-04-07)*
- Scope report output (repo/single-app/multi-app) on every workflow
- Full backward compatibility for single-app repositories

Exit gate: all six-app fixture tests pass for resolution, scope reporting, and dependency reporting;
all single-app regression tests pass; leadership approves the operating model.

#### v1b — PR Scope, Commands, and Packaging

Scope (requires v1a merged and stable):

- Pull request scope declaration and validation (`single-app`, `cross-app`, `repo-scope`)
- Approved shared path categorization for single-app PR validation
- `/devspark.add-application`, `/devspark.list-applications`, and `/devspark.validate-registry`
  commands *(Updated 2026-04-07: validate-registry added)*
- Updated release packaging and shim content
- Updated quickstart guidance for single-app and multi-app installs
- CLI support for initializing or upgrading repos with multi-app mode
- Migration guidance and examples

Exit gate: PR scope validation tests pass; add/list/validate commands pass; packaging produces
consistent artifacts; quickstarts are updated; no regression in single-app behavior.

### Deferred Beyond v1

- App-specific user override layers
- Complex non-conventional layouts unless explicitly overridden
- Broader app lifecycle commands (remove, rename, move, split)
- Dependency audit command
- Structured YAML rules for constitution enforcement
- Advanced dependency inference (transitive analysis, code-level call graph)

### Workstream 1 — Configuration and Resolution Model (v1a) — Effort: L

Deliverables:

- Registry loading and Pydantic validation (Python)
- App-local manifest (`app.json`) loading, schema validation, and merge into resolution chain
  *(Added 2026-04-07)*
- jq-based registry validation (Bash), ConvertFrom-Json validation (PowerShell)
- App-aware resolution contract for constitutions, prompts, scripts, and templates
- Constitution composition with keyword-based weakening detection
- Repo-scope versus app-scope execution rules
- Scope-selection decision table implementation
- Declared dependency reporting plus basic dependency inference from source imports and build
  configuration files *(Updated 2026-04-07)*
- Scope report format for workflow output (declared and inferred dependency sections)

Primary code surfaces:

- `scripts/bash/common.sh`
- `scripts/bash/platform.sh`
- `scripts/powershell/common.ps1`
- `scripts/powershell/platform.ps1`
- `src/devspark_cli/__init__.py`
- `src/devspark_cli/registry.py`
- `src/devspark_cli/scope.py`
- `src/devspark_cli/resolution.py`
- `src/devspark_cli/inference.py` (new) *(Added 2026-04-07)*

Exit criteria:

- Single-app mode remains the default path
- Multi-app mode is opt-in and validated
- Resolution order is documented and testable
- Declared and inferred downstream impacts are reported for shared changes *(Updated 2026-04-07)*
- App-local manifests merge correctly into the resolution chain *(Added 2026-04-07)*
- All Bash functions have a PowerShell equivalent (parity check)

### Workstream 2 — Script and Prompt Propagation (v1a + v1b) — Effort: XL

Deliverables:

- Common app selection and validation helpers for Bash and PowerShell
- App-aware spec directory discovery and branch-scoped feature creation
- Prompt templates updated to use app-aware paths and scope reporting
- Pull request declaration and review behavior for three scope modes (v1b)
- Validation comparing declared PR scope with changed paths (v1b)
- `/devspark.add-application`, `/devspark.list-applications`, and `/devspark.validate-registry`
  flows (v1b) *(Updated 2026-04-07)*
- Fallback behavior for repo-scoped workflows

Primary code surfaces:

- `scripts/bash/create-new-feature.sh`
- `scripts/bash/setup-plan.sh`
- `scripts/bash/get-pr-context.sh`
- `scripts/bash/quickfix-context.sh`
- `scripts/bash/release-context.sh`
- `scripts/bash/repo-story-context.sh`
- `scripts/bash/site-audit.sh`
- PowerShell equivalents (15 files)
- `templates/commands/pr-review.md`
- `templates/commands/add-application.md` (new, v1b)
- `templates/commands/list-applications.md` (new, v1b)
- `templates/commands/validate-registry.md` (new, v1b) *(Added 2026-04-07)*
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
- No workflow writes app-scoped artifacts into `.devspark/` or into nested folders under root `.documentation/`
- Missing or ambiguous app context fails clearly
- Single-app PRs fail when changed paths show undeclared multi-app scope (v1b)
- Add-application updates the registry and always scaffolds `{app.path}/.documentation/` (v1b)
  *(Updated 2026-04-07)*
- List-applications remains read-only (v1b)
- Validate-registry produces structured validation output and is read-only (v1b) *(Added 2026-04-07)*

### Workstream 3 — Packaging, Quickstarts, and CLI (v1b) — Effort: M

Deliverables:

- Updated release package generation and shim content
- Quickstart guidance for single-app and multi-app installs
- CLI support for initializing or upgrading repos that opt into multi-app mode
- Example layout and migration guidance
- Install/upgrade rules: DevSpark deploys only `.devspark/` and agent shims

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
- Upgrade paths do not overwrite user-owned `.documentation/` content

### Workstream 5 — Rationale Capture Pattern (v1a) — Effort: S

Deliverables:

- Rationale Summary block added to `templates/spec-template.md`, `templates/plan-template.md`,
  `templates/tasks-template.md`
- Standalone `templates/rationale-template.md` for reference
- `/devspark.specify` command updated to populate rationale from user description
- `/devspark.plan` command updated to carry forward and augment rationale from spec
- `/devspark.tasks` command updated to carry forward rationale from plan
- `/devspark.critic` command updated with Rationale & Traceability Risks category and rationale
  red flags in the Architecture Red Flags checklist

Primary code surfaces:

- `templates/spec-template.md`
- `templates/plan-template.md`
- `templates/tasks-template.md`
- `templates/rationale-template.md` (new)
- `templates/commands/specify.md`
- `templates/commands/plan.md`
- `templates/commands/tasks.md`
- `templates/commands/critic.md`

Exit criteria:

- All four templates contain the Rationale Summary block in the correct position
- All four commands reference and populate the block
- Existing single-app workflows produce no errors with the new block present
- Critic detects missing rationale and rationale drift between artifacts

### Workstream 4 — Validation, Fixtures, and Hardening (v1a + v1b) — Effort: L

Deliverables:

- Fixture repository trees (see Validation Matrix below)
- Validation for malformed registry state and dependency cycles
- Regression checks for single-app behavior
- Regression checks that install/upgrade never mutates `.documentation/`
- Bash/PowerShell parity validation (see below)
- PR scope validation fixtures (v1b)
- Add/list application validation fixtures (v1b)

Primary code surfaces:

- Script validation logic in Bash and PowerShell
- CLI validation paths
- Fixture content under test assets

Exit criteria:

- Known-bad registry configurations fail fast
- Single-app regression checks pass
- All validation matrix scenarios pass

## Effort Summary

| Workstream | Milestone | T-Shirt Size | Primary Risk |
|------------|-----------|-------------|--------------|
| WS1 — Configuration & Resolution | v1a | L | Registry schema churn if leadership changes authority model |
| WS2 — Script & Prompt Propagation | v1a + v1b | XL | 15+ script files × 2 platforms; highest divergence risk |
| WS3 — Packaging & Quickstarts | v1b | M | Low technical risk; coordination with release tooling |
| WS4 — Validation & Hardening | v1a + v1b | L | Fixture complexity; parity testing surface area |
| WS5 — Rationale Capture Pattern | v1a | S | Low risk; pure template/command additions |

## Phase Plan

### Phase 0 — Finalize the design contract (v1a gate) — **COMPLETE**

All leadership decisions resolved 2026-04-07 (see spec.md "Leadership Decisions" section):

- [x] Approve the authority model for `.documentation/devspark.json`
- [x] Approve the ownership model: `.devspark/` is installed, `.documentation/` is repo-owned
- [x] Approve the resolution order
- [x] Approve the explicit app scope decision
- [x] Approve app-local manifests (`app.json`) as subset mirrors (Q1)
- [x] Approve basic dependency inference from imports + build config (Q2)
- [x] Approve v1 command surface: add + list + validate-registry (Q3)
- [x] Approve shared path categories (Q4 — current list confirmed)
- [x] Approve always-scaffold behavior for add-application (Q5)
- [x] Approve the profile composition model (tags/rules/hints)
- [x] Approve the scope-selection decision table
- [x] Approve the v1a/v1b split boundary

Output: approved design baseline for v1a implementation.

### Phase 1 — Implement core resolution primitives (v1a)

Tasks:

- Add Pydantic model for registry loading and validation
- Add app-local manifest (`app.json`) Pydantic model, loading, and merge logic *(Added 2026-04-07)*
- Add jq-based validation helpers for Bash
- Add ConvertFrom-Json validation helpers for PowerShell
- Add app-aware helper functions to platform layers
- Define standard scope object
- Define repo-scope vs app-scope documentation root resolution
- Implement constitution composition with weakening detection
- Implement declared dependency reporting plus basic dependency inference from source imports
  and build configuration files *(Updated 2026-04-07)*

Output: shared primitives used by workflows and CLI.

### Phase 2 — Convert prompts and scripts (v1a core, v1b extensions)

Tasks (v1a):

- Update workflows to accept and propagate app context
- Route artifacts to correct scope directories
- Add scope summaries to outputs
- Verify Bash/PowerShell parity for all updated scripts

Tasks (v1b):

- Update PR review flows to validate declared scope
- Implement add-application (always-scaffold), list-applications, and validate-registry commands
  *(Updated 2026-04-07)*
- Define approved shared path validation

Output: end-to-end app-aware workflows.

### Phase 3 — Update install and upgrade surfaces (v1b)

Tasks:

- Update release packaging and shim generation
- Update quickstarts and docs
- Update CLI init and upgrade behavior
- Verify install/upgrade never touches `.documentation/`

Output: consistent install, upgrade, and execution model.

### Phase 4 — Validate and harden (v1a + v1b)

Tasks:

- Build fixture repositories
- Run full validation matrix
- Run single-app regression suite
- Run Bash/PowerShell parity checks
- Refine error messages and migration guidance

Output: leadership-ready implementation confidence.

## Validation Matrix

### Fixture Repositories

| Fixture | Apps | Purpose |
|---------|------|---------|
| `fixture-single-app` | 0 (no registry) | Baseline regression for current behavior |
| `fixture-two-api` | 2 runtime APIs | Minimal multi-app scenario |
| `fixture-full-monorepo` | 6 apps + 1 library | Full heterogeneous scenario from spec |

### Resolution Validation

| # | Fixture | Input | Expected Result | Pass Criteria |
|---|---------|-------|-----------------|---------------|
| R1 | single-app | Run `/devspark.plan` | Repo-scope artifacts at `.documentation/specs/` | Identical to pre-feature baseline |
| R2 | single-app | Run `/devspark.plan --app foo` | Error | "No multi-app registry found" message |
| R3 | full-monorepo | `/devspark.plan --app runtime-api-a` | Artifacts at `apps/runtime-api-a/.documentation/specs/` | Scope report shows `scope: single-app, app: runtime-api-a` |
| R4 | full-monorepo | `/devspark.plan --app admin-web` | Artifacts at `apps/admin-web/.documentation/specs/` | Admin-web constitution used, not runtime-api-a constitution |
| R5 | full-monorepo | `/devspark.plan` with no `--app` | Error | "Multiple apps registered; specify --app or use repo scope" |
| R6 | full-monorepo | `/devspark.plan --repo-scope` | Artifacts at `.documentation/specs/` | Scope report shows `scope: repo` |

### Dependency Validation

| # | Fixture | Input | Expected Result | Pass Criteria |
|---|---------|-------|-----------------|---------------|
| D1 | full-monorepo | Repo-scope workflow touching `shared-auth` | Scope report lists admin-api, client-web as impacted (declared) | Downstream apps from `dependsOn` graph present |
| D2 | full-monorepo | App-scope workflow for `admin-web` only | No downstream impact | Scope report shows empty impacted list |
| D3 | full-monorepo | App with undeclared import of another app path | Inferred dependency shown in scope report, labeled "inferred" | Inferred section populated, declared section does not contain it |
| D4 | full-monorepo | App with declared dep that also appears in imports | Dependency shown only in declared section, not duplicated in inferred | Deduplication works correctly |

### PR Scope Validation (v1b)

| # | Fixture | PR Declaration | Changed Paths | Expected Result |
|---|---------|---------------|---------------|-----------------|
| P1 | full-monorepo | `single-app: admin-web` | `apps/admin-web/src/...` | Pass |
| P2 | full-monorepo | `single-app: admin-web` | `apps/admin-web/...` + `.github/...` | Pass (approved shared path) |
| P3 | full-monorepo | `single-app: admin-web` | `apps/admin-web/...` + `apps/admin-api/...` | Fail: scope mismatch, suggest cross-app |
| P4 | full-monorepo | `cross-app: primary=admin-web, affected=admin-api` | Both app paths | Pass with combined scope report |
| P5 | full-monorepo | `repo-scope` | `libs/shared-auth/...` | Pass with impacted app listing |

### Registry Validation

| # | Input | Expected Result |
|---|-------|-----------------|
| V1 | Duplicate app id | Fail: "duplicate id: admin-api" |
| V2 | Invalid path (nonexistent directory) | Fail: "path does not exist: apps/ghost" |
| V3 | Unknown profile reference | Fail: "unknown profile: missing-profile" |
| V4 | Cyclic dependency (A→B→C→A) | Fail: "cyclic dependency detected" |
| V5 | Missing repository constitution | Fail: "repository constitution required" |
| V6 | Valid registry, all references resolve | Pass |
| V7 | app.json with identity fields (id, path) | Warning: "identity fields ignored in app.json" — validation passes but warns |
| V8 | app.json with rule that weakens mandatory repo rule | Warning: "app.json rule weakens mandatory rule" — weakening detection catches it |
| V9 | app.json with valid tags/hints/rules only | Pass — merged correctly into resolution |

### Command Validation (v1b)

| # | Command | Input | Expected Result |
|---|---------|-------|-----------------|
| C1 | add-application | Valid new app | Registry updated + `{app.path}/.documentation/` scaffolded |
| C2 | add-application | Duplicate id | Error, registry unchanged |
| C3 | list-applications | 6-app registry | Table with 6 rows, correct columns |
| C4 | list-applications | No registry | "No multi-app registry configured" message |
| C5 | validate-registry | Valid registry + valid app.json files | Pass with structured output |
| C6 | validate-registry | Registry with errors (duplicate id, bad path) | Fail with itemized error list |
| C7 | validate-registry | Registry valid but app.json has identity fields | Pass with warnings |

### Bash/PowerShell Parity Validation

For each function added or modified in Bash:

1. Verify a PowerShell equivalent exists with matching name and parameter signature
2. Run both against the same fixture input
3. Compare structured output (JSON mode) for equivalence
4. Log any divergence as a parity failure

This check runs as part of Workstream 4 for every modified script pair.

## Recommended Testing Strategy

- Fixture repositories are committed as test assets and version-controlled
- Each validation matrix row maps to a discrete test case
- Single-app regression suite runs on every PR to the feature branch
- Parity checks run on every PR that modifies a Bash or PowerShell script
- Install/upgrade regression verifies `.documentation/` is untouched after framework operations

## Key Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Partial rollout updates docs but not runtime | High | High | Sequence packaging after runtime resolution is implemented |
| App-specific overrides proliferate and drift | Medium | High | Profile inheritance and validate override usage |
| Scope ambiguity confuses users | High | High | Make app selection explicit and print scope in outputs |
| Undeclared multi-app PRs reviewed as local | High | High | Require explicit PR scope and validate against changed paths |
| Multi-app command surface grows prematurely | Medium | Medium | Limit v1 to add, list, and validate-registry only |
| Bash and PowerShell behavior diverges | Medium | High | Parity validation on every PR |
| CLI and prompt-template behavior drift | Medium | High | Registry contract as single source of truth |
| v1a/v1b boundary shifts during implementation | Medium | Medium | Hard gate: v1b does not start until v1a passes all fixture tests |

## Leadership Review Focus Areas — **All Resolved 2026-04-07**

All items below were resolved via leadership decisions recorded in spec.md:

- [x] Registry authority model — Approved
- [x] Explicit app scope — Approved
- [x] v1a/v1b split boundary — Approved
- [x] Profile composition model — Approved
- [x] Keyword-based weakening detection — Approved for v1
- [x] Dependency reporting — Declared + basic inference approved (Q2)
- [x] PR scope policy — Approved as specified
- [x] App-local manifests — Subset mirrors approved (Q1)
- [x] CLI command surface — Add + list + validate-registry approved (Q3)
- [x] Shared path categories — Current list confirmed (Q4)
- [x] Scaffolding — Always scaffold approved (Q5)

## Recommended Next Implementation Slice

Start with Workstream 1 (v1a): introduce the repository registry contract, app-local manifest
support, Pydantic validation, app-aware resolution order, constitution composition, and declared
plus inferred dependency reporting. Do not begin per-command rewrites until the core resolution
primitives are proven against fixture tests.
