# Changelog

All notable changes to DevSpark are documented here.

## [v4.1.0] - 2026-08-30

### Added

- Added `/devspark.discover-knowledge` to build source-grounded
  `.knowledge/entities` records, assimilate documentation intake, and refresh
  generated ontology reports.

### Changed

- Updated every quickstart to initialize `.knowledge/entities/` and
  `.knowledge/ontology/` on each execution.
- Quickstarts now delegate incomplete knowledge bootstrap work to
  `/devspark.discover-knowledge --bootstrap` instead of duplicating source
  discovery rules.
- Updated command catalogs and docs-site content for the 30-command inventory.

## [v4.0.0] - 2026-08-30

### Changed

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
