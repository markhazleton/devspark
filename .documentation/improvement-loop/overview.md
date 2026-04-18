# Improvement Loop

DevSpark closes the loop on its own quality through `suggest-improvement`.

## Workflow

`devspark run suggest-improvement` runs:

1. `capture-context` — summarize the current intent and surrounding code.
2. `classify-improvement` — pick one of `bug | enhancement | prompt-quality
   | workflow-design | documentation` and produce a structured proposal.
3. `create-issue` — file the proposal as a GitHub issue against
   `markhazleton/devspark` via the typed `gh api` adapter.
4. `assign-agent` (optional, gated by `context.assign_agent == true`) —
   assign the issue to a coding agent.
5. `implement` (same gate) — kick off implementation in the same run.

## Canonical issue target

All issues are filed against **`markhazleton/devspark`** regardless of the
caller's cwd repo. The endpoint is hardcoded; no flag or env var can
re-target it. This is enforced by `tests/test_issue_adapter_contract.py`
(including an adversarial title=`--repo evil/owner` test).

## Confirmation

Before invoking `gh`, the adapter prints:

```text
About to file an issue in markhazleton/devspark:
  title:          <truncated to 200 chars>
  classification: <bug|enhancement|prompt-quality|workflow-design|documentation>
  labels:         [<single label from the classification map>]
Proceed? [y/N]:
```

Pass `--yes` to skip. In non-interactive runs, `--yes` is mandatory; absent
it the workflow exits `EXIT_AUTONOMY_REQUIRED` (20).

## GitHub issue template

Issues filed by this workflow follow `.github/ISSUE_TEMPLATE/devspark-improvement.md`,
which mirrors the body template used by the adapter.

## Classification → label map

| classification | label |
|----------------|-------|
| `bug` | `bug` |
| `enhancement` | `enhancement` |
| `prompt-quality` | `area:prompts` |
| `workflow-design` | `area:workflows` |
| `documentation` | `documentation` |
