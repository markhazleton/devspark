# Feature Specification: Multi-Application Monorepo Support

**Feature Branch**: `feature/monorepo-multi-app-support`  
**Created**: 2026-04-06  
**Status**: Draft for Technical Leadership Review  
**Input**: User description: "Update DevSpark to support multiple applications within a single repository using monorepo best practices, with repo-wide constitutions, prompts, and scripts plus application-specific overrides for constitution, prompts, and scripts when needed."

## Background

DevSpark currently assumes a single application boundary per repository. That assumption is embedded in
its prompt resolution, script resolution, constitution loading, specification storage, and review flows.

That model breaks down for repositories that contain multiple applications with different platforms,
responsibilities, and risk profiles, for example:

- Two runtime APIs serving production traffic
- One admin or maintenance API
- One React-based admin configuration application
- One client-facing application
- One QA runtime API test harness

These applications often share repository-wide engineering rules, but they do not share the same runtime
constraints, testing obligations, operational posture, or review criteria. A client-facing React app,
for example, has materially different non-functional constraints than a runtime API or an internal test
harness.

The objective of this feature is to let DevSpark model that reality without fragmenting into several
independent DevSpark installations inside one repository.

## Problem Statement

DevSpark needs to support heterogeneous multi-application repositories while preserving three properties:

1. A single repository-wide source of truth for shared governance and shared DevSpark defaults
2. Application-specific overlays for constitutions, prompts, scripts, templates, and specifications
3. Explicit, reviewable app context so workflows remain deterministic and leadership can reason about
   scope, ownership, and impact

The solution must avoid hidden inference, duplicated framework installations, and governance drift.

## Goals

- Support repositories containing multiple applications with different platforms and purposes
- Preserve a repository-wide constitution and shared DevSpark defaults
- Allow application-specific constitutions that strengthen or extend repo-wide rules
- Allow application-specific prompt, script, and template overrides
- Make app context explicit in command and script execution
- Support dependency-aware planning and review for changes that affect multiple applications
- Preserve full backward compatibility for current single-application repositories
- Favor simple conventions over highly configurable layouts
- Favor explicit scope selection over inferred or implicit behavior

## Non-Goals

- Create completely isolated DevSpark installations per application
- Infer app context only from current working directory or branch naming
- Allow app-level governance to weaken mandatory repository-wide governance
- Fully solve shared library ownership or shared package release orchestration in this first iteration
- Introduce a breaking change that forces existing single-app repositories to migrate immediately

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Govern a heterogeneous multi-app repository (Priority: P1)

As a technical lead, I need DevSpark to distinguish between applications in the same repository so that
reviews, plans, and specifications apply the correct governance rules for each application type.

**Why this priority**: Without reliable app boundaries, DevSpark produces incorrect plans and reviews,
which undermines its value in the exact repositories that are hardest to manage.

**Independent Test**: Configure a repository with at least one runtime API and one React admin
application, then run equivalent DevSpark workflows for both and confirm the system resolves different
app-specific constitutions and overrides while preserving repo-wide governance.

**Acceptance Scenarios**:

1. **Given** a repository with repo-wide governance and app-specific constitutions for `runtime-api-a`
   and `admin-web`, **When** a plan or review workflow runs for `runtime-api-a`, **Then** DevSpark uses
   the repo-wide governance plus the `runtime-api-a` overlay and does not apply the `admin-web` overlay.
2. **Given** the same repository, **When** a plan or review workflow runs for `admin-web`, **Then**
   DevSpark uses the repo-wide governance plus the `admin-web` overlay and does not apply the
   `runtime-api-a` overlay.

---

### User Story 2 - Execute app-scoped workflows with explicit context (Priority: P1)

As an engineer, I need to run DevSpark commands against a specific application so that specifications,
plans, and implementation tasks land in the correct app scope instead of a single shared repo scope.

**Why this priority**: Multi-app support is not real unless app context is passed through prompts,
scripts, and generated artifacts in a deterministic way.

**Independent Test**: Run a feature workflow with explicit app context for `admin-api` and verify the
resulting spec, plan, and tasks are created under the `admin-api` scope and use the correct resolution
chain.

