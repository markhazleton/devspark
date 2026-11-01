---
id: devspark-prompt-mapping
role: governance
appliesTo:
- templates/commands/explain.md
- templates/commands/merge-from-main.md
- templates/commands/pr-review.md
- scripts/bash/merge-from-main.sh
- scripts/powershell/merge-from-main.ps1
- scripts/bash/get-pr-context.sh
- scripts/powershell/get-pr-context.ps1
- scripts/pr-risk.py
- scripts/pr-review-validate.py
- scripts/pr-risk-calibrate.py
- tests/test_explain_scope_contract.py
- tests/test_merge_from_main_contract.py
- tests/test_pr_risk_contract.py
- tests/test_pr_risk_knowledge_contract.py
- tests/test_pr_review_validate_contract.py
- tests/test_pr_risk_calibrate_contract.py
- scripts/pr-review-state.py
- scripts/pr-review-validate.py
- tests/test_pr_review_state_contract.py
- tests/test_pr_review_validate_contract.py
- tests/test_review_resolution_contract.py
source_of_truth:
- templates/commands/pr-review.md
- templates/commands/address-pr-review.md
- templates/pr-review-state-contract.md
- scripts/pr-review-state.py
- scripts/pr-review-validate.py
- tests/test_pr_review_state_contract.py
- tests/test_pr_review_validate_contract.py
- tests/test_review_resolution_contract.py
last_verified: 2026-10-14
---

# DevSpark: Prompt Inventory Mapped to Philosophy

Companion to [the DevSpark Manifesto](devspark-philosophy.md). This is a **descriptive inventory
of currently implemented commands**, not a required developer journey and not a substitute for
actual command templates. Model First, Code First, a bounded experiment, and defect-driven work
may start at different points and must converge on applicable Delta and blast-radius assurance.
Entries below describing mandatory spec artifacts apply only to routes that actually use a spec.
Any unsupported entry point is identified as a capability gap, not treated as a governance
violation by the developer.

## New work — universal start and resume

| Command | Current behavior |
|---|---|
| **specify** | The single start point for new work: establishes the intended outcome and first useful increment, inspects relevant code/tests/Knowledge, and checks whether material assurance is needed. It offers work-item grounding only when tracking is configured and the developer names an item, keeps tracker text untrusted, and carries verification expectations into implementation. It creates a `NNN-work-*` branch without a specification or other file. A minimal `work.md` is written only when intent, decisions, blockers, status or next action would otherwise be lost across sessions. It does not classify work by size or generate planning gates; DevSpark no longer creates new full-spec or quick-spec bundles, and existing ones continue. |
| **clarify** | Retained for active v9.3 specification bundles. New work asks only for a material decision that blocks the affected implementation; it does not create a question ledger or route through a clarification stage. On a `NNN-work-*` branch the prerequisite check resolves `FEATURE_SPEC` to the optional `work.md`, which clarify must not treat as a spec: it creates no `spec.md`, writes no `## Clarifications`, asks at most five questions in conversation, records an answer under `## Material Decisions` only when it must survive the session, and returns to implementation. |
| **plan** | Retained for active v9.3 bundles and available on request when a material design or contract decision needs a durable record. It is not a prerequisite for new work. On a `NNN-work-*` branch it needs no specification and writes, only when requested or justified by a material uncertainty, a concise advisory `plan.md` that implementation may follow but never requires; it adds no tasks, gates or reviews and does not change the work route. |
| **tasks** | Retained for active v9.3 bundles and optional coordination where dependencies or parallel ownership justify a task list. New work does not generate tasks merely to route to Implement. On a `NNN-work-*` branch it needs no specification or plan. It identifies a few dependency-ordered deliverables (or states that none are needed) and tracks them with the agent's built-in task tracking. Only when the list must survive a session, spans substantial dependencies, or coordinates several developers does it record a `## Remaining Deliverables` checklist in the optional `work.md`; it never writes `tasks.md` there. Open deliverables are not a completion gate, and the command triggers no Analyze, Critic, Judge or Planning Review. |
| **analyze** | The **closed-world** half of planning assurance: proves the planning artifacts are internally sound. Owns artifact consistency, requirement↔task coverage and traceability, requirement anchors, task sequencing validity, task mechanisms the Plan does not support (justified support files are fine; new architecture is not), completion bookkeeping, declared-contract conformance, and `context_resolved` **validity** — a stale or hallucinated reference is CRITICAL, the same severity class as traceability hallucination. It also reports a Plan whose mechanism contradicts a recorded spec decision or changes declared behavior (semantic fidelity), report-only and without proposing a redesign. Everything it owns is provable from the artifacts alone. Open-world concerns are routed to `critic` under `routed_findings:`, never emitted. On a `NNN-work-*` branch it runs on demand for one stated concern (`WORK` tier): whether the recorded intent, plan decisions, declared contracts and tests contradict one another on it. It reports one compact result, writes no gate file, and returns to implementation. |
| **critic** | The **open-world** half of planning assurance: challenges whether that internally sound plan is wrong about the real system it will run in. Applies on observable change shape — persistent-data shape, cross-boundary interaction, state/lifecycle, nondeterministic behavior, new entry point — not on authored `risk_level`, which only scales severity. Must inspect the relevant existing code, tests, and `.knowledge/` before claiming anything about current behavior. Judges `context_resolved` *sufficiency* (`analyze` already confirmed it *resolves*), and emits a sufficiency finding only when the omission is demonstrably material. Emits no finding for its own missing metadata, and never reviews the work that resolved its earlier findings. On a `NNN-work-*` branch it runs on demand for one stated concern (`WORK` tier) against the current code, tests, contracts and `.knowledge/`. It reports one compact result, writes no gate file, and returns to implementation. Its handoffs are offered, never auto-sent. |
| **checklist** | An ephemeral planning aid for existing v9.3 specifications, same lifecycle as the rest of the package. On a `NNN-work-*` branch it writes no `checklists/` file and no `gates/checklist.md`, answers one named requirements-quality concern in conversation, and returns to implementation; its only handoff is back to implementation. |
| **planning-review** | Retained for active v9.3 bundles or invoked for a specific planning concern. It is not a default pre-implementation sequence for new work. Its existing Analyze/Critic/Judge semantics and freshness behavior are unchanged for bundles. On a `NNN-work-*` branch, `judge.py resolve` reports `work-branch`. Judge then adjudicates only genuinely conflicting findings or a consequential trade-off, in chat, with no gate file. A decision needing someone else's authority goes to that person. Analyze or Critic never obliges a Judge run. |
| **quickfix** | Retained as a direct legacy entry point. `/devspark-next` no longer asks developers to choose it over Specify; new work starts through the same `work` branch path. Scope discovered mid-fix never converts the route: a material signal adds only the assurance its concern needs (Critic, record-level Analyze, or a human decision) to the same quickfix, and the developer decides whether genuinely separate work starts with Specify. |

