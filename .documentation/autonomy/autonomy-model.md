# Autonomy Model

DevSpark workflows declare their `autonomy.level` and (optionally) a set of
`guardrails`. The runner enforces both before, during, and after each step.

## Levels

| Level | Behavior |
|-------|----------|
| `assisted` (default) | Pauses at every `pause_after: true` step and at every `review_after` step. Guardrail breaches downgrade to a pause. |
| `autonomous` | Runs through `pause_after` and `review_after` markers. Guardrail breaches HARD-FAIL with `EXIT_GUARDRAIL_BLOCKED` (21). Requires `guardrails` to be declared. |

## Guardrails

| Key | Type | Behavior |
|-----|------|----------|
| `max_files_changed` | int | Reject the step when the post-step diff vs the pre-step baseline touches more than N files. |
| `max_total_lines_changed` | int | Reject the step when `git diff --numstat` against the baseline sums to more than N lines (added + deleted). |
| `restricted_paths` | list[glob] | Reject when ANY changed path matches ANY glob (fnmatch). |

## Resolution channels

The effective autonomy level is taken from (in order):

1. CLI flag: `--autonomy assisted|autonomous`.
2. Env var: `DEVSPARK_AUTONOMY=assisted|autonomous`.
3. Project file: `.devspark/autonomy.yaml` (`level: ...`).
4. Workflow default: `autonomy.level` in the workflow YAML.

If `--non-interactive` is supplied without any of the above, `devspark run`
exits `EXIT_AUTONOMY_REQUIRED` (20) with a message naming all three input
channels (FR-016, SC-006).

## Telemetry signals

Every guardrail evaluation emits a JSONL event under
`.documentation/telemetry/workflow-events.jsonl`:

- `phase`: `started` | `completed` | `paused` | `failed` | `guardrail_triggered`
- `status`: `success` | `pause` | `block` | `failure`
- `guardrail_rule`: name of the breached rule (e.g., `max_files_changed`)
- `error_class` (required when `phase=failed`): short Pythonic class name

## Pause and resume

When a step pauses (either explicitly via `pause_after` or via a downgraded
guardrail breach in `assisted` mode), the runner writes
`.documentation/telemetry/runs/<workflow_run_id>.json` (override with
`DEVSPARK_RUNS_PATH`) atomically and prints:

```text
Paused. Resume with: devspark resume <workflow_run_id>
```

`devspark resume` re-resolves the workflow definition, validates the
`schema_version` (currently `1`) and the SHA-256 `context_checksum`, and
continues from `next_step_id` reusing the original `workflow_run_id`. Any
mismatch exits `EXIT_RESUME_FAILED` (25).

## Performance trade-off

The guardrail enforcer captures a per-step baseline by SHA-1-hashing every
tracked file (`git ls-files`) before the step runs. On large repositories
with many short steps this can add measurable latency. As of PR #28 (M-04)
the enforcer **short-circuits** when no `guardrails` are declared on the
workflow, so guardrail-free runs incur zero baseline cost. When guardrails
are declared, accept the per-step hashing cost or scope `restricted_paths`
narrowly to keep the active set small.
