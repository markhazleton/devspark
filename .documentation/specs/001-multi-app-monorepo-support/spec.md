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
- Broader app lifecycle commands such as remove, rename, move, or split (deferred beyond v1)

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Govern a heterogeneous multi-app repository (Priority: P1)

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

### User Story 2 — Execute app-scoped workflows with explicit context (Priority: P1)

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

### User Story 3 — Review cross-application changes safely (Priority: P1)

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
   `admin-api`, **Then** DevSpark fails validation or requires reclassification as cross-app or
   repo-scope.
5. **Given** a pull request declared as cross-app with primary app `admin-web` and affected app
   `admin-api`, **When** the changed files touch both app paths, **Then** DevSpark reviews the pull
   request using repo-wide governance plus the declared app scopes and emits the combined scope report.

---

### User Story 4 — Keep single-application repositories unchanged (Priority: P2)

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

### User Story 5 — Limit customization drift through profile-based inheritance (Priority: P2)

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

---

### User Story 6 — Add a new application to the registry (Priority: P2)

As an engineer adding a new service to the monorepo, I need a guided workflow that registers the
application in the authoritative registry so that DevSpark immediately recognizes the new app without
manual JSON editing.

**Why this priority**: Manual registry editing is error-prone. A validated command reduces onboarding
friction for new applications and enforces uniqueness and path rules from the start.

**Independent Test**: Run `/devspark.add-application` with valid metadata for a new `payments-api`,
then verify the registry is updated and a subsequent `/devspark.list-applications` includes the new entry.

**Acceptance Scenarios**:

1. **Given** a multi-app repository, **When** a user runs `/devspark.add-application` with id
   `payments-api`, a valid path, kind, owner, and profile references, **Then** the registry at
   `.documentation/devspark.json` is updated with the new entry and passes validation.
2. **Given** a multi-app repository where `admin-api` already exists, **When** a user runs
   `/devspark.add-application` with id `admin-api`, **Then** the command fails with a duplicate-id error
   and does not modify the registry.
3. **Given** a valid add-application invocation with the `--scaffold` flag, **When** the command
   completes, **Then** `{app.path}/.documentation/` is created with standard subdirectories, but
   `.devspark/` is not modified.
4. **Given** a valid add-application invocation without `--scaffold`, **When** the command completes,
   **Then** only the registry file is updated; no directories are created.

---

### User Story 7 — List registered applications (Priority: P2)

As a technical lead or reviewer, I need to see all registered applications, their paths, kinds, owners,
and dependencies at a glance so that I can select the correct scope for DevSpark workflows.

**Why this priority**: Without a quick reference, engineers guess app identifiers or skip app context
entirely, which defeats multi-app governance.

**Independent Test**: Run `/devspark.list-applications` on the example six-app registry and verify the
output includes all six entries with correct metadata in a readable format.

**Acceptance Scenarios**:

1. **Given** a multi-app repository with six registered applications, **When** a user runs
   `/devspark.list-applications`, **Then** the output displays each app's id, path, kind, owner,
   criticality, inherited profiles, dependencies, and effective documentation root.
2. **Given** a single-app repository with no registry, **When** a user runs
   `/devspark.list-applications`, **Then** the output states no multi-app registry is configured and
   the repository operates in single-app mode.
3. **Given** a multi-app repository, **When** `/devspark.list-applications` runs, **Then** no files are
   modified or created.

---

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
- A registry entry references a profile that does not exist.
- A registry entry creates a cyclic dependency chain.
- An app inherits two profiles that declare conflicting values for the same setting.

## Requirements *(mandatory)*

### Requirement Group A — Backward Compatibility

- **FR-A1**: DevSpark MUST preserve current single-application behavior for repositories that do not
  define a multi-app registry; no directory restructure or configuration change may be required.
- **FR-A2**: DevSpark MUST support repo-scoped workflows that intentionally operate without an app
  context, even in multi-app repositories.

### Requirement Group B — Registry and App Identity

- **FR-B1**: DevSpark MUST support an explicit repository-level application registry at
  `.documentation/devspark.json` that defines each application's identifier, path, type, purpose,
  dependency relationships, and inheritance profile.
- **FR-B2**: Application identifiers MUST be unique, lowercase, and path-safe; paths MUST point to
  existing directories; profile and dependency references MUST resolve to declared entries.
- **FR-B3**: DevSpark MUST validate the registry on load and fail fast for duplicate ids, invalid paths,
  unresolved profile or dependency references, and cyclic dependencies.