### Planning Review in one place

For new work, the default path is *specify → implement ↔ verify → create-pr → pr-review*.
Implementation and verification may iterate. Existing v9.3 specification bundles keep their
current *plan → tasks → planning-review → implement* behavior and are not migrated. No synthetic
planning bundle or historical approval is created solely to reconstruct a new-work journey.
Analyze, Critic and Judge retain their existing responsibilities and may still be invoked for
specific concerns. Judge does not discover or remediate; each adjudicated concern still cites its
existing child finding, and existing seal/freshness checks remain unchanged. Four finding terms stay separate:

| Term | Meaning |
|---|---|
| **classification** | The finding's convergence state: `blocking-defect`, `accepted-limitation`, `deferred-work`, `learning` |
| **resolution** | The smallest valid remediation choice: `require`, `simplify`, `accept`, `defer` |
| **route** | A later phase (`verify`, `closeout`, `pr-review`) owns the proof. A routed obligation is still part of this spec's completion — it is not deferred |
| **future work** | A real discovery intentionally removed from scope, preserved outside the spec as a Future Work Plan under `.devspark.work/intake/`. DEFER is a disposition, not a task status |

Only authorized `require` and `simplify` corrections become current work. The remediation helper
separates `plan_revisions` from `task_work`; Plan and machinery corrections default to Plan, while
explicit `revision_target` selects Plan or Tasks. Ambiguous ownership uses pending decisions rather
than task creation. Accepted, deferred and routed obligations keep their existing owners and never
enter either automatic-work partition. Create PR means DevSpark believes the spec is complete:
a pull request represents completed spec work offered for acceptance, and merge terminates the
spec lifecycle. It also means DevSpark believes the committed revision is complete, internally
consistent, and ready for other people to review: the deterministic checks it can run against the
pushed HEAD (generated Knowledge matches that commit, and no Knowledge entity the PR touches is
stale) must pass, and a known failure stops it. PR Review independently evaluates a change that
already claims readiness; it is not completion detection, and it re-checks the same Knowledge state
read-only.

The deterministic helper also provides `semantic-hash --path <artifact>` for supported planning
roles. It emits an algorithm-tagged `sem1:` fingerprint without rewriting the artifact. Recognized
status, completion, linkage and producer metadata can be excluded while requirements, design,
task definitions, unknown fields and literal whitespace remain significant. Malformed YAML,
duplicate mapping keys, unclosed fences and unsupported roles yield an unavailable fingerprint,
not evidence of unchanged semantics. Raw hashes remain separate provenance facts. The CLI and
projection boundaries are pinned by `test_semantic_hash_cli_ignores_only_spec_status`,
`test_semantic_projection_preserves_decisions` and
`test_semantic_projection_unavailable_for_unsafe_input` in `tests/test_judge_contract.py`.

