---
expected_owner: critic
expected_applicable: true
signals: [state-lifecycle]
---

# Sole required path removed as redundant

## Shape

The plan removes a guard, branch, or fallback on the stated grounds that it
duplicates another mechanism. In the baseline, the other mechanism does not
cover every case — the path being removed is the only one that satisfies a
requirement on at least one route through the system.

```text
Plan states:  The secondary eligibility check is redundant with the primary
              check and can be removed.
Baseline:     The primary check is skipped when the record arrives through
              the batch path, which only the secondary check covers.
Consequence:  Removing the secondary check leaves the batch path unguarded.
```

## Why Critic owns it

The redundancy claim is an assertion about the existing system. It can only be
confirmed or refuted by reading the paths that reach the guard. The artifacts
are internally consistent either way.

## What a correct finding looks like

Cites the path that bypasses the surviving mechanism, states which requirement
or invariant becomes unenforced, and asks whether the batch path should be
covered before the removal lands.

## Negative result is also valid

If inspection shows the surviving mechanism genuinely covers every path, there
is no finding. "I could not confirm the redundancy" is a verification
obligation, not a defect.
