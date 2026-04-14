# Data Model: DevSpark Harness Runtime

**Feature**: 002-harness-runtime | **Date**: 2026-04-14 | **Source**: [spec.md](spec.md)

---

## Entity Relationship Overview

```
HarnessSpec
  ├── scope: ScopeDeclaration
  ├── defaults: StepDefaults
  ├── telemetry: TelemetryConfig
  └── steps[]: StepSpec
        ├── validation[]: ValidationRule
        └── retry: RetryPolicy

Run
  ├── context: RunContext
  └── steps[]: StepResult
        └── validation_findings[]: ValidationFinding

TelemetryEvent  →  emitted by Run to events.jsonl
RunArtifact     →  files written to .documentation/devspark/runs/<run-id>/
```

---

## HarnessSpec

The top-level document parsed from a `.yaml` or `.json` harness spec file.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `apiVersion` | `str` | Yes | Must equal `devspark.ai/v1`; any other value → FR-027 rejection |
| `kind` | `str` | Yes | Must equal `HarnessSpec` |
| `name` | `str` | Yes | Human-readable name for display and run artifact naming |
| `scope` | `ScopeDeclaration` | No | Defaults to `type: repo` |
| `defaults` | `StepDefaults` | No | Applied to all steps unless overridden per-step |
| `steps` | `list[StepSpec]` | Yes | Minimum 1 step; executed in declared order |
| `telemetry` | `TelemetryConfig` | No | Controls event output location |

**Validation rules**:
- `apiVersion` must match `SUPPORTED_API_VERSION` constant in CLI
- `steps` must be non-empty
- All `step.id` values must be unique within the spec
- `step.on_success` and `step.on_failure` must reference a valid `step.id` or be absent

---

## ScopeDeclaration

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `type` | `"repo" \| "app"` | Yes | Defaults to `repo` |
| `app` | `str` | Conditional | Required when `type: app`; must match a registered app ID |

**Validation rules**: `app` field is only valid when `type: app`; unknown app IDs produce a clear error before execution begins.

---

## StepDefaults

Applied to every step that does not override the field.

| Field | Type | Default |
|-------|------|---------|
| `adapter` | `str` | `"noop"` |
| `retry` | `RetryPolicy` | `{maxAttempts: 1, backoff: "none"}` |
| `mode` | `"agent" \| "manual"` | `"agent"` |

---

## TelemetryConfig

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `emit_jsonl` | `bool` | `true` | Write events.jsonl |
| `run_dir` | `str` | `.documentation/devspark/runs` | Root directory for run artifacts |

---

## StepSpec

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | `str` | Yes | Unique within spec; used in `on_success`/`on_failure` routing and trace output |
| `name` | `str` | No | Human-readable label for display |
| `type` | `"agent_task" \| "validation" \| "human_gate"` | Yes | What kind of work this step represents |
| `mode` | `"agent" \| "manual"` | No | How the step is executed; inherits from `defaults.mode`; `validation` steps do not invoke an adapter |
| `adapter` | `str` | No | Overrides `defaults.adapter` for this step |
| `prompt_file` | `str` | No | Path to prompt `.md` file for `agent_task` or `human_gate`; resolved relative to spec file location |
| `inputs` | `list[str]` | No | Glob patterns for files this step reads; recorded in artifact delta |
| `outputs` | `list[str]` | No | Glob patterns for files this step produces; verified post-execution |
| `validation` | `list[ValidationRule]` | No | Rules evaluated after step execution; for `validation` steps, these rules are the step payload |
| `retry` | `RetryPolicy` | No | Overrides `defaults.retry` |
| `on_success` | `str` | No | ID of next step on success; if absent, proceed sequentially |
| `on_failure` | `str` | No | ID of next step on failure after retries exhausted; if absent, run fails |

---

## ValidationRule

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | `str` | Yes | Unique within step |
| `type` | `RuleType` | Yes | One of the 7 built-in types |
| `severity` | `"error" \| "warning"` | Yes | `error` → blocks and triggers retry; `warning` → recorded only |
| `path` | `str` | Conditional | Required for `file.exists`, `file.contains`, `git.clean` |
| `contains` | `str` | Conditional | Required for `file.contains` |
| `command` | `str` | Conditional | Required for `command.exit_code` |
| `expected_exit` | `int` | No | Default `0`; used by `command.exit_code` |
| `schema_file` | `str` | Conditional | Required for `json.schema`; path to JSON Schema file |
| `target_file` | `str` | Conditional | Required for `json.schema`; path to file to validate |
| `pattern` | `str` | Conditional | Required for `regex.match` |

**RuleType values and behaviors**:

| Type | Passes when |
|------|------------|
| `always.pass` | Unconditionally — for wiring and dry-run testing |
| `file.exists` | `path` exists on disk |
| `file.contains` | `path` exists and its content includes `contains` substring |
| `command.exit_code` | Shell command exits with `expected_exit` code |
| `json.schema` | `target_file` is valid JSON conforming to `schema_file` |
| `git.clean` | `git status --porcelain [path]` returns empty output |
| `regex.match` | `path` content matches `pattern` |

---

## RetryPolicy

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `maxAttempts` | `int` | `1` | Total attempts including the first; minimum 1 |
| `backoff` | `"none" \| "fixed" \| "exponential"` | `"none"` | Delay strategy between retry attempts |
| `retryOn` | `list["validation_fail" \| "tool_error" \| "timeout"]` | `["validation_fail"]` | Triggers that activate retry |
| `requireHumanAfter` | `int` | absent | Pause for human review after N failed attempts |
| `repairPrompt` | `str` | absent | Path to `.md` file; appended with validation errors on retry |

---