New child reports optionally record these fingerprints per planning input, and Judge optionally
records them per child while retaining raw hashes. Compatible unchanged decisions produce
non-blocking `bookkeeping-changed`; absent or incompatible metadata keeps legacy raw behavior.
Semantic task-scope changes invalidate evidence even after execution starts. Approved source
changes remain execution evidence for Verify/PR Review, not unchanged code; unexplained, missing
and governance inputs still require review. Child annotations cannot hide an undispositioned
reopened blocker, changed classification or weakened proof. Seal/guard concurrency stays raw.
These boundaries are exercised by `test_recorded_semantics_handle_status_without_rewriting_gates`,
`test_execution_evidence_retains_planning_boundaries`,
`test_child_annotations_cannot_hide_reopened_blockers_or_weakened_proof` and
`test_completion_bookkeeping_preserves_review_and_lifecycle` in `tests/test_judge_contract.py`.

Both Next wrappers consume the helper's exact Verify-mode readiness. Pending authority takes
precedence over automatic STOP remediation, and required Judge evidence is not replaced by child
files. Completed work with missing proof runs Verify; missing Closeout is recovered through Verify,
and not-complete returns to approved defect handling. Once proof and Closeout are satisfied, retained
bundles proceed through existing Git/PR states without deletion or another implementation pass.
`test_completed_bundle_routes_through_required_proof`,
`test_pending_authority_precedes_stop_remediation`,
`test_completed_retained_bundle_reaches_git_and_pr_states` and
`test_semantic_completion_bookkeeping_reaches_delivery_without_recheck` in
`tests/test_next_context_resolution_contract.py` exercise these boundaries offline in both shells.

Plan setup creates a Plan only when absent. Existing empty, template-only, authored, BOM and CRLF
files remain byte-identical; `PLAN_EXISTS` reports prior existence and `PLAN_MODE` is `create`,
`revise` or `reset`. Only explicit `--reset` / `-Reset` replaces the Plan with the resolved template.
Existing output keys and Knowledge refresh behavior are retained. Both shells are exercised by
`test_setup_plan_preserves_bytes_until_explicit_reset` in `tests/test_spec_hardening_contract.py`.
On a `NNN-work-*` branch, setup reports `WORK_BRANCH` true, an empty `FEATURE_SPEC` and the optional
`WORK_NOTE`, and creates nothing: it neither copies the full-spec template (even with reset) nor
refreshes the spec knowledge document. `check-prerequisites` lists an existing work-branch
`plan.md` in `AVAILABLE_DOCS`; `next-context` ignores it for routing, and Judge lifecycle adds no
gate for it. Both shells are exercised by `test_setup_plan_on_a_work_branch_needs_no_specification`,
`test_work_branch_prerequisites_expose_an_optional_plan` and
`test_an_optional_plan_keeps_work_on_the_universal_route`.

On a `NNN-work-*` branch whose work directory exists, both `next-context` shells run `judge.py
lifecycle` against it and report `LIFECYCLE_STATUS` and `LIFECYCLE_BLOCKERS`; they do not parse
`work.md` obligations themselves. A committed branch whose lifecycle check fails routes to
`delivery-blocked` instead of `ready-for-pr`: an unchecked `## Required Obligations` entry, or one
checked without its authority or an evidence reference (a repository path, commit, review or
approval id, or link; prose and placeholders do not count), recommends `resolve-obligation` and
names the obligation and its authority, and any other failure
returns to `/devspark-implement`. An open obligation on work that is still in progress or
uncommitted keeps that route and adds a "Delivery stays blocked" note. Advisory findings and
material decisions never block. If Python cannot run the check, the route is unchanged and the PR
recommendation says readiness is unconfirmed; `/devspark-create-pr` still runs the same check. Spec
and quickfix bundles keep their existing ladder. Both shells are exercised by
`test_work_that_passes_lifecycle_reaches_the_pr_path`,
`test_an_unresolved_obligation_blocks_the_pr_recommendation`,
`test_a_checked_obligation_without_an_evidence_reference_still_blocks_delivery` and
`test_an_open_obligation_is_named_before_delivery_without_changing_the_route`. The reference rule
itself lives only in `judge.py lifecycle` and is exercised by
`test_a_checked_obligation_needs_an_evidence_reference_and_its_authority`; it confirms a reference
is recorded, not that the approval behind it is authentic.

