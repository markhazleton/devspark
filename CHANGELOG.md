# Changelog

<!-- DevSpark — © 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com -->

<!-- markdownlint-disable MD024 -->

All notable changes to DevSpark are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Optional roadmap planning.** `/devspark-roadmap` records product direction and right-sized Prospective Specs without adding a delivery stage or gate. Its structural checker validates, locates, and safely repairs roadmap records; `/devspark-specify` reads a Prospective Spec only when named, and `/devspark-release` can archive resolved items with explicit approval.

## [9.4.1] - 2026-11-01

**An upgraded install now matches a fresh one.** The quickstart's Update and Repair modes remove framework files that the release manifest no longer lists, and the Bash steps work on Windows with a native `jq`. No action is needed beyond running Update Mode.

### Changed

- **`.devspark/` now matches the manifest exactly after an upgrade.** Quickstart Step 9.5 (Update and Repair) adds a second pass: after pruning root entries not in `manifest.devspark_root`, it deletes every file under `.devspark/defaults/`, `.devspark/templates/` and `.devspark/scripts/` whose path is not a `dest` in `manifest.install`, then removes empty directories. Files a release dropped or renamed, such as `create-new-feature` and `validate-knowledge-coverage`, no longer linger in upgraded repositories. The pass runs only after Step 4 verified every `dest`, and never against an absent or empty `install` array. `.devspark.work/`, `.knowledge/` and `.archive/` are never touched, so customizations are unaffected.

### Fixed

- **Bash quickstart steps on Windows with a native `jq`.** A Windows build of `jq` ends lines with CRLF, and the Bash steps that read its output line by line kept the trailing carriage return. Step 9.5 then failed to match `defaults`, `templates` and `scripts` against `manifest.devspark_root` and deleted all three, the Step 4 install loop wrote each file under a name ending in a carriage return, and Step 4 validation reported every file missing. Those pipelines now strip carriage returns. The PowerShell steps were not affected.

## [9.4.0] - 2026-10-31

**One Flow. Assurance as Needed. Deliver Software.** DevSpark 9.4 replaces the choice between a quickfix, a quick spec and a full spec with one path: understand, implement and verify, deliver. Start new work with `/devspark-specify` and resume it with `/devspark-next`; neither asks for a route or writes a planning bundle. A plan, a task list, Analyze, Critic or Judge runs only when a specific uncertainty, material risk or mandatory obligation justifies it, and none of them adds a gate or triggers another. Delivery readiness is decided by evidence: `/devspark-verify` reports what was proven, and `/devspark-next` and `/devspark-create-pr` refuse delivery while a declared required obligation lacks its authority and an evidence reference. Code, tests and current Knowledge remain the durable outcomes; an optional `work.md` carries context across sessions only when it would otherwise be lost.

