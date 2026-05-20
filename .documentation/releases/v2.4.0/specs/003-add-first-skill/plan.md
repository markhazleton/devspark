# Implementation Plan: Add First Agent Skill (write-spec)

**Branch**: `003-add-first-skill` | **Date**: 2026-05-19 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `.documentation/specs/003-add-first-skill/spec.md`

## Rationale Summary

### Core Problem

DevSpark's 28 `/devspark.*` slash-command prompts use a DevSpark-specific
frontmatter contract (`handoffs`, `scripts`, `classification`) that is not
interoperable with the open Agent Skills standard. DevSpark capabilities cannot
be discovered, loaded, or executed by skills-compatible clients without bespoke
DevSpark tooling.

### Decision Summary

Ship one portable, standalone skill — `write-spec` — that complies with the
open Agent Skills specification, and refactor `/devspark.specify` to delegate
spec-drafting to that skill via a well-defined adapter contract. Existing
user-facing slash-command UX remains stable; the architectural change is
internal.

### Key Drivers

- **Interoperability**: Make at least one DevSpark capability portable to any
  skills-compatible client without DevSpark installation.
- **Standards awareness**: Demonstrate first-class support for the open Agent
  Skills spec (agentskills.io).
- **Separation of concerns**: Establish the
  `command → adapter → skill → context scripts → agent reasoning → artifact`
  boundary that DevSpark's governance model requires.

### Source Inputs

- Open Agent Skills spec: <https://agentskills.io/specification>
- Reference repo: <https://github.com/agentskills/agentskills>
- Existing command: `templates/commands/specify.md`
- Shared contract: `templates/spec-validation-contract.md`
- Constitution v1.3.0: `.documentation/memory/constitution.md`
- Clarifications session 2026-05-19 (recorded in spec.md)

### Tradeoffs Considered

- Option A — Replace slash-command surface with Agent Skills directly: rejected.
  Breaks §I Backward Compatibility; reframes DevSpark as a skills framework.
- Option B — Ship skill standalone with no command integration: rejected. Fails
  to demonstrate the `command → invokes → skill` architectural value.
- Option C — Auto-generate skills from all 28 commands: rejected. Premature
  dual-maintenance burden.
- Option D — Make `write-spec` orchestrate full spec + plan + tasks: rejected
  for this feature. Smallest credible orchestration first.
- **Selected** — Single portable `write-spec` skill + adapter contract + thin
  command refactor: validates the dual-surface model end-to-end on one
  high-value capability before scaling.

### Architectural Impact

- New top-level directory `templates/skills/` parallel to `templates/commands/`.
- New contract files: `templates/skills/ADAPTER-contract.md`,
  `templates/skills/SKILL-validation-contract.md`.
- New skill: `templates/skills/write-spec/` (SKILL.md + scripts/ + references/).
- New tests: `tests/test_skill_contract.py`, `tests/test_adapter_contract.py`.
- New CLI command group: `devspark skills list` and `devspark skills validate`.
- Thin refactor: `templates/commands/specify.md` delegates drafting to the skill.
- No changes to the other 27 `/devspark.*` commands.
- No changes to any `.documentation/` user artifacts in installed repos.

### Reviewer Guidance

1. **Adapter contract clarity (2A)**: Does it cleanly separate skill
   responsibility (portable reasoning) from command responsibility (DevSpark
   lifecycle)?
2. **Skill portability (2B)**: Does `SKILL.md` frontmatter contain no
   DevSpark-only keys? Is the body within budget?
3. **Context engineering (2B)**: Does the skill demonstrate structured context
   gathering on top of bare prompt delivery?
4. **Refactor parity (2D)**: Does the existing test suite pass unchanged after
   the command becomes a thin wrapper?
5. **Scope discipline**: Exactly one skill (`write-spec`, spec-drafting only).

## Summary

