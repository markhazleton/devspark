# DevSpark Current-Truth Philosophy

## Purpose

DevSpark turns an externally motivated request into a verified change without
letting temporary planning artifacts become permanent product documentation.
Every workflow must remain traceable to a user need, business request,
operational problem, or external constraint. The framework does not invent work
merely because a technique or feature is interesting.

The active lifecycle narrows uncertainty in deliberate stages:

```text
request
  -> specify
  -> clarify when required
  -> plan
  -> tasks
  -> required checklist, analyze, and critic gates
  -> implement
  -> focused verification when needed
  -> pull request and review
  -> merge
  -> release
```

`/devspark.next` may be used at any point to inspect current repository state
and recommend one next action. Release remains a separate, human-triggered event
and is never appended automatically after merge.

## Repository truth model

The maintained repository describes what is true now:

| Root | Ownership | Content |
|---|---|---|
| `.devspark/` | Framework | Installed stock prompts, templates, scripts, and version metadata |
| `.knowledge/` | Repository | Current entities, governance, decisions, ontology output, and overrides |
| `.devspark.work/` | Workflow | Temporary specs, plans, tasks, gates, reviews, audits, and release candidates |
| Source and tests | Product | Current executable behavior and its verification |

Committed change records belong to Git. Temporary workflow artifacts are not
promoted into `.knowledge`, and permanent source or knowledge never points back
to `.devspark.work`.

## Current knowledge and governance

Durable content answers one of three questions:

| Category | Question | Update rule |
|---|---|---|
| Entity knowledge | What is true now? | Edit the current entity documents in place |
| Constitution | What rules govern all work? | Amend the current constitution explicitly |
| Decisions | What choice currently governs a topic, and why? | Keep one current decision file per domain or topic |

Decisions live under `.knowledge/governance/decisions/`. A decision declares
the entities it governs through `governs`. Generated entity metadata exposes
the inverse `constrained_by` relationship in `_derived.yaml`; authors do not
edit that generated field directly.

An entity is self-orienting: its metadata shows whether governance constrains
it, while the shared decision document remains the single source for the
rationale.

## Evidence contract

Every knowledge entity and governance decision cites evidence that can be
checked against the repository:

- `verified_by: execution` identifies a test or deterministic check that can be
  run directly.
- `verified_by: inspection` identifies code that must be read and evaluated.
- Inspection evidence records `test_attempted` and `fallback_reason` when an
  executable test is not practical.

```yaml
evidence:
  - type: test
    ref: tests/Auth/TokenRefreshTests.cs::RefreshesBeforeExpiry
    verified_by: execution
  - type: code
    ref: src/Auth/TokenService.cs::RefreshToken
    verified_by: inspection
    test_attempted: true
    fallback_reason: "requires live token expiry timing"
```

Missing evidence is a strong warning surfaced by review and audit; it does not
block normal work. Inspection evidence without a meaningful fallback reason is
also a strong warning. Agents must report the gap clearly and must not present
an unsupported claim as verified.

## Work-package contract

Specs, plans, tasks, checklists, and gate reports are temporary work-package
content. They remain under `.devspark.work/` throughout implementation, focused
verification, pull-request review, and merge.

Every implementation task records where its result landed:

```yaml
- id: task_003
  description: "Add token refresh retry logic"
  status: complete
  code_ref: src/Auth/TokenService.cs::RefreshToken
  test_ref: tests/Auth/TokenRefreshTests.cs::RefreshesBeforeExpiry
  knowledge_ref: .knowledge/entities/token-service/architecture.md
  governance_ref: n/a — no governance change
```

Each reference must resolve, or use `n/a — <reason>` when the category does not
apply. These links point from temporary work to permanent truth. `test_ref` and
`governance_ref` are work-package linkage fields only: they are recorded in
`.devspark.work` spec-related documents and are never persisted as linkage
metadata in code, tests, entity documents, or governance files. Permanent code,
tests, entity documents, and governance files never reference package names,
spec IDs, task IDs, plan paths, review threads, or archive paths.

## Retrieval contract

Design and implementation use different retrieval budgets:

- Specify, plan, and tasks resolve relevant knowledge and governance through
  bounded multi-hop traversal and record the result as `context_resolved` in the
  work package.
- Analyze verifies that every recorded entity and relation resolves against the
  current ontology.
- Critic judges whether the resolved context is sufficient for the proposed
  change.
- Implement consumes the resolved context and limits additional traversal to
  one hop unless it reports an explicit context gap.

This keeps discovery and design judgment before deterministic implementation.

## Assimilation and validation

Implementation applies one delta to code, tests, and knowledge in the same
pass. It also updates governance when the change affects a governing rule or
decision and fills the task linkage fields.

Pull-request review is the primary assimilation checkpoint. It validates:

- changed behavior against requirements and tests;
- changed knowledge against the code it describes;
- ontology and evidence integrity for touched entities;
- completed task linkage;
- the absence of permanent references to temporary artifacts.

`/devspark.verify` runs focused behavioral and evidence checks without changing
task state or archiving work. `/devspark.site-audit` applies the same
current-truth discipline across the repository. `/devspark.explain` applies it
to one topic and proposes knowledge corrections only after confirmation.

## Release and archive boundary

`/devspark.release` is the only command allowed to write to `.archive/`.
Implementation, verification, PR review, audits, quickstart, and navigation
leave work packages in `.devspark.work/`.

A package is release-eligible only when:

- its status and every task are complete;
- code, test, knowledge, and governance linkages resolve or carry explained
  `n/a` values;
- referenced tests pass;
- knowledge and decision evidence status is reported, with missing evidence
  surfaced as a strong warning rather than an automatic blocker;
- generated ontology output is current;
- permanent content contains no reference to temporary work or archive paths.

Release moves each eligible package intact to
`.archive/YYYY-MM-DD/<topic>/`. Ineligible packages remain unchanged in
`.devspark.work/` with explicit blockers. Release notes are derived from Git,
merged pull requests, and current truth—not from archive contents.

`.archive/` is a human-only recovery buffer outside the DevSpark retrieval
model. No DevSpark command reads, lists, enumerates, globs, or summarizes it.
Humans decide when its contents can be deleted.

## Prompt and script boundary

DevSpark has no standalone command-line application. Quickstart prompts are the
only install, upgrade, and repair interface.

Prompts own judgment, lifecycle routing, and repository mutations. Helper
scripts gather or transform deterministic context for one prompt invocation.
The read-only `next-context` helper is an explicit navigator: it reduces current
Git, artifact, gate, and PR state to one recommendation but performs no
mutation. It does not create a general DevSpark command dispatcher.

## Non-negotiable rules

1. Work begins from an externally motivated request.
2. Permanent source and current truth never reference temporary lifecycle
   artifacts or archive paths.
3. Every knowledge and governance claim has checkable evidence.
4. Each governance topic has one current decision file.
5. Implement updates code, tests, knowledge, governance when applicable, and
   task linkage together.
6. Verification does not archive.
7. Release is the sole archive writer.
8. No DevSpark command reads `.archive/`.
9. Install, upgrade, and repair remain quickstart-only operations.
