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

When `/devspark-explain` finds missing or drifted knowledge, it asks targeted
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
   is a two-stage gate: `/devspark-implement` performs the verification
   and populates the linkage that proves it, but deliberately leaves the
   spec live in `.devspark.work/` afterward; `/devspark-release` is the only
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
then reads as a mechanical check `/devspark-release` performs later: no spec is
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
  per-document currency pair either way. `/devspark-verify`, `/devspark-implement`,
  `/devspark-create-pr`/`update-pr`, and `/devspark-site-audit` each carry
  the instructions that track and report test-vs-code evidence,
  `verified_by`, and `fallback_reason` as part of their own workflow. Object claims add a second,
  independent evidence axis: content drift, evaluated by `build_knowledge_index.py
  --detect-drift` against a retained canonical baseline rather than a commit date, bounded to
  explicit Git scope (`--base`/`--head`) or a history-free `--full-inventory`, and never asserting
  human verification on its own — only `/devspark-explain <topic>`'s retained-baseline diff and
  explicit confirmation can record one.
- **Existence and accuracy are two separate reports.** `coverage.json`
  answers "does the required layer's document exist." `/devspark-site-audit`
  runs the accuracy pass — resolving `execution`-type evidence by
  re-running its cited test, and judging `inspection`-type evidence by
  reading the code.
- **The tooling runs inside the DevSpark lifecycle.** `/devspark-pr-review`
  and `/devspark-site-audit` both invoke `build_knowledge_index.py` and gate
  on gap-report failures for touched/all entities. Audit scopes its
  contradiction scan to graph-adjacent objects (same entity, entities
  sharing a `constrains` decision, objects citing the same evidence) rather
  than brute-force pairwise comparison.

## Knowledge maintenance discovery: proposals, not automation

> **Knowledge maintenance is continuous; knowledge discovery is periodic.**
>
> **The best time to author knowledge is when the code makes the truth evident. Discovery exists
> for the truths we missed.**

Every `/devspark-*` skill that touches `.knowledge` — `/devspark-plan`'s Context Resolution,
`/devspark-implement`'s current-knowledge updates, `/devspark-explain`'s drafted-and-verified
gaps — authors or corrects `.knowledge` continuously, as a direct byproduct of the delta already in
front of an agent, at the exact moment the changed code makes the new or corrected truth evident.
That is the default path, and it is why most `.knowledge` never needs a dedicated discovery pass at
all. `/devspark-discover-knowledge` exists only for what continuous, delta-scoped maintenance
cannot catch by construction — gaps, weak mappings, aliases, and contradictions with no active
delta to surface them, found only by periodically scanning the whole graph rather than one change
at a time. It is a backstop for missed truths, not a substitute for authoring them when the code
already made them evident.

`/devspark-discover-knowledge` (`scripts/discover-knowledge.py`) is a separate concern from the
concept-reachability discovery described below — it does not answer "how do I find this
document," it answers "what does `.knowledge` still need." It inspects the same signals
`build_knowledge_index.py` already validates (declared `appliesTo`/`source_of_truth` mappings,
`links.references` targets, entity `aliases`/headings, pinned object-claim status) plus repository
code and test layout, and reports findings through the same shared schema
`scripts/knowledge_findings.py` defines for `knowledge-integrity.py` — so findings from both tools
triage side by side under one vocabulary of category, severity, and confidence.

Two properties keep this tool inside the rules above rather than becoming a second, informal
assimilation path:

- **It never promotes an inference into authoritative `.knowledge` on its own initiative.**
  Every finding is `changes_authoritative_truth: false`. The only writes it can ever perform are
  two narrow, mechanical, schema-conformant edits — adding one alias to one node, or one relation
  entry to one entity — and only when invoked with the corresponding `--apply-alias`/
  `--apply-relation-from`+`--apply-relation-to` flag *and* `--write`; without `--write` both report
  a dry-run of what would change and touch nothing. Every other category (knowledge gaps, entity
  candidates, broad/overlapping mappings, contradictions, historical leakage) is left for a human,
  or a chaining agent with explicit confirmation, to act on.
