# Contract: Adapter Doctor / Preflight Capability Profile

## Scope

Defines normalized capability output used to approve or block hands-off execution.

## Required Fields

- `adapter`: string
- `state`: `ready` | `write_approval_required` | `write_incompatible` | `unavailable`
- `is_available`: boolean
- `can_execute_read_only`: boolean
- `can_execute_write`: boolean
- `requires_write_approval`: boolean
- `diagnostics`: array[string]
- `remediation_guidance`: string|null

## Behavioral Requirements

1. Hands-off mode MUST refuse write-required stages when `state` is not `ready`.
2. Runner MUST fail fast before executing blocked stages and emit actionable remediation.
3. Adapter state classifications MUST be based on executable behavior probes, not registration metadata alone.
4. Diagnostics MUST include at least one actionable next step when state is `write_approval_required`, `write_incompatible`, or `unavailable`.
