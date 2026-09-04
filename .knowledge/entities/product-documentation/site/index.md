# DevSpark

## Current Release

[![Current Release](https://img.shields.io/github/v/release/markhazleton/devspark?label=current%20release)](https://github.com/markhazleton/devspark/releases/latest)

**Current version:** [v4.1.0](https://github.com/markhazleton/devspark/releases/tag/v4.1.0)

DevSpark is an Adaptive System Life Cycle Development toolkit for AI coding
assistants. It is prompt-first: the product is the command prompt collection,
quickstart prompts, helper scripts, schemas, skills, and current-truth knowledge
model.

The current source tree contains 30 active stock command prompts.

Install, upgrade, and repair DevSpark only by running the matching quickstart
prompt from `quickstart/` in the target repository.

## Guides

- [DevSpark Philosophy](philosophy.md) - External pressure, current truth, and assimilation
- [Quick Start Guide](quickstart.md) - Install, upgrade, repair, and first workflow
- [Installation Guide](installation.md) - Approved quickstart-based installation
- [Upgrade Guide](upgrade.md) - Approved quickstart-based upgrades and repairs
- [Implementation Lifecycle](implementation-lifecycle.md) - Prompt workflow from idea through release
- [Release Guide](release-usage.md) - Final validation and release-only archival
- [Constitution Guide](constitution-guide.md) - Governance principles and evolution
- [PR Review Guide](pr-review-usage.md) - Constitution-based PR review
- [Site Audit Guide](site-audit-usage.md) - Whole-repository audit prompt
- [Critic Guide](critic-usage.md) - Adversarial risk analysis
- [Checklist Guide](checklist-usage.md) - Validation checklist generation
- [Repo Story Guide](repo-story-usage.md) - Evidence-based repository narrative
- [Monorepo Guide](monorepo-guide.md) - Optional multi-application support
- [FAQ](faq.md) - Common questions

## Command Categories

The canonical feature path is `specify → clarify when needed → plan → tasks →
required checklist/analyze/critic gates → implement → focused verify when needed
→ commit/push → create-pr → pr-review ↔ address-pr-review → merge`. Release is a
separate human-triggered event.

### Core Workflow

| Command | Purpose |
|---------|---------|
| `/devspark.constitution` | Create or update governance principles |
| `/devspark.specify` | Define requirements and route work by size |
| `/devspark.plan` | Create the technical plan |
| `/devspark.tasks` | Break the plan into implementable tasks |
| `/devspark.implement` | Execute tasks and update work status |
| `/devspark.verify` | Verify behavioral proof and reject metric-only fixes |
| `/devspark.create-pr` | Draft a PR with workflow context |
| `/devspark.update-pr` | Refresh an existing PR description |
| `/devspark.next` | Detect the current workflow state and recommend the next command |

### Review and Quality

| Command | Purpose |
|---------|---------|
| `/devspark.pr-review` | Review a PR against the constitution |
| `/devspark.address-pr-review` | Resolve review findings with commit isolation |
| `/devspark.site-audit` | Audit repository quality and compliance |
| `/devspark.explain` | Explain existing behavior and verify its current-truth knowledge |
| `/devspark.critic` | Perform adversarial risk analysis |
| `/devspark.analyze` | Check cross-artifact consistency |
| `/devspark.checklist` | Generate validation checklists |
| `/devspark.fix-score` | Diagnose and resolve repository score blockers |

### Lifecycle

| Command | Purpose |
|---------|---------|
| `/devspark.quickfix` | Handle small fixes with lightweight records |
| `/devspark.release` | Validate code, tests, knowledge, and linkage; archive completed work |
| `/devspark.evolve-constitution` | Propose governance amendments |
| `/devspark.repo-story` | Generate a repository narrative from evidence |
| `/devspark.commit-audit` | Analyze commit history for delivery signals |
| `/devspark.taskstoissues` | Convert tasks into GitHub issues |
| `/devspark.personalize` | Create per-user prompt overrides |
| `/devspark.discover-constitution` | Generate a constitution from an existing codebase |
| `/devspark.discover-knowledge` | Build source-grounded `.knowledge/entities` and ontology |

### Multi-App

| Command | Purpose |
|---------|---------|
| `/devspark.add-application` | Register an application in `.knowledge/entities/application-registry/registry.json` |
| `/devspark.list-applications` | List applications and profiles |
| `/devspark.validate-registry` | Validate registry schema, references, and consistency |

## Current-Truth Model

- `.devspark/` contains framework-owned stock assets and the version stamp.
- `.knowledge/` contains durable governance, entities, decisions, ontology reports, repository documentation, and overrides.
- `.devspark.work/` contains temporary lifecycle work and should not be committed.
