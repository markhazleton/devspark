# Upgrade DevSpark

## Current Release

[![Current Release](https://img.shields.io/github/v/release/markhazleton/devspark?label=current%20release)](https://github.com/markhazleton/devspark/releases/latest)

**Current version:** [v4.0.0](https://github.com/markhazleton/devspark/releases/tag/v4.0.0)

DevSpark upgrades are quickstart-driven. Re-run the same quickstart prompt used
for installation in the target repository.

## Upgrade Flow

1. Open your AI coding assistant in the target repository.
2. Paste the matching quickstart prompt from `quickstart/`.
3. Ask the agent to run the version check and preview the upgrade plan.
4. Approve the plan.
5. Let the agent refresh framework-owned files under `.devspark/`.

The upgrade must preserve repository-owned `.documentation/` and `.knowledge/`
content. It may refresh stock prompts, helper scripts, templates, schemas,
skills, agent shims, and `.devspark/VERSION`.

## Repair Flow

Use the same quickstart prompt. Missing stock prompts, scripts, templates,
schemas, skills, or shims are repaired by re-fetching the current release assets.

## Not Supported

Any separate DevSpark terminal installer, updater, or repair command is not a
supported maintenance path. Keep all installation, upgrade, and repair behavior
inside the quickstart prompts.
