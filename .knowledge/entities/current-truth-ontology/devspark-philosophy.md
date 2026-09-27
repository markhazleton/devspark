---
aliases:
- current truth
- plan temporarily review the delta
- ephemeral spec
source_of_truth:
- scripts/build_knowledge_index.py
- templates/schemas/entity-node.schema.json
- templates/schemas/knowledge-node.schema.json
- templates/commands/release.md
last_verified: '2026-09-26'
---
# DevSpark Philosophy & Guide: Plan Temporarily, Review the Delta

## The core shift

A spec is not a record. A spec is a **temporary definition of a delta** — the
change we intend to make to our code and to our knowledge. It exists only to
produce that delta correctly. Once the delta has landed — code changed,
knowledge updated, governance updated if affected — the spec has completed
its purpose and is archived out of `.devspark.work/` into `.archive/{YYYY-MM-DD}/`. It is never
referenced again, by code, by knowledge, or by an agent, and nothing about it influences current
behavior once archived — its content is retained only as an inert historical copy, not as active
planning state.

This is a stronger claim than "we choose not to keep spec history in active view." The spec was
never meant to be *active* history in the first place — once archived, it is inert. There is no
spec-vs-code drift to manage, because nothing in the active repository state persists that could
drift — and, as established below, there is no such thing as "cross-spec drift" either, because
archived specs don't have enough identity to have interacted with one another. What's left to check is always synchronic:
does the current state hold together, never "did these two past changes
conflict."

## The governing principle: current truth, not lifecycle history

