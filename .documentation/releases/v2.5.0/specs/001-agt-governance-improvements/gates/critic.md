---
gate: critic
status: pass
blocking: false
severity: info
summary: "All 6 findings resolved 2026-06-03. Frontmatter added (critic-001), string-match anchors added to T010/plan (critic-002), T003/T005 anchor text and verification added (critic-003), L-006 + registry self-note + edge case added (critic-004), re-run obligation documented in T013/Notes (critic-005), T008 precise insertion point specified (critic-006). VERDICT: PROCEED."
---

# Technical Risk Assessment: AGT-Inspired Governance Improvements

**Analysis Date:** 2026-06-03
**Scope:** FULL (spec.md + plan.md + tasks.md)
**Detected Archetype:** `documentation-site` (pure Markdown governance toolkit; no runtime code, no framework, no storage)
**Detected Stack:** Markdown + YAML — no language runtime
**Context Mode:** `brownfield` (modifying existing command templates and adding companion documents to an established repository)
**Risk Profile:** `internal` (developer tooling; defaulted — no `risk_profile` in spec frontmatter)
**Risk Posture:** YELLOW

*No stack/archetype checklists found at `.devspark/risk-checklists/` — risks derived from first principles using the universal failure-mode lens.*

---

## Executive Summary

This feature delivers pure Markdown and YAML governance artifacts with no runtime code, no new tool dependencies, and no database or network surfaces — the production risk profile is inherently low. The primary risks are process-level: semantic evaluation of command templates depends entirely on AI agent judgment (no deterministic enforcement), brownfield edits to the critical `pr-review.md` template could silently break existing review flows if not applied carefully, and the spec's `internal` risk profile was inferred rather than declared. No showstoppers or critical findings. Proceed with implementation after noting the four HIGH findings.

---

## Findings (source of truth)