**Acceptance Scenarios**:

1. **Given** a registered application `admin-api`, **When** a user invokes a workflow with that app
   context, **Then** artifacts are created under the `admin-api` scope and script resolution checks the
   `admin-api` override tier before repo-wide tiers.
2. **Given** no explicit app context, **When** the user runs a repo-wide workflow, **Then** DevSpark
   operates in repo scope and does not silently guess an application.

---

### User Story 3 - Review cross-application changes safely (Priority: P1)

As an architect or reviewer, I need DevSpark to recognize when a change affects more than one
application so that the generated plan and review account for downstream dependencies and shared risks.

**Why this priority**: In monorepos, the highest-cost failures are usually caused by cross-app impacts
that were treated as local changes.

**Independent Test**: Define an application dependency graph where `admin-web` depends on `admin-api`
and the QA harness targets both runtime APIs, then run a workflow for a shared authentication change and
verify that impacted applications are identified and included in the plan or review scope.

**Acceptance Scenarios**:

1. **Given** a declared dependency graph, **When** a change touches a shared contract or shared module,
   **Then** DevSpark identifies impacted applications and includes them in the resulting scope report.
2. **Given** a change limited to one application with no downstream consumers, **When** a workflow runs,
   **Then** DevSpark keeps the scope local to that application.
3. **Given** a pull request declared as single-app for `admin-web`, **When** the changed files touch only
  `admin-web` plus approved shared paths, **Then** DevSpark reviews it as a single-app pull request.
4. **Given** a pull request declared as single-app for `admin-web`, **When** the changed files also touch
  `admin-api`, **Then** DevSpark fails validation or requires reclassification as cross-app or repo-scope.
5. **Given** a pull request declared as cross-app with primary app `admin-web` and affected app
  `admin-api`, **When** the changed files touch both app paths, **Then** DevSpark reviews the pull
  request using repo-wide governance plus the declared app scopes and emits the combined scope report.

---

### User Story 4 - Keep single-application repositories unchanged (Priority: P2)

As an existing DevSpark user, I need current single-application repositories to continue working without
restructure or behavior changes so that multi-app support is an additive capability, not a forced
migration.

**Why this priority**: Breaking the current installation model would create adoption resistance and add
unnecessary migration cost.

**Independent Test**: Run existing DevSpark workflows in a repository that does not define any app
registry or app directories and confirm that behavior matches the current single-app model.

**Acceptance Scenarios**:

1. **Given** a repository with only the current `.documentation/` and `.devspark/` structure, **When**
   workflows run, **Then** DevSpark behaves exactly as it does today.
2. **Given** a repository that opts into multi-app mode, **When** repo-wide workflows run without app
   context, **Then** DevSpark still supports repo-scoped operations.

---

### User Story 5 - Limit customization drift through profile-based inheritance (Priority: P2)

As a platform owner, I need a model that supports app-specific rules without requiring each application
to fork every prompt and script so that DevSpark remains maintainable across large repositories.

**Why this priority**: A naive per-app override model turns a shared framework into a patchwork of local
variants that are expensive to upgrade and impossible to audit.

**Independent Test**: Configure one runtime API, one admin API, one React admin app, and one QA harness
using profile inheritance plus minimal app-specific deltas, then confirm the resolved rules match the
expected behavior without duplicating all base prompts or scripts.

**Acceptance Scenarios**:

1. **Given** shared repo defaults and reusable profiles such as `api-profile`, `web-profile`, and
   `qa-profile`, **When** an app is resolved, **Then** DevSpark composes the correct inherited context
   and applies only app-specific deltas afterward.
2. **Given** an app-specific override that attempts to weaken a repo-wide mandatory rule, **When** the
   configuration is validated, **Then** DevSpark rejects or flags the conflict.

### Edge Cases

- A change affects both a runtime API and the client-facing application through a shared authentication
  contract.
- A QA harness is intentionally allowed to diverge in tooling from production applications but must still
  inherit shared security and review rules.
- A repository contains shared libraries that are not deployable applications but are depended on by
  several applications.
