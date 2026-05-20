---
gate: critic
status: pass
blocking: false
severity: info
summary: "0 showstoppers, 0 critical. All 8 findings (4 high, 4 medium) resolved in spec/plan/tasks. PROCEED."
---

## Technical Risk Assessment

**Analysis Date:** 2026-05-19
**Scope:** FULL (spec.md + plan.md + tasks.md)
**Detected Archetype:** `cli` (primary) + `library` (secondary — `skills.py` exposes a Python API surface)
**Detected Stack:** Python 3.11+ · Typer + Rich · PyYAML · pytest · PowerShell + Bash scripts
**Context Mode:** brownfield (new subcommand group + command refactor in established CLI)
**Risk Profile:** `internal` (defaulted — no `risk_profile` in spec.md frontmatter)
**Risk Posture:** YELLOW

Checklists loaded from `templates/risk-checklists/cli.md` and `templates/risk-checklists/library.md`.
No `.devspark/risk-checklists/` overrides found.

---

### Executive Summary

No showstoppers or critical findings. The feature's architectural separation
(command/adapter/skill) is sound, and the sub-phase sequencing (2A→2B→2C→2D)
reduces brownfield regression risk appropriately. The primary risks are: (1) the
`skills validate` CLI subcommand has underspecified exit-code semantics for the
`warn` tier (body-budget advisory), (2) PyYAML's YAML 1.1 parser can misread
frontmatter boolean-like values in ways that silently pass validation, (3) the
adapter contract's delegation mechanism is prose-only in a Markdown prompt —
there is no machine-enforced boundary between command and skill at runtime, so
drift is detectable only by the test suite, and (4) the `specify.md` refactor
touches a heavily-exercised brownfield command and has no rollback path beyond
git revert if behavior drift is discovered post-merge.

---

### Findings

