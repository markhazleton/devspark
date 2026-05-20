---
classification: full-spec
risk_level: medium
risk_profile: internal
change_type: brownfield
target_workflow: specify-full
required_artifacts: spec, plan, tasks
recommended_next_step: clarify
required_gates: checklist, analyze, critic
---

# Feature Specification: Add First Agent Skill (write-spec)

**Feature Branch**: `003-add-first-skill`
**Created**: 2026-05-19
**Status**: Draft <!-- Valid: Draft | In Progress | Complete -->
**Input**: User description: "Add Agent Skills support to DevSpark, starting with a write-spec skill that wraps /devspark.specify per the agentskills.io open spec"

## Rationale Summary

### Core Problem

DevSpark's spec-driven workflows are exposed today only as 28 `/devspark.*` slash-command prompts under `templates/commands/`. Each prompt uses a DevSpark-specific frontmatter contract (`handoffs`, `scripts`, `classification`) that is not interoperable with the open **Agent Skills** standard (originally from Anthropic, now adopted by a growing list of agentic clients per agentskills.io). Consequently, DevSpark's procedural knowledge cannot be discovered, loaded, or executed by skills-compatible clients without bespoke DevSpark tooling — and there is no demonstration that DevSpark's value proposition (lifecycle orchestration, governance, context engineering) is *distinct from and complementary to* the emerging skills ecosystem.

### Decision Summary

Position DevSpark as a **lifecycle orchestration layer that hosts portable Agent Skills**, not as a skills framework. Ship one portable, standalone skill — `write-spec` — that complies with the open Agent Skills specification, and refactor the existing `/devspark.specify` command to invoke that skill via a well-defined adapter contract. Existing user-facing slash-command UX remains stable; the architectural change is internal.

**Positioning statement** (for repo-level docs, FR-019):

> DevSpark treats skills as portable capability packages within a governed lifecycle orchestration system. Commands invoke skills; DevSpark governs the lifecycle around them.

### Key Drivers

- **Interoperability**: Make at least one DevSpark capability portable to any skills-compatible client.
- **Standards awareness**: Demonstrate first-class support for the open Agent Skills spec.
- **Separation of concerns**: Establish the architectural boundary `command → adapter → skill → context-gathering scripts → agent reasoning → governed artifact placement`, which most skill ecosystems currently conflate.
- **Context engineering as differentiator**: A skill in DevSpark is not just a prompt — it is a prompt plus deterministic, script-driven repository context gathering. This is the capability gap DevSpark fills above the bare skills layer.
- **Constitution alignment**: Must be additive (§I Backward Compatibility), live in the framework payload not user docs (§III Ownership Boundary), justify added complexity (§V Simplicity), preserve script parity (§VI), and pass markdownlint (§VIII).

### Source Inputs

- Agent Skills specification: <https://agentskills.io/specification>
- Reference repository: <https://github.com/agentskills/agentskills>
- Existing DevSpark command contract: `templates/commands/specify.md`, `templates/spec-validation-contract.md`
- DevSpark Constitution v1.3.0: `.documentation/memory/constitution.md`
- Tactical guidance reviewed in feature kickoff (recorded in Clarifications session 2026-05-19)

### Tradeoffs Considered

- **Option A — Replace slash-command surface with Agent Skills directly**: rejected. Breaks §I Backward Compatibility and reframes DevSpark *as* a skills framework rather than an orchestrator of skills.
- **Option B — Ship the skill standalone with no integration into existing commands**: rejected. Fails to demonstrate the architectural value (`command → invokes → skill`) that distinguishes DevSpark from a prompt collection.
- **Option C — Auto-generate skills from all 28 commands in one pass**: rejected. Premature commitment, immediate dual-maintenance burden, encourages "prompt collection syndrome" and "tiny-skill fragmentation."
- **Option D — Make `write-spec` orchestrate the full spec + plan + tasks lifecycle**: rejected for this feature (deferred). Smallest credible orchestration first; expand later if the model holds.
- **Selected — Single portable skill (`write-spec`, spec-drafting only) + adapter contract + thin-command refactor**: validates the dual-surface model end-to-end on one high-value capability before scaling.

### Architectural Impact

This feature introduces a four-phase internal restructure for the `specify` capability while preserving the user-facing command:

