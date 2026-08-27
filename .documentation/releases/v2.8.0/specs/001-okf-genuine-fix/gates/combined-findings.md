# Combined Analyze and Critic Findings

**Feature**: `001-okf-genuine-fix`  
**Generated**: 2026-08-27  
**Source gates**: [analyze.md](analyze.md), [critic.md](critic.md)  
**Overall verdict**: PROCEED. All combined action items have been applied to the planning artifacts.

## Combined Action Plan

| Priority | Source Finding(s) | Severity | Action | Files to Update | Resolution Criteria |
| --- | --- | --- | --- | --- | --- |
| 1 | analyze-003, critic-004 | SHOWSTOPPER | Applied: T054 gates constitution edits on amendment rationale, leadership approval, version/sync impact report, and migration-plan notes. | `tasks.md`, `plan.md`, `contracts/genuine-fix-discipline.md` | Resolved. |
| 2 | critic-001, critic-002, critic-003 | HIGH | Applied: spec frontmatter now includes `archetype: cli`, `risk_profile: internal`, and `change_type: brownfield`. | `spec.md` | Resolved. |
| 3 | analyze-002 | HIGH | Applied: T015-T018 require exact before/after JSON baselines for Bash and PowerShell `create-new-feature` and `setup-plan`. | `tasks.md` | Resolved. |
| 4 | analyze-001, critic-006 | HIGH | Applied: T058-T064 cover packaging, upgrade/preflight, command discovery, atomic-shim coverage, and user docs. | `tasks.md`, `plan.md` | Resolved. |
| 5 | critic-005 | HIGH | Applied: research/plan/tasks choose a shared Python validation and coverage core with Bash/PowerShell wrappers. | `research.md`, `plan.md`, `tasks.md` | Resolved. |

## Applied Remediation Edits

1. `spec.md` frontmatter now declares `archetype: cli`, `risk_profile: internal`, and `change_type: brownfield`.
2. `tasks.md` now includes T054 as the manual governance prerequisite before T055/T056 constitution edits.
3. `tasks.md` now includes T015-T018 for the four exact JSON baselines: Bash and PowerShell `create-new-feature`, plus Bash and PowerShell `setup-plan`.
4. `tasks.md` now includes T058-T064 for release packaging, upgrade/preflight, command discovery, atomic-shim coverage, and user documentation.
5. `research.md`, `plan.md`, and `tasks.md` now select a shared Python parser and coverage core with Bash and PowerShell wrappers.

## Implementation Readiness

Implementation may proceed. Start with T001-T014 so the schema, shared parser, wrappers, and contract tests are established before lifecycle command changes.
