# Contract: Run Outcome and Hands-Off Convergence

## Scope

Defines required output contract for hands-off lifecycle runs and iterative analyze/critic convergence artifacts.

## Required Top-Level Fields

- `run_id`: string
- `workflow_status`: `complete` | `failed` | `stalled`
- `delivery_status`: `met` | `unmet`
- `create_pr_ready`: boolean
- `failure_reason_code`: string|null
- `delivery_checks`: array of DeliveryCheckResult
- `iterations`: array of StageIterationRecord
- `decision_packet`: DecisionPacket

## Artifact Mapping

- `decision_packet` is persisted to `decision-packet.json`
- max-pass failures are persisted to `max-pass-failure-report.md`
- delivery evidence failures are persisted to `no-change-explainer.md`

## Delivery Gate Rules

1. `create_pr_ready` MUST be `false` when `delivery_status` is `unmet`.
2. Implement-stage default evidence requires at least one changed path matching `src/**` or `test/**`.
3. Delivery evidence MUST evaluate branch-aware diffs using `git diff origin/main...HEAD -- src/ test/`, with fallback checks for staged (`git diff --cached`) and working tree (`git diff`) changes.
4. Branch sync checks MUST pass before create-pr/pr-review in hands-off mode.

## Iteration Rules

1. Analyze and critic MUST each allow up to 3 remediation passes by default.
2. After each pass, findings are re-evaluated with status in `open|resolved|deferred`.
3. A stage converges only when no blocking `open` findings remain.
4. If max pass reached with blocking findings, status MUST be `max-pass-failed` and run MUST fail.

## Decision Packet Rules

- `decision_packet.workflow_status` MUST be present.
- `decision_packet.delivery_status` MUST be present.
- `decision_packet.create_pr_ready` MUST be present.
- Packet MUST support final human PR accept/reject decision.