| Sub-phase | Deliverable | Touches |
|-----------|-------------|---------|
| 2A | **Shared skills foundations** documenting DevSpark skill conventions and how a DevSpark command invokes a skill (input mapping, output mapping, governance hooks) | `templates/skills/SKILL-validation-contract.md`, `templates/skills/ADAPTER-contract.md`, `templates/skills/references/devspark-skills-guide.md` |
| 2B | **Standalone `write-spec` skill** (`templates/skills/write-spec/SKILL.md` + `references/` + paired PowerShell/Bash `scripts/` for context gathering) that is portable to any skills-compatible client | `templates/skills/write-spec/**` |
| 2C | **Test suite** enforcing skill validation contract + adapter contract on every PR | `tests/test_skill_contract.py`, `tests/test_adapter_contract.py` |
| 2D | **Thin-wrapper refactor** of `templates/commands/specify.md` so the command performs DevSpark-specific lifecycle work (routing, branch creation, artifact placement, gating) and delegates the spec-drafting itself to the `write-spec` skill | `templates/commands/specify.md` |

Sub-phases must land in order (2A → 2B → 2C → 2D) so the adapter contract is stable before the skill is built, the test gate exists before the command refactor, and behavior parity for the command can be enforced by the existing `/devspark.specify` test suite throughout.

Other architectural notes:

- New top-level directory `templates/skills/` parallel to `templates/commands/`, `templates/prompts/`, `templates/workflows/`.
- New CLI subcommand surface for listing and validating skills, parallel to existing CLI patterns in `src/devspark_cli/`.
- No changes to user `.documentation/` artifacts in installed repos (§III Ownership Boundary).
- The other 27 `/devspark.*` commands are unchanged by this feature.

### Reviewer Guidance

Reviewers should focus on:

1. **Adapter contract clarity** (2A): does it cleanly separate skill responsibility (portable reasoning) from command responsibility (DevSpark-specific lifecycle: branch creation, artifact placement, gating, multi-app scoping)? Could a *different* skills-compatible client execute the skill standalone without any DevSpark code?
2. **Skill portability** (2B): does `SKILL.md` strictly use the open Agent Skills frontmatter dialect (no DevSpark-only keys leaking in)? Is the body ≤500 lines? Are bundled context-gathering scripts self-contained and dual-parity (PowerShell + Bash) per §VI?
3. **Context-engineering surface** (2B): does the skill demonstrate that DevSpark contributes structured context gathering (repository inspection, prior-spec lookup, constitution loading) on top of a bare prompt — not just prompt engineering?
4. **Refactor parity** (2D): does the existing `/devspark.specify` test suite still pass unchanged after the command becomes a thin wrapper? Are there any user-observable behavior differences?
5. **Scope discipline**: this feature delivers ONE skill (`write-spec`, spec-drafting only). Reviewers should reject any attempt to expand to `plan` or `tasks` skills inside this feature.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Portable skill executes in a non-DevSpark client (Priority: P1)

A developer using a skills-compatible agent client (Claude Code, Cursor, or any other client listed on the agentskills.io Client Showcase) that has **no DevSpark installation** loads the `templates/skills/write-spec/` folder. The client surfaces the skill in its discovery list. The developer asks the agent to "draft a feature spec for X." The agent activates the skill, runs any bundled context-gathering scripts, and produces a draft `spec.md` artifact that conforms to the shared spec validation contract.

**Why this priority**: This is the interoperability proof. Without it, the open-spec compliance has no observable user value and the "portable capability package" positioning is unsubstantiated.

**Independent Test**: Copy only `templates/skills/write-spec/` into a fresh workspace without DevSpark CLI installed, load it into a skills-compatible client per its standard installation flow, request a draft spec for a sample feature description, and verify the produced `spec.md` conforms to `templates/spec-validation-contract.md`.

**Acceptance Scenarios**:

1. **Given** a skills-compatible client has loaded the `write-spec` skill with no DevSpark CLI present, **When** the user asks the agent to draft a spec for a feature, **Then** the agent activates the skill (visible in its activation trace) and produces a draft `spec.md` with valid route-metadata frontmatter, the four mandatory full-spec sections, a `Draft` status line, and no more than three `[NEEDS CLARIFICATION]` markers.
2. **Given** the skill is loaded at startup, **When** the agent enumerates available skills, **Then** only the skill's `name` and `description` are loaded into context (progressive disclosure); the full body is loaded only on activation.
3. **Given** the skill's `SKILL.md` frontmatter, **When** it is parsed by an open-spec validator, **Then** it contains no DevSpark-specific keys (e.g., `handoffs`, `scripts:` in the command-prompt sense) and complies with the open Agent Skills spec.

