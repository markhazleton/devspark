# Contract: Events Schema

**Feature**: 002-harness-runtime | **Date**: 2026-04-14 | **Source**: [data-model.md](../data-model.md)

---

## Overview

This contract defines the structure of two run artifact files:

1. **`events.jsonl`** — append-only stream of telemetry events emitted during a run
2. **`result.json`** — final run summary written on run completion or failure

Both files are written to `.documentation/devspark/runs/<run-id>/` and are user-owned.

---

## File: `events.jsonl`

A newline-delimited JSON file. Each line is a valid JSON object representing one telemetry event. Events are appended in chronological order as they occur.

### Base Fields (all events)

| Field | Type | Notes |
|-------|------|-------|
| `event` | string | Named event type (see below) |
| `run_id` | string | Format: `run_<YYYYMMDDTHHMMSSZ>_<6-char-hex>` |
| `ts` | string | ISO 8601 UTC timestamp e.g. `"2026-04-14T19:30:00.123Z"` |

### Named Event Types

#### `harness.run.started`

Emitted when `devspark harness run` begins execution (after spec validation passes).

```json
{
  "event": "harness.run.started",
  "run_id": "run_20260414T193000Z_a1b2c3",
  "ts": "2026-04-14T19:30:00.000Z",
  "harness_name": "specify-plan-implement cycle",
  "api_version": "devspark.ai/v1",
  "scope": { "type": "repo" },
  "adapter": "noop",
  "dry_run": false
}
```

Additional fields:

| Field | Type | Notes |
|-------|------|-------|
| `harness_name` | string | From `HarnessSpec.name` |
| `api_version` | string | From `HarnessSpec.apiVersion` |
| `scope` | object | `{"type": "repo"}` or `{"type": "app", "app": "<id>"}` |
| `adapter` | string | Resolved default adapter for this run |
| `dry_run` | boolean | True when `--dry-run` flag was passed |

---

#### `harness.run.finished`

Emitted when the run reaches a terminal state (`complete`, `failed`, or `aborted`).

```json
{
  "event": "harness.run.finished",
  "run_id": "run_20260414T193000Z_a1b2c3",
  "ts": "2026-04-14T19:30:01.500Z",
  "status": "complete",
  "duration_ms": 1500,
  "steps_total": 3,
  "validation_failures": 0
}
```

Additional fields:

| Field | Type | Notes |
|-------|------|-------|
| `status` | string | `"complete"` \| `"failed"` \| `"aborted"` |
| `duration_ms` | integer | Total wall-clock time for the run |
| `steps_total` | integer | Total number of steps executed |
| `validation_failures` | integer | Total `error`-severity rule failures across all steps and attempts |

---

#### `harness.step.started`

Emitted at the beginning of each step attempt.

```json
{
  "event": "harness.step.started",
  "run_id": "run_20260414T193000Z_a1b2c3",
  "ts": "2026-04-14T19:30:00.100Z",
  "step_id": "specify",
  "attempt": 1,
  "adapter": "noop"
}
```

Additional fields:

| Field | Type | Notes |
|-------|------|-------|
| `step_id` | string | Matches `StepSpec.id` |
| `attempt` | integer | Attempt number starting at 1 |
| `adapter` | string | Adapter used for this attempt |

---

#### `harness.step.finished`

Emitted at the end of each step attempt.

```json
{
  "event": "harness.step.finished",
  "run_id": "run_20260414T193000Z_a1b2c3",
  "ts": "2026-04-14T19:30:00.400Z",
  "step_id": "specify",
  "attempt": 1,
  "status": "passed",
  "duration_ms": 300
}
```

Additional fields:

| Field | Type | Notes |
|-------|------|-------|
| `step_id` | string | |
| `attempt` | integer | |
| `status` | string | `"passed"` \| `"failed"` \| `"skipped_dry_run"` \| `"skipped_no_tty"` \| `"aborted"` |
| `duration_ms` | integer | Wall-clock time for this attempt only |

---

#### `harness.step.validation`

Emitted once per validation rule evaluated. May emit multiple times per step if multiple rules are defined.

```json
{
  "event": "harness.step.validation",
  "run_id": "run_20260414T193000Z_a1b2c3",
  "ts": "2026-04-14T19:30:00.350Z",
  "step_id": "specify",
  "rule_id": "spec-file-exists",
  "rule_type": "file.exists",
  "status": "passed",
  "severity": "error",
  "message": "File .documentation/specs/001-feature/spec.md exists"
}
```

Additional fields:

