```yaml
gate: critic
status: warn
blocking: false
severity: warning
summary: "No showstoppers; 3 critical risks, 6 high-priority concerns, and several missing operational tasks require attention before implementation."
```

## Technical Risk Assessment

**Analysis Date:** 2026-04-19
**Risk Posture:** YELLOW (0 showstoppers, 3 critical, 6 high)
**Detected Stack:** Python 3.11+ / typer+rich+click CLI / File-based artifacts / Cross-platform (Windows/macOS/Linux)

### Executive Summary

The feature is architecturally sound and well-specified but carries critical risks around convergence loop correctness, stall-detection false positives, and the absence of integration tests for the hands-off lifecycle chain. The scope is large (47 tasks, 8 phases, cross-cutting) and the plan acknowledges this via a governance checkpoint, but task estimates are implicit and several operational concerns are unaddressed. Recommend proceeding with caution after addressing the critical risks below.

### Showstopper Risks (Must Fix Before Implementation)

*None identified.* Constitution compliance was verified in the plan's gate check. No security breaches, data loss vectors, or blocking architecture flaws detected.

### Critical Risks (High Probability of Costly Issues)

| ID | Category | Location | Risk Description | Likely Impact | Recommended Action |
|----|----------|----------|------------------|---------------|--------------------|
| CR-1 | Convergence Loop | FR-018 / T026 | The iterative remediation loop (max 3 passes) for analyze/critic stages has no specification for how "auto-remediation" actually works. The plan says analyze and critic "MUST apply configured auto-remediation rules" but no remediation engine exists in the current codebase and no task creates one. The loop controller (T026) will have nothing to call. | Hands-off mode will either skip remediation entirely (rendering the loop useless) or require a large unplanned implementation effort for an LLM-driven fix engine. | Add explicit tasks for a remediation dispatcher that invokes agent adapters to fix findings. Alternatively, scope the MVP convergence loop to re-validation only (detect if manual fixes resolved issues between passes) and defer auto-remediation to a follow-up feature. |
| CR-2 | Stall Detection | FR-008 / T011 | Stall detection fires after 5 minutes of output inactivity. The current adapter model (`AgentAdapter.execute`) is synchronous and blocking — it calls `subprocess.run` or equivalent and returns when done. There is no streaming output model to monitor. Stall detection requires either async subprocess monitoring or a background watchdog thread, neither of which exists in the codebase. | Stall detection will be impossible to implement without refactoring the adapter execution model to use streaming I/O or background monitoring, adding significant unplanned complexity. | Either (a) refactor adapter execution to use `subprocess.Popen` with streaming output and a watchdog timer, or (b) descope stall detection to a post-step timeout check (step exceeded N minutes total) which is achievable with the current model. |
| CR-3 | Scope Creep | tasks.md overall | 47 tasks across 8 phases touching CLI runtime, templates, scripts, docs, and contracts. The plan explicitly flags this as a "cross-cutting change" requiring governance approval. No effort estimates exist. Based on codebase analysis, Phases 2 and 5 alone require new models, new command flows, a lifecycle orchestrator, convergence loops, and adapter gating — each a significant implementation unit. | High probability of incomplete delivery, where early phases consume available effort and later phases (US3, US4, parity) are deferred indefinitely, leaving the feature half-implemented. | Break into at least 2 PRs: PR1 = Phases 1-3 (delivery integrity MVP), PR2 = Phases 4-8 (adapter doctor, hands-off, policies, parity). Each PR is independently valuable and reviewable. |

### High-Priority Concerns