- **Its "contradiction" and "historical-leakage" categories are deliberately narrow, not the
  general-purpose versions the plain-English names might imply.** "Contradiction" here is pinned
  `source_of_truth` object-claim drift only (a document's pinned claim was marked verified but the
  canonical source has since changed, or was never confirmed) — it is not the free-text semantic
  contradiction judgment call described above, which stays a human/audit responsibility.
  "Historical-leakage" is a deterministic match on ephemeral-identifier syntax (`FR-###`, `T###`,
  `spec-##`) or a historical-sounding heading — not a semantic scan of body prose. Any
  documentation or command output describing this tool must preserve that precision rather than
  imply broader inference than it performs.

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
and every entry point resolves to it.** `/devspark-explain`, `site-audit`, `create-pr`,
`get-pr-context`, `release-context`, and the quickstart-driven index check all share one resolver
(`resolve_knowledge_engine` in `common.sh` / `Resolve-KnowledgeEngine` in `common.ps1`) that prefers
the framework-managed `.devspark/scripts/` copy, falling back to a legacy repository-root copy only
when the framework-managed one is absent, and `/devspark-upgrade` reconciles a lingering legacy
copy rather than leaving it to drift silently. A repository is never allowed to have two answers to
"what does the knowledge index look like" depending on which entry point happened to run — that is
the same category of drift this document rules out for specs and ADRs, just at the tooling layer
instead of the content layer.

## Integrity is checkable, not assumed

Claiming "the knowledge index is trustworthy" and actually checking it are different things.
`scripts/knowledge-integrity.py` makes the claim mechanically verifiable: a CI-friendly,
non-mutating validator that runs the same one canonical engine (`build_knowledge_index.py`)
against six specific ways `.knowledge` can quietly go wrong — a second, drifted engine copy
answering differently than the canonical one; a generated artifact (`index.json`,
`ontology/coverage.json`) that no longer matches a fresh build; a taxonomy-registry mapping that
disagrees with the engine's own type inference; a mapping so broken the index build itself fails
(surfaced as a structured finding instead of a crash); a `.knowledge/` directory the index never
reaches at all (for example one nested under `examples/`); and a taxonomy registry declaring a
`nodeType` the engine does not recognize. `site-audit --scope=knowledge` folds these checks in as
`KNOW7`–`KNOW9` rather than re-deriving them, and `/devspark-upgrade` calls the same validator's
`--verify-sync` before *and* after reconciling a legacy engine copy, so "resolved" always means
"re-checked," never "believed."

Every integrity check, and any future knowledge diagnostic, reports through one shared finding
shape (`scripts/knowledge_findings.py`): a deterministic, content-addressed `finding_id` (hashed
from the condition's identity, never from timestamp or scan order, so the same underlying problem
reports the same id on every re-run), a fixed category vocabulary, and an explicit
`severity`/`confidence` pair kept separate on purpose — severity is "how bad if true," confidence
is "how sure we are it's true," and collapsing the two into one score would hide exactly the
distinction a human reviewer needs to triage a finding correctly. Findings that indicate the index
itself cannot be trusted (engine divergence, artifact drift, an unreachable root, a dangling
reference) are hard failures that gate CI; everything else is advisory.

Retrieval quality is measured the same way integrity is — mechanically, not by inspection.
`scripts/knowledge-benchmark.py` runs `/devspark-explain`'s exact, unmodified matching engine
against a fixture of `{query, expected}` cases and reports rank/visibility metrics
(`rank1_rate_pct`, `top3_rate_pct`, `topn_rate_pct`, `miss_rate_pct`) plus multi-concept recall
kept as a separate figure, never averaged into the single-concept rate. It deliberately reuses
`explain-context.py` rather than reimplementing ranking logic a second time, so a benchmark result
always reflects what an agent actually gets back, and it never filters governance/ADR nodes out of
its raw candidate list — a benchmark that could silently hide a governance node from its own report
would defeat the point of measuring visibility at all.