The `create-pr` preflight in both shells reports the same check as `lifecycle` (`status` of `pass`,
`fail`, `unavailable` or `not-applicable`, with `failures` and `pending_later_phase`) for any route
whose work directory or planning bundle exists. Create and update mode refuse
`required-obligation-unresolved`, with `CREATE PR BLOCKED — REQUIRED OBLIGATION UNRESOLVED`, the
committed HEAD, and each obligation's authority. The refusal clears when the `work.md` entry is
checked with a reference to the evidence or the authority's decision, then committed and pushed;
no flag bypasses it. An `unavailable` check is never a pass: it carries a `reason`
(`judge-missing`, `python-unavailable` or `invalid-output`) and `obligations_declared`, and when
`work.md` declares `## Required Obligations` create and update mode refuse with
`CREATE PR BLOCKED — LIFECYCLE CHECK UNAVAILABLE` and the recovery step for that reason. Without
declared obligations an unavailable check is reported as unconfirmed and does not refuse, and
`/devspark-next` says the same in its `REASON`. Other lifecycle failures stay a prompt-level stop
the developer may override. Create and update mode exit `1` on every refusal or failure and `0`
only on `status: ok`, in both shells. On a work branch `/devspark-verify` answers delivered,
verified and eligible from proportional proof and writes no gate document; `/devspark-closeout`
reassesses the same questions without one. Both shells are exercised by
`test_an_unresolved_obligation_refuses_creation_and_names_its_authority`,
`test_an_unevaluated_obligation_refuses_creation_and_says_why`,
`test_create_and_update_exit_codes_separate_success_from_refusal` and
`test_both_shells_report_the_same_lifecycle` in
`tests/test_create_pr_knowledge_readiness_contract.py`.

Revision state compares reviewed Plan/Tasks inputs and Tasks' recorded `plan_semantic_hash`.
Changed inputs do not resolve a concern or rewrite Judge. An owned STOP routes to Plan revise,
then stale Tasks re-projection, then focused review; unrelated specification changes return to
review first. Plan preserves unrelated sections, and Tasks must ask before invalidating completed
work. `test_remediation_is_partitioned_by_authorized_owner`,
`test_invalid_revision_owner_is_rejected` and
`test_revision_state_tracks_plan_inputs_without_resolving_concerns` in
`tests/test_judge_contract.py` pin helper behavior. Both-shell routing is covered by
`test_owned_stop_correction_routes_to_focused_recheck` in
`tests/test_next_context_resolution_contract.py`. These scripted checks do not establish model
compliance with the Plan/Tasks editing instructions; that requires a prompt-driven execution proof.

Plan and Tasks each record the fingerprint of the upstream content they read: the Plan's
`spec_semantic_hash` (excluded from the Plan's own semantic projection, so restamping never
stales Planning Review evidence) and Tasks' `plan_semantic_hash`. `review-state` reports
`plan_spec_state` and `tasks_plan_state` as `current`, `stale` or `unknown` with or without a
Judge artifact; a missing, malformed or unprojectable stamp is `unknown`, and `unknown` never
routes. Both shells route only `stale`: `plan-stale-against-spec` recommends Plan and
`tasks-stale-against-plan` recommends Tasks, and a pending decision, `STOP` or review invalidation
keeps precedence, so a spec change after Planning Review goes to review first.

Before Judge the Plan is a draft, and re-running Plan reconciles it with the current spec under
its initial-generation authority, reporting NO CONTENT CHANGE, BOUNDED CORRECTION or SUBSTANTIVE
REVISION in run output only. After Judge, revise stays Judge-driven: Plan only restamps when no
content change is required, applies Judge-owned `plan_revisions`, or revises under explicit human
authority during the run, and only while review evidence is current for the spec it read. Tasks
reports NO CONTENT CHANGE and restamps alone when its projection is still coherent. Accepted
limitation: `plan_semantic_hash` covers only `plan.md`, so a change confined to Plan support
artifacts is not detected by `tasks_plan_state`. `test_edge_state_truth_table`,
`test_a_plan_restamp_changes_no_review_comparison_or_edge_state` and
`test_next_routes_only_on_a_stale_edge_and_identically_in_both_shells` in
`tests/test_planning_edge_freshness_contract.py` pin the helper and both-shell routing.

## Acceptance planning and ownership

When independent acceptance validation is warranted, **plan** creates one conditional, ephemeral `qa-acceptance.md` in the spec bundle; **tasks** derives only pre-PR Tests work from it; **implement** applies the planned durable Tests delta (add, update or retire; a durable manual-regression reference where planned); **analyze** checks scenario trace validity, scope and uncovered external success criteria; **critic** challenges scenario quality and proportionality; **pr-review** verifies planned `update`/`retire` proportionately without running QA. No new command, stage or gate is involved.