| ID | Category | Location | Issue | Impact | Suggestion |
|----|----------|----------|-------|--------|------------|
| HP-1 | Missing Integration Tests | tasks.md | No task creates integration tests for the hands-off lifecycle chain (plan→tasks→analyze→critic→implement→create-pr→pr-review). T045/T046 mention "validation smoke" and "full pytest" but no new test files are specified for convergence, adapter doctor, or delivery-status gating. | Convergence and gating logic will ship without automated regression coverage, creating silent breakage risk on future changes. | Add explicit tasks for `test_delivery_status_contract.py`, `test_convergence_loop_contract.py`, `test_adapter_doctor_contract.py`, and `test_hands_off_lifecycle_contract.py`. |
| HP-2 | Git Diff as Delivery Evidence | FR-002 / T006 | Delivery evidence relies on `git diff` to detect `src/**` or `test/**` mutations. This assumes changes are uncommitted or staged. If the adapter commits changes (some adapters auto-commit), `git diff` against HEAD will show nothing. The spec doesn't define which git diff reference to use (working tree, staged, HEAD~1, branch diff). | False negatives where real implementation work is missed because commits already landed, causing delivery_status=unmet despite actual delivery. | Specify the diff reference explicitly: `git diff origin/main...HEAD -- src/ test/` (branch diff) for committed changes, plus `git diff --cached` for staged. Add this to the data model contract. |
| HP-3 | Adapter Doctor Probe Design | T021 | "Behavior-based adapter doctor probes" are unspecified. The current `AgentAdapter` protocol has only `is_available()` and `execute()`. There's no `can_write()`, `requires_approval()`, or probe mechanism. Distinguishing `read-only-works` from `write-approval-required` requires actually attempting a write operation or parsing adapter-specific configuration, neither of which is defined. | Adapter doctor will either (a) produce inaccurate classifications based on guesswork, or (b) require adapter-specific hardcoded knowledge that breaks when adapters change. | Define a `probe()` method on the `AgentAdapter` protocol that returns a `ProbeResult` with capability flags. Each adapter implements its own probe logic. Document the probe contract. |
| HP-4 | Non-UTF Decode Handling | FR-012 / T011 | The spec requires "fail-soft" handling of non-UTF terminal bytes. The current `subprocess.run` calls in `validation.py` use `text=True` which will raise on decode errors. The adapter base uses `read_text(encoding="utf-8")`. There's no `errors="replace"` or `errors="surrogateescape"` anywhere in the subprocess execution path. | On Windows especially, non-UTF-8 output from tools (common with PowerShell, MSBuild, etc.) will cause hard crashes in step execution rather than the intended fail-soft behavior. | Add `errors="replace"` to all subprocess text decoding in adapter and validation code. Emit a telemetry event when replacement occurs. |
| HP-5 | Two Runner Architectures | runner/executor.py vs harness/runner.py | The codebase has two separate runner implementations: `runner/executor.py` (workflow runner with pause/resume) and `harness/runner.py` (harness runner with validation). Tasks reference both. T025 creates a "full lifecycle orchestrator" in `runner/executor.py` while T026/T027/T028 add convergence logic in `harness/runner.py`. How these two runners interact is undefined. | Confusion about which runner owns lifecycle control, potential duplication of execution logic, and integration bugs where one runner's state model conflicts with the other's. | Clarify in the plan which runner is the top-level orchestrator for hands-off mode and which is a subordinate. Ideally the workflow runner (`executor.py`) orchestrates step sequencing while `harness/runner.py` handles per-step validation and delivery checks. |
| HP-6 | Platform Parity Gap | T042/T043 | Bash and PowerShell parity tasks are in Phase 8 (last), but the governance checkpoint and adapter doctor features in earlier phases may require script changes. Constitution Principle VI mandates platform parity. Deferring parity to the end risks shipping an intermediate state where PowerShell and Bash diverge. | Constitution violation if intermediate PRs ship with platform-divergent behavior. | Move parity verification to each phase checkpoint rather than deferring to Phase 8. At minimum, include a parity smoke check in each phase's checkpoint criteria. |

### Framework-Specific Red Flags

**Python + typer/rich/click CLI:**

- [x] No async concerns in CLI layer (CLI is synchronous — appropriate for this tool)
- [ ] `subprocess.run` with `shell=True` in `validation.py` line 46 — shell injection risk if `rule.command` comes from user-controlled YAML. Currently mitigated by file-based harness specs but worth noting for future extensibility.
- [ ] No `text=False` + explicit decode path for non-UTF subprocess output (HP-4)
- [ ] Missing `timeout` parameter on `subprocess.run` calls in `validation.py` — a hanging command will block the entire CLI indefinitely
- [ ] `secrets.token_hex(3)` for run IDs gives only 6 hex chars (16M combinations) — sufficient for local use but could collide in CI environments with concurrent runs

**File-based artifact storage:**

- [ ] No file locking on concurrent writes to run directories — if two harness runs execute simultaneously, artifact corruption is possible
- [ ] `_atomic_write` in `executor.py` uses `os.replace` which is atomic on POSIX but has edge cases on Windows network drives

### Architecture Red Flags

- [ ] Over-engineered for stated requirements — The iterative remediation loop with finding state transitions (open→resolved→deferred), max-pass convergence, and per-pass iteration records is a substantial state machine for what is currently a single-user CLI tool. **Justified** given the stated goal of fully unattended execution, but adds significant testing surface.
- [x] Under-engineered for implied scale — Not applicable; repository-level CLI tool.
- [ ] Single point of failure without redundancy — The adapter is the single execution path. If the chosen adapter fails, there's no fallback. The adapter doctor helps detect this pre-flight but doesn't solve mid-run adapter failures.
- [ ] Missing standard patterns for problem domain — No circuit breaker or retry with backoff for adapter execution failures during hands-off mode. A transient adapter failure will fail the entire run.
- [x] Inadequate async/concurrency handling — Not applicable; intentionally synchronous.

### Missing Critical Tasks

