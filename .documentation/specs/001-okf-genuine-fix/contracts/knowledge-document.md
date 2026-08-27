# Contract: OKF Knowledge Document

## Purpose

Every generated feature can contain a `knowledge/` directory with Markdown documents that expose traceability in YAML frontmatter while preserving readable body content.

## Location

```text
.documentation/specs/<feature>/knowledge/*.md
```

## Schema

The validating schema lives at:

```text
templates/schemas/okf-knowledge-document.schema.json
```

## Required Frontmatter Shape

```yaml
---
okf_schema_version: "1.0"
document_id: okf-001
document_type: traceability-index
feature_id: 001-okf-genuine-fix
title: Traceability Index
status: active
requirement_ids:
  - FR-001
task_ids:
  - T001
gate_evidence_ids:
  - gate-analyze-001
source_artifacts:
  - spec.md
updated_at: 2026-08-27
---
```

## Rules

- Existing JSON output from lifecycle scripts must not include new fields solely for OKF support.
- Knowledge documents are additive work product under the feature directory.
- Documents should use stable IDs so validator output remains stable across reruns.
- Schema validation errors are advisory unless a command explicitly requests strict mode in the future.
