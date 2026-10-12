# Multi-Application Monorepo Support

Multi-app support lets one repository hold several applications with per-app governance, scoped workflows, and dependency-aware reviews. It is entirely opt-in: a repository without `.devspark.work/devspark.registry.json` behaves exactly as a single-app repository, and the registry skills report that no registry is configured.

The design rests on three ideas: **explicit scope** (a registry declares each app), **layered governance** (repo-wide rules always apply; apps add to them), and **dependency awareness** (a change reports the apps it can affect).

## The application registry

Every app is declared in `.devspark.work/devspark.registry.json`, the single source of truth:

```json
{
  "version": 1,
  "mode": "multi-app",
  "profiles": {
    "api-profile": {
      "description": "Shared rules for all API services",
      "rules": ["Integration tests for every public endpoint", "OpenAPI spec required"]
    }
  },
  "apps": [
    {
      "id": "admin-web",
      "path": "apps/admin-web",
      "kind": "web",
      "purpose": "Internal administration dashboard",
      "owner": "admin-team",
      "criticality": "medium",
      "inherits": ["web-profile"],
      "dependsOn": ["admin-api"]
    }
  ]
}
```

IDs must be unique, lowercase, and path-safe. Paths must exist, and profile and dependency references must resolve. Validation fails fast on errors. Shared libraries are entries with `kind: "library"` and `deployable: false`; they take part in dependency tracking but not in deployment or release workflows.

An older registry stored inside the combined `devspark.json` is moved with `/devspark-migrate-registry` (optional, confirmed by you).

## Layered governance

```text
Repository-wide governance (mandatory)   .knowledge/governance/constitution.md, shared overrides
Profile rules (shared by app class)      api-profile, web-profile, ...
App-specific overlays (additive only)    {app.path}/.knowledge/, {app.path}/app.json
```

App-level rules can strengthen or extend repo-wide rules but never weaken them. If the repository constitution requires 80% coverage, no app can opt out.

| Asset | Resolution order (highest priority first) |
|---|---|
| Constitution | Repo constitution, then profile rules, then app overlay (additive) |
| Prompts | App team override, repo user override, repo team override, stock default |
| Scripts and templates | App team override, repo team override, stock default |
| Specs, plans, tasks | Stored under `{app.path}/.devspark.work/specs/` for app-scoped work |

### Profiles

An app's `inherits` list applies profiles in order, then its own `overrides`. Rules accumulate and are never removed; tags and hints are last-writer-wins. Rules from the repository constitution are immutable across all layers.

### Weakening detection

Validation parses the repo constitution for `NON-NEGOTIABLE`, `MUST`, and `MANDATORY` lines. If an app constitution contradicts or relaxes one (for example, "optional" or "does not apply"), validation emits a **CONFLICT** warning. Conflicts are reported in validation output and scope reports; they do not hard-block workflows.

## Scope and dependencies

Declared `dependsOn` links tell DevSpark when a change to one app may affect another: a change to `admin-api` contracts reports `admin-web` as a downstream consumer. It also infers dependencies from imports and build files (`package.json`, `pyproject.toml`, `.csproj` references) and labels them "inferred".

PRs declare a scope, which is compared with the changed files and dependency graph:

| PR scope | Use when | Validation |
|---|---|---|
| `single-app` | One application changes | Changed files stay within the app path plus approved shared paths |
| `cross-app` | A change intentionally spans apps | Declare the primary app, all affected apps, and why it cannot be split |
| `repo-scope` | Shared contracts, libraries, or infrastructure | For changes that belong to no single app |

Approved shared paths for `single-app` PRs: root-level `.knowledge/guides/`, `.github/`, `.devspark/`, root config files (`*.md`, `*.json`, `*.yaml`, `*.toml`, `*.cfg`), and root CI files such as `azure-pipelines.yml`. A file belonging to another registered app triggers a scope mismatch and requires reclassification.

## Commands

| Skill | Does |
|---|---|
| `/devspark-add-application` | Guided registration: collects id, path, kind, owner, criticality, profiles, and dependencies; scaffolds the app's `.devspark.work/` and `.knowledge/` roots. It also handles removing an app, refusing when another registered app depends on it |
| `/devspark-list-applications` | Read-only listing of every app and its metadata |
| `/devspark-validate-registry` | Checks schema, references, cycles, paths, and app-local manifest consistency |
| `/devspark-migrate-registry` | Moves a legacy registry into `devspark.registry.json` |

Pass `--app <id>` to scope a workflow to one application. Renaming, moving, and splitting apps, and shared-package release orchestration, are not yet supported.

## On-disk layout

```text
repo-root/
├── .devspark/                       # Framework (do not edit)
├── .devspark.work/
│   ├── devspark.json                # Repository configuration
│   ├── devspark.registry.json       # Application registry
│   ├── commands/, scripts/          # Shared overrides
│   └── specs/                       # Active repository plans
├── .knowledge/                      # Repo-wide governance and truth
│   ├── governance/constitution.md   # Mandatory constitution
│   └── guides/                      # Published repository guidance
├── apps/
│   └── admin-web/
│       ├── .devspark.work/          # App-scoped temporary work
│       ├── .knowledge/              # App truth and constitution overlay
│       ├── app.json                 # Optional tags, hints, and rules
│       └── src/
└── libs/shared-auth/                # kind: "library"
```

`{app.path}/app.json` carries app-specific tags, hints, and rules only. Identity fields (id, path, kind, owner) are ignored there because the registry is authoritative.

## Design decisions

| Rejected alternative | Why |
|---|---|
| One DevSpark install per app | Duplicates framework files, drifts on upgrade, and makes cross-app review harder |
| One repo-wide install with no app overrides | Ignores real governance differences between APIs, web apps, and QA tooling |
| Infer the app from working directory or branch name | Brittle in CI and unclear for root-level workflows |
| Let app constitutions override repo governance | Makes compliance non-deterministic |

## Getting started

1. Run `/devspark-add-application` for your first app; it creates the registry.
2. Repeat for each additional app.
3. Run `/devspark-validate-registry`, then `/devspark-list-applications`.
4. Use `--app <id>` to scope workflows.