### User Story 2 - DevSpark command invokes the skill internally (Priority: P1)

A user runs `/devspark.specify "..."` inside a DevSpark-enabled repository. The command performs DevSpark-specific lifecycle work (route classification, branch creation, multi-app scoping, artifact placement, checklist generation, gate enforcement) and delegates the actual spec-drafting reasoning to the `write-spec` skill via the documented adapter contract. The user observes **no behavior change** compared to the pre-refactor `/devspark.specify`.

**Why this priority**: This is the architectural proof. Without it, the skill is a sidecar; with it, the `command → invokes → skill` model is real and reusable.

**Independent Test**: Run the existing `/devspark.specify` test suite (`tests/test_create_spec_workflow_integration.py` and related) against the refactored command. All tests must pass unchanged. Additionally, the adapter test (`tests/test_adapter_contract.py`) must verify the command actually delegates to the skill rather than reimplementing the drafting logic.

**Acceptance Scenarios**:

1. **Given** the refactored `/devspark.specify` and the `write-spec` skill, **When** a user issues `/devspark.specify "Add user auth"`, **Then** the resulting artifacts (`spec.md`, `checklists/requirements.md`, branch creation, frontmatter) are structurally equivalent to what the pre-refactor command would have produced.
2. **Given** the adapter contract, **When** the adapter test runs, **Then** it confirms the command file references the skill and does not duplicate the drafting procedure inline.
3. **Given** a DevSpark multi-app repository, **When** a user issues `/devspark.specify --app <id> "..."`, **Then** the command resolves the app scope and the skill receives the correctly scoped paths via the adapter — multi-app scoping remains a command responsibility, not a skill responsibility.

### User Story 3 - Maintainer validates a skill before merging (Priority: P2)

A DevSpark contributor adds or edits a skill in `templates/skills/`. They run a single CLI command to validate the skill against both the open Agent Skills spec, the DevSpark skill-validation addendum, and the adapter contract. CI runs the same validation on every PR.

**Why this priority**: Without enforced validation, skills will drift from the open spec, from DevSpark conventions, and from the adapter contract — eroding the interop guarantee that motivates the feature.

**Independent Test**: Introduce a deliberate violation (uppercase letter in `name`, `description` over 1024 chars, missing required body section, or a command that references a non-existent skill) into a fixture; verify the CLI command and the test suite both fail with a precise error message naming the violated rule.

**Acceptance Scenarios**:

1. **Given** a skill folder with a valid `SKILL.md`, **When** the validation CLI command is run, **Then** it exits zero with a one-line summary including skill name and version.
2. **Given** any rule violation, **When** the validation CLI command is run, **Then** it exits non-zero with a human-readable diagnostic naming the violated rule and offending value.
3. **Given** any pull request that adds or modifies files under `templates/skills/` or under `templates/commands/specify.md`, **When** CI runs, **Then** the skill validation test AND the adapter contract test both gate merge.

### Edge Cases

- **Name/directory mismatch**: A skill's frontmatter `name` does not match its parent directory name. Validation MUST fail with a clear diagnostic per the open spec.
- **Body length budget exceeded**: A `SKILL.md` body exceeds the recommended 500-line / ~5000-token budget. Validation MUST warn and recommend moving detail into `references/`.
- **Markdownlint violations**: A new `SKILL.md` fails the repo-wide markdownlint job. Per §VIII this MUST block merge.
- **Multi-app scoping**: A user invokes `/devspark.specify --app <id>` in a multi-app repository. Multi-app resolution MUST remain a command responsibility (not pushed into the skill), since multi-app scoping is a DevSpark-specific governance concern.
- **Source-command drift**: The skill body is updated but `templates/commands/specify.md` is not (or vice versa). The adapter contract test MUST detect drift (e.g., command delegates to a skill version that no longer exposes the expected interface).
- **Bundled-script parity**: The skill bundles executable code under `scripts/`; both PowerShell and Bash variants MUST exist per §VI.
- **Conflicting frontmatter dialects**: DevSpark command frontmatter keys (`handoffs`, `scripts`, `classification`) MUST NOT appear in `SKILL.md`. Conversely, open Agent Skills frontmatter fields beyond what the adapter contract reads SHOULD NOT appear in `templates/commands/`.
- **Skill executed in a non-DevSpark client**: When invoked outside DevSpark, the skill MUST still produce a valid `spec.md` artifact in the user's current working directory — but it MUST NOT attempt DevSpark-specific operations (branch creation, multi-app resolution, gate enforcement). Graceful degradation, not failure.
- **Context-gathering script unavailable**: If a context-gathering script under the skill's `scripts/` cannot run (e.g., not in a git repo, required tool missing), the skill MUST proceed with reduced context and surface what was skipped in the produced spec's Assumptions section — never silently fail.

