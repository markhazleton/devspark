# Contract: Atomic Prompt Frontmatter

Markdown files under `templates/prompts/atomic/<id>.md`. Validated by `tests/test_atomic_prompt_frontmatter_contract.py`.

```markdown
---
id: capture-context
name: Capture Context
audience: intermediate
exposed: false
category: improvement
description: Gather situational context for an improvement proposal.
inputs:
  - user_input
outputs:
  - context.summary
  - context.classification_hint
legacy_command: null
---

## Outline

<prompt body in normal Markdown>
```

## Field rules

| Field | Required | Constraint | Error code |
|-------|----------|------------|------------|
| `id` | yes | `^[a-z][a-z0-9-]*$`; equals filename minus `.md` | `AP_ID_INVALID` |
| `name` | yes | non-empty string | `AP_NAME_REQUIRED` |
| `audience` | yes | enum: `beginner` \| `intermediate` \| `expert` | `AP_AUDIENCE_INVALID` |
| `exposed` | yes | bool | `AP_EXPOSED_INVALID` |
| `category` | yes | non-empty string | `AP_CATEGORY_REQUIRED` |
| `description` | yes | non-empty string ≤ 200 chars | `AP_DESC_INVALID` |
| `inputs` | no | list of context-key strings | `AP_INPUTS_INVALID` |
| `outputs` | no | list of context-key strings | `AP_OUTPUTS_INVALID` |
| `legacy_command` | no | string or null; if set, MUST match an existing `templates/commands/<value>.md` | `AP_LEGACY_UNKNOWN` |

## Discovery rules

- `devspark help` default view shows only prompts where `exposed: true`.
- `devspark help --all` includes hidden prompts.
- Prompts are grouped by `category` and sorted by `audience` (beginner first).

## Backward-compatibility mapping

For each of the existing 28 commands under `templates/commands/`, this feature ships a thin atomic prompt under `templates/prompts/atomic/<command>.md` whose body is a one-line pointer to the canonical command file. This avoids content duplication while exposing the command id to the workflow runner.