- An app has no local constitution and should inherit only repo-wide governance plus reusable profiles.
- A user runs a workflow from the repository root while multiple applications are registered.
- A user passes an unknown app identifier.
- A repository defines app-specific scripts for Bash but not PowerShell, or vice versa.
- A change spans multiple applications plus repo-wide documentation or shared platform assets.
- A pull request is declared single-app but its changed files touch more than one registered app path.
- A pull request touches shared contracts or shared libraries but declares only a single app scope.
- A pull request is intentionally cross-app and must name a primary app plus all declared affected apps.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: DevSpark MUST support an explicit repository-level application registry that defines each
  application's identifier, path, type, purpose, dependency relationships, and inheritance profile.
- **FR-002**: DevSpark MUST continue to support a repository-wide constitution, prompts, scripts, and
  templates as the default shared layer.
- **FR-003**: DevSpark MUST support optional application-specific constitutions, prompts, scripts,
  templates, and specification directories.
- **FR-004**: DevSpark MUST require explicit app context for app-scoped workflows through a declared
  parameter, configuration value, or equivalent explicit mechanism; it MUST NOT rely solely on implicit
  inference from current directory or branch naming.
- **FR-005**: DevSpark MUST support repo-scoped workflows that intentionally operate without an app
  context.
- **FR-006**: Constitution resolution MUST always load the repository constitution first and then apply
  an application constitution as an additive overlay when one exists; app constitutions MUST NOT weaken
  mandatory repo-wide rules.
- **FR-007**: Prompt resolution for v1 MUST support a simple, explicit order: app team override,
  repository user override, repository team override, then stock default.
- **FR-008**: Script resolution for v1 MUST support a simple, explicit order: app team override,
  repository team override, then stock default.
- **FR-009**: Template resolution for v1 MUST support a simple, explicit order: app team override,
  repository team override, then stock default.
- **FR-010**: App-scoped specs, plans, tasks, and related artifacts MUST be stored under the owning
  application's scope rather than a single shared specification directory.
- **FR-011**: DevSpark MUST preserve a repo-wide specification scope for changes that are intentionally
  cross-cutting or not owned by a single application.
- **FR-012**: DevSpark MUST support dependency-aware scope analysis so that workflows can identify
  directly impacted downstream applications for shared contract or shared module changes.
- **FR-013**: DevSpark MUST support reusable inheritance profiles so different application classes, such
  as runtime APIs, admin APIs, web applications, and QA harnesses, can share rule sets without copying
  all prompts and scripts.
- **FR-014**: DevSpark MUST prevent application-specific governance from silently weakening mandatory
  repository-wide governance.
- **FR-015**: DevSpark MUST provide validation for malformed multi-app configuration, including unknown
  app identifiers, duplicate app identifiers, invalid paths, cyclic dependencies, and missing required
  files.
- **FR-016**: DevSpark MUST remain backward compatible for repositories that do not opt into multi-app
  mode.
- **FR-017**: DevSpark MUST define a documented on-disk layout for multi-app repositories.
- **FR-018**: DevSpark MUST update packaged templates, quickstart guidance, and CLI behavior so the
  multi-app capability is installable and discoverable, not only documented in source files.
- **FR-019**: DevSpark MUST support platform-diverse applications in a single repository, including API,
  web, internal tooling, and QA-oriented applications, without assuming a single runtime model.
- **FR-020**: DevSpark MUST make the resolved scope visible in workflow output so users and reviewers can
  see whether a command executed in repo scope, single-app scope, or multi-app scope.
- **FR-021**: DevSpark MUST define deterministic scope-selection rules for app-owned changes,
  cross-app changes, shared libraries, shared contracts, infrastructure changes, documentation-only
  changes, and ambiguous root-level execution.
- **FR-022**: v1 MUST use `.documentation/devspark.json` as the only authoritative application registry.
- **FR-023**: v1 MUST derive standard app override paths by convention from the registered app path,
  using `{app.path}/.documentation/` as the default application documentation root, and MUST only use
  explicit path overrides when an application intentionally deviates from those conventions.
- **FR-024**: v1 MUST include direct downstream dependency reporting for shared contract and shared module
  changes before the feature is considered complete.
