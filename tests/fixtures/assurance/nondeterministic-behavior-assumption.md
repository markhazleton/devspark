---
expected_owner: critic
expected_applicable: true
signals: [nondeterministic-behavior]
---

# Behavior resting on nondeterministic output

## Shape

A requirement treats the output of a model, heuristic, or other
nondeterministic component as if it were a stable contract — a fixed shape, a
guaranteed field, or a value from a closed set.

```text
Requirement:  Branch on the confidence label returned by the scoring step.
Reality:      The scoring step is a model whose label set is not pinned and
              whose output is not guaranteed to be well-formed.
Consequence:  The branch has undefined behavior for any output the
              requirement did not anticipate.
```

## Why Critic owns it

Whether the component actually guarantees the assumed shape is a fact about the
system and its dependencies, not about the artifacts.

## The uncertainty boundary

If the answer cannot be settled before execution, this is **not** a defect. It
becomes a verification obligation: state the assumption, state what breaks if
it is false, and name the proof that would settle it. Critic identifies the
risk in time to plan for proof; Verify performs the proof.
