<!-- DevSpark — © 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com -->

<div align="center">
    <img src="site/src/media/brand/logo/makeboldsolutions-mark.svg" alt="Make Bold Solutions" width="56" height="56" />
    <h1>DevSpark</h1>
    <h3><em>A structured development process for AI coding assistants.<br/>Just markdown files — no install required.</em></h3>
</div>

> **Not a program. Not a subscription.** Copy 38 active slash-command prompts and helper templates/scripts into your project and your AI coding assistant gets a repeatable workflow — from requirements through release. Works with Claude, Copilot, Cursor, Gemini, and [14 more](#supported-ai-agents).

**Docs & install (no repo access required):** [https://dev.makeboldspark.com](https://dev.makeboldspark.com)

---

## What's In This Repo

```text
devspark/
├── agents-registry.json  ← Canonical metadata for supported agent integrations
├── templates/commands/   ← 38 prompt files (38 active commands)
├── scripts/              ← Context-gathering scripts (PowerShell + Bash)
└── site/
  ├── src/              ← Authored public-site pages and media
  └── _site/            ← Generated DocFX output (ignored)
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

In 9.0 every DevSpark command is itself installed as a GitHub Copilot Agent Skill, invoked as
`/devspark-<command>`. The portable capability skills described here are a separate layer that
commands can call.

The dual-surface model:

```text
command -> adapter -> skill -> context scripts -> agent reasoning -> artifact
```

- **Slash-commands** (`templates/commands/`) own DevSpark-specific lifecycle behavior:
  universal work start/resume, safe branch creation, multi-app scoping, optional artifact placement,
  and legacy v9.3 gate routing.
- **Agent Skills** (`templates/skills/`) own portable capability instructions that
  run in any skills-compatible client without DevSpark installed.

The adapter contract (`templates/skills/ADAPTER-contract.md`) defines how a command
invokes a skill. The skill validation contract
(`templates/skills/SKILL-validation-contract.md`) defines the rules every `SKILL.md`
must satisfy. See `templates/skills/references/devspark-skills-guide.md` for the
contributor walkthrough for adding new skills.

---

## Get Started

See the [engineering philosophy](site/src/why/philosophy.md#our-vision): Code First and
Model First are equally legitimate ways to build excellent software with AI tools. For a small
already-implemented or partially implemented change, use `/devspark-quickfix` to inspect the diff,
validate it, and reconcile any lasting Knowledge without inventing earlier planning artifacts.

DevSpark's core spec-driven flow runs entirely as slash commands — no install, no CLI:

| Flow | Commands |
|------|--------------|
| Create a spec | `/devspark-specify` → `/devspark-plan` → `/devspark-tasks` → `/devspark-planning-review` (Analyze, Critic when applicable, and Judge as one decision before implementing) |
| Execute a plan | `/devspark-implement` → `/devspark-create-pr` → `/devspark-pr-review` |

See [.knowledge/tooling/developer-guide.md](.knowledge/tooling/developer-guide.md) and the command tables below for the full command set.

For new work, use `/devspark-specify` (or `/devspark-next` to resume). It establishes the intended outcome and first useful increment, then starts the same implementation path without a Light/Full choice or mandatory planning bundle. A brief `work.md` resume note is created only when material context would otherwise be lost. Active v9.3 specifications continue on their existing route.

**Agent Quickstart** (the only supported install/upgrade path)

Point your AI agent at the quickstart prompt for your platform:

- [GitHub Copilot](quickstart/devspark_quickstart_copilot.md)
- [Claude Code](quickstart/devspark_quickstart_claudecode.md)
- [Cursor](quickstart/devspark_quickstart_cursor.md)
- [Codex](quickstart/devspark_quickstart_codex.md)
- [Any other agent](quickstart/devspark_quickstart_generic.md)

The agent asks a few questions, then pulls and installs all DevSpark prompts.

> **Trust but verify.** Each quickstart opens with a **Preview Prompt** section — read the exact instructions and command prompts, or ask the agent for a read-only dry run, before anything is written to your repo. Nothing runs until you approve.

For ongoing updates, use the same no-install approach:

- Paste your agent's [quickstart guide URL](https://dev.makeboldspark.com/raw/quickstart/devspark_quickstart_copilot.md) into your agent chat
- It detects the existing install and runs a manifest-driven upgrade in your current repository

This keeps installs and upgrades prompt-first, with no CLI and no packages to download.

Recommended review loop: `specify → implement → pr-review → address-pr-review → pr-review UPDATE → merge`.

### What's new in 9.0

- **One command convention: `/devspark-<command>`.** All 38 commands install as native GitHub Copilot Agent Skills (`.github/skills/devspark-<command>/SKILL.md`). The dotted `/devspark.<command>` form from 8.x is retired with no aliases, fallback, or compatibility mode.
- **Safe upgrade from 8.x.** The upgrade shows the 8.x entry points it will retire and asks once. Unmodified managed files are deleted, edited ones are preserved byte-for-byte in `.devspark.work/migration/8.x-entry-points/`, and your team and personal customizations in `.devspark.work/` are never touched. Re-running the upgrade changes nothing.
- **Same customization precedence.** Developer, then team, then distributed default, resolved by the same rule as before.
- **Tested with.** VS Code Insiders 1.142.0 and its built-in Copilot Chat, local Windows. Typed text after `/devspark-<command>` is passed to the skill as the command's input. Older builds were not tested.
- **Implementation complete means ready to merge and deploy.** Verification obligations that can only be proven in a deployed environment are recorded as post-deploy requirements with an owner and a real tracking record. They stay visible and unproven until deployment evidence exists, and they never block implementation or the pull request. Pre-merge safety and compliance requirements still block.

This is a breaking release. See [Upgrading from 8.x](site/src/get-started/upgrade.md#upgrading-from-8x), the [release notes](site/src/releases.md) and the [Command Catalog](site/src/guides/prompt-lifecycle-mapping.md).

## Slash Commands

### Not sure which command to run?

| Command | Purpose |
|---------|---------|
| `/devspark-next` | Detect where you are in the lifecycle and run the single next step (after one confirmation) |

### Core Workflow

| Command | Purpose |
|---------|---------|
| `/devspark-constitution` | Establish project principles and guidelines |
| `/devspark-specify` | Define what you want to build (requirements & user stories) |
| `/devspark-plan` | Create a technical implementation plan |
| `/devspark-tasks` | Break the plan into actionable task lists |
| `/devspark-implement` | Update code, tests, and current knowledge; verify; record test evidence so the delta stays validate-able in `.devspark.work/` |
| `/devspark-create-pr` | Draft or update a pull request from the durable delta |
| `/devspark-update-pr` | Refresh an existing pull request description from the current branch delta |

### Constitution-Powered (no spec required)

| Command | Purpose |
|---------|---------|
| `/devspark-pr-review` | [Constitution-based PR review](site/src/guides/review-and-audit.md) |
| `/devspark-address-pr-review` | Apply PR review fixes with mandatory commit isolation gates |
| `/devspark-site-audit` | [Comprehensive codebase audit](site/src/guides/review-and-audit.md) |
| `/devspark-explain` | [Trace "how is X done?" against code and knowledge, fixing drift as it's found](site/src/guides/knowledge-management.md) |
| `/devspark-quickfix` | Lightweight workflow for bug fixes |
| `/devspark-critic` | [Adversarial risk analysis](site/src/guides/planning-review.md) |
| `/devspark-planning-review` | Analyze + conditional Critic + Judge: one bounded planning decision |
| `/devspark-verify` | Empirical proof gate for declared verification modes |
| `/devspark-release` | Verify the durable Git delta, sweep `.devspark.work/` retention, and archive completed work into `.archive/{YYYY-MM-DD}/` |
| `/devspark-evolve-constitution` | Propose constitution amendments |
| `/devspark-repo-story` | Generate narrative from commit history |
| `/devspark-commit-audit` | Analyze commit history for workflow, hygiene, and delivery signals |
| `/devspark-taskstoissues` | Explain why temporary tasks are not exported to durable issues |
| `/devspark-merge-from-main` | Script-first merge of remote `main`; the agent only resolves conflicts |
| `/devspark-workitem-review` | [Grade a named Azure DevOps work item against the shared standard](.knowledge/guides/azure-devops-work-tracking.md) (opt-in) |
| `/devspark-workitem-create` | Draft and, after confirmation, create a new Azure DevOps work item (opt-in) |

### Quality & Personalization

| Command | Purpose |
|---------|---------|
| `/devspark-clarify` | Ask structured questions to de-risk ambiguity |
| `/devspark-analyze` | Cross-artifact consistency check |
| `/devspark-checklist` | Generate quality validation checklists |
| `/devspark-personalize` | Create per-user command overrides |
| `/devspark-discover-constitution` | Generate a constitution from existing code |
| `/devspark-upgrade` | Pull latest DevSpark prompts into your project |

`/devspark-release` is the sole command that sweeps `.devspark.work/` retention and archives
completed work into `.archive/{YYYY-MM-DD}/`. It runs the `release-archive` script
(`plan`, `apply`, `validate`): moves are journaled in a manifest, never overwrite archived files,
stay resumable, and anything ambiguous is reported for a decision instead of moved.

### Multi-App (Optional)

| Command | Purpose |
|---------|---------|
| `/devspark-add-application` | Register a new application in the multi-app registry |
| `/devspark-list-applications` | Display all registered applications |
| `/devspark-validate-registry` | Validate registry schema, references, and consistency |

See [site/src/index.md](site/src/index.md#command-categories) for full command details.

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

1. **Create a registry** at `.devspark.work/devspark.registry.json` — or run `/devspark-add-application` to create one interactively
2. **Assign profiles** — reusable rule bundles (e.g., `api-profile`, `web-profile`) that apps inherit
3. **Scope commands** — use `--app <id>` to target a specific application, or `--repo-scope` for repo-wide operations
4. **App-local roots** — each app can have its own `.devspark.work/` and `.knowledge/` (including `.knowledge/guides/` for app-specific published guidance) directories plus an optional `app.json` manifest

### Multi-App Commands

| Command | Purpose |
|---------|---------|
| `/devspark-add-application` | Register a new application in the registry |
| `/devspark-list-applications` | Display all registered applications and profiles |
| `/devspark-validate-registry` | Validate registry schema, references, and consistency |

For the full specification, see the [Monorepo Guide](site/src/guides/monorepo-guide.md).

---

## Customization Without Risk

DevSpark separates replaceable framework files, temporary work, current truth, and published guidance:

```text
.devspark/                 ← Installation (removable, upgrade-safe)
├── defaults/commands/     ← Stock prompts
├── scripts/              ← Stock helper scripts
├── templates/            ← Spec/plan templates
└── VERSION  ← Installed version stamp

.devspark.work/            ← Temporary plans and operational work
├── specs/
├── commands/             ← Team command overrides
├── scripts/              ← Team script overrides (optional)
├── devspark.json         ← Repository configuration (optional)
├── devspark.registry.json ← Multi-app registry (optional)
└── {git-user}/commands/  ← Personal overrides

.knowledge/               ← Current authoritative truth
└── governance/constitution.md

.archive/                  ← Landing place for old work products, grouped by release
```

> **Multi-app layout** (optional): Each application may also have app-local `.devspark.work/` and `.knowledge/` (including `.knowledge/guides/`) roots.

**3-tier prompt resolution** (first match wins):

1. `.devspark.work/{git-user}/commands/` — Personal tweaks
2. `.devspark.work/commands/` — Team customizations
3. `.devspark/defaults/commands/` — Stock prompts

**2-tier script resolution** (first match wins):

1. `.devspark.work/scripts/` — Team script overrides (e.g., Azure DevOps adapter)
2. `.devspark/scripts/` — Stock scripts

There is no third ownership tier. If an organization wants a shared baseline in `.knowledge/guides/`, it manages that through its own repo practices; DevSpark still only writes to `.devspark/`.

Participant metadata uses these existing repository-owned artifacts when present.
It does not change how prompts or scripts are found; customization layers and
precedence are unchanged.

**Clean removal**: delete `.devspark/` and the agent skills (`.github/skills/devspark-*`, or your agent's equivalent); `.devspark.work/`, `.knowledge/`, and `.archive/` are left untouched.

---

## Supported AI Agents

DevSpark is agent-agnostic. Every agent below gets thin shims that resolve personal overrides, team overrides, and stock prompts through the same command contract.

| Agent | | Agent | | Agent | |
|-------|---|-------|---|-------|---|
| Claude Code | ✅ | Cursor | ✅ | Gemini CLI | ✅ |
| GitHub Copilot | ✅ | Codex CLI | ✅ | Windsurf | ✅ |
| Amp | ✅ | Roo Code | ✅ | Kilo Code | ✅ |
| Auggie CLI | ✅ | opencode | ✅ | Qwen Code | ✅ |
| SHAI | ✅ | Amazon Q | ⚠️ | IBM Bob | ✅ |
| CodeBuddy | ✅ | Qoder CLI | ✅ | Antigravity | ✅ |

Install each agent from your organization-approved software channel; DevSpark intentionally links to no third-party sites.

---

## Learn More

| Topic | Link |
|-------|------|
| How it works | [how-it-works.md](site/src/get-started/how-it-works.md) |
| Quickstart | [quickstart.md](site/src/get-started/quickstart.md) |
| Constitution guide | [constitution-guide.md](site/src/guides/constitution-guide.md) |
| Upgrading | [upgrade.md](site/src/get-started/upgrade.md) |
| Planning review | [planning-review.md](site/src/guides/planning-review.md) |
| PR review and site audit | [review-and-audit.md](site/src/guides/review-and-audit.md) |
| Knowledge and explain | [knowledge-management.md](site/src/guides/knowledge-management.md) |
| Command catalog | [prompt-lifecycle-mapping.md](site/src/guides/prompt-lifecycle-mapping.md) |

---

## Prerequisites

- **Any OS** (Linux / macOS / Windows)
- A [supported AI coding agent](#supported-ai-agents)
- Git (recommended)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Acknowledgements

DevSpark is maintained by the Make Bold Solutions engineering community.

A [Make Bold Solutions](https://makeboldsolutions.com) project, part of the [Make Bold Spark](https://makeboldspark.com) family.

## License

MIT — see [LICENSE](./LICENSE).
