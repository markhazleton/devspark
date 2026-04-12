# Release Notes: v1.6.0

## Release Metadata

- Version: v1.6.0
- Release Date: 2026-04-12
- Previous Version: v1.5.0
- Commits Since Previous Release: 8
- Contributors: Mark Hazleton, copilot-swe-agent[bot]

## Highlights

DevSpark v1.6.0 is a consistency and install-hardening release. It standardizes how installed repositories resolve stock helper templates, closes quickstart drift around constitution seeding and inventory completeness, and makes incomplete same-version installs repairable instead of only reportable.

This release also tightens the quickstart intake experience. Users are now asked only for install-critical information up front, while project metadata questions are deferred until a new constitution actually needs to be created.

## Added

- `/devspark.update-pr` prompt template for refreshing an existing pull request description from branch delta
- `/devspark.commit-audit` prompt template for commit-history workflow and hygiene review
- Explicit quickstart Repair Mode for missing stock framework files in existing installs

## Changed

- Installed-repository prompt templates now resolve helper templates from `.devspark/templates/`
- Quickstarts now preserve existing constitutions and reuse them instead of re-asking for project metadata
- Quickstarts now separate install-critical questions from constitution-bootstrap questions
- Release evidence docs and validation references now track v1.6.0

## Fixed

- Missing quickstart inventory entries for `quick-spec-template.md` and `update-pr.md`
- Duplicate constitution seeding under `.devspark/`
- Mismatch between command-template helper-template paths and quickstart install paths
- Same-version quickstart installs that were missing framework files now trigger repair guidance instead of a false success path

## Validation

- 10 repository test scripts executed successfully
- Targeted markdown linting passed for all edited quickstart files and quickstart README
- GitHub CLI release prerequisites validated before publication

## Upgrade Notes

- Team and per-user overrides under `.documentation/` remain preserved.
- Stock framework assets under `.devspark/` can now be repaired even when the installed version already matches the latest release.
- Existing constitutions under `.documentation/memory/constitution.md` are treated as the source of truth during quickstart bootstrap.

## Release Artifacts

- Changelog updated for v1.6.0
- Package version bumped to 1.6.0
- Release readiness documented in `.documentation/release-readiness-v1.6.0.md`
- Documentation audit documented in `.documentation/docs-audit-2026-04-12.md`
