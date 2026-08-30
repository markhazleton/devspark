---
description: Execute the implementation planning workflow using the plan template to generate design artifacts.
handoffs:
  - label: Create Tasks
    agent: devspark.tasks
    prompt: Break the plan into tasks
    send: true
  - label: Create Checklist
    agent: devspark.checklist
    prompt: Create a checklist for the following domain...
scripts:
  sh: .devspark/scripts/bash/setup-plan.sh --json
  ps: .devspark/scripts/powershell/setup-plan.ps1 -Json
agent_scripts:
  sh: .devspark/scripts/bash/update-agent-context.sh __AGENT__
  ps: .devspark/scripts/powershell/update-agent-context.ps1 -AgentType __AGENT__
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## DevSpark v4 Override

This command enriches the ephemeral work package and resolves current-truth
context before implementation. When any later section conflicts with this
section, the v4 section wins.

- Resolve relevant `.knowledge` entities and governance decisions 2-3 hops, or
  until traversal stops finding relevant edges.
- Record resolved context in `context_resolved` inside the work package.
- Use `.knowledge/ontology/relations.generated.md` and
  `.knowledge/ontology/governance.generated.md` as the bounded graph index after
  confirming generated ontology files are current.
- Do not copy governance rationale into entity files; reference governed
  entities and decisions instead.
- Load governance from `.knowledge/governance/constitution.md`, with legacy
  fallback only when the v4 file is absent.

## Workflow Position

**Step 3 of 4** in the authoring chain (`specify → clarify → plan → tasks`).

- **Owns**: technical context (stack, libraries, project structure), Constitution Check gate, research consolidation, data model, interface contracts, per-agent context update.
- **Does NOT own**: re-litigating WHAT/WHY (spec is authoritative); resolving open functional ambiguities (→ `/devspark.clarify`); the executable task list (→ `/devspark.tasks`); adversarial review (→ `/devspark.critic`, `/devspark.analyze`).
- **Pre-flight**: if the loaded spec still contains `[NEEDS CLARIFICATION: …]` markers, halt and route to `/devspark.clarify`. Do not silently default open questions into planning decisions.

## Definition of Done

Done when: research.md has zero `NEEDS CLARIFICATION` markers, data-model.md/contracts//quickstart.md exist where applicable to the project type, the agent-context script has run, and the Constitution Check is re-evaluated post-design with no unresolved violations. This command stops after Phase 1 (step 4) — it does not generate tasks or write code. Chat output: report only the branch, IMPL_PLAN path, and generated artifact list — full design detail lives in the files.

## Constitution Authority

`/.knowledge/governance/constitution.md` is **non-negotiable** for planning. Violations may not be carried forward as `NEEDS CLARIFICATION`; they must be resolved before exiting the Constitution Check gate. Justified deviations require an explicit `## Constitution Waivers` block in `plan.md` citing the principle, deviation, reason, and compensating control.

## Outline

**Multi-app support**: If this repository uses multi-app mode (`.knowledge/entities/application-registry/registry.json` exists with `mode: "multi-app"`), check for `--app <id>` in the user input to scope this workflow to a specific application. When app context is provided, resolve artifacts from `{app.path}/.knowledge/` instead of the repository root `.knowledge/`. Print the resolved scope (app name, doc root) at the start of output.

> **Script Resolution**: Before running `{SCRIPT}` or `{AGENT_SCRIPT}`, apply the 2-tier override check — if `.knowledge/overrides/scripts/powershell/<filename>` (PowerShell) or `.knowledge/overrides/scripts/bash/<filename>` (Bash) exists on disk, run that file instead, preserving all arguments. Team overrides in `.knowledge/overrides/scripts/` always take priority over `.devspark/scripts/`.

1. **Setup**: Run `{SCRIPT}` from repo root and parse JSON for FEATURE_SPEC, IMPL_PLAN, SPECS_DIR, BRANCH. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **Load context**: Read FEATURE_SPEC and `/.knowledge/governance/constitution.md`. Load IMPL_PLAN template (already copied).
   - Read the YAML frontmatter in FEATURE_SPEC before planning.
   - Treat frontmatter as authoritative for `classification`, `risk_level`, `recommended_next_step`, and `required_gates`.
   - If the body text appears to conflict with the frontmatter, flag the inconsistency to the user instead of overriding the metadata.
   - Run `python .devspark/scripts/python/build_knowledge_index.py --check` if
     available; otherwise run `python scripts/python/build_knowledge_index.py
     --check` in source repos. If it reports stale generated files, refresh them
     with `--write` before resolving `context_resolved`.

3. **Execute plan workflow**: Follow the structure in IMPL_PLAN template to:
   - Fill Technical Context (mark unknowns as "NEEDS CLARIFICATION")
   - Fill Constitution Check section from constitution
   - Evaluate gates (ERROR if violations unjustified)
   - Phase 0: Generate research.md (resolve all NEEDS CLARIFICATION)
   - Phase 1: Generate data-model.md, contracts/, quickstart.md
   - Phase 1: Update agent context by running the agent script
   - Re-evaluate Constitution Check post-design

4. **Stop and report**: Command ends after Phase 2 planning. Report branch, IMPL_PLAN path, and generated artifacts.

## Phases

### Phase 0: Outline & Research

1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:

   ```text
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

### Phase 1: Design & Contracts

**Prerequisites:** `research.md` complete

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Define interface contracts** (if project has external interfaces) → `/contracts/`:
   - Identify what interfaces the project exposes to users or other systems
   - Document the contract format appropriate for the project type
   - Examples: public APIs for libraries, command schemas for CLI tools, endpoints for web services, grammars for parsers, UI contracts for applications
   - Skip if project is purely internal (build scripts, one-off tools, etc.)

3. **Agent context update**:
   - Run `{AGENT_SCRIPT}`
   - These scripts detect which AI agent is in use
   - Update the appropriate agent-specific context file
   - Add only new technology from current plan
   - Preserve manual additions between markers

**Output**: data-model.md, /contracts/\*, quickstart.md, agent-specific file

## Constraints

- Use absolute paths
- ERROR on gate failures or unresolved clarifications