Existing v9.3 full-spec bundles, quick-spec bundles and quickfix records continue unchanged, and no migration is needed. See [Upgrading to 9.4](site/src/get-started/upgrade.md#upgrading-to-94).

**Changes that can affect custom automation**:

- `scripts/{powershell,bash}/create-new-feature.*` are removed, and `new-branch` accepts only `--type work` and `--type fix`.
- `create-pr.ps1` create and update mode now exit `1` on a refusal or failure, matching `create-pr.sh`.
- `create-pr` create and update mode refuse an unresolved required obligation, and refuse when the lifecycle check cannot run while obligations are declared.
- A checked required obligation now needs an evidence reference.

**Known limitations**:

- A recorded evidence reference proves that a reference exists, not that the approval behind it is authentic. Policy kept only outside the repository is not mechanically enforced.
- `next-context` does not read `DEVSPARK_PLATFORM`; it detects the platform from the remote.
- `/devspark-implement` and `/devspark-explain` name some helper scripts by their source path (`scripts/…`); an installed repository has them under `.devspark/scripts/`, so run them from there.
- Older releases' packages are not hosted after a newer release deploys; the quickstart always installs the latest release.

### Added

- **Universal start and resume path**: `/devspark-specify` starts `NNN-work-*` branches without a specification or workflow-size choice; `/devspark-implement` resumes those branches from repository evidence and an optional minimal `work.md` when continuity needs it. Existing v9.3 spec and quickfix routes remain supported.
  - The start keeps the existing safeguards: work-item grounding (offered only when tracking is configured and the developer names an item, with tracker text kept in its untrusted-data envelope and scope left to the developer), verification expectations (snapshot-neutral refactors, golden and end-to-end proof for prompt changes, §2.1 verify-sensitive shapes), and branch-safety confirmation. After that confirmation the declared script runs non-interactively with `--yes`/`-Yes`; numbering collision checks still apply.
  - `/devspark-next` reads the `work.md` status case-insensitively in both shells (new `WORK_COMPLETE` field), routes a finished note with uncommitted changes to commit, and, for a committed work branch with no finished note, recommends `/devspark-create-pr` only with an explicit reminder that Git state is not proof of completion; `--auto` stops there for confirmation.
- **Optional planning on work branches**: `/devspark-plan` runs on `NNN-work-*` branches without a specification. `setup-plan` (both shells) reports `WORK_BRANCH` and `WORK_NOTE`, returns an empty `FEATURE_SPEC`, and neither copies the full-spec plan template nor refreshes the spec knowledge document there. The agent writes a concise advisory `plan.md` only when the developer asks or a material uncertainty justifies one. `check-prerequisites` lists that plan in `AVAILABLE_DOCS`, and `/devspark-implement` follows it when present but never requires it. A plan adds no tasks, gates, Analyze, Critic, Judge or Planning Review, and the branch stays on the work route in `/devspark-next`.
- **Optional task coordination on work branches**: `/devspark-tasks` runs on `NNN-work-*` branches without a specification or plan; `check-prerequisites --require-plan` (both shells) no longer blocks there. Simple work needs no decomposition. Otherwise the agent identifies a few dependency-ordered deliverables, tracks them with its built-in task tracking, and records them as `## Remaining Deliverables` in the optional `work.md` only when cross-session continuity, substantial dependencies or multi-developer coordination justify it. No work-branch `tasks.md` is written, and open deliverables are not a completion gate. `/devspark-implement` follows that list when present and never requires it.
- The `/devspark-plan` and `/devspark-tasks` handoffs no longer auto-send to Tasks, Checklist, Analyze or Planning Review. Both offer a single "Recommend Next Step" handoff to `/devspark-next`, which still routes legacy bundles from plan to tasks to Planning Review.
- **Assurance on demand on work branches** (assurance contract §13): `/devspark-analyze`, `/devspark-critic`, and Judge through `/devspark-planning-review` each run independently on a `NNN-work-*` branch for one stated concern, with no specification, task list or gate file. Each reports a compact Concern / Capability / Evidence / Outcome / Disposition result and returns to `/devspark-implement`, which applies the disposition (continue, pause affected work, or decision needed). One capability never chains another.
  - `judge.py resolve` reports `work-branch` (exit 0, no run id) instead of an error there.
  - An accepted decision that must survive the session goes under `## Material Decisions` in the optional `work.md`, with its basis and commit. It is reconsidered only when that basis changes.
  - An applicable mandatory control goes under `## Required Obligations`, naming its authority. `judge.py lifecycle` fails with `required-obligation-unresolved` while one stays unchecked, so `/devspark-implement` finalization and `/devspark-create-pr` block delivery. Policy that exists only outside the repository is not mechanically enforced.
  - `/devspark-critic` handoffs are no longer auto-sent, and it offers "Return to Implementation".
- **Evidence-based delivery readiness in `/devspark-next`**: on a `NNN-work-*` branch both `next-context` shells run `judge.py lifecycle` and report `LIFECYCLE_STATUS` and `LIFECYCLE_BLOCKERS`. Committed work that fails the check routes to the new `delivery-blocked` state instead of `ready-for-pr`. An unresolved required obligation recommends `resolve-obligation`, naming the obligation and its authority, and `--auto` stops there. Other lifecycle failures return to `/devspark-implement`. Work still in progress or uncommitted keeps its route with a note that delivery stays blocked. The `required-obligation-unresolved` failure now names each obligation's authority and lists them in an `obligations` field. Spec and quickfix bundles route as before.
- **Delivery readiness in `/devspark-create-pr`, `/devspark-verify` and `/devspark-closeout`**: the `create-pr` preflight (both shells) reports the same `judge.py lifecycle` check as `lifecycle` (`pass`, `fail`, `unavailable` or `not-applicable`), so the prompt reads it instead of running Judge separately.
  - Create and update mode now refuse an unresolved required obligation with `CREATE PR BLOCKED — REQUIRED OBLIGATION UNRESOLVED`, naming the committed HEAD and each obligation's authority. It clears only when the `work.md` entry is checked with a reference to the evidence or the authority's decision. Previously the prompt let the agent proceed and record the decision in the PR. Other lifecycle failures do not refuse.
  - A lifecycle check that cannot run is reported as `unavailable` with a `reason` (`judge-missing`, `python-unavailable`, `invalid-output`) and `obligations_declared`, and is never treated as a pass. When `work.md` declares `## Required Obligations`, create and update mode refuse with `CREATE PR BLOCKED — LIFECYCLE CHECK UNAVAILABLE` and the recovery step for that reason. DevSpark has no override; an approval path that organizational policy authorizes is followed outside DevSpark. Without declared obligations the check is reported as unconfirmed and does not refuse. `/devspark-next` says the same in its `REASON`.
  - On a `NNN-work-*` branch `/devspark-verify` chooses proof in proportion to risk, reports what was observed, assumed and unobtainable, and answers delivered, verified and eligible. It writes no `gates/verify.md` or `gates/closeout.md`. `/devspark-closeout` reassesses the same questions without a document. Post-deploy requirements stay visible as deferred and never block merge. Verify keeps them stated in `work.md`, and `/devspark-create-pr` lists them under deployment status, as it already did for a full-spec closeout's deferred items.
  - `/devspark-implement` offers an optional "Run Verification" handoff. `/devspark-create-pr` no longer recommends Analyze or Critic just because gate artifacts are absent.

### Changed

- DevSpark no longer creates a **new** full-spec or quick-spec bundle; new work starts on the universal route. Existing full-spec and quick-spec bundles continue unchanged through `/devspark-next` and `/devspark-implement`.
- The public site, quickstart, and home-page explorer now describe one flow (understand, implement and verify, deliver) instead of a Quickfix, Quick spec, or Full spec route choice. The Skill Catalog groups skills as the normal path, optional when justified, and existing v9.3 specifications. Troubleshooting no longer asks you to size a fix, and its `/devspark-next` diagram shows the work-branch states with v9.3 bundles as a separate branch.
- The `plan`, `analyze`, `critic`, `planning-review`, `clarify`, `checklist`, and `quickfix` descriptions now say when each applies: optional, on demand for one concern, or for an existing specification.
- Handoffs that pointed at a specification route now start or continue the work: `/devspark-constitution`, `/devspark-workitem-create`, and `/devspark-workitem-review` offer `/devspark-specify` to start work rather than a full specification; `/devspark-explain` offers one "Start Work on a Gap or Defect" handoff to `/devspark-specify` instead of separate specify and `/devspark-quickfix` handoffs; `/devspark-next` no longer names `/devspark-quickfix` as a dispatch target, which its script never recommends; `/devspark-clarify` offers a return to implementation; `/devspark-checklist` no longer chains into `/devspark-analyze`; and `/devspark-critic` sends spec showstoppers to `/devspark-clarify` because `/devspark-specify` cannot revise an existing spec.
- **A checked required obligation now needs an evidence reference.** `judge.py lifecycle` fails a `## Required Obligations` entry in `work.md` with `required-obligation-unresolved` while it is unchecked, or checked without its `Authority:` or a traceable reference to the satisfying evidence or authorized decision: a repository path, commit, review or approval id, or link, either labelled (`Evidence:`, `Approval:`, `Decision:` and similar) or as its own `—` segment, on the entry or an indented line under it. Prose and `<placeholder>` text do not count. Each listed obligation now carries a `missing` field, and the message says what is missing. `/devspark-next`, `/devspark-verify`, `/devspark-closeout` and `/devspark-create-pr` receive the same result because they all read this check. It confirms that a reference is recorded, not that the approval behind it is authentic. Spec bundles, tasks and planning checklists are unaffected.

### Fixed

- On a work branch, `/devspark-clarify` no longer treats `work.md` as a spec (the prerequisite check resolves `FEATURE_SPEC` to it) and `/devspark-checklist` no longer writes `gates/checklist.md`. Both answer the concern in conversation and return to implementation.
- The `/devspark-pr-review` "Address Current Findings" handoff now opens `/devspark-address-pr-review`; it re-ran the review instead.
- `/devspark-next` and `/devspark-create-pr` messages now name `/devspark-next` and `/devspark-create-pr` rather than the retired 8.x dotted form, and the config and registry schema descriptions use the hyphenated names.
- `create-pr.ps1` create and update mode now exit `1` when they refuse or fail (`error: true`), matching `create-pr.sh`, and exit `0` only on `status: ok`. Previously every PowerShell refusal, including the knowledge and obligation blocks, exited `0`. The JSON output is unchanged; a PowerShell caller that treated exit `0` as "the script ran" must now read the JSON on a non-zero exit too.
- The Gemini and Qwen packages now escape quotes and backslashes in a command's TOML `description`. `devspark-explain.toml` was invalid TOML (its description contains quotes), so those agents could not load `/devspark-explain`. Both packagers are fixed.
- `next-context.ps1` no longer reads a quickfix record's blank `- **Completed**:` field as complete. Its pattern crossed into the next line, so in PowerShell every newly created quickfix routed to `/devspark-create-pr` instead of `/devspark-implement`. It now reads the field on its own line, as `next-context.sh` already did.
- `next-context.ps1` and `create-pr.ps1 -Mode Preflight` now exit `0` explicitly. Run in-process, as agent terminals do, they left the nested lifecycle check's exit status in `$LASTEXITCODE`, so a failing lifecycle check made a successful run look like a script failure.
- Agent-observed gaps in the work-route prompts are closed:
  - `/devspark-verify` routes an unresolved obligation to its authority's evidence, not to more implementation, and names the installed `judge` wrapper.
  - `/devspark-implement` runs **Finalize Every Route** after completing work-route work, names the files the developer needs to commit, and no longer asks a work branch to record traceability in a planning record it does not have.
  - `/devspark-specify` says how to get the proposed branch name before confirmation (a dry run).
  - `/devspark-next` lists `uncommitted-changes` and drops the retired `one-off-fix` choice.
  - The verification contract no longer cites a route classification that `/devspark-specify` no longer performs.
- The `/devspark-closeout` "Fix Blocking Defects" handoff now says to re-run verification after the fix, not closeout, which no command may recommend as a routine step.
- `judge.py lifecycle` now reports a required obligation's text in full, up to 200 characters, rather than cutting it at 60 characters mid-word. That text appears in the `/devspark-next` and `/devspark-create-pr` refusals.
- `/devspark-quickfix` no longer offers an "Upgrade to Full Spec" handoff to `/devspark-specify`, which can no longer create a full-spec bundle. A material scope signal now adds only the assurance its concern needs to the same quickfix (a "Review a Material Concern" handoff to `/devspark-critic`, not auto-sent), and the developer decides whether genuinely separate work starts with `/devspark-specify`.
- `judge.py lifecycle` no longer fails a universal work directory (no `spec.md`) with `incomplete-tasks` because of an unchecked `tasks.md`; on that route a task list is coordination. Spec bundles still enforce required tasks, and every other lifecycle check is unchanged.
- A file named `spec.md` in a `NNN-work-*` directory no longer turns the work into a legacy full-spec. Before, `/devspark-next` (both shells) routed it through the spec ladder and could recommend Tasks or Planning Review, and `judge.py lifecycle` read `required_gates` from that file and treated a `tasks.md` there as a completion gate. `judge.py resolve` also issued a review run id. The branch name now decides: `next-context`, `judge.py lifecycle` and `judge.py resolve` treat every `NNN-work-*` directory as universal work, and `/devspark-implement` checks the branch before reading `spec.md`, and `/devspark-critic` no longer reads its frontmatter there. Legacy branches are unaffected.

- `/devspark-analyze` no longer passes `--require-tasks`, which made its documented `QUICKFIX-ONLY`, `SPEC-ONLY` and `SPEC+PLAN` tiers unreachable. It now degrades as its own tier table describes.
- `pr-review-validate.py` no longer rejects `request-changes` with `rec-without-blocker` when the shared review-state engine derived it from an unmet required condition. A recommendation with neither an open blocker nor an unmet required condition is still rejected, and disposition rules are unchanged.
- `/devspark-verify` and `/devspark-closeout` now read the prior `gates/closeout.md` before replacing it and carry forward its decisions (including a human `accepted_by`) within their original scope. An optional Verify that supplies no new evidence leaves a still-applicable closeout untouched instead of rewriting it as `not-complete`. A materially changed input, changed work, invalidated evidence, a real defect, or an unmet mandatory obligation still reassesses the affected items (closeout contract §7.1). `evaluated_commit` is a new optional closeout field; older artifacts and pre-contract specs are read as written and are never reclassified or waived.

### Removed

- `scripts/{powershell,bash}/create-new-feature.*`. No command has called them since `/devspark-specify` moved to `new-branch --type work`. A team override that still calls them should be rebuilt on the current stock `/devspark-specify`.
- `new-branch` types `spec` and `quick`. New work never scaffolds a full-spec or quick-spec bundle, so `new-branch` accepts `work` and `fix` only and exits `1` with `type must be one of: fix, work` otherwise. Existing `NNN-spec-*` and `NNN-quick-*` branches still resolve and are still counted by the allocator.

## [9.3.0] - 2026-10-17

### Added

- **Closest-existing-pattern discovery**: Planning looks for the nearest existing implementation before proposing anything new, and `plan.md` records `Closest existing pattern` and `New mechanism`. Tasks derive from the change surface rather than fixed phases. Critic raises a finding when a closer existing implementation than the planned new mechanism exists, and Planning Review adjudicates reuse first.
- **Test evidence record**: `gates/test-evidence.md` records `commit`, `tree`, `command`, `result`, `run_at` and `run_by` for a test run (verification contract §4.1), with reuse and invalidation rules. Repository risk policy and independent-verification requirements always take precedence.

### Changed

- **Evidence-first PR review**: `/devspark-pr-review` inspects recorded evidence before deciding to run tests, reuses valid evidence for the current commit and environment, escalates to execution on stated triggers, and reports a `Test Evidence` section. Implement and Verify record their runs to the evidence file.
- **Knowledge checks are build validation**: `build_knowledge_index.py --check` confirms the Knowledge builds and no longer compares `index.json` / `coverage.json`; `--fail-on-stale` remains an opt-in. `/devspark-create-pr` readiness is `ready`, `not-applicable`, `unknown` or `blocked` (a build error), returned as `{gap_summary, readiness, blockers, checked_head, check_output}`. `/devspark-release` context reports `KNOWLEDGE_BUILDS` in place of `KNOWLEDGE_INDEX_PRESENT` / `KNOWLEDGE_INDEX_CURRENT`.
- **Content over dates**: `/devspark-explain` and `/devspark-site-audit` judge Knowledge against the code. A `last_verified` date is never a finding by itself, and `last_verified` is optional on entity-layer documents (an ISO date when present). Constitution Principle X and the Knowledge Framework Contract now treat derived index files as optional build output.
- **Release archiving no longer needs linkage**: A `Complete` spec or quickfix is archive-eligible without populated `code_ref` / `knowledge_ref`. `check-planning-references` no longer emits `linkage_findings`; branch and identifier leak detection is unchanged.

### Fixed

- **Release archival recognizes a passing closeout gate**: A spec whose `gates/closeout.md` records `status: pass` and `decision: complete` is treated as complete even when `spec.md` still carries a stale Status line.

### Removed

- Per-requirement Knowledge stubs (`knowledge/fr-NNN.md`) generated by `setup-plan`, and the `validate-knowledge-coverage` scripts.
- `code_ref` / `knowledge_ref` task and checklist fields from the Tasks, Implement and Quickfix guidance.
- The derived-index regeneration step in Implement, the derived-index and `last_verified` drift gates in `/devspark-create-pr`, `/devspark-pr-review` and the `generated-artifact-drift` check in `knowledge-integrity.py`.

### Migration

Forward-only; no conversion script and no rewrite of existing specifications. Older stubs and `code_ref` / `knowledge_ref` suffixes remain readable and are ignored. CI that compared `index.json` / `coverage.json` should use `build_knowledge_index.py --check`. Copies of the removed `validate-knowledge-coverage` scripts left in an existing `.devspark/scripts/` are unused and can be deleted. See [Upgrade](site/src/get-started/upgrade.md).

### Known limitations

- Command and contract text shrank only modestly (commands about 84.3k to 81.6k words, -3%; `pr-review` about 9.8k to 8.1k, -17%; contracts roughly unchanged at 15.7k). The simplification is mainly in removed mechanisms and checks, not shorter prompts. The report template no longer hand-writes Action Items and Findings Detail, which the state engine renders from `review_state`.
- The Spec 160 reuse replay was a single run per arm. ArrowSpark 016, Triage 044 and the `_etag` replay were not run.
- Judge states and seals, Analyze, Verify and Closeout consolidation are deferred: Judge has many consumers across commands and tests.

## [9.2.0] - 2026-10-15

### Added

- **PR review finding closeout**: PR reviews keep one canonical state per finding, with guarded transitions and derived review views. `/devspark-address-pr-review` updates a review in place with bounded changes instead of re-reviewing from scratch. Severity and blocking are separate: a finding's severity does not decide whether it blocks. Known limitation: the end-to-end check by a distinct reviewer has not been run, so independent-reviewer assurance is not claimed.
- **Architectural Fitness review**: `/devspark-pr-review` weighs coupling, responsibilities, fragile state, duplication, and the consequences of a reasonably foreseeable next change. A finding needs code evidence and a concrete consequence, and speculative refactoring is excluded.
- **Knowledge Strength review**: `/devspark-pr-review` names the Knowledge owners for the change, cites the applicable invariants and sources concisely, and flags stale, missing or contradictory authoritative Knowledge.
- **Code First quickfix**: `/devspark-quickfix` accepts a change that already exists, reconciles the actual diff, and finalizes it through the same quickfix record and assurance, with no prior spec, plan or tasks.
- **Release archival script**: `/devspark-release` now archives completed work with a script (`scripts/release-archive.py`, with PowerShell and Bash wrappers) instead of leaving the moves to the model. `plan` previews, `apply` journals every move in `.archive/{YYYY-MM-DD}/release/archive-manifest-{version}.json` before moving, and `validate` re-checks the archive against the recorded hashes. It never overwrites archived files, is safe to rerun after an interruption, stages moves so Git keeps history, and reports orphaned bundles, untracked files, uncategorized work areas and stale references to moved paths for a decision. Operational files, `.knowledge/` and in-flight specs stay.

### Fixed

- **Archive eligibility false positives**: The release classifier read the `code_ref: pending | knowledge_ref: pending` legend text in a spec's prose as unpopulated linkage, so completed specs were reported as not archive-eligible. Only task and checklist items and standalone linkage fields are checked now.
- **Knowledge integrity scope**: `scripts/knowledge-integrity.py` no longer expects a Knowledge node under `examples/`.
- **Linux CI test failures**: The legacy-interpretation tests in `test_address_pr_review_contract.py` removed `/usr/bin` from `PATH` on Linux, which also removed `git` and `dirname`. They now hide only the Python executables. Four stale contract tests were updated to match current command text.

### Changed

- **Faster test suite and release packager**: The test suite runs in parallel with shared fixtures, and the release packager and Bash helpers start far fewer processes. Behavior is unchanged.
- **Philosophy and getting-started documents**: The philosophy page is split into a vision and a manifesto, and the getting-started guidance matches.
- **Command invocation guidance**: The quickstart guides, quickstart README and skills architecture doc now state that DevSpark command skills start only when typed as a slash command with the leading `/`. The agent does not start them on its own, and the bare name is sent as plain text. Invocation behavior is unchanged.

## [9.1.0] - 2026-10-12

### Added

- **Lean Shift-Left Constitutional Validation**: Early constitutional conflict detection during Specify and Clarify stages to catch contradictions before planning and task generation.
- **Delta-Oriented Development Guidance**: Embedded bounded-delta authoring philosophy across Specify and Plan workflows, defining specifications as bounded hypotheses about the next valuable change to working software.
- **Specification/Release Lifecycle Separation**: Decoupled specification completion from product release, packaging, and deployment obligations. A specification delivers a releasable change without depending on version publication or distribution.
- **Engineering-Judgment Hardening**: Integration boundary seam evaluation in Plan (evaluating existing orchestration and enrichment seams before widespread wiring), safe contract-preserving simplification in Implement, and accidental complexity review in PR Review.

### Changed

- **Lean Specification & Planning Templates**: Reduced boilerplate, streamlined Rationale Summary consolidation, and eliminated duplicated requirements across planning artifacts.
- **Lifecycle Freshness Alignment**: Harmonized planning-edge freshness, stage evidence classification, and judge approvals.

### Fixed

- Fixed PowerShell automatic pipeline variable `$Input` collision in `create-release-packages.ps1`.
- Excluded trunk branch names from literal planning reference checks in `check-planning-references.*`.
- Ensured POSIX path and Git Bash compatibility in `test_devspark_config_contract.py`.

## [9.0.0] - 2026-10-11

DevSpark 9.0 is a **breaking** release: one version, one command convention, one installation format.
Every command is invoked as `/devspark-<command>` (for example `/devspark-plan`), and GitHub Copilot receives each of the 38
commands as a native Agent Skill. The dotted `/devspark.<command>` form from 8.x is retired with no
aliases, fallback, or compatibility mode.

### Changed

- **Hyphenated Agent Skills.** GitHub Copilot installs `.github/skills/devspark-<command>/SKILL.md`
  for all 38 commands; other agents install the same hyphenated command names. Prompt and agent
  files are no longer distributed, and the installers, packagers and manifest ship skills only.
- **Hyphenated guidance everywhere.** Command templates, next-step recommendations, errors,
  recovery messages, quickstarts, the site and the README use `/devspark-<command>`.
- **Implementation complete means ready to merge and deploy.** Verification obligations carry a
  `stage` (`pre-merge` or `post-deploy`) and an `evidence_class` (`automated`, `local-integration`,
  `deployed`, `rollout`). A post-deploy obligation is deferred with an owner and an existing durable
  record, stays outstanding until deployed evidence exists, and does not block implementation
  closeout or the pull request. Pre-merge safety, compliance and security requirements still block.
- **No Azure DevOps `User Story` creation, and no work item as a side effect.** The work-item
  helper refuses `User Story` in both script twins and defaults to `Task` when no type is set.
  No lifecycle command creates a work item of any type, and a missing tracking record is never a
  reason to create one. `/devspark-workitem-create` remains the developer-invoked, confirmed,
  one-item creation path, and `/devspark-workitem-review` no longer hands off to it. Existing items
  can still be read, reviewed and referenced.

### Fixed

- **No Python bytecode in installs.** The published manifest and `/raw` tree no longer list
  compiled `.pyc` files, so a quickstart install places only source scripts.
- **Quickstart previews the real prompt.** The Path A preview prints the stock prompt, not the
  short skill entry point, and every guide names skills with `/devspark-<command>`.

### Upgrading from 8.x

Run your agent's quickstart. It installs the 9.0 skills, lists the 8.x entry points it will retire,
and asks once. Unmodified managed entry points are deleted; edited ones are preserved byte-for-byte in
`.devspark.work/migration/8.x-entry-points/`; team and developer customizations under
`.devspark.work/` are untouched and keep the developer, team, default precedence. Conflicts, such as
an existing non-DevSpark `devspark-<command>` skill folder, are reported and never overwritten.
Repeating the upgrade changes nothing. See the upgrade guide on the site.

## [8.3.0] - 2026-10-10

DevSpark 8.3 keeps Plan and Tasks current with their upstream artifacts and adds script-first
branch synchronization. It adds one command, with no new planning stage, gate, or state store.

### Added

- **`/devspark.merge-from-main`.** Merges the latest remote `main` into the current branch with a
  script (`merge-from-main.sh` / `merge-from-main.ps1`): fetch, merge, report conflicted files with
  their marker line ranges, then `--continue` verifies no markers remain, stages, and commits. The
  agent is used only to resolve the reported conflict hunks, keeping routine syncs token-cheap.

### Changed

- **Plan and Tasks stay current with their upstream.** The Plan records the spec fingerprint it read
  (`spec_semantic_hash`, ignored by the Plan's own review fingerprint), and `review-state` reports
  `plan_spec_state` and `tasks_plan_state` as `current`, `stale` or `unknown`. `/devspark.next` routes
  a stale edge to `plan-stale-against-spec` or `tasks-stale-against-plan` in both shells; `unknown`
  never routes and pending decisions, `STOP` and review invalidation keep precedence. Before Judge,
  re-running `/devspark.plan` reconciles the draft plan with the current spec; after Judge, revise
  stays Judge-driven. `/devspark.tasks` restamps alone when its projection is still coherent.

- **Risk-sized PR reviews.** Context helpers compute per-file tiers, an auditable risk rating and
  short, standard or full report forms from the complete changed-file set. Knowledge ownership
  can promote critical files; reviewers may escalate but never lower the supplied floor.
  Deterministic validation checks report consistency, while calibration compares recorded
  outcomes by the framework version that produced them, without claiming to prove review quality.
- **Explain keeps discovery separate from work.** Knowledge updates require a developer request
  and their own explicit approval; trace saving requires separate approval. Confirmed code defects
  are offered to Quickfix, and missing behavior to Specify.

### Fixed

- Create PR returns `knowledge.checked_head` inside its result object rather than emitting a
  stray statement.
- Current Knowledge and public guides now cover branch synchronization, PR risk helpers,
  Explain's approval boundary and upstream planning freshness. Tooling references have explicit
  taxonomy coverage, and the README consistently reports 38 active commands.

## [8.2.0] - 2026-10-08

DevSpark 8.2 makes the spec the source of truth for the commands that read it, and makes Tests a
durable pillar with an optional acceptance-planning artifact. It adds no command, lifecycle stage
or gate, and Planning Review and Judge are unchanged.

### Changed

- Clarify, Plan and Analyze consume the spec by declared purpose. A ten-element consumption map in the spec validation contract names which spec knowledge each command reads and writes; only requirements and success criteria authorize plan work, constraints shape the design, and context informs it. Clarify applies answers to every affected spec element and records confirmed invariants, constraints and accepted limitations. Analyze reports a Plan that contradicts a recorded decision or changes declared behavior (report-only). Plan setup records which spec sections exist. No new command, stage, gate or artifact.
- Tasks guidance no longer says tests are optional: every behavior change considers its Tests impact (add, update, retire or none), and acceptance work is limited to what can finish before the PR.
- Public site simplified. Get Started now centers on one canonical How It Works page, with an interactive route explorer on the home page; the command guides are consolidated into Planning Review, Review and Audit, Knowledge, and a Command Catalog; the Why section merges About with Architecture and Controls, and Evidence becomes How to Evaluate. Retired pages redirect to their replacements.

### Added

- Plan can create one conditional, ephemeral `qa-acceptance.md` when independent acceptance validation is warranted: Given/When/Then scenarios traced to the spec, a free-text surface, an automated, manual or hybrid runner, and a regression disposition (`add`, `update`, `retire` or `none`). Analyze, Critic, Implement and PR Review consume it through their existing lanes; no new command, stage or gate.
- The Tests pillar in the Knowledge Framework Contract: Tests are durable, repeatable evidence, and the regression baseline is curated rather than only accumulated. The spec owns defining and preparing acceptance, and post-deployment QA execution stays outside spec completion.

## [8.1.0] - 2026-10-05

DevSpark 8.1 stabilizes the lifecycle 8.0 introduced. A feature that passed Planning Review now
stays valid through implementation bookkeeping, a Plan rerun can no longer destroy work, a Judge
`STOP` is recovered through the owner of the correction, and two scope-authority gaps are closed.
Create PR becomes the review-readiness boundary, and PR Review becomes a more precise and more
reliable independent reviewer: it promotes only validated findings and checks Knowledge claims, not
just Knowledge changes. It adds no command, lifecycle stage, assurance gate, state store or cache.

### Changed

- **Planning freshness distinguishes meaning from bookkeeping.** `judge.py semantic-hash` records
  an algorithm-versioned (`sem1`) digest of the decision-bearing content of a spec, plan, tasks
  file or gate. Task checkboxes and linkage, spec status, Implementation Notes and verification
  evidence no longer invalidate a valid Planning Review (`bookkeeping-changed`, non-blocking). A
  changed requirement, design, or task definition still does. Raw hashes remain as provenance and
  for seal and guard concurrency checks.
- **`next` is directional after `PROCEED`.** Unfinished work routes to Implement, completed work to
  the required Verify modes (including Closeout), then to the existing commit, Create PR and PR
  Review states. A retained completed bundle or quickfix record never routes back to Implement or
  Planning Review.
- **`setup-plan` no longer overwrites an existing Plan** (both shells). It reports `PLAN_EXISTS`
  and `PLAN_MODE` (`create` or `revise`) and recreates the template only on an explicit
  `--reset` / `-Reset`. Existing JSON keys are unchanged.
- **A Judge `STOP` has an owned recovery path.** `judge.py remediation` adds `plan_revisions` and
  `task_work`; Plan revises in place, Tasks re-projects unchecked work against the recorded
  `plan_semantic_hash`, and a focused Planning Review follows. Raw Analyze and Critic findings
  never become architecture directly.
- **Tasks operationalizes the Plan.** Every task cites a forcing source, and a task that would add
  a mechanism the Plan lacks stops as a `PLANNING GAP` routed to Plan revise. Tasks hands off to
  Planning Review rather than straight to Implement, and the legacy gate-remediation merge no
  longer auto-selects Medium or Low findings.
- **`address-pr-review --auto` is narrower.** The helper recognizes `PRD{N}-##` ids and reports
  `status`, `blocking`, `auto_eligible`, `route` and `reason` per finding; only open critical/high
  or blocking PR-delta findings are auto-eligible. Medium/Low are reported, `CON` findings route to
  `evolve-constitution`, and a suggested fix is evidence rather than permission to add machinery.
- **Planning is question-driven.** `research.md` is a question ledger created only when a material
  planning question needed research; `data-model.md`, `contracts/` and `quickstart.md` exist only
  when the change justifies them. The Plan records `expected_change_surface` as orientation, not an
  allow-list.
- **The shared preamble is split into a core and consumer modules.** The core
  (`command-preamble-contract.md`) binds every command; finding-fix, convergence, orchestration,
  provenance and configuration live under `templates/preamble/` and are loaded only by the commands
  listed in the core's module table. Section numbers are unchanged, and a new core section lets a
  command reuse a full, unchanged artifact already in its context. Shared bytes loaded drop from
  28,437 for every command to 15,945 (Plan), 19,946 (Tasks), 19,588 (Next) and 26,495 (Analyze,
  Critic). These are structural byte counts, not measured token or runtime savings.
- **Create PR is the review-readiness boundary.** `create-pr` (both shells) now evaluates
  committed-state Knowledge against the exact HEAD it submits and reports `knowledge.readiness`
  (`ready`, `blocked`, `not-applicable`, `unknown`) with structured `knowledge.blockers[]`
  (`kind`, `path`, `source`, `source_date`, `last_verified`, `message`),
  `knowledge.stale_untouched_count` and `knowledge.checked_head`. A tracked index that drifts from
  the committed HEAD, a Knowledge build failure, or a stale entity the PR touches blocks both Create
  and Update mode with an actionable message; a stale entity the PR does not touch is only counted.
  There is no override (draft and `--auto` do not bypass it) and the command never regenerates,
  edits, bumps `last_verified`, or commits. Previously the same `--check` result was reported but
  never enforced, so a pre-commit regeneration that went stale at commit time first failed in PR
  Review.
- **PR Review's Knowledge check is read-only.** Section 6c confirms the repository HEAD equals the
  PR's commit SHA and runs the builder with `--check`; it no longer runs the generator in write
  mode, which overwrote the artifacts it was meant to check.
- **PR Review promotes only validated findings.** A concern stays a candidate until it passes the
  Finding Legitimacy Check, which now requires a concrete observation, a violated expectation,
  current-PR relevance and actionability for every numbered finding (including Low), a consumer
  trace with the nearest falsifying evidence for behavioral Medium-and-above concerns, and an
  attribution of introduced, exposed or pre-existing debt. Intended or merely surprising behavior,
  unrelated inherited debt and unconfirmed risks go to a new non-blocking `### Observations`
  subsection; an unconfirmed risk never blocks or exceeds Low. PRD3 coverage is judged against the
  changed behavior and existing helper coverage, so delegation call sites do not each need a test.
  Severity no longer prefers the higher tier, `REQUEST CHANGES` must trace to a validated blocking
  finding, and remediation starts with the least-complex sufficient correction.
- **PR Review checks Knowledge claims, not just Knowledge changes.** PRD1 now finds owners with the
  existing `explain-context --files`, searches them word-bounded for members the diff adds to an
  enumerable contract, and reads the section a gap points to before asserting that Knowledge
  matches. `last_verified` is treated as a claim of review rather than proof. The duplicate
  "Review Updates" guideline was removed; no pass, helper, gate or schema was added.
- Implement now states that Knowledge it generates is provisional for fields that depend on future
  committed Git history; Create PR owns final validation.
- The create-pr preflight resolves `python3` then `python` (requiring PyYAML and Python 3.11+)
  instead of failing when `python3` is absent.
- The active-command count in the README, the templates README and the site About page now matches
  the 37 command prompts shipped.

### Added

- `explain-context --files <paths>` reports which Knowledge nodes apply to or cite each file, with
  the matched pattern and relationship, plus unmapped files.
- `explain-context --project` runs lexical matching and projection over one verified index build.
  An input that changes during the run discards the output and exits 3 with `RETRY_REQUIRED`.
  Nothing is persisted. Within a build each cited source's commit date is queried once.
- `tests/test_preamble_modules_contract.py`: a command that cites a preamble section must load the
  module that owns it, and every listed consumer must load its module.

### Compatibility

- Gates, specs and Tasks written before 8.1 carry no semantic hashes and keep the raw-hash
  behavior; nothing is retro-stamped and no existing artifact needs rewriting.
- New fields (`semantic_hash`, `plan_semantic_hash`, `revision_target`, `expected_change_surface`)
  are additive and optional. Commands tolerate a missing `research.md`, `data-model.md`,
  `contracts/` or `quickstart.md`.
- The Plan overwrite change is intentional: scripts or habits that relied on `setup-plan`
  restoring the template must now pass the explicit reset flag.
- Create PR readiness is additive: a repository with no engine, no usable interpreter, a legacy
  engine, or no tracked `.knowledge/index.json` reports `unknown` or `not-applicable` and continues.
  The legacy `knowledge.index_fresh` and `knowledge.gap_summary` fields are unchanged; a missing
  index is now `not-applicable` rather than reported as stale.

## [8.0.0] - 2026-10-04

DevSpark 8.0 introduces Planning Review and Judge. Analyze and Critic remain independent assurance
lenses, but their findings no longer directly expand implementation scope. Judge reconciles them
into root concerns, human decisions, required work, simplifications, routes, accepted limitations,
and future work. 8.0 also introduces Minimum Sufficient Change: MVP, KISS, and YAGNI as an explicit
counterweight to assurance-driven complexity.

### Added

- **`/devspark.planning-review` — one bounded planning decision.** Analyze, Critic (when a
  change-shape signal applies), and a new Judge phase now run behind a single developer-facing
  step. The feature is resolved once and handed to every child, so a branch name that differs from
  the spec directory can no longer send two children to different work. Analyze and Critic remain
  available for expert use and drill-down.
- **Judge adjudicates; it does not discover and does not remediate.** Every Judge concern must cite
  at least one existing child finding, and the phase may write only `gates/judge.md`. Both are
  enforced by `scripts/judge.py` (`validate`, and a `guard begin`/`guard end` read-only guard with
  PowerShell and Bash entry points), not only by prompt wording. The contract is
  `templates/judge-contract.md`.
- **Four separate concepts.** Severity stays lane-specific; `classification` reuses the closeout
  vocabulary; `resolution` (`require`, `simplify`, `accept`, `defer`) is the remediation choice;
  `change_shape` and `route` record what kind of change is proposed and which later phase owns it.
  A significant finding cannot be downgraded without human authority, a governing requirement, or
  deterministic contradictory evidence.
- **Semantic freshness.** Child gates are `fresh`, `stale-nonblocking`, `stale-recheck-required`, or
  `superseded`. Staleness blocks only when it invalidates the evidence for a blocking decision, and
  traceable bounded remediation no longer forces a full rerun.
- **Future Work Plans.** A deferral is a disposition, not a task status. Preserved future work is
  materialized outside the spec under `.devspark.work/intake/` (`templates/future-work-plan-template.md`).
- **`scripts/judge.py lifecycle`.** Create PR and Implement now check that required tasks, routed
  obligations, preserved future work, and closeout are complete: a pull request represents
  completed spec work offered for acceptance, and merge terminates the spec lifecycle. It also
  rejects a stale Judge, a child that needs a recheck, a pending decision, and a required planning
  review that never ran (a stale `PROCEED` is not evidence).
- **Pending human decisions are an honest state.** A concern awaiting a human carries
  `resolution: null`, `needs_authority: true`, and a `decisions_needed` entry. It yields
  `CONDITIONAL` and lands in a new `pending_decisions` bucket: no task, no future work, not
  accepted. `pending` is deliberately not a fifth resolution.
- **Planning Review run provenance.** `judge.py resolve` generates one run id handed to Analyze and
  Critic, which stamp it as `planning_review.run_id`. `judge.py seal` records whether each child was
  generated by this run or intentionally reused, and a child replaced after sealing is invalidated.
  No locks, no run database.
- **Minimum Sufficient Change.** A short doctrine (MVP, KISS, YAGNI) in the shared preamble
  contract. Specify gains a small MVP-boundary section, Plan gains `operating_context` and
  `expected_new_mechanisms` (an expected shape, not limits), Critic leads with the least-complex
  mitigation (`least_complex_mitigation`, `mitigation_kind`), and Judge asks what can be removed.
  No new command or gate.

### Changed

- Analyze findings now carry the shared `classification` and use one `analyze-NNN` identifier in both
  the report table and the machine-readable block. Critic's `root_cause` is populated when the
  evidence supports a causal relationship and may stay empty.
- Gate Remediation Merge consumes Judge dispositions when a valid `gates/judge.md` exists. Only
  `require` and `simplify` become planning tasks; routed obligations, accepted limitations, and
  future work do not. Routes with no Judge artifact behave as before.
- `/devspark.next` recommends one `tasks-need-review` step instead of Analyze then Critic. An
  unresolved Planning Review (missing, `STOP`, `CONDITIONAL`, or needing a recheck) now outranks task
  progress, so a finished task list no longer routes to implementation finalization.
- The Judge read-only guard now protects the planning bundle (spec, plan, tasks, child gates)
  instead of every dirty file in the repository. Unrelated concurrent changes are reported as
  `concurrent-change-detected` and are not attributed to Judge.

## [7.8.0] - 2026-10-01

Explicit, bounded, attributable judgment. This release separates how Knowledge is *shaped* from
what it *means*, gives each assurance capability a single question it owns, defines when a route
is allowed to finish, and records which framework version produced every artifact.

### Added

- **Artifact form and semantic role are now separate axes.** A Knowledge artifact previously
  carried one `type` field that conflated its physical shape with its meaning, which made some
  legitimate combinations unrepresentable. Artifacts now declare a `form` (`flat-document`,
  `entity-layer`, or `governance-decision`) and a `role` drawn from the set valid for that form.
  The vocabulary is published as a machine-readable contract at
  `templates/schemas/knowledge-ontology.json`. Flat documents and entity layers are co-equal
  citizens of one corpus — neither is a degraded form of the other, and both are indexed,
  retrieved, and governed identically.
- **Entity type and entity layer are stated to be independent axes.** Both vocabularies contain
  the term `integration`, which invited the reading that an entity with an integration layer must
  *be* an integration. An entity may *be* a boundary (`type: integration`) or merely *have* an
  integration facet (`layer: integration`); neither implies the other, and the ontology contract
  says so explicitly.
- **An assurance contract gives each reviewing capability one question it owns.** Analyze asks
  whether the planning artifacts are internally sound; Critic asks whether an internally sound
  plan is wrong about the real system it will run in; Verify asks whether the implementation
  actually worked; PR Review asks whether the resulting delta should be accepted. Each capability
  also declares what it does *not* own, which is what prevents the same finding from being raised
  four times in four voices. Verdicts are derived from the findings rather than asserted, passes
  are bounded, and uncertainty is recorded as uncertainty instead of being inflated into a defect.
- **Critic declares when it applies.** Rather than running at uniform depth on every change,
  Critic names the signals that make a change worth open-world challenge — persistent data shape,
  cross-boundary interaction, state lifecycle, nondeterministic behavior, and new entry points —
  so a contained change is not subjected to speculative review it cannot benefit from.
- **A closeout phase defines when a route is finished.** The convergence rule is now explicit: a
  spec is complete when its stated objective has been resolved and every remaining finding has
  been classified — not when every observation generated during the work has been eliminated.
  Verification may discover work, but discovery alone does not expand the current specification.
  Five expansion triggers (failed objective, unresolved requirement, violated invariant,
  correctness defect, regression caused by this change) are the only grounds for mandatory work
  inside the active route. Closeout runs automatically inside `/devspark.verify`; the new
  `/devspark.closeout` command is an advanced re-entry point, not a normal-path step.
- **Findings carry one of four classifications.** Blocking Defect, Accepted Limitation, Deferred
  Work, or Learning / Changed Assumption. Only a Blocking Defect creates mandatory work in the
  current route; an unclassified finding is itself blocking, and a classification without its
  required record — who accepted it, where it was captured, what the revised understanding is —
  is an unclassified finding wearing a classification's name.
- **Acceptance criteria declare their kind.** A criterion is a `requirement`, an `invariant`, a
  `hypothesis`, or a `target`. A failed requirement is a defect; a disproven hypothesis is a
  result, and may be a successful outcome. An undeclared criterion reads as a `requirement` — the
  strictest reading — so existing specs keep their current meaning with no edit required. A
  failed requirement or violated invariant can never be relabelled into a softer kind after the
  evidence arrives, and pull-request review gates on that laundering directly.
- **Artifacts record the framework version that produced them.** Paired PowerShell and Bash
  helpers resolve the active version and revision, planning and gate artifacts carry it, and a
  route that spans an upgrade stays attributable rather than being silently restamped.

### Changed

- **Verification depth is selected from the shape of the change.** `/devspark.verify` matches the
  change against a set of named shapes and reports which ones it matched, instead of applying one
  fixed verification depth regardless of what was actually modified.
- **A quickfix that outgrows its route surfaces the decision.** Named signals prompt an explicit
  continue-or-promote choice rather than letting a quickfix quietly accumulate the weight of a
  full spec. The escalation is never automatic — the developer decides.

### Fixed

- **The Knowledge index no longer drifts between Windows and Linux.** Generated artifacts sorted
  paths using `Path` ordering, which is case-insensitive on Windows and case-sensitive on Linux,
  so an index regenerated on one platform failed the drift gate on the other with no real content
  change. Sorting now uses a stable, platform-independent key.
- **Taxonomy classification no longer reports permanent mismatches.** Separating form from role
  resolved a standing set of `taxonomy-mismatch` findings that could not previously be cleared
  without widening the node-type vocabulary.

## [7.7.2] - 2026-09-30

Knowledge Context correctness. This release improves what an agent actually retrieves and
carries into a task: retrieval precision, parity for flat Knowledge documents, structural
reachability of entity layers, explicit context provenance, and a stated distinction between
candidate context and resolved context.

### Fixed

- **Keyword matching no longer produces substring false positives.** Relevance scoring in
  `explain-context.py` compared keywords against document text with a plain substring test, so
  `not` matched `notation` and `annotation`, `plan` matched `explanation` and `planning`, and
  `id` matched nearly everything. Short, common fragments therefore accumulated score across
  unrelated documents and pushed genuinely relevant Knowledge below the selection threshold.
  Matching is now token-aware: text is split on non-alphanumeric boundaries and on camelCase
  and acronym boundaries, tokens are normalized for grammatical number only (deliberately not
  stemmed, so `planning` and `plan` stay distinct), closed-class stopwords are excluded, and
  keywords shorter than three characters are dropped. A keyword now matches only when it
  equals a whole normalized token. Scoring weights are unchanged — only the matching predicate
  changed — so this sharpens precision without re-tuning ranking behavior.
- **Entity layer documents were unreachable through graph traversal.** The composition
  relationship between an entity and its layer documents was implied by directory structure
  but never materialized as edges in `.knowledge/index.json`, so layers could only be found
  lexically. A layer whose wording did not happen to overlap the request was invisible to any
  graph-based traversal, even when its parent entity was the subject of the request. The index
  now emits `has-layer` edges from each entity to each of its layer documents, making layer
  composition traversable. In this repository that raises the authored graph from 9 edges to
  20, and the added edges recover layer documents that no lexical path reaches.
- **Stale and ephemeral applicability references in the Knowledge corpus.** The participant
  vocabulary document still declared applicability to `src/**`, a tree removed when the CLI was
  retired, and the autonomy execution model declared applicability to `.devspark.work/autonomy/**`,
  a path that never existed and that sits under an ephemeral root which authoritative Knowledge
  must not cite. Both references are removed.

### Changed

- **Context projection now reports why each candidate was reached.** Every projected candidate
  carries a provenance classification — `governance_constraint` for constrains and
  constrained_by edges, `structural_composition` for entity-to-layer composition, and
  `graph_relation` for all other authored relationships. A reviewer can now distinguish a
  document reached because governance binds it from one reached because it is structurally part
  of the subject, rather than treating every traversal result as equivalent.
- **Candidate context and resolved context are now explicitly distinguished.** Planning and
  projection guidance previously left room to treat everything a traversal surfaced as context
  to load. The guidance now states that projection produces candidates, that selection is a
  separate and required judgment, and that a resolved set materially smaller than the candidate
  set is the expected outcome — a resolved set equal to the candidate set means no selection
  happened. Guidance for dropping sibling layers and governance hubs that were reached
  structurally but are not relevant to the task is included.

## [7.7.1] - 2026-09-27

### Fixed

- **Deterministic, OS-independent ordering in generated `.knowledge` artifacts.**
  `build_knowledge_index.py` sorted `pathlib.Path` objects directly at several call sites.
  `Path`/`PurePath` comparison is platform-flavor-dependent — `PureWindowsPath` normalizes case
  before comparing, `PurePosixPath` does not — so the same repository could produce a different
  node order in `.knowledge/index.json` (and, transitively via entity ordering, in
  `.knowledge/ontology/coverage.json`) depending on which OS generated it. A Windows-generated
  index checked by Linux CI's drift gate could then fail with a false positive purely from
  reordering, with no actual content change. Fixed by introducing a canonical
  `stable_path_sort_key(path) -> str` helper (returns `path.as_posix()`, deliberately not
  case-folded) and applying it at every direct-`Path`-sort call site: five in
  `build_knowledge_index.py` (`build_entities`, `build_index`,
  `iter_source_claim_documents`, `prune_unreferenced_baselines`), one in
  `knowledge-integrity.py`'s `check_root_reachability` (reused from the primary engine, which it
  already imports for drift validation), and one each in `migrate-knowledge-to-entities.py`'s
  `plan_moves` and `release-context.py`'s `bundle_text` (small standalone duplicates, matching
  this codebase's existing convention of independently duplicating tiny path helpers like
  `relative()` across framework scripts rather than sharing a library). Regenerating this repo's
  own `.knowledge/index.json`/`coverage.json` with the fix produced no content diff beyond the
  `generated.at` timestamp, confirming the change is purely about eliminating platform-dependent
  ordering, not altering any current output. `/devspark.context-projection` (7.7.0) is unaffected
  — it never sorts `Path` objects directly.

