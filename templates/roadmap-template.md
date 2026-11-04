# Roadmap and Prospective Spec Template

<!-- DevSpark — © 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com -->

A roadmap is optional, shift-left planning: it records product direction and the right-sized increments
that advance it. It is not a delivery workflow, a status board, or a gate. `/devspark-roadmap` owns it;
`/devspark-specify` reads a Prospective Spec only when the developer names one.

> **Roadmap the direction. Deliver through one flow. Measure outcomes. Adapt deliberately.**

## Layout

Relative to the roadmap root (default `.devspark.work/roadmap/`, or `roadmap.root` in
`.devspark.work/devspark.json`):

```text
roadmap.md
specs/
  ps-001-<slug>.md
  complete/
    ps-002-<slug>.md      resolved (complete or dropped) items, staged until release
```

`ps-NNN` identifiers are permanent and never reused. `scripts/roadmap-check.py check` reports the next
free id.

## `roadmap.md`

```markdown
# Roadmap: <product or application>

## Direction

What the application is for, who it serves, and the outcomes that matter over the planning horizon.

## Current Baseline

The factual state of the application today, with evidence (paths, commits, observed behavior).

## Themes

The few outcome areas the roadmap advances, in priority order, each linking its Prospective Specs:

- <theme>: [ps-001 <title>](specs/ps-001-<slug>.md)

## Decisions

Significant, developer-approved planning decisions and changes of direction, newest first, each with
its basis. Not every tracking observation.

## Delivered

Permanent live records of every archived Prospective Spec. Release archival repoints roadmap links to
the archived copies and adds one explicit-status line here for every item, including items already
linked elsewhere. These records preserve ids and dependency status after referring specs are archived:

- [ps-002-<slug>](<relative path to its archived copy>) — complete; archived with release <version>
- [ps-003-<slug>](<relative path to its archived copy>) — dropped; archived with release <version>
```

The checker reads these live Delivered records, never the archived copies. A bare archive link without
an explicit resolved status is `unknown` and does not satisfy dependencies. For an older record,
confirm completion or dropping from current code and Git delivery evidence, then record the
developer-approved status here. Do not infer completion from an archive link or inspect archived files.

## Prospective Spec (`specs/ps-NNN-<slug>.md`)

A Prospective Spec (PS) is the smallest cohesive, independently verifiable and shippable increment
that advances the roadmap. **Tasks divide implementation work. Prospective Specs divide deliverable
outcomes.**

```markdown
---
id: ps-NNN
title: <outcome in a few words>
status: proposed        # proposed | ready | active | complete | dropped
order: 10               # optional; lower comes first
depends_on: []          # ids of delivered prerequisites, e.g. [ps-001]
delivery: []            # branch, commit, or pull request references once delivery starts
---

# ps-NNN: <title>

## Outcome

What will exist, and why it matters.

## Current Reality

Relevant existing behavior and the evidence for it.

## Scope and Independence

In scope, out of scope, and the standalone shipping boundary: if this PS were completed and every
later roadmap item were canceled, the application would remain healthy, complete, and releasable.

## Future Health

Related technical debt to leave cleaner, compatibility concerns, and credible future options this
increment must not close off.

## Dependencies and Decisions

Delivered prerequisites, constraints, decisions that shape the delivery boundary, and open questions.

## Completion Expectations

How to recognize that the outcome is independently complete and safe.
```

Keep a PS short. It is not an implementation specification: no task lists, file-by-file plans, test
inventories, line-level instructions, or repeated status audits. Once delivery starts, the delivery
branch and its code, tests, and Knowledge own the detail. Keep only the current assessment in the PS;
Git keeps its history.

## Status

| Status     | Meaning                                                           | Location          |
| ---------- | ----------------------------------------------------------------- | ----------------- |
| `proposed` | Captured; not yet right-sized                                     | `specs/`          |
| `ready`    | Right-sized; dependencies delivered or explicitly accepted        | `specs/`          |
| `active`   | Explicitly handed to `/devspark-specify`                          | `specs/`          |
| `complete` | Delivery evidence shows the outcome shipped (merged, at minimum) | `specs/complete/` |
| `dropped`  | Intentionally not pursued; the reason stays in the PS             | `specs/complete/` |

Planning status is not delivery evidence. Merged is not necessarily deployed, deployed is not
necessarily activated, and a complete capability may legitimately ship inactive. Code and Git evidence
take precedence over a stale planning claim.