Ownership split: the spec owns defining and preparing acceptance; QA operations own post-deployment execution. Post-deployment QA is not required to complete, close out or make the spec archive-ready. A post-deployment failure creates new work and does not reopen the spec.

## Implementation — applies the delta

| Command | Current behavior |
|---|---|
| **implement** | Carries the heaviest discipline in the lifecycle: (1) consumes `context_resolved` as already-resolved context — takes at most **one additional hop** itself, and an escalation past that hop is logged and attributable, not silent; (2) updates code and knowledge together in one pass, preferring test evidence over code-only evidence, recording `test_attempted`/`fallback_reason` when it falls back; (3) records the test run as evidence for later reuse; (4) never writes a spec, task, or plan identifier into code, tests, or `.knowledge/` (rule 1/5); (5) never archives anything — the spec or quickfix record stays live in `.devspark.work/`, so it remains validate-able against code, tests, and knowledge for as long as the sprint needs it. `/devspark-release` is the sole command that later archives it. On a `NNN-work-*` branch it runs at most one assurance capability on demand for a stated concern, applies the disposition, and continues. An unchecked `## Required Obligations` entry in `work.md` blocks completion and delivery, and the developer cannot waive it. |

## Validation — carries assimilation forward, enforces the permanent record

| Command | Current behavior |
|---|---|
| **pr-review** | The primary assimilation trigger — nothing merges without it. §6 tracks durable-delta consistency as ID-tracked blocking findings (`PRD1` code/knowledge contradiction, `PRD2` unsupported knowledge claim, `PRD3` insufficient test depth, `PRD4` planning-identifier leak — rule 1 enforced here, `PRD5` knowledge completeness for architecturally significant behavior). §6c runs `build_knowledge_index.py` against the diff's touched entities, gates on gap-report failures (blocking, same tier as a constitution violation), and surfaces two non-blocking warnings: a code-only evidence entry missing `fallback_reason`, and contradiction candidates scoped to graph-adjacent objects (same entity, entities sharing a `constrains` decision, objects citing the same `source_of_truth`) — never brute-force pairwise comparison. §6d consumes the route's closeout decision rather than restarting discovery: an unclassified finding, an unresolved blocking defect, a laundered requirement/invariant, or counts that contradict the findings list are `PRD6` (blocking); a documented accepted limitation, deferred item, or learning is converged and must not be reopened. A genuine new defect still reopens the work; the mere availability of a better approach never does. A missing closeout artifact is a note, not a finding. PR-specific state is authoritative in the existing review file; the review-state engine derives report views, and UPDATE evaluates the original concern and correction in one bounded pass before writing the outcome. This is local recommendation state, not hosted approval. |
| **address-pr-review** | Commit isolation between fixes and review-file updates, unchanged in mechanism. Explicitly enforces rule 1 on its own fixes: a fix that patches code must not introduce a spec/task/plan/PR-thread reference to "explain" what review comment it addresses — that context belongs in the commit message or the review file. Its helper derives eligibility per finding from status, severity and blocking evidence (ids `C`, `H`, `M`, `L`, `CON` and `PRD{N}`): `--auto` selects only open critical/high or blocking PR-delta findings with no accepted, deferred or withdrawn disposition, reports ordinary Medium/Low and non-blocking PRD findings, and routes `CON` findings to `evolve-constitution`. A single already-authorized finding is selected deterministically; pending reviewer verification remains blocking and is never author-auto-eligible. Remediation beyond the approved Plan's shape stops for explicit authority. |
| **create-pr / update-pr** | Both surface evidence and linkage status directly in the PR description/delta: whether each touched `.knowledge/` node cites a test-verified (`verified_by: execution`) or code-only claim, and flag a code-only entry with no `fallback_reason` as a reviewer note (non-blocking) — the same signal `pr-review` §6c checks mechanically, visible here without digging. |
| **verify** | The evidence mechanism's engine, installed as a skill. Runs in two phases in one invocation. **Evidence phase**: runs the declared proof mode(s) from `spec.md`'s `required_gates`, writes `gates/verify.md`, and records a `test_ref` pointer for any mode that passed via a named, committed test — the citable evidence `implement` needs to record `verified_by: execution` on a knowledge object or decision. Observations surfaced during the run that are not proof results go to a `discovered:` list and never change a mode's status. **Closeout phase**: classifies every open finding against `templates/closeout-contract.md`, evaluates each acceptance criterion by its declared kind, and writes the completion decision to `gates/closeout.md` with `produced_by: verify`. It never tells the developer to go run a closeout command — the decision was just made. A route with no declared proof mode skips the evidence phase and still converges. |
| **closeout** | **Optional / advanced — not on the normal path.** Re-runs verify's closeout phase alone, against the identical contract, producing the identical artifact with `produced_by: closeout`. Exists for reassessment: work continued after verify ran, a limitation was accepted later, a human wants to re-decide completion without paying for re-verification, or an experimental result needs a fresh decision. Explicitly accounts for the evidence it did **not** refresh — stale evidence is reported as stale and routes back to `/devspark-verify` rather than producing a `complete` decision about a previous version of the work. No command recommends it as a routine next step. |
| **site-audit** | The one repo-wide, non-diff-scoped audit command — there is no separate `audit` command. Resolves `execution`-type evidence entries by re-running their cited tests (a separate accuracy pass from the existence-only coverage matrix), and runs the same graph-adjacent contradiction scan as `pr-review` §6c (same entity, same `constrains` decision, same `source_of_truth`) repo-wide instead of diff-scoped. Contradiction findings are always non-blocking warnings for human review. |
| **explain** | Topic-scoped, read-only by default: grounds its answer and DELTA/KNOW findings in current code and tests. Discovery does not create work. Only a developer-requested Knowledge correction or draft may be written, after its own explicit approval, followed by a Knowledge build check and focused re-verification. Saving a trace requires a separate approval; neither action is bundled with the other. Confirmed code defects route to Quickfix, genuinely missing behavior to Specify. Explain never implements code or creates a planning record. |
| **release** | Is the **sole** command that ever moves anything from `.devspark.work/` into `.archive/{YYYY-MM-DD}/`: it sweeps `.devspark.work/specs/` and `.devspark.work/quickfixes/` for bundles that are `Complete` and archives them, unconditionally moves every other categorized `.devspark.work/` artifact (`pr-review/`, `audit/`, `metrics/`, `telemetry/`) into the same release archive folder — no age, count, or eligibility check for these, unlike specs/quickfixes — flags (but never auto-archives) orphaned in-flight state whose branch is stale/merged/deleted but never reached `Complete`, runs a lighter non-blocking backstop check of `.knowledge/` for obsolete/duplicate/historical content and decision docs whose `constrains`/`constrained_by` pointers have drifted, and is a second, window-wide checkpoint for the same guarantee `pr-review` checks per-diff (the Knowledge builds, a current `site-audit` knowledge-scope result with no open `KNOW1`–`KNOW6` findings for the window). |
| **taskstoissues** | Already fully aligned without any change needed — its entire purpose is explaining why ephemeral tasks don't get exported as durable records, which is rule 1 stated as a user-facing explanation rather than an enforcement mechanism. |

