---
description: Implement the active route, update current knowledge and tests, verify the delta, and populate code/knowledge linkage for in-sprint validation.
handoffs:
  - label: Create Pull Request
    agent: devspark.create-pr
    prompt: Draft a pull request for the implemented changes
    send: true
---

## Prompt Resolution

Determine the current git user by running `git config user.name`.
Normalize to a folder-safe slug: lowercase, replace spaces with hyphens, strip non-alphanumeric/hyphen chars.

Read and execute the instructions from the **first file that exists**:
1. `.devspark.work/{git-user}/commands/devspark.implement.md` (personalized override)
2. `.devspark.work/commands/devspark.implement.md` (team customization)
3. `.devspark/defaults/commands/devspark.implement.md` (stock default)

Where `{git-user}` is the normalized slug from step above.

## User Input

```text
$ARGUMENTS
```

Pass the user input above to the resolved prompt.
