# Data Model

This feature is configuration-driven (YAML/Markdown artifacts) plus an in-process runner state machine. There is no persistent database. Entities below model the on-disk artifacts and runtime records the runner produces.

## Entity: Atomic Prompt

**Location**: `templates/prompts/atomic/<id>.md`
**Format**: Markdown body + YAML frontmatter

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Unique identifier (kebab-case); referenced by workflows |
| `name` | string | yes | Human-readable display name |
| `audience` | enum | yes | `beginner` \| `intermediate` \| `expert` |
| `exposed` | bool | yes | Show in default `devspark help` output |
| `category` | string | yes | Grouping tag (e.g., `spec`, `review`, `improvement`) |
| `description` | string | yes | One-line summary |
| `inputs` | list[string] | no | Named context keys the prompt reads |
| `outputs` | list[string] | no | Named context keys the prompt writes |
| `legacy_command` | string | no | Slash-command name this atomic prompt mirrors (back-compat) |

**Validation rules**: `id` matches `^[a-z][a-z0-9-]*$`; required fields non-empty; `audience` and `category` from enum/known set.

**Lifecycle**: Authored once, read-only at runtime. Resolved through 3-tier chain (personal → team → stock).

---

## Entity: Workflow Definition

**Location**: `templates/workflows/<id>.yaml`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Workflow identifier |
| `name` | string | yes | Display name |
| `description` | string | yes | One-line summary |
| `output_type` | enum | yes | `reviewable-artifact` \| `pull-request` \| `issue-link` \| `none` |
| `autonomy` | object | yes | See **Autonomy Policy** below |
| `steps` | list[Step] | yes | Ordered list of step definitions |

**Step**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Unique within workflow |
| `prompt` | string | yes | Atomic prompt `id` to invoke |
| `pause_after` | bool | no | Default false; if true, runner halts for review |
| `when` | string | no | Boolean expression over context keys (conditional execution) |
| `on_failure` | enum | no | `abort` (default) \| `continue` \| `pause` |

**Validation rules**: `id`s unique; every `prompt` resolves to an atomic prompt; `when` expression parseable; cycle-free step list.

**Lifecycle**: Versioned in Git. Loader caches parsed workflows per process.

---

## Entity: Alias Entrypoint

**Location**: `templates/aliases/<id>.yaml`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Alias name shown to users |
| `target_workflow` | string | yes | Workflow `id` this alias resolves to |
| `description` | string | yes | One-line summary for help output |

**Validation rules**: `target_workflow` MUST resolve to an existing workflow definition; aliases MUST NOT chain to other aliases.

---

## Entity: Autonomy Policy

Embedded in Workflow Definition under `autonomy:`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `level` | enum | yes | `assisted` (default) \| `autonomous` |
| `review_after` | list[string] | no | Step ids that trigger pause when `level=assisted` |
| `guardrails` | object | no | See below; required when `level=autonomous` |

**Guardrails**:

| Field | Type | Description |
|-------|------|-------------|
| `max_files_changed` | int | Block if a single step proposes more than N file changes |
| `restricted_paths` | list[string] | Glob patterns that may not be written |
| `max_total_lines_changed` | int | Workflow-wide line-change budget |

**State transitions**: `assisted` may run without guardrails; `autonomous` MUST declare guardrails or runner aborts before step 1.

---

## Entity: Workflow Event (Telemetry)

**Location**: appended as one JSON object per line to `.documentation/telemetry/workflow-events.jsonl` (override via env `DEVSPARK_TELEMETRY_PATH`).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schema_version` | string | yes | `"1"` |
| `event_id` | string (uuid) | yes | Unique per event |
| `timestamp` | string (ISO 8601) | yes | UTC, millisecond precision |
| `workflow_id` | string | yes | Workflow definition id |
| `workflow_run_id` | string (uuid) | yes | Constant for all events in a single run |
| `step_id` | string | yes | Step definition id (or `__workflow__` for workflow-level events) |
| `phase` | enum | yes | `started` \| `completed` \| `paused` \| `failed` \| `guardrail_triggered` |
| `status` | enum | yes | `success` \| `failure` \| `pending` |
| `duration_ms` | int | yes | Step or workflow elapsed milliseconds (0 for `started` events) |
| `success` | bool | yes | True on `completed` + `success` |
| `autonomy_level` | enum | yes | Effective level at event time |
| `guardrail_rule` | string | no | Populated when `phase=guardrail_triggered` |
| `error` | string | no | Short error summary on failure |
| `context` | object | no | Optional additional metadata (≤ 1 KB) |

**Validation rules**: Writer rejects events missing required fields; events are append-only and never rewritten.

---

## Entity: Improvement Proposal

**In-flight** (workflow context) record produced by `suggest-improvement`:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | yes | Issue title |
| `classification` | enum | yes | `bug` \| `enhancement` \| `prompt-quality` \| `workflow-design` \| `documentation` |
| `context` | string | yes | Captured situation/repro |
| `current_behavior` | string | yes | What happens today |
| `expected_behavior` | string | yes | What should happen |
| `suggested_fix` | string | no | Optional author proposal |
| `issue_url` | string | no | Populated after `create-issue` step (output) |

**Persistence**: Not persisted locally beyond the workflow run; the canonical record is the GitHub issue created in `markhazleton/devspark`.

---

## Entity: Review Resolution Contract

Shared output shape required for `clarify`, `analyze`, `critic`, `pr-review`, `address-pr-review`. Already partially modeled by existing gate artifacts; this feature formalizes it.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `finding_id` | string | yes | Stable id (e.g., `analyze-001`) |
| `severity` | enum | yes | `low` \| `medium` \| `high` \| `critical` |
| `description` | string | yes | What the finding says |
| `recommended_action` | string | yes | Machine-actionable next step |
| `execution_mode` | enum | yes | `auto` \| `selective` \| `manual` |
| `status` | enum | yes | `pending` \| `applied` \| `rejected` \| `deferred` |
| `outcome` | string | no | Result after resolution |

**Validation rules**: `finding_id` unique within an artifact; `status` and `outcome` updated by `address-pr-review` and analyze remediation flows.
