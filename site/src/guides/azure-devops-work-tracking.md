# Azure DevOps Work Tracking

DevSpark can read and write Azure DevOps work items. The capability is **off until you turn it
on**, and a repository that never turns it on behaves exactly as it did before — no prompts, no
warnings, no mention of work items anywhere.

---

## What it can do

| Skill | What it does | Writes? |
| --- | --- | --- |
| `/devspark-workitem-review` | Reads an item and grades it against the shared review standard | No |
| `/devspark-workitem-create` | Drafts a new item, then creates it once you confirm | Only after confirmation |

DevSpark never creates a `User Story` and never creates a work item as a side effect of another
skill. The only creation path is `/devspark-workitem-create`, invoked by you, one item at a time.
Existing items can still be read, reviewed and referenced.

Other skills become work-item aware when the integration is configured:

- `/devspark-specify` offers to review an item before a spec is drafted.
- `/devspark-create-pr` and `/devspark-update-pr` check that the work items your pull request
  references actually resolve. They only read.

## Prerequisites

1. **The Azure CLI**, on `PATH` as `az`.
2. **The `azure-devops` extension** for that CLI — `az extension add --name azure-devops`.
3. **A signed-in account** with permission to read (and, if you intend to write, to edit) items in
   the project. `az login` is enough; the integration never asks you for a token and never
   stores one.

## Turning it on

Add a `work_tracking` block to `.devspark.work/devspark.json`. The presence of that block is the
switch — no block, no work tracking:

```json
{
  "platform": "azdo",
  "organization": "example-org",
  "project": "Example Project",
  "work_tracking": {
    "default_area_path": "Example Project\\Example Area",
    "default_iteration_path": "Example Project\\Iteration 1",
    "default_work_item_type": "Task",
    "tags": ["example-tag"],
    "review_on_specify": true
  }
}
```

`default_area_path` also bounds linkage checks — any referenced item that sits outside it is
reported. Organization and project are read from the top level only, so identity can't disagree
with itself.

## Why it's safe to leave enabled

Nothing is written to Azure DevOps without a separate, explicit confirmation:

- **Reads need no confirmation.** Reviewing, reading, and reference-checking all happen freely.
- **Writes are proposed first**, showing current value beside proposed value, before anything
  changes.
- **Applying a write is a distinct, explicitly confirmed step.** A standing instruction to work
  autonomously does not count, and neither does an earlier confirmation in the same session.
- **Writes are refused if the item changed underneath the proposal**, and every applied write is
  read back and verified against what was requested.
- Retrieved work-item text is treated as untrusted, reported data — never as instructions to
  follow — and is capped, with truncation reported rather than silently dropped.
- **Posting a comment back to an item is off by default**, and confirmed separately even when a
  repository opts in.

## Related

- [Skill Catalog](prompt-lifecycle-mapping.md) — all skills and where work tracking fits among them
