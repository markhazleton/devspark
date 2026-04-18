# Implementation Plan: Harness Validation Enhancements (v2)

<!-- markdownlint-disable MD032 MD040 -->

**Branch**: `harness_validation` | **Date**: 2026-04-15 | **Spec**: [spec.md](spec.md)
**Predecessor**: [plan.md](plan.md) (v1 harness runtime — all phases complete)
**Status**: Complete — Merged via PR [#24](https://github.com/markhazleton/devspark/pull/24) on 2026-04-16. All five phases delivered.

## Rationale Summary

### Core Problem

The v1 harness runtime delivers repeatable, validated, observable workflows. However, review against current agent-engineering research reveals five structural gaps: (1) artifact tracking is declared but never populated, (2) no mode-based gating separates read-only planning from write-enabled execution, (3) validation is purely deterministic with no rubric/LLM scoring tier, (4) historical runs cannot be re-scored or replayed, and (5) there is no mechanism to progressively simplify the harness as models improve.

### Decision Summary

Address these gaps in five phases, ordered by dependency and impact. Each phase is independently shippable and testable. No existing behavior changes — all additions are additive to the v1 harness surface.

### Key Drivers

- Research shows harness orchestration drives more performance variation than model choice
- ArtifactDelta is the most visible gap — outputs are declared but never compared to reality
- Mode gating prevents accidental writes during planning and CI contexts
- LLM rubric scoring completes the two-tier validation model (deterministic → rubric)
- Replay/re-score enables harness optimization from historical failure data

---

## Phase 1: Wire ArtifactDelta Tracking

**Priority**: P0 | **Effort**: ~1 session | **Dependencies**: None (builds on existing models)

### Goal

After each step execution, compare declared `outputs` against actual filesystem state and populate `ArtifactDelta.created`, `modified`, `deleted` on the `StepResult`. Emit artifact events in the telemetry stream.

### Steps

#### Step 1.1 — Add filesystem snapshot helper

**File**: `src/devspark_cli/harness/runner.py`

Create a helper function that takes a list of output paths and returns a dict mapping each path to its modification timestamp and size (or `None` if missing). This captures the "before" state.

```python
def _snapshot_outputs(paths: list[str]) -> dict[str, tuple[float, int] | None]:
    """Capture mtime+size for each declared output path, or None if missing."""
    result = {}
    for p in paths:
        path = Path(p)
        if path.exists():
            stat = path.stat()
            result[p] = (stat.st_mtime, stat.st_size)
        else:
            result[p] = None
    return result
```

#### Step 1.2 — Add diff function

**File**: `src/devspark_cli/harness/runner.py`

Create a function that compares before/after snapshots and returns a populated `ArtifactDelta`.

```python
def _diff_snapshots(
    before: dict[str, tuple[float, int] | None],
    after: dict[str, tuple[float, int] | None],
) -> ArtifactDelta:
    created, modified, deleted = [], [], []
    all_paths = set(before) | set(after)
    for p in sorted(all_paths):
        b, a = before.get(p), after.get(p)
        if b is None and a is not None:
            created.append(p)
        elif b is not None and a is None:
            deleted.append(p)
        elif b is not None and a is not None and b != a:
            modified.append(p)
    return ArtifactDelta(created=created, modified=modified, deleted=deleted)
```

#### Step 1.3 — Integrate into execute_step

**File**: `src/devspark_cli/harness/runner.py`

In `execute_step()`, call `_snapshot_outputs(step.outputs)` before the adapter runs and again after. Pass the resulting `ArtifactDelta` into every `StepResult` instead of the current empty `ArtifactDelta()`.

#### Step 1.4 — Add telemetry event for artifacts

**File**: `src/devspark_cli/harness/telemetry.py`

Add `"harness.step.artifacts"` to `EVENT_TYPES`. Emit it from `execute_step` after computing the delta, with payload `created`, `modified`, `deleted` counts and paths.

#### Step 1.5 — Update contract test

**File**: `tests/test_harness_validation_contract.py`

Add a test case: create a harness spec where step outputs include a file that doesn't exist before the run. Use the noop adapter (which won't create the file). Verify `ArtifactDelta` is populated in `result.json` — the output file should appear as neither created nor modified. Then create a second spec where the file is pre-created; verify it appears correctly in the delta.

#### Checkpoint

`python tests/test_harness_validation_contract.py` passes. `result.json` from any run now contains non-empty `artifacts` on steps that declare outputs.

---

## Phase 2: Plan/Act Mode Gating

**Priority**: P1 | **Effort**: ~1 session | **Dependencies**: None (parallel with Phase 1)

### Goal

Introduce a `plan` execution mode where adapters return proposed changes without writing to disk. Enforce this structurally so `plan` mode runs cannot accidentally mutate the repo.

### Steps

#### Step 2.1 — Add `execution_mode` to RunContext

**File**: `src/devspark_cli/harness/spec_models.py`

Add a field to `RunContext`:

```python
ExecutionMode = Literal["plan", "act"]

class RunContext(BaseModel):
    # ... existing fields ...
    execution_mode: ExecutionMode = "act"
```

