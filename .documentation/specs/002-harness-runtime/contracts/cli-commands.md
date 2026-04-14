# Contract: CLI Commands

**Feature**: 002-harness-runtime | **Date**: 2026-04-14 | **Source**: [spec.md](../spec.md), [plan.md](../plan.md)

---

## Overview

This contract defines the input/output behavior of all new commands introduced by the harness runtime. All existing commands (`init`, `upgrade`, `registry`) are unchanged.

**Principle**: All new commands are additive. Zero changes to existing command behavior.

---

## Command Index

| Command | Group | Phase |
|---------|-------|-------|
| `devspark harness run <spec>` | harness | 2 |
| `devspark harness validate <spec>` | harness | 2 |
| `devspark harness trace <run-id>` | harness | 2 |
| `devspark adapter list` | adapter | 2 |
| `devspark adapter default <name>` | adapter | 2 |
| `devspark doctor` | top-level | 3 |

---

## `devspark harness run`

Execute a harness spec file end-to-end.

### Synopsis

```
devspark harness run <spec_file> [OPTIONS]
```

### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `spec_file` | path | Yes | Path to `.yaml` or `.json` harness spec file |

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--dry-run` | flag | false | Parse and validate spec; skip all step execution; write `skipped_dry_run` status per step |
| `--adapter <name>` | string | user config or `noop` | Override the default adapter for all steps |
| `--adapter-default` | flag | false | Use the adapter stored in user config |

### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Run completed with all steps passing |
| `1` | Run failed (one or more steps exhausted retries) |
| `2` | Run aborted (user Ctrl+C interrupt) |
| `3` | Spec validation error (invalid YAML, unsupported apiVersion, missing required fields) |

### Output — TTY (interactive)

```
DevSpark Harness: specify-plan-implement cycle
Run ID: run_20260414T193000Z_a1b2c3
Adapter: noop | Scope: repo

  ✓  specify          [noop]  0.3s
  ✓  plan             [noop]  0.2s
  ⚠  validate-outputs [noop]  0.1s  (1 warning)
  ✗  human-review     [manual] —    retries exhausted

Run failed — 3/4 steps passed | 1 failed | 0 aborted
Artifacts: .documentation/devspark/runs/run_20260414T193000Z_a1b2c3/
```

### Output — Non-TTY (CI)

```
run_start run_20260414T193000Z_a1b2c3 specify-plan-implement cycle
step_pass specify noop 0.3s
step_pass plan noop 0.2s
step_warn validate-outputs noop 0.1s
step_fail human-review manual 0 retries_exhausted
run_fail 3/4 passed
```

### Behavior

- Writes run artifacts to `.documentation/devspark/runs/<run-id>/` (created on first run)
- After completing, prunes oldest runs when count exceeds retention limit (default 20)
- On Ctrl+C: sets run status to `aborted`, preserves all artifacts written so far, exits code `2`
- `--dry-run`: parses spec, resolves context, skips all step execution, writes artifacts with `skipped_dry_run` status; exits `0` on any valid spec

---

## `devspark harness validate`

Validate a harness spec file against domain models without executing it.

### Synopsis

```
devspark harness validate <spec_file>
```

### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `spec_file` | path | Yes | Path to `.yaml` or `.json` harness spec file |

### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Spec is valid |
| `1` | Spec has validation errors |

### Output — TTY

```
Validating: my-harness.yaml

  ✓  apiVersion: devspark.ai/v1
  ✓  kind: HarnessSpec
  ✓  3 steps — all IDs unique
  ✓  on_success/on_failure references valid
  ✗  step "specify" validation[0] missing required field "path" for type "file.exists"

Spec invalid — 1 error
```

### Output — Non-TTY

```
validate_ok apiVersion
validate_ok kind
validate_ok step_ids
validate_ok routing_refs
validate_err specify validation[0] missing field path for type file.exists
spec_invalid 1 error
```

### Performance

Must complete in < 2 seconds on any valid spec (SC-004).

---

## `devspark harness trace`

Display the event stream of a completed run as a formatted table.

### Synopsis

```
devspark harness trace <run_id>
```

### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `run_id` | string | Yes | Run ID (e.g. `run_20260414T193000Z_a1b2c3`) or the literal `latest` |

### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Trace rendered successfully |
| `1` | Run ID not found |

### Output — TTY (Rich table)

```
Run: run_20260414T193000Z_a1b2c3  |  Status: complete  |  Duration: 0.6s
Harness: specify-plan-implement cycle  |  Adapter: noop  |  Scope: repo

