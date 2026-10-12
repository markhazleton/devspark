# Upgrade DevSpark

Upgrades refresh framework-owned files while preserving repository-owned work and truth.

## Ownership Boundary

| Root | Upgrade behavior |
|---|---|
| `.devspark/` | Refresh from the versioned distribution manifest |
| `.devspark.work/` | Preserve active plans, overrides, configuration, and operational work products |
| `.knowledge/` | Preserve all current authoritative knowledge, including published guidance under `.knowledge/guides/` |
| `.archive/` | Preserve; never read, listed, or modified by upgrade |

Use the agent-specific [quickstart](quickstart.md) as the canonical manifest-driven install and upgrade procedure. Run `/devspark-upgrade --dry-run` to inspect a local upgrade before applying it. The four roots are described in [How It Works](how-it-works.md#four-roots).

## Upgrading from 8.x

DevSpark 9.0 is a breaking release: every skill is invoked with a `/devspark-<command>` slash command (for example `/devspark-plan`), and GitHub Copilot installs each one as a native Agent Skill under `.github/skills/`. The 8.x entry points (`.github/agents/devspark.<command>.agent.md` and `.github/prompts/devspark.<command>.prompt.md` for Copilot, or `devspark.<command>.<ext>` in another agent's commands directory) would list every skill twice, so the upgrade retires them. There is no dotted alias, fallback, or compatibility mode.

Run your agent's [quickstart](quickstart.md). When it detects an 8.x install it:

1. installs the 9.0 skill entry points (native Agent Skills for Copilot, platform-specific command or prompt shims for other agents) first, and never blocks that install on a retirement problem;
2. lists exactly what it will retire and asks **once** for confirmation, and changes nothing without a yes;
3. deletes unmodified managed entry points, and prunes only the managed `chat.promptFilesRecommendations` keys in `.vscode/settings.json`;
4. moves any entry point you edited, byte-for-byte, to `.devspark.work/migration/8.x-entry-points/` instead of deleting it, and reports it;
5. reports any conflict, such as an existing `devspark-<command>` skill folder that is not DevSpark's, for you to rename or remove. It never overwrites it.

Your customizations are not touched. `.devspark.work/commands/` (team) and `.devspark.work/{git-user}/commands/` (developer) keep resolving before the distributed default, and `.knowledge/`, `.archive/` and your active plans are left alone. To keep an edit from a quarantined entry point, recreate it as a customization in `.devspark.work/commands/devspark.<command>.md` (team) or `.devspark.work/{git-user}/commands/devspark.<command>.md` (developer).

Running the upgrade again lists nothing and changes nothing. The upgrade leaves no marker or flag behind.

## After Upgrade

Check that:

- `.devspark/VERSION` reports the installed version;
- all stock skills have `/devspark-<command>` slash-command entry points (for GitHub Copilot, `.github/skills/devspark-<command>/SKILL.md`);
- no unmodified 8.x entry point remains, and anything you edited is in `.devspark.work/migration/8.x-entry-points/`;
- team and personal overrides still resolve before stock files;
- overrides contain no legacy root references;
- both PowerShell and Bash script adapters are present;
- `.devspark/templates/skills/` is complete;
- `.devspark.work/devspark.user.json` is ignored by Git;
- the constitution resolves from `.knowledge/governance/constitution.md`.

Never copy repository-owned files into `.devspark/` to make an upgrade pass. Fix path resolution or
migrate ownership explicitly.
