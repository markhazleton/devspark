# Quickstart: Tiered Prompt and Workflow Engine

This quickstart shows the end-state developer experience after the feature ships. It is also the manual-validation script for SC-001 through SC-010.

## Prerequisites

- DevSpark installed (`uvx --from git+https://github.com/markhazleton/devspark.git devspark --help` works)
- `gh` CLI authenticated (only required for `suggest-improvement`)
- Python 3.11+

## 1. Discover workflows

```bash
devspark help
```

Expected: top section lists three high-level aliases — `create-spec`, `execute-plan`, `suggest-improvement` — with one-line descriptions. A second section lists advanced atomic prompts grouped by category. Hidden prompts (`exposed: false`) are not shown unless `devspark help --all` is used.

Validates: **SC-004**, FR-020, FR-021, FR-024, FR-025.

## 2. Create a spec via single entrypoint

```bash
devspark run create-spec "Add OAuth login to the admin app"
```

Expected: runner executes `specify` → `plan` → `generate-tasks` → `analyze` in order, pausing after `analyze` for human review. Output is a reviewable artifact package (spec.md, plan.md, tasks.md, analyze gate). No PR is opened.

Validates: **SC-001**, FR-005, FR-007, FR-008, US1.

## 3. Execute a plan with governance pause

```bash
devspark run execute-plan
```

Expected: runner runs `implement` → `create-pr`, pauses for human review (assisted mode default), then `review-pr` only after explicit continue. A PR is opened on continue.

Validates: **SC-002**, FR-006, FR-014, US2, US5.

## 4. Submit an improvement

```bash
devspark run suggest-improvement
```

Expected: interactive prompts capture context, classification, current/expected behavior. A GitHub issue is created in `markhazleton/devspark` and the URL is printed. If `--assign-agent` is passed, conditional steps run.

Validates: **SC-003**, **SC-009**, FR-009, FR-010, FR-011, FR-029, FR-031, US3.

## 5. Inspect telemetry

```bash
tail -n 5 .documentation/telemetry/workflow-events.jsonl | jq -c '{workflow_id, step_id, phase, success, duration_ms}'
```

Expected: each line is a valid JSON object with all required fields per `contracts/telemetry-event.md`.

```bash
DEVSPARK_TELEMETRY_PATH=/tmp/dev-events.jsonl devspark run create-spec ...
```

Expected: events written to `/tmp/dev-events.jsonl` instead.

Validates: **SC-005**, FR-017, FR-018, FR-019.

## 6. Verify autonomy guardrails

Author a workflow with `autonomy.level: autonomous` and `max_files_changed: 1`. Run a step that proposes 5 file changes.

Expected: runner emits a `guardrail_triggered` telemetry event with `guardrail_rule=max_files_changed`, downgrades to assisted mode, and pauses.

Validates: FR-013, FR-015, US5 AS-3.

## 7. Verify non-interactive policy enforcement

```bash
devspark run create-spec --non-interactive
```

Expected: exits non-zero with action-required message naming the missing autonomy policy input. Does not run any step.

Validates: **SC-006**, FR-016.

## 8. Verify backward compatibility

```bash
# Existing slash command still works in any AI agent surface
/devspark.specify "Test back-compat"
```

Expected: identical behavior to pre-feature DevSpark; `templates/commands/specify.md` resolves unchanged.

Validates: **SC-008**, FR-034, FR-035.

## 9. Verify shared review resolution contract

Run any of `clarify`, `analyze`, `critic`, `pr-review`, `address-pr-review` and inspect the resulting artifact.

Expected: each finding entry contains `finding_id`, `severity`, `description`, `recommended_action`, `execution_mode`, `status`, and (post-resolution) `outcome`.

Validates: **SC-007**, FR-026, FR-027, FR-028.

## 10. Documentation gates

```bash
ls .documentation/architecture/ \
   .documentation/autonomy/ \
   .documentation/workflows/ \
   .documentation/improvement-loop/
```

Expected: required documentation sections present before status advances from Draft.

Validates: **SC-010**, FR-032, FR-033.
