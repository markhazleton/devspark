# Changelog

All notable changes to DevSpark are documented here.

## [v5.0.0] - 2026-09-27

DevSpark now follows the "Plan Temporarily, Review the Delta" current-truth
philosophy. This is a breaking release for existing installations: re-run the
matching quickstart prompt, which installs the new engine, removes legacy
engine copies, and migrates `.knowledge/` (review the
`migrate-knowledge-to-entities.py --dry-run` output, including any conflicts,
before confirming).

### Breaking

- The knowledge engine moved from `scripts/python/build_knowledge_index.py` to
  `scripts/build_knowledge_index.py` (installed at `.devspark/scripts/`). The
  `--write` flag is gone: running without flags writes, `--check` validates.
- `.knowledge/ontology/*.generated.md` and `_derived.yaml` are replaced by
  `index.json` and `coverage.json`.
- Decisions declare `constrains` (not `governs`), entities hand-author the
  reciprocal `constrained_by`, and `status`, `lifecycle`, `supersedes`,
  `superseded-by`, `replaced`, and `obsolete` are rejected on current knowledge.
- Missing evidence on an entity or decision now fails `--check`, and every
  document under an entity needs `source_of_truth` and `last_verified`; a
  missing `fallback_reason` stays a warning.
- `/devspark.next --auto` and command dispatch were removed; `/devspark.next`
  only recommends.

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
- Added `scripts/scan-ephemeral-refs.py`, which fails when code comments name
  spec, task, requirement, proposal, work-package, or archive identifiers.
- Added flat knowledge nodes (`.knowledge/<topic>.md`, `.knowledge/guides/**`)
  and validated `links.references` on any knowledge node.
- Added `scripts/discover-knowledge-context.py`, read-only discovery signals
  for `/devspark.discover-knowledge`.
- The release pre-scan now blocks unresolved linkage refs
  (`UNRESOLVED_LINKAGE_REFS`) and lists `RETENTION_CANDIDATES`.

### Fixed

- `discover-knowledge-context.py` scales to large repositories (about 80x
  faster: 800 files across 20 entities went from over a minute to about a
  second) and its output no longer depends on hash ordering.
- Windows drive paths (`C:/...`) are treated as local references, not URLs, by
  the knowledge engine and both release pre-scans.

### Changed

- Constitution §X now covers migrations of repository-owned knowledge:
  preserve authored content or report a conflict until explicit force.
- The generated `.knowledge/ontology/*.json` files are marked
  `linguist-generated` so pull requests collapse their diffs; quickstarts seed
  the same `.gitattributes` lines.
- `/devspark.discover-knowledge` is now a propose-only authoring aid: it reports
  knowledge gaps, mapping gaps and ambiguities, relationship and alias
  candidates, contradictions, historical leakage, and entity candidates, and
  applies only findings a human selects and confirms. `--bootstrap` remains for
  first-time setup.
- Engine writes keep unreferenced pinned baselines (reported as warnings), and
  `--check --entity` scopes decision errors to the entities they constrain.
- Release archives packages under `.archive/YYYY-MM-DD/` preserving their path
  relative to `.devspark.work/` and also sweeps routine work-product retention
  and orphaned state; constitution commands archive their own resolved
  proposals.
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