## [7.7.0] - 2026-09-30

### Added

- **Context Projection v1 (`scripts/context-projection.py`, `/devspark.context-projection`).**
  Deterministic bounded-hop context expansion for planning, built entirely on the authoritative
  `.knowledge` graph `build_knowledge_index.py` already maintains — no redesign of knowledge
  discovery, no semantic/vector retrieval, no automatic graph authoring. Given one or more
  lexically discovered seed ids (the same ids `/devspark.explain`'s `MATCHED_KNOWLEDGE` /
  `MATCHED_ENTITIES` surface), it performs a multi-source breadth-first traversal across
  **accepted** relationships only — entity `relations[]`, `constrains`/`constrained_by`
  reciprocity, and `links.references` — never an unaccepted `/devspark.discover-knowledge`
  finding. Traversal is bounded (`--max-hops`, default 2) and guarded against explosion
  (`--max-candidates`, default 100, with reported `truncated`/`truncation_reason` and
  deterministic distance-then-id ordering, never silent). Every candidate carries full
  provenance (seed, immediate predecessor, relation, hop distance) even when multiple paths
  converge on the same node, and is grouped into `entity` / `governance` / `other` channels
  rather than forced into one competing lexical score. An `--audit-fan-out` mode reports
  per-entity and repository-wide 1-hop/2-hop fan-out sizes to surface graph hubs before this
  becomes default `/devspark.plan` behavior. Dual-language wrappers ship at
  `scripts/bash/context-projection.sh` and `scripts/powershell/context-projection.ps1`.
