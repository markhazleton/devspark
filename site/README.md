# Documentation

This folder contains the DevSpark public-site project, built using [DocFX](https://dotnet.github.io/docfx/).
It is intentionally separate from `.knowledge/guides/`, which is reserved for published project guidance
in repositories that use DevSpark.

## Building Locally

To build the documentation locally:

1. Install DocFX:

   ```bash
   dotnet tool install -g docfx
   ```

2. Build the documentation:

   ```bash
   cd site
   docfx docfx.json --serve
   ```

3. Open your browser to `http://localhost:8080` to view the documentation.

   To preview installation and release metadata too, run the following from the repository root after building DocFX:

   ```powershell
   ./eng/release/create-release-packages.ps1 -Version v9.0.0
   python eng/site/build-distribution.py
   ```

   Release metadata comes from `/dist/manifest.json`. The same manifest drives
   quickstart installation from `/raw/`, including native Copilot skills.

## Structure

- `src/` - authored pages, navigation, media, and published data
- `templates/` - DocFX presentation customizations
- `docfx.json` - DocFX configuration
- `AGENTS.md` - source-scoped AI agent guidance; never published
- `_site/` - generated deployment output; ignored by Git

## Deployment

Documentation, release archives, and the raw install tree are built and deployed
to GitHub Pages at <https://dev.makeboldspark.com> by `.github/workflows/docs.yml`
when publishing inputs change on `main`. Make Bold branding is configured in
`docfx.json` and `templates/devspark/`.