## Requirements *(mandatory)*

### Functional Requirements

#### Phase 2A — Adapter Contract

- **FR-001**: The repository MUST contain `templates/skills/ADAPTER-contract.md` defining how a DevSpark command invokes an Agent Skill. The contract MUST specify: (a) skill discovery (path resolution rules), (b) input mapping (how command arguments and resolved context are passed to the skill), (c) output mapping (how skill-produced artifacts are placed into DevSpark-governed paths), (d) responsibility split (which concerns belong to the command vs. the skill), and (e) backward-compatibility rules (how command behavior parity is preserved across a skill refactor).
- **FR-002**: The repository MUST contain `templates/skills/SKILL-validation-contract.md` defining (a) the open Agent Skills frontmatter rules (name/description/length limits), (b) DevSpark addendum rules (required `metadata.version`, required body sections, body-length budget, mandatory back-reference to a source command when one exists, prohibited frontmatter keys), and (c) repair rules consistent with `templates/spec-validation-contract.md` style.
- **FR-002a**: The repository MUST contain `templates/skills/references/devspark-skills-guide.md` as the shared contributor guide for DevSpark skills. The guide MUST summarize the upstream Agent Skills rules and DevSpark-specific conventions for repository layout, command-vs-skill ownership, context engineering, script parity, validation surfaces, and adding future skills.
- **FR-003**: The adapter contract MUST explicitly assign DevSpark-specific lifecycle concerns (route classification, branch creation, multi-app scoping, artifact path placement, checklist generation, gate enforcement) to the **command**, and reasoning/drafting concerns to the **skill**.

#### Phase 2B — Standalone `write-spec` Skill

- **FR-004**: The repository MUST contain a `write-spec` skill at `templates/skills/write-spec/SKILL.md` whose frontmatter strictly complies with the open Agent Skills specification (valid `name` matching the directory, non-empty `description` within length limits) and contains no DevSpark-only frontmatter keys.
- **FR-004a**: Every DevSpark-managed skill under `templates/skills/` MUST declare its version in `metadata.version` using a quoted semantic-version string. Top-level `version` frontmatter MUST NOT be used.
- **FR-005**: The `write-spec` skill's `description` MUST be discovery-rich, naming both *what* the skill does and *when* to use it, including the keywords commonly used to request a spec (draft specification, feature spec, requirements document, user stories, acceptance criteria).
- **FR-006**: The `write-spec` skill body MUST instruct the agent to perform the spec-drafting workflow: load context (constitution, prior specs, relevant repo conventions when available), draft the spec against the shared validation contract, limit `[NEEDS CLARIFICATION]` markers to a maximum of three, and start the spec in `Draft` status.
- **FR-007**: The `write-spec` skill body MUST stay within the recommended budget (≤ 500 lines / ~5000 tokens); longer material MUST be moved under `templates/skills/write-spec/references/`.
- **FR-008**: The `write-spec` skill MUST demonstrate **context engineering** as a first-class concern by bundling minimal context-gathering scripts under `templates/skills/write-spec/scripts/`. The scripts MUST produce structured context for constitution loading and prior-spec summary at minimum. The skill MUST NOT rely solely on the agent's freeform repository exploration.
- **FR-009**: The `write-spec` skill's bundled context-gathering scripts MUST provide equivalent PowerShell and Bash variants (§VI Platform Parity).
- **FR-010**: The `write-spec` skill MUST degrade gracefully when invoked outside a DevSpark-enabled repository: it MUST still produce a valid `spec.md` artifact, MUST NOT attempt DevSpark-specific operations (branch creation, multi-app scoping), and MUST record skipped context in the produced spec's Assumptions section.

#### Phase 2C — Tests

