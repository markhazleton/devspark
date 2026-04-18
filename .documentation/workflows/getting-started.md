# Getting Started with DevSpark Workflows

DevSpark v2 ships three flagship aliases that wrap the core spec-driven flow.
Run them via `devspark run <alias>` (or your agent's `/devspark.run` slash
command).

## 1. `create-spec` — From idea to ready-to-implement spec

```pwsh
devspark run create-spec
```

Steps:

1. `specify` — capture the feature in `.documentation/specs/NNN-<slug>/spec.md`.
2. `plan` — produce `plan.md`, `data-model.md`, contracts/.
3. `tasks` — break the plan into `tasks.md`.
4. `analyze` — final pass; **the workflow pauses here** so you can review.

After review, resume with `devspark resume <run_id>` (the pause prints the
exact command).

## 2. `execute-plan` — From spec to PR

```pwsh
devspark run execute-plan
```

Steps:

1. `implement` — execute `tasks.md`.
2. `create-pr` — open the pull request. **The workflow pauses here.**
3. `pr-review` — constitution-aware review of the PR.

## 3. `suggest-improvement` — File a workflow/prompt improvement

```pwsh
devspark run suggest-improvement
```

Captures context, classifies the proposal, and files an issue against
`markhazleton/devspark` via `gh api`. Pass `--yes` to skip the
confirmation prompt; non-interactive runs without `--yes` exit with
code 20 (`EXIT_AUTONOMY_REQUIRED`).

## Discovery

```pwsh
devspark help                  # aliases first, then workflows, then exposed atomic prompts
devspark help --all            # include hidden (legacy) prompts
devspark help --category improvement
devspark help --audience intermediate
devspark workflows list
devspark workflows validate    # parse every YAML under templates/workflows and templates/aliases
devspark runs list             # show paused runs
```

## Resume contract

Pause-state lives at `.documentation/telemetry/runs/<run_id>.json` (override
with `DEVSPARK_RUNS_PATH`). On resume, DevSpark verifies the persisted
`schema_version`, `workflow_id`, and `context_checksum`; any mismatch exits
with code 25 (`EXIT_RESUME_FAILED`).
