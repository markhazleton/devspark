# Harness Engineering

DevSpark's harness runtime is an optional CLI execution layer for repeatable engineering workflows. It is additive: the prompt-first slash-command workflow remains unchanged, while the CLI adds a way to validate, execute, and inspect declarative workflow specs.

This page documents what is currently implemented in the repository.

> **CLI required** — Everything on this page requires the DevSpark CLI. Install it once with:
>
> ```bash
> uv tool install devspark-cli --force --from git+https://github.com/markhazleton/devspark.git
> ```
>
> Prompt-first slash commands (`/devspark.*`) work without the CLI and are documented in the [Implementation Lifecycle Guide](implementation-lifecycle.md).

---

## devspark.run — Development Workflow Aliases

`devspark run <alias>` is the fastest path through the spec-driven development cycle when the CLI is installed. It chains atomic prompts into a single terminal command with built-in pause points and structured artifact output.

**These are CLI-only commands.** There is no `/devspark.run` slash command and no backing file exists in `.claude/commands/`. Without the CLI, run the atomic commands manually in sequence (see [Without the CLI](#without-the-cli) below).

### Available Aliases

| Alias | Chains | Pause point | Output |
|-------|--------|-------------|--------|
| `create-spec` | `specify → plan → tasks → analyze` | After `analyze` — review before implementing | Reviewable spec artifact |
| `execute-plan` | `implement → create-pr → pr-review` | After `create-pr` — confirm PR before review runs | Pull request |
| `suggest-improvement` | `capture-context → classify-improvement → create-issue → (assign-agent) → (implement)` | None by default; pass `--yes` to skip confirmation | GitHub issue link |

### Usage

```bash
# Start a new feature from scratch
devspark run create-spec

# Execute an existing plan through to a reviewed PR
devspark run execute-plan

# File a workflow improvement against markhazleton/devspark
devspark run suggest-improvement
devspark run suggest-improvement --yes    # skip confirmation prompt
```

### Pause and Resume

`create-spec` and `execute-plan` pause at defined checkpoints so a human can review before the workflow continues. When a pause fires, the CLI prints the exact resume command:

```bash
devspark resume <run_id>
```

Pause state is saved at `.documentation/telemetry/runs/<run_id>.json`. On resume, DevSpark verifies the persisted `schema_version`, `workflow_id`, and `context_checksum` — any mismatch exits with code 25 (`EXIT_RESUME_FAILED`).

Active paused runs can be listed with:

```bash
devspark runs list
```

### Full Development Cycle with devspark.run

The two aliases cover the entire feature lifecycle when used in sequence:

```text
devspark run create-spec
# → review analyze output, then resume or continue:
devspark run execute-plan
# → review and merge PR, then release:
devspark release <version>
```

For the full command order including release, see the [Full Development → Release Cycle](index.md#full-development--release-cycle) on the home page.

### Without the CLI

Use the atomic slash commands directly in your agent:

| `devspark.run` alias | Manual equivalent (no CLI required) |
|----------------------|-------------------------------------|
| `create-spec` | `/devspark.specify` → `/devspark.plan` → `/devspark.tasks` → `/devspark.analyze` |
| `execute-plan` | `/devspark.implement` → `/devspark.create-pr` → `/devspark.pr-review` |
| `suggest-improvement` | `/devspark.specify` with improvement framing, then file the issue manually |

---

## When to Use It

Use the harness runtime when you need terminal-driven execution, repeatable local validation, or a structured audit trail for a workflow that should run the same way more than once.

Good fits:

- validate a harness spec before using it in a repeatable workflow
- run a repo or app-scoped engineering sequence and capture artifacts
- inspect why a prior run failed, retried, or aborted
- verify adapter availability on a new machine

Less suitable fits:

- ad hoc product work that already fits the prompt-first `/devspark.*` flow
- one-off changes where a full execution spec would add more overhead than value

## Command Surface

These are CLI commands, not slash commands.

```bash
devspark doctor
devspark harness validate sample.harness.yaml
devspark harness run sample.harness.yaml --dry-run
devspark harness trace latest
devspark adapter list
devspark adapter default claude_code
```

### `devspark doctor`

Checks whether the current environment is ready for harness workflows.

Current checks include:

- Python 3.11+
- `pydantic` importability
- compatible project layout
- readable and valid `agents-registry.json`
- `git` availability
- required local CLIs for agent integrations that declare `requires_cli`

The command accepts both installed-project layouts with `.devspark/` and compatible source checkouts with `.documentation/`, `pyproject.toml`, and `src/devspark_cli/`.

### `devspark harness validate`

Loads a YAML or JSON harness spec, validates it against the current Pydantic model and schema expectations, and exits without executing any steps.

Use it before committing a new spec or before a real run.

### `devspark harness run`

Executes a harness spec sequentially, evaluates validations after each step, persists artifacts, and returns structured exit codes.

Important current behavior:

- exit codes are `0` complete, `1` failed, `2` aborted, `3` validation error
- `--dry-run` writes a run record without executing step actions
- `--adapter` overrides the adapter for executable steps
- `--adapter-default` uses the saved user default adapter when present

### `devspark harness trace`

Reads `events.jsonl` from a prior run and renders the recorded event stream. Use an explicit run ID or `latest`.

### `devspark adapter list`

Lists the built-in adapters, whether each is available on the current machine, and the currently saved default.

### `devspark adapter doctor`

Produces normalized readiness states for each adapter:

- `ready`
- `write_approval_required`
- `write_incompatible`
- `unavailable`

Use this before hands-off lifecycle runs to confirm the selected adapter can execute write-required stages without interactive approval.

### `devspark adapter default`

Persists a local default adapter in the user's config directory. This does not modify `.devspark/` or `.documentation/`, so upgrades do not overwrite the preference.

## Built-In Adapters

The current built-in adapters are:

- `noop`
- `manual`
- `claude_code`
- `copilot`
- `cursor`

### `noop`

Safe default for contract tests, dry runs, and environments without an AI tool installed.

### `manual`

Displays the prompt for a human operator and waits for an acknowledgement keypress. It requires a TTY. In non-interactive contexts it fails clearly instead of silently skipping the gate.

### `claude_code`, `copilot`, `cursor`

These adapters call the corresponding local CLI if it is installed. Prompt content is sent through standard input rather than as a command-line argument, which avoids Windows command-length issues for larger prompts.

## Spec Model

Harness specs are YAML or JSON documents with:

- `apiVersion: devspark.ai/v1`
- `kind: HarnessSpec`
- `name`
- `scope`
- `defaults`
- `steps`
- `telemetry`

The checked-in example is [sample.harness.yaml](../sample.harness.yaml).

Step types currently implemented:

- `agent_task`
- `validation`
- `human_gate`

Validation rule types currently implemented:

- `always.pass`
- `file.exists`
- `file.contains`
- `command.exit_code`
- `json.schema`
- `git.clean`
- `regex.match`

## Scope Resolution

Harness runs support repository scope and application scope.

- `scope.type: repo` writes under the repository's `.documentation/devspark/runs/`
- `scope.type: app` requires a valid multi-app registry and resolves the documentation root through the existing scope system

Current guardrails:

- the repository root is derived from the spec path, not the caller's current working directory
- malformed or path-invalid multi-app registries fail clearly instead of being treated as missing
- ambiguous scope resolution is surfaced as a harness spec error

## Run Artifacts

By default, telemetry writes to `.documentation/devspark/runs/<run-id>/`.

Current artifact layout includes:

- `spec.resolved.yaml`
- `context.json`
- `events.jsonl`
- `result.json`
- `adapter-doctor.json`
- `decision-packet.json`
- `steps/<step-id>/prompt.md` when a prompt was materialized
- `steps/<step-id>/output.txt` when an adapter produced output
- `steps/<step-id>/stdout.txt` for `command.exit_code` validation output

Conditional artifacts:

- `no-change-explainer.md` when workflow completed but delivery evidence was unmet
- `max-pass-failure-report.md` when hands-off convergence reaches max passes without resolution

Runs are retained with a user-configurable limit. The default retention limit is `20`.

## Retry and Validation Behavior

After each executable step, the runner evaluates the declared validations.

- error-severity failures block success
- warning-severity failures are recorded but do not block the run
- retry policies can request another attempt on validation failure
- retry repair prompts append a `## Validation Errors` section to the next adapter prompt
- `requireHumanAfter` can force a manual pause after a configured attempt count

If a run is interrupted, the current implementation preserves the artifacts already written and records the run as `aborted`.

## Operator Guidance

Recommended flow for a new spec:

1. Run `devspark doctor` on the target machine.
2. Validate the spec with `devspark harness validate <spec.yaml>`.
3. Run a dry run first with `devspark harness run <spec.yaml> --dry-run`.
4. Inspect the generated artifacts and the resolved spec.
5. Execute a real run only after the adapter and validation behavior are what you expect.

For adapter-driven runs, prefer explicit adapters in the spec when reproducibility matters across machines. Use a saved adapter default when you want a machine-local convenience setting.

## Hands-Off Troubleshooting

- If run fails with `write_incompatible_adapter`, switch to a write-capable non-interactive adapter and rerun `devspark adapter doctor`.
- If `delivery_status` is unmet, review `no-change-explainer.md` and ensure changes exist under `src/` or `test/`.
- If convergence fails after max passes, inspect `max-pass-failure-report.md` and resolve remaining findings manually before retrying.

## Relationship to the Prompt Workflow

The harness runtime does not replace DevSpark's prompt-first lifecycle.

- use slash commands to define, plan, implement, review, and release work
- use the harness runtime when you need repeatable terminal-driven execution and traceable run artifacts

That separation is intentional: prompt workflows manage human and agent collaboration, while the harness runtime executes declarative engineering flows.

## Test Coverage

The harness runtime is covered by two kinds of tests, both under `tests/`:

### pytest test modules (run via `pytest tests/`)

These use standard `def test_*` functions and are picked up automatically by the test runner.

| File | Tests | What it covers |
|------|-------|----------------|
| `test_delivery_status_contract.py` | 2 | Delivery gate logic: `unmet` when no `src/` or `test/` changes; `met` when `src/` changes present |
| `test_convergence_loop_contract.py` | 2 | Finding state transitions (`open`, `resolved`, `deferred`); stage iteration record structure |

Run: `pytest tests/ -v`

### Runnable contract scripts (run directly via `python`)

These use a `main()` entry point and validate end-to-end CLI behavior through `typer.testing.CliRunner` or subprocess. CI runs them in the `contract-validation` job.

| File | What it covers |
|------|----------------|
| `test_harness_validation_contract.py` | `devspark harness validate` — loads and validates a spec YAML against the schema |
| `test_harness_spec_contract.py` | Spec model parsing, field validation, and constraint checking |
| `test_harness_runner_contract.py` | Full harness run lifecycle — artifacts written, exit codes, retry and abort paths |
| `test_harness_adapters_contract.py` | Adapter routing via `agents-registry.json`, step-level adapter resolution |
| `test_adapter_doctor_contract.py` | `devspark adapter doctor` — normalized readiness states (`ready`, `write_approval_required`, `write_incompatible`, `unavailable`) |
| `test_hands_off_lifecycle_contract.py` | `--hands-off` flag — write-incompatible adapter triggers abort; `decision-packet.json` and `result.json` artifacts created |

Run individually: `python tests/test_harness_runner_contract.py`

Run all: `python tests/test_harness_validation_contract.py && python tests/test_harness_spec_contract.py && python tests/test_harness_runner_contract.py && python tests/test_harness_adapters_contract.py && python tests/test_adapter_doctor_contract.py && python tests/test_hands_off_lifecycle_contract.py`
