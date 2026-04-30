# Harness Engineering

DevSpark's harness runtime is an optional CLI execution layer for repeatable engineering workflows. It is additive: the prompt-first slash-command workflow remains unchanged, while the CLI adds a way to validate, execute, and inspect declarative workflow specs.

This page documents what is currently implemented in the repository.

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
