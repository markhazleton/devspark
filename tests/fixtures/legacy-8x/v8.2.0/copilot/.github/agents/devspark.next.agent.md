---
description: Detect where you are in the delivery lifecycle and run the single next DevSpark command after one confirmation.
handoffs:
  - label: Start New Work
    agent: devspark.specify
    prompt: Classify and route a new piece of work
  - label: Quick Fix
    agent: devspark.quickfix
    prompt: Start a lightweight fix for a small, contained change
---

## Prompt Resolution

Determine the current git user by running `git config user.name`.
Normalize to a folder-safe slug: lowercase, replace spaces with hyphens, strip non-alphanumeric/hyphen chars.

Read and execute the instructions from the **first file that exists**:
1. `.devspark.work/{git-user}/commands/devspark.next.md` (personalized override)
2. `.devspark.work/commands/devspark.next.md` (team customization)
3. `.devspark/defaults/commands/devspark.next.md` (stock default)

Where `{git-user}` is the normalized slug from step above.

## User Input

```text
$ARGUMENTS
```

Pass the user input above to the resolved prompt.
