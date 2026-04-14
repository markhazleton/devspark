# Contract: HarnessSpec YAML Format

**Feature**: 002-harness-runtime | **Date**: 2026-04-14 | **Source**: [data-model.md](../data-model.md)

---

## Overview

A HarnessSpec file is a declarative YAML (or JSON) document that defines a repeatable, multi-step workflow for AI-assisted development. The file is authored by developers and consumed by `devspark harness run` and `devspark harness validate`.

**File extension**: `.yaml` or `.yml` (preferred) or `.json`
**Required header constant**: `apiVersion: devspark.ai/v1`
**Supported apiVersion values**: `devspark.ai/v1` (any other value is rejected per FR-027)

---

## Minimal Valid Spec

```yaml
apiVersion: devspark.ai/v1
kind: HarnessSpec
name: my-first-harness

steps:
  - id: step-one
    type: agent_task
    prompt_file: prompts/step-one.md
```

---

## Full Annotated Spec

```yaml
# Required header
apiVersion: devspark.ai/v1
kind: HarnessSpec

# Human-readable name for display and run artifact naming
name: specify-plan-implement cycle

# Optional: scope declaration
# Defaults to type: repo if omitted
scope:
  type: repo           # "repo" | "app"
  # app: my-app        # Required only when type: app

# Optional: defaults applied to all steps unless overridden per-step
defaults:
  adapter: noop        # default adapter; overridden by --adapter flag or user config
  mode: agent          # "agent" | "shell" | "manual"
  retry:
    maxAttempts: 1
    backoff: none

# Optional: controls event output
telemetry:
  emit_jsonl: true
  run_dir: .documentation/devspark/runs   # Root directory for run artifacts

# Required: steps list (minimum 1)
steps:
  - id: specify
    name: Write Feature Specification
    type: agent_task           # "agent_task" | "validation" | "function" | "human_gate"
    mode: agent                # inherits from defaults if omitted
    adapter: noop              # overrides defaults.adapter for this step
    prompt_file: prompts/specify.md    # resolved relative to spec file location
    inputs:
      - .documentation/memory/constitution.md
      - .documentation/specs/**/*.md
    outputs:
      - .documentation/specs/*/spec.md
    validation:
      - id: spec-file-exists
        type: file.exists
        severity: error
        path: .documentation/specs/001-feature/spec.md
      - id: spec-has-rationale
        type: file.contains
        severity: warning
        path: .documentation/specs/001-feature/spec.md
        contains: "## Rationale Summary"
    retry:
      maxAttempts: 3
      backoff: exponential
      retryOn:
        - validation_fail
      requireHumanAfter: 2
      repairPrompt: prompts/specify-repair.md
    on_success: plan     # ID of next step on success; if absent, proceed sequentially
    on_failure: abort    # ID of next step after retries exhausted; if absent, run fails

  - id: plan
    name: Generate Implementation Plan
    type: agent_task
    prompt_file: prompts/plan.md
    inputs:
      - .documentation/specs/001-feature/spec.md
    outputs:
      - .documentation/specs/001-feature/plan.md
    validation:
      - id: plan-file-exists
        type: file.exists
        severity: error
        path: .documentation/specs/001-feature/plan.md
      - id: plan-schema-valid
        type: json.schema
        severity: error
        schema_file: .devspark/schemas/plan.schema.json
        target_file: .documentation/specs/001-feature/plan.md
      - id: git-branch-clean
        type: git.clean
        severity: warning
        path: .documentation/specs/001-feature/

  - id: validate-outputs
    name: Validate All Outputs Present
    type: validation
    validation:
      - id: spec-exists
        type: file.exists
        severity: error
        path: .documentation/specs/001-feature/spec.md
      - id: plan-exists
        type: file.exists
        severity: error
        path: .documentation/specs/001-feature/plan.md
      - id: always-ok
        type: always.pass
        severity: error

  - id: human-review
    name: Human Review Gate
    type: human_gate
    mode: manual             # Displays copy/paste panel in IDE; waits for keypress
    prompt_file: prompts/review-gate.md

  - id: shell-check
    name: Run linter
    type: function
    mode: shell
    validation:
      - id: lint-passes
        type: command.exit_code
        severity: error
        command: markdownlint-cli2 .documentation/specs/001-feature/spec.md
        expected_exit: 0
      - id: pattern-check
        type: regex.match
        severity: warning
        path: .documentation/specs/001-feature/spec.md
        pattern: "\\*\\*Status\\*\\*: (Draft|In Progress|Complete)"
```

---

## Field Reference

### Top-Level Fields

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `apiVersion` | string | Yes | — | Must be `devspark.ai/v1`; any other value → rejected |
| `kind` | string | Yes | — | Must be `HarnessSpec` |
| `name` | string | Yes | — | Human-readable name; used in run artifact directory name |
| `scope` | object | No | `{type: repo}` | See Scope fields |
| `defaults` | object | No | See below | Applied to steps that omit the field |
| `telemetry` | object | No | See below | Controls event output location |
| `steps` | list | Yes | — | Minimum 1 step; executed in declared order |

### Scope Fields

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `type` | `"repo"` \| `"app"` | Yes | `repo` = repository root; `app` = registered app |
| `app` | string | Conditional | Required when `type: app`; must match a registered app ID |