## Run

Runtime state created when `devspark harness run` is invoked.

| Field | Type | Notes |
|-------|------|-------|
| `run_id` | `str` | Format: `run_<YYYYMMDDTHHMMSSZ>_<6-char-hex>` e.g. `run_20260414T193000Z_a1b2c3` |
| `status` | `"running" \| "complete" \| "failed" \| "aborted"` | `aborted` = user interrupt; `failed` = exhausted retries |
| `harness_name` | `str` | From `HarnessSpec.name` |
| `api_version` | `str` | From `HarnessSpec.apiVersion` |
| `scope` | `ScopeDeclaration` | Resolved scope |
| `started_at` | `str` | ISO 8601 UTC |
| `finished_at` | `str \| None` | ISO 8601 UTC; absent if aborted before completion |
| `steps` | `list[StepResult]` | One entry per executed step |
| `metrics` | `RunMetrics` | Aggregate counts |

---

## RunContext

Resolved at run start, passed through all step executions.

| Field | Type | Notes |
|-------|------|-------|
| `run_id` | `str` | Matches `Run.run_id` |
| `repo_root` | `Path` | Absolute path to repository root |
| `spec_path` | `Path` | Absolute path to the spec file being executed |
| `doc_root` | `Path` | `.documentation/` for repo scope; `{app.path}/.documentation/` for app scope |
| `adapter` | `str` | Resolved adapter name (spec → user default → "noop") |
| `dry_run` | `bool` | When true, steps are not executed |

---

## StepResult

| Field | Type | Notes |
|-------|------|-------|
| `step_id` | `str` | Matches `StepSpec.id` |
| `status` | `"passed" \| "failed" \| "skipped_dry_run" \| "aborted"` | |
| `attempts` | `int` | Number of execution attempts made |
| `adapter` | `str` | Adapter used for this step |
| `duration_ms` | `int` | Total wall-clock time across all attempts |
| `validation_findings` | `list[ValidationFinding]` | Per-rule outcomes from last attempt |
| `artifacts` | `ArtifactDelta` | Files created/modified/deleted during this step |

---

## ValidationFinding

| Field | Type | Notes |
|-------|------|-------|
| `rule_id` | `str` | Matches `ValidationRule.id` |
| `type` | `str` | Rule type (e.g. `file.exists`) |
| `status` | `"passed" \| "failed" \| "skipped"` | |
| `severity` | `"error" \| "warning"` | |
| `message` | `str` | Human-readable outcome detail |

---

## ArtifactDelta

| Field | Type | Notes |
|-------|------|-------|
| `created` | `list[str]` | Repo-relative paths of files created during the step |
| `modified` | `list[str]` | Repo-relative paths of files modified |
| `deleted` | `list[str]` | Repo-relative paths of files deleted |

---

## RunMetrics

| Field | Type | Notes |
|-------|------|-------|
| `duration_ms` | `int` | Total run wall-clock time |
| `steps_total` | `int` | |
| `steps_passed` | `int` | |
| `steps_failed` | `int` | |
| `validation_failures` | `int` | Total `error`-severity rule failures across all steps and attempts |

---

## TelemetryEvent

A single append-only entry written to `events.jsonl`. All events share these base fields:

| Field | Type | Notes |
|-------|------|-------|
| `event` | `str` | Named event type (see below) |
| `run_id` | `str` | |
| `ts` | `str` | ISO 8601 UTC timestamp |

Named event types and their additional fields:

| Event | Additional Fields |
|-------|------------------|
| `harness.run.started` | `harness_name`, `api_version`, `scope`, `adapter`, `dry_run` |
| `harness.run.finished` | `status`, `duration_ms`, `steps_total`, `validation_failures` |
| `harness.step.started` | `step_id`, `attempt`, `adapter` |
| `harness.step.finished` | `step_id`, `attempt`, `status`, `duration_ms` |
| `harness.step.validation` | `step_id`, `rule_id`, `rule_type`, `status`, `severity`, `message` |
| `harness.tool.called` | `step_id`, `tool` (e.g. `noop`, `manual`, `claude_code`), `command_preview` |
| `harness.policy.blocked` | `step_id`, `reason` |

---

## Run Artifact File Layout

```text
.documentation/devspark/runs/<run-id>/
├── spec.resolved.yaml     ← HarnessSpec after path resolution and defaults applied
├── context.json           ← RunContext snapshot (repo_root, doc_root, adapter, dry_run)
├── events.jsonl           ← append-only TelemetryEvent stream
├── result.json            ← Run summary (status, metrics, StepResults with findings)
└── steps/
    └── <step-id>/
        ├── prompt.md      ← rendered prompt passed to adapter (if applicable)
        ├── output.txt     ← adapter output (if applicable)
        └── stdout.txt     ← captured stdout/stderr for command.exit_code rules
```

---

## State Transitions

### Run Status

```
(start)
   │
   ▼
running ──── all steps passed ──→ complete
   │
   ├── step exhausted retries ──→ failed
   │
   └── Ctrl+C interrupt ────────→ aborted
```

### Step Status

```
(start)
   │
   ▼
executing ──── validation passed ──→ passed
   │
   ├── error-severity rule failed ──→ (retry if attempts remain) ──→ failed
   │
   ├── dry_run=true ──────────────→ skipped_dry_run
   │
   ├── manual + no TTY ────────────→ failed
   │
   └── Ctrl+C ──────────────────────→ aborted
```

---

## User Config Schema

Stored at `platformdirs.user_config_dir("devspark") / "config.json"`.

```json
{
  "default_adapter": "noop",
  "run_retention_limit": 20
}
```

All fields optional; defaults applied at runtime when absent.