Introduce the `templates/skills/` surface and one portable pilot skill
(`write-spec`) that extracts the spec-drafting logic currently embedded in
`templates/commands/specify.md`. Refactor `specify.md` to delegate drafting to
the skill via a new adapter contract. Add CLI commands and tests that validate
skill and adapter contract compliance on every PR.

## Technical Context

**Language/Version**: Python 3.11+ (CLI code), Markdown (skill/contract files),
PowerShell 5.1+ and Bash (context-gathering scripts)

**Primary Dependencies**: typer, rich, click (CLI); PyYAML>=6.0 (skill
frontmatter parsing in tests and CLI — confirmed direct dependency in
pyproject.toml, critic-006 resolved); pytest (test suite)

**Storage**: File system only. Skill artifacts land in `templates/skills/`;
spec outputs land in `.documentation/specs/`.

**Testing**: pytest (existing suite extended). Two new test modules:
`test_skill_contract.py` and `test_adapter_contract.py`.

**Target Platform**: Portable Markdown (skill) + cross-platform scripts
(PowerShell + Bash); CLI runs on Linux/macOS/Windows per existing constraints.

**Project Type**: CLI tool + Markdown template framework

**Performance Goals**: Not applicable for this feature; validation CLI should
complete in < 5 s per skill on typical developer hardware.

**Constraints**: §I Backward Compatibility (27 other commands unchanged),
§III Ownership Boundary (no `.documentation/` writes by framework),
§VI Platform Parity (dual PowerShell + Bash scripts), §VIII Markdown Quality
(zero markdownlint errors on all new and modified Markdown).

**Scale/Scope**: 1 new skill, 2 new contract files, 1 new skills guide
reference, 2 new test files, 1 new CLI subcommand group, 1 command refactor.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
| --------- | ------ | ----- |
| §I Backward Compatibility | PASS | Only `specify.md` is refactored; 27 other commands unchanged. User-observable behavior preserved per SC-003. |
| §II Explicit Over Implied | PASS | Adapter contract documents all responsibility boundaries explicitly; no silent scope inference. |
| §III Ownership Boundary | PASS | No framework writes to `.documentation/` user artifacts. Skill ships under `templates/skills/`. |
| §IV Governance Authority | PASS | Constitution authority remains repo-wide; new skill surface inherits all mandatory rules. |
| §V Simplicity | PASS | Single skill, minimal adapter, no config layer. Complexity justified by interoperability goal with documented rejected simpler options. |
| §VI Platform Parity | PASS | Context-gathering scripts supplied in both PowerShell and Bash per FR-009. |
| §VII PR Review Artifact Commit Discipline | N/A | No PR review file involved in this feature's implementation commits. |
| §VIII Markdown Quality | PASS | All new and modified Markdown gated by FR-018 (zero markdownlint errors). `ignores` block update required if any runtime output path is introduced. |

**Gate result: PASS — proceed to Phase 0.**

## Project Structure

### Documentation (this feature)

```text
.documentation/specs/003-add-first-skill/
├── plan.md              ← this file
├── research.md          ← Phase 0 output
├── data-model.md        ← Phase 1 output
├── contracts/           ← Phase 1 interface contracts
├── checklists/
│   └── requirements.md  ← created by /devspark.specify
├── gates/               ← persisted gate artifacts from analyze/critic/checklist
└── tasks.md             ← Phase 2 output (/devspark.tasks — not created here)
```

### Source Code (repository root)

```text
templates/skills/
├── README.md                          ← 2A: new
├── ADAPTER-contract.md                ← 2A: new
├── SKILL-validation-contract.md       ← 2A: new
├── references/
│   └── devspark-skills-guide.md      ← 2A: complete existing stub
└── write-spec/
    ├── SKILL.md                       ← 2B: new
    ├── references/                    ← 2B: new files
    └── scripts/
        ├── gather-context.ps1         ← 2B: new, PowerShell
        └── gather-context.sh          ← 2B: new, Bash

templates/commands/
└── specify.md                         ← 2D: refactor (thin wrapper)

src/devspark_cli/
└── commands/
    └── skills.py                      ← 2C: new CLI subcommand group

tests/
├── test_skill_contract.py             ← 2C: new
└── test_adapter_contract.py           ← 2C: new

README.md                              ← FR-019: update (dual-surface model)
CLAUDE.md                              ← FR-019: update (positioning statement)
```

