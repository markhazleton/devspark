# Release Notes

Full per-version detail is in the [CHANGELOG](https://github.com/MarkHazleton/DevSpark/blob/main/CHANGELOG.md). This page summarizes the current line. To adopt a release, run your agent's [quickstart](get-started/quickstart.md) in Update Mode; see [Upgrade](get-started/upgrade.md).

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