- **FR-025**: DevSpark packaging, installation, and upgrade flows MUST deploy and update only `.devspark/`
  and agent shim files; they MUST NOT add, remove, or modify files under any repo-owned `.documentation/`
  directory.
- **FR-026**: Multi-app repositories MUST support a two-level documentation model: one repository-level
  `.documentation/` directory for shared governance and registry data, plus optional application-local
  `.documentation/` directories rooted at `{app.path}/.documentation/` for app-owned overrides and
  artifacts.
- **FR-027**: DevSpark MUST support explicit pull request scope declaration with three modes: `single-app`,
  `cross-app`, and `repo-scope`.
- **FR-028**: A `single-app` pull request MUST declare one primary application and MUST validate that the
  changed files touch only that application's registered path plus approved shared or repo-scoped paths.
- **FR-029**: A `cross-app` pull request MUST declare one primary application, one or more affected
  applications, and a reason the change cannot be cleanly split into separate single-app pull requests.
- **FR-030**: A `repo-scope` pull request MUST be used for shared contracts, shared libraries used by
  multiple apps, infrastructure changes affecting multiple apps, or other intentionally cross-cutting
  changes that do not belong to one primary application alone.
- **FR-031**: Pull request review workflows MUST compare the declared pull request scope against actual
  changed paths and registered dependencies and MUST fail, warn, or require reclassification when the
  declaration does not match the detected scope.
- **FR-032**: Pull request review output MUST report the declared scope mode, the primary application when
  one exists, affected applications, and any scope mismatches discovered during validation.
- **FR-033**: Multi-application pull requests MUST be facilitated rather than forbidden, but they MUST
  carry more explicit review metadata and validation than single-app pull requests.
- **FR-034**: v1 MUST define approved shared or repo-scoped path categories that a `single-app` pull
  request may touch without being automatically reclassified as `cross-app`.
- **FR-035**: DevSpark MUST support a `/devspark.add-application` workflow that adds a new application to
  the authoritative root registry, validates uniqueness and path rules, and optionally scaffolds the
  repository-owned app-local `{app.path}/.documentation/` structure when explicitly requested.
- **FR-036**: `/devspark.add-application` MUST update only repository-owned files and MUST NOT add,
  remove, or mutate installed framework content under `.devspark/`.
- **FR-037**: DevSpark MUST support a `/devspark.list-applications` workflow that reads the authoritative
  root registry and displays registered applications, paths, kinds, owners, dependencies, and effective
  documentation roots.
- **FR-038**: v1 MUST limit new multi-app-specific command surface area to `/devspark.add-application`
  and `/devspark.list-applications`; broader application lifecycle commands such as remove, rename, move,
  or split application workflows are explicitly deferred.

### Key Entities *(include if feature involves data)*

- **Application Registry**: Repository-scoped configuration that declares applications, profiles,
  ownership metadata, dependencies, and resolution hints.
- **Application Definition**: A single registered application with an id, path, type, purpose,
  inheritance chain, dependency list, and optional override settings.
- **Profile**: A reusable rule bundle such as `api-profile`, `web-profile`, `admin-profile`, or
  `qa-profile` that captures class-level governance and workflow behavior.
- **Resolution Context**: The explicit execution scope used by DevSpark, including repo scope, app scope,
  selected app id, inherited profiles, and impacted dependencies.
- **Pull Request Scope Declaration**: Explicit metadata that identifies whether a pull request is
  `single-app`, `cross-app`, or `repo-scope`, along with the primary app, affected apps, and validation
  rationale.
- **Application Registration Command**: A workflow that captures required app metadata, validates the
  authoritative registry update, and optionally scaffolds the app-local documentation root.
- **Governance Layer**: A constitution source at repo or app scope that contributes non-negotiable rules.
- **Override Layer**: A prompt, script, or template source that can specialize behavior at app or repo
  scope.
- **Scope Report**: A generated summary that identifies the primary app context, affected downstream
  applications, repo-wide implications, and the resolution chain used.

## Proposed Solution

### Operating Model

DevSpark should treat a repository as a shared control plane with optional application overlays rather
than a single project root.

The recommended authority model is:

- `.documentation/devspark.json` is the authoritative repository registry
- `.devspark/` is the only DevSpark installation payload; `.documentation/` directories are repo-owned
  work product and are never modified by install or upgrade flows
