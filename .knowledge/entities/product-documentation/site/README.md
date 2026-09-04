# Documentation

Current Release: [![Current Release](https://img.shields.io/github/v/release/markhazleton/devspark?label=current%20release)](https://github.com/markhazleton/devspark/releases/latest)

Current version: [v4.2.0](https://github.com/markhazleton/devspark/releases/tag/v4.2.0)

This folder contains the documentation source files for DevSpark, built using [DocFX](https://dotnet.github.io/docfx/).

## Building Locally

To build the documentation locally:

1. Install DocFX:

   ```bash
   dotnet tool install -g docfx
   ```

2. Build the documentation:

   ```bash
   cd .knowledge/entities/product-documentation/site
   docfx docfx.json --serve
   ```

3. Open your browser to `http://localhost:8080` to view the documentation.

   > "Current Release" on each page is a live badge pulled from the GitHub Releases API — it always reflects the latest published release with no manual edits or build step required.

## Structure

- `docfx.json` - DocFX configuration file
- `toc.yml` - Table of contents / sidebar navigation
- `index.md` - Main homepage and command reference
- `philosophy.md` - Governing philosophy and current-truth model
- `quickstart.md` - Bootstrap and first-feature walkthrough
- `implementation-lifecycle.md` - Full workflow with anti-patterns guide
- `release-usage.md` - Final validation and release-only archival guide
- `next-usage.md` - State-aware next-command navigation and safe auto progression
- `installation.md` - Approved quickstart-based installation
- `upgrade.md` - Approved quickstart-based upgrades and repairs
- `constitution-guide.md` - Constitution creation, structure, and best practices
- `monorepo-guide.md` - Optional multi-app monorepo support
- `pr-review-usage.md` - PR review command guide
- `site-audit-usage.md` - Site audit command guide
- `explain-usage.md` - Existing-functionality explanation and knowledge-sync guide
- `critic-usage.md` - Critic command guide
- `checklist-usage.md` - Checklist command guide
- `repo-story-usage.md` - Repo story command guide
- `faq.md` - Frequently asked questions
- `about.md` - Design philosophy and project overview
- `AGENTS.md` - AI agent integration architecture
- `_site/` - Generated documentation output (ignored by git)

## Deployment

Documentation is automatically built and deployed to GitHub Pages when changes are pushed to the `main` branch. The workflow is defined in `.github/workflows/docs.yml`.