**Structure Decision**: Single project layout. `templates/skills/` is new and
parallel to `templates/commands/`. CLI additions go in
`src/devspark_cli/commands/skills.py`, following the existing pattern in
`src/devspark_cli/commands/lifecycle.py`. No new top-level project directories
are needed.

## Complexity Tracking

> No unjustified violations. All §V Simplicity concerns are addressed by the
> single-skill, single-command-refactor scope with explicit tradeoff
> documentation in spec.md.

---

## Phase 0: Research Findings

*All NEEDS CLARIFICATION markers from the spec have been resolved (Clarifications
session 2026-05-19). See `research.md` for full citations.*

### Open Agent Skills frontmatter dialect

- Decision: use `name`, `description`, and `metadata.version` (quoted semver)
- DevSpark prohibits in `SKILL.md`: `handoffs`, `scripts` (command sense),
  `classification`, `required_gates`, `recommended_next_step`, bare `version`
- Rationale: upstream spec reserves `metadata` for additional properties while
  keeping the top-level dialect portable; `metadata.version` is the stable hook

### Context-gathering script scope for `write-spec`

- Decision: constitution loading + prior-spec summary, JSON output format
- Failure mode: emit partial JSON + `skipped_context` array; never block skill
- Rejected: freeform exploration (non-deterministic, not demonstrable as context
  engineering)

### CLI command group shape

- Decision: `devspark skills list` / `devspark skills validate [path]`
- Consistent with existing `devspark harness` and `devspark adapter` groups
- Exit non-zero on any failure per FR-013

### Adapter contract responsibility split

- Command: route classification, branch creation, multi-app scoping, artifact
  path placement, checklist generation, gate enforcement
- Skill: portable reasoning, context-gathering script execution, spec draft
- Adapter: input mapping, output mapping, discovery path rules, parity rules

### Phase sequencing (mandatory)

- 2A before 2B: adapter contract stable before skill is built
- 2B before 2C: skill exists before tests assert on it
- 2C before 2D: test gate exists before command is refactored
- 2D last: parity enforced by existing test suite throughout

---

## Phase 1: Design & Contracts

### Data Model

See [data-model.md](data-model.md) for full entity definitions.

#### Skill Package (directory at `templates/skills/<skill-name>/`)

| Field | Type | Constraint |
| ----- | ---- | ---------- |
| `name` | string | Max 64 chars; `[a-z0-9-]`; no leading/trailing/consecutive hyphens; matches parent dir |
| `description` | string | 1–1024 chars; non-empty; discovery-rich |
| `metadata.version` | quoted string | SemVer `"MAJOR.MINOR.PATCH"`; required for DevSpark skills |
| `license` | string | Optional; upstream field |
| `compatibility` | string | Optional; max 500 chars when present |
| Body | Markdown | Max 500 lines / ~5000 tokens |

Prohibited top-level keys in `SKILL.md`: `handoffs`, `scripts` (command sense),
`classification`, `required_gates`, `recommended_next_step`, `version` (bare).

#### Validation Result

| Field | Type | Values |
| ----- | ---- | ------ |
| `skill_name` | string | from `name` frontmatter |
| `skill_version` | string | from `metadata.version` |
| `status` | enum | `pass`, `warn`, `fail` |
| `findings` | list | each: `{rule, severity, message}` |

Severity: `error` (validation fails), `warning` (advisory), `info`.

#### Adapter Input Map

| Command input | Skill context variable |
| ------------- | ---------------------- |
| User feature description | `$FEATURE_DESCRIPTION` |
| Resolved constitution path | `$CONSTITUTION_PATH` |
| Prior-spec summary (from script) | `$PRIOR_SPEC_SUMMARY` |

