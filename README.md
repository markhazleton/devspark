<div align="center">
    <img src=".knowledge/entities/product-documentation/site/media/brand/logo/makeboldsolutions-mark.svg" alt="Make Bold Solutions" width="56" height="56" />
    <h1>DevSpark</h1>
    <h3><em>A structured development process for AI coding assistants.<br/>Just markdown files — no install required.</em></h3>
</div>

<p align="center">
    <a href="https://github.com/markhazleton/devspark/releases/latest"><img src="https://img.shields.io/github/v/release/markhazleton/devspark?label=current%20release" alt="Current Release"/></a>
    <a href="https://github.com/markhazleton/devspark/actions/workflows/release.yml"><img src="https://github.com/markhazleton/devspark/actions/workflows/release.yml/badge.svg" alt="Release"/></a>
    <a href="https://github.com/markhazleton/devspark/stargazers"><img src="https://img.shields.io/github/stars/markhazleton/devspark?style=social" alt="GitHub stars"/></a>
    <a href="https://github.com/markhazleton/devspark/blob/main/LICENSE"><img src="https://img.shields.io/github/license/markhazleton/devspark" alt="License"/></a>
    <a href="https://markhazleton.github.io/devspark/"><img src="https://img.shields.io/badge/docs-GitHub_Pages-blue" alt="Documentation"/></a>
</p>