## Prompt inventory

Every `/devspark-*` skill mapped against this philosophy, with updated
purpose guidance per command, is in the companion document
`devspark-prompt-mapping.md`. Headline items: `implement` carries the
heaviest discipline (one-hop-only retrieval, evidence preference, task
linkage) but never archives anything — the spec or quickfix record stays
live in `.devspark.work/` with its linkage populated for as long as the
sprint needs it; `pr-review` is the primary assimilation trigger; `release`
is the **sole** command that sweeps `.devspark.work/` retention, orphaned
in-flight state, and completed/linkage-verified specs and quickfixes into
`.archive/`; and `devspark-verify` is the evidence-execution engine the
test-evidence preference depends on, running cited proof modes and
recording the `test_ref` pointer `implement` consumes for `verified_by:
execution` evidence. Every command in the inventory is installed as an
Agent Skill. `devspark-explain` both *detects and remediates* knowledge
drift in a single interactive run — topic-scoped rather than diff-scoped
(`pr-review`) or repo-wide (`site-audit`), reusing the same DELTA/KNOW
finding codes, but writing the correction or drafting the missing doc
itself after one explicit confirmation instead of only reporting the gap.

## Convergence: a spec finishes when its findings are classified, not eliminated

DevSpark is good at finding things. Every gate, audit, and verification run
reliably surfaces more evidence, more gaps, more improvements, more
questions. The capability it lacked was the opposite one: recognizing that
the work is **done**.

The failure mode is a loop. Verify runs, discovers an observation, the
observation becomes work, the new work is verified, which discovers another
observation. Each step is individually defensible and the net effect is that
verification silently expands the specification it was supposed to close.
The route never converges, because "no remaining observations" is not a
reachable state — any sufficiently careful look at any system produces more
observations.

This is not a hypothetical. Repository history taken from before the
convergence model existed shows exactly the predicted shape: routes carrying
repeated gate rounds in which each pass resolves the prior finding and
surfaces a new non-blocking one. The model below is what makes that loop
terminate, and the historical evidence is the argument for keeping it rather
than a reason to revisit it.

So the completion test is not elimination, it is classification:

> **A spec is complete when its stated objective has been resolved and every
> remaining finding has been classified — not when every observation
> generated during the work has been eliminated.**
>
> **Verification may discover work, but discovery alone does not expand the
> current specification.**

A finding creates mandatory work inside the active route only when it
demonstrates one of five expansion triggers: failure of the stated
objective, an unresolved requirement, a violated invariant, a correctness
defect, or a regression caused by the change. Everything else is classified
as an **Accepted Limitation**, **Deferred Work**, or a **Learning / Changed
Assumption**, and the route converges carrying it.

The rule is symmetric, and that half matters just as much. A finding that
*does* hit an expansion trigger is a Blocking Defect and cannot be
classified away. Classification is how a route converges honestly, not how a
failed requirement is retired quietly — which is why acceptance statements
declare their kind (`requirement`, `invariant`, `hypothesis`, `target`) when
they are *written*, not when they are judged. A failed requirement and a
disproven hypothesis look identical in a gate report; only the declared kind
tells you that one is a defect and the other is a result. An undeclared kind
reads as `requirement`, the strictest reading, so nothing can be quietly
downgraded once the evidence is in.

That last distinction is what makes experimental and design work finishable
at all. A disproven hypothesis is a valid outcome — the objective was to
settle a proposition, and the evidence settled it. Treating "the evidence
contradicted what we wrote down" as an implementation failure makes those
routes impossible to close, and quietly discourages anyone from writing down
a falsifiable proposition in the first place. The original hypothesis and
the evidence that disproved it both stay visible; history is not rewritten
to match the result.

Finally, **scope expands only on human intent.** Acting on a deferred item
immediately is a legitimate choice, but it is the developer's choice to
make. "The agent discovered this" and "the developer decided to include
this" are different facts and stay distinguishable in the record. Without
that, the loop just reappears one level down.