### Defaults Fields

| Field | Type | Default |
|-------|------|---------|
| `adapter` | string | `"noop"` |
| `mode` | `"agent"` \| `"shell"` \| `"manual"` | `"agent"` |
| `retry` | object | `{maxAttempts: 1, backoff: "none"}` |

### Telemetry Fields

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `emit_jsonl` | boolean | `true` | Write events.jsonl |
| `run_dir` | string | `.documentation/devspark/runs` | Root directory for run artifacts |

### Step Fields

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | string | Yes | Unique within spec; used in routing and trace output |
| `name` | string | No | Human-readable label |
| `type` | string | Yes | `"agent_task"` \| `"validation"` \| `"function"` \| `"human_gate"` |
| `mode` | string | No | `"agent"` \| `"shell"` \| `"manual"`; inherits from defaults |
| `adapter` | string | No | Overrides `defaults.adapter` for this step |
| `prompt_file` | string | No | Path to `.md` prompt file; resolved relative to spec file location |
| `inputs` | list[string] | No | Glob patterns for input files; recorded in artifact delta |
| `outputs` | list[string] | No | Glob patterns for output files; verified post-execution |
| `validation` | list | No | Rules evaluated after step execution |
| `retry` | object | No | Overrides `defaults.retry` |
| `on_success` | string | No | Step ID to execute on success; sequential if absent |
| `on_failure` | string | No | Step ID to execute after retries exhausted; run fails if absent |

### Validation Rule Fields

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | string | Yes | Unique within step |
| `type` | string | Yes | One of the 7 built-in rule types |
| `severity` | `"error"` \| `"warning"` | Yes | `error` blocks and triggers retry; `warning` is recorded only |
| `path` | string | Conditional | Required for `file.exists`, `file.contains`, `git.clean`, `regex.match` |
| `contains` | string | Conditional | Required for `file.contains` |
| `command` | string | Conditional | Required for `command.exit_code` |
| `expected_exit` | integer | No | Default `0`; used by `command.exit_code` |
| `schema_file` | string | Conditional | Required for `json.schema` |
| `target_file` | string | Conditional | Required for `json.schema` |
| `pattern` | string | Conditional | Required for `regex.match` |

#### Rule Types

| Type | Passes when |
|------|------------|
| `always.pass` | Unconditionally — use for wiring and dry-run testing |
| `file.exists` | `path` exists on disk |
| `file.contains` | `path` exists and content includes `contains` substring |
| `command.exit_code` | Shell command exits with `expected_exit` code |
| `json.schema` | `target_file` is valid JSON conforming to `schema_file` |
| `git.clean` | `git status --porcelain [path]` returns empty output |
| `regex.match` | `path` content matches `pattern` |

### Retry Policy Fields

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `maxAttempts` | integer | `1` | Total attempts including the first; minimum 1 |
| `backoff` | `"none"` \| `"fixed"` \| `"exponential"` | `"none"` | Delay strategy between retry attempts |
| `retryOn` | list[string] | `["validation_fail"]` | Triggers: `validation_fail`, `tool_error`, `timeout` |
| `requireHumanAfter` | integer | absent | Pause for human review after N failed attempts |
| `repairPrompt` | string | absent | Path to `.md` file appended with validation errors on retry |

---

## Validation Rules (enforced at load time)

1. `apiVersion` must equal `devspark.ai/v1` — any other value is rejected with a version mismatch error before execution begins
2. `kind` must equal `HarnessSpec`
3. `steps` must be non-empty (at least one step)
4. All `step.id` values must be unique within the spec
5. `step.on_success` and `step.on_failure` must reference a valid `step.id` or be absent
6. When `scope.type` is `app`, `scope.app` must be present and match a registered app ID
7. `scope.app` is only valid when `scope.type` is `app`
8. All `validation[].id` values must be unique within their step
9. Conditional fields (`path`, `contains`, `command`, `schema_file`, `target_file`, `pattern`) must be present when required by rule type
10. `retry.maxAttempts` must be ≥ 1

---

## Path Resolution

All relative paths in a spec file are resolved relative to the directory containing the spec file, not the repository root or the current working directory.

```
spec file: /repo/.documentation/specs/001-feature/harness.yaml
prompt_file: prompts/specify.md
resolved: /repo/.documentation/specs/001-feature/prompts/specify.md
```

To reference repository-root-relative paths, use paths starting from the root (e.g., `.documentation/memory/constitution.md`) — these are resolved against `repo_root` detected at run time.

---

## Error Examples

### Unsupported apiVersion (FR-027)

```
Error: unsupported apiVersion "devspark.ai/v2"
  Expected: devspark.ai/v1
  File: my-harness.yaml
  Fix: Update apiVersion to "devspark.ai/v1"
```

### Missing Required Step Field

```
Error: step[0] missing required field "type"
  Step ID: specify
  File: my-harness.yaml
```

### Duplicate Step ID

```
Error: duplicate step ID "specify" at positions 0 and 2
  File: my-harness.yaml
  Fix: Each step ID must be unique within the spec
```

### Invalid on_success Reference

```
Error: step "specify" on_success references unknown step ID "planx"
  Valid step IDs: specify, plan, validate-outputs
  File: my-harness.yaml
```
