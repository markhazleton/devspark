---
fixture_kind: verify-applicability
shapes: [runtime-configuration, deployment-state-assumption, datastore-semantics]
---

# Verify applicability by change shape

## Indicated — runtime configuration over deployed state

A change alters how a setting resolves at runtime. Every test supplies the
setting itself, so the suite proves the resolution logic and nothing about
the configuration already deployed.

```text
Empirical verification: REQUIRED (end-to-end)
Reason: runtime-configuration — resolution depends on the shape of
        configuration already present in the target environment
```

## Indicated — real datastore semantics

A query is rewritten. The tests run against an in-memory substitute whose
ordering, collation, and index behavior are not the engine's.

```text
Empirical verification: REQUIRED (end-to-end)
Reason: datastore-semantics — the substitute used in every covering test
        does not reproduce the engine's ordering guarantees
```

## Not indicated — contained local refactor

A symbol is renamed across its call sites. Nothing resolves at runtime,
nothing crosses a boundary, no deployed state is assumed.

```text
Empirical verification: NOT REQUIRED
Reason: no verify-sensitive change shape — local rename with no
        environment-dependent behavior
```

The negative answer is still reported. A silent omission and a reasoned
"not required" look identical in the artifact unless the reason is written
down, and only one of them can be disagreed with.

## What this is not

Shape makes a mode recommended. Declaring it in `required_gates` is what
makes it required, and that remains a human act. A proof mode needing live
traffic, a production-like environment, or anything with a cost is proposed
and authorized — never assumed because a shape matched.