A human-authorized bounded correction needed to satisfy the existing objective
is not optional deferred work: it is a scoped decision to complete the current
work, recorded in its existing artifacts. It does not permit an agent to
promote unrelated findings, relabel a failed requirement, or bypass verification.

Implementation complete means ready to merge and deploy, not already deployed.
A requirement that only a deployed environment can prove is declared
`stage: post-deploy` and is carried as deferred work with an existing durable
record (never one created to satisfy closeout), an owner, and the required deployed evidence. It never blocks merge
and is never recorded as satisfied on local or automated evidence. A mandatory
pre-merge requirement that fails, or a pre-merge safety or compliance
requirement, still blocks, and a pre-merge mode that can only pass in a deployed
environment is a spec authoring defect rather than something to defer.

The mechanics — the four classifications, the criterion kinds, the
`gates/closeout.md` artifact, the stop condition, and the `stage` and
`evidence_class` attributes — live in `templates/closeout-contract.md` and
`templates/verification-contract.md`.

## Assurance: four capabilities, four questions, one owner per finding

Four commands evaluate work they did not author. Left undifferentiated they
all collapse into the same behavior — "review the change" — and the cost is
not merely untidy. Duplicate findings train a reader to skim, and a reader
who skims misses the one finding that mattered.

So each capability answers a question the others structurally cannot:

> **Analyze checks whether the plan makes sense on paper. Critic checks
> whether that sensible plan survives contact with the real system. Verify
> proves whether the implementation works. PR Review decides whether the
> resulting delta should be accepted.**

The split between the two planning gates is the sharp one, and it is a
**closed-world / open-world** distinction, not a difference in tone. Analyze
can prove everything it owns from the artifacts alone: requirements that
contradict each other, a task citing an anchor that was never defined, a
field name that disagrees with the plan's own data model, a prerequisite
ordered after the task that needs it. Critic owns what the artifacts cannot
settle — whether the baseline can actually produce a condition a requirement
depends on, whether behavior being deleted as redundant is in fact the only
path satisfying a guard, whether operating this design would require a
control nobody asked for.

Three rules keep that boundary from eroding in practice.

**Evidence, not intuition.** Critic must read the relevant code, tests, and
`.knowledge/` before asserting anything about current behavior. A claim about
the baseline with no cited file and symbol is a guess wearing a severity
label, and it is indistinguishable from a real finding until someone spends
an hour disproving it. The strongest finding shape is a contradiction between
a plan statement and an inspected source fact.

**One finding, one owner.** A capability that notices a defect in another's
lane routes it rather than emitting it. Ignoring the observation would lose
real information; emitting it would destroy the boundary. Routing preserves
both — the finding reaches its owner, and the emitting capability's output
stays honest about what it actually proved.

**Uncertainty is an obligation, not a defect.** Much of what a reviewer
worries about cannot be known until something runs. Escalating that into a
pseudo-defect produces a gate that is simultaneously alarming and
unactionable. Critic identifies the risk in time to plan for proof; Verify
performs the proof.

Two failure modes follow from getting this wrong, and both were observed
before the boundary was written down. A capability with no stated scope
limit generates **generic noise** — "consider scalability", "ensure
observability" — advice that is never wrong and never useful, because it
names no evidence and no decision. And a capability that treats its own
missing configuration as a defect spends the developer's attention
**policing its own metadata** instead of reviewing their change. Absent
classification metadata is inferred and reported in the gate header; it is
never a finding.

Critic also applies on **observable change shape**, not on an authored risk
label. Repository evidence showed the label predicting poorly in both
directions — low-risk routes carrying critical design defects, and
safety-critical routes with nothing for Critic to find. Shape is the better
signal: persisted data or controlled vocabulary changing, a boundary being
crossed, a lifecycle or terminal path moving, behavior resting on
nondeterministic output, a new write path appearing. A change exhibiting
none of these is not automatically applicable — which is a routing decision,
never a prohibition. Critic stays explicitly callable on anything.

