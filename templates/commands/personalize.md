---
description: Create a personalized copy of any published speckit command prompt for the current git user.
handoffs:
  - label: List Available Commands
    agent: speckit.discover-constitution
    prompt: Show available speckit commands
scripts:
  sh: .documentation/scripts/bash/check-prerequisites.sh --json
  ps: .documentation/scripts/powershell/check-prerequisites.ps1 -Json
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

This command creates a per-user personalized copy of any published speckit command prompt.
Personalized prompts live in `.documentation/{git-user}/commands/` and take priority
over the shared defaults in `.documentation/commands/` when any speckit command runs.

### Steps

1. **Determine the git user identity**:

   ```bash
   git config user.name
   ```

   Normalize the result to a folder-safe slug:
   - Lowercase
   - Replace spaces with hyphens
   - Strip characters that are not alphanumeric or hyphens
   - Example: `"Mark Hazleton"` → `mark-hazleton`

   If `git config user.name` is empty, fall back to `git config user.email` (take the local part before `@`).

2. **Parse the command name from user input** (`$ARGUMENTS`):

   The argument should be a speckit command name, with or without the `speckit.` prefix.
   Examples of valid input:
   - `specify` → resolves to `speckit.specify.md`
   - `speckit.plan` → resolves to `speckit.plan.md`
   - `implement` → resolves to `speckit.implement.md`

   If no argument is given, list all available commands from `.documentation/commands/` and ask the user which one to personalize.

3. **Verify the source prompt exists**:

   Check that `.documentation/commands/speckit.{command}.md` exists.
   If not found, show available commands and ask the user to pick one.

4. **Create the user directory structure**:

   ```text
   .documentation/{git-user}/commands/
   ```

5. **Check if a personalized version already exists**:

   If `.documentation/{git-user}/commands/speckit.{command}.md` already exists:
   - Show the user and ask if they want to overwrite or edit the existing one
   - Default: open the existing file for review

6. **Copy and annotate the prompt**:

   Copy `.documentation/commands/speckit.{command}.md` to `.documentation/{git-user}/commands/speckit.{command}.md`.

   Add a header comment block at the very top of the personalized copy:

   ```markdown
   <!-- 
     Personalized prompt for: {git-user}
     Based on: .documentation/commands/speckit.{command}.md
     Created: {date}
     
     This file takes priority over the shared default when you run /speckit.{command}.
     Edit freely. To revert to the default, delete this file.
   -->
   ```

7. **Inform the user**:

   ```text
   Created personalized prompt:
     .documentation/{git-user}/commands/speckit.{command}.md
   
   This file will be used instead of the shared default whenever you run /speckit.{command}.
   Edit it to customize the behavior for your workflow.
   
   To revert to the shared default, simply delete the personalized file.
   ```

8. **Open the file** for editing so the user can customize it immediately.
