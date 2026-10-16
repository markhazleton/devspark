# DevSpark Quickstart Guides

<!-- DevSpark — © 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com -->

Install DevSpark into any repository by pointing your AI agent at the right quickstart file. No CLI required.

## Pick Your Agent

| Agent | Quickstart File |
|---|---|
| **GitHub Copilot** | [`devspark_quickstart_copilot.md`](devspark_quickstart_copilot.md) |
| **Claude Code** | [`devspark_quickstart_claudecode.md`](devspark_quickstart_claudecode.md) |
| **Cursor** | [`devspark_quickstart_cursor.md`](devspark_quickstart_cursor.md) |
| **Codex** | [`devspark_quickstart_codex.md`](devspark_quickstart_codex.md) |
| **Antigravity** | [`devspark_quickstart_antigravity.md`](devspark_quickstart_antigravity.md) |
| **Any other agent** | [`devspark_quickstart_generic.md`](devspark_quickstart_generic.md) |

## How It Works

1. Open a chat with your AI agent in the target repository
2. Paste the URL to the raw quickstart file, or copy its contents into the chat
3. *(Optional but recommended)* **Preview first** — before authorizing any changes, use the **Preview Prompt** section at the top of every quickstart to read the exact instructions and command prompts, or ask the agent for a read-only dry run. Nothing is written until you say `proceed`.
4. The agent detects the current OS (for plan preview only), then pulls and installs the full DevSpark framework payload — **both** PowerShell and Bash script sets are always installed regardless of OS
5. For upgrades, re-run the same quickstart guide URL — it detects the existing install and runs a manifest-driven [Update Mode](https://dev.makeboldspark.com/raw/quickstart/devspark_quickstart_copilot.md)

> ⚠️ **Avoid stale installs.** Webpage-fetch tools cache `dev.makeboldspark.com` URLs aggressively and can hand the agent an **old version** of the guide, manifest, and framework files. Each quickstart now opens with **Step 0**, which forces the agent to re-fetch the guide and every file via cache-busted terminal commands. If your agent appears to install an outdated version, tell it: *"Re-run Step 0 — re-fetch the guide and manifest via a terminal command with a `?cb=<timestamp>` cache-buster, not a webpage fetch."*

After installation, start new work with `/devspark-specify`. It now classifies the request as a one-off fix, quick spec, or full spec and asks the user to confirm the route before artifacts are created.

DevSpark commands start only when you type them as slash commands, with the leading `/` (for example `/devspark-create-pr`). The agent does not start them on its own, so typing the bare name or asking the agent to "run devspark-create-pr" sends plain text and the command skill never loads.

The quickstart guides can handle fresh installs, version-based upgrades, and repair of incomplete framework installs when expected stock files are missing.

## Upgrade Paths

- Re-run your agent's quickstart guide — paste your agent's [quickstart guide URL](https://dev.makeboldspark.com/raw/quickstart/devspark_quickstart_copilot.md) into your agent chat in the target repo — it detects the existing install and runs a manifest-driven upgrade
- Tell the agent to run a dry run first, then apply the upgrade.

Example (Copilot):

```text
@workspace Follow the instructions at https://dev.makeboldspark.com/raw/quickstart/devspark_quickstart_copilot.md
```

Example (Claude Code):

```text
/devspark Follow the instructions at https://dev.makeboldspark.com/raw/quickstart/devspark_quickstart_claudecode.md
```

Example (Codex):

```text
Follow the instructions at https://dev.makeboldspark.com/raw/quickstart/devspark_quickstart_codex.md
```

## What Gets Installed

- **`.devspark/`** — Framework files (stock prompts, templates, both PowerShell and Bash scripts). Safe to delete or upgrade.
- **`.devspark.work/`** — Temporary plans, gates, configuration, registries, and overrides.
- **`.knowledge/`** — Current authoritative technical and governance truth, plus published user-facing guidance under `.knowledge/guides/`.
- **`.archive/`** — Landing place for all old work products, grouped by release.
- **`agents-registry.json`** — Shared agent metadata used by context-generation and packaging workflows.
- **Agent entry points** — Platform-specific files that wire `/devspark-*` commands to personal, team, and stock prompt resolution. For GitHub Copilot they are native Agent Skills under `.github/skills/`; upgrades retire the 8.x dotted entry points once, safely, with edited files quarantined.

Framework upgrades only replace `.devspark/`. The `.devspark.work/`, `.knowledge/`, and
`.archive/` roots remain repository-owned.

## Multi-App Support (Optional)

If your repository contains multiple applications with different platforms or governance rules, each quickstart includes an **optional** multi-app section at the end. Single-application repositories can skip this entirely — no registry or extra configuration is needed.

To opt in, run `/devspark-add-application` after installation to create a registry at `.devspark.work/devspark.registry.json`.
