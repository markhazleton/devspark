# Contract: Exit Code Registry

Centralized exit-code registry for all DevSpark CLI subcommands and adapters. Add new entries here when introducing user-facing exit codes to avoid collisions.

## General

| Code | Constant | Meaning |
|------|----------|---------|
| 0 | `EXIT_OK` | Success |
| 1 | `EXIT_GENERIC` | Generic failure (no specific category applies) |
| 2 | `EXIT_USAGE` | Invalid CLI usage / unknown flag |

## Workflow runner

| Code | Constant | Meaning |
|------|----------|---------|
| 20 | `EXIT_AUTONOMY_REQUIRED` | Non-interactive run with no autonomy policy from any input channel (FR-016) |
| 21 | `EXIT_GUARDRAIL_BLOCKED` | Autonomous run aborted because guardrail violation could not be downgraded |
| 22 | `EXIT_WORKFLOW_INVALID` | Workflow definition failed schema validation |
| 23 | `EXIT_ALIAS_INVALID` | Alias definition failed schema validation or chain check |
| 24 | `EXIT_PROMPT_UNKNOWN` | Workflow references an atomic prompt that does not resolve |
| 25 | `EXIT_RESUME_FAILED` | `devspark resume` could not load or replay the persisted run state |

## Issue adapter (`src/devspark_cli/issues.py`)

| Code | Constant | Meaning |
|------|----------|---------|
| 10 | `EXIT_GH_UNAVAILABLE` | `gh` CLI not installed or not on PATH |
| 11 | `EXIT_GH_UNAUTHENTICATED` | `gh` CLI present but not authenticated |
| 12 | `EXIT_GH_API` | GitHub API returned an error |
| 13 | `EXIT_GH_NETWORK` | Network unreachable or DNS failure |

## Reservation policy

- Codes 0–9: reserved for general/usage outcomes.
- Codes 10–19: reserved for the issue adapter.
- Codes 20–29: reserved for the workflow runner.
- Codes 30–49: reserved for future adapters (PR adapter, telemetry sink adapter).
- Codes 50+: free for new feature areas; add an entry here in the same PR that introduces them.
