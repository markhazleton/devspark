---
expected_owner: analyze
expected_applicable: false
signals: []
---

# Negative control: mechanical change with no behavioral surface

## Shape

A change with no persisted data effect, no boundary interaction, no lifecycle
transition, no nondeterministic dependency, and no new entry point.

```text
Examples:  A symbol renamed consistently across its call sites.
           A local extraction with identical observable behavior.
           A documentation-only edit.
           Formatting.
```

## Expected outcome

No change-shape signal fires, so Critic is not automatically applicable. A
Critic run on this shape should produce an explicit `applicable: false` with a
one-line reason — not a manufactured risk list assembled to justify having run.

Generating findings here is the failure mode this control exists to catch: with
no real hazard present, a capability under pressure to produce output will
produce generic advice instead.

## If anything is wrong

Residual concerns on this shape are closed-world ones — an inconsistent rename,
a stale reference — and they belong to Analyze.