```yaml
findings:
  - finding_id: critic-001
    category: missing-risk-profile
    archetype_applicable: true
    location: spec.md#frontmatter
    description: >
      spec.md has no `risk_profile`, `archetype`, or `change_type` frontmatter fields.
      Defaulted to internal/documentation-site/brownfield per backward-compat rules.
      If this feature ships to other repos via DevSpark CLI, the risk profile may be
      customer-facing or higher — the absence of metadata makes this invisible to future
      critic runs.
    base_severity: high
    effective_severity: high
    recommended_action: >
      Add `risk_profile: internal`, `archetype: documentation-site`, and
      `change_type: brownfield` to spec.md YAML frontmatter before closing the PR.
    execution_mode: auto
    status: resolved
    outcome: "Applied 2026-06-03 per recommendations"

  - finding_id: critic-002
    category: trust_boundaries
    archetype_applicable: true
    location: plan.md#Phase1-Design-Contracts / tasks.md#T013
    description: >
      The prompt conformance check relies entirely on AI agent semantic judgment to
      determine whether a command template contains a "Constitution Authority block."
      There is no deterministic definition of what constitutes a passing evaluation.
      Two different AI agents (or the same agent on two different days) could reach
      opposite conclusions for the same template — particularly for edge cases like
      evolve-constitution.md's "## Lifecycle Position" variant. This means the
      conformance check cannot be meaningfully enforced in CI or audited.
    base_severity: high
    effective_severity: high
    recommended_action: >
      Add a concrete, testable definition to the conformance manifest for what
      constitutes a passing Constitution Authority check: e.g., "the template file
      MUST contain the exact string `constitution.md` and the word `non-negotiable`
      within 10 lines of each other." Document the evolve-constitution.md exemption
      explicitly with the qualifying text that passes. This makes the check reproducible
      across agent runs without requiring exact heading matches.
    execution_mode: selective
    status: resolved
    outcome: "Applied 2026-06-03 per recommendations"

  - finding_id: critic-003
    category: error_handling_resilience
    archetype_applicable: true
    location: tasks.md#T003 / tasks.md#T005
    description: >
      Both T003 and T005 make additive edits to `templates/commands/pr-review.md` —
      one of the most critical and complex command templates in DevSpark (835 lines).
      The tasks specify WHAT to insert but not WHERE precisely within the file's
      existing structure. An implementer who misreads the insertion point could
      accidentally nest new content inside an existing markdown code block, break
      heading hierarchy, or duplicate existing severity guidance. There is no
      rollback procedure specified if the edit corrupts the template.
    base_severity: high
    effective_severity: high
    recommended_action: >
      Expand T003 and T005 in tasks.md to specify exact anchor text for each insertion:
      for T003, "insert after the line '**CON**: Constitution needs updating...'" ;
      for T005, "insert after the line '### 1. Initialize Review Context' closing
      paragraph, before the line '### 2. Load Constitution'." Also add a verification
      step: after each edit, confirm the file still passes markdownlint and that the
      heading count for '###' sections has increased by exactly the expected amount.
    execution_mode: selective
    status: resolved
    outcome: "Applied 2026-06-03 per recommendations"

  - finding_id: critic-004
    category: documentation
    archetype_applicable: true
    location: spec.md#Out-of-Scope / plan.md#Interface-Contracts
    description: >
      The severity registry is explicitly designed as a companion document that must
      stay in sync with constitution.md across amendment cycles. However, there is no
      documented procedure for what happens when the constitution is amended by someone
      who does NOT run /devspark.evolve-constitution (e.g., a direct edit to
      constitution.md). The checklist item in evolve-constitution.md only fires when
      that command is used. A direct constitution edit bypasses the gate entirely,
      leaving the registry silently stale.
    base_severity: high
    effective_severity: high
    recommended_action: >
      Add a note to the severity-registry.md document itself (T002) stating:
      "If constitution.md is amended without using /devspark.evolve-constitution,
      the author MUST manually verify and update this registry in the same PR."
      Also add this as an explicit edge case in the spec's Edge Cases section
      and as a limitation entry in known-limitations.md (L-006).
    execution_mode: selective
    status: resolved
    outcome: "Applied 2026-06-03 per recommendations"

  - finding_id: critic-005
    category: testing_strategy
    archetype_applicable: true
    location: tasks.md#T013
    description: >
      T013 performs a one-time baseline conformance check and documents results
      as a comment in the manifest file. This is a snapshot test, not a repeatable
      test. If command templates are edited after this baseline is taken, there is
      no automated or semi-automated mechanism to re-run the check and detect
      regressions. The conformance check is only as good as the last time someone
      thought to run it.
    base_severity: medium
    effective_severity: medium
    recommended_action: >
      Add a note in the conformance manifest (T010) and in the README or
      CONTRIBUTING.md explaining that /devspark.checklist against
      prompt-conformance-manifest.md should be run before any PR that modifies
      files in templates/commands/. This is a process gate, not automation,
      but it should be documented as a contributor obligation.
    execution_mode: selective
    status: resolved
    outcome: "Applied 2026-06-03 per recommendations"

  - finding_id: critic-006
    category: documentation
    archetype_applicable: true
    location: tasks.md#T008
    description: >
      T008 adds a reference to known-limitations.md in constitution.md by
      appending a "See Also" line "at the bottom of the constitution." The
      constitution v1.4.0 ends with governance metadata (version, ratified date,
      last amended date). Appending after this metadata is fine, but the task
      does not specify whether the reference goes before or after the version
      line — an implementer could accidentally place it in a position that breaks
      the constitution's formatting or appears below the closing metadata in a way
      that looks orphaned.
    base_severity: medium
    effective_severity: medium
    recommended_action: >
      Expand T008 to specify the exact insertion point: "Add a '## Companion
      Documents' section immediately before the '**Version**:' metadata line at
      the bottom of constitution.md, containing a bullet: '- [Known Governance
      Limitations](.documentation/memory/known-limitations.md)'"
    execution_mode: auto
    status: resolved
    outcome: "Applied 2026-06-03 per recommendations"
```

---

## High

| ID | Category | Location | Issue | Impact | Suggestion |
|----|----------|----------|-------|--------|------------|
| critic-001 | missing-risk-profile | spec.md#frontmatter | No `risk_profile`, `archetype`, or `change_type` frontmatter — defaults used silently | Future critic runs on this feature branch will re-default, making metadata drift invisible | Add three frontmatter fields to spec.md before PR close |
| critic-002 | trust_boundaries | plan.md / T013 | Conformance check is purely AI-semantic with no deterministic pass/fail definition | Two runs could disagree on the same template; check cannot be CI-enforced or audited | Add testable string-match criteria to the conformance manifest alongside semantic evaluation |
| critic-003 | error_handling_resilience | T003, T005 | Insertion point for pr-review.md edits underspecified — 835-line file with complex structure | Mis-placed insertion could silently corrupt template structure or duplicate existing guidance | Expand T003/T005 with exact anchor text and post-edit heading-count verification |
| critic-004 | documentation | spec.md / plan.md | No procedure for direct constitution.md edits bypassing evolve-constitution — registry becomes silently stale | Constitution and registry drift undetected until next pr-review surfaces inconsistency | Add self-referential note in severity-registry.md + edge case + L-006 in known-limitations |

