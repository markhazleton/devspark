---
id: distribution-and-update-model
type: architecture
title: "Distribution and Update Model"
appliesTo:
  - azure-pipelines.yml
  - eng/release/create-release-packages.sh
  - eng/release/create-release-packages.ps1
  - agents-registry.json
  - templates/agents-registry.schema.json  - quickstart/devspark_quickstart_copilot.md
---

<!-- DevSpark — © 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com -->
<!-- markdownlint-disable MD025 -->

# Distribution and Update Model

DevSpark files never move directly from this source repository to a target repository. A
single Azure Pipeline publishes everything to one Azure Static Web App, and a target repo's
quickstart guide (or a downloaded zip) pulls from that published surface.

## Publish pipeline (this repo → Static Web App)

`azure-pipelines.yml` (see `README.md`/`ROOTS` conventions) triggers on every push to `main` **and**
on every `v*` tag — not tag pushes only. After test/lint/drift gates pass it:

1. Runs `eng/release/create-release-packages.sh <version>` to build one template zip per
   AI-agent/script-type combination under `.genreleases/`, using `agents-registry.json` as the
   source of truth for which agents exist and where their files land. `copy_relative_files` /
   direct `cp -r scripts/bash` and `cp -r scripts/powershell` calls copy the **entire** `scripts/`
   tree into each package's `.devspark/scripts/` — there is no per-file registration step, so any
   `.sh`/`.ps1` change under `scripts/` is automatically included in the next build with no extra
   wiring. Agents whose registry `release` entry uses `skills_dir` (Copilot) receive the committed
   `templates/consumer-skills/` copied byte-identically; every other agent receives hyphenated
   `devspark-<command>.<ext>` entry points whose resolution data paths stay dotted
   (`devspark.<command>.md`). The two `release` forms are mutually exclusive and no agent receives
   both.
2. Assembles the Static Web App payload with three sections: `/` (DocFX site), `/dist/{version}/`
   (the zips + `manifest.json`), and `/raw/` (the raw `templates/`, `scripts/`, `quickstart/`,
   `agents-registry.json` trees, served as individual files for prompt-first fetch).
3. Generates `manifest.json`'s `install` array via `build_install_index()`, which walks the same
   `templates/commands/*.md`, `templates/consumer-skills/*/SKILL.md`, `templates/**`, and
   `scripts/**` trees to produce `{source, dest, category}` entries. The closed category set is
   `command`, `skill`, `template`, `script` and `registry`; `skill` entries land at
   `.github/skills/devspark-<command>/SKILL.md`, and `consumer-skills/` is never mapped under
   `.devspark/templates`. This is the single source of truth both the zip packaging and the
   prompt-first quickstart flow are generated from, so they cannot drift apart.
4. Deploys the assembled payload via `AzureStaticWebApp@0`, **conditioned on the build not being a
   tag-triggered run** — a tag build skips the deploy step because the same commit's `main` push
   already deployed identical content; the tag only exists to pin a version number.

### Version resolution and "is the zip release-gated?"

The version used for a given build is **not tied to whether a tag exists**:

- If the triggering ref is `refs/tags/vX.Y.Z`, that tag is the version.
- Otherwise (an ordinary push to `main`), the version is read straight from `pyproject.toml`'s
  current `version` field.

Because the package-build and manifest-assembly steps run unconditionally on **every** triggering
push (not only tag pushes), and the deploy step's only exclusion is tag-triggered runs, a plain
merge to `main` — even one with no version bump, no CHANGELOG entry, and no tag — rebuilds and
redeploys `dist/{current-pyproject-version}/*.zip` and the `raw/` tree with whatever is on `main`
right now. If `pyproject.toml`'s version hasn't changed since the last publish, this **overwrites
the existing zip at that same version path** with the new content. A small script fix merged to
`main` therefore reaches the published surface (and any `--force`-refetching quickstart run) on the
very next pipeline run, independent of the formal `/devspark-release` versioning ceremony. Tagging
a release is what gives that specific point-in-time build a stable, permanent version number and
entry in `manifest.json`'s `versions` history — it is not what causes the publish to happen.

