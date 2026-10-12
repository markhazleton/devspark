---
description: Explain why temporary DevSpark tasks cannot be exported as durable issue-tracker records.
---

## Prompt Resolution

Determine the current git user by running `git config user.name`.
Normalize to a folder-safe slug: lowercase, replace spaces with hyphens, strip non-alphanumeric/hyphen chars.

Read and execute the instructions from the **first file that exists**:
1. `.devspark.work/{git-user}/commands/devspark.taskstoissues.md` (personalized override)
2. `.devspark.work/commands/devspark.taskstoissues.md` (team customization)
3. `.devspark/defaults/commands/devspark.taskstoissues.md` (stock default)

Where `{git-user}` is the normalized slug from step above.

## User Input

```text
$ARGUMENTS
```

Pass the user input above to the resolved prompt.