Assurance is bounded the same way the route is: discovery, remediation,
recheck, stop. A capability does not review the work that resolved its own
earlier findings, and a new observation noticed during a recheck is
classified under the one convergence model rather than reopening the pass.
There is no second taxonomy.

The boundary itself — the capability table, the lane prohibitions, the
routing escape, the deduplication rules, the quality bar, the derived verdict
vocabulary, and the applicability signals — lives in
`templates/assurance-contract.md`, stated once so four prompts can reference
it instead of drifting four ways.

## Empirical proof follows change shape, not route label

Ordinary validation — the suite, the linters, the type checker — answers
whether the code does what the code says. It cannot answer whether the code
is right about the world it runs in. Verification exists for the second
question, and the useful trigger for it is not how important the work feels
but whether the change depends on something the tests cannot observe:
runtime configuration, environment-dependent behavior, an external contract,
real datastore semantics, a component every covering test replaces with a
double, or the shape of data already deployed.

Those shapes are what produce the "tests green, reality wrong" defect, which
is precisely the class static assurance structurally cannot reach. Binding
verification to a route label instead misses it in both directions: a route
named `refactor` gets proof it may not need, while a config change on an
ordinary route — exactly the shape most likely to be wrong — gets none.

The correction is to make the decision better, not universal. Requiring
every mode everywhere would convert a targeted capability into ceremony, and
ceremony is what developers route around. The vocabulary is deliberately
small, technology-neutral, and advisory: a shape makes a mode *recommended*;
declaring it is what makes it *required*. Exhibiting no shape is a normal
answer, and manufacturing proof for a contained local change is waste.

What is not optional is that the decision be **visible**. "Empirical
verification: NOT REQUIRED — no verify-sensitive change shape" is two lines,
and it is the difference between a judgment a developer can disagree with
and a silent omission nobody notices. Classification can be automatic;
reasoning may not be invisible. The same rule binds in the other direction:
a proof mode that needs live traffic, a production-like environment, or
anything with a cost is proposed and authorized, never assumed.

The shape vocabulary and the reporting form live in
`templates/verification-contract.md`.

## A lightweight route may admit it grew up

Choosing a lightweight route is a decision made before the work is
understood, which means it is sometimes wrong — and the failure is quiet.
A fix that turns out to introduce an architectural contract, cross a trust
boundary, or change governance does not announce itself; it simply proceeds
under ceremony sized for something smaller, and the record that survives
understates what happened.

The correction is not to make the lightweight route heavier. It is to notice
when the *discovered* scope no longer matches the route's assumptions and to
put that in front of the developer as an explicit choice: continue as a
quickfix, or promote to a full spec. Effort-based warnings already catch
"this is taking longer than expected"; the signals that matter here are about
what the work turned out to be — a new contract, a new cross-subsystem
dependency, a governance change, a public contract change, a semantic schema
change, a security or trust-boundary issue, or several unrelated concerns
bundled together.

Surfacing is conservative by design. Most quickfixes exhibit none of these
and finish as quickfixes; a prompt that escalates routinely trains developers
to dismiss it. And the decision stays the developer's — the framework's job
is to make sure the route was *chosen* rather than merely inherited.

## Leave enough evidence to evaluate the framework itself

A framework that claims to improve outcomes should be able to prove it, and
that requires knowing which version produced which artifact. Reconstructing
that from Git dates and upgrade commits is both laborious and unreliable —
and the ambiguity falls hardest exactly where it matters, on the question of
whether a change made after some version actually helped.

So every generated lifecycle artifact records the DevSpark version that
produced it. The convention is small on purpose. It is artifact-local, not a
central ledger: a spec records the version that authored it, a gate records
the version that produced that instance, and nothing accumulates a
`planned_with:` / `verified_with:` history inside the spec. It is truthful:
upgrading does not restamp existing artifacts, and a later command never
rewrites an earlier one, so a route legitimately shows its spec at one
version and its verify gate at a newer one. And it is additive: artifacts
without the field remain valid, nothing is migrated, and no business
semantics depend on it.