**Live Site**: [https://dev.makeboldspark.com](https://dev.makeboldspark.com)
**Current version:** [v4.0.0](https://github.com/markhazleton/devspark/releases/tag/v4.0.0)

> **Not a program. Not a subscription.** Copy 28 stock command prompts plus the helper templates and scripts into your project and your AI coding assistant gets a repeatable current-truth workflow. Works with Claude, Copilot, Cursor, Gemini, and [14 more](#supported-ai-agents).

---

## What's In This Repo

```text
devspark/
├── agents-registry.json  ← Canonical metadata for supported agent integrations
├── templates/commands/   ← 28 stock command prompt files (THE PRODUCT)
├── scripts/              ← Context-gathering scripts (PowerShell + Bash)
├── .knowledge/           ← Current truth: entities, governance, ontology reports
└── .knowledge/           ← Current truth, overrides, docs source, and ontology reports
```

## DevSpark Vocabulary

- **Prompt**: A workflow command surface, usually a slash-command file, that
  orchestrates DevSpark lifecycle behavior such as specification, planning,
  implementation, review, or release.
- **Agent**: An AI runtime or client integration such as Codex, Claude,
  Copilot, Cursor, or Gemini. Agent metadata lives in `agents-registry.json`
  and describes supported integrations, not team responsibilities.
- **Skill**: A reusable portable capability package that a prompt can delegate
  to when specialized task knowledge is useful.
- **Participant**: A human or AI-filled team member carrying responsibility for
  work, review, approval, critique, or decision capture in a workflow.
- **Role**: A responsibility label assigned to a participant, such as owner,
  planner, implementer, reviewer, critic, or scribe.

Participant metadata is optional advisory context in artifacts. It does not
change prompt resolution, script resolution, command behavior, or the existing
customization process.

## Agent Skills

DevSpark treats skills as portable capability packages within a governed lifecycle
orchestration system. Commands invoke skills; DevSpark governs the lifecycle around
them.

The dual-surface model:

```text
command -> adapter -> skill -> context scripts -> agent reasoning -> artifact
```

- **Slash-commands** (`templates/commands/`) own DevSpark-specific lifecycle behavior:
  route classification, branch creation, multi-app scoping, artifact placement, and
  gate enforcement.
- **Agent Skills** (`templates/skills/`) own portable capability instructions that
  run in any skills-compatible client without DevSpark installed.

The adapter contract (`templates/skills/ADAPTER-contract.md`) defines how a command
invokes a skill. The skill validation contract
(`templates/skills/SKILL-validation-contract.md`) defines the rules every `SKILL.md`
must satisfy. See `templates/skills/references/devspark-skills-guide.md` for the
contributor walkthrough for adding new skills.

---

## Get Started

DevSpark is installed, upgraded, and repaired only through quickstart prompts.
Point your AI agent at the quickstart prompt for your platform:

- [GitHub Copilot](quickstart/devspark_quickstart_copilot.md)
- [Claude Code](quickstart/devspark_quickstart_claudecode.md)
- [Cursor](quickstart/devspark_quickstart_cursor.md)
- [Codex](quickstart/devspark_quickstart_codex.md)
- [Any other agent](quickstart/devspark_quickstart_generic.md)

For ongoing updates or repairs, run the same quickstart prompt again in the
target repository. The quickstart compares the installed version, refreshes
framework-owned files, repairs missing stock assets, and preserves
repository-owned `.knowledge/` content.

For a full walkthrough see the [Implementation Lifecycle Guide](.knowledge/entities/product-documentation/site/implementation-lifecycle.md).

Recommended review loop: `specify → implement → pr-review → address-pr-review → pr-review UPDATE → merge`.

---

## Slash Commands

### Core Workflow

| Command | Purpose |
|---------|---------|
| `/devspark.constitution` | Establish project principles and guidelines |
| `/devspark.specify` | Define what you want to build (requirements & user stories) |
| `/devspark.plan` | Create a technical implementation plan |
| `/devspark.tasks` | Break the plan into actionable task lists |
| `/devspark.implement` | Execute tasks and build the feature |
| `/devspark.verify` | Verify behavioral proof and reject metric-only fixes |
| `/devspark.create-pr` | Draft or update a spec-aware pull request |
| `/devspark.update-pr` | Refresh an existing pull request description from the current branch delta |

### Constitution-Powered (no spec required)

| Command | Purpose |
|---------|---------|
| `/devspark.pr-review` | [Constitution-based PR review](.knowledge/entities/product-documentation/site/pr-review-usage.md) |
| `/devspark.address-pr-review` | Apply PR review fixes with mandatory commit isolation gates |
| `/devspark.site-audit` | [Comprehensive codebase audit](.knowledge/entities/product-documentation/site/site-audit-usage.md) |
| `/devspark.quickfix` | Lightweight workflow for bug fixes |
| `/devspark.fix-score` | Diagnose and remediate repository score blockers without weakening scoring rules |
| `/devspark.critic` | [Adversarial risk analysis](.knowledge/entities/product-documentation/site/critic-usage.md) |
| `/devspark.release` | Validate current truth, version, and prepare releases |
| `/devspark.harvest` | [Validate current truth and archive verified in-flight work packages](.knowledge/entities/product-documentation/site/harvest-usage.md) |
| `/devspark.evolve-constitution` | Propose constitution amendments |
| `/devspark.repo-story` | Generate narrative from commit history |
| `/devspark.commit-audit` | Analyze commit history for workflow, hygiene, and delivery signals |
| `/devspark.taskstoissues` | Convert tasks.md into dependency-ordered GitHub issues |

### Quality & Personalization

| Command | Purpose |
|---------|---------|
| `/devspark.clarify` | Ask structured questions to de-risk ambiguity |
| `/devspark.analyze` | Cross-artifact consistency check |
| `/devspark.checklist` | Generate quality validation checklists |
| `/devspark.personalize` | Create per-user command overrides |
| `/devspark.discover-constitution` | Generate a constitution from existing code |

### Multi-App (Optional)

| Command | Purpose |
|---------|---------|
| `/devspark.add-application` | Register a new application in the multi-app registry |
| `/devspark.list-applications` | Display all registered applications |
| `/devspark.validate-registry` | Validate registry schema, references, and consistency |

See [.knowledge/entities/product-documentation/site/index.md](.knowledge/entities/product-documentation/site/index.md#command-categories) for full command details.

---

## Multi-App Monorepo Support (Optional)

> **Single-app repositories need nothing here.** Multi-app is entirely optional — if your repo has one application, skip this section entirely. Everything works out of the box.

For repositories containing **multiple applications** with different platforms, runtimes, or governance rules, DevSpark offers opt-in multi-app support:

### When to Use Multi-App

| Scenario | Recommendation |
|----------|---------------|
| Single application or library | **Skip multi-app** — standard DevSpark is all you need |
| Monorepo with shared conventions | **Skip multi-app** — one constitution covers everything |
| Monorepo with different platforms (e.g., .NET API + React UI) | **Consider multi-app** — each app can have tailored rules |
| Monorepo with different governance (e.g., PCI service + internal tool) | **Use multi-app** — app-specific constitutions and profiles |

### How It Works

1. **Create a registry** at `.knowledge/entities/application-registry/registry.json` — or run `/devspark.add-application` to create one interactively
2. **Assign profiles** — reusable rule bundles (e.g., `api-profile`, `web-profile`) that apps inherit
3. **Scope commands** — use `--app <id>` to target a specific application, or `--repo-scope` for repo-wide operations
4. **App-local overrides** — each app can have its own `.knowledge/` directory and optional `app.json` manifest

### Multi-App Commands

| Command | Purpose |
|---------|---------|
| `/devspark.add-application` | Register a new application in the registry |
| `/devspark.list-applications` | Display all registered applications and profiles |
| `/devspark.validate-registry` | Validate registry schema, references, and consistency |

For the full specification, see the [Monorepo Guide](.knowledge/entities/product-documentation/site/monorepo-guide.md).

---

## Customization Without Risk

DevSpark cleanly separates **your work** from **its installation**:

```text
.devspark/                 ← Installation (removable, upgrade-safe)
├── defaults/commands/     ← Stock prompts
├── scripts/              ← Stock helper scripts
├── templates/            ← Spec/plan templates
└── VERSION               ← Installed version stamp

.knowledge/                ← Repository-owned current truth
├── governance/constitution.md
├── governance/decisions/
├── entities/
├── overrides/commands/             ← Team command overrides
├── overrides/scripts/              ← Team script overrides (optional)
└── overrides/{git-user}/commands/  ← Personal overrides

.devspark.work/            ← Ephemeral in-flight work packages
```

> **Multi-app layout** (optional): When using multi-app, each application also gets `{app-path}/.knowledge/` for app-local constitutions and overrides.

**3-tier prompt resolution** (first match wins):

1. `.knowledge/overrides/{git-user}/commands/` — Personal tweaks
2. `.knowledge/overrides/commands/` — Team customizations
3. `.devspark/defaults/commands/` — Stock prompts

**2-tier script resolution** (first match wins):

1. `.knowledge/overrides/scripts/` — Team script overrides (e.g., Azure DevOps adapter)
2. `.devspark/scripts/` — Stock scripts

There is no third ownership tier. If an organization wants a shared baseline in `.knowledge/`, it manages that through its own repo practices; DevSpark still only writes to `.devspark/`.

Participant metadata uses these existing repository-owned artifacts when present.
It does not change how prompts or scripts are found; customization layers and
precedence are unchanged.

**Clean removal**: remove `.devspark/` and generated agent shims. Leave
`.knowledge/` intact unless the user explicitly asks to remove repository-owned
current truth.

---

## Supported AI Agents

DevSpark is agent-agnostic. Every agent below gets thin shims that resolve personal overrides, team overrides, and stock prompts through the same command contract.

| Agent | | Agent | | Agent | |
|-------|---|-------|---|-------|---|
| [Claude Code](https://www.anthropic.com/claude-code) | ✅ | [Cursor](https://cursor.sh/) | ✅ | [Gemini CLI](https://github.com/google-gemini/gemini-cli) | ✅ |
| [GitHub Copilot](https://code.visualstudio.com/) | ✅ | [Codex CLI](https://github.com/openai/codex) | ✅ | [Windsurf](https://windsurf.com/) | ✅ |
| [Amp](https://ampcode.com/) | ✅ | [Roo Code](https://roocode.com/) | ✅ | [Kilo Code](https://github.com/Kilo-Org/kilocode) | ✅ |
| [Auggie CLI](https://docs.augmentcode.com/cli/overview) | ✅ | [opencode](https://opencode.ai/) | ✅ | [Qwen Code](https://github.com/QwenLM/qwen-code) | ✅ |
| [SHAI](https://github.com/ovh/shai) | ✅ | [Amazon Q](https://aws.amazon.com/developer/learning/q-developer-cli/) | ⚠️ | [IBM Bob](https://www.ibm.com/products/bob) | ✅ |
| [CodeBuddy](https://www.codebuddy.ai/cli) | ✅ | [Qoder CLI](https://qoder.com/cli) | ✅ | [Antigravity](https://deepmind.google/technologies/gemini/) | ✅ |

---

## Learn More

| Topic | Link |
|-------|------|
| Implementation lifecycle | [implementation-lifecycle.md](.knowledge/entities/product-documentation/site/implementation-lifecycle.md) |
| Quickstart | [quickstart.md](.knowledge/entities/product-documentation/site/quickstart.md) |
| Constitution guide | [constitution-guide.md](.knowledge/entities/product-documentation/site/constitution-guide.md) |
| Installation | [installation.md](.knowledge/entities/product-documentation/site/installation.md) |
| Upgrading | [upgrade.md](.knowledge/entities/product-documentation/site/upgrade.md) |
| PR review guide | [pr-review-usage.md](.knowledge/entities/product-documentation/site/pr-review-usage.md) |
| Site audit guide | [site-audit-usage.md](.knowledge/entities/product-documentation/site/site-audit-usage.md) |
| Critic guide | [critic-usage.md](.knowledge/entities/product-documentation/site/critic-usage.md) |
| Harvest guide | [harvest-usage.md](.knowledge/entities/product-documentation/site/harvest-usage.md) |
| Repo story | [repo-story-usage.md](.knowledge/entities/product-documentation/site/repo-story-usage.md) |

---

## Prerequisites

- **Any OS** (Linux / macOS / Windows)
- A [supported AI coding agent](#supported-ai-agents)
- [Git](https://git-scm.com/downloads) (recommended)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Acknowledgements

DevSpark is maintained by [Mark Hazleton](https://github.com/markhazleton) and the open-source community.

> Built by [Mark Hazleton](https://markhazleton.com) — Mark Hazleton, Solutions Architect
> DevSpark is part of the [Make Bold Spark](https://makeboldspark.com) portfolio of technical demonstrations.

A [Make Bold Solutions](https://makeboldsolutions.com) project, part of the [Make Bold Spark](https://makeboldspark.com) family.

## License

MIT — see [LICENSE](./LICENSE).
