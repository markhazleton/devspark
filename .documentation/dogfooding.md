# Dogfooding DevSpark

How we set up the DevSpark source repository to use its own spec-driven workflow — always running against the latest source version of every prompt and script.

## The Problem

DevSpark's normal install process copies stock prompts from `templates/commands/` into `.devspark/defaults/commands/` with a `devspark.` prefix. Agent shims then resolve through a 3-tier override chain:

1. `.documentation/{user}/commands/devspark.{name}.md` (personal override)
2. `.documentation/commands/devspark.{name}.md` (team override)
3. `.devspark/defaults/commands/devspark.{name}.md` (stock default)

This works great for consumer repos, but in the DevSpark source repo it creates two problems:

- **Stale copies** — Every prompt edit in `templates/commands/` would need to be mirrored to `.devspark/defaults/commands/`. Forget once and you're testing yesterday's prompt.
- **Override shadowing** — Personal or team overrides would shadow the source files you're actively developing, hiding bugs in the actual product.

## The Solution: Source-Direct Shims

Instead of copying files, every agent shim points directly at the source:

### GitHub Copilot (`.github/agents/`)

```markdown
---
name: devspark.specify
description: Create or update the feature specification...
---

Read and follow the instructions in `templates/commands/specify.md` exactly.
```

No 3-tier resolution. No `.devspark/defaults/commands/` directory. The shim reads the source file directly.

### Claude Code (`.claude/commands/`)

```markdown
Read and follow the instructions in `templates/commands/specify.md` exactly.

User input: $ARGUMENTS
```

Same pattern — delegates to the source template and passes through user arguments.

### Scripts

The `.vscode/settings.json` auto-approves scripts from `scripts/` (the source location), not `.devspark/scripts/`:

```json
{
    "chat.tools.terminal.autoApprove": {
        "scripts/bash/": true,
        "scripts/powershell/": true
    }
}
```

## What We Skipped

The following directories are **not needed** in the source repo:

| Directory | Why it's absent |
|-----------|----------------|
| `.devspark/defaults/commands/` | Shims point at `templates/commands/` directly |
| `.devspark/scripts/` | Scripts live at `scripts/` (the source location) |
| `.devspark/templates/` | Templates live at `templates/` (the source location) |

Only `.devspark/VERSION` and `.devspark/schemas/` exist — metadata that doesn't duplicate source content.

## Guard Clauses

Six commands are nonsensical in the source repo. Their shims display a **STOP** message with an explanation and redirect:

| Command | Why blocked | Redirect |
|---------|-------------|----------|
| `upgrade` | You ARE the latest version by definition | Edit `CHANGELOG.md` and `.devspark/VERSION` directly |
| `personalize` | Overrides would shadow source prompts | Edit `templates/commands/{name}.md` directly |
| `add-application` | DevSpark is not a multi-app monorepo | Use `tests/fixtures/` or `examples/todo-app/` to test |
| `list-applications` | Same as above | Same as above |
| `discover-constitution` | The constitution already exists as the authoritative source | Use `evolve-constitution` or edit directly |
| `archive` | Deprecated alias | Use `harvest` instead |

The remaining 21 commands work normally and resolve to source.

## Steps We Took

1. **Removed duplicate framework files** — Deleted `.devspark/defaults/commands/`, `.devspark/scripts/`, and `.devspark/templates/` which were copies of the source
2. **Created Copilot agent shims** — 27 files in `.github/agents/devspark.*.agent.md`, each pointing at `templates/commands/{name}.md`
3. **Created Copilot prompt shims** — 27 companion files in `.github/prompts/devspark.*.prompt.md`
4. **Created Claude Code commands** — 27 files in `.claude/commands/devspark.*.md` with `$ARGUMENTS` passthrough
5. **Added guard clauses** — 6 commands blocked with STOP messages in both Copilot and Claude shims
6. **Updated `CLAUDE.md`** — Added dogfooding note explaining source-direct resolution
7. **Updated `.gitignore`** — Added `!.vscode/settings.json` exception so Copilot settings are tracked
8. **Wrote `.devspark/VERSION`** — Stamped with `method: source-dogfood`

## The Result

When you type `@devspark.specify` (Copilot) or `/devspark.specify` (Claude Code), the agent reads `templates/commands/specify.md` — the exact file you're editing. Change a prompt, use it immediately, see the result. True dogfooding.

## Consumer Repos vs. Source Repo

| Aspect | Consumer repo | DevSpark source repo |
|--------|--------------|---------------------|
| Stock commands | `.devspark/defaults/commands/` (copied) | `templates/commands/` (source) |
| Scripts | `.devspark/scripts/` (copied) | `scripts/` (source) |
| Templates | `.devspark/templates/` (copied) | `templates/` (source) |
| Override chain | 3-tier (personal → team → stock) | None — always source |
| Upgrade command | Refreshes `.devspark/` from latest release | Blocked — you are the source |
| Personalize command | Creates user override files | Blocked — edit source directly |
