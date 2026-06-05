# Contract: Telemetry Event

Each workflow step emits one JSON object per line appended to `.documentation/telemetry/workflow-events.jsonl`. Validated by `tests/test_telemetry_event_contract.py`.

## Schema (v1)

```json
{
  "schema_version": "1",
  "event_id": "1f0c4d36-2b71-4c3e-9f60-2c4a4d8f9e10",
  "timestamp": "2026-04-18T17:42:11.523Z",
  "workflow_id": "create-spec",
  "workflow_run_id": "0a7e6b4c-1d2e-4f30-9c1a-b7e0f3a2c8d4",
  "step_id": "analyze",
  "phase": "completed",
  "status": "success",
  "duration_ms": 4821,
  "success": true,
  "autonomy_level": "assisted",
  "guardrail_rule": null,
  "error": null,
  "context": {
    "files_changed": 3
  }
}
```

## Required fields

`schema_version`, `event_id`, `timestamp`, `workflow_id`, `workflow_run_id`, `step_id`, `phase`, `status`, `duration_ms`, `success`, `autonomy_level`.

## Phase semantics

| `phase` | When emitted | Required additional |
|---------|--------------|---------------------|
| `started` | Immediately before step execution | `duration_ms=0`, `status=pending` |
| `completed` | After successful step | `success=true`, `status=success`, `duration_ms>0` |
| `paused` | When runner halts for review (manual or `pause_after`) | `status=pending` |
| `failed` | On step error | `success=false`, `status=failure`, `error` populated |
| `guardrail_triggered` | When autonomy guardrail blocks/downgrades | `guardrail_rule` populated, `autonomy_level` reflects effective level |

## Writer behavior

- Append-only; never rewrite existing lines.
- Auto-create parent directory `.documentation/telemetry/` at first write.
- Auto-create file with mode `0644`.
- Each line is a complete JSON document terminated by `\n`.
- Each serialized event MUST be ≤ 4 KB; the optional `context` blob MUST be ≤ 1 KB. Writer rejects oversized events with `EVT_TOO_LARGE` (does not abort the workflow).
- The writer MUST acquire an OS-level exclusive file lock around each single `write()` call: `fcntl.flock(fd, LOCK_EX)` on POSIX, `msvcrt.locking(fd, LK_LOCK, ...)` on Windows. The lock is released immediately after the write. This guarantees concurrent `devspark run` invocations produce a fully parseable JSONL file.
- On write failure, runner logs to stderr and continues (telemetry MUST NOT block workflow execution); a `failed` write counts as a workflow-level diagnostic but not a step failure.

## Override

Environment variable `DEVSPARK_TELEMETRY_PATH` overrides the destination path. If unset or empty, default applies.

## Validation rules

| Rule | Error code |
|------|------------|
| Missing required field | `EVT_FIELD_MISSING` |
| `timestamp` not ISO 8601 UTC | `EVT_TIMESTAMP_INVALID` |
| `phase` not in enum | `EVT_PHASE_INVALID` |
| `status` not in enum | `EVT_STATUS_INVALID` |
| `phase=guardrail_triggered` with empty `guardrail_rule` | `EVT_GUARDRAIL_RULE_REQUIRED` |
| `phase=failed` with empty `error` | `EVT_ERROR_REQUIRED` |
| `phase=failed` with empty `error_class` | `EVT_ERROR_CLASS_REQUIRED` |
| `error` exceeds 500 characters | `EVT_ERROR_TOO_LONG` |
| Serialized event exceeds 4 KB OR `context` exceeds 1 KB | `EVT_TOO_LARGE` |

## Aggregation guidance

Consumers can `jq -c 'select(.workflow_run_id=="<id>")'` to slice a run, or aggregate by `workflow_id` + `success` for reliability metrics.