- **Testing:** No tasks for new contract test files covering delivery status, convergence loops, adapter doctor, or hands-off lifecycle integration
- **Operations:** No task for updating CI/CD configuration to run new tests or validate new harness features
- **Security:** No task to audit `shell=True` subprocess calls with harness spec-provided commands for injection risk
- **Documentation:** No task to update `CHANGELOG.md` with new feature entries
- **Parity:** No per-phase parity verification (deferred entirely to Phase 8)

### Questionable Assumptions

1. **"Auto-remediation rules" exist or can be built** → The spec and plan reference auto-remediation in analyze/critic stages but no remediation engine exists. Building an LLM-driven auto-fix system is a feature unto itself. Without it, the convergence loop is a re-validation loop only — which is still valuable but should be named accurately.

2. **Git diff reliably captures implementation evidence** → Git diff behavior varies by adapter (some auto-commit, some leave changes staged, some leave them unstaged). The spec assumes a single diff strategy works for all adapter modes. It won't.

3. **Adapter capability can be probed non-destructively** → Distinguishing "write-approval-required" from "available" for adapters like Copilot or Claude Code may require actually attempting a write operation. A non-destructive probe may not be technically feasible for all adapters without adapter-specific heuristics.

4. **5-minute stall threshold is universal** → Legitimate long operations (large repo analysis, extensive test suites, AI model inference) can easily exceed 5 minutes without output. The spec mentions "legitimately long operations that still produce intermittent output" as an edge case but the current adapter model provides no output streaming to distinguish stalled from working.

5. **47 tasks can be sequenced correctly without circular dependencies** → The dependency graph has Phase 2 blocking everything, US5 depending on US1+US2, and US4 depending on US1+US2+US5. But within phases, tasks reference the same files (e.g., 8 tasks modify `harness/runner.py`) creating implicit ordering dependencies not captured in the task graph.

### Dependencies Risk Assessment

| Dependency | Concern | Alternative to Consider |
|------------|---------|-------------------------|
| pydantic (models) | Heavy use for new entities; schema migration needed if models change | Acceptable; already in use throughout codebase |
| git CLI | Delivery evidence relies on `git diff` subprocess calls | Consider using `gitpython` for programmatic access with better error handling |
| subprocess (shell=True) | Validation engine passes spec-provided commands to shell | Use `shlex.split` + `subprocess.run(shell=False)` where possible |
| File system (artifacts) | All state persisted as files; no locking | Acceptable for single-user CLI; document concurrency limitation |

### Estimated Technical Debt at Launch

- **Code Debt:** Two runner architectures (`runner/executor.py` and `harness/runner.py`) with overlapping concerns; convergence loop without true auto-remediation engine
- **Operational Debt:** No CI integration tasks; parity testing deferred to final phase
- **Documentation Debt:** No CHANGELOG update task; adapter doctor probe contract undocumented
- **Testing Debt:** No new contract test files specified for core new functionality (delivery status, convergence, adapter doctor)

### Metrics

- Showstopper Count: 0
- Critical Risk Count: 3
- High-Priority Concern Count: 6
- Missing Operational Tasks: 5 categories
- Underspecified Security Requirements: 1 (shell injection surface)
- Scale Bottlenecks Identified: 0 (appropriate for CLI tool scope)
- Questionable Assumptions: 5

---

**GO/NO-GO RECOMMENDATION:**

```text
[ ] STOP - Showstoppers present, cannot proceed to implementation
[x] CONDITIONAL - Fix critical risks first, then reassess
[ ] PROCEED WITH CAUTION - Document acknowledged risks, add mitigation tasks
```

**Required Actions Before Implementation:**

1. **CR-1**: Clarify what "auto-remediation" means in the convergence loop. Either (a) add tasks for a remediation dispatcher that invokes adapters to fix findings, or (b) explicitly scope the loop as re-validation-only for MVP and rename accordingly.
2. **CR-2**: Decide on stall detection approach — either refactor to streaming subprocess execution or descope to total-step-timeout (achievable with current architecture).
3. **CR-3**: Split the 47-task plan into at least 2 independently deliverable PRs to reduce delivery risk.

**Recommended Risk Mitigations:**

- Add tasks for: `test_delivery_status_contract.py`, `test_convergence_loop_contract.py`, `test_adapter_doctor_contract.py`, `test_hands_off_lifecycle_contract.py`
- Revise plan to address: git diff reference strategy for delivery evidence (HP-2), adapter probe protocol design (HP-3), non-UTF decode handling (HP-4), dual-runner orchestration model (HP-5)
- Clarify spec requirements for: auto-remediation semantics, stall detection architecture, adapter write-capability probing
- Move platform parity checks from Phase 8 into per-phase checkpoints (HP-6)
- Add `subprocess.run` timeout parameters throughout validation and adapter execution code