## Install/upgrade paths (Static Web App → target repo)

- **Prompt-first (primary).** The target repo's agent runs its quickstart guide, which fetches
  `manifest.json` (cache-busted, never via a webpage-fetch tool — the site aggressively caches),
  then loops every `manifest.install[]` entry, downloading `{raw_base}/{source}` and writing it to
  `{dest}` in the target repo. This is how individual command/template/script files physically land
  in a consumer repo.
- **Zip download.** A developer downloads and extracts
  `dist/{version}/devspark-template-{agent}-{scripts}-{version}.zip`, which already has the final
  `.devspark/` (and agent-specific entry point or skill) layout baked in — no manifest walk required.

Both paths write only to `.devspark/` and to the agent's own entry-point location
(`.github/skills/` for Copilot). `.devspark.work/`, `.knowledge/`, and `.archive/` are
repository-owned and must never be touched by install or upgrade (constitution, showstopper
severity). Migrating between major layouts is always an explicit, separately-run, human-confirmed
action, never automatic.

Observed host support for the Copilot skills: VS Code Insiders 1.142.0 with the built-in Copilot Chat
(local Windows). Skills are listed once each under `/devspark-<command>`, and text typed after the
command reaches the skill as the command's input. Older builds were not tested, so no minimum
version is claimed.

## 8.x entry point retirement (Update and Repair)

Moving a repository from 8.x to 9.0 changes every command from `/devspark.<cmd>` to
`/devspark-<cmd>`, so the dotted entry points an 8.x install wrote would list each command a second
time. Update and Repair therefore retire them in a step that follows the entry-point install, never
blocks it, and needs **one** human confirmation for the whole list.

- **Scope.** Only the agent's own 8.x file names for stock commands are examined
  (Copilot: `.github/agents/devspark.<cmd>.agent.md` and `.github/prompts/devspark.<cmd>.prompt.md`;
  other agents: `devspark.<cmd>.<ext>` in the agent's commands directory). The 8.x classes apply only
  when the installed major version is below 9. Orphan generated 9.0 entry points (a stock command that
  no longer exists) are retired on every run. Managed `chat.promptFilesRecommendations` entries
  (`devspark.<cmd>` keys) are pruned from `.vscode/settings.json`; user-added entries are left.
- **Recognition.** A file is an unmodified managed entry point only when its frontmatter is absent or
  limited to `description`, `handoffs`, `agent` and a `name` equal to its own `devspark.<cmd>`, and its
  body is exactly the generated package form or the quickstart-authored form (the placeholder may be
  `{{input}}`, `$ARGUMENTS` or `{{args}}`, bare or fenced; the `Where {git-user}` line is optional).
  Descriptions are free text. No hashes are used. Everything else is an edit.
- **Actions.** Unmodified files and orphans are deleted. Edited files are moved byte-identical to
  `.devspark.work/migration/8.x-entry-points/<file name>` (numeric suffix on collision, never
  overwriting) with a remedy to recreate the edit as a team or developer customization; this is the
  only write the procedure makes inside a repository-owned root and it only adds files. Foreign files
  and foreign `devspark-<cmd>` skill folders are left untouched and reported as conflicts.
- **Idempotence.** The step is stateless: no marker and no flag. The candidate rule alone decides, so
  repeat runs and interrupted runs converge on the same result.
- **Executable oracle.** `tests/legacy_retirement_oracle.py` encodes the same rule over the fixtures
  in `tests/fixtures/upgrade/`. It is test-only; no retirement script ships. The agent-executed
  procedure is demonstrated against that oracle on the fixture classes, not assumed to match.
- **Customization.** Developer, then team, then distributed default resolution is unchanged: the 9.0
  entry points resolve the same three layers, so a quarantined edit recreated as a customization takes
  effect through the existing precedence.
