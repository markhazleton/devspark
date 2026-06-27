# Getting Started with DevSpark Workflows

> **CLI required** — `devspark run` is a CLI command, not a slash command. No `/devspark.run` slash command exists. Install the CLI first:
>
> ```bash
> uv tool install devspark-cli --force --from git+https://github.com/markhazleton/devspark.git
> ```
>
> To work without the CLI, run the atomic slash commands manually instead — see [Harness Engineering](../harness-engineering.md) for the manual equivalents.

DevSpark v2 ships three flagship aliases that wrap the core spec-driven flow.
Run them via `devspark run <alias>` in your terminal.

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

## 4. `full-cycle` — The entire lifecycle, fewer checkpoints

```pwsh
devspark run full-cycle
```

Chains all nine steps in one alias: `specify → plan → tasks → critic → analyze → tasks (remediate) → implement → create-pr → pr-review`. Unlike the three aliases above, `full-cycle` declares `autonomy.level: autonomous` with guardrails (`max_files_changed`, `restricted_paths`, `max_total_lines_changed`) instead of `pause_after` checkpoints — it's for users who explicitly want fewer human gates, not a safer default.

Two important caveats:

- **`devspark run full-cycle` still needs a driving agent.** This CLI layer sequences steps and tracks telemetry/guardrails, but its invoker only prints which prompt to invoke next — it does not itself call an LLM. It's meant to be run from inside an agent session (the agent reads the printed instruction and executes the corresponding `templates/commands/*.md` prompt itself), the same as `create-spec`/`execute-plan`.
- **For genuinely unattended execution** (no agent watching — e.g., a scheduled or CI-triggered run), use the harness-runtime equivalent instead, which does shell out to a real adapter CLI:

  ```pwsh
  devspark adapter doctor
  devspark harness run full-cycle.harness.yaml --adapter claude_code --hands-off
  ```

  See [Harness Engineering](../harness-engineering.md#full-unattended-lifecycle) for the full-cycle harness spec, its validation rules, and the convergence-loop caveat.

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

## Template discovery (install / packaging note)

The runner resolves aliases, workflows, and atomic prompts via the
following repo-relative chain (first match wins):

1. `<app>/.documentation/templates/<kind>/` — multi-app override
2. `.documentation/<git-user>/templates/<kind>/` — personal override
3. `.documentation/templates/<kind>/` — team override
4. `templates/<kind>/` — source repo (DevSpark itself)
5. `.devspark/templates/<kind>/` — installed framework payload

For consumers installed via `pip install devspark-cli`, only paths 1–3
and 5 are searched at runtime; the wheel does **not** ship
`templates/aliases/*.yaml`, `templates/workflows/*.yaml`, or
`templates/prompts/atomic/*.md` as importable package data. The standard
install path provisions `.devspark/templates/` (see `quickstart/`), so
this is only a concern if you skipped the framework-extraction step.

For repository-scoped fixes (process suggestion **M-03** from
`.documentation/specs/pr-review/pr-28.md`): when a feature spec PR grows
beyond ~50 files / ~1k LOC, prefer splitting along the
`spec → runner → prompts/workflows → cli → docs` boundary so revert and
bisect remain low-cost.
