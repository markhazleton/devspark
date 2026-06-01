# Contract: Participant Metadata

## Purpose

Define the optional `participants` YAML frontmatter shape used in stock
DevSpark examples for specs, plans, and tasks.

## Applicability

This contract applies to stock template examples only:

- `templates/spec-template.md`
- `templates/quick-spec-template.md`
- `templates/plan-template.md`
- `templates/tasks-template.md`

It does not require existing generated artifacts to include participant
metadata.

## Required Behavior

1. Existing artifacts without `participants` metadata remain valid.
2. Existing tests and fixtures without `participants` metadata continue to pass.
3. Participant metadata does not change prompt resolution, script resolution,
   workflow routing, command output, or gate enforcement.
4. Participant examples must not redefine `agent` as a team member.

## Stock Example Shape

Use optional YAML frontmatter:

```yaml
participants:
  owner:
    kind: human
  planner:
    kind: ai
  implementer:
    kind: ai
  reviewer:
    kind: human
  critic:
    kind: ai
  scribe:
    kind: ai
```

Short examples may use compact role-to-kind values:

```yaml
participants:
  owner: human
  planner: ai
  reviewer: human
```

## Optional Display Labels

Teams may add an optional `name` field when they choose to carry local display
labels:

```yaml
participants:
  reviewer:
    kind: human
    name: "Human Reviewer"
```

Stock documentation must not recommend storing personally identifying
information. Teams that add personal data own their own PII handling.

## Advisory Role Set

Stock examples should use these advisory roles:

- `owner`
- `planner`
- `implementer`
- `reviewer`
- `critic`
- `scribe`

Other role names remain valid unless a future approved spec introduces
validation.

## Non-Goals

- No participant routing.
- No reviewer lockout behavior.
- No participant registry.
- No participant inheritance or override model.
- No command output summary.
