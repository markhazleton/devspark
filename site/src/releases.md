# Release Notes

Full per-version detail is in the [CHANGELOG](https://github.com/MarkHazleton/DevSpark/blob/main/CHANGELOG.md). This page summarizes the current line. To adopt a release, run your agent's [quickstart](get-started/quickstart.md) in Update Mode; see [Upgrade](get-started/upgrade.md).

## 9.5.0: 2026-11-04

Optional roadmap planning gives teams a place to record product direction and right-sized Prospective Specs without adding a delivery stage or gate.

- **Plan direction.** `/devspark-roadmap` creates and maintains a roadmap, reviews dependencies and future health, and compares delivery evidence with the intended outcomes.
- **Keep delivery explicit.** `/devspark-specify` reads a Prospective Spec only when you name it. `/devspark-release` can archive resolved items only with your agreement; roadmap problems never block a release.
- **Knowledge integrity.** Generated DocFX `_site` output is not reported as a second Knowledge root.
- **Install and upgrade.** Run your agent's [quickstart](get-started/quickstart.md) in Update Mode. No migration is needed.

## 9.4.1: 2026-11-01

An upgraded install now matches a fresh one.

- **`.devspark/` matches the manifest.** Update and Repair now remove any file under `.devspark/defaults/`, `.devspark/templates/` and `.devspark/scripts/` that the release manifest does not list, so files a release dropped or renamed no longer linger. Customizations in `.devspark.work/`, and everything in `.knowledge/` and `.archive/`, are never touched.
- **Bash quickstart on Windows.** With a native Windows `jq`, the Bash steps could delete the installed framework, write misnamed files and report every file missing. They now work. The PowerShell steps were not affected.
- **Install and upgrade.** Run your agent's [quickstart](get-started/quickstart.md) in Update Mode. See [Upgrading to 9.4.1](get-started/upgrade.md#upgrading-to-941).

## 9.4.0: 2026-10-31

**One Flow. Assurance as Needed. Deliver Software.** Every change now follows one path: understand, implement and verify, deliver. There is no quickfix, quick-spec or full-spec route to choose.

- **What changed.** `/devspark-specify` starts new work on a `NNN-work-*` branch with no route question and no planning file. `/devspark-next` resumes it in a later session from Git and an optional `work.md` note. `/devspark-implement` changes code, tests and Knowledge together, `/devspark-verify` reports what was proven, and `/devspark-create-pr` delivers.
- **Planning and assurance on demand.** A plan, a task list, `/devspark-analyze`, `/devspark-critic` or Judge runs only when a specific uncertainty, coordination need or risk justifies it. None of them is a stage, adds a gate or triggers another.
- **Evidence-based delivery.** `/devspark-next` and `/devspark-create-pr` read the same lifecycle check. Delivery is refused while a required obligation declared in `work.md` is unchecked, or is checked without its authority and a traceable evidence or decision reference. A recorded reference is not proof that the approval behind it is authentic. See [Assurance as needed](get-started/how-it-works.md#assurance-as-needed).
- **Why it matters.** Small changes no longer pay for a full-spec ceremony, and large ones gain assurance where the risk actually is. Code, tests and current Knowledge remain the durable outcomes.
- **Install and upgrade.** Run your agent's [quickstart](get-started/quickstart.md), in Update Mode for an existing install. No migration is needed: existing v9.3 full-spec and quick-spec bundles and quickfix records continue on their recorded route.
- **Behavior changes for automation.** The `create-new-feature` scripts are removed; `new-branch` accepts only `work` and `fix`. `create-pr.ps1` create and update mode now exit `1` on a refusal or failure, as `create-pr.sh` already did. See [Upgrading to 9.4](get-started/upgrade.md#upgrading-to-94).
- **Known limitations.** Policy kept only outside the repository is not mechanically enforced. The quickstart installs the latest release only, and older releases' packages are not hosted after a newer release deploys.

## 9.3.0: 2026-10-17

Simplifies planning, PR review and Knowledge upkeep, and removes bookkeeping that never caught a defect.

- **Reuse before building.** Planning looks for the closest existing implementation first and records it, and tasks follow the change surface instead of fixed phases. Critic flags a new mechanism when a closer existing one exists.
- **Evidence-first PR review.** A test run is recorded once as a small evidence record. `/devspark-pr-review` reuses valid evidence for the current commit and environment instead of re-running the same tests, and still runs them when evidence is missing, stale or a repository policy requires independent execution.
- **Knowledge without bureaucracy.** Per-requirement Knowledge stubs, the coverage validator, `code_ref` / `knowledge_ref` task fields, mandatory regeneration of `index.json` / `coverage.json`, and blocking on a `last_verified` date are gone. Knowledge is checked by content and by whether it builds. Curated Knowledge and graph discovery are unchanged.
- **No migration needed.** Older artifacts stay readable. See [Upgrade](get-started/upgrade.md#upgrading-to-93).

## 9.2.0: 2026-10-15

Strengthens PR review and makes release archival dependable.

- **PR review finding closeout.** Each finding has one canonical state, and reviews are updated in place by `/devspark-address-pr-review`. Severity and blocking are separate. Independent-reviewer verification of this flow has not yet been run.
- **Architectural Fitness and Knowledge Strength.** `/devspark-pr-review` weighs coupling, responsibilities, fragile state and the next foreseeable change, and cites the Knowledge owners and invariants that apply, flagging stale or missing Knowledge.
- **Code First quickfix.** `/devspark-quickfix` can finalize a change that already exists without a prior spec.
- **Reliable release archival.** `/devspark-release` archives completed specs, quickfixes and work products with a journaled script that never overwrites archived files and reports anything ambiguous for a decision. A classifier bug that hid completed specs from archiving is fixed.

## 9.1.0: 2026-10-12

Builds on DevSpark 9.0 by introducing lean specification shift-left validation, delta-oriented development guidance, lifecycle separation of specification from product release, and engineering-judgment hardening.

- **Lean Shift-Left Constitutional Validation.** Specification and Clarify stages incorporate early constitutional conflict detection to identify contradictions before planning and task decomposition.
- **Delta-Oriented Development Guidance.** Specifications are treated as bounded hypotheses about the next valuable change to working software rather than exhaustive system blueprints. Authoring focuses on the intended delta and leaves software easy to change again.
- **Specification and Release Separation.** Clear lifecycle boundary separating feature completion from product release and distribution. A spec delivers a releasable change through implementation, PR review, and verification closeout, without depending on version tags or package deployment.
- **Engineering-Judgment Hardening.** Planning evaluates existing ownership and integration boundaries before widespread call-site wiring; Implementation permits safe contract-preserving simplification without redefining the feature contract; PR Review challenges accidental complexity while enforcing that dropping validation or altering exception behavior is not an acceptable shortcut.

## 9.0.0: 2026-10-11

A breaking release: one slash-command convention and one Copilot installation format. Every skill is invoked with a `/devspark-<command>` slash command, and GitHub Copilot receives all 38 skills as native Agent Skills. The dotted 8.x form is retired with no aliases or compatibility mode.

- **Hyphenated Agent Skills.** Copilot installs `.github/skills/devspark-<command>/SKILL.md`; other agents install entry points with the same hyphenated names in their own platform format. Copilot prompt and custom-agent entry-point files are no longer distributed; the skill prompt instructions remain.
- **A safe upgrade from 8.x.** The upgrade lists the 8.x entry points it will retire and asks once. Unmodified ones are deleted, edited ones are preserved in `.devspark.work/migration/8.x-entry-points/`, and conflicts are reported, never overwritten. Team and developer customizations are untouched, and the developer, team, default precedence is unchanged. See [Upgrading from 8.x](get-started/upgrade.md#upgrading-from-8x).
- **Implementation complete means ready to merge and deploy.** A verification obligation can be deferred as post-deploy with an owner and a real tracking record. It stays outstanding until deployed evidence exists and does not block implementation closeout or the pull request; pre-merge safety and compliance requirements still block.

## 8.3.0: 2026-10-10

Keeps Plan and Tasks current with their upstream artifacts and adds one branch-sync skill. No new planning stage, gate, or state store is introduced.

- **Freshness follows both planning edges.** Plan records the spec fingerprint it consumed, and Tasks records its Plan fingerprint. Review state reports each edge as `current`, `stale`, or `unknown`; legacy artifacts without a fingerprint remain non-blocking.
- **A stale edge has an owner.** `/devspark-next` routes stale Plan or Tasks content to reconciliation. Pending decisions, Judge stops, and review invalidation still take precedence. Before Judge, rerunning Plan reconciles the draft; after Judge, revisions remain Judge-driven. Tasks can restamp without rewriting when its projection remains coherent.
- **Branch sync is script-first.** `/devspark-merge-from-main` fetches and merges remote `main`, reports conflict hunks for the agent, and verifies their resolution before committing.
- **PR reviews scale to risk.** The complete changed-file set determines review-depth floors and short, standard, or full report forms. Deterministic validation checks report consistency; calibration compares recorded outcomes by producer version.
- **Explain separates discovery from action.** A requested Knowledge update and a saved trace each need their own approval. Confirmed code defects route to Quickfix; missing behavior routes to Specify.

## 8.2.0: 2026-10-08

Makes the spec the source of truth for the skills that read it, and makes Tests a durable pillar. It adds no skill, stage, or gate, and Planning Review and Judge are unchanged.

- **Specs are consumed by purpose.** Clarify, Plan, and Analyze read the spec through one consumption map. Only requirements and success criteria authorize plan work; constraints shape the design; context informs it and never becomes scope.
- **Plans can't quietly change what was declared.** Clarify applies each answer to every spec element it affects and records confirmed invariants, constraints, and accepted limitations. Analyze reports, without redesigning, a Plan that contradicts a recorded decision or changes declared behavior.
- **Acceptance planning is optional and conditional.** When independent acceptance validation is warranted, Plan creates one ephemeral `qa-acceptance.md` of Given/When/Then scenarios, each with a regression disposition (`add`, `update`, `retire`, or `none`). Analyze, Critic, Implement, and PR Review use it through their existing roles.
- **Tests are a durable pillar.** Every behavior change considers its Tests impact, and the regression baseline is curated, not only accumulated. Post-deployment QA stays outside spec completion.
- **A simpler public site.** One How It Works page and an interactive route explorer on the home page.

## 8.1.0: 2026-10-05

Stabilizes the 8.0 lifecycle. It adds no skill, stage, gate, or state store; it makes the existing lifecycle stay valid, recover from a stop, and review honestly.

- **A planning decision stays valid.** Task checkboxes, spec status, and implementation notes no longer invalidate a Planning Review; a changed requirement, design, or task definition still does. `/devspark-next` is directional after `PROCEED`, and `setup-plan` no longer overwrites an existing Plan.
- **A stop has an owner.** A Judge `STOP` is recovered through whoever owns the correction (Plan, then Tasks, then a focused Planning Review). Tasks operationalize the Plan and never expand scope silently. `/devspark-address-pr-review --auto` acts only on open critical, high, or blocking findings.
- **Planning costs less.** Research, data model, contracts, and quickstart exist only when a change justifies them. The shared prompt preamble loads only what each skill uses, and `explain-context --files` maps changed files to the Knowledge that applies.
- **Create PR is the readiness boundary.** It checks committed-state Knowledge against the exact commit it submits and blocks on index drift, a build failure, or a stale entity the PR touches.
- **PR Review is a better independent reviewer.** A concern is a candidate until it passes a legitimacy check; findings are attributed as introduced, exposed, or pre-existing; and `REQUEST CHANGES` must trace to a validated blocking finding.

## 8.0.0: 2026-10-04

Changes what happens to discovered work: a finding is evidence, not automatically work.

- `/devspark-planning-review` runs Analyze, Critic when a change-shape signal applies, and Judge, and returns one decision: `PROCEED`, `CONDITIONAL`, or `STOP`.
- A Judge phase decides which findings belong in the current change, and a Minimum Sufficient Change doctrine pushes back on complexity that assurance itself adds.

See [Planning Review](guides/planning-review.md).

## 7.8.0: 2026-10-01

Makes framework judgments explicit, bounded, and attributable.

- Knowledge artifacts declare a **form** and a **role** instead of one conflated type.
- Each assurance capability (Analyze, Critic, Verify, PR Review) owns a single question and an explicit "does not own" list.
- Closeout defines when a route may finish, with a convergence rule and four finding classifications.
- Every artifact records the framework version that produced it.

## Earlier releases

7.x added context projection, knowledge drift detection, and the knowledge ontology. 5.x and 6.x introduced the four-root layout and the knowledge entity model. 3.x and 4.x established the manifest-driven install, multi-app registry, and lifecycle parity across quickfix, quick-spec, and full-spec routes. All of it is in the [CHANGELOG](https://github.com/MarkHazleton/DevSpark/blob/main/CHANGELOG.md).
