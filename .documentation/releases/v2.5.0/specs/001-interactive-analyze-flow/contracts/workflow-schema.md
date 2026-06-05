# Contract: Workflow Definition Schema

YAML files under `templates/workflows/<id>.yaml` MUST conform to this schema. Validation is implemented in `src/devspark_cli/runner/loader.py` and exercised by `tests/test_workflow_schema_contract.py`.

## Top-level fields

```yaml
id: create-spec                          # required, ^[a-z][a-z0-9-]*$, matches filename
name: Create Spec                        # required, non-empty string
description: >                           # required, one-line summary
  Orchestrate specify → plan → tasks → analyze for a new feature.
output_type: reviewable-artifact         # required: reviewable-artifact | pull-request | issue-link | none
autonomy:                                # required object
  level: assisted                        # required: assisted | autonomous
  review_after:                          # optional, list of step ids
    - analyze
  guardrails:                            # required when level=autonomous
    max_files_changed: 50
    restricted_paths:
      - ".github/workflows/**"
      - ".devspark/**"
    max_total_lines_changed: 2000
steps:                                   # required, non-empty ordered list
  - id: specify
    prompt: specify                      # required, atomic prompt id
    pause_after: false                   # optional, default false
    on_failure: abort                    # optional: abort (default) | continue | pause
  - id: plan
    prompt: plan
  - id: generate-tasks
    prompt: generate-tasks
  - id: analyze
    prompt: analyze
    pause_after: true
```

## Conditional steps

```yaml
- id: assign-agent
  prompt: assign-agent
  when: "context.assign_agent == true"   # boolean expression over context keys
- id: trigger-implementation
  prompt: implement
  when: "context.assign_agent == true"
```

Expressions are restricted: `==`, `!=`, `&&`, `||`, parentheses, boolean / string / int literals, and `context.<key>` references. No function calls, no loops.

## Validation rules

| Rule | Error code |
|------|------------|
| File `id` field MUST equal filename minus `.yaml` | `WF_ID_MISMATCH` |
| Every `prompt` MUST resolve to an atomic prompt | `WF_PROMPT_UNKNOWN` |
| Step ids MUST be unique within the workflow | `WF_STEP_DUPLICATE` |
| `autonomy.level` MUST be one of the enum values | `WF_AUTONOMY_INVALID` |
| `autonomy.guardrails` MUST be present when `level=autonomous` | `WF_GUARDRAILS_REQUIRED` |
| `when` expression MUST parse | `WF_WHEN_PARSE` |
| `output_type` MUST be one of the enum values | `WF_OUTPUT_TYPE_INVALID` |
| Any `review_after` entry MUST reference an existing step id | `WF_REVIEW_AFTER_UNKNOWN` |

## Compatibility

This schema is `schema_version` implicit "1". A future breaking change MUST add a top-level `schema_version: <int>` field; absence means version 1.
