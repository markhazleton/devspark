# Documentation

Current Release: v2.3.0

This folder contains the documentation source files for DevSpark, built using [DocFX](https://dotnet.github.io/docfx/).

## Building Locally

To build the documentation locally:

1. Install DocFX:

   ```bash
   dotnet tool install -g docfx
   ```

2. Build the documentation:

   ```bash
   cd .documentation
   docfx docfx.json --serve
   ```

3. Open your browser to `http://localhost:8080` to view the documentation.

## Structure

- `docfx.json` - DocFX configuration file
- `toc.yml` - Table of contents / sidebar navigation
- `index.md` - Main homepage and command reference
- `quickstart.md` - Bootstrap and first-feature walkthrough
- `implementation-lifecycle.md` - Full workflow with anti-patterns guide
- `installation.md` - Advanced CLI alternatives
- `harness-engineering.md` - Harness runtime commands, adapters, artifacts, and engineering model
- `upgrade.md` - Prompt-first and CLI upgrade steps
- `constitution-guide.md` - Constitution creation, structure, and best practices
- `monorepo-guide.md` - Optional multi-app monorepo support
- `pr-review-usage.md` - PR review command guide
- `site-audit-usage.md` - Site audit command guide
- `critic-usage.md` - Critic command guide
- `harvest-usage.md` - Harvest command guide
- `checklist-usage.md` - Checklist command guide
- `repo-story-usage.md` - Repo story command guide
- `faq.md` - Frequently asked questions
- `about.md` - Design philosophy and project overview
- `AGENTS.md` - AI agent integration architecture
- `_site/` - Generated documentation output (ignored by git)

## Deployment

Documentation is automatically built and deployed to GitHub Pages when changes are pushed to the `main` branch. The workflow is defined in `.github/workflows/docs.yml`.
