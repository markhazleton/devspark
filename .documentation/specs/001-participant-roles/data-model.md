# Data Model: Participant Roles

## Entity: Agent

An AI runtime or client integration that executes DevSpark prompts.

Fields:

- `key`: Stable integration key from `agents-registry.json`.
- `name`: Human-readable integration name.
- `context_file`: Runtime-specific context file path.
- `release.commands_dir`: Runtime-specific command shim location.

Rules:

- `agent` terminology remains tied to runtime/client integration.
- Participant role names must not be added to `agents-registry.json`.

## Entity: Prompt

A DevSpark command or workflow instruction surface.

Fields:

- `command_name`: Slash-command name such as `/devspark.plan`.
- `lifecycle_responsibilities`: Scope checks, script invocation, artifact
  placement, gates, and handoffs.
- `delegated_skills`: Optional portable skills used by the prompt.

Rules:

- Prompts own DevSpark lifecycle behavior.
- Prompts do not become participants.

## Entity: Skill

A reusable portable capability package.

Fields:

- `name`: Skill package name.
- `description`: Discovery text.
- `metadata.version`: Skill package version.
- `resources`: Optional scripts, references, and assets.

Rules:

- Skills provide reusable know-how.
- Skills do not own participant responsibility metadata unless a future spec
  defines skill-specific behavior.

## Entity: Participant

A human or AI-filled team member carrying responsibility for work, review,
approval, or decision capture.

Fields:

- `role`: Responsibility label.
- `kind`: Lightweight fill type: `human` or `ai`.
- `name`: Optional display label.

Rules:

- Participant metadata is advisory.
- Missing participant metadata is valid.
- Personal names are optional and not recommended in stock examples.
- Teams own PII handling for any personal names they choose to record.

## Entity: Participant Metadata

Optional YAML frontmatter block carried by spec, plan, and task artifacts.

Example:

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

Compact examples may use role-to-kind values where readability is better:

```yaml
participants:
  owner: human
  planner: ai
  reviewer: human
```

Rules:

- Both compact and expanded examples are advisory unless tests choose one form
  as the stock template convention.
- `kind` values in stock examples should be `human` or `ai`.
- Role names are advisory and not a closed validation set.
- Commands must not fail when this block is absent.

## State Transitions

Participant metadata has no lifecycle state in this feature.

```text
absent -> present -> edited -> absent
```

All states are valid. No command should treat the transition as a workflow gate.