This is observability for the methodology, not analytics. No command
collects, aggregates, scores, or reports these values. The deliberate
omission is counting: findings, tasks, tests, and spec size are not success
measures, and instrumenting them would reward the wrong behavior. More
findings is not better assurance; more tests is not the right test. What the
provenance enables is a later, external, human question — *which specs were
authored under which version, and did the outcomes differ* — answered from
artifacts DevSpark already produces.

The convention is stated once in `templates/preamble/provenance.md`,
and resolved through one shared version helper so no prompt invents its own
detection.

## Orchestration: rigor belongs inside the framework, not in the developer's head

Convergence needed a new lifecycle responsibility. It did not need a new
mandatory command, and the distinction is load-bearing:

> **Minimize required developer orchestration. DevSpark may use rich
> internal lifecycle states and specialist capabilities, but the normal
> developer path exposes only meaningful human decision boundaries.**
>
> **A new lifecycle responsibility does not automatically justify a new
> mandatory command.**

Internal rigor is supposed to *reduce* a developer's cognitive load. A
framework that answers every new responsibility with a new required prompt
eventually demands a workflow cheat sheet for ordinary work, and at that
point it has traded adoption for tidiness. If convergence made DevSpark feel
more bureaucratic, the design would have failed even with a cleaner
lifecycle model underneath.

The test for exposing a command is one question: **does meaningful human
judgment or authorization need to occur between these phases?** Evidence →
closeout does not — it is mechanical, so `/devspark-verify` runs both and
emits the completion decision in a single interaction. Closeout → PR does,
because the developer is deciding whether to act on that decision. A
proposal becoming authoritative Knowledge does. Pushing, tagging, and
publishing do. The principle has a converse that binds just as hard:
simplification is not a licence for an opaque command that silently
specifies, plans, implements, accepts limitations, revises hypotheses,
approves, and publishes. **Automate mechanical transitions; expose
consequential decisions.**

Capabilities and entry points are therefore different things. Closeout is a
*capability* invoked automatically by verify, and `/devspark-closeout` is an
optional reassessment entry point that runs the same contract for the cases
automation cannot reach — work that continued after verification, a
limitation accepted later, a decision gone stale. One contract, two ways in,
never two implementations that can drift apart. The normal path stays
`specify → plan → implement → verify → create-pr → pr-review`, with
`/devspark-next` above all of it for anyone who would rather not memorize
even that. The per-command classification — happy path, advanced, internal,
diagnostic — is in `devspark-prompt-mapping.md`.

## Minimum Sufficient Change: the counterweight to completeness

> **Minimum Sufficient Change.** Build the smallest complete solution that
> satisfies the current objective, explicit requirements, invariants, and
> demonstrated operating constraints. Prefer simpler and more local solutions
> over speculative flexibility. Future usefulness alone does not justify
> present complexity.

Assurance finds risks, and a risk is cheap to turn into machinery. Left
unchecked, finding → remediation → new machinery → new findings ratchets a small
change into a large one. Three named ideas hold the line: **MVP** (the
smallest valuable outcome, with non-scope stated up front), **KISS** (the
simplest safe design, and the least powerful mechanism that satisfies the
requirement), and **YAGNI** (no behavior, state, configuration, or
extensibility for hypothetical needs). **Complexity is a cost that requires
justification**, and *complete* means completely satisfying today's justified
needs, not anticipating every future one. The boundary is just as firm in the
other direction: correctness, security, safety, data integrity, and explicit
contracts are not optional simplifications.

It is a rule of reasoning, not a gate. Specify records the minimum valuable
outcome and what is explicitly not required; Plan records the operating context
and the *expected* mechanism shape (expected counts are not limits, only a
shape that deviations must explain); Critic proposes the least-complex
mitigation first and never prescribes architecture; Judge asks what can be
removed while every forcing requirement still holds. The normative text is
`templates/command-preamble-contract.md` §13.

