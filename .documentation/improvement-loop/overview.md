# Improvement Loop

DevSpark closes the loop on its own quality through prompt-driven improvement
capture.

## Workflow

Use this prompt sequence:

1. `capture-context` - summarize the current intent and surrounding code.
2. `classify-improvement` - pick one of `bug | enhancement | prompt-quality
   | workflow-design | documentation` and produce a structured proposal.
3. `create-issue` - file the proposal as a GitHub issue against
   `markhazleton/devspark` via the typed `gh api` adapter.
4. `assign-agent` (optional, gated by `context.assign_agent == true`) -
   assign the issue to a coding agent.
5. `implement` (same gate) - start implementation in the same agent session.

## Canonical issue target

All issues are filed against **`markhazleton/devspark`** regardless of the
caller's cwd repo. The endpoint is fixed by the prompt contract.

## Confirmation

Before invoking `gh`, the adapter prints:

```text
About to file an issue in markhazleton/devspark:
  title:          <truncated to 200 chars>
  classification: <bug|enhancement|prompt-quality|workflow-design|documentation>
  labels:         [<single label from the classification map>]
Proceed? [y/N]:
```

The user must approve issue creation before the prompt uses `gh`.

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
