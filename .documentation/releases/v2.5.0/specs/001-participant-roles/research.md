# Research: Participant Roles

## Decision: Reserve `agent` for AI runtime/client integrations

**Rationale**: DevSpark already has `agents-registry.json` and user-facing docs
that use `agent` for supported AI integrations such as Codex, Claude, Copilot,
Cursor, and Gemini. Reusing the same word for team members would make command
shims, agent context files, and participant responsibility metadata ambiguous.

**Alternatives considered**:

- Reuse `agent` for team members. Rejected because it conflicts with existing
  DevSpark terminology.
- Rename existing AI integrations. Rejected because it would create unnecessary
  migration and documentation churn.

## Decision: Use `participant` for human or AI-filled team members

**Rationale**: `Participant` works for humans and AI-filled roles without
implying a specific runtime, identity, or execution engine. It also avoids
overloading `role`, which is better used for responsibility labels.

**Alternatives considered**:

- `Role`: too narrow for a concrete team member.
- `Contributor`: already has common source-control meaning.
- `Worker`: implies execution behavior that is out of scope.

## Decision: Store optional metadata in YAML frontmatter

**Rationale**: Frontmatter is already used by DevSpark specs and prompts for
machine-readable metadata. Optional YAML metadata can be ignored by existing
commands and tests while remaining discoverable for future tooling.

**Alternatives considered**:

- Visible `## Participants` section. Rejected because this feature should keep
  participant context silent/artifact-only in command output.
- No canonical location. Rejected because templates would drift.

## Decision: Use advisory canonical roles

**Rationale**: A small role set gives examples consistent names without
creating validation behavior. The selected roles cover responsibility,
planning, implementation, review, adversarial review, and decision capture.

**Selected advisory roles**:

- `owner`
- `planner`
- `implementer`
- `reviewer`
- `critic`
- `scribe`

**Alternatives considered**:

- Minimal role set only. Rejected because `critic` and `scribe` are distinct
  DevSpark workflow responsibilities.
- Closed validation set. Rejected because teams may need local role names.

## Decision: Use simple role-to-kind values with optional names

**Rationale**: A role-to-kind map is enough for examples and avoids identity
semantics. The optional `name` field can support local teams that want labels,
but DevSpark should not require or recommend personal data.

**Alternatives considered**:

- Role-to-label only. Rejected because it does not distinguish human vs AI.
- Required objects with names. Rejected because it would create unnecessary PII
  pressure.

## Decision: Keep command output unchanged

**Rationale**: The clarified spec says participant metadata is silent and
artifact-only. Commands may preserve or ignore it, but they should not add a
dedicated participant printout step in this phase.

**Alternatives considered**:

- Print participant summaries in command reports. Rejected because it creates
  behavior before participants have workflow semantics.
