# Multi-Application Monorepo Support

<video controls width="100%">
  <source src="https://github.com/markhazleton/devspark/releases/download/v0.1.1/DevSpark__Taming_the_Monorepo.mp4" type="video/mp4">
  Your browser does not support the video tag.
</video>

DevSpark's multi-app monorepo support lets you manage multiple applications in a single repository with per-app governance, scoped workflows, and dependency-aware reviews — while keeping full backward compatibility with single-app repositories.

---

## What Is a Monorepo?

A **monorepo** (monolithic repository) is a software development strategy where multiple applications, services, and libraries live in a single version-controlled repository. Instead of one repository per deployable unit, a team maintains one repository that contains all related codebases.

A typical monorepo might contain:

- Two runtime APIs serving production traffic
- An admin API for internal operations
- A React-based admin dashboard
- A client-facing web application
- An internal QA tool
- Shared libraries consumed by multiple services

### Why Teams Use Monorepos

| Benefit | Description |
|---------|-------------|
| **Atomic changes** | A single commit can update an API contract and all its consumers at once |
| **Unified history** | One `git log` shows the full picture of how the system evolved |
| **Shared tooling** | CI pipelines, linters, and dependency management are configured once |
| **Easier refactoring** | Cross-cutting changes don't require coordinating across multiple repositories |
| **Simplified onboarding** | New team members clone one repository instead of tracking down many |

### The Challenges

Monorepos introduce governance and workflow problems that don't exist in single-app repositories:

| Challenge | Impact |
|-----------|--------|
| **Mixed governance** | A client-facing React app and an internal QA tool have different security, testing, and review requirements — but live side by side |
| **Scope ambiguity** | When a PR touches multiple directories, it's unclear which applications are affected and which review rules apply |
| **Dependency risk** | Changes to shared contracts or libraries can break downstream consumers without the author realizing it |
| **Context overload** | AI coding assistants treat the entire repository as one unit, producing plans and reviews that conflate unrelated applications |
| **Configuration drift** | Per-app customizations multiply into an unmanageable patchwork of overrides |

---

## How DevSpark Addresses Monorepo Challenges

DevSpark's approach is built on three principles: **explicit scope**, **layered governance**, and **dependency awareness** — all without requiring changes to repositories that don't need multi-app support.

### Explicit Application Registry

Every monorepo declares its applications in a single authoritative file: `.documentation/devspark.json`.

```json
{
  "version": 1,
  "mode": "multi-app",
  "profiles": {
    "api-profile": {
      "description": "Shared rules for all API services",
      "rules": ["100% integration test coverage", "OpenAPI spec required"]
    },
    "web-profile": {
      "description": "Shared rules for web applications",
      "rules": ["Lighthouse score ≥ 90", "WCAG 2.1 AA compliance"]
    }
  },
  "apps": [
    {
      "id": "runtime-api-a",
      "path": "apps/runtime-api-a",
      "kind": "api",
      "purpose": "Primary customer-facing API",
      "owner": "platform-team",
      "criticality": "critical",
      "inherits": ["api-profile"],
      "dependsOn": []
    },
    {
      "id": "admin-web",
      "path": "apps/admin-web",
      "kind": "web",
      "purpose": "Internal administration dashboard",
      "owner": "admin-team",
      "criticality": "medium",
      "inherits": ["web-profile"],
      "dependsOn": ["admin-api"]
    },
    {
      "id": "admin-api",
      "path": "apps/admin-api",
      "kind": "api",
      "purpose": "Backend for admin dashboard",
      "owner": "admin-team",
      "criticality": "medium",
      "inherits": ["api-profile"],
      "dependsOn": []
    }
  ]
}
```

This registry is the single source of truth. Application identifiers must be unique, lowercase, and path-safe. Paths must point to existing directories. Profile and dependency references must resolve to declared entries. DevSpark validates all of this on load and fails fast on errors.

### Layered Governance — Not Fragmented Governance

DevSpark does not create isolated installations per application. Instead, it uses a layered resolution model:

```text
┌─────────────────────────────────────────────┐
│  Repository-Wide Governance (mandatory)     │
│  .documentation/memory/constitution.md      │
│  .documentation/commands/                   │
│  .documentation/scripts/                    │
├─────────────────────────────────────────────┤
│  Profile Rules (shared by app class)        │
│  api-profile, web-profile, qa-profile       │
├─────────────────────────────────────────────┤
│  App-Specific Overlays (additive only)      │
│  {app.path}/.documentation/                 │
│  {app.path}/app.json (optional overrides)   │
└─────────────────────────────────────────────┘
```

**Key rule**: App-level governance can **strengthen or extend** repository-wide rules but can never **weaken** mandatory repo-wide rules. If a repository constitution requires signed commits and 80% test coverage, no individual application can opt out.

#### Resolution Order

When DevSpark resolves prompts, scripts, templates, and constitutions for an app-scoped workflow, it follows a defined priority chain:

