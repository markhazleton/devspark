<div align="center">
    <img src="./.documentation/media/logo_large.webp" alt="DevSpark Logo" width="200" height="200"/>
    <h1>DevSpark</h1>
    <h3><em>A structured development process for AI coding assistants.<br/>Just markdown files — no install required.</em></h3>
</div>

<p align="center">
    <a href="https://github.com/markhazleton/devspark/actions/workflows/release.yml"><img src="https://github.com/markhazleton/devspark/actions/workflows/release.yml/badge.svg" alt="Release"/></a>
    <a href="https://github.com/markhazleton/devspark/stargazers"><img src="https://img.shields.io/github/stars/markhazleton/devspark?style=social" alt="GitHub stars"/></a>
    <a href="https://github.com/markhazleton/devspark/blob/main/LICENSE"><img src="https://img.shields.io/github/license/markhazleton/devspark" alt="License"/></a>
    <a href="https://markhazleton.github.io/devspark/"><img src="https://img.shields.io/badge/docs-GitHub_Pages-blue" alt="Documentation"/></a>
</p>

> **Not a program. Not a subscription.** Copy 21 prompt files into your project and your AI coding assistant gets a repeatable workflow — from requirements through release. Works with Claude, Copilot, Cursor, Gemini, and [13 more](#supported-ai-agents).

---

## What's In This Repo

```text
devspark/
├── templates/commands/   ← 21 slash-command prompt files (THE PRODUCT)
├── scripts/              ← Context-gathering scripts (PowerShell + Bash)
├── src/devspark_cli/     ← Optional CLI for automated setup
└── .documentation/       ← Guides, media, and GitHub Pages site
```

## Get Started

**Option A — Agent Quickstart** (recommended — no install)

Point your AI agent at the quickstart prompt for your platform:
- [GitHub Copilot](quickstart/devspark_quickstart_copilot.md)
- [Claude Code](quickstart/devspark_quickstart_claudecode.md)
- [Cursor](quickstart/devspark_quickstart_cursor.md)
- [Any other agent](quickstart/devspark_quickstart_generic.md)

The agent asks a few questions, then pulls and installs all DevSpark prompts — including migration from Spec Kit if needed.

**Option B — Download and Drop**

1. Download the [latest release](https://github.com/markhazleton/devspark/releases) zip for your agent and unzip into your project
2. Start using `/devspark.*` commands in your AI assistant

**Option C — CLI** (automates Option A)

```bash
uv tool install devspark-cli --from git+https://github.com/markhazleton/devspark.git
devspark init my-project          # new project
devspark init --here --ai claude  # existing project
```

For a full walkthrough see the [Quickstart Guide](.documentation/quickstart.md) or the [Step-by-Step Tutorial](.documentation/spec-driven-development.md).

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

### Constitution-Powered (no spec required)

| Command | Purpose |
|---------|---------|
| `/devspark.pr-review` | [Constitution-based PR review](.documentation/pr-review-usage.md) |
| `/devspark.site-audit` | [Comprehensive codebase audit](.documentation/site-audit-usage.md) |
| `/devspark.quickfix` | Lightweight workflow for bug fixes |
| `/devspark.critic` | [Adversarial risk analysis](.documentation/critic-usage.md) |
| `/devspark.release` | Archive dev artifacts and prepare releases |
| `/devspark.harvest` | [Clean stale docs and archive obsolete artifacts](.documentation/harvest-usage.md) |
| `/devspark.evolve-constitution` | Propose constitution amendments |
| `/devspark.repo-story` | Generate narrative from commit history |

### Quality & Personalization

| Command | Purpose |
|---------|---------|
| `/devspark.clarify` | Ask structured questions to de-risk ambiguity |
| `/devspark.analyze` | Cross-artifact consistency check |
| `/devspark.checklist` | Generate quality validation checklists |
| `/devspark.personalize` | Create per-user command overrides |
| `/devspark.discover-constitution` | Generate a constitution from existing code |
| `/devspark.archive` | Archive completed spec artifacts |
| `/devspark.upgrade` | Pull latest DevSpark prompts into your project |

See [templates/README.md](templates/README.md) for full command details.

---

## Customization Without Risk

DevSpark cleanly separates **your work** from **its installation**:

```text
.devspark/                 ← Installation (removable, upgrade-safe)
├── defaults/commands/     ← Stock prompts
├── scripts/              ← Helper scripts
├── templates/            ← Spec/plan templates
└── VERSION               ← Installed version stamp

.documentation/            ← Your work (never touched by DevSpark)
├── memory/constitution.md
├── specs/
├── commands/             ← Team command overrides
└── {git-user}/commands/  ← Personal overrides
```

**3-tier prompt resolution** (first match wins):
1. `.documentation/{git-user}/commands/` — Personal tweaks
2. `.documentation/commands/` — Team customizations
3. `.devspark/defaults/commands/` — Stock prompts

**Clean removal**: `devspark uninstall` removes `.devspark/` and agent shims, leaves `.documentation/` untouched.

---

## Supported AI Agents

DevSpark is agent-agnostic. Every agent below gets thin shims that redirect to shared canonical prompts.

| Agent | | Agent | | Agent |
|-------|-|-------|-|-------|
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
| Quickstart | [quickstart.md](.documentation/quickstart.md) |
| Full methodology | [spec-driven-development.md](.documentation/spec-driven-development.md) |
| Adaptive lifecycle (ASLCD) | [adaptive-lifecycle.md](.documentation/adaptive-lifecycle.md) |
| Constitution guide | [constitution-guide.md](.documentation/constitution-guide.md) |
| CLI reference | [installation.md](.documentation/installation.md) |
| Upgrading | [upgrade.md](.documentation/upgrade.md) |
| Roadmap | [roadmap.md](.documentation/roadmap.md) |
| PR review guide | [pr-review-usage.md](.documentation/pr-review-usage.md) |
| Site audit guide | [site-audit-usage.md](.documentation/site-audit-usage.md) |
| Critic guide | [critic-usage.md](.documentation/critic-usage.md) |
| Harvest guide | [harvest-usage.md](.documentation/harvest-usage.md) |

[![DevSpark video](./.documentation/media/devspark-video-header.jpg)](https://www.youtube.com/watch?v=a9eR1xsfvHg)

---

## Prerequisites

- **Any OS** (Linux / macOS / Windows)
- A [supported AI coding agent](#supported-ai-agents)
- [Git](https://git-scm.com/downloads) (recommended)
- [uv](https://docs.astral.sh/uv/) + [Python 3.11+](https://www.python.org/downloads/) (only if using the CLI)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Acknowledgements

DevSpark is inspired by [github/spec-kit](https://github.com/github/spec-kit) by [John Lam](https://github.com/jflam) and [Den Delimarsky](https://github.com/localden).

## License

MIT — see [LICENSE](./LICENSE).
