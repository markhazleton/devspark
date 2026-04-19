# Contract: Adapter Doctor / Preflight Capability Profile

## Scope

Defines normalized capability output used to approve or block hands-off execution.

## Required Fields

- `adapter`: string
- `state`: `available` | `read-only-works` | `write-approval-required` | `unusable`
- `write_capable_non_interactive`: boolean
- `diagnostics`: array[string]
- `remediation_actions`: array[string]

## Behavioral Requirements

1. Hands-off mode MUST refuse write-required stages when `write_capable_non_interactive` is `false`.
2. Runner MUST fail fast before executing blocked stages and emit actionable remediation.
3. Adapter state classifications MUST be based on executable behavior probes, not registration metadata alone.
4. Diagnostics MUST include at least one actionable next step when state is `write-approval-required` or `unusable`.
