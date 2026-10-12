---
description: Trace "how is X done?" against current code and .knowledge/, verifying sync/accuracy/completeness and updating or drafting knowledge as needed
handoffs:
  - label: Repo-Wide Audit
    agent: devspark.site-audit
    prompt: Run a full audit now that this topic's knowledge is in sync
  - label: Sweep Unrelated Stale Content
    agent: devspark.release
    prompt: Clean up unrelated stale work products or knowledge noticed during this trace
  - label: Spec the Missing Behavior
    agent: devspark.specify
    prompt: This topic revealed genuinely unimplemented behavior, not just undocumented behavior
---

## Prompt Resolution

Determine the current git user by running `git config user.name`.
Normalize to a folder-safe slug: lowercase, replace spaces with hyphens, strip non-alphanumeric/hyphen chars.

Read and execute the instructions from the **first file that exists**:
1. `.devspark.work/{git-user}/commands/devspark.explain.md` (personalized override)
2. `.devspark.work/commands/devspark.explain.md` (team customization)
3. `.devspark/defaults/commands/devspark.explain.md` (stock default)

Where `{git-user}` is the normalized slug from step above.

## User Input

```text
$ARGUMENTS
```

Pass the user input above to the resolved prompt.