- Repository governance remains authoritative over all applications
- Application governance may extend or strengthen repo governance, but it may not weaken mandatory
  repo-level rules
- v1 does not require app-local manifests; all authoritative app configuration lives in the repo registry
- v1 prefers convention-based paths over repeated per-app path declarations
- v1 uses one repo-level `.documentation/` plus optional application-local `{app.path}/.documentation/`
  directories instead of nesting application state under the repo-level `.documentation/`

The recommended layout is:

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
│   └── .documentation/
│       ├── memory/constitution.md
│       ├── commands/
│       ├── scripts/
│       ├── templates/
│       └── specs/
├── runtime-api-b/
│   └── .documentation/
├── admin-api/
│   └── .documentation/
├── admin-web/
│   └── .documentation/
├── client-web/
│   └── .documentation/
└── qa-harness/
    └── .documentation/
```

In this model:

- the repo root `.documentation/` holds repo-scoped governance, registry, shared overrides, and repo-wide
  specifications
- each application may define its own `{app.path}/.documentation/` folder for app-scoped governance,
  overrides, and specs
- DevSpark resolves and consumes these folders, but it does not install, update, or remove them

### Resolution Model

For an app-scoped workflow, DevSpark resolves assets using these principles:

#### Constitution resolution

1. Load the repository constitution
2. Load the application constitution if it exists
3. Compose the effective governance by adding application-specific rules on top of repo-wide rules
4. Reject the configuration if the application constitution weakens a mandatory repo-wide rule
5. Error if a governance-requiring workflow cannot resolve a repository constitution

#### Prompt, script, and template resolution

Prompt resolution in v1:

1. Application team override from `{app.path}/.documentation/commands/`
2. Repository user override from `.documentation/{git-user}/commands/`
3. Repository team override from `.documentation/commands/`
4. Stock DevSpark default

Script resolution in v1:

1. Application team override from `{app.path}/.documentation/scripts/`
2. Repository team override from `.documentation/scripts/`
3. Stock DevSpark default

Template resolution in v1:

1. Application team override from `{app.path}/.documentation/templates/`
2. Repository team override from `.documentation/templates/`
3. Stock DevSpark default

This ordering keeps v1 simple, preserves the current repo-user customization model where it already
exists, and avoids introducing a new app-user override layer before the base model is proven.

### Scope Selection Rules

DevSpark must use explicit, deterministic scope selection. It must not guess silently.

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

### Direct Dependency Reporting

Dependency-aware scope analysis is a v1 capability, but it is intentionally limited to direct,
declared dependencies to keep the model simple and explicit.

v1 behavior:

- report the primary scope
- report directly impacted downstream applications from the declared dependency graph
- do not attempt inferred code-level dependency discovery
- treat missing dependency declarations as configuration gaps, not inference opportunities

### Repository Registry Schema

The first implementation should standardize on a repository-level manifest at
`.documentation/devspark.json`.

Recommended top-level shape:

```json
{
  "version": 1,
  "mode": "multi-app",
  "profiles": {},
  "apps": []
}
```

Recommended field definitions:

- `version`: integer schema version for future migration and validation
- `mode`: `single-app` or `multi-app`
- `profiles`: reusable inheritance units for application classes and governance bundles
- `apps`: registered application definitions

Standard v1 conventions derive these paths from the registered app path:

- app documentation root: `{app.path}/.documentation/`
- constitution: `{app.path}/.documentation/memory/constitution.md`
- commands: `{app.path}/.documentation/commands/`
- scripts: `{app.path}/.documentation/scripts/`
- templates: `{app.path}/.documentation/templates/`
- specs: `{app.path}/.documentation/specs/`

Recommended application definition shape:

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
  "inherits": ["repo-default", "web-profile", "admin-profile"],
  "dependsOn": ["admin-api"],
  "tags": ["internal", "admin", "react"],
  "platforms": ["web"],
  "overrides": {}
}
```

Recommended validation rules:

- `id` MUST be unique, lowercase, and path-safe
- `path` MUST point to a directory inside the repository
- `inherits` entries MUST resolve to declared profiles
- `dependsOn` entries MUST resolve to declared app ids
- cyclic dependencies MUST be rejected
- `overrides` MAY be omitted, but if present they MUST resolve inside the repository
- governance-requiring workflows MUST always resolve a repository constitution

### Example Repository Registry

The following example covers the heterogeneous application set discussed in review:

```json
{
  "version": 1,
  "mode": "multi-app",
  "profiles": {
    "repo-default": {
      "description": "Mandatory repository-wide governance and workflow defaults"
    },
    "api-profile": {
      "description": "Contract-first API rules, backward compatibility, observability, and performance"
    },
    "admin-profile": {
      "description": "Administrative auditability, authorization rigor, and change traceability"
    },
    "web-profile": {
      "description": "Accessibility, browser support, frontend testing, and UX telemetry"
    },
    "qa-profile": {
      "description": "Environment-safe test execution, fixture isolation, and diagnostic capture"
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
      "inherits": ["repo-default", "api-profile"],
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
      "inherits": ["repo-default", "api-profile", "admin-profile"],
      "dependsOn": ["runtime-api-a", "runtime-api-b"]
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
      "inherits": ["repo-default", "web-profile"],
      "dependsOn": ["runtime-api-a", "runtime-api-b"]
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
      "inherits": ["repo-default", "qa-profile"],
      "dependsOn": ["runtime-api-a", "runtime-api-b", "admin-api"]
    }
  ]
}
```

### Deferred Simplicity Decisions

The following capabilities are intentionally out of scope for v1 to keep the first release simple and
explicit:

- app-local `app.json` manifests
- app-specific user override layers
- inferred dependency discovery from code or build systems
- non-conventional path layouts unless explicitly overridden

### Installation and Ownership Boundary

DevSpark must preserve the existing product boundary:

- `.devspark/` is the installed framework payload and is the only directory DevSpark packages, deploys,
  upgrades, or removes
- `.documentation/` at the repo root and `{app.path}/.documentation/` at the app level are owned by the
  repository, not by the DevSpark installer
- DevSpark may read and validate repo-owned `.documentation/` directories, but install and upgrade flows
  must not add, remove, or rewrite files within them
- quickstarts and docs may describe the expected `.documentation/` layout, but they must not blur the
  ownership boundary by implying those folders are installed content

This keeps installation upgrade-safe while allowing multi-app repositories to organize repo-level and
app-level documentation explicitly.

### App Context Propagation

App context must propagate through the entire workflow chain. A command that targets `admin-web` must
pass that scope to all invoked scripts, all generated artifacts, and all review or planning steps.

The first implementation should prefer explicit scope selection over inference. Inference may be offered
as a convenience only when it is deterministic and reviewable.

For multi-app repositories, scope propagation must distinguish between two documentation levels:

- repo scope uses the repository root `.documentation/`
- app scope uses the selected application's `{app.path}/.documentation/`

DevSpark must never remap app-scoped artifacts into nested folders under the repo root `.documentation/`
when the application has its own documentation root.

### Profile-Based Inheritance

Applications should not be required to duplicate every prompt or script. Instead, the registry should
support reusable profiles, for example:

- `repo-default`
- `api-profile`
- `admin-profile`
- `web-profile`
- `qa-profile`

An application such as `admin-web` could inherit `repo-default`, `web-profile`, and `admin-profile`,
then add only the app-specific deltas that are truly unique.

### Cross-App Dependency Awareness

The registry must declare dependency relationships. That allows DevSpark to:

- Expand review scope when an upstream app or shared contract changes
- Flag downstream verification obligations
- Distinguish local changes from ecosystem changes
- Produce more accurate plans and implementation tasks

### Pull Request Scope Model

DevSpark should treat pull request scope as explicit metadata, not an inferred afterthought.

The default and preferred mode is `single-app`:

- declare one primary application
- validate that changed files stay within that app's registered path plus approved shared paths
- review using repo-wide governance plus the primary app context

When a legitimate feature spans multiple applications, DevSpark should support `cross-app` pull requests:

- declare one primary application
- declare all additional affected applications
- require a short reason that the work cannot be split cleanly into separate single-app pull requests
- review using repo-wide governance plus all declared app contexts and the dependency report

