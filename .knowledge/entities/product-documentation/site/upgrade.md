# Upgrade DevSpark

## Current Release

[![Current Release](https://img.shields.io/github/v/release/markhazleton/devspark?label=current%20release)](https://github.com/markhazleton/devspark/releases/latest)

**Current version:** [v4.2.0](https://github.com/markhazleton/devspark/releases/tag/v4.2.0)

DevSpark upgrades are quickstart-driven. Re-run the same quickstart prompt used
for installation in the target repository.

## Upgrade Flow

1. Open your AI coding assistant in the target repository.
2. Paste the matching quickstart prompt from `quickstart/`.
3. Ask the agent to run the version check and preview the upgrade plan.
4. Approve the plan.
5. Let the agent refresh framework-owned files under `.devspark/` and verify
   the `.knowledge` current-truth scaffold.

The upgrade must preserve authored repository-owned `.knowledge/` content. It
may refresh stock prompts, helper scripts, templates, schemas, skills, agent
shims, and `.devspark/VERSION`. It may also create missing `.knowledge/entities/`
and `.knowledge/ontology/` scaffold files, regenerate generated ontology
reports, and assimilate reviewed `.documentation/` intake.

## Repair Flow

Use the same quickstart prompt. Missing stock prompts, scripts, templates,
schemas, skills, or shims are repaired by re-fetching the current release
assets. Missing knowledge scaffold files are repaired without overwriting
authored current-truth documents.

## Not Supported

Any separate DevSpark terminal installer, updater, or repair command is not a
supported maintenance path. Keep all installation, upgrade, and repair behavior
inside the quickstart prompts.