Multi-app scope (`$APP_SCOPE`) is resolved by the command and is NOT passed
into the skill body — multi-app scoping is a command-only responsibility.

#### Adapter Output Map

| Skill output | Command action |
| ------------ | -------------- |
| Draft `spec.md` body | Written to `SPEC_FILE` resolved by command |
| `[NEEDS CLARIFICATION]` markers | Preserved; command may invoke `/devspark.clarify` |
| `Assumptions` section | Preserved verbatim in placed spec |

### Interface Contracts

See [contracts/](contracts/) for full contract files.

**contracts/skill-discovery.md** — The `write-spec` skill is discoverable via
`templates/skills/write-spec/`. `devspark skills list` enumerates all sibling
directories of `templates/skills/` that contain a `SKILL.md`. Clients load only
`name` and `description` for indexing; full body is loaded on activation.

**contracts/cli-commands.md** — Full CLI contract for `devspark skills list` and
`devspark skills validate [path]`. Three-tier exit-code contract (critic-002):
`pass` exits 0 with a one-line summary; `warn` exits 0 with warning count on
stderr (body-budget pressure does not block CI); `fail` exits 1 with a
`[RULE] [OFFENDING-VALUE] message` diagnostic on stderr. `skills list` output
format is not yet stable for scripting (no `--json` flag in this release — see
critic-007 decision).

**contracts/adapter-contract.md** — Summary: command resolves skill path before
invoking; command passes context as named variables per adapter contract; command
places draft in DevSpark-governed artifact path; skill must not perform branch
creation, multi-app resolution, or gate enforcement.

---

## Ordered Sub-Phases for /devspark.tasks

Sub-phases must land in order (2A → 2B → 2C → 2D). Each sub-phase has a clear
completion gate before the next begins.

### Sub-phase 2A — Shared Skills Foundation

**Completion gate**: `ADAPTER-contract.md` and `SKILL-validation-contract.md`
both exist, `devspark-skills-guide.md` is complete, FR-002/FR-002a/FR-003
satisfied.

Files to deliver:

1. `templates/skills/README.md`
2. `templates/skills/SKILL-validation-contract.md`
3. `templates/skills/ADAPTER-contract.md`
4. `templates/skills/references/devspark-skills-guide.md` (complete existing)
5. `README.md` update (FR-019 positioning statement + pointers)
6. `CLAUDE.md` update (FR-019 dual-surface model)

### Sub-phase 2B — Standalone `write-spec` Skill

**Completion gate**: `templates/skills/write-spec/SKILL.md` exists and passes
manual validation against `SKILL-validation-contract.md`; both context scripts
run without error on current repo; FR-004 through FR-010 satisfied.

Files to deliver:

1. `templates/skills/write-spec/SKILL.md`
2. `templates/skills/write-spec/references/` (at minimum: spec-template
   reference, clarification format, success criteria guidelines)
3. `templates/skills/write-spec/scripts/gather-context.ps1`
4. `templates/skills/write-spec/scripts/gather-context.sh`

### Sub-phase 2C — Tests and CLI

**Completion gate**: `pytest tests/test_skill_contract.py tests/test_adapter_contract.py`
passes; `devspark skills list` and `devspark skills validate` subcommands are
wired into the CLI; deliberate-violation fixture confirms non-zero exit;
FR-011 through FR-013 satisfied.

Files to deliver:

1. `tests/test_skill_contract.py`
2. `tests/test_adapter_contract.py`
3. `src/devspark_cli/commands/skills.py`
4. Wiring: `_app.py` adds `skills_app` subcommand

### Sub-phase 2D — Thin-Wrapper Command Refactor

**Completion gate**: All existing tests under `tests/test_create_spec_workflow_integration.py`
and related pass unchanged; `test_adapter_contract.py` confirms delegation;
no user-observable behavior difference; FR-014 and FR-015 satisfied.

Files to deliver:

1. `templates/commands/specify.md` (refactored)
