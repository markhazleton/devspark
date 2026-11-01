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

## Upgrading to 9.4

DevSpark 9.4 needs no conversion script, and existing work is never migrated into the new format. Run your agent's [quickstart](quickstart.md) in Update Mode, or install it fresh. Afterwards:

- **New work** starts with `/devspark-specify` on a `NNN-work-*` branch, with no route question and no planning file. In a later session `/devspark-next` resumes it.
- **Active v9.3 work continues as it was.** A full-spec bundle keeps its plan, tasks and Planning Review route, a quick spec continues to implementation, and an open quickfix record continues to `/devspark-implement`. `/devspark-next` resolves each one from its recorded files, and nothing is rewritten.
- **Retired creation paths.** DevSpark no longer creates a new full-spec or quick-spec bundle. `create-new-feature.sh` and `.ps1` are no longer shipped, and `new-branch` accepts only `--type work` and `--type fix`; any other type exits `1` with `type must be one of: fix, work` and creates nothing. An upgrade does not delete copies already in `.devspark/scripts/`. No 9.4 command calls them, so remove them whenever convenient. A team override or CI step that calls them, or passes `spec` or `quick` to `new-branch`, must be rebuilt on the current stock `/devspark-specify`. `/devspark-upgrade` lists such an override as orphaned.
- **`create-pr` exit codes.** `create-pr.ps1` create and update mode now exit `1` on a refusal or failure and `0` only on `status: ok`, as `create-pr.sh` already did. The JSON output is unchanged, so a PowerShell caller that treated exit `0` as "the script ran" should read the JSON on a non-zero exit too.
- **Required obligations need evidence.** When `work.md` declares `## Required Obligations`, delivery is refused until each entry is checked with its `Authority:` and a traceable reference to the satisfying evidence or decision, such as a repository path, commit, review or approval id, or link. See [Assurance as needed](how-it-works.md#assurance-as-needed).
- **Drift.** `/devspark-upgrade --dry-run` reports a stale version stamp, missing or orphaned skills, and overrides that shadow a changed stock command. Re-run the quickstart in Repair Mode to restore missing framework files.
- **Rollback.** The upgrade changes only framework-owned files, so revert the commit that applied it to return to 9.3. Your work, Knowledge and overrides are untouched either way.

## Upgrading to 9.3

DevSpark 9.3 needs no conversion script and no rewrite of existing specifications, tasks or Knowledge. Run your agent's [quickstart](quickstart.md) in Update Mode. Existing artifacts stay readable:

- Per-requirement Knowledge stubs (`knowledge/fr-NNN.md`) and `code_ref` / `knowledge_ref` task suffixes from earlier versions are ignored, not rejected, and are not required for archiving. Delete them whenever convenient.
- `last_verified` stays valid on Knowledge documents and is now optional. A date alone never blocks a change.
- `index.json` and `coverage.json` are optional build output. If your CI or scripts compare them, switch to `python scripts/build_knowledge_index.py --repo-root . --check`, which now only confirms the Knowledge builds.
- Scripts that read `/devspark-release` context (`KNOWLEDGE_INDEX_PRESENT`, `KNOWLEDGE_INDEX_CURRENT`) should read `KNOWLEDGE_BUILDS`, and scripts that read the `INDEX_FRESH` field of `explain-context` output should drop it. The `/devspark-create-pr` readiness result is now `ready`, `not-applicable`, `unknown` or `blocked`, and `check-planning-references` no longer emits `linkage_findings`.
- `validate-knowledge-coverage.sh` and `.ps1` are no longer shipped. An upgrade does not delete copies already in `.devspark/scripts/`; no 9.3 command calls them, so remove them (and any CI step that invokes them) whenever convenient.

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