## Script-first merge and PR review helpers

**merge-from-main** delegates fetch, merge and status to its PowerShell/Bash twins. A dirty tree
blocks the merge; on `main` synchronization is fast-forward-only. On another branch, conflicts are
reported with marker ranges and the agent edits only those hunks. Continue verifies markers are
gone before staging and committing; abort cancels the merge. Push is opt-in, never implied by a
successful local merge. `tests/test_merge_from_main_contract.py` covers the script and command
boundaries offline.

**pr-risk.py** computes per-file review tiers, delta classes, an auditable `risk_score` and rating,
and `report_form` (`short`, `standard`, `full`) from the full changed-file set before the context
scripts sample it. Existing Knowledge ownership can promote domain or integration files to P0;
`unmapped_production` is a completeness lead, not proof of a defect. Tiers and rating are floors:
the reviewer may escalate, never lower them. Rendered changed-file and test tables are consumed
by PR Review rather than reconstructed. The risk and Knowledge contracts are covered by
`tests/test_pr_risk_contract.py` and `tests/test_pr_risk_knowledge_contract.py`.

**pr-review-validate.py** checks only deterministic report consistency: metadata versus body,
recommendation versus open blockers, and risk floors; with a Git range it also checks the digest,
report form and tables. It does not establish semantic correctness or reviewer quality.
`tests/test_pr_review_validate_contract.py` covers these boundaries. **pr-risk-calibrate.py** pairs
predictions with recorded finding severity, grouped by producer version, and reports recall and
over-rating. Its optional minimum-recall threshold can fail the run; recorded outcomes are not
proof of review quality. `tests/test_pr_risk_calibrate_contract.py` covers the calculation.

## Governance & framework — Constitution, framework lifecycle

