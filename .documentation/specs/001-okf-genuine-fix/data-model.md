# Data Model: OKF Traceability and Genuine Fix Discipline

## Entity: OKF Knowledge Document

Represents one per-feature Markdown file with YAML frontmatter and human-readable body content.

**Fields**:

- `okf_schema_version`: Schema version string.
- `document_id`: Stable unique ID within the feature.
- `document_type`: One of `requirement`, `task`, `gate-evidence`, `traceability-index`, or `decision`.
- `feature_id`: Feature directory name, such as `001-okf-genuine-fix`.
- `title`: Human-readable title.
- `status`: One of `draft`, `active`, `superseded`, or `complete`.
- `requirement_ids`: List of requirement IDs referenced by the document.
- `task_ids`: List of task IDs referenced by the document.
- `gate_evidence_ids`: List of evidence IDs referenced by the document.
- `source_artifacts`: List of artifact paths or identifiers supporting the document.
- `updated_at`: Date in `YYYY-MM-DD` format.

**Validation rules**:

- `document_id`, `document_type`, `feature_id`, `title`, and `updated_at` are required.
- Requirement IDs must match the feature's requirement ID format, such as `FR-001`.
- Task IDs must match task IDs, such as `T001`.
- Gate evidence IDs must be stable within the feature.

## Entity: Traceability Link

Represents a relationship between a requirement, one or more tasks, and gate evidence.

**Fields**:

- `requirement_id`: Requirement being satisfied.
- `task_ids`: Tasks that implement or validate the requirement.
- `gate_evidence_ids`: Evidence proving the requirement has been reviewed or verified.
- `coverage_status`: `covered`, `partial`, `uncovered`, or `unknown`.

**Validation rules**:

- A covered requirement has at least one linked task and one linked gate evidence item.
- Partial coverage identifies which side is missing.
- Unknown coverage is advisory and never blocks when the knowledge layer is absent.

## Entity: Knowledge Coverage Report

Represents the validator output consumed by analyze and critic.

**Fields**:

- `status`: `ok`, `warn`, or `skipped`.
- `feature_dir`: Absolute feature directory path.
- `knowledge_dir`: Absolute knowledge directory path.
- `requirements_total`: Count of requirement references.
- `tasks_total`: Count of task references.
- `gate_evidence_total`: Count of gate evidence references.
- `requirements_covered`: Count of requirements with complete traceability.
- `requirements_uncovered`: List of requirement IDs lacking task or gate evidence links.
- `tasks_without_requirements`: List of task IDs not linked to any requirement.
- `evidence_without_requirements`: List of evidence IDs not linked to any requirement.
- `messages`: Human-readable advisory messages.

**Validation rules**:

- Missing `knowledge/` returns `status: skipped` and exits successfully.
- Invalid documents return `status: warn` and exit successfully for advisory mode.

## Entity: Genuine Fix Intent Cue

Represents the behavioral intent attached to a finding.

**Fields**:

- `intent_cue`: One sentence stating the user-visible, system, or safety behavior that must be restored or preserved.
- `metric_context`: Optional metric that exposed the issue.
- `behavioral_evidence_required`: Proof expected before the finding can be considered fixed.

**Validation rules**:

- Analyze and critic findings must include `intent_cue`.
- Site-audit findings must include `Intent`.
- Metric context cannot substitute for behavioral evidence.

## Entity: Genuine Fix Proof

Represents verification evidence for a claimed fix.

**Fields**:

- `intent`: Behavior the fix was meant to change or preserve.
- `behavior_before`: Observed behavior before the fix.
- `behavior_after`: Observed behavior after the fix.
- `metric_before`: Optional metric value before the fix.
- `metric_after`: Optional metric value after the fix.
- `evidence`: Tests, reproduction steps, logs, screenshots, or review observations.

**Validation rules**:

- A proof that only changes `metric_after` while `behavior_after` remains unchanged fails Genuine Fix Guard.
- A proof must include behavioral evidence for the intended change.
