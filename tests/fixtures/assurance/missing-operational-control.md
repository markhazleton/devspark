---
expected_owner: critic
expected_applicable: true
signals: [new-entry-point, cross-boundary-interaction]
---

# Missing operational control

## Shape

A change introduces a new externally reachable write path. The artifacts
specify the behavior completely and correctly. No requirement asks for a way to
turn the path off, and so no task creates one.

```text
Change:       New endpoint accepts submissions and writes them downstream.
Artifacts:    Fully specified; every requirement has a task.
Absent:       No disable switch, no rollback posture, and no signal that
              would show the path misbehaving in production.
```

## Why Critic owns it

Nothing is inconsistent. The gap is between what the artifacts say and what
operating the result would require. Analyze cannot surface a task that no
requirement called for — by construction it only maps stated requirements to
stated tasks.

## What a correct finding looks like

Names the specific control that is absent, the operational scenario that needs
it, and the concrete task that would close it. A finding that says "ensure
observability" fails the quality bar: no scenario, no evidence, no decision.