When the work is intentionally cross-cutting, DevSpark should support `repo-scope` pull requests:

- no primary application is required
- use this mode for shared contracts, shared libraries used by multiple apps, infrastructure or platform
  changes affecting multiple apps, or other repo-owned work
- review using repo-wide governance first and list impacted apps when they exist

DevSpark must protect against undeclared multi-app pull requests rather than forbidding valid multi-app
work outright.

v1 should therefore enforce these behaviors:

- a pull request declared as `single-app` must fail validation or require reclassification if changed files
  touch additional registered app paths beyond approved shared categories
- a pull request declared as `cross-app` must name all touched registered app paths that are in scope
- a pull request touching shared contracts or shared libraries used by multiple apps must be `cross-app`
  or `repo-scope`
- review output must always show declared scope, detected scope, mismatches, and downstream app impact

### Multi-App Command Surface

The first multi-app-specific command surface should stay intentionally small.

v1 should introduce only these two commands:

- `/devspark.add-application`
- `/devspark.list-applications`

`/devspark.add-application` should:

- collect required app metadata such as id, name, path, kind, purpose, owner, criticality, inherited
  profiles, and dependencies
- validate duplicate ids, invalid paths, invalid profile references, and invalid dependency references
- update the authoritative root registry at `.documentation/devspark.json`
- optionally scaffold `{app.path}/.documentation/` only when the repository owner explicitly asks for it
- never install or modify `.devspark/`

`/devspark.list-applications` should:

- read the authoritative root registry
- display registered apps in a human-readable form suitable for leadership review and workflow targeting
- show id, path, kind, owner, dependencies, and effective documentation root
- remain read-only

To keep v1 simple, DevSpark should not introduce broader app lifecycle commands yet. Commands such as
remove application, rename application, move application, or split application create policy and migration
complexity that is not required to prove the multi-app operating model.

## Alternatives Considered

### Alternative A - Independent DevSpark installation per application

This was rejected because it duplicates framework files, creates upgrade drift, and makes cross-app
reviews harder rather than easier.

### Alternative B - Single repo-wide DevSpark with no app-specific overrides

This was rejected because it does not reflect the operational and governance differences between runtime
APIs, web applications, admin surfaces, and QA tooling.

### Alternative C - Infer app context only from working directory or branch naming

This was rejected because it is brittle in CI, unclear for root-level workflows, and unsafe for
leadership review or regulated environments.

### Alternative D - Allow app constitutions to fully override repo-wide governance

This was rejected because it destroys the meaning of repo-wide governance and makes compliance
non-deterministic.

## Architecture Risks and Critical Review Notes

### Risk 1 - Customization drift

If every application forks prompts and scripts, DevSpark becomes expensive to upgrade and difficult to
audit. The design therefore depends on inheritance and delta-based overrides.

### Risk 2 - False confidence through implicit scope

If DevSpark guesses the application instead of making scope explicit, leadership will not be able to
trust the resulting plans or reviews. Explicit scope must be visible in output.

### Risk 3 - Governance fragmentation

If app-level constitutions can contradict repo-wide mandatory rules, teams will create local exceptions
that are hard to detect. Repo-wide rules must remain authoritative.

### Risk 4 - Under-modeling dependencies

A multi-app monorepo is not just a directory tree. Without dependency modeling, DevSpark will treat
shared changes as local changes and miss downstream risk.

### Risk 5 - Partial implementation that only updates docs

This feature is not real unless prompt templates, helper scripts, packaging, quickstarts, and CLI
install or update paths all become app-aware.

### Risk 6 - Breaking the installation ownership boundary

If multi-app support causes DevSpark to start creating or mutating repo-owned `.documentation/` folders,
the product breaks its upgrade-safety promise and risks overwriting application-owned material.

### Risk 7 - Undeclared multi-app pull requests

If a pull request claims to target one app but changes multiple registered app paths, reviewers will get a
false sense of locality and miss downstream impact. Pull request scope must therefore be declared and
validated against changed paths.

### Risk 8 - Command surface explosion