- **FR-011**: The repository MUST include automated tests under `tests/` that enforce the skill validation contract on every skill folder present in `templates/skills/`, gating PR merge.
- **FR-012**: The repository MUST include an adapter contract test that verifies (a) `templates/commands/specify.md` references the `write-spec` skill, (b) the command does not duplicate the drafting procedure inline, and (c) the existing `/devspark.specify` integration tests still pass against the refactored command.
- **FR-013**: The repository MUST expose a plural CLI command group for skills: `devspark skills list` to enumerate skills found under `templates/skills/`, and `devspark skills validate [path]` to validate all skills or one supplied skill path. Validation MUST return a non-zero exit code on any failure.

#### Phase 2D — Thin-Wrapper Command Refactor

- **FR-014**: `templates/commands/specify.md` MUST be refactored so that DevSpark-specific lifecycle work (route classification, branch creation, multi-app scoping, artifact placement, checklist generation, gate enforcement) remains in the command, and the spec-drafting reasoning is delegated to the `write-spec` skill via the adapter contract.
- **FR-015**: After the refactor, the existing `/devspark.specify` integration test suite MUST pass unchanged. User-observable behavior (artifacts produced, branch naming, frontmatter, checklist contents) MUST be equivalent in structure to the pre-refactor command.

#### Cross-Cutting

- **FR-016**: The other 27 `/devspark.*` commands MUST NOT be modified by this feature; the change is scoped to `specify` only (§I Backward Compatibility).
- **FR-017**: The repository MUST NOT install, modify, or remove any file under any `.documentation/` directory as a result of adopting skills (§III Ownership Boundary).
- **FR-018**: All new and modified markdown introduced by this feature MUST pass `npx markdownlint-cli2 "**/*.md"` with zero errors (§VIII).
- **FR-019**: Repository-level documentation (`README.md` and `CLAUDE.md`) MUST be updated with: (a) the positioning statement from Rationale Summary, (b) a description of the dual-surface model (commands ↔ skills) and the `command → invokes → skill` internal architecture, and (c) pointers to `templates/skills/README.md`, `SKILL-validation-contract.md`, `ADAPTER-contract.md`, and `templates/skills/references/devspark-skills-guide.md`.
- **FR-020**: The distribution surface for the skill MUST be in-repo only for this release. The `write-spec` skill MUST ship under `templates/skills/write-spec/`; publication to an external index (for example, agentskills.io Client Showcase or a community registry) is explicitly deferred.

### Key Entities

- **Skill**: A versioned folder under `templates/skills/<skill-name>/` that packages a single agent capability per the open Agent Skills specification. Portable; can run in any skills-compatible client without DevSpark.
- **SKILL.md**: The required entry point of a skill — YAML frontmatter (open-spec fields only) plus Markdown body of agent instructions.
- **Skill Version**: A quoted semantic-version string stored at `metadata.version` in `SKILL.md`. DevSpark validation reports the skill name and this version; top-level `version` is prohibited.
- **Command**: A `/devspark.*` slash-command prompt under `templates/commands/`. Owns DevSpark-specific lifecycle and governance concerns. After this feature, `specify` invokes a skill for the reasoning portion.
- **Adapter Contract**: The DevSpark-authored document defining the boundary between commands and skills (responsibilities, input/output mapping, discovery, backward-compatibility rules).
- **Skill Validation Contract**: The DevSpark-authored document defining the rules every `SKILL.md` and skill folder must satisfy, layered on top of upstream open-spec rules.
- **DevSpark Skills Guide**: The shared contributor reference at `templates/skills/references/devspark-skills-guide.md` that explains how this repository designs, organizes, validates, and reviews skills.
- **Context-Gathering Script**: Deterministic, dual-parity (PowerShell + Bash) code under a skill's `scripts/` directory that prepares structured repository context for the agent before reasoning. For `write-spec`, this includes constitution loading and prior-spec summary at minimum. The DevSpark-distinctive contribution above bare prompt engineering.
- **Skill Validation Result**: Structured pass/warn/fail output from the validation CLI and test suite, used by humans and CI to gate merges.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A spec-drafting task that previously required a DevSpark-native client can be completed end-to-end in any skills-compatible client by loading only the `templates/skills/write-spec/` folder — with **zero** DevSpark-specific configuration required in the host client.
- **SC-002**: 100% of skill folders under `templates/skills/` pass the skill validation contract in CI on the default branch; any contract violation blocks merge.
- **SC-003**: After the Phase 2D refactor, 100% of the existing `/devspark.specify` integration tests pass unchanged — confirming structural behavior parity for DevSpark users.
- **SC-004**: All markdown introduced or modified by the feature produces zero markdownlint errors on the feature PR's required CI lint job.
- **SC-005**: A new contributor following only `templates/skills/README.md`, the adapter contract, and the `write-spec` example can produce a second skill folder + thin-wrapper command that passes both the skill validation and adapter contract tests on their first PR attempt.
- **SC-006**: Existing DevSpark users observe zero regressions in any `/devspark.*` slash-command behavior (verified by the existing test suite passing unchanged) — the new surface is strictly additive and the `specify` refactor is observably transparent.
- **SC-007**: The `write-spec` skill, when invoked, produces a structured context payload (constitution summary + prior-spec summary at minimum) that is verifiable in its execution trace — demonstrating context engineering, not just prompt delivery.