- **FR-B4**: Shared libraries that are not independently deployable MUST be modeled as registry entries
  with `kind: "library"` and `deployable: false`. They participate in dependency tracking but are not
  valid targets for app-scoped deployment or release workflows.
- **FR-B5**: DevSpark MUST support `/devspark.add-application` to add a validated entry to the registry
  and optionally scaffold `{app.path}/.documentation/` when explicitly requested; the command MUST NOT
  modify `.devspark/`.
- **FR-B6**: DevSpark MUST support `/devspark.list-applications` as a read-only command that renders
  registered applications with id, path, kind, owner, dependencies, and effective documentation root.
- **FR-B7**: v1 MUST limit multi-app command surface to `/devspark.add-application` and
  `/devspark.list-applications`; broader lifecycle commands are deferred.

### Requirement Group C — Resolution Model

- **FR-C1**: DevSpark MUST support a repository-wide constitution, prompts, scripts, and templates as the
  default shared layer.
- **FR-C2**: DevSpark MUST support optional application-specific constitutions, prompts, scripts,
  templates, and specification directories at `{app.path}/.documentation/`.
- **FR-C3**: Constitution resolution MUST load the repository constitution first, then apply an
  application constitution as an additive overlay; the application constitution MUST NOT weaken mandatory
  repo-wide rules (see "Constitution Weakening Detection" below).
- **FR-C4**: Prompt resolution MUST follow this order: app team override → repository user override →
  repository team override → stock DevSpark default.
- **FR-C5**: Script resolution MUST follow this order: app team override → repository team override →
  stock DevSpark default.
- **FR-C6**: Template resolution MUST follow this order: app team override → repository team override →
  stock DevSpark default.
- **FR-C7**: App-scoped artifacts (specs, plans, tasks) MUST be stored under the owning application's
  `{app.path}/.documentation/specs/` rather than the shared repo-level specification directory.
- **FR-C8**: DevSpark MUST make the resolved scope visible in workflow output so users can see whether
  a command executed in repo scope, single-app scope, or multi-app scope.

### Requirement Group D — Scope and PR Governance

- **FR-D1**: DevSpark MUST require explicit app context for app-scoped workflows through a declared
  parameter; it MUST NOT rely solely on implicit inference.
- **FR-D2**: DevSpark MUST support explicit pull request scope declaration with three modes:
  `single-app`, `cross-app`, and `repo-scope`.
- **FR-D3**: A `single-app` PR MUST declare one primary application and MUST validate that changed files
  touch only that app's path plus approved shared paths (see "Approved Shared Path Categories" below).
- **FR-D4**: A `cross-app` PR MUST declare a primary application, all affected applications, and a reason
  the change cannot be split into single-app PRs.
- **FR-D5**: A `repo-scope` PR MUST be used for shared contracts, shared libraries consumed by multiple
  apps, and infrastructure changes affecting multiple apps.
- **FR-D6**: PR review workflows MUST compare declared scope against changed paths and dependency data
  and MUST fail or require reclassification when the declaration does not match detected scope.
- **FR-D7**: DevSpark MUST support dependency-aware scope analysis using declared `dependsOn` entries to
  report directly impacted downstream applications for shared changes.

### Requirement Group E — Profiles and Inheritance

- **FR-E1**: DevSpark MUST support reusable inheritance profiles so application classes can share rule
  sets without duplicating all prompts and scripts.
