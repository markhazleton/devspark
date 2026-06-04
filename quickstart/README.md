# DevSpark Quickstart Guides

Install DevSpark into any repository by pointing your AI agent at the right quickstart file. No CLI required.

## Pick Your Agent

| Agent | Quickstart File |
|---|---|
| **GitHub Copilot** | [`devspark_quickstart_copilot.md`](devspark_quickstart_copilot.md) |
| **Claude Code** | [`devspark_quickstart_claudecode.md`](devspark_quickstart_claudecode.md) |
| **Cursor** | [`devspark_quickstart_cursor.md`](devspark_quickstart_cursor.md) |
| **Codex** | [`devspark_quickstart_codex.md`](devspark_quickstart_codex.md) |
| **Any other agent** | [`devspark_quickstart_generic.md`](devspark_quickstart_generic.md) |

## How It Works

1. Open a chat with your AI agent in the target repository
2. Paste the URL to the raw quickstart file, or copy its contents into the chat
3. The agent detects the current OS (for plan preview only), then pulls and installs the full DevSpark framework payload — **both** PowerShell and Bash script sets are always installed regardless of OS
4. For upgrades, run the [remote upgrade prompt](https://raw.githubusercontent.com/markhazleton/devspark/main/templates/commands/upgrade.md) (no CLI required)
5. Use CLI only if you want advanced automation (`devspark upgrade`)

After installation, start new work with `/devspark.specify`. It now classifies the request as a one-off fix, quick spec, or full spec and asks the user to confirm the route before artifacts are created.

If you also install the optional CLI, you can validate the local environment with `devspark doctor` and run declarative harness workflows with `devspark harness run`, `devspark harness validate`, and `devspark harness trace`.

The quickstart guides can handle fresh installs, legacy migrations, version-based upgrades, and repair of incomplete framework installs when expected stock files are missing.

## Upgrade Paths

- Basic (recommended): remote upgrade prompt
- Paste this [upgrade prompt URL](https://raw.githubusercontent.com/markhazleton/devspark/main/templates/commands/upgrade.md) into your agent chat in the target repo
- Tell the agent to run a dry run first, then apply the upgrade.
- Advanced (optional): CLI
- Run `devspark upgrade` if you have CLI tooling installed and prefer terminal-driven upgrades.

Example (Copilot):

```text
@workspace Follow the instructions at https://raw.githubusercontent.com/markhazleton/devspark/main/quickstart/devspark_quickstart_copilot.md
```

Example (Claude Code):

```text
/devspark Follow the instructions at https://raw.githubusercontent.com/markhazleton/devspark/main/quickstart/devspark_quickstart_claudecode.md
```

Example (Codex):

```text
Follow the instructions at https://raw.githubusercontent.com/markhazleton/devspark/main/quickstart/devspark_quickstart_codex.md
```

## What Gets Installed

- **`.devspark/`** — Framework files (stock prompts, templates, both PowerShell and Bash scripts). Safe to delete or upgrade.
- **`.documentation/`** — Your project artifacts (constitution, specs, decisions). Seeded during initial setup and preserved afterward.
- **`agents-registry.json`** — Shared agent metadata used by context-generation and packaging workflows.
- **Agent shims** — Platform-specific files that wire `/devspark.*` commands to personal, team, and stock prompt resolution.

Framework upgrades only write to `.devspark/`. `.documentation/` remains repository-owned work product after the initial quickstart seeds project artifacts.

## Multi-App Support (Optional)

If your repository contains multiple applications with different platforms or governance rules, each quickstart includes an **optional** multi-app section at the end. Single-application repositories can skip this entirely — no registry or extra configuration is needed.

To opt in, run `/devspark.add-application` after installation to create a registry at `.documentation/devspark.json`.

## Migration Support

Each quickstart automatically detects and migrates from:

- **Legacy `.specify/` layout** (`.specify/` directory) → moves user content to `.documentation/`, renames old dir to `.specify.old/`
- **Pre-separation DevSpark** (`.documentation/defaults/`) → moves framework files to `.devspark/`
- **Legacy root-level dirs** (`memory/`, `specs/`) → consolidates into `.documentation/`

No data is deleted — old directories are renamed with `.old` suffix as backups.
