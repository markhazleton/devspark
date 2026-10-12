# Planning Review

Planning review checks a plan before any code is written. Invoke one skill and get one decision.

```text
/devspark-planning-review
```

It resolves the feature once, runs `/devspark-analyze` always and `/devspark-critic` when the change shape calls for it, then a Judge step, and returns a single planning decision:

| Decision | Meaning |
|---|---|
| `PROCEED` | Start `/devspark-implement` |
| `CONDITIONAL` | Proceed, with the listed conditions recorded |
| `STOP` | Fix the plan first; the report names the owner of each correction |

Planning review applies to full specs. Quickfix and quick-spec routes skip it.

## What each part asks

| Skill | The one question it owns | Style |
|---|---|---|
| `/devspark-analyze` | Are `spec.md`, `plan.md`, and `tasks.md` consistent, covered, and traceable, and does every knowledge reference in `context_resolved` actually resolve? | Mechanical; a stale or invented reference fails outright |
| `/devspark-critic` | Is this internally sound plan wrong about the real system: unimplementable conditions, missing operational controls, unexamined assumptions about code, dependencies, and failure? | Adversarial judgment, not a hard stop |
| Judge | Given the findings, should we proceed? | Does not discover and does not remediate; every concern cites an existing child finding |
| `/devspark-checklist` | Are the written requirements themselves clear, complete, and testable? ("Unit tests for English.") | Optional; tests the requirements, never the code |

Run `/devspark-analyze` or `/devspark-critic` directly only when you want one report without the decision.

Both read the spec by declared purpose: `/devspark-analyze` also reports a Plan that contradicts a recorded decision or changes declared behavior, and checks a conditional `qa-acceptance.md` for trace and scope, while `/devspark-critic` challenges that file's scenario quality. See [Acceptance planning](prompt-lifecycle-mapping.md#acceptance-planning-and-the-tests-pillar).

## Severity and blocking are separate

Critic rates findings from SHOWSTOPPER down to MEDIUM. Severity describes how bad a finding would be, not whether it blocks. Each finding also gets a classification: `blocking-defect`, `accepted-limitation`, `deferred-work`, or `learning`. Only a blocking defect creates mandatory work, and an unclassified finding is itself blocking. A SHOWSTOPPER can therefore be recorded as an accepted limitation if a human explicitly accepts it.

Each concern gets the smallest valid resolution: `require`, `simplify`, `accept`, or `defer`. Only `require` and `simplify` become planning tasks. A deferred discovery goes to a Future Work Plan outside the spec.

## Recovering from `STOP`

Fix the correction at its owner, then re-run:

- Plan-shaped problem: `/devspark-plan` in revise mode, then `/devspark-tasks`, then a focused review.
- Task-shaped problem: `/devspark-tasks`.

A review goes stale only when a requirement, the design, or the task scope changes. Completing tasks, changing status, or adding notes or verification evidence never invalidates it.

## Keeping upstream planning current

Plan records the spec fingerprint it consumed; Tasks records its Plan fingerprint. `/devspark-next`
routes a stale Plan to Plan and stale Tasks to Tasks. Missing or unusable legacy fingerprints are
`unknown`, never an automatic reroute. Pending decisions, Judge stops, and review invalidation
take precedence: a changed spec after Planning Review goes to review first.

Before Judge, rerunning Plan reconciles the draft against the current spec. After Judge, content
revision needs Judge-owned remediation or explicit human authority with current review evidence.
Plan restamping alone does not invalidate Planning Review; Tasks can restamp without rewriting
when its projection is coherent. Tasks freshness covers `plan.md`, not changes confined to its
optional supporting artifacts.

## Checklist example

```text
/devspark-checklist security
```

Checklist items ask about requirement quality (for example, "Are authentication failure responses specified for every endpoint?"), never about whether code works. Anti-pattern: "Verify the button renders" belongs in a test, not a checklist. You can keep several checklists per feature, one per theme.

## Related

- [Troubleshooting](troubleshooting-usage.md): where planning review sits on each route.
- [Skill Catalog](prompt-lifecycle-mapping.md#lifecycle-detail): the detailed contract for each skill.