| Command | Current behavior |
|---|---|
| **constitution** | Already explicit that the Constitution is one of three current-truth categories alongside `.knowledge/` entities and `.knowledge/governance/decisions/` — not "documentation." "Dependent templates staying in sync" includes the decisions contract, and its own step 4 scans `.knowledge/governance/decisions/*.md` for `constrains` entries or prose that assumes the prior rule set. |
| **discover-constitution** | Unchanged in mechanism — discovering implicit patterns is a different activity than maintaining the current-truth categories, and needs no revision. |
| **evolve-constitution** | Already connects amendments to the decision-editing discipline: applying an approved amendment includes checking `.knowledge/governance/decisions/*.md` for a decision that contradicts it (a rationale, rejected alternative, or `constrains` entry that no longer holds), and correcting that decision in place — never a second, competing decision file for the same topic. |
| **release** | A second, window-wide checkpoint for the same guarantee `pr-review` checks per-diff: confirms the Knowledge builds, confirms a current `site-audit` knowledge-scope result with no open `KNOW1`–`KNOW6` findings for the release window, and is the sole command that archives every `Complete` spec or quickfix from `.devspark.work/` into `.archive/{YYYY-MM-DD}/` — see the Validation section above for its full scope. |
| **commit-audit / repo-story** | Read Git history, not the repo's current-truth layer — naturally exempt from current-truth-only, since Git is explicitly *where* history is supposed to live under this model. |
| **upgrade** | Framework-version concern, orthogonal to the knowledge model. No change. |

## App/framework operations — unaffected

**add-application, list-applications, migrate-registry, validate-registry,
personalize, next** — these manage the multi-app registry and framework
mechanics, not the knowledge/spec lifecycle. `next` is aware of the gate
order (plan → tasks → planning review → implement, with `context_resolved`
part of what analyze and critic check) when deciding what the next command
is.

## External work tracking — optional, outside the repository

| Command | Current behavior |
| --- | --- |
| **workitem-review** | Reads one explicitly named work item, grades it against the calibrated standard in `templates/workitem-standard.md`, and proposes improvements for confirmation. Never writes without confirmation, and proves it left the item alone by re-reading and comparing rather than by asserting it. Retrieved text arrives inside an untrusted-data envelope, so instructions embedded in a work item are treated as reported content, never as directives. |
| **workitem-create** | Drafts exactly one work item per invocation from either a spec or the conversation, states which, and creates it only after explicit confirmation. It never creates a `User Story`, no other command invokes it, and no lifecycle command creates a work item as a side effect. Acceptance criteria go to the dedicated field, never appended to the description, and every created item carries the `devspark-generated` marker tag. The created identifier is recorded only in the feature's temporary record under `.devspark.work/specs/` — durable code and `.knowledge/` never name a work item, since a board can be renumbered or reorganised at any time. |

Both are opt-in: with no `work_tracking` block configured, they report that and stop, and no other
command mentions work items at all. `specify` may offer a pre-artifact review when tracking is
configured **and** the developer named an item explicitly; `create-pr` and `update-pr` verify the
references they carry through a read-only path and never mutate the board as a side effect of
opening or updating a pull request.

## Shim gaps

Every command in this inventory has exactly one source-repository skill,
`.github/skills/devspark-<command>/SKILL.md`, invoked as `/devspark-<command>` — one-to-one, no gaps.
There are no agent shims, prompt shims, or atomic prompt shims.

`generate-atomic-shims.(sh|ps1)` writes each skill from the template's description plus either a
direct route to `templates/commands/<command>.md` or, for the five source-only commands, the stop
body kept in `eng/skills/source-stop/<command>.md`. It marks the skill explicit-invocation only, and
its `--check` gate fails on any hand edit, missing skill, or orphan. A skill never holds command
instructions.

These source-repository skills are an exception to the three-tier command override chain: they read
`templates/commands/<command>.md` directly, so this repository always runs its current source, and
five commands that only make sense in a consumer repository (`add-application`, `list-applications`,
`discover-constitution`, `personalize`, `upgrade`) stop with an explanation. They consult neither
`.devspark.work/commands/` nor `.devspark.work/{git-user}/commands/`, and the host's own
skill-discovery precedence is not a substitute for that chain. Consumer-repository skills are
generated into `templates/consumer-skills/` and keep the three-tier resolution.

## Developer-experience classification

A command existing is not the same as a developer needing to know it exists.
The table below distinguishes the new-work happy path from capabilities retained for existing
bundles. A core-path entry is guidance, not a new constitutional obligation.

| Class | Meaning |
|---|---|
| **CORE HAPPY-PATH** | On the normal route for ordinary work. A developer is expected to know it. |
| **OPTIONAL ADVANCED** | Real user entry point, reached deliberately for a specific situation. Nothing routine requires it. |
| **INTERNAL CAPABILITY** | A lifecycle phase or mechanism another command invokes. Exposed as a command only for recovery or inspection. |
| **DIAGNOSTIC / MAINTENANCE** | Operates on the repository, framework, or history rather than on the active change. |