| Field | Type | Notes |
|-------|------|-------|
| `step_id` | string | |
| `rule_id` | string | Matches `ValidationRule.id` |
| `rule_type` | string | e.g. `"file.exists"`, `"command.exit_code"` |
| `status` | string | `"passed"` \| `"failed"` \| `"skipped"` |
| `severity` | string | `"error"` \| `"warning"` |
| `message` | string | Human-readable outcome detail |

---

#### `harness.tool.called`

Emitted when an adapter invokes a tool (e.g., runs a shell command or calls an AI agent CLI).

```json
{
  "event": "harness.tool.called",
  "run_id": "run_20260414T193000Z_a1b2c3",
  "ts": "2026-04-14T19:30:00.200Z",
  "step_id": "shell-check",
  "tool": "shell",
  "command_preview": "markdownlint-cli2 .documentation/specs/001-feature/spec.md"
}
```

Additional fields:

| Field | Type | Notes |
|-------|------|-------|
| `step_id` | string | |
| `tool` | string | e.g. `"shell"`, `"claude_code"`, `"copilot"`, `"noop"` |
| `command_preview` | string | First 200 chars of the command or prompt |

---

#### `harness.policy.blocked`

Emitted when a step is blocked by a policy check (e.g., scope restriction, missing required tool).

```json
{
  "event": "harness.policy.blocked",
  "run_id": "run_20260414T193000Z_a1b2c3",
  "ts": "2026-04-14T19:30:00.050Z",
  "step_id": "specify",
  "reason": "adapter claude_code not available: claude CLI not found"
}
```

Additional fields:

| Field | Type | Notes |
|-------|------|-------|
| `step_id` | string | |
| `reason` | string | Human-readable explanation of why the step was blocked |

---

### Complete `events.jsonl` Example

```jsonl
{"event":"harness.run.started","run_id":"run_20260414T193000Z_a1b2c3","ts":"2026-04-14T19:30:00.000Z","harness_name":"specify-plan cycle","api_version":"devspark.ai/v1","scope":{"type":"repo"},"adapter":"noop","dry_run":false}
{"event":"harness.step.started","run_id":"run_20260414T193000Z_a1b2c3","ts":"2026-04-14T19:30:00.100Z","step_id":"specify","attempt":1,"adapter":"noop"}
{"event":"harness.tool.called","run_id":"run_20260414T193000Z_a1b2c3","ts":"2026-04-14T19:30:00.200Z","step_id":"specify","tool":"noop","command_preview":"noop: specify"}
{"event":"harness.step.validation","run_id":"run_20260414T193000Z_a1b2c3","ts":"2026-04-14T19:30:00.350Z","step_id":"specify","rule_id":"spec-file-exists","rule_type":"file.exists","status":"passed","severity":"error","message":"File .documentation/specs/001-feature/spec.md exists"}
{"event":"harness.step.finished","run_id":"run_20260414T193000Z_a1b2c3","ts":"2026-04-14T19:30:00.400Z","step_id":"specify","attempt":1,"status":"passed","duration_ms":300}
{"event":"harness.step.started","run_id":"run_20260414T193000Z_a1b2c3","ts":"2026-04-14T19:30:00.500Z","step_id":"plan","attempt":1,"adapter":"noop"}
{"event":"harness.step.finished","run_id":"run_20260414T193000Z_a1b2c3","ts":"2026-04-14T19:30:00.700Z","step_id":"plan","attempt":1,"status":"passed","duration_ms":200}
{"event":"harness.run.finished","run_id":"run_20260414T193000Z_a1b2c3","ts":"2026-04-14T19:30:00.700Z","status":"complete","duration_ms":700,"steps_total":2,"validation_failures":0}
```

---

## File: `result.json`

A single JSON object written on run completion. Contains the full run summary including step results and validation findings.

### Schema

```json
{
  "run_id": "run_20260414T193000Z_a1b2c3",
  "status": "complete",
  "harness_name": "specify-plan-implement cycle",
  "api_version": "devspark.ai/v1",
  "scope": { "type": "repo" },
  "started_at": "2026-04-14T19:30:00.000Z",
  "finished_at": "2026-04-14T19:30:01.500Z",
  "metrics": {
    "duration_ms": 1500,
    "steps_total": 3,
    "steps_passed": 3,
    "steps_failed": 0,
    "validation_failures": 0
  },
  "steps": [
    {
      "step_id": "specify",
      "status": "passed",
      "attempts": 1,
      "adapter": "noop",
      "duration_ms": 300,
      "validation_findings": [
        {
          "rule_id": "spec-file-exists",
          "type": "file.exists",
          "status": "passed",
          "severity": "error",
          "message": "File .documentation/specs/001-feature/spec.md exists"
        }
      ],
      "artifacts": {
        "created": [".documentation/specs/001-feature/spec.md"],
        "modified": [],
        "deleted": []
      }
    },
    {
      "step_id": "plan",
      "status": "passed",
      "attempts": 2,
      "adapter": "noop",
      "duration_ms": 800,
      "validation_findings": [
        {
          "rule_id": "plan-file-exists",
          "type": "file.exists",
          "status": "passed",
          "severity": "error",
          "message": "File .documentation/specs/001-feature/plan.md exists"
        }
      ],
      "artifacts": {
        "created": [".documentation/specs/001-feature/plan.md"],
        "modified": [],
        "deleted": []
      }
    }
  ]
}
```