- **`/devspark.plan` Context Resolution now uses Context Projection.** Step 4 (Context
  Resolution) is unchanged in intent — still a pinned, human/agent-curated working set recorded
  as `context_resolved` in `plan.md` — but now names Context Projection as the traversal
  mechanism seeded from lexical hits, so the same deterministic, provenance-preserving expansion
  backs every plan. `/devspark.analyze`'s existing mechanical validity check (§I) and
  `/devspark.critic`'s existing judgment-based sufficiency check both already covered this
  surface unchanged; `/devspark.critic` can now optionally re-run
  `/devspark.context-projection` against the same seeds as a diagnostic cross-check when judging
  sufficiency.

## [7.6.1] - 2026-09-29

### Fixed

- **`scripts/discover-knowledge.py` finding precision.** Corrective release addressing several
  sources of low-signal noise identified after the 7.6.0 discovery rollout:
  - `missing-relationship` no longer fires on hub-only co-occurrence (a shared fixture or helper
    touched by many unrelated entities). Hub tests are detected and excluded from evidence;
    findings are only emitted when distinctive evidence (shared headings, or narrow shared test
    coverage outside the hub set) remains, with confidence graded on evidence quality.
  - `alias-candidate` suppresses generic single-word noise (a stopword list covering common
    identifiers like `id`, `data`, `config`, `result`) and terms that recur broadly across many
    unrelated entities (hub terms), unless the term forms a distinctive multi-word phrase.
  - New `governance-relationship-candidate` category: detects entities whose source files overlap
    a governance decision's `appliesTo` paths but are not listed in that decision's `constrains`,
    so governance/ADR context participates in discovery instead of being invisible to it.
  - `entity`-scoped discovery (`/devspark.discover-knowledge <entity-id>`) now correctly resolves
    an entity's declared `source_of_truth` directory/glob references into their concrete member
    files before comparing against other nodes' claims, fixing `broad-mapping` and
    `overlapping-ownership` findings that were previously silently dropped for entities whose
    `source_of_truth` was a directory rather than a single file.
  - Repository-wide-only categories (`knowledge-gap`, `entity-candidate`) are now reported
    separately as `GLOBAL_FINDINGS` for `entity` scopes instead of bleeding unrelated
    repository-wide findings into a single entity's review; opt back in with `--include-global`.
  - New `--min-confidence` and `--limit-per-category` flags bound output size for large
    repositories without changing default (unfiltered) behavior when omitted.
- **`scripts/knowledge-benchmark.py` consumer-visible metrics.** Benchmark metrics now separately
  report consumer-visible candidate-set accuracy alongside full-ranking accuracy, so benchmark
  scores reflect what a consumer of discovery output actually sees rather than only the full
  ranked list.

## [7.6.0] - 2026-09-28

### Added

- **Knowledge integrity validation (`scripts/knowledge-integrity.py`).** A CI-friendly,
  non-mutating validator that runs six checks against `.knowledge`: engine divergence between the
  canonical `build_knowledge_index.py` and any legacy repo-local copy, generated-artifact drift
  (`.knowledge/index.json` out of sync with a fresh build), taxonomy-registry consistency,
  mapping integrity (a failed index build is now surfaced as a structured finding instead of a
  crash), unreachable `.knowledge` roots (extra directories the index never covers, e.g. under
  `examples/`), and taxonomy/schema contradictions. Emits human-readable and `--json` output and
  exits non-zero on any hard-failure finding, so it can gate CI. Dual-language wrappers ship at
  `scripts/bash/knowledge-integrity.sh` and `scripts/powershell/knowledge-integrity.ps1`.
- **Shared knowledge finding schema (`scripts/knowledge_findings.py`).** A stable finding shape
  (`finding_id`, `category`, `severity`, `confidence`, `subject`, `summary`, `evidence`,
  `recommendation`, `changes_authoritative_truth`, `source`) with a deterministic
  content-addressed `finding_id` so the same underlying condition always reports the same id
  across repeated scans. `knowledge-integrity.py` and `/devspark.discover-knowledge` both emit
  findings in this schema, so results from either tool triage side by side under one vocabulary.
- **Knowledge retrieval evaluation harness (`scripts/knowledge-benchmark.py`).** Reuses
  `/devspark.explain`'s exact matching engine (`explain-context.py`) unchanged, so benchmark
  results reflect real retrieval behavior rather than a parallel reimplementation. Accepts a
  JSON/YAML fixture of `{query, expected}` cases (single- or multi-concept), and reports
  rank/visibility metrics (`rank1_rate_pct`, `top3_rate_pct`, `topn_rate_pct`, `miss_rate_pct`)
  and multi-concept recall separately, plus raw top candidates so governance/ADR nodes are never
  silently hidden from the report. Dual-language wrappers ship at
  `scripts/bash/knowledge-benchmark.sh` and `scripts/powershell/knowledge-benchmark.ps1`.
