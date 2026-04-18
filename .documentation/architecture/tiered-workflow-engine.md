# Tiered Workflow Engine

DevSpark v2 organizes prompts into three tiers and resolves them through a
deterministic chain.

## Tiers

1. **Atomic prompts** (`templates/prompts/atomic/*.md`) — single-purpose
   prompts. Identified by `id:` in YAML frontmatter; categorized by
   `audience`, `category`, and `exposed`.
2. **Workflows** (`templates/workflows/*.yaml`) — ordered sequences of atomic
   prompts with `pause_after`, `when`, `on_failure`, autonomy guardrails,
   `output_type`, and `review_after` semantics.
3. **Aliases** (`templates/aliases/*.yaml`) — short names that point at a
   `target_workflow`. The recommended user-facing surface.

## Resolver chain

For each id, the runner walks tiers in order and uses the first hit:

1. App-local: `{app.path}/templates/{tier}/{id}.{ext}` when `--app <id>` is
   supplied and `.documentation/devspark.json` is in `mode: multi-app`.
2. Personal: `~/.devspark/personal/{git_user}/templates/{tier}/{id}.{ext}`.
3. Team: `.devspark/team/templates/{tier}/{id}.{ext}`.
4. Workspace stock: `templates/{tier}/{id}.{ext}` (this repo).
5. Framework stock: `.devspark/defaults/templates/{tier}/{id}.{ext}`.

Resolution is implemented in `src/devspark_cli/resolution.py` and exercised by
`tests/test_alias_resolution_contract.py` and
`tests/test_script_resolution_contract.py`.

## Multi-app mode

When `.documentation/devspark.json` declares `mode: multi-app`, the registry
in `agents-registry.json` lists each application's `id` and `path`. Passing
`--app <id>` to `devspark run` causes the resolver to prepend the app-local
templates directory to the chain. Workflows and aliases defined under
`{app.path}/templates/` shadow the workspace and framework stock for that
invocation only.

## Concurrency model

A single repo MAY run multiple `devspark run` invocations concurrently:

- Telemetry writer is concurrency-safe (OS-level exclusive lock around every
  JSONL append).
- Pause-state files are run-id-scoped (`<workflow_run_id>.json`) and use
  atomic writes.
- Guardrail enforcement assumes a per-process working-tree boundary — a single
  shared working tree across two concurrent autonomous runs is **not**
  supported. Use git worktrees for true concurrent autonomy.

## Validation

Every PR runs:

- `devspark workflows validate` — parses every YAML under
  `templates/workflows/` and `templates/aliases/` without executing.
- `pytest tests/test_workflow_schema_contract.py` — schema + fuzz coverage.
- `pytest tests/test_alias_resolution_contract.py` — resolver contract.
- `pytest tests/test_atomic_prompt_frontmatter_contract.py` — frontmatter
  contract for every file under `templates/prompts/atomic/`.