| Asset | Resolution Order (highest priority first) |
|-------|-------------------------------------------|
| **Constitution** | Repo constitution → Profile rules → App overlay (additive) |
| **Prompts** | App team override → Repo user override → Repo team override → Stock default |
| **Scripts** | App team override → Repo team override → Stock default |
| **Templates** | App team override → Repo team override → Stock default |
| **Specs/Plans/Tasks** | Stored under `{app.path}/.documentation/specs/` for app-scoped workflows |

This means a team of six applications doesn't need six copies of every prompt. Most applications inherit shared defaults and profiles, adding only the specific overrides they need.

### Profiles — Reusable Rule Bundles

Profiles prevent configuration drift by grouping rules that apply to a class of applications. Instead of duplicating rules across every API service, you define an `api-profile` once and let each API inherit it:

```json
"profiles": {
  "api-profile": {
    "description": "Shared API service rules",
    "rules": [
      "All endpoints must have OpenAPI documentation",
      "Integration tests required for every public endpoint",
      "Health check endpoint required at /health"
    ],
    "hints": {
      "testing-framework": "pytest",
      "documentation-format": "OpenAPI 3.1"
    }
  }
}
```

An application's `inherits` array specifies which profiles apply. Later profiles override earlier ones, and app-specific overrides are applied last.

#### Profile Composition in Detail

Profiles carry three types of content:

| Content Type | Merge Behavior | Example |
|-------------|----------------|--------|
| **Tags** | Last-writer-wins per key | `{ "testing-framework": "pytest" }` |
| **Rules** | Additive — rules accumulate and are never removed | `"Health check endpoint required"` |
| **Hints** | Last-writer-wins (non-binding suggestions) | `{ "review-depth": "thorough" }` |

For an application with `"inherits": ["repo-default", "api-profile", "admin-profile"]`:

1. Start with `repo-default` as the base
2. Merge `api-profile` on top — tags overwrite, rules accumulate, hints overwrite
3. Merge `admin-profile` on top — same merge behavior
4. Apply app-specific overrides from the application's `overrides` field — same merge behavior

Rules contributed by the repository constitution (mandatory rules) are immutable across all layers. No profile or app override can remove them.

### Dependency-Aware Scope Analysis

DevSpark uses declared `dependsOn` relationships to detect when a change to one application may affect others. If `admin-web` depends on `admin-api`, a change to `admin-api`'s public contracts triggers a scope report that includes `admin-web` as a downstream consumer.

DevSpark also supports basic dependency inference by scanning import statements and build configuration files (`package.json`, `pyproject.toml`, `.csproj` project references) for references to other registered application paths. Inferred dependencies are reported separately from declared dependencies and clearly labeled as "inferred."

### PR Scope Governance

Pull requests in monorepos require explicit scope declarations. DevSpark supports three modes:

| PR Scope | When to Use | Validation |
|----------|-------------|------------|
| **single-app** | Change touches one application only | Changed files must be within that app's path plus approved shared paths |
| **cross-app** | Change intentionally spans multiple applications | Must declare primary app, all affected apps, and a reason it can't be split |
| **repo-scope** | Shared contracts, libraries, or infrastructure affecting multiple apps | Used for changes that don't belong to any single application |

DevSpark compares the declared scope against the actual changed files and dependency graph. If a PR is declared as `single-app` for `admin-web` but its changed files also touch `admin-api`, DevSpark flags the mismatch and requires reclassification.

#### Approved Shared Paths for Single-App PRs

The following paths are allowed in `single-app` PRs without triggering automatic reclassification to `cross-app`:

| Category | Path Pattern |
|----------|--------------|
| Repository documentation root | `.documentation/` (root-level only, not app-local) |
| GitHub configuration | `.github/` |
| DevSpark framework | `.devspark/` |
| Root configuration files | `*.md`, `*.json`, `*.yaml`, `*.toml`, `*.cfg` at repo root only |
| CI/CD configuration | `.gitlab-ci.yml`, `Jenkinsfile`, `azure-pipelines.yml` at repo root |

Files outside these categories that belong to a different registered application's path trigger scope mismatch validation.

---

## Commands for Monorepo Management

DevSpark provides three dedicated commands for managing applications in a monorepo. These commands are optional — single-app repositories never need them.

### `/devspark.add-application`

Registers a new application in the repository registry through a guided workflow. Collects the application's identifier, path, kind, owner, criticality, profile inheritance, and dependencies. Validates all inputs against the registry and scaffolds the application's `.documentation/` directory with standard subdirectories.

```text
/devspark.add-application Add payments-api as a new critical API service owned by platform-team
```

### `/devspark.list-applications`

Displays all registered applications with their metadata: id, path, kind, owner, criticality, inherited profiles, dependencies, and effective documentation root. Read-only — does not modify any files.

```text
/devspark.list-applications
```

### `/devspark.validate-registry`

Validates the registry schema, reference resolution, cycle detection, path existence, and app-local manifest consistency. Produces structured validation output identifying any errors or warnings.

```text
/devspark.validate-registry
```

---

## On-Disk Layout

A multi-app repository using DevSpark follows this structure:

```text
repo-root/
├── .documentation/                  # Repository-wide governance
│   ├── memory/
│   │   └── constitution.md          # Repo-wide constitution (mandatory)
│   ├── commands/                    # Shared command overrides
│   ├── scripts/                     # Shared script overrides
│   ├── devspark.json                # Application registry
│   └── specs/                       # Repo-scoped specifications
├── .devspark/                       # DevSpark framework (don't edit)
├── apps/
│   ├── runtime-api-a/
│   │   ├── .documentation/          # App-specific governance
│   │   │   ├── memory/
│   │   │   │   └── constitution.md  # App constitution overlay
│   │   │   ├── commands/            # App-specific command overrides
│   │   │   └── specs/               # App-scoped specifications
│   │   ├── app.json                 # Optional local overrides (tags, hints, rules)
│   │   └── src/                     # Application source code
│   ├── admin-web/
│   │   ├── .documentation/
│   │   └── src/
│   └── admin-api/
│       ├── .documentation/
│       └── src/
└── libs/                            # Shared libraries (kind: "library", deployable: false)
    └── shared-auth/
```

### Key Boundaries

- **`.devspark/`** contains only framework files. DevSpark installation and upgrade flows never touch `.documentation/`.
- **`.documentation/`** at the repo root contains shared governance that applies to all applications.
- **`{app.path}/.documentation/`** contains app-specific overlays that extend (never weaken) repo-wide governance.
- **`{app.path}/app.json`** is an optional local manifest for app-specific tags, hints, and rules. Identity fields (id, path, kind, owner) are ignored here — the registry is authoritative.

---

## Constitution Weakening Detection

A core guarantee of DevSpark's monorepo model is that app-level governance can never silently weaken mandatory repository-wide rules. The MVP uses a keyword-based detection model:

1. The repository constitution is parsed for lines containing `NON-NEGOTIABLE`, `MUST`, or `MANDATORY` markers — these form the mandatory rule set
2. If an application constitution contains a line that explicitly contradicts, relaxes, or removes a mandatory rule (detected via negation patterns such as "not required", "optional", "may skip", or "does not apply"), validation emits a **CONFLICT** warning
3. Detected conflicts appear in validation output and scope reports — they do not silently pass, but they also do not hard-block workflows in v1
4. A future version may introduce structured YAML rules for machine-enforceable validation

---

## Backward Compatibility

Multi-app support is entirely **opt-in**. Repositories without a `devspark.json` registry continue to work exactly as they do today:

- No directory restructure required
- No configuration changes needed
- All existing workflows behave identically
- The multi-app commands (`add-application`, `list-applications`, `validate-registry`) gracefully report that no registry is configured

A repository enters multi-app mode only when `.documentation/devspark.json` is created — either manually or through `/devspark.add-application`.

---

## Shared Libraries

Not every entry in the registry is a deployable service. Shared libraries — authentication modules, API contracts, utility packages — are modeled as registry entries with `kind: "library"` and `deployable: false`. They participate in dependency tracking so DevSpark can identify downstream consumers when shared code changes, but they are not valid targets for app-scoped deployment or release workflows.

---

## What's in the MVP

The initial release (v1) provides the foundation for monorepo support:

| Capability | Status |
|------------|--------|
| Application registry (`devspark.json`) | Included |
| Registry validation (schema, references, cycles, paths) | Included |
| Profile inheritance and composition | Included |
| App-local manifest (`app.json`) overrides | Included |
| Scope resolution (repo, single-app, cross-app) | Included |
| Dependency-aware scope analysis (declared + inferred) | Included |
| PR scope validation (single-app, cross-app, repo-scope) | Included |
| `/devspark.add-application` command | Included |
| `/devspark.list-applications` command | Included |
| `/devspark.validate-registry` command | Included |
| Scope report generation | Included |
| App lifecycle commands (remove, rename, move, split) | Deferred |
| Shared package release orchestration | Deferred |

---

## Design Decisions

Several alternative approaches were evaluated during the design of monorepo support. Understanding why they were rejected helps explain the current design:

| Alternative | Why It Was Rejected |
|------------|--------------------|
| **Independent DevSpark installation per application** | Duplicates framework files, creates upgrade drift, and makes cross-app reviews harder |
| **Single repo-wide DevSpark with no app-specific overrides** | Doesn't reflect operational and governance differences between runtime APIs, web applications, admin surfaces, and QA tooling |
| **Infer app context only from working directory or branch naming** | Brittle in CI, unclear for root-level workflows, unsafe for leadership review |
| **Allow app constitutions to fully override repo-wide governance** | Destroys the meaning of repo-wide governance and makes compliance non-deterministic |

---

## Getting Started

1. **Run `/devspark.add-application`** to register your first application. This creates the registry file and scaffolds the app's documentation directory.
2. **Repeat** for each additional application in the repository.
3. **Run `/devspark.validate-registry`** to confirm the registry is consistent.
4. **Run `/devspark.list-applications`** to see the full registry at a glance.
5. **Use `--app <id>`** when running DevSpark workflows to scope them to a specific application.