- **`/devspark.discover-knowledge` is now an installed command.** Evidence-based `.knowledge`
  maintenance discovery — proposes knowledge gaps, entity candidates, missing/broad/overlapping
  mappings, missing relationships, alias candidates, pinned-claim contradictions, and
  ephemeral-identifier/heading historical leakage for human review. Non-mutating by default; the
  only writes it can ever perform are two narrow, explicitly-confirmed apply operations
  (`--apply-alias`, `--apply-relation-from`/`--apply-relation-to`, both gated behind `--write`).
  Ships the full command surface (`templates/commands/discover-knowledge.md`, agent/prompt/atomic
  shims, dual-language wrappers at `scripts/bash/discover-knowledge.sh` and
  `scripts/powershell/discover-knowledge.ps1`) plus `tests/test_discover_knowledge_contract.py`
  covering command wiring, repository-wide and scoped discovery, every finding category, shared-
  schema validation, deterministic finding identity, `--repo-root` resolution, and non-mutation
  safety (discovery, and unwritten apply operations, never touch disk).
- 25 new contract tests across `tests/test_knowledge_integrity_contract.py`,
  `tests/test_knowledge_benchmark_contract.py`, and
  `tests/test_knowledge_findings_schema_contract.py` pin finding-schema validation, deterministic
  finding identity across repeated scans, each integrity check individually, and the retrieval
  harness's reproducibility, governance-visibility, body-only-discovery, alias-discovery, and
  multi-concept-recall behavior.

## [7.5.1] - 2026-09-28

### Fixed

- **One canonical `.knowledge` index implementation.** 7.5's discovery build introduced a
  resolution-order bug: `site-audit`, `create-pr`, `get-pr-context`, `release-context`, and the
  quickstart guides could each resolve `build_knowledge_index.py` differently depending on
  whether a repo happened to carry a legacy repo-root copy alongside the framework-managed
  `.devspark/scripts/` copy — the repo-root copy silently won and never got refreshed by
  upgrades, so two definitions of `.knowledge` truth could coexist and drift apart. Every entry
  point now shares one resolver (`resolve_knowledge_engine` in `common.sh` /
  `Resolve-KnowledgeEngine` in `common.ps1`) that always prefers `.devspark/scripts/`, falling
  back to a legacy root copy only when the framework-managed copy is absent. `/devspark.upgrade`
  and the quickstart guides now detect and reconcile a lingering legacy root copy, deleting it
  when it is an identical, redundant leftover and flagging a genuine diff for the repository
  owner to resolve instead of deleting it silently.
- **Retrieval ranking no longer rewards document breadth.** A term repeated across many
  headings, or across many `source_of_truth`/`appliesTo` entries, previously added its evidence
  weight once per occurrence, so a broad document with many headings could out-rank a precise
  one that mentioned the same term only once. Each evidence class (heading, alias, metadata) now
  contributes its ranking weight at most once per query term, no matter how many fields of that
  class repeat it; `matched_on` still lists every occurrence for explainability.

## [7.5.0] - 2026-09-26

### Added

- **Content-based knowledge discovery.** `.knowledge` documents are now reachable by the concepts
  they explain, not only by id, title, path, or source mapping. Document headings and an optional
  `aliases:` frontmatter list are indexed, and body prose is searched at query time. Ranking is
  deterministic and identical for every agent: a keyword scores once per field, so relevance comes
  from *where* a term appears rather than how often, and every match reports a `matched_on`
  evidence list explaining its score. Body text is rebuilt per query rather than committed, so
  `index.json` stays small and reviewable and can never carry stale prose.

### Fixed

- **Entity relations authored as `{predicate, object}` no longer fail the index build.** 7.3.0
  began requiring `{to, rel}` and rejected the alternative spelling outright, which stopped the
  build on the first entity for repositories that had adopted it. Both spellings are now accepted
  by the generator and by `entity-node.schema.json`, and entity ids may use `_` as well as `-`.
- **`edges` now contains the graph it claimed to.** Entity `relations` and `constrained_by` were
  validated and stored but never materialized as edges, so the ontology graph held only
  `references` links and could not be traversed between entities.
- **`fully_covered` is reachable.** Coverage counted `pattern` and `plan` as gaps for every
  entity, even though both are authored only when they apply. Coverage now measures the layers
  every entity is expected to carry, so the metric reports real gaps instead of a constant zero.

### Upgrading

Regenerate the knowledge index after upgrading:

```bash
python .devspark/scripts/build_knowledge_index.py --repo-root .
```

The index gains discovery fields and a populated `edges` array, so a previously committed
`index.json` will be reported as stale by the `--check` gate used in `site-audit` and `release`
until it is rebuilt. `explain` regenerates it automatically.

## [7.3.0] - 2026-09-26

### Added

- **Content-based knowledge drift detection.** Knowledge source claims can opt into retained,
  content-addressed baselines with canonical comparison profiles for Python, text, and binary
  sources. Explicit commit scopes or full inventory evaluate pinned claims; reports distinguish
  verified, changed, and not-yet-verified content without exposing source or baseline bodies.
- **Confirmed knowledge-baseline maintenance.** `/devspark.explain` can show the exact retained-
  baseline diff and rotate one claim only after explicit confirmation. Migration is preview-first,
  enforcement is opt-in, and pruning removes only unreferenced baseline evidence.
- **Stronger knowledge completeness checks.** Knowledge auditing now reports coverage gaps and
  dangling references, validates source-claim inputs, and includes a published knowledge
  management guide covering the flat and entity models, evidence, and drift workflows.
- **PR finding-legitimacy check.** Pull-request review now evaluates whether findings are grounded
  in the changed code and evidence before treating them as actionable.

### Changed

- Knowledge-drift evaluation now validates scope and runtime controls fail-closed, supports
  migration and retained-baseline self-tests, and exposes matching behavior through the PowerShell
  and Bash entry points.
- Python, normalized-text, and byte-exact comparison profiles support appropriately scoped drift
  checks; unsupported or invalid comparisons do not silently suppress detected changes.

### Fixed

- Pull-request re-review no longer treats the pull request's own planning bundle as an escaped
  scope reference.
- Knowledge audit results now account for unresolved references and missing taxonomy coverage,
  making gaps visible instead of relying on index freshness alone.
- The release package builder strips CRLF from Windows `jq` output so agent metadata resolves
  correctly when packages are built from Git Bash.
- The knowledge-drift performance check uses an absolute runtime budget so filesystem cache and
  operating-system differences do not turn a fast token sweep into a false CI failure.

## [7.2.0] - 2026-09-23

### Added

- **Optional Azure DevOps work-tracking integration.** Off until a repository adds a
  `work_tracking` block to `.devspark.work/devspark.json` — its presence is the only switch; a
  repository that never adds it behaves exactly as before, with no prompts or mentions of work
  items anywhere. Two new commands: `/devspark.workitem-review` reads one named work item and
  grades it against the shared standard in `templates/workitem-standard.md`, proposing
  improvements for confirmation and never writing without one; `/devspark.workitem-create` drafts
  exactly one work item from a spec or the conversation and creates it only after explicit
  confirmation, with acceptance criteria going to the dedicated field rather than the description.
  `/devspark.specify` and `/devspark.create-pr`/`/devspark.update-pr` become work-item aware when
  the block is present — offering a review before drafting a spec, and confirming referenced work
  items resolve, respectively (read-only). Text retrieved from a work item is always treated as
  untrusted, reported content, never as instructions. The created work-item identifier is recorded
  only in the feature's temporary record under `.devspark.work/specs/` — durable code and
  `.knowledge/` never name a work item, since a board can be renumbered or reorganized at any
  time. New helper script pair `scripts/{powershell,bash}/workitem.ps1|sh` (check, read,
  propose-update, apply-update, comment, propose-create, apply-create, verify-link) and
  `templates/devspark-config.schema.json` gains the `work_tracking` schema. Documented in the new
  `.knowledge/guides/azure-devops-work-tracking.md` user guide.
- **Constitution Principle IX: Verification Command Discipline (MUST).** Every command run to
  verify work must terminate on its own, prove something the previous run did not, and show what
  it produced: non-interactive with a bounded timeout, tests run offline against recorded fixtures
  (never a live service or credentials), output streamed rather than piped through `tail`/
  `Select-Object -Last`/`Out-File`, and a command that runs long is stopped and reported rather
  than waited out. `.knowledge/governance/severity-registry.md` gains matching `§IX.HIGH` (an
  unbounded or interactive command hangs CI, or a test reaches a live service) and `§IX.MEDIUM`
  (a missing `timeout=`, or output hidden until completion) entries.

### Changed

- The no-planning-identifier-leak contract (spec/task/FR references never appearing in shipped
  code, tests, or `.knowledge/**`) is now explicitly extended to cover tests, not just production
  code and current knowledge.
- Planning bundle lifecycle and `.archive/` ownership guidance clarified across the lifecycle and
  philosophy docs: a spec bundle that is not yet `Complete` stays exactly where it is under
  `.devspark.work/specs/`, and spanning more than one release window is normal, not an error.
- `scripts/build_knowledge_index.py` reorganized its import ordering and tightened its freshness
  check logic.
- `/devspark.add-application` corrected the registry file path it writes to and clarified spec
  bundle handling.
- Site-audit script exclusion patterns corrected so generated/ignored paths are consistently
  skipped.

## [7.1.0] - 2026-09-11

### Added

- **Assisted entity-scaffold script** (`scripts/scaffold-entity.py`): drafts a new
  `.knowledge/entities/<id>/_entity.yaml` plus candidate layer doc(s) from explicit `--source`
  paths and `--layer` names, for human review before anything is written — dry-run by default,
  writes only with `--write`, refuses to overwrite an existing entity without `--force`. Reuses
  `ALLOWED_LAYERS`/`_is_forbidden_reference` from `build_knowledge_index.py` rather than
  duplicating them. Closes the gap where the only prior paths to entity content were fully manual
  authoring or a one-time bulk migration (`migrate-knowledge-to-entities.py`), neither of which
  supported ongoing, assisted creation. `/devspark.implement` step 8 now names it as an optional
  assisted alternative alongside the existing manual steps (unchanged, fully additive), and gained
  a per-task `build_knowledge_index.py` regeneration so a mistake is caught within the same task
  instead of only at Finalize. `.knowledge/tooling/developer-guide.md` documents the assisted path.
- **`.knowledge/architecture/distribution-and-update-model.md`**: new architecture doc covering how
  DevSpark is published (`azure-pipelines.yml` → Static Web App `dist/`+`raw/`) and how a
  target repo installs/upgrades from it (prompt-first manifest walk vs. zip download) — a
  knowledge-completeness gap found via `/devspark.explain`.
- **`build_knowledge_index.py --unmapped-files`**: reports which of a given set of paths match no
  node's `appliesTo` pattern. Wired into `get-pr-context.{ps1,sh}` as a new `unmapped_files` field,
  referenced by `/devspark.pr-review`'s `PRD5` step as a computed starting hint for its
  "new behavior with no knowledge" judgment call — the judgment itself stays a human call.
- **`/devspark.create-pr`**: preflight scripts (`create-pr.{ps1,sh}`) now compute a real
  `knowledge.index_fresh` / `knowledge.gap_summary` field (via `build_knowledge_index.py --check`)
  instead of the prior prompt text overstating a nonexistent script capability. Step 6 gained an
  optional, non-blocking "PR-Review Reminder" offering an immediate handoff into
  `/devspark.pr-review` after a PR is created — mirrors the existing Verify Reminder pattern;
  deliberately not auto-chained (review stays a distinct, separately invoked pass).
- **CI now validates pull requests before merge.** `azure-pipelines.yml` previously had `pr: none`
  — none of the pytest/ruff/markdownlint/`build_knowledge_index.py --check`/atomic-shim-drift/
  agents-registry-validation gates ran before a PR merged, only on push to `main`/tags. Added a
  `pr: branches: include: [main]` trigger; the `AzureStaticWebApp@0` deploy step's condition now
  also excludes `Build.Reason == 'PullRequest'` so a PR build validates only and never publishes.

## [7.0.0] - 2026-09-10

### Removed

- **`scripts/migrate-to-four-root.py` and its bash/PowerShell wrappers deleted outright, along with
  their contract test and the 3.x → 4.x major-version migration guard in all 6 quickstart guides.**
  All consumers of DevSpark are confirmed fully on v6.x, and the guard's Spec-Kit
  (`.specify/`) onboarding path is dropped with it — a repo still carrying that layout is no longer
  auto-migrated. `site/src/guides/v3-to-v5-migration.md` (the dedicated historical migration guide)
  is removed along with its nav entry and cross-links. `/devspark.migrate-knowledge-entities`
  (opt-in flat-docs → entity-ontology migration) is unaffected — a separate concern.
- **`.documentation/` is fully retired as a canonical root.** The four roots are now `.devspark/`,
  `.devspark.work/`, `.knowledge/` (including `.knowledge/guides/` for published user-facing
  guidance, previously `.documentation/`'s job), and `.archive/`. Every live script, quickstart
  step, command template, and site page that still created, preserved, or reconciled into
  `.documentation/` is updated; `.knowledge/index.json`'s `roots` list reflects the change.
  Quickstart Step 11.7 is simplified from a full `.documentation/` reconciliation workflow down to
  a lightweight `.knowledge/index.json` health check, since nothing writes there anymore.
- Stale references to the already-removed `devspark_cli` package and the `.devspark.work/runs/`
  telemetry work-product (tied to that same removed CLI) scrubbed from `AGENTS.md`,
  `copilot-instructions.md`, the constitution, and `.markdownlint-cli2.jsonc`.

### Changed

- **`/devspark.release` now sweeps `pr-review/`, `audit/`, `metrics/`, and `telemetry/` into the
  release's `.archive/{YYYY-MM-DD}/` folder unconditionally** — no age or count check, unlike
  specs/quickfixes' `Complete`-status gate. Dropped timed/counted retention (`keepCount`/
  `maxAgeDays`) from `.knowledge/taxonomy-registry.json`'s schema entirely; it no longer exists as a
  concept anywhere in the framework. Release output (`metrics.json`, `release-notes.md`) now writes
  directly to `.archive/{YYYY-MM-DD}/release/` and is never staged under `.devspark.work/releases/`.
- `scripts/release-context.py` gained `STRAY_RELEASE_ARTIFACTS` detection (a committed
  `release-context-*.json`/`release-history-*.json` left over from an interrupted prior run) and
  dropped the legacy `.documentation/` scan root and `DOCUMENTATION_ROOT`/`DOCUMENTATION_CHANGED`
  fields.
- `scripts/build_knowledge_index.py` now collects every stale `last_verified` finding across a run
  and reports them together, instead of raising on the first one found.