```yaml
findings:
  - finding_id: critic-001
    category: missing-risk-profile
    archetype_applicable: true
    location: spec.md#frontmatter
    description: >
      spec.md frontmatter has no `risk_profile` field. Defaulted to `internal`
      (no severity shift applied). If this tool ships to end-users or is used in
      CI pipelines affecting production repositories, the profile should be
      `customer-facing`, which would shift HIGH findings to CRITICAL.
    base_severity: high
    effective_severity: high
    recommended_action: >
      Add `risk_profile: internal` (or appropriate value) to spec.md frontmatter
      to make the default explicit and suppress this finding on re-run.
    execution_mode: auto
    status: resolved
    outcome: "Added risk_profile: internal and change_type: brownfield to spec.md frontmatter."

  - finding_id: critic-002
    category: cli_ergonomics
    archetype_applicable: true
    location: tasks.md#T020; plan.md#contracts/cli-commands.md
    description: >
      The `devspark skills validate` exit-code contract specifies exit 0 (pass)
      and exit 1 (failure), but the SKILL-validation-contract.md introduces a
      three-tier result: pass / warn / fail. Body-budget pressure produces a
      `warn`, not a `fail`. The tasks and plan do not define whether `warn`
      exits 0 or 1. If it exits 0, CI will silently pass oversized skills; if it
      exits 1, implementers will have to decide during coding with no spec
      guidance. The CLI checklist requires documented exit codes.
    base_severity: high
    effective_severity: high
    recommended_action: >
      Add to the adapter contract or SKILL-validation-contract.md: "warn exits 0
      with a non-zero warning count on stdout/stderr; fail exits 1." Update
      contracts/cli-commands.md in tasks.md (Phase 1 of 2A deliverables, T004)
      to include the three-tier exit-code table. This is a contract authoring
      decision, not a code change.
    execution_mode: manual
    status: resolved
    outcome: "Three-tier exit-code table (pass=0, warn=0+stderr-count, fail=1) added to
      T004 task description and plan.md contracts/cli-commands.md section."

  - finding_id: critic-003
    category: testing_strategy
    archetype_applicable: true
    location: tasks.md#T018; spec.md#FR-011
    description: >
      `test_skill_contract.py` (T018) plans to parse SKILL.md frontmatter with
      PyYAML. PyYAML uses YAML 1.1 semantics by default: bare `yes`, `no`,
      `on`, `off`, `true`, `false` in frontmatter are parsed as Python booleans,
      not strings. A future skill description containing "on" as a standalone
      word, or a metadata value like `version: 1.0` (unquoted), could be
      silently mistyped. T018 specifies `metadata.version` must be a "quoted
      semver string" but the test assertion is likely a string equality check —
      PyYAML will produce a float for `version: 1.0` (unquoted) and the test
      would correctly catch that, but a `version: "1.0"` (quoted) parsed as
      string `"1.0"` may not enforce the full `MAJOR.MINOR.PATCH` semver pattern.
      No test task explicitly asserts the semver regex.
    base_severity: high
    effective_severity: high
    recommended_action: >
      In T018, explicitly assert: (a) `metadata.version` is a string (not int
      or float — rejects unquoted `1.0`); (b) `metadata.version` matches regex
      `^\d+\.\d+\.\d+$` (rejects `"1.0"` missing patch). Use `ruamel.yaml`
      (YAML 1.2) or add a PyYAML `Loader=yaml.SafeLoader` with explicit string
      enforcement to avoid YAML 1.1 boolean surprises on other frontmatter values.
    execution_mode: manual
    status: resolved
    outcome: "T018 updated to use yaml.safe_load(), assert metadata.version is str type,
      assert regex ^\\d+\\.\\d+\\.\\d+$, and include deliberate-violation fixtures for
      unquoted float and partial semver. Portability body-scan (critic-008) also added."

  - finding_id: critic-004
    category: api_compatibility
    archetype_applicable: true
    location: plan.md#Adapter-Input-Map; spec.md#FR-014
    description: >
      The adapter contract maps `$FEATURE_DESCRIPTION`, `$CONSTITUTION_PATH`,
      and `$PRIOR_SPEC_SUMMARY` as named inputs from command to skill. In a
      Markdown prompt system, "passing named inputs" is prose convention, not
      enforced by a runtime. The adapter contract test (T019/T026) checks that
      `specify.md` "references the write-spec skill" and "does not duplicate the
      drafting procedure inline" — both are text-grep assertions. If the skill
      body is updated to rename or remove an expected input variable, the grep
      test will still pass. There is no machine-checked interface between the
      command and the skill at the variable level.
    base_severity: high
    effective_severity: high
    recommended_action: >
      Add at least one test assertion that the named input variables
      (`$FEATURE_DESCRIPTION`, `$CONSTITUTION_PATH`, `$PRIOR_SPEC_SUMMARY`)
      are referenced in `specify.md`'s delegation block AND declared in the
      ADAPTER-contract.md. This is a grep-based cross-file consistency check
      that makes the contract machine-verifiable without a runtime. Document in
      ADAPTER-contract.md that variable names are part of the versioned contract
      surface — changing them requires a version bump in `metadata.version`.
    execution_mode: manual
    status: resolved
    outcome: "T019 updated to include cross-file grep assertions for $FEATURE_DESCRIPTION,
      $CONSTITUTION_PATH, $PRIOR_SPEC_SUMMARY in both specify.md and ADAPTER-contract.md."

  - finding_id: critic-005
    category: error_handling_resilience
    archetype_applicable: true
    location: spec.md#FR-010; tasks.md#T013; tasks.md#T014
    description: >
      The context-gathering scripts must "degrade gracefully" and "never block
      skill execution." The tasks specify JSON output with a `skipped_context`
      array, but do not specify what the skill should do when the script itself
      fails to produce valid JSON (e.g., script exits non-zero, or stdout is
      empty, or malformed JSON). If the skill attempts to parse an empty or
      broken JSON payload without guarding, the skill activation fails rather
      than degrading. This is a gap between the graceful-degradation requirement
      and the skill body's error handling.
    base_severity: medium
    effective_severity: medium
    recommended_action: >
      Add to T011 (SKILL.md authoring) and T013/T014 (script authoring):
      the skill MUST treat any non-JSON, empty, or error output from the
      context scripts as equivalent to `{"constitution_summary": null,
      "prior_specs": [], "skipped_context": ["script-error"]}`. Document this
      fallback in the skill body's context-loading section and in the script's
      error-output contract.
    execution_mode: manual
    status: resolved
    outcome: "T011 updated with explicit fallback JSON contract for broken/empty/non-JSON
      script output. T013 and T014 updated to always exit 0 and always emit valid JSON
      with skipped_context array for any unavailable context."

  - finding_id: critic-006
    category: dependency_supply_chain
    archetype_applicable: true
    location: plan.md#Technical-Context; tasks.md (no task)
    description: >
      PyYAML is used by the new `test_skill_contract.py` and
      `src/devspark_cli/commands/skills.py` for frontmatter parsing. No task
      verifies that PyYAML is already in the project's pinned dependency set
      (`pyproject.toml` / lockfile). If it is only a transitive dependency,
      adding an explicit import without a declared direct dependency risks
      breakage on future lockfile regeneration. The library checklist requires
      direct dependencies to be declared correctly.
    base_severity: medium
    effective_severity: medium
    recommended_action: >
      Add a setup task (or amend T001) to verify PyYAML is declared as a direct
      dependency in `pyproject.toml`. If not, add it with a pinned version range
      consistent with the existing lockfile. Consider `ruamel.yaml` as an
      alternative (YAML 1.2, avoids critic-003 boolean surprises).
    execution_mode: selective
    status: resolved
    outcome: "PyYAML>=6.0 confirmed as direct dependency in pyproject.toml. T001 updated
      to include verification step. plan.md Technical Context updated to note confirmed
      status."

  - finding_id: critic-007
    category: cli_ergonomics
    archetype_applicable: true
    location: tasks.md#T020; tasks.md#T021
    description: >
      `devspark skills list` is spec'd to print a table (name, version, path,
      status). The existing CLI uses Rich for output. No task specifies whether
      `skills list` supports `--json` output for scripting consumption
      (e.g., CI workflows that want to enumerate skills programmatically). The
      CLI checklist requires a structured output mode for scripting. Omitting it
      now means adding it later as a breaking change (output format change).
    base_severity: medium
    effective_severity: medium
    recommended_action: >
      Decide and document in T020 whether `skills list` will support `--json`
      flag in this feature. If deferred, add an explicit note to the adapter
      contract that the output format is not yet stable so consumers know not
      to parse it. A one-line `--json` flag costs minimal effort now vs.
      a semver-breaking change later.
    execution_mode: manual
    status: resolved
    outcome: "T020 updated: no --json flag in this release (explicitly deferred with
      comment that output format is not yet stable); three-tier exit codes added;
      SafeLoader specified. plan.md contracts section notes output format instability."

  - finding_id: critic-008
    category: testing_strategy
    archetype_applicable: true
    location: tasks.md#T032; spec.md#SC-001
    description: >
      T032 (manual portability check) is the only verification for SC-001 —
      that the skill works in a non-DevSpark client. This is a manual task in
      the Polish phase, performed after all implementation is complete. If the
      skill body inadvertently references a DevSpark-specific path, variable, or
      assumption that only works inside a DevSpark-enabled repo, the failure is
      discovered at the last possible moment. There is no automated check that
      the SKILL.md body contains no DevSpark-specific instructions.
    base_severity: medium
    effective_severity: medium
    recommended_action: >
      Add a lightweight automated test to `test_skill_contract.py` (T018) that
      scans the SKILL.md body for known DevSpark-specific strings (`.devspark/`,
      `{SCRIPT}`, `FEATURE_DIR`, `{AGENT_SCRIPT}`, `handoffs:`) and fails if
      any are found. This catches the most common portability regressions
      mechanically without requiring a live non-DevSpark client.
    execution_mode: selective
    status: resolved
    outcome: "T018 updated to include portability body-scan: asserts SKILL.md body contains
      none of .devspark/, {SCRIPT}, FEATURE_DIR, {AGENT_SCRIPT}, handoffs: — included
      in deliberate-violation fixture set."
```