| Command | Current role | Required on the normal path? | UX classification |
|---|---|---|---|
| **next** | Detects lifecycle state and dispatches the single next step | No — but it makes every other row optional to memorize | CORE HAPPY-PATH (the zero-knowledge entry point) |
| **specify** | Understands new work and starts a bundle-free `work` branch | Yes, for new work | CORE HAPPY-PATH |
| **plan** | Design artifacts + bounded `.knowledge/` traversal | Existing v9.3 bundles; otherwise on request | OPTIONAL ADVANCED |
| **implement** | Starts or resumes work; also executes legacy bundles | Yes | CORE HAPPY-PATH |
| **verify** | Evidence phase + closeout phase, one invocation | Yes, where a proof mode is declared | CORE HAPPY-PATH |
| **create-pr** | Opens the PR and surfaces evidence/linkage status | Yes | CORE HAPPY-PATH |
| **pr-review** | Primary assimilation trigger; nothing merges without it | Yes | CORE HAPPY-PATH |
| **quickfix** | Legacy contained-change entry and active-record continuation | No new-work route choice; direct use remains supported | OPTIONAL ADVANCED (legacy compatibility) |
| **tasks** | Dependency-ordered task list | Existing v9.3 bundles or coordination that needs it | OPTIONAL ADVANCED |
| **clarify** | Targeted questions encoded back into the spec | No | OPTIONAL ADVANCED |
| **analyze** | Closed-world planning assurance: are the artifacts internally sound? | No — `planning-review` runs it for bundles; on demand for a stated concern on work branches | OPTIONAL ADVANCED (expert drill-down) |
| **critic** | Open-world planning assurance: is the sound plan wrong about the real system? | No — `planning-review` runs it for bundles when applicable; on demand for a stated concern on work branches | OPTIONAL ADVANCED (expert drill-down) |
| **planning-review** | Analyze + conditional Critic + Judge → one planning decision; on work branches, Judge alone on demand | Existing required v9.3 gates or a specific concern | OPTIONAL ADVANCED / LEGACY GATE |
| **checklist** | Custom checklist for a feature | No | OPTIONAL ADVANCED |
| **closeout** | Re-runs verify's closeout phase alone | **No — verify already does it** | INTERNAL CAPABILITY (advanced recovery entry point) |
| **address-pr-review** | Works open review findings with commit isolation | Only when a review has open findings | OPTIONAL ADVANCED |
| **update-pr** | Refreshes an existing PR description | No | OPTIONAL ADVANCED |
| **explain** | Topic-scoped knowledge drift detection + remediation | No | OPTIONAL ADVANCED |
| **release** | Seals a release; sole archiver of `.devspark.work/` | At release boundaries, not per change | OPTIONAL ADVANCED |
| **constitution** | Creates or amends the constitution | Once per repository | OPTIONAL ADVANCED |
| **evolve-constitution** | Proposes amendments from observed patterns | No | OPTIONAL ADVANCED |
| **discover-constitution** | Infers implicit conventions from an existing codebase | Onboarding only | DIAGNOSTIC / MAINTENANCE |
| **discover-knowledge** | Evidence-based `.knowledge/` maintenance proposals | No | DIAGNOSTIC / MAINTENANCE |
| **context-projection** | Direct inspection of `.knowledge/` traversal | No — `plan` performs projection itself | INTERNAL CAPABILITY (debugging entry point) |
| **site-audit** | Repo-wide compliance and drift audit | No | DIAGNOSTIC / MAINTENANCE |
| **commit-audit** | Commit-history metrics | No | DIAGNOSTIC / MAINTENANCE |
| **repo-story** | Narrative from full repository history | No | DIAGNOSTIC / MAINTENANCE |
| **upgrade** | Framework version check and safe upgrade | At framework boundaries | DIAGNOSTIC / MAINTENANCE |
| **personalize** | Creates a per-user prompt override | No | DIAGNOSTIC / MAINTENANCE |
| **add-application** / **list-applications** / **validate-registry** / **migrate-registry** | Multi-app registry management | Multi-app repos only | DIAGNOSTIC / MAINTENANCE |
| **migrate-knowledge-entities** | One-time move to the entity layout | No | DIAGNOSTIC / MAINTENANCE |
| **workitem-create** / **workitem-review** | External work-tracking integration | Opt-in; inert without `work_tracking` | OPTIONAL ADVANCED |
| **taskstoissues** | Explains why temporary tasks aren't exported | No — it performs no writes | DIAGNOSTIC / MAINTENANCE |

The convergence work added one internal lifecycle phase and **zero** commands
to the happy path: verify absorbed closeout rather than handing it to the
developer as a sixth step. `/devspark-closeout` is listed above as an
internal capability with an entry point precisely because exposing it does
not make it required.