Minimum Sufficient Change applies to governance as well as implementation. Once implementation
begins, an agent must not silently widen scope; a human may explicitly authorize a bounded
correction needed to complete the existing objective. Record the authorization in the current
feature artifacts, make the minimum correction, and satisfy every applicable verification and
freshness obligation. A changed file list alone does not require a new feature or a full lifecycle
restart. Material changes to the objective, design, invariants, security, or data contracts still
require the existing authoring and review decisions.

Two related mechanics keep Planning Review honest. A human decision that has
not happened is an *unset resolution*, not a made-up one, so it cannot leak into
tasks or future work. And each child artifact records the Planning Review run
that generated it or accepted it for reuse, so Judge can tell its own children
from an unexpected concurrent overwrite, without locks or a run database.

## The `.archive/` retention: preserving short-lived value without keeping it active

A spec that hasn't yet produced a committed delta represents real, if
short-lived, value — and an agent-driven removal of a file that was never
committed is unrecoverable even though Git is technically the system of
record for everything that *was* committed. Rather than accept that gap,
`/devspark-release` — the command that sweeps completed planning bundles
and routine work products — moves them out of the active tree instead of
deleting them outright, once they meet their applicable completion rules.

`/devspark-implement` deliberately does **not** do this: it
populates a spec or quickfix record's `code_ref`/`knowledge_ref` linkage and
leaves the record exactly where it is, live in `.devspark.work/`, for as
long as the sprint needs it — that linkage is what lets anyone validate the
delta against code, tests, and knowledge while it's still there. A record
can sit verified-but-unarchived across more than one release window before
`/devspark-release` finally sweeps it; that's normal, not a stall.

**Mechanics:**

- On confirming a spec or quickfix's linkage is still populated — never for
  a stalled or incomplete record — `/devspark-release`'s archive step moves
  the entire spec package intact into `.archive/{YYYY-MM-DD}/` (preserving
  its relative path minus the `.devspark.work/` prefix) instead of deleting
  it. Whole package, not a summary: plan, tasks, checklists, gates,
  `context_resolved` — deciding now what a human might want to see later
  would be the same premature judgment call the model avoids everywhere
  else.
- `.archive/` is a repository-owned root alongside `.devspark.work/` and
  `.knowledge/` — retiring resolved
  `.devspark.work/` planning artifacts, never a parallel history for
  `.knowledge/`. `/devspark-release`, `/devspark-constitution`, and
  `/devspark-evolve-constitution` are the only commands that write to it,
  moving eligible archive-eligible/retention/orphan/proposal content there.
  Writing is the only direction any command ever takes. `/devspark-release`
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

- **Design time** (specify → plan → tasks) does the bounded ontology
  traversal — projection to a maximum of two hops from the lexical seeds —
  and pins the result down as an explicit `context_resolved` list in the
  ephemeral spec package — the same
  ephemeral-artifact-points-at-permanent-record shape as task-level
  `code_ref` / `knowledge_ref`, safe under rule 1's one-way gate, and it
  disappears when the spec does. Flat documents, entities, entity layers,
  and decisions are all first-class entries; a resolved set containing no
  entities at all is complete, not deficient.
- **Analyze** gates on resolution *validity* — every id and relation
  named in `context_resolved` must actually resolve against the current
  ontology, whatever its kind. Mechanical, hard-stop: a stale or
  hallucinated reference fails outright, the same class of check the
  generator already runs on `relations[].object`.
- **Critic** gates on resolution *sufficiency* — does `context_resolved`
  look complete for the delta being planned. Adversarial, judgment-based,
  not a hard stop — the natural place to ask "what did design time miss."
- **Implement** takes at most one additional hop beyond what it was given;
  it consumes `context_resolved` as already-resolved context. An escalation
  past that hop during implement is an attributable signal rather than a vague
  shortfall: frequent escalation on one pair means the ontology's
  relations are too sparse and an edge should be added directly; escalation
  despite a passing `context_resolved` means critic isn't catching
  sufficiency gaps and that prompt needs tightening; an analyze failure
  means the spec itself named stale or hallucinated context, a spec-quality
  problem rather than a gate problem.
