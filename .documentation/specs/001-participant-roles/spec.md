---
classification: full-spec
risk_level: medium
risk_profile: internal
change_type: brownfield
archetype: documentation-site
target_workflow: specify-full
required_artifacts: spec, plan, tasks
recommended_next_step: plan
required_gates: checklist, analyze, critic
---

# Feature Specification: Participant Roles

**Feature Branch**: `001-participant-roles`
**Created**: 2026-05-31
**Status**: Complete
**Input**: User description: "Document participant terminology and optional participant metadata for DevSpark phase 1 and phase 2, preserving existing customization layers and keeping agent reserved for AI runtimes."

## Rationale Summary

### Core Problem

DevSpark currently uses `agent` clearly for supported AI runtimes and
integrations, but discussion around Squad-style team concepts introduces a
different meaning: a human or AI-filled team member. Without a distinct term,
future documentation and workflow metadata could blur runtime integration,
responsibility assignment, prompts, and skills.

### Decision Summary

Use `participant` for human or AI-filled team members and keep `agent` reserved
for AI runtime/client integrations. Document the vocabulary first, then add
optional participant metadata to lifecycle templates as advisory context only.

### Key Drivers

- Preserve DevSpark's existing prompt, agent, and skill boundaries.
- Prevent Squad-inspired team concepts from changing DevSpark's stable
  default, team, and individual customization process.
- Improve auditability by making ownership and review responsibilities visible
  without creating a parallel orchestration system.

### Source Inputs

- User decision to use `participants` for team members.
- DevSpark constitution principles for backward compatibility, explicit scope,
  ownership boundaries, simplicity, and platform parity.
- Existing README language that defines agents as supported AI integrations and
  skills as portable capability packages.
- Existing spec, plan, and task templates that can carry optional advisory
  metadata without changing command execution.

### Tradeoffs Considered

- Option A: Reuse `agent` for team members. Not chosen because it conflicts
  with `agents-registry.json` and supported AI runtime terminology.
- Option B: Introduce a full team orchestration model. Not chosen because it
  adds complexity before DevSpark has a proven need for execution behavior.
- Selected: Define `participant` as a responsibility-bearing team member and
  add optional metadata in templates without hard validation or new layering.

### Architectural Impact

- Documentation gains a stable glossary for prompt, agent, skill, participant,
  and role.
- Spec, plan, and task templates may include optional `participants` YAML
  frontmatter metadata.
- Existing command resolution, customization layers, script resolution, and
  agent registry behavior remain unchanged.
- Missing participant metadata remains valid and must not block workflows.

### Reviewer Guidance

Reviewers should focus on terminology precision, preservation of existing
customization layers, warning-only treatment of optional metadata, and avoiding
new inheritance or orchestration behavior.

### Assumptions

- This feature covers phase 1 and phase 2 only; reviewer lockout, scribe
  harvesting, or participant-based routing behavior is deferred.
- Existing personal, team, and stock prompt resolution remains unchanged.
- Existing team and stock script resolution remains unchanged.
- Participant metadata is advisory until a later approved spec defines behavior
  that consumes it.

## Clarifications

### Session 2026-05-31

- Q: Where should optional participant context live in generated artifacts? → A: Optional `participants` YAML frontmatter in spec, plan, and tasks templates.
- Q: Should DevSpark define a canonical participant role set for examples? → A: Use advisory canonical roles: `owner`, `planner`, `implementer`, `reviewer`, `critic`, `scribe`.
- Q: What shape should the optional `participants` YAML metadata use? → A: Map each role to a simple kind value such as `human` or `ai`.
- Q: May participant metadata include a display name field alongside role and kind? → A: Yes — an optional `name:` field is allowed; it is advisory and teams own PII handling for any personal data they choose to record.
- Q: Should commands surface participant metadata visibly in output when present? → A: No — metadata is silent / artifact-only; commands do not add a dedicated participant printout step.
- Q: How should SC-004 be validated at acceptance time? → A: SC-004 is satisfied when the existing `pytest` suite passes green with no participant metadata present in any fixture.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Understand Core Vocabulary (Priority: P1) ✅ Complete

As a DevSpark user, I want documentation to distinguish prompts, agents, skills,
participants, and roles so that I can discuss team workflows without confusing
runtime integrations with responsibility assignments.

**Why this priority**: Clear vocabulary is the foundation for every later
participant-related change.

**Independent Test**: Read the updated documentation and verify each term has a
single DevSpark-specific definition with examples.

**Acceptance Scenarios**:

1. **Given** a user reads the DevSpark lifecycle or glossary documentation,
   **When** they look up `agent`, **Then** it is defined as an AI runtime or
   client integration such as Codex, Claude, Copilot, Cursor, or Gemini.
2. **Given** a user reads the same documentation, **When** they look up
   `participant`, **Then** it is defined as a human or AI-filled team member
   responsible for work, review, approval, or decision capture.
3. **Given** a user reads the glossary, **When** they compare `prompt` and
   `skill`, **Then** prompts are described as workflow command surfaces and
   skills as reusable portable capability packages.

---

### User Story 2 - Preserve Existing Customization Layers (Priority: P2) ✅ Complete

As a DevSpark maintainer, I want participant guidance to explicitly preserve
the current default, team, and individual customization process so that new
concepts do not introduce a competing layer model.

**Why this priority**: The existing layer process is a core DevSpark value and
must remain stable while participant terminology is introduced.

**Independent Test**: Inspect changed docs and templates and confirm they do
not rename, relocate, reorder, or replace the existing customization layers.

**Acceptance Scenarios**:

