---
gate: analyze
status: pass
blocking: false
severity: info
summary: "All 13 findings resolved in-place (2026-04-14): spec.md FR-027 field name and semantics corrected (H1, H2); FR-042 harness.policy.blocked added (M3); tasks.md T017 hardened with .gitignore, regression, --help, and partial-log assertions (M1, M2, L4, L5); T018 timing assertion added (L2); T020 file location fixed to config.py (M4, L3); Phase 3 checkpoint corrected for partial US1 delivery (M5); T032 adapter contract test added (M6). No CRITICAL or constitution violations found."
---

<!-- markdownlint-disable MD040 -->

# Specification Analysis Report: DevSpark Harness Runtime

**Feature**: `002-harness-runtime` | **Analyzed**: 2026-04-14
**Artifacts scanned**: spec.md, plan.md, tasks.md, data-model.md, contracts/harness-spec-yaml.md, contracts/cli-commands.md, contracts/events-schema.md, constitution.md

---

## Findings Table

| ID | Category | Severity | Location(s) | Summary | Resolution |
|----|----------|----------|-------------|---------|-----------|
| H1 | Inconsistency | HIGH ✅ | spec.md FR-027 | FR-027 used `version` field; all downstream artifacts use `apiVersion` | **Fixed**: spec.md FR-027 updated — "whose declared `apiVersion`" |
| H2 | Inconsistency | HIGH ✅ | spec.md FR-027 | FR-027 described version-range check; plan/data-model implement equality check | **Fixed**: spec.md FR-027 rewritten — "does not equal the CLI's supported version constant (`devspark.ai/v1`)" |
| M1 | Coverage Gap | MEDIUM ✅ | tasks.md T017 | FR-033 (.gitignore prohibition) had no verification task | **Fixed**: T017 now asserts `.gitignore` is unmodified before and after every run |
| M2 | Coverage Gap | MEDIUM ✅ | tasks.md T017 | SC-002 (zero regressions) had no explicit regression test task | **Fixed**: T017 now includes existing command suite assertion (`devspark init --help`, `devspark registry list`, `devspark upgrade --help`) |
| M3 | Inconsistency | MEDIUM ✅ | spec.md FR-042 | FR-042 listed 6 telemetry event types; contracts defined 7 — `harness.policy.blocked` missing | **Fixed**: `harness.policy.blocked` added to FR-042 enumeration in spec.md |
| M4 | Underspecification | MEDIUM ✅ | tasks.md T020 | T020 left user config file location undecided ("can be in runner.py or config.py") | **Fixed**: T020 now specifies `src/devspark_cli/harness/config.py` as the definitive module |
| M5 | Inconsistency | MEDIUM ✅ | tasks.md Phase 3 checkpoint | Checkpoint declared "US1 and US6 independently functional" — overstated; US1 scenarios 2–3 require Phase 7 | **Fixed**: Checkpoint now reads "US6 complete. US1 partial — scenarios 1,4,5 shippable; scenarios 2,3 require Phase 7 (T024)" |
| M6 | Coverage Gap | MEDIUM ✅ | tasks.md Phase 8 | T027–T029 (real adapters + app scope) had no contract test task | **Fixed**: T032 added — `tests/test_harness_adapters_contract.py` |
| L1 | Underspecification | LOW — no fix | spec.md FR-037 | "e.g., press a key" is vague; plan specifies `readchar.readkey()` | No change — plan is authoritative for implementation detail |
| L2 | Coverage Gap | LOW ✅ | tasks.md T018 | SC-004 (validate < 2s) had no automated timing assertion | **Fixed**: T018 now directs a `< 2s` timing assertion to `test_harness_spec_contract.py` (T007) |
| L3 | Coverage Gap | LOW ✅ | tasks.md T020 | SC-006 upgrade survival had no explicit path verification | **Fixed**: T020 now requires config path to be `platformdirs.user_config_dir()` only, not under `.devspark/` |
| L4 | Coverage Gap | LOW ✅ | tasks.md T017 | FR-032 (exit codes in help text) had no test assertion | **Fixed**: T017 now asserts `devspark harness run --help` output contains exit code documentation |
| L5 | Coverage Gap | LOW ✅ | tasks.md T017 | FR-026 partial log readability after abort had no trace assertion | **Fixed**: T017 now asserts `devspark harness trace <run-id>` renders partial log without error after Ctrl+C |

---

## Coverage Summary Table

