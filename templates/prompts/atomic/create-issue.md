---
id: create-issue
name: create-issue
audience: intermediate
exposed: true
category: improvement
description: File the proposed improvement as a GitHub issue in markhazleton/devspark via the typed gh adapter.
inputs:
  - proposal.title
  - proposal.classification
  - proposal.context
  - proposal.current_behavior
  - proposal.expected_behavior
  - proposal.suggested_fix
outputs:
  - proposal.issue_url
---

## Outline

Create a new issue in `markhazleton/devspark` with `gh api`. Construct the JSON
payload as structured data and pass it through stdin; do not place
model-generated title or body content in command arguments.

## Steps

1. Display the resolved repo, title, classification, and labels for confirmation.
2. If the user declines, stop without creating an issue.
3. Call `gh api repos/markhazleton/devspark/issues -X POST --input -` with a
   JSON payload containing `title`, `body`, and labels.
4. Surface the returned URL as `proposal.issue_url`.

## Failure exit codes

| Condition | Exit code |
|-----------|-----------|
| `gh` not installed | 10 (`EXIT_GH_UNAVAILABLE`) |
| `gh` not authenticated | 11 (`EXIT_GH_UNAUTHENTICATED`) |
| GitHub API error | 12 (`EXIT_GH_API`) |
| Network unreachable | 13 (`EXIT_GH_NETWORK`) |
| User declined | Stop without changes |

## Output

```yaml
proposal:
  issue_url: https://github.com/markhazleton/devspark/issues/<n>
```
