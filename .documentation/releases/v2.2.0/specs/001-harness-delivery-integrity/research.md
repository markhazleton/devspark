# Research: Harness Delivery Integrity

## Decision 1: Dual Outcome Model

- Decision: Use separate `workflow_status` and `delivery_status` in run results, with `create_pr_ready` derived from delivery gates.
- Rationale: Prevents procedural completion from being interpreted as implementation completion.
- Alternatives considered:
- Single status field with extra notes (rejected: ambiguous and easy to misread)
- Status inferred from step outcomes only (rejected: does not encode delivery evidence)

## Decision 2: Delivery Evidence Default

- Decision: Require at least one changed file under `src/**` or `test/**` for implement-stage delivery success by default.
- Rationale: Matches clarified requirement and blocks no-op implementation passes.
- Alternatives considered:
- Require both `src/**` and `test/**` changes (rejected: too strict for some valid changes)
- Allow docs/config-only success (rejected: recreates false-positive risk)

## Decision 3: Adapter Readiness and Write Capability

- Decision: Add adapter doctor/preflight with explicit states (`available`, `read-only-works`, `write-approval-required`, `unusable`) and fail-fast behavior for write-incompatible adapters on write-required stages.
- Rationale: Retrospective showed adapter registration alone is insufficient for unattended execution.
- Alternatives considered:
- Attempt runtime fallback to manual gates (rejected: violates hands-off guarantees)
- Continue with warning only (rejected: produces unpredictable outcomes)

## Decision 4: Iterative Analyze/Critic Convergence

- Decision: Run up to 3 remediation passes per stage, revalidating after each pass and failing with a convergence report if blocking findings remain.
- Rationale: Ensures deterministic iterative behavior and transparent failure state.
- Alternatives considered:
- Single auto-fix pass (rejected: insufficient for cascaded findings)
- Unlimited retries (rejected: non-deterministic and expensive)

## Decision 5: Hands-Off Lifecycle Orchestration

- Decision: Add optional single-run hands-off mode chaining `plan -> tasks -> analyze -> critic -> implement -> create-pr -> pr-review` with hard gate enforcement.
- Rationale: Aligns product behavior with target operating model (human only accepts/rejects final PR outcome).
- Alternatives considered:
- Keep pause-at-analyze and pause-at-create-pr aliases only (rejected: not true unattended flow)
- Human confirmation checkpoints in hands-off mode (rejected: contradictory to objective)

## Decision 6: Artifact and Diagnostics Contract

- Decision: Persist per-pass iteration records and final decision packet including evidence summary, findings, and recommendation.
- Rationale: Supports auditability, debugging, and deterministic downstream automation.
- Alternatives considered:
- Store only final summary (rejected: insufficient traceability)
- Emit verbose logs without structured schema (rejected: poor machine consumption)