| Requirement | Has Task? | Task IDs | Notes |
|-------------|-----------|----------|-------|
| FR-001 (load spec) | ✓ | T005 | |
| FR-002 (execute in order) | ✓ | T014 | |
| FR-003 (validate step output) | ✓ | T023, T024 | |
| FR-004 (retry with feedback) | ✓ | T024 | |
| FR-005 (stop on retries exhausted) | ✓ | T014, T024 | |
| FR-006 (write run artifacts) | ✓ | T014 | |
| FR-007 (noop default adapter) | ✓ | T012 | |
| FR-008 (validate against schema) | ✓ | T018 | |
| FR-009 (errors with field names) | ✓ | T005, T018 | |
| FR-010 (no execution on validate) | ✓ | T018 | |
| FR-011 (trace event table) | ✓ | T019 | |
| FR-012 (latest alias) | ✓ | T019 | |
| FR-013 (event table columns) | ✓ | T019 | |
| FR-014 (adapter list) | ✓ | T021 | |
| FR-015 (save adapter preference) | ✓ | T020, T022 | |
| FR-016 (preference survives upgrade) | ✓ | T020 | uses platformdirs |
| FR-017 (validate adapter name) | ✓ | T022 | |
| FR-018 (doctor checks) | ✓ | T026 | |
| FR-019 (doctor remediation) | ✓ | T026 | |
| FR-020 (doctor read-only) | ✓ | T026 | |
| FR-021 (existing commands unchanged) | ✓ | T016 | no regression suite task — see M2 |
| FR-022 (existing imports valid) | ✓ | T016 | |
| FR-023 (no config for non-harness repos) | ✓ | T016 | |
| FR-024 (sample harness spec) | ✓ | T009 | |
| FR-025 (harness.schema.json) | ✓ | T008 | |
| FR-026 (aborted status + artifacts) | ✓ | T014 | trace of partial log untested — see L5 |
| FR-027 (apiVersion enforcement) | ✓ | T005 | field name inconsistency in spec — see H1, H2 |
| FR-028 (run retention pruning) | ✓ | T014 | |
| FR-029 (retention limit in user config) | ✓ | T020 | |
| FR-030 (TTY auto-detect) | ✓ | T015, T018, T019 | |
| FR-031 (exit codes) | ✓ | T015 | |
| FR-032 (exit codes in help text) | ✓ | T015 | no assertion — see L4 |
| FR-033 (no .gitignore management) | ⚠ | none | prohibition; no verification task — see M1 |
| FR-034 (dry-run mode) | ✓ | T015, T017 | |
| FR-035 (dry-run on any valid spec) | ✓ | T015, T017 | |
| FR-036 (manual adapter prompt block) | ✓ | T013 | |
| FR-037 (manual adapter waits for key) | ✓ | T013 | |
| FR-038 (scope: app declaration) | ✓ | T029 | Phase 8 |
| FR-039 (scope: app path resolution) | ✓ | T029 | Phase 8 |
| FR-040 (7 validation rule types) | ✓ | T023 | |
| FR-041 (severity enforcement) | ✓ | T023, T024 | |
| FR-042 (7 named telemetry events) | ✓ | T010, T014 | spec lists only 6 — see M3 |
| FR-043 (StepResult findings + delta) | ✓ | T014, T024 | |
| SC-001 (noop < 5s) | ✓ | T017 | asserted in contract test |
| SC-002 (zero regressions) | ⚠ | T016 | no explicit regression suite — see M2 |
| SC-003 (retry visible in trace) | ✓ | T025 | |
| SC-004 (validate < 2s) | ⚠ | T018 | no perf assertion — see L2 |
| SC-005 (doctor install URLs) | ✓ | T026 | |
| SC-006 (adapter default survives upgrade) | ⚠ | T020 | no upgrade simulation — see L3 |
| SC-007 (sample + schema sufficient) | ✓ | T008, T009 | |
| SC-008 (CI exit code only) | ✓ | T015, T017 | |

---

## Constitution Alignment Issues

No violations found. All six principles verified:

| Principle | Status | Basis |
|-----------|--------|-------|
| I. Backward Compatibility (NON-NEGOTIABLE) | PASS | T016 is the only touch to an existing file (one `add_typer()` call); FR-021/022/023 explicitly enforce this; US6 is P1 |
| II. Explicit Over Implied (NON-NEGOTIABLE) | PASS | All scope declarations are explicit; noop default is a documented fallback, not silent scope inference; apiVersion enforcement is explicit rejection |
| III. Ownership Boundary (NON-NEGOTIABLE) | PASS | Run artifacts → `.documentation/devspark/runs/` (user-owned); JSON Schema → `.devspark/schemas/` (framework payload); FR-033 prohibits .gitignore management; no task modifies existing `.documentation/` content |
| IV. Governance Authority | PASS | App-scope harness (FR-038/039) routes through existing `scope.resolve_doc_root()` — repo-level governance preserved |
| V. Simplicity | PASS | Complexity tracking table in plan.md documents all additions with rejected-simpler-alternative rationale; T020 location needs one decision (see M4) |
| VI. Platform Parity | N/A | Harness commands are Python CLI only; no shell script equivalents required |

---

## Unmapped Tasks

| Task | Reason |
|------|--------|
| T031 (update spec.md status) | Workflow administration task — no FR maps to status field update; intentional |
| T030 (update sample.harness.yaml) | Maps to FR-024 (sample spec) — considered covered |

No tasks lack a mapped requirement.

---

## Metrics

| Metric | Value |
|--------|-------|
| Total Functional Requirements | 43 (FR-001–FR-043) |
| Total Success Criteria | 8 (SC-001–SC-008) |
| Total Tasks (post-fixes) | 32 (T001–T032) |
| FR Coverage (≥1 task) | 42/43 (97.7%) — FR-033 is a prohibition (verified via T017) |
| SC Coverage (≥1 task) | 8/8 ✓ |
| Ambiguity Count | 0 (L1 was inconsequential — no fix required) |
| Duplication Count | 0 |
| Inconsistency Count | 0 (H1, H2, M3 resolved) |
| Coverage Gap Count | 0 (all resolved) |
| Underspecification Count | 0 (M4, M5 resolved) |
| CRITICAL Issues | 0 |
| HIGH Issues Resolved | 2/2 |
| MEDIUM Issues Resolved | 6/6 |
| LOW Issues Resolved | 4/5 (L1 intentionally no-fix) |

---

## Next Actions

All findings resolved. Gate status upgraded to **pass**.

### Remaining Gate

`critic` has not been run. It is required per spec frontmatter (`required_gates: checklist, analyze, critic`). Run it before Phase 3 implementation begins.

```
/devspark.critic
```

After critic passes:

```
/devspark.implement
```
