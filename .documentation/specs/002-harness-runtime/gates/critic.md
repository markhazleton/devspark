---
gate: critic
status: fail
blocking: true
severity: showstopper
summary: "Two showstoppers and two high-severity delivery risks remain: the current model cannot express executable shell/function steps, manual gates are bypassed in non-TTY runs, doctor hard-codes an installed .devspark payload check, and app-scope integration calls the wrong scope API."
---

# Technical Risk Assessment: DevSpark Harness Runtime

**Feature**: `002-harness-runtime` | **Reviewed**: 2026-04-14
**Resolved scope**: repository | **Documentation root**: `.documentation/`
**Artifacts scanned**: `spec.md`, `plan.md`, `tasks.md`, `data-model.md`, `contracts/harness-spec-yaml.md`, `contracts/cli-commands.md`, `contracts/events-schema.md`, `/.documentation/memory/constitution.md`
**Detected stack**: Python 3.11+, Typer, Rich, Pydantic v2, platformdirs, readchar, PyYAML, local filesystem artifacts, Git, optional external agent CLIs

## Findings

| ID | Severity | Location(s) | Risk | Why this fails in practice | Required remediation |
|----|----------|-------------|------|----------------------------|----------------------|
| S1 | SHOWSTOPPER | `spec.md` Step/Adapter entities; `data-model.md` StepSpec; `contracts/harness-spec-yaml.md` full example; `tasks.md` T011/T023 | The design claims support for `function` + `shell` steps, but the actual step model has no execution payload for them. | The spec says a Step can be `agent_task`, `validation`, `function`, or `human_gate`, and that adapters execute both `agent_task` and `shell` steps. The sample contract includes a `shell-check` step. But StepSpec only carries `prompt_file`, `inputs`, `outputs`, `validation`, and routing; there is no field for a shell command, callable name, or function reference. The task plan then routes shell execution through `command.exit_code` validation instead of step execution itself. As written, Phase 2 cannot truthfully execute all supported step types or generate a faithful sample/schema pair. | Add an explicit execution contract for non-agent steps before implementation begins. At minimum, define the executable payload for `mode: shell` and `type: function`, decide whether they are step kinds or adapters, and update the data model, YAML contract, sample spec, and task list together. |
| S2 | SHOWSTOPPER | `spec.md` FR-037; `contracts/cli-commands.md` non-TTY output example; `plan.md` Phase 2 key decisions; `tasks.md` T013 | Manual review gates are bypassed in CI/non-TTY mode. | FR-037 requires the run to pause and wait for user confirmation before continuing. The CLI contract's non-TTY example shows a manual step failing the run. But the plan and task list implement the opposite behavior: `skipped_no_tty` without blocking. That converts a required human gate into an automatic pass-through in CI, which is exactly where teams are most likely to rely on exit codes alone. This creates false-positive successful runs for workflows that were explicitly intended to stop for human review. | Define a blocking non-TTY policy now. The safest default is: manual/human-gate steps fail or abort in non-interactive mode unless the user explicitly opts into a bypass mode in the spec. Reflect that in FR-037, CLI contracts, exit codes, and tests. |
| H1 | HIGH | `plan.md` Phase 3 key decisions; `tasks.md` T026; `src/devspark_cli/__init__.py` project detection | `devspark doctor` is specified against the installed `.devspark/` payload rather than the environments this repository already supports. | The planned doctor command treats `.devspark/` presence as a required health check. In the current source repository, there is no `.devspark/` directory at repo root, while the existing CLI already considers either `.devspark/` or `.documentation/` sufficient to identify a DevSpark project. That means doctor will report a broken environment for editable/source checkouts that the product itself currently recognizes as valid. This will create noisy false negatives for contributors and for any workflow that runs the CLI from source. | Split health checks into environment-level and installation-layout checks. Reuse the existing project detection rules instead of hard-coding `.devspark/` as mandatory, or explicitly scope doctor to installed-project validation and document a separate source-dev mode. |
| H2 | HIGH | `tasks.md` T029; `plan.md` Phase 4 key decisions; `src/devspark_cli/scope.py` `resolve_doc_root`; `src/devspark_cli/scope.py` `resolve_scope` | App-scope integration is planned against the wrong API and ignores existing ambiguity validation. | T029 says the runner can call `scope.resolve_doc_root(app_id, repo_root)` with no new resolution logic. The actual function takes an `AppDefinition | None`, not an app ID, and the repo already has `resolve_scope()` to validate app existence and explicit scope selection. If implemented as currently written, Phase 4 will either not compile, or it will re-implement a partial scope resolver and miss the existing error paths for unknown/ambiguous apps. | Change the plan before coding: the harness runner should resolve app scope through the same registry + scope-resolution path used elsewhere, then derive `doc_root` from the resolved app object. Add a contract test for unknown app IDs and multi-app ambiguity, not just the happy path. |

## Additional Risk Notes

- Backward compatibility is under-tested relative to the claim in SC-002. `tasks.md` only checks `devspark init --help`, `devspark registry list`, and `devspark upgrade --help`, which is materially weaker than "the existing command suite" for a monolithic CLI entrypoint.
- Using directory mtime as the sole source of truth for `trace latest` and retention pruning is brittle after artifact copies/restores or manual edits. It is serviceable for a prototype, but not a stable definition of recency.
- The spec's assumptions explicitly defer non-interactive `human_gate` behavior, but the plan and tasks already bake in one behavior. That drift needs to be closed before Phase 2 implementation.

## Constitution Check

No direct constitution violation is documented in the current artifacts. The primary issue is delivery viability: the current plan leaves required behavior underspecified or contradictory in ways that will fail during implementation and CI usage.

## Go/No-Go Recommendation

**NO-GO** for `/devspark.implement` in the current state.

Address S1 and S2 first, then regenerate the plan/tasks sections that depend on execution semantics and app-scope resolution. After that, rerun `/devspark.analyze` only if the artifacts materially change, and rerun `/devspark.critic` before implementation starts.

## Evidence Pointers

- Step kinds and adapter scope are declared in `spec.md` (Step and Adapter entities) and exemplified in `contracts/harness-spec-yaml.md` (`shell-check`), but StepSpec in `data-model.md` lacks any executable payload field.
- Manual-gate intent is defined in `spec.md` FR-037 and `contracts/cli-commands.md`, while `plan.md` and `tasks.md` currently implement `skipped_no_tty` instead.
- Scope integration assumptions in `tasks.md` T029 do not match the actual signature and validation flow in `src/devspark_cli/scope.py`.
- Doctor's required `.devspark/` check in `plan.md` and `tasks.md` is stricter than the current project-detection logic in `src/devspark_cli/__init__.py`.