### Top-Level Fields

| Field | Type | Notes |
|-------|------|-------|
| `run_id` | string | Format: `run_<YYYYMMDDTHHMMSSZ>_<6-char-hex>` |
| `status` | string | `"complete"` \| `"failed"` \| `"aborted"` |
| `harness_name` | string | From `HarnessSpec.name` |
| `api_version` | string | From `HarnessSpec.apiVersion` |
| `scope` | object | Resolved scope declaration |
| `started_at` | string | ISO 8601 UTC |
| `finished_at` | string \| null | ISO 8601 UTC; null if aborted before completion |
| `metrics` | object | See RunMetrics |
| `steps` | array | One object per executed step; see StepResult |

### RunMetrics Fields

| Field | Type | Notes |
|-------|------|-------|
| `duration_ms` | integer | Total run wall-clock time |
| `steps_total` | integer | |
| `steps_passed` | integer | |
| `steps_failed` | integer | |
| `validation_failures` | integer | Total `error`-severity rule failures across all steps and attempts |

### StepResult Fields

| Field | Type | Notes |
|-------|------|-------|
| `step_id` | string | Matches `StepSpec.id` |
| `status` | string | `"passed"` \| `"failed"` \| `"skipped_dry_run"` \| `"skipped_no_tty"` \| `"aborted"` |
| `attempts` | integer | Total attempts made |
| `adapter` | string | Adapter used for this step |
| `duration_ms` | integer | Total wall-clock across all attempts |
| `validation_findings` | array | Per-rule outcomes from the last attempt only |
| `artifacts` | object | See ArtifactDelta |

### ValidationFinding Fields

| Field | Type | Notes |
|-------|------|-------|
| `rule_id` | string | Matches `ValidationRule.id` |
| `type` | string | Rule type e.g. `"file.exists"` |
| `status` | string | `"passed"` \| `"failed"` \| `"skipped"` |
| `severity` | string | `"error"` \| `"warning"` |
| `message` | string | Human-readable outcome detail |

### ArtifactDelta Fields

| Field | Type | Notes |
|-------|------|-------|
| `created` | array[string] | Repo-relative paths of files created during the step |
| `modified` | array[string] | Repo-relative paths of files modified |
| `deleted` | array[string] | Repo-relative paths of files deleted |

---

## Run Artifact Directory Layout

```text
.documentation/devspark/runs/<run-id>/
├── spec.resolved.yaml     ← HarnessSpec after path resolution and defaults applied
├── context.json           ← RunContext snapshot
├── events.jsonl           ← append-only TelemetryEvent stream (this contract)
├── result.json            ← Run summary (this contract)
└── steps/
    └── <step-id>/
        ├── prompt.md      ← rendered prompt passed to adapter (if applicable)
        ├── output.txt     ← adapter output (if applicable)
        └── stdout.txt     ← captured stdout/stderr for command.exit_code rules
```

### `context.json` Schema

```json
{
  "run_id": "run_20260414T193000Z_a1b2c3",
  "repo_root": "/absolute/path/to/repo",
  "spec_path": "/absolute/path/to/harness.yaml",
  "doc_root": "/absolute/path/to/repo/.documentation",
  "adapter": "noop",
  "dry_run": false
}
```

### `spec.resolved.yaml`

The HarnessSpec after all defaults have been merged into steps and all relative paths have been resolved to absolute paths. This file records exactly what was executed, not what was authored.

---

## Retention and Pruning

- Default retention: 20 most recent runs
- Configurable via `run_retention_limit` in user config (`platformdirs.user_config_dir("devspark") / "config.json"`)
- After each new run completes, scan `.documentation/devspark/runs/`, sort by directory mtime, delete oldest directories when count exceeds limit
- Runs with status `running` are never pruned

---

## Immutability

- `events.jsonl` is append-only; no event is ever modified or deleted during a run
- `result.json` is written exactly once at run completion; never overwritten for the same run ID
- Both files are user-owned and are never modified by `devspark` after the run completes
