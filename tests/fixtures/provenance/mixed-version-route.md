---
fixture_kind: provenance
---

# Mixed-version route

## Shape

A route authored under one framework version and finished under another.

```text
spec.md          devspark_version: 7.7.1   (authored)
plan.md          devspark_version: 7.7.1   (authored)
gates/critic.md  devspark_version: 7.7.1   (that instance)
gates/verify.md  devspark_version: 7.8.0   (that instance)
```

This is the correct result, not a drift defect. The repository upgraded
mid-route; the verify gate was produced afterward and says so. Nothing
restamps `spec.md`, because `spec.md` was not regenerated.

## Old artifacts remain valid

```text
spec.md          (no devspark_version field)
gates/analyze.md (no devspark_version field)
```

A route predating the convention carries no provenance at all. Every
consumer tolerates the absence, no migration is performed, and the artifact
is not reported as defective. A future audit infers the version from
repository history for this route only — the fallback path, used because the
metadata is genuinely absent rather than because it was never read.

## What provenance does not become

No artifact accumulates a history of every command that touched it. A spec
that grew `planned_with:`, `analyzed_with:`, and `verified_with:` fields
would be a mutable lifecycle database wearing frontmatter, which is the
thing this convention exists instead of.
