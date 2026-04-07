# DevSpark Implementation Lifecycle

This guide defines the recommended DevSpark lifecycle for teams.

Primary approach: prompt-first workflows through your AI agent using remote prompt files.
Advanced option: CLI automation when you explicitly want terminal-driven operations.

## Lifecycle at a Glance

1. Bootstrap with quickstart prompt (no CLI)
2. Run the implementation workflow (`/devspark.constitution` -> `/devspark.specify` -> `/devspark.plan` -> `/devspark.tasks` -> `/devspark.implement`)
3. Maintain with the remote upgrade prompt (no CLI)
4. Use CLI only for advanced automation

## 1. Bootstrap (Primary)

Open your AI agent in the target repository and run the matching quickstart prompt:

- Copilot: `@workspace Follow the instructions at https://raw.githubusercontent.com/markhazleton/devspark/main/quickstart/devspark_quickstart_copilot.md`
- Claude Code: `Follow the instructions at https://raw.githubusercontent.com/markhazleton/devspark/main/quickstart/devspark_quickstart_claudecode.md`
- Cursor: `Follow the instructions at https://raw.githubusercontent.com/markhazleton/devspark/main/quickstart/devspark_quickstart_cursor.md`
- Other agents: `Follow the instructions at https://raw.githubusercontent.com/markhazleton/devspark/main/quickstart/devspark_quickstart_generic.md`

The quickstart prompt installs stock framework files into `.devspark/` and preserves project work in `.documentation/`.

This is the standard installation path for DevSpark.

## 2. Implement Features

After bootstrap, run the standard implementation lifecycle in chat:

1. `/devspark.constitution`
2. `/devspark.specify`
3. `/devspark.clarify` (optional but recommended)
4. `/devspark.plan`
5. `/devspark.tasks`
6. `/devspark.analyze` and `/devspark.critic` (optional quality gates)
7. `/devspark.implement`

### Multi-App Workflows (Optional)

If your repository contains multiple applications, you can scope any command to a specific application:

- Use `--app <id>` with any command to target a specific application
- Use `--repo-scope` for repository-wide operations
- Run `/devspark.add-application` to register new applications in the multi-app registry

Multi-app support is entirely optional. Single-application repositories use the standard workflow above with no changes.

## 3. Upgrade (Primary)

Use the remote upgrade prompt in chat (no CLI required):

- `https://raw.githubusercontent.com/markhazleton/devspark/main/templates/commands/upgrade.md`

Recommended cadence:

1. Run dry-run first
2. Review proposed stock changes
3. Apply upgrade

Upgrade behavior:

- Updates stock framework files in `.devspark/`
- Preserves team and personal customizations in `.documentation/`

This is the standard update path for DevSpark.

## 4. Version Stamping Rules

Quickstart and upgrade flows must keep `.devspark/VERSION` authoritative.

- The `version:` value must be the latest DevSpark semantic version (`X.Y.Z`)
- Do not write `quickstart` as a version value
- If missing or invalid, treat installed version as unknown and refresh from latest

## 5. CLI (Advanced Only)

Use CLI if you need terminal-driven automation, scripting, or CI-like control.

- Install/update CLI: `uv tool install devspark-cli --force --from git+https://github.com/markhazleton/devspark.git`
- Upgrade project via CLI: `devspark upgrade`

If your team does not need CLI automation, stay with prompt-first quickstart and prompt-first upgrade.