- **FR-E2**: Profile composition MUST follow the order declared in an application's `inherits` array,
  applying later profiles on top of earlier ones, with app-specific overrides applied last (see "Profile
  Composition Model" below).
- **FR-E3**: DevSpark MUST prevent application-specific governance from silently weakening mandatory
  repository-wide governance.

### Requirement Group F — Ownership Boundary

- **FR-F1**: DevSpark packaging, installation, and upgrade flows MUST deploy and update only `.devspark/`
  and agent shim files; they MUST NOT add, remove, or modify files under any `.documentation/` directory.
- **FR-F2**: DevSpark MUST define a documented on-disk layout for multi-app repositories using the
  two-level documentation model: repo-level `.documentation/` plus optional `{app.path}/.documentation/`.
- **FR-F3**: DevSpark MUST update packaged templates, quickstart guidance, and CLI behavior so the
  multi-app capability is installable and discoverable.

### Constitution Weakening Detection

v1 uses a keyword-based detection model rather than requiring structured constitution formats:

1. The repository constitution is parsed for lines containing `NON-NEGOTIABLE`, `MUST`, or `MANDATORY`
   markers. These are extracted as the mandatory rule set.
2. If an application constitution contains a line that explicitly contradicts, relaxes, or removes a
   mandatory rule (detected via negation patterns such as "not required", "optional", "may skip",
   or "does not apply"), validation emits a **CONFLICT** warning.
3. In v1, detected conflicts produce a warning in validation output and scope reports. They do not
   silently pass, but they also do not hard-block workflows — the assumption is that leadership
   reviews and resolves conflicts.
4. v2 may introduce structured YAML rules for machine-enforceable validation.

### Approved Shared Path Categories

The following path categories are approved for `single-app` pull requests without automatic
reclassification to `cross-app`:

| Category | Path Pattern | Rationale |
|----------|-------------|-----------|
| Repository documentation root | `.documentation/` (root-level only, not app-local) | Shared guides, memory, and governance |
| GitHub configuration | `.github/` | Workflows, templates, issue forms |
| DevSpark framework | `.devspark/` | Installed framework content |
| Root configuration files | `*.md`, `*.json`, `*.yaml`, `*.toml`, `*.cfg` at repo root only | README, LICENSE, pyproject.toml, etc. |
| CI/CD configuration | `.gitlab-ci.yml`, `Jenkinsfile`, `azure-pipelines.yml` at repo root | Pipeline definitions |

Files outside these categories that belong to a different registered application's path trigger scope
mismatch validation.

### Profile Composition Model

Profiles carry three types of content in v1:

1. **Tags**: key-value metadata merged across the inheritance chain (last writer wins per key)
2. **Rules**: governance statements added to the effective context (additive, never removed by override)
3. **Hints**: non-binding suggestions for workflows (e.g., preferred test runner, default review depth)

Composition order for an application with `"inherits": ["repo-default", "api-profile", "admin-profile"]`:

1. Start with `repo-default` profile as the base
2. Merge `api-profile` on top: tags overwrite, rules accumulate, hints overwrite
3. Merge `admin-profile` on top: same merge behavior
4. Apply app-specific overrides from the application's `overrides` field: same merge behavior

Conflict resolution:

- **Tags**: last-writer-wins within the inheritance chain; app override is always last
- **Rules**: purely additive; no profile or app override may remove a rule contributed by an earlier
  layer; rules contributed by the repo constitution (mandatory rules) are immutable across all layers
- **Hints**: last-writer-wins; these are non-binding and do not require conflict detection

Profile definitions are stored in the `profiles` section of `.documentation/devspark.json`. Each profile
contains optional `tags`, `rules`, and `hints` objects.

### Key Entities

- **Application Registry**: Repository-scoped configuration in `.documentation/devspark.json` that
  declares applications, profiles, ownership metadata, and dependencies.
- **Application Definition**: A registered application with id, path, kind, purpose, inheritance chain,
  dependency list, and optional override settings.
- **Profile**: A reusable rule bundle (e.g., `api-profile`, `web-profile`) containing tags, rules,
  and hints that apply to a class of applications.
- **Resolution Context**: The execution scope used by DevSpark: repo scope or app scope, selected app id,
  inherited profiles, and impacted dependencies.
- **Pull Request Scope Declaration**: Metadata identifying whether a PR is `single-app`, `cross-app`, or
  `repo-scope`, with primary app, affected apps, and validation rationale.
- **Shared Library**: A registry entry with `kind: "library"` and `deployable: false` that participates
  in dependency tracking but is not a valid target for deployment workflows.

## Non-Functional Requirements

- **NFR-001**: Registry validation and resolution MUST complete in under 500ms for repositories with up
  to 20 registered applications.
- **NFR-002**: v1 MUST be tested with fixture registries of up to 20 applications; no hard upper limit
  is enforced, but performance beyond 20 apps is not guaranteed.
- **NFR-003**: Resolution overhead MUST remain negligible relative to current single-app command startup
  time (target: less than 100ms added latency).
- **NFR-004**: The `devspark.json` registry schema MUST include a `version` integer to support future
  schema migrations without breaking existing registries.

## Alternatives Considered

### Alternative A — Independent DevSpark installation per application

Rejected: duplicates framework files, creates upgrade drift, and makes cross-app reviews harder.

### Alternative B — Single repo-wide DevSpark with no app-specific overrides

Rejected: does not reflect operational and governance differences between runtime APIs, web applications,
admin surfaces, and QA tooling.

### Alternative C — Infer app context only from working directory or branch naming

Rejected: brittle in CI, unclear for root-level workflows, unsafe for leadership review.

### Alternative D — Allow app constitutions to fully override repo-wide governance

Rejected: destroys the meaning of repo-wide governance and makes compliance non-deterministic.

## Architecture Risks

### Risk 1 — Customization drift

If every application forks prompts and scripts, DevSpark becomes expensive to upgrade. Mitigated by
profile inheritance and delta-based overrides.

### Risk 2 — False confidence through implicit scope

If DevSpark guesses the application, leadership cannot trust plans or reviews. Mitigated by requiring
explicit scope visible in output.

### Risk 3 — Governance fragmentation

If app constitutions can contradict repo-wide mandatory rules, teams create undetectable exceptions.
Mitigated by keyword-based conflict detection in v1, structured rules in v2.

### Risk 4 — Under-modeling dependencies

Without dependency modeling, shared changes are treated as local. Mitigated by declared `dependsOn`
entries and direct downstream reporting.

### Risk 5 — Partial implementation that only updates docs

Feature is not real unless prompts, scripts, packaging, quickstarts, and CLI all become app-aware.
Mitigated by phased delivery with hard gates (v1a/v1b split in the plan).

### Risk 6 — Breaking the installation ownership boundary

If multi-app support causes DevSpark to mutate repo-owned `.documentation/`, upgrade safety breaks.
Mitigated by constitution principle III (Ownership Boundary) and regression tests.

### Risk 7 — Undeclared multi-app pull requests

A PR claiming single-app scope but changing multiple app paths gives false locality. Mitigated by
mandatory scope validation against changed paths.

### Risk 8 — Stale dependency declarations

Teams fail to maintain `dependsOn` entries. Mitigated by treating missing declarations as config gaps
surfaced in scope reports. A dependency audit command is deferred to v2.

## Open Questions for Leadership Review

- Is the v1 simplicity boundary acceptable: authoritative repo registry, conventional paths,
  no app-local manifests, and no app-user overrides?
- Is direct downstream dependency reporting sufficient for v1, with inferred dependency analysis deferred?
- What is the minimum acceptable CLI support for the first release?
- What specific shared path categories should be added to or removed from the approved list?
- Is optional scaffolding of `{app.path}/.documentation/` during `/devspark.add-application` acceptable,
  or should the command remain registry-only in the first release?

## Operational Constraints

- The default single-application behavior must remain unchanged.
- DevSpark installation and upgrade operations must only manage `.devspark/` and agent shims.
- Repo-level `.documentation/` and app-level `{app.path}/.documentation/` are repository-owned.
- Application selection must be explicit for ambiguous contexts.
- Single-app PRs are the default; cross-app PRs are supported through explicit declaration.
- The first multi-app command set is limited to add and list application workflows.
- Multi-app support must work across Bash and PowerShell script variants.
- Repo-wide workflows such as release or constitution evolution must continue to function.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Given the six-app fixture registry (runtime-api-a, runtime-api-b, admin-api, admin-web,
  client-web, qa-harness), running `/devspark.plan` with `--app runtime-api-a` produces a plan artifact
  at `apps/runtime-api-a/.documentation/specs/` and the scope report output contains
  `scope: single-app` and `app: runtime-api-a`.
- **SC-002**: Given the same fixture, running `/devspark.plan` with `--app admin-web` does NOT include
  any content from `runtime-api-a`'s constitution or overrides in the resolved context.
- **SC-003**: Given a single-app fixture repository with no `devspark.json`, all existing DevSpark
  commands produce identical output and artifact locations compared to the pre-feature baseline.
- **SC-004**: Given a fixture registry where `admin-web` depends on `admin-api`, running a repo-scope
  workflow for a shared contract change produces a scope report listing both `admin-api` and `admin-web`
  in the impacted applications section.
- **SC-005**: Given a PR declared as `single-app` for `admin-web` where changed files include a file
  under `apps/admin-api/`, the PR review workflow emits a scope mismatch warning naming `admin-api`.
- **SC-006**: Running `/devspark.add-application` with id `payments-api`, path `apps/payments-api`,
  kind `runtime-api`, and valid profile references adds exactly one entry to `devspark.json` and the
  file passes schema validation. Running it again with the same id fails with a duplicate error.
- **SC-007**: Running `/devspark.list-applications` on the six-app fixture produces a table with six
  rows, each showing id, path, kind, owner, and dependencies. No files are modified.
- **SC-008**: The quickstart documents, CLI `--help` output, and packaged template README all reference
  the multi-app capability with consistent terminology matching the spec.

## Recommended Leadership Decision

Approve the multi-app strategy only if it is implemented as an explicit, app-aware operating model with
profile-based inheritance and dependency-aware scoping. Reject any implementation that only adds new
folders or documentation while leaving prompt resolution, script resolution, and governance loading tied
to the current single-app assumptions.