---

## Missing Critical Tasks

No missing operational tasks for a `documentation-site` archetype with no runtime code. The applicable universal failure-mode lens items (resource leaks, race conditions, unbounded growth, timeouts) do not apply to static Markdown files.

Process-level operational gap noted but not a missing task:

- **Re-run trigger for conformance check**: No contributor workflow specifies when to re-run `/devspark.checklist` against the conformance manifest. Addressed via critic-005 recommendation (documentation, not a new task).

---

## Questionable Assumptions

1. **"The AI agent performing conformance checks will be consistent across runs"** → Failure mode: Two different implementers (or the same implementer with different context) get contradictory pass/fail results for `evolve-constitution.md`. The known-variant-headings section of the manifest mitigates this but does not eliminate it for future edge cases. Mitigation: add string-match anchors per critic-002.

2. **"pr-review.md insertions are purely additive and cannot break existing behavior"** → Failure mode: The trust-tier step (T005) inserts a new numbered step between existing steps 1 and 2. If the existing step numbering is referenced by other commands or documentation via text anchors, the renaming (step 2 becomes step 2b or steps shift) could create dead cross-references. Mitigation: search for cross-references to "step 1" / "step 2" in pr-review.md before inserting.

3. **"The severity registry will be consulted by AI agents automatically"** → Failure mode: Nothing in the updated pr-review.md instructs the reviewing AI to *load* the severity registry before emitting findings. The template tells it to emit `§{section}.{LEVEL}` codes but doesn't say to verify those codes against the registry. The registry is useful for humans but invisible to the agent unless explicitly referenced in the command. Mitigation: T003 should explicitly instruct the pr-review template to load `.documentation/memory/severity-registry.md` as part of step 2 (Load Constitution).

---

## Dependency Risk Assessment

| Dependency | Concern | Alternative |
|---|---|---|
| `npx markdownlint-cli2` (T004, T006, T009, T012, T014) | Requires Node.js and internet access to run `npx`; may fail in air-gapped or Node-less environments | Use locally installed `markdownlint-cli2` binary; document in CONTRIBUTING.md |
| `/devspark.checklist` command (T013) | Command must be available and working at time T013 runs; if checklist command has a bug, baseline is invalid | Run checklist against at least 2–3 known-good templates manually as a sanity check before accepting baseline |
| AI agent consistency for conformance evaluation (T013) | Results depend on agent model version and context — not reproducible in the strict sense | Add string-match anchors per critic-002 to make the evaluation deterministic |

---

## Estimated Technical Debt at Launch

- **Documentation debt**: LOW — the spec, plan, and tasks are thorough. The main gap is the undocumented "re-run conformance check before template PRs" contributor obligation (critic-005).
- **Process debt**: MEDIUM — the direct-constitution-edit bypass (critic-004) is a known gap that requires a future process improvement or CAP to close formally.
- **Testing debt**: LOW — markdownlint provides automated validation for all new files. Conformance check is manual but documented.
- **Code debt**: N/A — no code produced.

---

## Metrics

- **Showstoppers**: 0
- **Critical**: 0
- **High**: 4 (critic-001, critic-002, critic-003, critic-004)
- **Medium**: 2 (critic-005, critic-006)
- **Low**: 0
- **Missing operational tasks**: 0
- **Questionable assumptions**: 3

**VERDICT:** CONDITIONAL

**Required Actions Before Implementation:**

1. **critic-001** (auto): Add `risk_profile: internal`, `archetype: documentation-site`, `change_type: brownfield` to spec.md frontmatter.
2. **critic-003** (selective): Expand T003 and T005 in tasks.md with exact anchor text and post-edit verification step for pr-review.md insertions.
3. **critic-002** (selective): Decide whether to add deterministic string-match criteria to the conformance manifest definition (T010) alongside semantic evaluation. Recommended but not blocking if team accepts the ambiguity.
4. **critic-004** (selective): Add direct-edit bypass note to T002 (severity-registry.md content) and as L-006 in known-limitations.md. Low implementation cost.

**Recommended Risk Mitigations:**

- Add a note to T003 that the updated pr-review.md template should explicitly instruct the reviewing agent to load `.documentation/memory/severity-registry.md` during step 2 — otherwise the registry is useful for humans but invisible to the AI agent at review time.
- Search for "step 1" / "step 2" cross-references in pr-review.md before executing T005 insertions.
- Document in CONTRIBUTING.md that `/devspark.checklist` against `prompt-conformance-manifest.md` is a required pre-PR step when editing any file in `templates/commands/`.
