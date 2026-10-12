---
expected_owner: critic
expected_applicable: true
signals: [state-lifecycle, cross-boundary-interaction]
---

# Coherent but impossible condition

## Shape

A requirement describes behavior for a state the baseline system can never
actually reach. The planning artifacts are internally consistent: the
requirement is anchored, a task implements it, the plan names the component.
Nothing in a closed-world reading of the artifacts is wrong.

```text
Requirement:  When the upstream result arrives with no category assigned,
              route the record to manual review.
Baseline:     The upstream adapter assigns a default category on every
              response before the record is persisted.
Consequence:  The "no category assigned" branch is unreachable. The manual
              review path will never execute.
```

## Why Critic owns it

Establishing the defect requires reading the existing adapter and discovering
that it always populates the field. No amount of artifact cross-checking
surfaces it, because the artifacts agree with each other.

## What a correct finding looks like

Names the file and symbol that proves the field is always populated, states
that the dependent branch is unreachable, and asks for the decision: change
the condition, change the adapter, or drop the requirement.

## What a wrong finding looks like

"Consider whether the no-category case is handled." That states no evidence,
no consequence, and no decision.