- The quickfix record's `## Completion` block (`Completed`, `Commit`) is now actually populated by
  `/devspark.implement`'s Finalize Every Route, and `PR` by `/devspark.create-pr` once the PR opens
  — previously neither field was ever wired to anything despite the record template promising it.

## [6.0.0] - 2026-09-05

### Changed

- **`/devspark.harvest` and its `/devspark.archive` alias removed outright; folded into
  `/devspark.release`.** No compatibility redirect was kept — every command/agent/prompt/atomic shim
  file, both cleanup scripts (`harvest.sh`/`harvest.ps1`/`harvest-context.py`), and their contract
  test were deleted. `/devspark.release` is now the **sole** command that ever moves anything from
  `.devspark.work/` into `.archive/{YYYY-MM-DD}/`; it absorbed harvest's work-product retention,
  orphaned-in-flight-state detection, and knowledge-currentness backstop responsibilities.
- **`/devspark.implement` no longer archives anything.** It populates `code_ref`/`knowledge_ref`
  linkage on every task and leaves the spec or quickfix record live in `.devspark.work/` (marked
  `Complete`) so it stays validate-able against code, tests, and knowledge for the rest of the
  sprint — potentially across more than one release window — instead of being swept away the
  moment implementation finishes.
- `scripts/release-context.py` absorbed `harvest-context.py`'s work-product/knowledge-scan helpers
  and gained `SPEC_BUNDLES`, `QUICKFIX_RECORDS`, `RETAINED_WORK_PRODUCTS`, `KNOWLEDGE_FILES`,
  `KNOWLEDGE_HISTORY_NODES`, `KNOWLEDGE_INDEX_CURRENT`, and `PLANNING_REFERENCES` fields.

## [5.2.0] - 2026-08-31

### Added

- **`/devspark.explain` command.** Given a free-text topic or question ("how is X done?"), resolves
  matching `.knowledge/` content (entities, flat docs, governance decisions) via a new dedicated
  context script (`scripts/explain-context.py` + bash/PowerShell wrappers, reusing
  `build_knowledge_index.py`'s frontmatter/git-log logic rather than duplicating it), then verifies
  it against current code and tests using `/devspark.site-audit`'s exact DELTA1/DELTA2/DELTA3/
  DELTA5/KNOW1-4 finding codes, scoped to that one topic instead of repo-wide. Unlike `site-audit`
  and `harvest`, which only ever report a gap, `/devspark.explain` is the first command that both
  detects *and remediates* knowledge drift in the same interactive run: it answers the question in
  human prose with `path:line` citations, then — after one explicit confirmation — writes the
  corrected doc or drafts a brand-new one for genuinely undocumented functionality and regenerates
  the knowledge index. Every run also emits a fenced `## Agent Summary` JSON block so the same run
  serves both a human reader and a chaining agent without maintaining two representations that
  could drift apart. Never creates a `.devspark.work/` planning record; a topic that reveals
  genuinely unimplemented behavior routes to `/devspark.specify` instead. Ships with both an agent
  shim (`.github/agents/devspark.explain.agent.md`) and a prompt shim
  (`.github/prompts/devspark.explain.prompt.md`) in the same change — 33 commands, 33 agent files,
  33 prompt files, still one-to-one.
- `.knowledge/governance/devspark-philosophy.md` and `devspark-prompt-mapping.md` updated with
  `/devspark.explain`'s place in the prompt inventory and lifecycle (Validation phase, alongside
  `site-audit`/`harvest`), and the shim-gap tracker bumped to reflect the new one-to-one count.

## [5.1.0] - 2026-08-30

### Added

- **`/devspark.pr-review` §6 (Durable Delta Consistency Validation) is now a stable, ID-tracked
  blocking gate**, not prose guidance. Every check now emits a `PRD{N}-{seq}` finding with its own
  Findings Detail table (mirroring Critical/High constitution findings) and a slot in Immediate
  Actions: `PRD1` code/knowledge contradiction, `PRD2` unsupported knowledge claim introduced by
  the diff, `PRD3` insufficient test depth, `PRD4` planning-identifier leak, and new `PRD5`
  — knowledge completeness for the diff (architecturally significant new/changed behavior that
  touches no `.knowledge/` node at all, neither existing nor new). Closes a gap where this section
  only produced a single PASS/FAIL summary line with no per-finding tracking, unlike every other
  review dimension. Named `PRD` (not `DELTA`) specifically to avoid colliding with
  `/devspark.site-audit`'s own repo-wide `DELTA{N}`/`KNOW{N}` IDs, which check the same class of
  thing at a different scope. Also fixed malformed YAML frontmatter (`handoffs:` indentation) in
  `pr-review.md` found while editing the same file.
- **Closed the remaining `.knowledge/` lifecycle-ownership gaps identified while auditing which
  commands are responsible for auditing/creating `.knowledge/*`:**
  - `/devspark.release` now requires a current `/devspark.site-audit` knowledge-completeness result
    (`KNOW1`–`KNOW6` clean) for the release window before sealing, alongside its existing
    `.knowledge/index.json`-currency check — the same two-checkpoint pattern already used for
    verify-before-archive.
  - `/devspark.verify` now records a `test_ref: <path>::<test name>` pointer alongside any mode that
    passed via a named, committed test — the citable evidence `/devspark.implement`'s
    evidence-preference bullet needs to record `verified_by: execution` on a `.knowledge/` node,
    captured where the proof actually ran instead of reconstructed later.
  - `/devspark.upgrade`'s legacy-migration guidance now mentions `/devspark.migrate-knowledge-entities`
    as a separate, optional follow-up after the four-root migration (previously only the quickstart
    guides said this — the upgrade command template itself never did).
  - `/devspark.specify` gained an "Early Knowledge Grounding" step: a cheap, best-effort check for
    whether the feature area already has a `.knowledge/` node or decision that the request might
    contradict, surfaced before drafting instead of only being caught later by `/devspark.analyze`'s
    `context_resolved` hard gate.
  - Confirmed `/devspark.taskstoissues` needs no change — it is an intentionally deprecated stub
    (v4 removed task export entirely) and was never a real gap.
- **`/devspark.migrate-knowledge-entities` command.** Closes a gap where
  `scripts/migrate-knowledge-to-entities.py` (the opt-in flat-docs → entity-ontology migration)
  had no slash-command wrapper and was never mentioned by any quickstart guide's major-version
  migration guard — the four-root migration (`migrate-to-four-root.py`) moves directories but
  never offers the separate, still-necessary content migration into `.knowledge/entities/<id>/`.
  The new command drives dry-run, confirmation, `git mv` apply, and a `build_knowledge_index.py`
  rebuild, mirroring the existing `migrate-registry` pattern (optional, human-confirmed, never
  run automatically). All 6 quickstart guides' major-version migration guards now mention it as
  a follow-up step; `.knowledge/tooling/developer-guide.md` and the published
  `v3-to-v5-migration.md` / `prompt-lifecycle-mapping.md` guides reference it alongside the
  existing manual-script instructions.
- **`v3-to-v4-migration.md` renamed to `v3-to-v5-migration.md`** and expanded to cover the full
  v3 → v5 journey (four-root migration, entity-ontology adoption, and the v5.0.0 CLI removal /
  archive-instead-of-delete changes), with a new "Initializing `.knowledge/entities/` and
  `.knowledge/ontology/`" section covering both moving existing flat `.knowledge/` docs and
  discovering new entity candidates from `.documentation/` and code.
- **Step 11.7 (Initialize and Reconcile `.knowledge/`) added to all 6 quickstart guides.** Runs on
  every quickstart execution regardless of mode (Fresh Install, Update, Repair, Migration, Already
  Current) — never gated behind the mode banner. Checks whether `.knowledge/entities/` and
  `.knowledge/ontology/coverage.json` are present and current; if not, inventories every file under
  `.documentation/` and classifies each into exactly one bucket: archive (`.archive/{YYYY-MM-DD}/`,
  never deleted), in-process work product (`.devspark.work/<subfolder>/`, per
  `.knowledge/taxonomy-registry.json`), or current knowledge (`.knowledge/`, flat or entity-ontology
  per `.knowledge/tooling/content-lifecycle.md`). Requires explicit confirmation before moving
  anything, uses `git mv` throughout, and rebuilds the index/coverage report at the end.
- **`/devspark.site-audit` gained repo-wide knowledge completeness and knowledge/code
  mapping-accuracy checks (`KNOW1`–`KNOW6`), plus a new `--scope=knowledge` flag.** Previously
  `/devspark.pr-review`'s §6c ontology gap-report gate only evaluated entities a PR's diff touched;
  nothing repo-wide checked `.knowledge/` for structural completeness or verified that `appliesTo`/
  `source_of_truth` references still point at real files. Section 5 of `site-audit.md` now runs
  `build_knowledge_index.py --check` (stale index/coverage = `KNOW1`), reads the full
  `ontology/coverage.json` for every entity (`KNOW2`), confirms every knowledge→code path reference
  still resolves (`KNOW3`), resolves every `relations[].object` and `constrains`/`constrained_by`
  pair (`KNOW4`), and cross-checks `taxonomy-registry.json` classification plus central-module
  coverage gaps (`KNOW5`/`KNOW6`). The Executive Summary report template gained a "Knowledge
  Completeness & Mapping Accuracy" row.

## [5.0.0] - 2026-08-30

### Removed

- **The `devspark-cli` Python package, harness runtime, and CLI-driven aliases/workflows.**
  Removed `src/devspark_cli/` (harness runner, workflow adapters, telemetry, registry/config
  resolution, upgrade helpers) along with `templates/aliases/`, `templates/workflows/`,
  `sample.harness.yaml`, `full-cycle.harness.yaml`, the CLI-only atomic prompts
  (`assign-agent`, `capture-context`, `classify-improvement`, `create-issue`), and the 39
  CLI-coupled test files. The `suggest-improvement` and `full-cycle` flagship flows are
  retired with it (no standalone slash-command equivalent existed). The 30 `/devspark.*`
  slash commands are unaffected — they never depended on the CLI.
- **Quickstart is now the only supported install/upgrade path.** Removed the CLI-assisted
  advanced install/upgrade options from `README.md`, `templates/commands/upgrade.md`, and
  every quickstart guide, along with the `site/src/guides/harness-engineering.md` and
  `site/src/get-started/installation.md` pages. `pyproject.toml` no longer defines an
  installable package (no `[project.scripts]`, no build backend) — it is now dev/test/lint
  tooling configuration only.

### Changed

- **Completed `.devspark.work/` planning artifacts are archived, not deleted.** `/devspark.implement`
  now moves a finished spec, quick-spec, or quickfix record to `.archive/{YYYY-MM-DD}/` (preserving
  its relative path minus the `.devspark.work/` prefix) instead of removing it; `/devspark.harvest`
  does the same for orphaned in-flight bundles and expired work-product retention;
  `/devspark.constitution` and `/devspark.evolve-constitution` archive applied/rejected constitution
  amendment proposals and discovery drafts under `.archive/{YYYY-MM-DD}/governance/`. This preserves
  short-lived planning value between releases even when it hasn't yet landed in a commit. `.knowledge/`
  content is unaffected — it is still corrected in place or deleted, with Git as its sole history.

## [4.1.0] - 2026-08-30

### Added

- **Entity-ontology superset for `.knowledge/`.** Opt-in `.knowledge/entities/<id>/` layout with
  `_entity.yaml` nodes and `layer`-classified docs (architecture/business/integration/operations
  /pattern/plan), each requiring `source_of_truth` (validated to exist) and `last_verified`
  (validated against source commit history). `scripts/build_knowledge_index.py` supersedes
  `scripts/generate-knowledge-index.py` (kept as a deprecated alias) and additionally emits
  `.knowledge/ontology/coverage.json`. Existing flat type-folder knowledge (`architecture/`,
  `governance/`, `reference/`) is unaffected and requires no migration; adopt entities per-domain via
  `scripts/migrate-knowledge-to-entities.py --dry-run`. New authoring guidance lives in
  `.knowledge/tooling/developer-guide.md` and `.knowledge/tooling/content-lifecycle.md`.
- **Governance decisions as current-truth content.** `.knowledge/governance/decisions/<topic>.md`
  (`type: governance-decision`) captures cross-cutting choices as a present-tense claim, keyed by
  domain/topic and edited in place — no creation-order numbering, no "superseded by" chains.
  `constrains` names the entities a decision constrains; each named entity's `_entity.yaml` must
  carry a reciprocal `constrained_by` pointer, both directions validated by
  `scripts/build_knowledge_index.py`. `/devspark.implement`'s finalize step now checks whether a
  delta touches anything an existing decision claims about and corrects it in place before the
  planning bundle is deleted; `/devspark.harvest` flags decisions that have drifted into numbering,
  supersession chains, or stale entity pointers.
- **Context/evidence linkage threaded through the lifecycle.** `/devspark.plan` resolves and pins
  `context_resolved` (entity/decision ids, resolution path, hop count) into the spec package;
  `/devspark.analyze` hard-gates on every entry actually resolving against the current knowledge
  graph; `/devspark.critic` judges whether the resolved set is sufficient for the delta. Generated
  tasks in `/devspark.tasks` carry `code_ref`/`knowledge_ref` placeholders that `/devspark.implement`
  populates as each task completes and never traverses more than one hop past `context_resolved`
  itself; the finalize route now hard-checks every task's linkage before deleting the planning
  bundle ("verify-before-delete"). `/devspark.pr-review` gained an ontology gap-report gate scoped to
  diff-touched entities plus non-blocking warnings for missing evidence `fallback_reason` and
  graph-adjacent contradiction candidates; `/devspark.site-audit` gained a repo-wide evidence-
  accuracy re-run and the same contradiction scan. Closed the two missing shim gaps
  (`devspark.verify`, `devspark.address-pr-review` agent shims) this model depended on.
- **v3 → v4 migration guide** published at `site/src/guides/v3-to-v4-migration.md`, covering the
  four-root mapping, migration steps, and post-migration checks.
- **v4 philosophy and prompt-lifecycle-mapping published to the docs site.** New
  `site/src/why/v4-philosophy.md` and `site/src/guides/prompt-lifecycle-mapping.md` pages carry the
  full current-truth model (three categories, decision discipline, evidence typing, the five
  non-negotiable rules, verify-before-delete, retrieval budget) and the per-command v4 requirements
  table onto the public site, cross-linked from the homepage, "How It Works", and the migration guide.

### Changed

- Quickstarts now identify DevSpark 3.x → 4.x as a major migration, require the four-root
  migration guard before framework refresh, and preserve repositories already using the v4 roots.
- Moved the public DocFX project to `site/`, with authored content under `site/src/` and generated
  output under ignored `site/_site/`; Azure Pipelines now builds and publishes from those paths.