1. **Given** a user reads participant documentation, **When** customization is
   discussed, **Then** the documentation states that participant concepts must
   use DevSpark's existing customization process.
2. **Given** a maintainer reviews the implementation, **When** they inspect
   prompt and script resolution documentation, **Then** the existing precedence
   remains unchanged.
3. **Given** a team has existing personal or team command overrides, **When**
   DevSpark participant documentation is added, **Then** those overrides remain
   valid and are not migrated.

---

### User Story 3 - Add Optional Participant Metadata (Priority: P3) ✅ Complete

As a DevSpark author, I want spec, plan, and task artifacts to have an optional
place to record participant context so responsibility is visible without making
the metadata mandatory.

**Why this priority**: Optional metadata improves auditability while preserving
backward compatibility for existing artifacts.

**Independent Test**: Generate or inspect stock templates and confirm they show
optional participant examples while validation guidance treats absence as valid.

**Acceptance Scenarios**:

1. **Given** a new spec is created from the stock template, **When** optional
   participant metadata is present, **Then** it identifies responsibility
   context such as owner, planner, implementer, reviewer, critic, or scribe.
2. **Given** an existing spec lacks participant metadata, **When** DevSpark
   validation or review guidance evaluates it, **Then** the missing metadata is
   at most a warning or recommendation and not a failure.
3. **Given** participant metadata is present in plan or task artifacts, **When**
   commands run or summarize artifact context, **Then** the metadata remains
   preserved in artifacts and is not surfaced through a dedicated participant
   printout step.

### Edge Cases

- Existing artifacts without participant metadata must remain valid.
- Team or personal prompt overrides that do not know about participants must
  continue to resolve normally.
- Participant metadata must not be confused with `agents-registry.json`.
- Human names may be omitted; role labels alone must be acceptable.
- Multi-app repositories must not gain a new scope resolution mechanism from
  participant metadata.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: DevSpark documentation MUST define `agent` as an AI runtime or
  client integration and MUST NOT redefine it as a team member.
- **FR-002**: DevSpark documentation MUST define `participant` as a human or
  AI-filled team member that carries responsibility in a workflow.
- **FR-003**: DevSpark documentation MUST define `prompt` as a command or
  workflow instruction surface that orchestrates DevSpark lifecycle behavior.
- **FR-004**: DevSpark documentation MUST define `skill` as a reusable portable
  capability package that can be delegated to by prompts.
- **FR-005**: Participant guidance MUST state that DevSpark's existing
  customization layers and precedence are unchanged.
- **FR-006**: Stock spec, plan, and task templates SHOULD include optional
  `participants` YAML frontmatter metadata.
- **FR-007**: Missing participant metadata MUST NOT fail the shared
  specification validation contract, task format expectations, or plan
  generation guidance.
- **FR-008**: Commands that mention participant metadata MUST describe it as
  advisory responsibility context unless a later approved spec defines
  executable behavior. Commands MUST NOT add a dedicated participant printout
  step; participant metadata is silent / artifact-only and is not surfaced in
  command output in this phase.
- **FR-009**: Participant metadata MUST NOT introduce a new upstream,
  inheritance, or override model.
- **FR-010**: Documentation updates MUST use `participant` for team-member
  concepts and reserve `agent` for supported AI integrations or agent-specific
  runtime files.
- **FR-011**: Participant examples SHOULD use the advisory canonical roles
  `owner`, `planner`, `implementer`, `reviewer`, `critic`, and `scribe`; other
  role names MUST remain valid unless a later approved spec adds validation.
- **FR-012**: Participant metadata examples SHOULD use a simple role-to-kind
  mapping, such as `owner: human`, `planner: ai`, and `reviewer: human`.
  An optional `name:` field MAY appear alongside `kind:` as a display label;
  it is advisory and MUST NOT be required. Teams that include personal names
  in `name:` are responsible for their own PII handling; DevSpark documentation
  MUST NOT recommend storing personally identifying information in the field.

### Key Entities *(include if feature involves data)*

- **Agent**: A supported AI runtime or client integration that executes
  DevSpark prompts.
- **Prompt**: A DevSpark command or workflow instruction that owns lifecycle
  orchestration.
- **Skill**: A portable capability package that owns reusable task knowledge.
- **Participant**: A human or AI-filled team member carrying responsibility for
  work, review, approval, or decision capture.
- **Role**: A responsibility label a participant may hold, such as owner,
  planner, implementer, reviewer, critic, or scribe. These role names are
  advisory examples, not a closed validation set.
- **Participant Kind**: A lightweight value describing whether a role is filled
  by a `human` or `ai` participant. It is advisory metadata, not an identity
  record.
- **Participant Name**: An optional display label that MAY accompany a
  participant entry. It is advisory only. Teams that populate it with personal
  names are responsible for their own PII handling; DevSpark does not validate,
  process, or require this field.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The updated documentation contains definitions for all five
  vocabulary terms: prompt, agent, skill, participant, and role.
- **SC-002**: At least one lifecycle-facing document explains that participant
  concepts do not change DevSpark's existing customization layers.
- **SC-003**: The stock spec, plan, and task templates each include optional
  `participants` YAML frontmatter metadata.
- **SC-004**: The existing `pytest` suite passes green (`pytest` exits 0)
  without requiring participant metadata in fixtures or pre-existing artifacts,
  confirming that prompt resolution, skill validation, workflow validation, and
  documentation audit are unaffected by this feature.
- **SC-005**: A text search for new team-member guidance shows `participant`
  usage instead of redefining `agent` outside existing AI-runtime contexts.
