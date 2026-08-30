# Changelog

All notable changes to DevSpark are documented here.

## [v4.0.0] - 2026-08-30

### Changed

- Added `/devspark.discover-knowledge` to build source-grounded
  `.knowledge/entities` and refresh ontology reports.
- Repositioned DevSpark as a prompt-first lifecycle toolkit.
- Made quickstart prompts the only approved install, upgrade, and repair path.
- Removed the standalone DevSpark terminal application surface from the active
  repository.
- Moved durable current truth to `.knowledge/`.
- Moved temporary lifecycle work to `.devspark.work/`.
- Updated release automation to use `.devspark/VERSION` as the framework version
  authority.

### Removed

- Removed terminal runtime source, packaging metadata, runtime workflow fixtures,
  and tests.
- Removed the standalone framework-maintenance prompt and generated shims.
- Removed historical local archives and generated run/history artifacts from the
  working tree.