- Disabled local command metrics by default. Metrics require explicit
  `DEVSPARK_METRICS_ENABLED=true` opt-in, and previously tracked metric artifacts were removed.
- Consolidated 14 command prompts that duplicated the "Multi-app support" and "Script Resolution"
  paragraphs verbatim down to a single reference to `command-preamble-contract.md`.

### Fixed

- Corrected the decision→entity field name from a stale `governs:` to the shipped `constrains:` /
  `constrained_by:` pair across the v4 philosophy and prompt-mapping governance docs and two command
  prompts, and rewrote `site/src/get-started/how-it-works.md`'s Knowledge Model section, which had
  fallen out of date by claiming knowledge nodes never encode decisions.

## [4.0.0] - 2026-08-29

### Added

- **Canonical four-root migration.** `scripts/migrate-to-four-root.py` and thin Bash/PowerShell
  wrappers migrate v3 and older repositories without overwriting collisions or creating backup and
  archive trees. Tracked files retain Git rename history; conflicts stop with an actionable report.
- **Current-knowledge ontology and index.** Typed `.knowledge/` nodes, JSON schemas, taxonomy,
  cross-platform index wrappers, and contract tests make current architecture and governance
  machine-readable without preserving lifecycle history.

### Changed

- **Plan Temporarily, Review the Delta.** All 31 `devspark.*` command prompts now treat specs,
  plans, tasks, checklists, and gates as temporary implementation aids under `.devspark.work/`.
  Implementation changes code, tests, current knowledge, and published guidance together, verifies
  the result, and deletes the planning bundle. PR review, release, audit, and maintenance evaluate
  the durable Git delta instead of spec adherence.
- **Four-root ownership boundary.** `.devspark/` is replaceable framework content;
  `.devspark.work/` owns temporary plans, runtime state, configuration, registries, and overrides;
  `.knowledge/` owns current authoritative truth; `.documentation/` owns published user guidance.
  Personal overrides resolve from `.devspark.work/{git-user}/commands/`, and the split multi-app
  registry resolves from `.devspark.work/devspark.registry.json` across Python, Bash, and PowerShell.
- **Packaging, quickstarts, and static publishing** now enforce and document the same
  v4 paths. The raw publishing layout exposes current governance under `.knowledge/governance/`
  and builds a site with no legacy work-root instructions.

### Removed

- Legacy `migrate-to-documentation` implementations, archive recovery, completed-plan retention,
  ADR and rationale-history trees, constitution history, and release-time spec reconstruction.
  Git is the sole history; `.knowledge/` contains current truth only.

## [3.9.0] - 2026-08-26

### Added

- **OKF (Open Knowledge Format) Knowledge Documents (spec 005).** Lifecycle
  scripts now emit a parallel, integrated "knowledge" layer per feature
  alongside their existing machine-readable JSON: markdown documents with
  structured YAML frontmatter, co-located inside each feature's spec folder
  under `knowledge/`. This makes requirement↔task↔gate-evidence traceability
  mechanically checkable without disrupting any consumer of the existing JSON
  contracts. Ships `templates/schemas/okf-knowledge-document.schema.json`, new
  `scripts/{bash,powershell}/validate-knowledge-coverage.*` validators (wired
  into `/devspark.analyze` and `/devspark.critic` as an additive, fail-soft
  coverage pass that skips cleanly when `knowledge/` is absent), shared helper
  additions in `common`, `create-new-feature`, and `setup-plan` scripts, and
  `tests/test_knowledge_document_contract.py`.
- **Genuine Fix Discipline (anti-gaming) guidance across command templates.**
  New §9 + §9.1 intent-cue table in `command-preamble-contract.md` directs
  commands to resolve the *behavioral intent* a check is a proxy for rather
  than reacting to a bare lint/complexity/code-smell metric (a published eval
  measured genuine-fix rates of ~5.6% for bare-metric phrasing vs. ~83% when
  intent was stated first). Referenced from the fix/review commands
  (`/devspark.implement`, `/devspark.quickfix`, `/devspark.pr-review`,
  `/devspark.address-pr-review`) and now also from the finding-*generating*
  gates: `/devspark.critic` and `/devspark.analyze` carry an `intent_cue`
  field in their `findings:` schema and phrase structural-smell findings
  around intent; `/devspark.site-audit` adds an **Intent** field to its
  code-quality findings; `/devspark.verify` adds a Genuine Fix Guard that
  fails a proof showing only that "the tool's number went down" with
  unchanged behavior. Added §9.1 cross-language note (JS/TS, C#, Java
  patterns) and a §9.2 constitution-citation hook so a declared
  intent-over-metrics principle escalates a gamed fix to a constitution
  violation; `/devspark.constitution` now offers such a principle. New
  drift-guard `tests/test_genuine_fix_discipline_contract.py` pins the §9
  heading, the §9.1 table, and the set of commands that must reference it.

## [3.8.0] - 2026-07-29

### Added

- **Quick-Spec and Quickfix implementation routes in `/devspark.implement`.**
  `implement.md` was written entirely for the full-spec route (its Definition
  of Done required every `tasks.md` item checked), so quick-spec and quickfix
  branches had no working `/devspark.implement` path. Two new self-contained
  routes now branch off route detection: the **Quick-Spec Route** drives the
  spec's Action Plan as its task list and flips `Status` Draft → In Progress →
  Complete itself; the **Quickfix Route** drives the quickfix record's
  Validation Checklist and auto-fills its Completion block
  (Completed/Commit/PR), so a separate `/devspark.quickfix complete` run is no
  longer required. Full-spec behavior is unchanged.
- **`quickspec-needs-implement` state in `/devspark.next`.** The router's state
  machine gated quickfix behind a `quickfix-open` state but had no equivalent
  for quick-spec, so a quick-spec branch with an incomplete Action Plan fell
  through every full-spec-gated state and was recommended straight to
  `/devspark.create-pr`, skipping implementation. A new
  `quickspec-needs-implement` state now recommends `/devspark.implement` until
  a quick-spec's `Status` reaches Complete; `IS_FULL_SPEC`/`SPEC_STATUS` are
  also surfaced in the JSON output for debuggability.
- **Lifecycle-parity contract test**
  (`tests/test_lifecycle_parity_contract.py`) regression-proofing symmetric
  quickfix / quick-spec / full-spec support across the command surface.
- **Split multi-app registry file (opt-in).** `.documentation/devspark.registry.json`
  is now the new, preferred home for the multi-app registry
  (`version`/`mode`/`profiles`/`apps`), separate from `devspark.json` (repo
  facts/platform/policy). Detection/read order checks the new split file
  first and falls back to the legacy combined `devspark.json` forever — an
  existing repo with only the legacy file sees zero behavior change. A new
  `/devspark.migrate-registry` command performs
  the (always human-confirmed, never automatic) move.
- **JSON Schemas for both halves of `devspark.json`.**
  `templates/devspark-config.schema.json` (repo facts) and
  `templates/devspark-registry.schema.json` (multi-app registry), wired into
  `templates/vscode-settings.json` for editor autocomplete, and into
  `/devspark.validate-registry` as non-blocking warnings for the repo-facts
  half (previously never checked at all).

### Changed

- **Config-parse failures are loud, not silent.** `Get-DevSparkConfig` /
  `Get-DevSparkUserConfig` (PowerShell) and `get_devspark_config_value` /
  `get_devspark_user_config_value` (Bash) now emit a warning to stderr on a
  malformed `devspark.json`/`devspark.user.json` instead of silently
  returning nothing. The warning never appears in `-Json`/`--json` structured
  output.
- **`/devspark.upgrade` reports a missing `devspark.user.json` gitignore
  exclusion.** Detect-and-report only, consistent with the Ownership
  Boundary — install/upgrade never writes to `.documentation/.gitignore`
  itself.
- **`add_application()` gained a concurrency guard.** Re-checks the registry
  file's bytes immediately before writing and refuses to overwrite a
  concurrent change, asking the caller to retry instead.
- **`--app` is now deprecation-warned (Phase 1 of 2) when unresolvable.**
  Every command template that scopes to a multi-app repo now prints a
  visible warning and falls back to repo-root scope when `--app <id>` isn't
  passed, instead of silently defaulting with no signal. A future,
  separately-dated release will make this a hard error (Phase 2).
- **`DevSparkRegistryStrict` (`extra="forbid"`) applies only to the new
  split `devspark.registry.json`.** The legacy combined-file reader stays
  permissive forever, since current docs recommend co-locating repo-facts
  keys alongside the registry in that file.

### Fixed

- **`plan.md` prerequisite silently broke quick-spec and quickfix routes.**
  `check-prerequisites.{sh,ps1}` unconditionally hard-required `plan.md` with
  no flag guard (unlike `tasks.md`, already gated by `--require-tasks`), so
  every downstream command that called the script failed on routes that never
  produce `plan.md`. The requirement is now opt-in via
  `--require-plan`/`-RequirePlan` (default off); the full-spec-only `tasks` and
  `taskstoissues` commands pass it explicitly to preserve their original
  fail-fast behavior.
- **`critic` / `analyze` / `verify` couldn't find quickfix records.** On a
  quickfix branch (`NNN-fix-<slug>`), `FEATURE_SPEC` pointed at a nonexistent
  `spec.md` instead of the actual record file. `common.{sh,ps1}` now resolves
  `FEATURE_SPEC` to the record file when the feature directory is
  `quickfixes/`; `critic`/`analyze` gain a new `QUICKFIX-ONLY` degradation
  tier (and `analyze`, which previously hard-aborted on any missing artifact,
  now uses the same tiered graceful-degradation table as `critic`); `verify`
  reads `required_gates` from the quickfix record when no `spec.md` exists.
- **`quick-spec-template.md` recommended the wrong next step.** Its
  `recommended_next_step` pointed at `plan`, contradicting quick-spec's
  intent-plus-action-plan-only contract; it now points at `implement`.
- **`/devspark.pr-review` and `/devspark.create-pr` noise on light routes.**
  Quick-spec routes are now exempt from the `tasks.md` HIGH finding, stuck
  Draft status is flagged earlier in create-pr, and create-pr's environment
  checks plus functional/policy-gate test-signal wording are advisory-only.
- **`validate_paths()` is now actually enforced by `/devspark.validate-registry`.**
  Path-existence findings land as non-blocking `warnings` (not errors) for
  this release so an existing repo with a stale/renamed app `path` isn't
  newly broken by the fix.

## [3.5.0] - 2026-07-22

### Added

- **Product Owner TLDR — a required section at the top of every spec.** Every
  generated `spec.md` (full-spec and quick-spec) now opens with a short,
  non-technical `## Product Owner TLDR` that answers, at a high level, **what**
  the spec changes and **why** it matters now. The section is enforced as the
  first required heading for both routes in the shared specification validation
  contract, is authored by the `write-spec` skill, and is covered by a new
  contract test (`tests/test_spec_hardening_contract.py`). This gives product
  owners and non-technical stakeholders an at-a-glance summary without reading
  the full rationale, requirements, and success criteria.
- **Upgrade-path override health checks.** `/devspark.upgrade` (and the
  prompt-first Update Mode) now report three staleness signals so teams can keep
  overrides accurate as stock evolves — all advisory and non-destructive,
  never touching `.documentation/`:
  - **Orphaned overrides** — command overrides (`.devspark.work/commands/`,
    `.documentation/{git-user}/commands/`) and script overrides (both
    `bash/*.sh` and `powershell/*.ps1`) whose matching stock default no longer
    exists under `.devspark/`.
  - **Stale-fork rot markers** — overrides whose content still contains
    pre-DevSpark / legacy markers (`SPECIFY_FEATURE`, `.specify/` paths,
    pre-separation `.documentation/defaults/commands` paths), a reliable
    staleness signal a raw line diff cannot detect.
  - **Missing / stale agent shims** — stock commands added upstream with no
    agent shim yet, and shims left behind for removed/renamed commands.

### Changed

- **Spec-scaffolding scripts hardened (PowerShell + Bash).**
  `create-new-feature` and `setup-plan` now resolve templates through a shared
  fallback chain (`.devspark.work/templates` → `.devspark/templates` →
  `templates`) instead of a single path that silently produced an empty file;
  `create-new-feature` now fails fast when `git checkout -b` fails so specs are
  never scaffolded onto the wrong branch; and the create-new-feature success
  metric no longer reports a hardcoded `full-spec` route it cannot actually
  know.

## [3.4.2] - 2026-07-19

### Fixed

- **Azure publish pipeline `pip-audit` gate failure (`PYSEC-2026-3447`).**
  Updated the publish pipeline to upgrade `setuptools` to `>=83.0.0` before
  running `pip-audit`, remediating the hosted-agent vulnerability finding
  (`setuptools 79.0.1`) that blocked release publication.

## [3.4.1] - 2026-07-19

### Fixed

- **Azure publish pipeline markdownlint failures in `templates/commands/specify.md`.**
  Normalized ordered-list prefixes, list indentation, and blank-line spacing to
  satisfy markdownlint rules (`MD007`, `MD029`, `MD032`, `MD005`) and unblock
  the `Run markdownlint-cli2 (markdown lint gate)` stage in `DevSpark-publish`.

## [3.4.0] - 2026-07-19

### Added

- **Empirical verification gate (`/devspark.verify`).** Added a first-class proof
  command and contract-driven verification modes (`snapshot-neutral`, `golden`,
  `regression-pinned`, `shadow-agreement`, `end-to-end`) so feature routes and
  spec validation can require measurable evidence before PR completion.
- **Structured intake and command preamble contracts.** Added shared intake and
  preamble contract templates to reduce prompt drift and keep route, context,
  and execution metadata consistent across command prompts.
- **Cross-repo dependency metadata in spec templates.** Added `depends_on`,
  `supersedes`, and external-contract tracking fields to improve cross-repository
  planning and validation behavior.
- **Metrics capture and rollup output.** Added best-effort command metrics writes
  and a harvest rollup artifact at
  `.devspark.work/metrics/devspark-metrics-rollup.json` for release and workflow
  observability.

### Changed

- **Route-aware intake expanded.** `/devspark.specify` now supports explicit
  `refactor` and `prompt-change` intents in addition to one-off, quick-spec,
  and full-spec paths, with default verification expectations wired through
  spec validation.
- **Gate sequencing and documentation updated for verify-first evidence.**
  Lifecycle guidance and command catalogs now reflect verify-proof execution
  before PR finalization when verify modes are declared.

### Fixed

- **"Unsupported markdown: list" on the How It Works page.** The lifecycle flowchart's
  Mermaid node labels began with `1.`/`2.`/… numbering, which Mermaid's markdown label
  parser reads as an (unsupported) ordered list — every node rendered as an error string
  instead of a diagram. The flowchart is rebuilt with plain labels grouped into
  Define / Build / Ship-and-Learn phases, matching the homepage diagram's styling.

