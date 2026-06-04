# Data Model: Harness Delivery Integrity

## Entity: RunOutcome

- Purpose: Canonical outcome record for an end-to-end run.
- Fields:
- `run_id` (string): Unique run identifier.
- `workflow_status` (enum): `complete`, `failed`, `stalled`.
- `delivery_status` (enum): `met`, `unmet`.
- `create_pr_ready` (boolean): Derived readiness signal.
- `failure_reason_code` (string|null): Deterministic reason when failed or blocked.
- `started_at` (datetime)
- `completed_at` (datetime|null)

## Entity: DeliveryCheckResult

- Purpose: Per-check evidence used to compute delivery status.
- Fields:
- `check_id` (string)
- `check_type` (enum): `git.changed_count`, `git.changed_path_match`, `command.pass`, `artifact.exists`, `branch.sync`.
- `required` (boolean)
- `status` (enum): `pass`, `fail`, `skipped`.
- `details` (object): Rule-specific details (paths, counts, command output refs).

## Entity: AdapterCapabilityProfile

- Purpose: Normalized capability diagnosis before execution.
- Fields:
- `adapter` (string)
- `state` (enum): `available`, `read-only-works`, `write-approval-required`, `unusable`.
- `write_capable_non_interactive` (boolean)
- `diagnostics` (array[string])
- `remediation_actions` (array[string])

## Entity: StageIterationRecord

- Purpose: Evidence per remediation pass in analyze/critic loops.
- Fields:
- `stage` (enum): `analyze`, `critic`
- `pass_index` (integer, 1-based)
- `finding_deltas` (object): counts by state transitions
- `actions_attempted` (array[string])
- `revalidation_status` (enum): `converged`, `continue`, `max-pass-failed`

## Entity: Finding

- Purpose: Track review/analyze issues across passes.
- Fields:
- `finding_id` (string)
- `severity` (enum): `critical`, `high`, `medium`, `low`
- `description` (string)
- `recommended_action` (string)
- `execution_mode` (enum): `auto`, `selective`, `manual`
- `status` (enum): `open`, `resolved`, `deferred`

## Entity: DecisionPacket

- Purpose: Final handoff payload for human PR decision.
- Fields:
- `run_id` (string)
- `implementation_evidence_summary` (string)
- `open_findings` (array[Finding])
- `resolved_findings` (array[Finding])
- `merge_recommendation` (enum): `recommend_merge`, `recommend_do_not_merge`, `needs_human_review`

## Relationships

- RunOutcome 1..* DeliveryCheckResult
- RunOutcome 1..* StageIterationRecord
- StageIterationRecord 1..* Finding
- RunOutcome 1..1 AdapterCapabilityProfile (per selected adapter)
- RunOutcome 1..1 DecisionPacket

## State Transitions

- `workflow_status`: `failed|stalled -> complete` is not allowed; terminal once failed/stalled.
- `delivery_status`: starts `unmet`, transitions to `met` only when all required checks pass.
- Finding `status`: `open -> resolved|deferred`; `resolved` can reopen to `open` if revalidation fails.