┌──────────────────────────────┬──────────┬─────────┬────────────┬─────────────┐
│ Timestamp                    │ Step ID  │ Attempt │ Status     │ Duration ms │
├──────────────────────────────┼──────────┼─────────┼────────────┼─────────────┤
│ 2026-04-14T19:30:00.000Z     │ —        │ —       │ run.start  │ —           │
│ 2026-04-14T19:30:00.100Z     │ specify  │ 1       │ step.start │ —           │
│ 2026-04-14T19:30:00.400Z     │ specify  │ 1       │ passed     │ 300         │
│ 2026-04-14T19:30:00.500Z     │ plan     │ 1       │ step.start │ —           │
│ 2026-04-14T19:30:00.700Z     │ plan     │ 1       │ passed     │ 200         │
│ 2026-04-14T19:30:00.800Z     │ validate │ 1       │ step.start │ —           │
│ 2026-04-14T19:30:00.900Z     │ validate │ 1       │ passed     │ 100         │
│ 2026-04-14T19:30:00.900Z     │ —        │ —       │ run.finish │ 900         │
└──────────────────────────────┴──────────┴─────────┴────────────┴─────────────┘

Validation findings:
  validate  spec-file-exists   passed   (file.exists)
  validate  spec-has-rationale passed   (file.contains)
```

### Output — Non-TTY

Tab-separated rows, one per event, to stdout.

### Behavior

- `latest` resolves to the most recent run by directory mtime under `telemetry.run_dir`
- If no runs exist, prints `No runs found` and exits `1`

---

## `devspark adapter list`

List all registered execution adapters and their availability.

### Synopsis

```
devspark adapter list
```

### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Always |

### Output — TTY

```
Available adapters:

  ✓  noop        Always available (no AI required)
  ✓  manual      Always available (copy/paste for IDE agents)
  ✗  claude_code Requires claude CLI — not found (brew install claude)
  ✗  copilot     Requires gh CLI with Copilot extension — not found
  ✗  cursor      Requires Cursor IDE — not found

Default adapter: noop  (set via "devspark adapter default <name>")
```

### Output — Non-TTY

```
adapter noop available
adapter manual available
adapter claude_code unavailable requires_cli=claude
adapter copilot unavailable requires_cli=gh
adapter cursor unavailable requires_cli=cursor
default_adapter noop
```

---

## `devspark adapter default`

Set the default execution adapter stored in user config.

### Synopsis

```
devspark adapter default <name>
```

### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `name` | string | Yes | Adapter name (must be a registered adapter) |

### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Default saved |
| `1` | Unknown adapter name |

### Output

```
Default adapter set to: noop
Config: C:\Users\markh\AppData\Local\devspark\config.json
```

### Behavior

- Persists to `platformdirs.user_config_dir("devspark") / "config.json"`
- Does not require the adapter to be currently available
- Overrides can still be applied per-run via `--adapter <name>`

---

## `devspark doctor`

Run system health checks and print remediation hints.

### Synopsis

```
devspark doctor
```

### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | All checks passed |
| `1` | One or more checks failed |

### Output — TTY

```
DevSpark Doctor

  ✓  Python >= 3.11          (3.12.0)
  ✓  pydantic importable     (2.7.1)
  ✓  .devspark/ present
  ✓  agents-registry.json readable  (3 agents registered)
  ✓  git available            (/usr/bin/git)
  ✗  claude CLI not found
       Install: https://claude.ai/cli
  ⚠  copilot extension not found  (gh extension install github/gh-copilot)

2 issues found — run "devspark adapter list" to see adapter availability
```

### Checks (in order)

1. Python ≥ 3.11 — `sys.version_info`
2. pydantic importable — `import pydantic`
3. `.devspark/` directory present in repo root
4. `agents-registry.json` readable and valid JSON
5. `git` available — `shutil.which("git")`
6. Per-agent checks from registry: `requires_cli` present in PATH; `install_url` shown when absent

### Output — Non-TTY

```
check_pass python 3.12.0
check_pass pydantic 2.7.1
check_pass devspark_dir
check_pass agents_registry 3 agents
check_pass git /usr/bin/git
check_fail claude_code requires_cli=claude install_url=https://claude.ai/cli
check_warn copilot requires_cli=gh extension=github/gh-copilot
doctor_fail 2 issues
```

---

## Global Behaviors

### TTY Detection

All commands detect `sys.stdout.isatty()`:
- **TTY = True**: Rich-formatted output (colors, tables, panels, spinners)
- **TTY = False**: Plain-text structured output suitable for CI log parsing; exit codes are the primary signal

### Spec File Loading

`devspark harness run` and `devspark harness validate` accept both `.yaml`/`.yml` and `.json` spec files. File type is detected by extension.

### Error Format

All errors write to stderr. Format:
```
Error: <message>
  Detail: <optional detail>
  Fix: <optional remediation hint>
```

### Version Mismatch (FR-027)

When a spec file has an unsupported `apiVersion`, the command exits immediately with code `3` before any execution:

```
Error: unsupported apiVersion "devspark.ai/v2"
  Expected: devspark.ai/v1
  File: my-harness.yaml
  Fix: Update apiVersion to "devspark.ai/v1"
```
