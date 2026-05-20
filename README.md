<div align="center">
    <h1>DevSpark</h1>
    <h3><em>A structured development process for AI coding assistants.<br/>Just markdown files — no install required.</em></h3>
</div>

<p align="center">
    <a href="https://github.com/markhazleton/devspark/actions/workflows/release.yml"><img src="https://github.com/markhazleton/devspark/actions/workflows/release.yml/badge.svg" alt="Release"/></a>
    <a href="https://github.com/markhazleton/devspark/stargazers"><img src="https://img.shields.io/github/stars/markhazleton/devspark?style=social" alt="GitHub stars"/></a>
    <a href="https://github.com/markhazleton/devspark/blob/main/LICENSE"><img src="https://img.shields.io/github/license/markhazleton/devspark" alt="License"/></a>
    <a href="https://markhazleton.github.io/devspark/"><img src="https://img.shields.io/badge/docs-GitHub_Pages-blue" alt="Documentation"/></a>
</p>

**Live Site**: [https://dev.makeboldspark.com](https://dev.makeboldspark.com)

> **Not a program. Not a subscription.** Copy 28 slash-command prompts plus the helper templates and scripts into your project and your AI coding assistant gets a repeatable workflow — from requirements through release. Works with Claude, Copilot, Cursor, Gemini, and [13 more](#supported-ai-agents).

## Current Release: v2.3.0

---

## What's In This Repo

```text
devspark/
├── agents-registry.json  ← Canonical metadata for supported agent integrations
├── templates/commands/   ← 28 slash-command prompt files (THE PRODUCT)
├── scripts/              ← Context-gathering scripts (PowerShell + Bash)
├── src/devspark_cli/     ← Optional CLI for automated setup
└── .documentation/       ← Guides, media, and GitHub Pages site
```

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

DevSpark v2 ships three flagship aliases that are the recommended entrypoints for every new feature. Run them via `devspark run <alias>` (or your agent's `/devspark.run` slash command):

| Alias | What it runs |
|-------|--------------|
| `create-spec` | `specify → plan → tasks → analyze` (pauses after analyze for review) |
| `execute-plan` | `implement → create-pr → pr-review` (pauses after create-pr) |
| `suggest-improvement` | `capture-context → classify-improvement → create-issue` (files an issue against `markhazleton/devspark`) |

See [.documentation/workflows/getting-started.md](.documentation/workflows/getting-started.md) for the full walkthrough.

For one-off work outside a workflow, the legacy entry command remains: `/devspark.specify`. It classifies the request as a one-off fix, a quick spec, or a full spec, explains the recommendation, and lets the human confirm the route before proceeding.

**Option A — Agent Quickstart** (recommended — no install)

Point your AI agent at the quickstart prompt for your platform:

- [GitHub Copilot](quickstart/devspark_quickstart_copilot.md)
- [Claude Code](quickstart/devspark_quickstart_claudecode.md)
- [Cursor](quickstart/devspark_quickstart_cursor.md)
- [Codex](quickstart/devspark_quickstart_codex.md)
- [Any other agent](quickstart/devspark_quickstart_generic.md)

The agent asks a few questions, then pulls and installs all DevSpark prompts.

For ongoing updates, use the same no-install approach:

- Paste this [upgrade prompt URL](https://raw.githubusercontent.com/markhazleton/devspark/main/templates/commands/upgrade.md) into your agent chat
- Ask it to run an upgrade in your current repository

This keeps upgrades prompt-first and does not require the CLI.

## Option B — Download and Drop

1. Download the [latest release](https://github.com/markhazleton/devspark/releases) zip for your agent and unzip into your project
2. Start using `/devspark.*` commands in your AI assistant

### Option C — CLI (advanced/optional)

```bash
uv tool install devspark-cli --from git+https://github.com/markhazleton/devspark.git
devspark init my-project          # new project
devspark init --here --ai claude  # existing project
```

The CLI also exposes the optional harness runtime and environment checks:

```bash
devspark doctor
devspark harness validate sample.harness.yaml
devspark harness run sample.harness.yaml --dry-run
devspark adapter list
```

For a full walkthrough see the [Implementation Lifecycle Guide](.documentation/implementation-lifecycle.md).

Recommended review loop: `specify → implement → pr-review → address-pr-review → pr-review UPDATE → merge`.

## Harness Runtime

DevSpark also ships an additive CLI runtime for repeatable engineering workflows. This runtime is separate from the 28 slash commands and is available when you install the optional CLI or work from a compatible source checkout.

The harness runtime adds:

- `devspark harness run` to execute a declarative workflow spec
- `devspark harness validate` to check spec structure without execution
- `devspark harness trace` to inspect the event log from a prior run
- `devspark adapter list` and `devspark adapter default` to inspect and persist adapter preferences
- `devspark doctor` to verify the local environment is ready for harness workflows

Harness runs write structured artifacts to `.documentation/devspark/runs/` by default, preserve partial state on abort, and support repository or app-scoped execution when a multi-app registry is present.

See [Harness Engineering](.documentation/harness-engineering.md) for the runtime model, command reference, artifact layout, adapters, and spec design guidance.

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
| `/devspark.create-pr` | Draft or update a spec-aware pull request |
| `/devspark.update-pr` | Refresh an existing pull request description from the current branch delta |

### Constitution-Powered (no spec required)

| Command | Purpose |
|---------|---------|
| `/devspark.pr-review` | [Constitution-based PR review](.documentation/pr-review-usage.md) |
| `/devspark.address-pr-review` | Apply PR review fixes with mandatory commit isolation gates |
| `/devspark.site-audit` | [Comprehensive codebase audit](.documentation/site-audit-usage.md) |
| `/devspark.quickfix` | Lightweight workflow for bug fixes |
| `/devspark.critic` | [Adversarial risk analysis](.documentation/critic-usage.md) |
| `/devspark.release` | Archive dev artifacts and prepare releases |
| `/devspark.harvest` | [Canonical knowledge-preserving cleanup and archival workflow](.documentation/harvest-usage.md) |
| `/devspark.evolve-constitution` | Propose constitution amendments |
| `/devspark.repo-story` | Generate narrative from commit history |
| `/devspark.commit-audit` | Analyze commit history for workflow, hygiene, and delivery signals |

### Quality & Personalization

| Command | Purpose |
|---------|---------|
| `/devspark.clarify` | Ask structured questions to de-risk ambiguity |
| `/devspark.analyze` | Cross-artifact consistency check |
| `/devspark.checklist` | Generate quality validation checklists |
| `/devspark.personalize` | Create per-user command overrides |
| `/devspark.discover-constitution` | Generate a constitution from existing code |
| `/devspark.upgrade` | Pull latest DevSpark prompts into your project |

`/devspark.harvest` is the canonical cleanup and archival workflow. `/devspark.archive` remains available only as a deprecated compatibility alias during migration.

### Multi-App (Optional)

| Command | Purpose |
|---------|---------|
| `/devspark.add-application` | Register a new application in the multi-app registry |
| `/devspark.list-applications` | Display all registered applications |
| `/devspark.validate-registry` | Validate registry schema, references, and consistency |

See [templates/README.md](templates/README.md) for full command details.

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

1. **Create a registry** at `.documentation/devspark.json` — or run `/devspark.add-application` to create one interactively
2. **Assign profiles** — reusable rule bundles (e.g., `api-profile`, `web-profile`) that apps inherit
3. **Scope commands** — use `--app <id>` to target a specific application, or `--repo-scope` for repo-wide operations
4. **App-local overrides** — each app can have its own `.documentation/` directory and optional `app.json` manifest

### Multi-App Commands

| Command | Purpose |
|---------|---------|
| `/devspark.add-application` | Register a new application in the registry |
| `/devspark.list-applications` | Display all registered applications and profiles |
| `/devspark.validate-registry` | Validate registry schema, references, and consistency |

For the full specification, see the [Monorepo Guide](.documentation/monorepo-guide.md).

---

## Customization Without Risk

DevSpark cleanly separates **your work** from **its installation**:

```text
.devspark/                 ← Installation (removable, upgrade-safe)
├── defaults/commands/     ← Stock prompts
├── scripts/              ← Stock helper scripts
├── templates/            ← Spec/plan templates
└── VERSION               ← Installed version stamp

.documentation/            ← Your work (never touched by DevSpark)
├── memory/constitution.md
├── specs/
├── commands/             ← Team command overrides
├── scripts/              ← Team script overrides (optional)
├── devspark.json         ← Multi-app registry (optional)
└── {git-user}/commands/  ← Personal overrides
```

> **Multi-app layout** (optional): When using multi-app, each application also gets `{app-path}/.documentation/` for app-local constitutions and overrides.

**3-tier prompt resolution** (first match wins):

1. `.documentation/{git-user}/commands/` — Personal tweaks
2. `.documentation/commands/` — Team customizations
3. `.devspark/defaults/commands/` — Stock prompts

**2-tier script resolution** (first match wins):

1. `.documentation/scripts/` — Team script overrides (e.g., Azure DevOps adapter)
2. `.devspark/scripts/` — Stock scripts

There is no third ownership tier. If an organization wants a shared baseline in `.documentation/`, it manages that through its own repo practices; DevSpark still only writes to `.devspark/`.

**Clean removal**: `devspark uninstall` removes `.devspark/` and agent shims, leaves `.documentation/` untouched.

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
| [CodeBuddy](https://www.codebuddy.ai/cli) | ✅ | [Qoder CLI](https://qoder.com/cli) | ✅ | | |

---

## Learn More

| Topic | Link |
|-------|------|
| Implementation lifecycle | [implementation-lifecycle.md](.documentation/implementation-lifecycle.md) |
| Harness engineering | [harness-engineering.md](.documentation/harness-engineering.md) |
| Quickstart | [quickstart.md](.documentation/quickstart.md) |
| Constitution guide | [constitution-guide.md](.documentation/constitution-guide.md) |
| CLI reference | [installation.md](.documentation/installation.md) |
| Upgrading | [upgrade.md](.documentation/upgrade.md) |
| PR review guide | [pr-review-usage.md](.documentation/pr-review-usage.md) |
| Site audit guide | [site-audit-usage.md](.documentation/site-audit-usage.md) |
| Critic guide | [critic-usage.md](.documentation/critic-usage.md) |
| Harvest guide | [harvest-usage.md](.documentation/harvest-usage.md) |
| Repo story | [repo-story-usage.md](.documentation/repo-story-usage.md) |
| Repo story (latest) | [repo-story-2026-04-17.md](.documentation/repo-story/repo-story-2026-04-17.md) |

---

## Prerequisites

- **Any OS** (Linux / macOS / Windows)
- A [supported AI coding agent](#supported-ai-agents)
- [Git](https://git-scm.com/downloads) (recommended)
- [uv](https://docs.astral.sh/uv/) + [Python 3.11+](https://www.python.org/downloads/) (only if using the CLI)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Acknowledgements

DevSpark is maintained by [Mark Hazleton](https://github.com/markhazleton) and the open-source community.

> Built by [Mark Hazleton](https://markhazleton.com) — Mark Hazleton, Solutions Architect
> DevSpark is part of the [Make Bold Spark](https://makeboldspark.com) portfolio of technical demonstrations.

## License

MIT — see [LICENSE](./LICENSE).