#### Step 2.2 — Add `--mode` CLI flag

**File**: `src/devspark_cli/harness/cli.py`

Add `--mode plan|act` option to the `run` command (default: `act`). Pass it through to `HarnessRunner` and into `RunContext.execution_mode`.

#### Step 2.3 — Enforce in adapter protocol

**File**: `src/devspark_cli/harness/adapters/base.py`

In `CommandLineAdapter.execute()`, check `context.execution_mode`. When `plan`, append a `--dry-run` or equivalent flag to the subprocess command, or wrap the prompt with an explicit "do not write files" instruction prefix. Emit `harness.policy.blocked` if the adapter doesn't support plan mode.

#### Step 2.4 — Enforce in noop adapter

**File**: `src/devspark_cli/harness/adapters/noop.py`

Noop already doesn't write — just ensure telemetry records `execution_mode: plan` in events.

#### Step 2.5 — Add plan-mode validation behavior

**File**: `src/devspark_cli/harness/validation.py`

When `context.execution_mode == "plan"`, skip `command.exit_code` rules (they may have side effects) and mark them `skipped` with a message. All filesystem rules still evaluate (they're read-only).

#### Step 2.6 — Contract test

**File**: `tests/test_harness_runner_contract.py`

Add a test: run a spec with `--mode plan`; verify (a) the run completes, (b) `context.json` shows `execution_mode: plan`, (c) `command.exit_code` rules are skipped, (d) no filesystem mutations from declared outputs.

#### Checkpoint

`plan` mode runs are structurally read-only. `act` mode is unchanged from v1 behavior.

---

## Phase 3: LLM Rubric Validation Rule Type

**Priority**: P1 | **Effort**: ~1–2 sessions | **Dependencies**: None (parallel with Phases 1–2)

### Goal

Add an `llm.rubric` validation rule type that scores step output against a text rubric using an external LLM CLI. Runs only after all deterministic `error`-severity rules pass.

### Steps

#### Step 3.1 — Extend RuleType and ValidationRule

**File**: `src/devspark_cli/harness/spec_models.py`

Add `"llm.rubric"` to the `RuleType` literal. Add fields to `ValidationRule`:

```python
RuleType = Literal[
    # ... existing types ...
    "llm.rubric",
]

class ValidationRule(BaseModel):
    # ... existing fields ...
    rubric: str | None = None          # rubric text or path to rubric file
    grader_command: str | None = None  # CLI command to invoke (e.g., "claude --print")
    pass_threshold: int = 3            # minimum score (1-5) to pass
```

Add validation: `llm.rubric` requires `rubric` and `grader_command`.

#### Step 3.2 — Implement in ValidationEngine

**File**: `src/devspark_cli/harness/validation.py`

Add an `llm.rubric` handler:
1. Read the step's `output.txt` from `step_dir`.
2. Compose a grading prompt: rubric text + output content + "Score 1-5 on the first line."
3. Shell out to `grader_command` via `subprocess.run()` with the prompt on stdin.
4. Parse the first line of stdout for an integer score.
5. Pass if score >= `pass_threshold`; fail otherwise.
6. Capture full grader output to `step_dir / "rubric_result.txt"`.

No API keys in the harness — the `grader_command` CLI handles its own auth (same pattern as agent adapters).

#### Step 3.3 — Enforce deterministic-first ordering

**File**: `src/devspark_cli/harness/runner.py`

In `evaluate_step_validations()`, partition rules into deterministic and rubric groups. Evaluate deterministic rules first. If any `error`-severity deterministic rule fails, skip all `llm.rubric` rules (mark `skipped` with message "deterministic error-severity rule failed"). This saves LLM cost on obviously broken outputs.

#### Step 3.4 — Update schema and sample

**Files**: `.devspark/schemas/harness.schema.json`, `sample.harness.yaml`

Regenerate the JSON schema. Add a commented-out `llm.rubric` example to `sample.harness.yaml`.

#### Step 3.5 — Contract test

**File**: `tests/test_harness_validation_contract.py`

Add tests:
1. Mock a `grader_command` that echoes "4\nGood quality" — rubric rule passes.
2. Mock a grader that echoes "2\nPoor quality" — rubric rule fails.
3. A spec where a deterministic `file.exists` rule fails — rubric rules are skipped.
4. Verify `rubric_result.txt` is written to step dir.

#### Checkpoint

`llm.rubric` rules work end-to-end when a grader CLI is available. Deterministic rules always run first. No credentials stored in the harness.

---

## Phase 4: Harness Replay / Re-Score

**Priority**: P2 | **Effort**: ~1 session | **Dependencies**: Phase 1 (ArtifactDelta) recommended but not required

### Goal

Add a `devspark harness replay <run-id>` command that re-evaluates validation rules against a completed run's preserved artifacts, producing a new score without re-executing any steps.

### Steps

#### Step 4.1 — Implement replay in runner

**File**: `src/devspark_cli/harness/runner.py`

Add a `replay()` method to `HarnessRunner` (or a standalone `ReplayRunner` class):
1. Load `spec.resolved.yaml` from the run directory.
2. For each step, locate preserved artifacts (`output.txt`, `prompt.md`) in `steps/<step-id>/`.
3. Re-evaluate all validation rules against the current filesystem state (artifacts may have changed since the original run).
4. Write a `replay_result.json` alongside the original `result.json`.
5. Emit telemetry to a separate `replay_events.jsonl`.

#### Step 4.2 — Add CLI command

**File**: `src/devspark_cli/harness/cli.py`

Add `devspark harness replay <run-id> [--run-dir]` command. Accepts `latest` alias. Outputs a comparison: original vs replayed status for each step.

#### Step 4.3 — Contract test

**File**: `tests/test_harness_runner_contract.py`

Run a spec, then run `devspark harness replay latest`. Verify `replay_result.json` is created and contains valid step results. Modify a file that a `file.contains` rule checks, then replay — verify the rule now fails.

#### Checkpoint

Historical runs can be re-scored. Useful for diagnosing intermittent failures and validating harness rule changes.

---

## Phase 5: Context Budget and Subtraction Hooks

**Priority**: P2–P3 | **Effort**: ~1 session | **Dependencies**: None

### Goal

Add optional fields that let spec authors control context size and mark harness components as conditionally active, enabling progressive simplification.

### Steps

#### Step 5.1 — Add context_budget to StepSpec

**File**: `src/devspark_cli/harness/spec_models.py`

Add an optional field:

```python
class StepSpec(BaseModel):
    # ... existing fields ...
    context_budget: int | None = None  # max characters for combined prompt + inputs
```

#### Step 5.2 — Enforce in adapter base

**File**: `src/devspark_cli/harness/adapters/base.py`

In `load_prompt_text()`, if `step.context_budget` is set, truncate the combined prompt to that limit. Log a `harness.policy.blocked` event (with reason `context_budget_exceeded`) if truncation occurs, so the user knows content was dropped.

#### Step 5.3 — Add `enabled` flag to ValidationRule

**File**: `src/devspark_cli/harness/spec_models.py`

Add an optional field:

```python
class ValidationRule(BaseModel):
    # ... existing fields ...
    enabled: bool = True  # set to false to skip without removing from spec
```

In `ValidationEngine.evaluate()`, return `skipped` immediately when `enabled is False`. This is the "expiring assumption" mechanism — rules can be disabled as models improve without deleting them from the spec.

#### Step 5.4 — Add `min_model_capability` to StepDefaults (future-proofing)

**File**: `src/devspark_cli/harness/spec_models.py`

Add an optional string field to `StepDefaults`:

```python
class StepDefaults(BaseModel):
    # ... existing fields ...
    min_model_capability: str | None = None  # e.g., "gpt-4-class", advisory only
```

This is advisory-only for v2 — logged in telemetry but not enforced. It signals intent for future subtraction: "this harness was designed assuming a model of at least this capability."

#### Step 5.5 — Contract tests

Update `test_harness_spec_contract.py`:
1. Spec with `context_budget: 500` parses correctly.
2. Spec with `enabled: false` on a rule parses correctly.
3. Validation engine skips disabled rules.

Update `test_harness_validation_contract.py`:
1. A step with `context_budget` truncates prompt text to the limit.

#### Checkpoint

Spec authors can control context size and disable rules declaratively. Subtraction is now a first-class operation.

---

## Execution Order and Dependencies

```
Phase 1 (ArtifactDelta)  ──┐
Phase 2 (Plan/Act Mode)  ──┼── All three are independent; can run in parallel
Phase 3 (LLM Rubric)     ──┘
         │
         ▼
Phase 4 (Replay/Re-Score) ── benefits from Phase 1 but not blocked by it
         │
         ▼
Phase 5 (Context Budget + Subtraction) ── independent; can start anytime
```

### Suggested Serial Order (if one developer)

| Order | Phase | Key Deliverable |
|-------|-------|-----------------|
| 1 | Phase 1 | `ArtifactDelta` populated in every run |
| 2 | Phase 2 | `--mode plan` flag on `harness run` |
| 3 | Phase 3 | `llm.rubric` validation rule type |
| 4 | Phase 4 | `harness replay` CLI command |
| 5 | Phase 5 | `context_budget`, `enabled` flag, subtraction hooks |

### Testing Strategy

Each phase ships its own contract test additions to the existing test files. No new test files required — extend:
- `test_harness_spec_contract.py` — model parsing for new fields
- `test_harness_runner_contract.py` — end-to-end CLI behavior
- `test_harness_validation_contract.py` — engine evaluation for new rule types

### Risk Mitigation

| Risk | Mitigation |
|------|------------|
| `llm.rubric` grader CLI unavailable in CI | Skip rubric rules when grader is absent (same as adapter `is_available()` pattern) |
| Plan mode doesn't prevent all writes | Plan mode is advisory for external adapters; enforcement is structural for built-in adapters only |
| Context budget truncation loses critical content | Log truncation events prominently; start with simple end-truncation, evolve to priority-based |
| Replay against stale artifacts gives misleading results | Replay output clearly labels "re-scored at <timestamp>" vs original run timestamp |