If multi-app support ships with too many app lifecycle commands in the first release, DevSpark will add a
lot of policy surface before the underlying registry and scope model are proven. The first release should
stay limited to add and list operations.

## Proposed Phasing

### Phase 1 - Architecture and config foundations

- Define the multi-app on-disk layout
- Lock the ownership boundary: `.devspark/` is installed content, `.documentation/` is repo-owned content
- Define the app registry schema
- Define the `/devspark.add-application` and `/devspark.list-applications` command contracts
- Define resolution order and scope rules
- Define constitution composition semantics
- Add direct downstream dependency reporting from declared dependencies
- Preserve full backward compatibility for single-app repositories

### Phase 2 - Workflow and script propagation

- Make helper scripts app-aware
- Make prompt templates app-aware
- Make specs, plans, and tasks app-scoped when required
- Add pull request scope declaration and validation behavior for single-app, cross-app, and repo-scope
- Add scope reporting and validation

### Phase 3 - Packaging, quickstarts, and CLI support

- Update release packaging and generated shims
- Ensure install and upgrade flows only deploy `.devspark/` and never mutate repo-owned `.documentation/`
- Update quickstarts and installation guidance
- Update CLI install and validation behavior
- Ship only the limited multi-app command set: `/devspark.add-application` and `/devspark.list-applications`

### Phase 4 - Hardening and migration guidance

- Add migration guidance for existing monorepos
- Add examples for mixed-platform repositories
- Add optional future enhancements that were intentionally deferred from v1

## Operational Constraints

- The default single-application behavior must remain unchanged.
- DevSpark installation and upgrade operations must only manage `.devspark/` and agent shims.
- Repo-level `.documentation/` and app-level `{app.path}/.documentation/` folders are repository-owned.
- Application selection must be explicit for ambiguous contexts.
- Single-app pull requests are the default path, but legitimate cross-app pull requests must remain
  supported through explicit declaration and stricter validation.
- The first multi-app command set must remain limited to add and list application workflows.
- Multi-app support must work across Bash and PowerShell script variants.
- The design must tolerate applications that define only some local override layers.
- Repo-wide workflows such as release or constitution evolution must continue to function.

## Open Questions for Leadership Review

- Is the v1 simplicity boundary acceptable: authoritative repo registry, conventional paths,
  no app-local manifests, and no app-user overrides?
- Is direct downstream dependency reporting sufficient for v1, with inferred dependency analysis deferred?
- Should shared libraries be modeled as applications, components, or dependencies-only assets?
- What is the minimum acceptable CLI support for the first release?
- What set of shared or repo-scoped paths should remain valid inside `single-app` pull requests before
  reclassification becomes mandatory?
- Is optional scaffolding of `{app.path}/.documentation/` during `/devspark.add-application` acceptable,
  or should the command remain registry-only in the first release?

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A repository with at least five heterogeneous applications can configure DevSpark so that
  each app resolves the correct governance and override layers during planning and review workflows.
- **SC-002**: Existing single-application repositories require no directory restructure and show no
  behavior regression in core DevSpark workflows.
- **SC-003**: For a declared cross-app dependency change, DevSpark identifies the primary scope and at
  least the directly impacted downstream applications in the generated scope report.
- **SC-004**: A pull request declared as `single-app` is automatically flagged when its changed files touch
  additional registered app paths outside approved shared categories.
- **SC-005**: Technical leadership can review one written specification and determine the proposed
  operating model, migration strategy, risks, and unresolved questions without requiring source-code
  archaeology.
- **SC-006**: The packaged DevSpark installation, quickstart flow, and documented layout all support the
  same multi-app model.
- **SC-007**: `/devspark.add-application` can add a valid application to the root registry and optionally
  scaffold the app-local documentation root without modifying `.devspark/`.
- **SC-008**: `/devspark.list-applications` can render the registered application set with enough detail to
  support scope selection and leadership review.

## Recommended Leadership Decision

Approve the multi-app strategy only if it is implemented as an explicit, app-aware operating model with
profile-based inheritance and dependency-aware scoping. Reject any implementation that only adds new
folders or documentation while leaving prompt resolution, script resolution, and governance loading tied
to the current single-app assumptions.
