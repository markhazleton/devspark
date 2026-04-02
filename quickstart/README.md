# DevSpark Quickstart Guides

Install DevSpark into any repository by pointing your AI agent at the right quickstart file. No CLI required.

## Pick Your Agent

| Agent | Quickstart File |
|---|---|
| **GitHub Copilot** | [`devspark_quickstart_copilot.md`](devspark_quickstart_copilot.md) |
| **Claude Code** | [`devspark_quickstart_claudecode.md`](devspark_quickstart_claudecode.md) |
| **Cursor** | [`devspark_quickstart_cursor.md`](devspark_quickstart_cursor.md) |
| **Any other agent** | [`devspark_quickstart_generic.md`](devspark_quickstart_generic.md) |

## How It Works

1. Open a chat with your AI agent in the target repository
2. Paste the URL to the raw quickstart file, or copy its contents into the chat
3. The agent will ask a few questions about your project, then pull and install all DevSpark prompts

Example (Copilot):

```text
@workspace Follow the instructions at https://raw.githubusercontent.com/markhazleton/devspark/main/quickstart/devspark_quickstart_copilot.md
```

Example (Claude Code):

```text
/devspark Follow the instructions at https://raw.githubusercontent.com/markhazleton/devspark/main/quickstart/devspark_quickstart_claudecode.md
```

## What Gets Installed

- **`.devspark/`** — Framework files (stock prompts, templates, scripts). Safe to delete or upgrade.
- **`.documentation/`** — Your project artifacts (constitution, specs, decisions). Never touched by DevSpark.
- **Agent shims** — Platform-specific files that wire `/devspark.*` commands to the 3-tier resolution system.

## Migration Support

Each quickstart automatically detects and migrates from:

- **Spec Kit** (`.specify/` directory) → moves user content to `.documentation/`, renames old dir to `.specify.old/`
- **Pre-separation DevSpark** (`.documentation/defaults/`) → moves framework files to `.devspark/`
- **Legacy root-level dirs** (`memory/`, `specs/`) → consolidates into `.documentation/`

No data is deleted — old directories are renamed with `.old` suffix as backups.