## Assumptions

- The open Agent Skills specification at <https://agentskills.io/specification> remains stable in the fields used by this feature.
- Skills-compatible clients of interest respect progressive disclosure, making the body-length budget meaningful.
- Behavior parity for `/devspark.specify` after the Phase 2D refactor can be enforced by the existing integration test suite without writing new behavioral tests beyond the adapter contract test.
- The pilot skill bundles minimal context-gathering scripts for constitution loading and prior-spec summary under `scripts/`, accepting the §VI Platform Parity obligation for those scripts as a deliberate demonstration of context engineering.
- DevSpark skill versioning uses `metadata.version` because the upstream Agent Skills specification reserves `metadata` for additional key-value properties while keeping the top-level frontmatter dialect stable.
- Drift between the skill body and the thin-wrapper command can be detected mechanically by the adapter contract test; full code-generation between the two surfaces is not required.

## Out of Scope

- Conversion of any command other than `/devspark.specify` to a skill in this feature (`plan`, `tasks`, `implement`, etc. are deferred).
- Expansion of `write-spec` to orchestrate plan/tasks generation (deferred; see Tradeoffs Option D).
- The DevSpark AI Taxonomy document (Skill / Agent / Command / Workflow / Shim / Context Engineering / Lifecycle / Orchestrator). Deferred to a follow-up feature; the positioning statement and adapter contract in this feature provide enough conceptual scaffolding for the pilot.
- Publishing skills to any external registry beyond shipping them inside the DevSpark repository. External publication is deferred to a follow-up feature after the in-repo pilot proves the model.
- Generating skills automatically from existing `templates/commands/*.md` prompts.
- Changes to any of the other 27 `/devspark.*` slash commands.
- Changes to user `.documentation/` artifacts in installed repositories (forbidden by §III).
- Adoption of the experimental `allowed-tools` open-spec field (deferred until upstream stabilization).

## Clarifications

### Session 2026-05-19

- Q: Should the skill body be a thin wrapper that delegates to `/devspark.specify`, or a fully self-contained portable capability? → A: **Fully self-contained, portable.** Skills are portable capability packages; commands invoke them. Resolved via the Phase 2A–2D architecture.
- Q: Should this feature deliver only `write-spec`, or also `plan` and `tasks` skills? → A: **Only `write-spec`, spec-drafting only.** Smallest credible orchestration first. Plan/tasks deferred.
- Q: Should the `command → invokes → skill` pivot be implemented in this feature or deferred? → A: **Implemented in this feature, sequenced as sub-phases 2A → 2B → 2C → 2D** (adapter contract → standalone skill → tests → thin-wrapper command refactor).
- Q: Should the DevSpark AI Taxonomy doc be in scope? → A: **Deferred** to a follow-up feature. Positioning statement (in Rationale Summary, FR-019) is sufficient conceptual scaffolding for this pilot.
- Q: In addition to shipping inside the DevSpark repo, should this feature publish the skill to an external index? → A: **In-repo distribution only for this release.** External publication is deferred until after the pilot proves the model.
- Q: What CLI shape should skill list and validation commands use? → A: **Use a plural `skills` command group:** `devspark skills list` and `devspark skills validate [path]`.
- Q: Should the `write-spec` skill bundle context-gathering scripts or only document host-provided context? → A: **Bundle minimal dual-script context loaders** for constitution loading and prior-spec summary.
- Q: Where should DevSpark-managed skills declare their version? → A: **Require `metadata.version`** as a quoted semantic-version string; top-level `version` is prohibited.
- Q: Should `templates/skills/references/devspark-skills-guide.md` be a required deliverable or only a helper reference? → A: **Required Phase 2A deliverable** for shared DevSpark skills guidance.