---

### High

| ID | Category | Location | Issue | Impact | Suggestion |
| --- | --- | --- | --- | --- | --- |
| critic-001 | missing-risk-profile | spec.md#frontmatter | No `risk_profile` field; defaulted to `internal` | Future severity re-runs may produce wrong thresholds if profile changes | Add `risk_profile: internal` to spec.md frontmatter |
| critic-002 | cli_ergonomics | tasks.md#T020, contracts/cli-commands.md | `warn` tier exit code undefined for `skills validate` | CI silently passes oversized skills (exit 0) or breaks unexpectedly (exit 1) with no spec guidance | Define exit-code table (pass=0, warn=0+warning-count, fail=1) in T004/SKILL-validation-contract.md |
| critic-003 | testing_strategy | tasks.md#T018 | PyYAML YAML 1.1 boolean surprises; semver pattern not regex-enforced | `version: 1.0` (unquoted float) or partial semver silently passes validation | Assert `metadata.version` is a string matching `^\d+\.\d+\.\d+$`; consider `ruamel.yaml` |
| critic-004 | api_compatibility | plan.md#Adapter-Input-Map | Adapter input variable names are prose-only; no machine check | Variable rename in skill body or command passes grep tests; drift undetected | Add cross-file grep assertions for `$FEATURE_DESCRIPTION`, `$CONSTITUTION_PATH`, `$PRIOR_SPEC_SUMMARY` in adapter contract test |

---

### Questionable Assumptions

