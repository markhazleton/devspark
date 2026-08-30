# DevSpark

## Current Release

[![Current Release](https://img.shields.io/github/v/release/markhazleton/devspark?label=current%20release)](https://github.com/markhazleton/devspark/releases/latest)

**Current version:** [v4.1.0](https://github.com/markhazleton/devspark/releases/tag/v4.1.0)

DevSpark is an Adaptive System Life Cycle Development toolkit for AI coding
assistants. It is prompt-first: the product is the command prompt collection,
quickstart prompts, helper scripts, schemas, skills, and current-truth knowledge
model.

The v4.1.0 release ships 29 active stock command prompts.

Install, upgrade, and repair DevSpark only by running the matching quickstart
prompt from `quickstart/` in the target repository.

## Guides

- [Quick Start Guide](quickstart.md) - Install, upgrade, repair, and first workflow
- [Installation Guide](installation.md) - Approved quickstart-based installation
- [Upgrade Guide](upgrade.md) - Approved quickstart-based upgrades and repairs
- [Implementation Lifecycle](implementation-lifecycle.md) - Prompt workflow from idea through release
- [Constitution Guide](constitution-guide.md) - Governance principles and evolution
- [PR Review Guide](pr-review-usage.md) - Constitution-based PR review
- [Site Audit Guide](site-audit-usage.md) - Whole-repository audit prompt
- [Critic Guide](critic-usage.md) - Adversarial risk analysis
- [Harvest Guide](harvest-usage.md) - Knowledge-preserving cleanup
- [Checklist Guide](checklist-usage.md) - Validation checklist generation
- [Repo Story Guide](repo-story-usage.md) - Evidence-based repository narrative
- [Monorepo Guide](monorepo-guide.md) - Optional multi-application support
- [FAQ](faq.md) - Common questions

## Command Categories

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

### Review and Quality

| Command | Purpose |
|---------|---------|
| `/devspark.pr-review` | Review a PR against the constitution |
| `/devspark.address-pr-review` | Resolve review findings with commit isolation |
| `/devspark.site-audit` | Audit repository quality and compliance |
| `/devspark.critic` | Perform adversarial risk analysis |
| `/devspark.analyze` | Check cross-artifact consistency |
| `/devspark.checklist` | Generate validation checklists |
| `/devspark.fix-score` | Diagnose and resolve repository score blockers |

### Lifecycle

| Command | Purpose |
|---------|---------|
| `/devspark.quickfix` | Handle small fixes with lightweight records |
| `/devspark.release` | Validate current truth, version, and prepare releases |
| `/devspark.harvest` | Archive verified ephemeral work packages after current-truth assimilation |
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
- `.knowledge/` contains durable governance, entities, decisions, and ontology reports.
- `.knowledge/` contains repository-owned documentation and guides.
- `.devspark.work/` contains temporary lifecycle work and should not be committed.