### Changed

- **Site top navigation reduced from 10 entries to 4** (Home, Get Started, Guides,
  Why DevSpark). Doc pages moved into section folders (`get-started/`, `guides/`,
  `why/`), each with its own `toc.yml`, so the docfx modern template renders a
  left-sidebar secondary navigation with active-page highlight per section. All internal
  links updated repo-wide; the old flat page URLs 301-redirect to their new section
  locations via `staticwebapp.config.json`, so existing bookmarks keep working.

## [3.3.0] - 2026-07-12

### Added

- **`/devspark.commit-audit` context scripts.** The command's frontmatter has referenced
  `commit-audit.sh` / `commit-audit.ps1` since the initial import, but the scripts never
  existed — the command failed at step 1 on every install. Both are now implemented
  (anonymized contributor roles, per-commit change stats, monthly velocity aggregates,
  `report_path`), with parity token checks in `tests/test_script_parity_contract.py`.
- **Harness runtime guardrails.** `HarnessSpec` now accepts an optional `guardrails` block
  (`max_files_changed`, `restricted_paths`, `max_total_lines_changed`) enforced per step by
  the same `AutonomyEnforcer` the workflow runner uses. A violation fails the step, halts
  the run with `failure_reason_code: guardrail_blocked`, and emits `harness.policy.blocked`.
  `full-cycle.harness.yaml` — the spec recommended for `--hands-off` unattended runs —
  previously had **no** guardrails at all; it now declares the same policy as
  `templates/workflows/full-cycle.yaml`.
- **Contract scripts now actually run in CI.** Eleven `tests/test_*_contract.py` files are
  standalone `main()` scripts with no `def test_` functions — pytest collected them but ran
  nothing, so their assertions were silently skipped. `tests/test_contract_scripts.py` now
  executes each in a subprocess. Two had rotted while unenforced and are fixed:
  `test_address_pr_review_contract` (asserted install-layout shims this source repo doesn't
  carry) and `test_hands_off_lifecycle_contract` (copied fixture content from an archived
  `releases/v2.5.0/` tree that no longer exists; now writes inline stubs).
- **Lifecycle sync tests** (`tests/test_full_cycle_sync.py`): the nine-step full-cycle
  lifecycle is declared in two schemas (`full-cycle.harness.yaml` and
  `templates/workflows/full-cycle.yaml`) with nothing tying them together; tests now fail
  when the step sequences or guardrail policies diverge, and when the dogfood version stamp
  falls behind `pyproject.toml`.
- **CI quality gates in `azure-pipelines.yml`**: ruff, atomic-shim drift check,
  `agents-registry.json` schema validation, and markdownlint — ports of the gates that only
  existed in GitHub Actions workflows that never ran (this repo's sole remote is Azure
  DevOps).

### Changed

- **Autonomous guardrails now protect the real CI surface.** `restricted_paths` in both
  full-cycle specs adds `azure-pipelines.yml` and `.azuredevops/**` — previously only
  `.github/workflows/**` was restricted, leaving the pipeline that builds and publishes
  DevSpark editable by autonomous runs.
- **Atomic-shim generators emit the copyright header.** All 28 committed shims carry the
  `source:` line added by the repo-wide copyright pass, but neither generator emitted it —
  `--check` reported 100% drift and a regeneration would have stripped every header. Both
  generators now agree with the committed shims, and the drift gate runs in the Azure
  pipeline.
- **Release tooling moved to `eng/release/`** (`create-release-packages.sh|ps1`,
  `validate_agents_registry.py`) from `.github/workflows/scripts/`. `scripts/**` ships into
  consumer repos via the install index and `/raw` tree, so maintainer-only tooling must not
  live there; nothing under `eng/` is published.
- **Delivery gate preserves the root-cause failure reason.** `evaluate_delivery_gate` no
  longer overwrites an existing `failure_reason_code` (e.g. `guardrail_blocked`) with the
  downstream `delivery_status_unmet` symptom.
- **Dogfood version stamp** (`.devspark/VERSION`) updated from the stale
  `2.3.0` (below the v3.0.0 publish floor) to the current release version; now test-enforced.
- **Public site repositioned around outcomes and evidence instead of objections.** Reworked
  `.documentation/index.md` (homepage) to lead with an outcome-oriented hero, a one-task
  evaluation path, and a "what it does/does not replace" section, moving the objection/rebuttal
  table and closed-loop framing into a renamed "Architecture and Controls" page
  (`.documentation/enterprise.md`) with precise, qualified claims (core prompt-first workflow
  vs. optional CLI/harness, current public-access status, no unverified security-approval
  claims). Added new pages: `evaluate-one-task.md`, `how-it-works.md`,
  `advanced-capabilities.md`, and `evidence.md` ("Operational Experience"). Updated
  `about.md` with a "Current Status" section and `toc.yml` navigation to match.
- **Operational Experience backed by real git-history data.** Replaced placeholder usage
  claims with numbers pulled directly from two adopter repositories'
  git history (specs, quickfixes, decisions, PR review reports, releases, deployment
  cadence), recorded with method/definition/limitations in
  `.documentation/data/` evidence files,
  and summarized on `.documentation/evidence.md`. `docfx.json` now publishes `data/**` as a
  site resource so those files are linkable from the built site.

### Removed

- **All GitHub Actions workflows and GitHub-hosting conventions.** This repository's only
  remote is Azure DevOps and it publishes exclusively to an Azure Static Web
  App, so `docs.yml`, `lint.yml`, `release.yml`, `tests.yml`, `shim-drift.yml`, the
  GitHub-release helper scripts (`create-github-release`, `get-next-version`,
  `generate-release-notes`, `check-release-exists`, `update-version`), `CODEOWNERS`,
  `BRANCH_PROTECTION.md`, and the GitHub-native issue templates never functioned. The PR
  template moved to `.azuredevops/pull_request_template.md`. `.github/agents/` and
  `.github/prompts/` remain (local GitHub Copilot conventions, host-independent).
- **Third-party site links stripped from published surfaces** per the no-external-linkage
  policy: README agent table and prerequisites de-linked, all `install_url` values in
  `agents-registry.json` nulled (CLI messages now point to the organization-approved
  software channel), and navigational `github.com` links removed from command prompts and
  docs. Functional install commands (gh CLI apt source, Git Credential Manager download)
  are retained.
- **Orphaned script pairs deleted**: `archive-context`, `run-workflow`, and
  `delivery-status-smoke-test` (`.sh`/`.ps1`) were referenced by no command, doc, or CI
  step yet shipped into every consumer install. `migrate-to-documentation` is kept and now
  documented as a standalone migration tool in the new `scripts/README.md`;
  `release-history-context` is kept (invoked by `release-context`).

## [3.2.1] - 2026-07-09

### Fixed

- **pip-audit security gate failure.** Relaxed the dev dependency pin from
  `pytest>=7.0,<9.0` to `pytest>=9.0.3,<10.0` to pick up the fix for
  `PYSEC-2026-1845`. The `v3.2.0` tag and `main` branch builds failed the
  `pip-audit` gate because the previously pinned `pytest` 8.4.2 had a known
  vulnerability, which blocked publishing and left the live manifest at
  `3.1.0`. Full test suite (273 tests) verified passing under pytest 9.0.3.

## [3.2.0] - 2026-07-09

### Added

- **Preview Prompt (trust-but-verify) onboarding step.** All 6 quickstart guides (copilot,
  claudecode, cursor, codex, antigravity, generic) now open with a "Preview Prompt" section
  that lets users see exactly what an agent will do before authorizing any changes: a
  read-it-yourself terminal path (PowerShell + Bash) that prints the guide, manifest install
  list, and raw command-prompt contents, plus a read-only "Preview Prompt Mode" dry-run
  contract for the agent (no writes/deletes until the user explicitly says `proceed`).
- Trust-but-verify messaging added to `quickstart/README.md`, `.documentation/quickstart.md`,
  `.documentation/index.md`, and `.documentation/faq.md`.
- **Quickstart step-numbering parity.** Added the missing "Step 2b: Announce Mode and Preview
  Plan" section to the claudecode, cursor, antigravity, codex, and generic quickstart guides
  (previously copilot-only), and renumbered the codex/generic tail steps so all 6 guides now
  share the identical `0, 1, 2, 2b, 3, 4, 7, [8], 9, 9.5, 10, 11, 12` scheme.
- **CI test and security gates.** `azure-pipelines.yml` now runs `pytest` (with coverage) and
  `pip-audit` before the docs build and packaging steps, closing the gap where the production
  build pipeline shipped without running tests. `pip-audit` in `tests.yml` now fails the build
  on known vulnerabilities instead of swallowing failures. DocFX is pinned to `2.78.3`.
- **New lint jobs.** `lint.yml` gained a `ruff` job (source lint), a `link-check` job (lychee,
  offline markdown link validation), and a `registry-schema` job that validates
  `agents-registry.json` against a new `templates/agents-registry.schema.json` via
  `.github/workflows/scripts/validate_agents_registry.py` (also catches duplicate agent keys).
- **Closed unit-test gaps** for `scope.py`, `resolution.py`, `registry.py`, and `inference.py`
  with 65 new tests across `tests/test_scope_resolution.py`, `test_resolution_chain.py`,
  `test_registry_models.py`, and `test_inference.py`.
- Upper version bounds added to core dependencies in `pyproject.toml` (`typer`, `click`,
  `rich`, `httpx`, `platformdirs`, `readchar`, `truststore`, `pydantic`, `jsonschema`,
  `PyYAML`), and `pytest-cov`, `ruff`, `mypy`, `bandit` added to the `dev` extras.

### Fixed

- Broken link in `.documentation/architecture/review-stage-divergence.md` to a stale archived
  spec.
- Orphaned `dogfooding.md` added to `.documentation/toc.yml` navigation.
- Agent count in `faq.md` corrected (17+ → 18+) to match the registry.
- Fixed the closed-loop Mermaid diagram on the site home page (subgraph title text was
  overlapping the first node); added per-node icons and theme-matching styling.
- Removed unused `run_command()` in `_utils.py` — dead code carrying an unexercised
  `shell=True` capability, eliminating 2 Bandit High-severity findings outright.
- `hashlib.sha1()` in `runner/autonomy.py` now passes `usedforsecurity=False` (it computes a
  non-cryptographic file checksum). Added `# nosec B602` markers to the two already-justified,
  repo-trusted `shell=True` subprocess calls in `harness/validation.py`.
- Cleaned up remaining `ruff` findings across `src/devspark_cli` (unused imports/variables,
  dead f-strings, multi-statement lines, an ambiguous variable name, and one dead-code branch
  in `resolution.py`'s `detect_app_json_weakening`). Bandit High/Medium findings: 5 → 0.

## [3.1.0] - 2026-07-02

### Added

- **Requirement↔task traceability directive (`Implements: FR-###`).** Tasks now carry a
  trailing `(Implements: FR-001, FR-003)` naming the functional requirement ID(s) from
  `spec.md` that each task satisfies. `/devspark.tasks` emits the directive, the
  `spec-template` documents each `FR-###` as a stable traceability anchor, and
  `/devspark.analyze` treats the explicit directive as authoritative (falling back to
  keyword inference only when absent). Adds a **traceability-hallucination** check
  (CRITICAL): any task referencing an `FR-###` not defined in `spec.md` is flagged.
  Fully additive and backward compatible — existing specs/tasks without the directive
  still parse. Delivers audit-grade spec→task coverage without new commands or scripts.

### Changed

- **Upgrade/init/install now points to the canonical quickstart guide.** Every
  "upgrade later"/maintenance pointer across the six quickstart guides,
  `templates/commands/upgrade.md`, `README.md`, `quickstart/README.md`,
  `.documentation/upgrade.md`, `.documentation/implementation-lifecycle.md`, and
  `templates/commands/site-audit.md` now directs agents to the manifest-driven
  quickstart (Update Mode) instead of the standalone `raw/templates/commands/upgrade.md`
  prompt — a single canonical entrypoint that refreshes `.devspark/` and preserves
  `.documentation/`.

### Fixed

- **Update-source lockdown.** Neutralized the leftover public-DevSpark community
  extensions catalog (`.documentation/extensions/`) that pointed `download_url`/repository
  links at a public GitHub repo; the catalog is now Make-Bold-only with an explicit
  `source_policy`. Once installed, all DevSpark content and updates resolve
  exclusively to `https://dev.makeboldspark.com`.

## [3.0.1] - 2026-06-29

### Added

- **Manifest-driven prompt-first install.** `dist/manifest.json` now publishes the
  canonical install set (`install` — every `{source, dest}` a clean install must place),
  the `.devspark/` root allowlist (`devspark_root`), and the fetch base (`raw_base`).
  All six quickstart guides replay this list instead of hardcoded file tables, so the
  agent never guesses what to install and a prompt-first install matches the CLI template
  package exactly (closing the prior prompt-first vs. zip divergence).
- **`.devspark/` prune step** in every quickstart removes non-canonical / legacy
  (public-DevSpark) leftovers using `manifest.devspark_root`.
- **Public DevSpark → DevSpark migration detection** in the version-stamp helpers.
- **Live version** surfaced from `/dist/manifest.json` across docs and guides (no more
  hardcoded versions in content); the signed-in user now appears as a "logged in" chip
  in the docs header.
- **Source/copyright attribution headers** on all source files (Python, PowerShell, Bash,
  templates, quickstarts, root docs, and the pipeline) so every document is traceable to
  DevSpark.

### Fixed

- **Stale-version caching defeated** across the CLI, web, and guides: `/raw/*` is now served
  `no-store, no-cache, must-revalidate`; the quickstarts force an uncached terminal fetch
  (cache-busted) of `manifest.json`, so installs no longer pick up an old version.
- **Markdown lint is clean** (markdownlint-cli2: 0 errors across the repo); `.venv` and
  `node_modules` are ignored.

### Changed

- Enforce the **v3.0.0 release floor** and purge v2.x from the published version history.
- Code files use ASCII attribution (`(c)` / `-`) while markdown keeps the rendered glyphs —
  avoids PSScriptAnalyzer `PSUseBOMForUnicodeEncodedFile`, Windows PowerShell mojibake, and
  BOM-broken `.sh` shebangs.

## [3.0.0] - 2026-06-29

### Changed

- **DevSpark v3.0.0 — first Make Bold Solutions release.** The version reset marked a major
  transition in the supported workflow and distribution. Installs identify the product through a
  `product: DevSpark` marker in `.devspark/VERSION`.
- The original distribution used a Make Bold Solutions build pipeline and the
  `https://dev.makeboldspark.com` site for documentation, release packages, and `/raw` files.

### Added

- Initial Make Bold Solutions internal release of DevSpark.
