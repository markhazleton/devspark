# Advanced: Direct Atomic Prompt Usage

For expert users who already know exactly which atomic prompt they need,
DevSpark exposes them directly. Most users should prefer aliases (`devspark
run create-spec`) — atomic invocation skips the safety pauses, telemetry
context, and guardrails that wrap workflows.

## When to invoke an atomic prompt directly

- You are iterating on a single step (e.g., re-running `tasks` after editing
  the plan).
- You are building muscle memory for a custom workflow before authoring its
  YAML.
- You are debugging — running one prompt to inspect its output without
  triggering downstream steps.

## How to discover atomic prompts

```pwsh
devspark help --all                       # include hidden (audience: expert) prompts
devspark help --category improvement
devspark help --audience intermediate
```

The default `devspark help` view hides every prompt with `exposed: false`
because those are legacy compatibility shims that exist only so workflows can
target them by `id`.

## Repeated-sequence hint

If you invoke three or more atomic prompts in sequence whose ids match the
first three steps of a known workflow within a 30-minute window, DevSpark
emits an advisory:

```text
Tip: try `devspark run <alias>` next time — it wraps capture-context,
classify-improvement, create-issue with the safety pauses you skipped.
```

This is a SHOULD-level hint per FR-022; behavior is otherwise unchanged.

## Caveats

- No automatic pause between steps.
- Telemetry events still fire, but `workflow_id` is the prompt id rather
  than a workflow id (downstream dashboards SHOULD treat both as first-class).
- Guardrails are NOT enforced — they live on workflows, not on individual
  atomic prompts.
- No resumable pause-state is written.

If any of those caveats matter to you, wrap the prompts in a workflow
instead.
