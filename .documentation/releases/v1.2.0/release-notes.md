# Release Notes: v1.2.0

## Release Metadata

- **Version**: v1.2.0
- **Release Date**: 2026-03-07
- **Previous Version**: v1.1.0

## Highlights

This release introduces version tracking for consumer projects. Every time a project runs `devspark init` or `devspark upgrade`, a `.documentation/DEVSPARK_VERSION` stamp file is written with the installed version, date, and AI agent key. This gives AI commands and scripts a single, offline source of truth for the installed version — no network call required.

A new `/devspark.upgrade` AI command guides agents through the full upgrade workflow: reading the version stamp, comparing to the latest release, classifying framework-owned vs. user-owned files, identifying stale paths, running the upgrade, and verifying the stamp was updated.

The `/devspark.site-audit` command now includes a **DevSpark Version** check (Step 4) with structured finding codes (VER1–VER5) covering missing stamps, outdated versions, and stale pre-migration paths.

## New Features

### DEVSPARK_VERSION stamp

`devspark init` and `devspark upgrade` now write `.documentation/DEVSPARK_VERSION` after every successful install or upgrade. The file records the installed version, install date, and agent key.

### /devspark.upgrade AI command

New `templates/commands/upgrade.md` — a dedicated AI agent command that reads the version stamp, compares to the latest release, classifies files as framework-owned vs. user-owned, identifies stale paths, runs `devspark upgrade`, and verifies the stamp was updated after completion.

### Version check in /devspark.site-audit

Audit reports now include a **DevSpark Version** section (Step 4) with VER1–VER5 finding codes for missing stamps, outdated versions, and stale pre-migration paths.

### Release workflow version bump step

`templates/commands/release.md` now includes Step 9 — *Bump Version in Source Files* — which instructs maintainers to update `pyproject.toml`, verifies three-way consistency (pyproject / CHANGELOG / git tag), and explains that consumer projects receive the new stamp automatically on their next `devspark upgrade`.

### `DEVSPARK_VERSION_PATH` and `INSTALLED_VERSION` in release-context scripts

Both `release-context.ps1` and `release-context.sh` now surface the consumer project's installed version in JSON and human-readable output.

### `read_version_stamp()` helper

New Python helper in the CLI that reads and parses `.documentation/DEVSPARK_VERSION` back as a dict; used in the post-upgrade summary to display the newly written version.

## Upgrade Guide

Run `devspark upgrade` in your consumer project to receive the version stamp automatically.