The repository reflects **what is true now** — current code, current
knowledge, current governance. Historical content ("how we used to do
this") does not live in the repo. It doesn't help an agent execute today's
task; at best it's noise, at worst it actively misleads an agent into
thinking a rejected approach is still valid.

History isn't deleted from existence — it lives in Git. Version control is
the *only* place "what we used to do" is recoverable. Nothing in the
day-to-day repo structure exists to serve that need.

## Three categories of "current truth," not one

Everything durable in the system answers one of three different questions.
Confusing these categories is what produces the ADR/spec/knowledge muddle:

| Category | Question it answers | Who mainly needs it | Change model |
|---|---|---|---|
| **`.knowledge`** (entities) | What is true now? | Agent, to act correctly today | Mutated in place |
| **Governance: Constitution** | What are the rules of the game? | Agent and human, rarely changes | Mutated in place, amended explicitly |
| **Governance: Decisions** | What did we choose, and why not the alternatives? | Human, revisiting a choice; agent, checking a constraint | Mutated in place |

Governance — the Constitution and decisions — lives *inside* the knowledge
container as a distinct subfolder, not as a fourth, separate thing. All
three categories are current-state documents. None is an archive. They
differ in content, not in lifecycle discipline.

## Decisions (ADRs) are current governance, not history

An ADR is not "here's everything we tried." It is "here is what we do, and
here is why we don't do the alternatives" — as a present-tense claim.

- When the reasoning behind a decision changes, **the ADR is edited in
  place.** A new ADR does not take over for it. There is no chain of
  "decision 1, revisited in decision 2, revisited again in decision 3" —
  exactly one current file may exist per topic at any time.
- Decisions are keyed by **domain/topic**
  (`governance/decisions/auth-strategy.md`), never by sequential creation
  order. Sequential numbering is a historical-tracking device baked
  directly into the naming convention and contradicts current-truth
  discipline on its face.
- If a decision becomes moot entirely (the subsystem it governed no longer
  exists), it is deleted — not archived. Git still has it.

## Decisions live in governance, not inside entities

Entities are **complete and autonomous**: an agent working on one entity
should not need to traverse governance separately to act correctly on it.
That argues for keeping entity content — dev guide, business overview —
free of governance material.

But most real decisions are cross-cutting by nature — they constrain
multiple entities, or the framework itself — so they don't belong inside
any single entity's folder either. This is domain-driven design's oldest
unresolved tension: a bounded context gives local autonomy but never tells
you where the cross-cutting seams go. Concerns that are true across
contexts end up either duplicated per-context or hoisted into a shared
kernel, and human teams lose track of shared-kernel dependencies because no
one person reads the whole system before every change.

The mechanism that resolves this without recreating the human failure mode:
a decision declares which entities it constrains (`constrains:`), and each
constrained entity carries a lightweight pointer back
(`constrained_by:`) in its own metadata. The entity stays complete in the
sense that the *existence* of a constraint is always visible from the
entity itself, without the entity owning or duplicating the *why* — that
stays singular in governance. Because the check is mechanical rather than a
matter of someone remembering, an agent can be made to verify "does
anything constrain what I'm about to touch" every time, without the
discipline degrading under load the way it does for people.

## Evidence: every knowledge and governance claim must be checkable

Every knowledge object and every decision must cite at least one piece of
evidence — something that lets an agent verify the claim is still true
rather than taking it on faith. Evidence comes in two forms, and they are
not equally strong:

- **Test evidence** (`verified_by: execution`) — the claim holds if and
  only if the cited test currently passes. Mechanical, cheap, no
  interpretation required.
- **Code evidence** (`verified_by: inspection`) — the claim requires an
  agent or human to read the code and judge whether it still matches.
  Slower, and the harder case that still needs human oversight.

Where a test can reasonably assert the claim, a test reference is preferred
over a bare code reference, because it converts a judgment call into a
mechanical check. This preference is **encouraged, not enforced**: the
implement phase should attempt to write a test before falling back to a
code-only reference, but is never blocked from shipping a code-only
reference when a test genuinely isn't practical.

What keeps "encouraged" from quietly decaying into "ignored": a code-only
evidence entry must record whether a test was attempted and, if not used,
why:

```yaml
evidence:
  - type: test
    ref: tests/Auth/TokenRefreshTests.cs::RefreshesBeforeExpiry
    verified_by: execution
  - type: code
    ref: src/Auth/TokenService.cs::RefreshToken
    verified_by: inspection
    test_attempted: true
    fallback_reason: "requires live token expiry timing, not practical in unit test"
```

A code-only entry **missing** `fallback_reason` is a warning — surfaced
independently by both audit (continuously) and PR review (at merge time).
Neither surfacing blocks anything. This is the one place in the whole
model where visibility, not enforcement, is the mechanism: the reasoning
being tested is a matter of *degree* (how cheaply can this be verified),
not *existence* (can this be verified at all) — and degree questions get
warnings, existence questions get gates.

When `/devspark.explain` finds missing or drifted knowledge, it asks targeted
clarification questions whenever ownership, scope, layer, or intent is
ambiguous. After the human confirms the proposal, explain updates the owning
knowledge document and its durable references, or creates a typed node when no
owner exists. Durable knowledge cites durable code and tests only; temporary
spec, plan, task, and quickfix records carry the inverse traceability through
their linkage fields.

## What triggers assimilation

Assimilation — merging a completed delta's knowledge into the permanent
record — is not a periodic sweep decoupled from any individual unit of
work. The DevSpark prompt set groups into three phases, and the
downstream/repo-wide prompts (PR review, audit, release) are the ones that
carry assimilation forward:

- **Plan & build** — specify, plan, tasks, analyze, critic. Produces the
  ephemeral spec package.
- **Implementation** — implement. Applies the delta to code and knowledge
  together, in one disciplined pass. Never tracks specs, requirements, or
  tasks as comments in code — that would need cleanup later, so it is never
  created in the first place. It never archives anything: the spec package
  stays live in `.devspark.work/` with its `code_ref`/`knowledge_ref`
  linkage populated, so it remains validate-able against code, tests, and
  knowledge for as long as it takes a release to sweep it out.
- **Validation** — PR review, site audit, release. These pivot to validate
  and enforce knowledge/code linkage and consistency, rather than checking
  spec completion (which stays implement's job). Release is also the one
  place a completed, linkage-verified spec or quickfix actually leaves
  `.devspark.work/` — no other command ever moves it.

PR review is the natural trigger point because nothing merges without one —
it isn't a "when convenient" sweep, and the PR diff itself (not the spec,
which may already be gone) is what proves a delta's code and knowledge
changes actually landed together. Audit's job is different in kind: not
per-diff consistency, but scanning current knowledge for internal
contradiction and for claims whose cited evidence no longer holds — a
synchronic check across the whole current state, not a check against any
particular spec or diff.

## The minimum non-negotiable rules

Trying to avoid dogmatism, the test for whether a rule belongs on this list
is narrow: **a rule is non-negotiable only if violating it falsifies the
core guarantee** — that the permanent record is current-truth-only,
checkable, and contains no trace of the ephemeral scaffolding that produced
it. Everything else is quality, not existence, and belongs in "encourage,"
not "gate." Five rules pass this test, all mechanically enforceable:

1. **Closed reference graph, one direction only.** The permanent record —
   code and knowledge/governance documents — may only reference each other,
   never a spec, task, plan, PR thread, or any other repo-internal ephemeral
   artifact. This is a one-way gate, not a symmetric ban: the **inverse
   direction is encouraged, not forbidden**. An ephemeral artifact
   referencing the permanent record is safe by construction, because when
   the ephemeral thing is archived out of `.devspark.work/`, the reference
   goes inert with it — nothing is
   left dangling in code, knowledge, or governance. References to anything
   *outside* the repository (an RFC, a vendor API doc, a business
   objective) are unrestricted in either direction — those are stable by
   construction and can't leak the way an internal ephemeral pointer can.
2. **Verify before archive.** A spec cannot be archived until its delta is
   verified as landed in code, knowledge, and governance (if touched). This
   is a two-stage gate: `/devspark.implement` performs the verification
   and populates the linkage that proves it, but deliberately leaves the
   spec live in `.devspark.work/` afterward; `/devspark.release` is the only
   command that later re-checks the linkage and performs the actual move to
   `.archive/{YYYY-MM-DD}/`. A spec can sit verified-but-unarchived across
   more than one release window — that's normal, not a violation. Recovery
   after archiving is a human action: manually copying the file
   back out of `.archive/{YYYY-MM-DD}/` (no DevSpark command reads
   `.archive/`), not reconstructing it from nothing, so this ordering is
   still the model's entire integrity check.
3. **Evidence required, always.** Every knowledge object and every decision
   cites at least one piece of evidence. Which type is a warning-level
   quality question (see above); that *some* evidence exists at all is
   non-negotiable — a claim with nothing backing it isn't checkable, which
   breaks the guarantee outright rather than just making it more expensive
   to verify.
4. **One current file per decision topic.** Never a chain, never two
   files both claiming to govern the same topic at once. If two files can
   both claim to govern the same topic, "current truth" stops meaning
   anything.
5. **No ephemeral-artifact references in code**, implied by rule 1 but
   worth stating on its own since it's the clearest and most immediately
   checkable instance of it: no code comment references a spec ID, task
   ID, or plan identifier.

## In-flight linkage: how verify-before-archive actually gets checked

Rule 2 says a spec cannot be archived until its delta is verified as landed.
Task-level linkage is what makes that mechanical rather than a judgment
call. Every task tracked in `.devspark.work` during implementation carries
a live pointer to where it landed:

```yaml
- id: task_003
  description: "Add token refresh retry logic"
  status: complete
  code_ref: src/Auth/TokenService.cs::RefreshToken
  knowledge_ref: entities/token_service/architecture.md
```

This is the encouraged inverse of rule 1, not an exception to it: the task
is the ephemeral artifact, and it points at the permanent record, which is
safe because the pointer goes inert with the task once the spec is archived.
Implement populates this linkage and leaves it in place — verify-before-archive
then reads as a mechanical check `/devspark.release` performs later: no spec is
archived while any task lacks a populated `code_ref` and `knowledge_ref` (or an
explicit `n/a` with a reason, mirroring the `fallback_reason` pattern
already used for evidence). `.devspark.work` was already the designated
home for in-flight state; this is what it was for — the task list itself
*is* the tracked state, and its pointers are what the eventual release
checks before the whole package is moved to `.archive/{YYYY-MM-DD}/`.

One edge case worth naming rather than designing around: a task's
`code_ref` is checked for existence at verification time, not continuously.
If code is refactored again after the pointer is written but before a
release archives the spec, the pointer can go stale for however long the
spec stays live in `.devspark.work/` — which, under this model, can span
more than one release window while the spec's linkage keeps doubling as an
in-sprint validation aid. Low risk, and not worth building continuous
checking for something whose staleness release's own re-check will catch.

## The ontology implementation: `.knowledge/ontology/`

The philosophy above is specified concretely by `scripts/build_knowledge_index.py`
against the JSON Schema contracts in `templates/schemas/`
(`entity-node.schema.json`, `knowledge-node.schema.json`), with generated
output at `.knowledge/ontology/coverage.json` — living inside `.knowledge/`
rather than as a fifth root.

- **Decisions live at `.knowledge/governance/decisions/`**, as markdown
  with frontmatter — not as `_entity.yaml`-style nodes — because a
  decision's body is prose for humans ("what we do, why not the
  alternatives"), matching the existing knowledge-layer-doc contract rather
  than the pure-structural entity-node contract. Frontmatter carries `id`,
  `type: governance-decision`, `title`, and `constrains` (a non-empty array
  of entity ids this decision constrains — required for this type).
  `status`, `lifecycle`, `supersedes`, `superseded-by`, `replaced`, and
  `obsolete` are all banned keys on every current-knowledge doc, decisions
  included — there is no "deprecated" state a decision can hold; one that
  stops applying is edited in place or deleted, never marked deprecated. No
  `layer` key — a decision is one document, one topic, not a multi-view
  entity.
- **`constrains` / `constrained_by` is a hand-authored, validated
  reciprocal pair.** `constrains` is hand-authored on the decision.
  `constrained_by` is *also* hand-authored, directly on the entity's own
  `_entity.yaml` (per `entity-node.schema.json`) — the generator validates
  reciprocity (every entity a decision `constrains` must list that decision
  back in its own `constrained_by`, and vice versa).
- **Staleness detection is a `--check` flag, not a read-only default.**
  `build_knowledge_index.py --check` fails if the committed `index.json` /
  `coverage.json` don't match what the generator currently produces, and
  never writes files in that mode. There is no separate `--write` flag —
  without `--check`, the generator writes `index.json` and `coverage.json`
  directly.
- **The evidence discipline operates at the prompt level.**
  `knowledge-node.schema.json` defines `source_of_truth` as an array whose entries are either a
  plain path string (legacy, unchanged) or an opt-in object claim (`path`, `profile`, `region`,
  `digest`, `baseline`, `verification.state`) that a repository migrates into per-document once it
  sets `knowledge_drift.enforcement: pinned-claims`. `last_verified` (date) remains the required
  per-document currency pair either way. `/devspark.verify`, `/devspark.implement`,
  `/devspark.create-pr`/`update-pr`, and `/devspark.site-audit` each carry
  the instructions that track and report test-vs-code evidence,
  `verified_by`, and `fallback_reason` as part of their own workflow. Object claims add a second,
  independent evidence axis: content drift, evaluated by `build_knowledge_index.py
  --detect-drift` against a retained canonical baseline rather than a commit date, bounded to
  explicit Git scope (`--base`/`--head`) or a history-free `--full-inventory`, and never asserting
  human verification on its own — only `/devspark.explain <topic>`'s retained-baseline diff and
  explicit confirmation can record one.
- **Existence and accuracy are two separate reports.** `coverage.json`
  answers "does the required layer's document exist." `/devspark.site-audit`
  runs the accuracy pass — resolving `execution`-type evidence by
  re-running its cited test, and judging `inspection`-type evidence by
  reading the code.
- **The tooling runs inside the DevSpark lifecycle.** `/devspark.pr-review`
  and `/devspark.site-audit` both invoke `build_knowledge_index.py` and gate
  on gap-report failures for touched/all entities. Audit scopes its
  contradiction scan to graph-adjacent objects (same entity, entities
  sharing a `constrains` decision, objects citing the same evidence) rather
  than brute-force pairwise comparison.

## Discovery: reaching knowledge by concept, not only by id

A `.knowledge` document must be reachable by the concept it explains, not only by an identifier an
agent happens to already know. `build_knowledge_index.py` indexes each document's headings and an
optional `aliases:` frontmatter list at build time; `explain-context.py` additionally searches body
prose at query time rather than committing it to `index.json` — body text is rebuilt per query, so
the index stays small and reviewable and can never carry stale prose.

Ranking is deterministic and identical for every agent, not a similarity score computed by a model:
each evidence class (exact id/title match, alias, heading, path/`appliesTo`/`source_of_truth`
metadata, body) carries a fixed weight, strongest signal first, and every match reports a
`matched_on` list explaining exactly why it scored the way it did.

**An evidence class contributes its weight at most once per query term, never once per
occurrence.** A term repeated across ten headings, or across ten `source_of_truth` entries, scores
exactly like one matching heading or entry — evidence volume enriches `matched_on` explainability,
it never multiplies relevance. This is not an optimization; it is the same governing idea as the
rest of this document applied to search — a document's *relevance* is what matters, not how much
text it happens to contain. A retrieval model that rewards breadth would quietly punish the terse,
current-truth `.knowledge` documents this framework asks authors to write, and reward the sprawling
ones it asks them to avoid.

**There is exactly one implementation of this engine, `.devspark/scripts/build_knowledge_index.py`,
and every entry point resolves to it.** `/devspark.explain`, `site-audit`, `create-pr`,
`get-pr-context`, `release-context`, and the quickstart-driven index check all share one resolver
(`resolve_knowledge_engine` in `common.sh` / `Resolve-KnowledgeEngine` in `common.ps1`) that prefers
the framework-managed `.devspark/scripts/` copy, falling back to a legacy repository-root copy only
when the framework-managed one is absent, and the quickstart upgrade flow reconciles a lingering legacy
copy rather than leaving it to drift silently. A repository is never allowed to have two answers to
"what does the knowledge index look like" depending on which entry point happened to run — that is
the same category of drift this document rules out for specs and ADRs, just at the tooling layer
instead of the content layer.

## Prompt inventory

Every `devspark.*` command mapped against this philosophy, with updated
purpose guidance per command, is in the companion document
`devspark-prompt-mapping.md`. Headline items: `implement` carries the
heaviest discipline (one-hop-only retrieval, evidence preference, task
linkage) but never archives anything — the spec or quickfix record stays
live in `.devspark.work/` with its linkage populated for as long as the
sprint needs it; `pr-review` is the primary assimilation trigger; `release`
is the **sole** command that sweeps `.devspark.work/` retention, orphaned
in-flight state, and completed/linkage-verified specs and quickfixes into
`.archive/`; and `devspark.verify` is the evidence-execution engine the
test-evidence preference depends on, running cited proof modes and
recording the `test_ref` pointer `implement` consumes for `verified_by:
execution` evidence. Every command in the inventory has both an agent and
a prompt shim. `devspark.explain` both *detects and remediates* knowledge
drift in a single interactive run — topic-scoped rather than diff-scoped
(`pr-review`) or repo-wide (`site-audit`), reusing the same DELTA/KNOW
finding codes, but writing the correction or drafting the missing doc
itself after one explicit confirmation instead of only reporting the gap.

## The `.archive/` retention: preserving short-lived value without keeping it active

A spec that hasn't yet produced a committed delta represents real, if
short-lived, value — and an agent-driven removal of a file that was never
committed is unrecoverable even though Git is technically the system of
record for everything that *was* committed. Rather than accept that gap,
`/devspark.release` — the command that sweeps completed planning bundles
and routine work products — moves them out of the active tree instead of
deleting them outright, once they meet their applicable completion rules.

`/devspark.implement` deliberately does **not** do this: it
populates a spec or quickfix record's `code_ref`/`knowledge_ref` linkage and
leaves the record exactly where it is, live in `.devspark.work/`, for as
long as the sprint needs it — that linkage is what lets anyone validate the
delta against code, tests, and knowledge while it's still there. A record
can sit verified-but-unarchived across more than one release window before
`/devspark.release` finally sweeps it; that's normal, not a stall.

**Mechanics:**

- On confirming a spec or quickfix's linkage is still populated — never for
  a stalled or incomplete record — `/devspark.release`'s archive step moves
  the entire spec package intact into `.archive/{YYYY-MM-DD}/` (preserving
  its relative path minus the `.devspark.work/` prefix) instead of deleting
  it. Whole package, not a summary: plan, tasks, checklists, gates,
  `context_resolved` — deciding now what a human might want to see later
  would be the same premature judgment call the model avoids everywhere
  else.
- `.archive/` is a repository-owned root alongside `.devspark.work/` and
  `.knowledge/` — retiring resolved
  `.devspark.work/` planning artifacts, never a parallel history for
  `.knowledge/`. `/devspark.release`, `/devspark.constitution`, and
  `/devspark.evolve-constitution` are the only commands that write to it,
  moving eligible archive-eligible/retention/orphan/proposal content there.
  Writing is the only direction any command ever takes. `/devspark.release`
  is the sole command that sweeps `.devspark.work/` retention, orphaned
  in-flight state, and completed/linkage-verified specs and quickfixes into
  `.archive/`.
- **No DevSpark command reads, lists, enumerates, or globs `.archive/`,
  under any circumstance, once content has been moved there.** It is
  write-only from every command's perspective — nothing reconstructs
  planning state from it, and nothing scans it looking for content to
  report on or recover.
- Purging is human-only and has no schedule enforced by the model — a
  human decides when an `.archive/` entry no longer needs to be kept and
  removes it directly, outside any DevSpark command.

## No CLI, no harness — scripts and prompts instead

DevSpark deliberately has no standalone CLI executable and no
programming harness. This isn't tooling minimalism for its own sake — it's
the same argument the rest of this philosophy makes about specs, ADRs, and
retrieval, applied to DevSpark's own tooling: push judgment to prompts,
where a capable agent can reason through context-dependent decisions, and
reserve deterministic execution for scripts that need no judgment at all.
A harness is the most literal form of a "dogmatic guardrail" possible — a
fixed program the agent executes *through* rather than a set of judgment
calls it makes *within*. This applies the same thesis to DevSpark's own
tooling, not just to the artifacts it produces.

An unused CLI is a maintenance liability with no real test case behind it,
independent of what it symbolizes.

**Scripts are not the same thing as a CLI, and are actively encouraged.**
The distinguishing test: a script executes one deterministic operation with
no judgment involved, invoked directly by the prompt that needs it, when it
needs it. A CLI is a standing interface implying a strategy for interacting
with the framework, independent of any single prompt's need — competing
with prompts as the way work gets done, rather than serving them. Scripts
are the mechanical, no-judgment tier (same tier as `verified_by: execution`
evidence); prompts own everything requiring judgment; a CLI tries to
straddle both, which is exactly why it keeps accumulating complexity nobody
actually uses.

`build_knowledge_index.py` and the migration script
(`migrate-knowledge-to-entities.py`) are
small, single-purpose, testable in isolation, and invoked directly by name
— no dispatcher, no shared state between them, no subcommands. Their status
is unrelated to the CLI question — they were never its concern. Scripts
like these are the concrete mechanism that runs the gap-report and
evidence-accuracy checks `pr-review` and audit rely on.

**Where a CLI can creep back in under a different name**: not through any
one script, but through scripts accumulating a coordinating layer. The
moment two scripts need to know about each other, or something decides
*which* script to run based on framework state rather than a prompt simply
calling the one it needs, that coordinating thing is a CLI wearing a
script's clothes. The test for any new script: can it be described as
"runs one check, exits, done," invoked by exactly the prompt that needs it
— or does it need to know about DevSpark's overall state to decide what to
do? The first is a script. The second is the harness again, regardless of
what it's called.

## Contradiction judgment is a human call, not a mechanized gate

Once audit has a scoped, graph-adjacent set of objects to compare (same
entity, entities sharing a `constrains` decision, objects citing the same
evidence), judging whether the result is a genuine contradiction or an
acceptable nuance is not mechanized. It stays a permanent **warning
surfaced for human review**, the same tier as a missing `fallback_reason`.
Scoping the search space is a mechanical check; judging semantic
contradiction within that scope is a deliberate human judgment call — one
discipline to remember (audit surfaces, human disposes) instead of
maintaining two contradiction-detection code paths for a narrow mechanical
win.

## Retrieval budgets: design time vs. runtime

Design time and runtime carry different retrieval budgets, on the
principle that complexity should be worked out before code is written, not
discovered while writing it:

- **Design time** (specify → plan → tasks) does the expensive multi-hop
  ontology traversal and pins the result down as an explicit
  `context_resolved` list in the ephemeral spec package — the same
  ephemeral-artifact-points-at-permanent-record shape as task-level
  `code_ref` / `knowledge_ref`, safe under rule 1's one-way gate, and it
  disappears when the spec does.
- **Analyze** gates on resolution *validity* — every entity and relation
  named in `context_resolved` must actually resolve against the current
  ontology. Mechanical, hard-stop: a stale or hallucinated reference fails
  outright, the same class of check the generator already runs on
  `relations[].object`.
- **Critic** gates on resolution *sufficiency* — does `context_resolved`
  look complete for the delta being planned. Adversarial, judgment-based,
  not a hard stop — the natural place to ask "what did design time miss."
- **Implement** never traverses more than one hop; it consumes
  `context_resolved` as already-resolved context. An escalation past one
  hop during implement is an attributable signal rather than a vague
  shortfall: frequent escalation on one entity pair means the ontology's
  relations are too sparse and an edge should be added directly; escalation
  despite a passing `context_resolved` means critic isn't catching
  sufficiency gaps and that prompt needs tightening; an analyze failure
  means the spec itself named stale or hallucinated context, a spec-quality
  problem rather than a gate problem.