1. **"Behavior parity for `/devspark.specify` can be enforced by the existing integration test suite without new behavioral tests"** (spec.md Assumptions) → Failure mode: The existing `test_create_spec_workflow_integration.py` tests are workflow-runner contract tests (T-020 in that file checks workflow YAML structure), not end-to-end prompt-behavior tests. If the thin-wrapper refactor changes how the agent receives its instructions (prompt shape, ordering, variable names), the workflow runner tests may still pass while the actual agent behavior drifts. The test gap is real but accepted by the spec; implementers should be aware when authoring T025.

2. **"The open Agent Skills specification remains stable in the fields used by this feature"** (spec.md Assumptions) → Failure mode: If agentskills.io updates the spec to require new mandatory frontmatter fields (e.g., a `schema_version` key) or deprecates `metadata.version` in favor of a top-level `version`, the `write-spec` skill fails validation at clients without any CI signal. Mitigation: pin the spec version reviewed (2026-05-19) in `devspark-skills-guide.md` and add a note to re-review on upstream spec releases.

3. **"PyYAML can parse all skill frontmatter correctly"** → Failure mode: See critic-003. YAML 1.1 parses `on`/`off`/`yes`/`no` as booleans; a skill description containing "Turn on spec-drafting mode" has `on` as a YAML key if improperly quoted. Scoped risk, but worth one defensive test assertion.

4. **"The `write-spec/references/` files are loaded by the agent on demand"** → Failure mode: Progressive disclosure relies on client support. If a client loads the entire skill folder eagerly at startup (not uncommon in early adopters), the references/ files consume context budget regardless of task relevance. The `SKILL.md` body-length budget (500 lines) is respected, but `references/` has no stated size budget. Large reference files could bloat context. Mitigation: add a total-references size advisory (e.g., `references/` should stay under 2000 lines total) to `devspark-skills-guide.md`.

---

### Dependency Risk Assessment

| Dependency | Concern | Alternative |
| --- | --- | --- |
| PyYAML (implicit via transitive) | YAML 1.1 boolean surprises; may not be a declared direct dependency | `ruamel.yaml` (YAML 1.2, no boolean surprises); declare as direct dep |
| agentskills.io specification (external, no pinning) | Spec could change; no CI signal for upstream changes | Pin spec version reviewed in guide; note re-review trigger |
| `npx markdownlint-cli2` (via npx) | npx fetches latest if not cached; version drift in CI | Pin version in `package.json` devDependencies or CI step |
| PowerShell 5.1+ (assumed) | Scripts may use PS 7+ features unavailable on macOS/Linux PS 7 default | Test scripts on both PS 5.1 (Windows) and PS 7 (cross-platform) |

---

### Estimated Technical Debt at Launch

- **Testing Debt**: PyYAML semver-regex assertion missing (critic-003); portability body-scan missing (critic-008); adapter variable cross-check missing (critic-004). Estimated 2–3 test assertions to add.
- **Documentation Debt**: `warn` exit-code tier undocumented (critic-002); `references/` size advisory absent from guide (assumption 4); spec version pinning absent from guide (assumption 2).
- **Operational Debt**: No `--json` output for `skills list` means scripting consumers must screen-scrape (critic-007). Deferred but noted.
- **Dependency Debt**: PyYAML not confirmed as declared direct dependency (critic-006); `npx` version not pinned.

---

### Missing Critical Tasks

No tasks are critically missing relative to the archetype and risk profile. The
cli/library checklists surface the following gaps worth noting:

- **Documented exit codes (3-tier)**: Partially missing — critic-002. Resolvable in T004 authoring.
- **PyYAML direct dependency declaration**: Missing from T001 setup. Add a sub-task or amend T001.
- **Semver regex enforcement in tests**: Missing from T018 as specified. Add during T018 implementation.
- **Portability body-scan automated test**: Missing; T032 is manual-only. Add during T018 implementation.
- **`markdownlint-cli2` version pinning**: Not in scope of this feature, but a CI risk. Note in T002.

---

### Metrics

- **Showstopper count (effective):** 0
- **Critical count (effective):** 0
- **High count (effective):** 4 (critic-001, critic-002, critic-003, critic-004)
- **Medium count (effective):** 4 (critic-005, critic-006, critic-007, critic-008)
- **Findings by category:** cli\_ergonomics ×2, testing\_strategy ×2, api\_compatibility ×1, error\_handling\_resilience ×1, dependency\_supply\_chain ×1, missing-risk-profile ×1
- **Missing operational tasks:** 2 minor (PyYAML dep declaration, semver regex test)

---

**VERDICT:** PROCEED

All 8 findings resolved in spec.md, plan.md, and tasks.md before implementation.
No required actions remain. Recommended risk mitigations (Assumption 2 and 4)
are addressed via T006 authoring scope in tasks.md.
