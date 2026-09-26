# Changelog

All notable changes to DevSpark are documented here.

## [Unreleased]

### Added

- Added the single knowledge engine at `scripts/build_knowledge_index.py`
  (installed at `.devspark/scripts/`), writing `.knowledge/ontology/index.json`
  and `coverage.json`, with `--check`, `--search`, `--detect-drift`, and
  `--pin-claim` modes.
- Added deterministic concept discovery (aliases, headings, path metadata, and
  query-time body search through `scripts/explain-context.py`) with fixed
  per-class weights counted once per query term.
- Added pinned `source_of_truth` claims with retained baselines and the
  `knowledge_drift.enforcement` setting in `.knowledge/knowledge.config.yaml`.
- Added `scripts/migrate-knowledge-to-entities.py`, the `entity-node` and
  `knowledge-node` schemas, `resolve_knowledge_engine` /
  `Resolve-KnowledgeEngine`, and agent/prompt shims for `discover-knowledge`.

### Changed

- Decisions now declare `constrains`; entities hand-author the reciprocal
  `constrained_by`, validated by the engine. `_derived.yaml` and the Markdown
  ontology reports are retired.
- Lifecycle keys (`status`, `lifecycle`, `supersedes`, `superseded-by`,
  `replaced`, `obsolete`) are banned on current knowledge; missing evidence is
  now a gate, while a missing `fallback_reason` stays a warning.
- Release archives packages under `.archive/YYYY-MM-DD/` preserving their path
  relative to `.devspark.work/` and also sweeps routine work-product retention
  and orphaned state; constitution commands archive their own resolved
  proposals.
- `/devspark.next` now only recommends; `--auto` and dispatching were removed.
- Replaced the current-truth philosophy with "Plan Temporarily, Review the
  Delta" and aligned command prompts, quickstarts, and the constitution.

## [v4.3.0] - 2026-09-09

### Added

- Added the Knowledge, Code, and Tests guide to the static site and navigation.
- Added deterministic Bash and PowerShell generators for supported agent shims.

### Changed

- Clarified agent compatibility, descriptions, and current-release documentation.
- Removed legacy constitution path handling from helper scripts.
- Fixed installed knowledge-generator path resolution.
- Fixed ShellCheck parsing of generated shim Markdown.

## [v4.2.0] - 2026-09-04

### Added

- Added a published DevSpark Philosophy guide covering external-pressure
  discovery, current truth, evidence, assimilation, release rollover, and the
  prompt-first/no-CLI product boundary.

### Changed

- Aligned lifecycle documentation with human-selected release events and
  sprint reporting as a separate business view.
- Fixed documentation links to quickstart prompts so the DocFX site builds
  without warnings.

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
