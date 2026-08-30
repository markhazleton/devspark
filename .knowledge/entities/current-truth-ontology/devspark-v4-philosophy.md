# DevSpark v4 Philosophy & Guide: Plan Temporarily, Review the Delta

## The core shift

A spec is not a record. A spec is a **temporary definition of a delta** — the
change we intend to make to our code and to our knowledge. It exists only to
produce that delta correctly. Once the delta has landed — code changed,
knowledge updated, governance updated if affected — the spec has completed
its purpose and is moved out of `.devspark.work` into `.archive/YYYY-MM-DD/<topic>/`.
It is never referenced again by code, knowledge, or an agent, and nothing about
it persists in the current-truth model.

This is a stronger claim than "we choose not to keep spec history." The spec
was never meant to be history in the first place. There is no
spec-vs-code drift to manage, because nothing persists in current truth that
could drift — and, as established below, there is no such thing as "cross-spec
drift" either, because specs don't have enough identity after archival to have
interacted with one another. What's left to check is always synchronic:
does the current state hold together, never "did these two past changes
conflict."

## The governing principle: current truth, not lifecycle history

The repository reflects **what is true now** — current code, current
knowledge, current governance. Historical content ("how we used to do
this") does not live in the repo. It doesn't help an agent execute today's
task; at best it's noise, at worst it actively misleads an agent into
thinking a rejected approach is still valid.

History for committed states lives in Git. `.archive/` may preserve recent
uncommitted or between-release work for human recovery, but nothing in the
day-to-day current-truth graph exists to serve that need.

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
  place.** It is not superseded by a new ADR. There is no chain of
  "decision 1, revisited in decision 2, revisited again in decision 3" —
  exactly one current file may exist per topic at any time.
- Decisions are keyed by **domain/topic**
  (`governance/decisions/auth-strategy.md`), never by sequential creation
  order. Sequential numbering is a historical-tracking device baked
  directly into the naming convention and contradicts current-truth
  discipline on its face.
- If a decision becomes moot entirely (the subsystem it governed no longer
  exists), it is removed from current truth. Git keeps committed history.

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
a decision declares which entities it governs (`governs:`), and each
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

## What triggers assimilation

Assimilation — merging a completed delta's knowledge into the permanent
record — is not a periodic sweep decoupled from any individual unit of
work. The DevSpark prompt set groups into three phases, and the
downstream/repo-wide prompts (PR review, audit, harvest) are the ones that
carry assimilation forward:

- **Plan & build** — specify, plan, tasks, analyze, critic. Produces the
  ephemeral spec package.
- **Implementation** — implement. Applies the delta to code and knowledge
  together, in one disciplined pass. No longer tracks specs, requirements,
  or tasks as comments in code — that was always going to need cleanup
  later, so it should never be created in the first place.
- **Validation** — PR review, PR review site audit, repo-history/harvest.
  These pivot to validate and enforce knowledge/code linkage and
  consistency, rather than checking spec completion (which stays implement's
  job).

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
   the ephemeral thing leaves `.devspark.work`, the reference leaves active
   work with it — nothing is left dangling in code, knowledge, or governance.
   References to anything
   *outside* the repository (an RFC, a vendor API doc, a business
   objective) are unrestricted in either direction — those are stable by
   construction and can't leak the way an internal ephemeral pointer can.
2. **Verify before archive.** A spec cannot leave `.devspark.work` until its
   delta is verified as landed in code, knowledge, and governance (if touched).
   There is no going back to active work once a spec moves to `.archive/`, so
   this ordering is the model's entire integrity check.
3. **Evidence required, always.** Every knowledge object and every decision
   cites at least one piece of evidence. Which type is a warning-level
   quality question (see above); that *some* evidence exists at all is
   non-negotiable — a claim with nothing backing it isn't checkable, which
   breaks the guarantee outright rather than just making it more expensive
   to verify.
4. **One current file per decision topic.** Never a chain, never a
   superseded pair coexisting. If two files can both claim to govern the
   same topic, "current truth" stops meaning anything.
5. **No ephemeral-artifact references in code**, implied by rule 1 but
   worth stating on its own since it's the clearest and most immediately
   checkable instance of it: no code comment references a spec ID, task
   ID, or plan identifier.

## In-flight linkage: how verify-before-archive actually gets checked

Rule 2 says a spec cannot leave `.devspark.work` until its delta is verified as
landed.
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
safe because the pointer leaves active work with the task when the spec is
moved to `.archive/YYYY-MM-DD/<topic>/`. Verify-before-archive then reads as a mechanical
check — no spec leaves `.devspark.work` while any task lacks a populated
`code_ref` and `knowledge_ref` (or an
explicit `n/a` with a reason, mirroring the `fallback_reason` pattern
already used for evidence). `.devspark.work` was already the designated
home for in-flight state; this is what it was for — the task list itself
*is* the tracked state, and its pointers are what verification checks
before the whole package is moved to `.archive/YYYY-MM-DD/<topic>/`.

One edge case worth naming rather than designing around: a task's
`code_ref` is checked for existence at verification time, not continuously.
If code is refactored again after the pointer is written but before the
spec is archived, the pointer can go briefly stale for the remainder of the
spec's short life. Low risk given specs are meant to be short-lived, and not
worth building continuous checking for something ephemeral.

## The ontology implementation: `.knowledge/ontology/`

The philosophy above is now specified concretely against a working pilot
schema (`.knowledge/ontology/schema.md`, generated coverage at
`.knowledge/ontology/coverage.generated.md`), living inside `.knowledge/`
rather than as a fifth root:

- **Decisions live at `.knowledge/governance/decisions/`**, as markdown
  with frontmatter — not as `_entity.yaml`-style nodes — because a
  decision's body is prose for humans ("what we do, why not the
  alternatives"), matching the existing knowledge-layer-doc contract rather
  than the pure-structural entity-node contract. Frontmatter carries `id`,
  `governs` (entity ids this decision governs), `status` (`current` |
  `deprecated` — no `proposed`, since an undecided decision is still a spec,
  not a decision), `evidence`, and `last_verified`. No `layer` key — a
  decision is one document, one topic, not a multi-view entity.
- **`governs` / `constrained_by` is a generated, inverted pair.**
  `governs` is hand-authored on the decision. `constrained_by` is never
  hand-written on the entity — it's derived by inverting every decision's
  `governs` list, the same way `coverage.generated.md` is already derived
  rather than hand-maintained. It's written to a **sibling file**,
  `.knowledge/entities/<id>/_derived.yaml`, not mixed into the hand-authored
  `_entity.yaml` — keeping generated and hand-authored content in separate
  files avoids ambiguity about which fields are safe to edit, and keeps
  each file small enough that an agent doing a one-hop lookup only loads
  what that specific question needs. `_derived.yaml` is the general home
  for *any* generator-computed per-entity fact, not just `constrained_by` —
  new derived facts join it rather than spawning new sibling files.
- **Drift detection closes the loop.** A read-only run of the generator
  (no `--write`) computes `constrained_by` fresh in memory and compares it
  against what's on disk in `_derived.yaml`; a mismatch is reported as a
  validation warning, not silently corrected. Only `--write` actually
  regenerates the file. This means hand-tampering with a generated file
  surfaces as a signal before it's erased, rather than failing invisibly at
  the next write pass.
- **Evidence typing extends the existing `source_of_truth` field** rather
  than replacing it outright: entries gain `type` (`test` | `code`),
  `verified_by` (`execution` | `inspection`), and for code-only entries,
  `test_attempted` and `fallback_reason`. This is what turns `last_verified`
  from a human's memory of when they last looked into something the
  generator can partly check itself — `execution`-verified claims are
  re-checked by literally running the cited test; `last_verified` stays
  meaningful only for `inspection`-verified claims, where it's genuinely a
  human attestation with no mechanical substitute yet.
- **Existence and accuracy are two separate reports.** The existing
  coverage matrix answers "does the required layer's document exist" — it
  says nothing about whether an existing document's claim still matches the
  code. A second report (evidence pass/fail, resolving each `execution`
  entry and running its test) is needed to catch documents that exist but
  are wrong, which the current gap report cannot see.
- **This tooling moves inside the DevSpark lifecycle, not beside it.**
  Implement writes evidence and task linkage as part of closing a delta. PR
  review runs the generator (and the new evidence-accuracy pass) as a
  required step before approval — gap-report failures on touched entities
  gate; missing `fallback_reason` warns. Audit runs the same tooling
  repo-wide, scoped to graph-adjacent objects (same entity, entities
  sharing a `governs` decision, objects citing the same evidence) rather
  than brute-force pairwise comparison, to triage the existing gaps and
  catch relation-based contradictions.

## Prompt inventory

Every `devspark.*` command mapped against this philosophy, with updated
purpose guidance per command and shim gaps prioritized by v4 relevance, is
in the companion document `devspark-v4-prompt-mapping.md`. Headline items:
`implement` carries the heaviest new discipline (one-hop-only retrieval,
evidence preference, task linkage, verify-before-archive execution);
`pr-review` is the primary assimilation trigger; `harvest`'s role shrinks
to sweeping orphaned in-flight state now that pr-review and audit carry
continuous verification; and `devspark.verify` — currently missing both
shims — is the evidence-execution engine the test-evidence preference
depends on, making it the highest-priority gap to close.

## The `.archive` exception: human-only history, deliberately outside the model

Removal from active work under rule 2/5 is real removal from the model's
working surface — nothing lingers in `.knowledge`, code, or governance.
But some developers reasonably find "the agent deleted a file" unsettling
even when Git makes it fully recoverable, and there's a legitimate,
distinct need underneath that discomfort: a spec-level view of "what
happened since the last release" that Git's commit-by-commit history
doesn't present comfortably.

The resolution is not to keep specs around inside the model — that would
just relocate the archive problem the whole redesign exists to eliminate.
It's to give humans a channel the model doesn't know exists at all.

**Mechanics:**

- On completing verify-before-archive — only after every task's `code_ref` /
  `knowledge_ref` are confirmed populated, never for a stalled or
  incomplete package — `implement`'s final action moves the entire spec
  package intact into `.archive/YYYY-MM-DD/<topic>/`. Whole package, not a
  summary: plan, tasks, checklists, gates, `context_resolved` — deciding now
  what a human might want to see later would be the same premature judgment
  call the model avoids everywhere else.
- `.archive/` is a top-level dotfolder, structurally outside the four-root
  model — not a fifth root DevSpark manages, the same way `.git` isn't
  something any DevSpark command touches. It does not live under
  `.knowledge` (every prompt is built to scan that tree) or
  `.devspark.work` (explicitly the swept, temporary layer — mixing
  "temporary" with "permanent, human-only, never swept" in one root
  muddies what the four-root model is for).
- **No DevSpark command reads, lists, enumerates, or globs `.archive/`,
  under any circumstance, regardless of what it is searching for or why.**
  This is a Constitution-level rule, not a per-prompt convention left to
  every prompt author to remember — a future prompt that globs the repo
  tree for some unrelated reason must still exclude this path explicitly,
  by constitutional mandate, not by hoping every author remembers.
- The naming collision with the retired archive command is resolved: there is no
  archive prompt or shim. `.archive/` is a human-only folder name, not a
  DevSpark command surface.
- Purging is human-only and has no schedule enforced by the model — a
  human decides when `.archive/` no longer needs a given entry and deletes
  it directly, outside any DevSpark command.

**Why this isn't kept forever, stated plainly:** `.archive/` is a
deliberate, acknowledged risk, not a fully closed door. "No DevSpark command
reads `.archive/`" is a should-not enforced by instruction, not a cannot
enforced by architecture — it depends on every prompt actually honoring it,
and in practice agents have on occasion noticed the folder's existence and
referenced having found something there despite being told not to
acknowledge it. Strong, explicit, Constitution-level instructions reduce how
often this happens; nothing makes it impossible. There is no version of
this exception where an agent's ability to see `.archive/` can be
completely guaranteed to zero — that has to be stated honestly rather than
papered over with confident-sounding rule language.

Because the risk can be reduced but not eliminated at the instruction
layer, closing the gap the rest of the way is explicitly a **human
responsibility, not a system guarantee**: humans purge `.archive/` on a
timely basis, and that timeliness is the actual control, not the
instruction alone. The less that accumulates and the less time it sits
there, the smaller the window in which an instruction-following failure can
surface something real. This is deliberately not automated or scheduled by
any DevSpark command — automating it would just relocate the judgment call
("is this safe to remove yet") onto the model this whole exception exists
to keep out of the loop. The same principle that says "don't trust
encouragement alone, make it leave a trace" (evidence, `fallback_reason`)
applies here in reverse — don't trust an instruction alone either; bound
the blast radius through timely human action instead.

## No CLI, no harness — scripts and prompts instead

DevSpark v4 deliberately has no standalone CLI executable and no
programming harness. This isn't tooling minimalism for its own sake — it's
the same argument the rest of this philosophy makes about specs, ADRs, and
retrieval, applied to DevSpark's own tooling: push judgment to prompts,
where a capable agent can reason through context-dependent decisions, and
reserve deterministic execution for scripts that need no judgment at all.
A harness is the most literal form of a "dogmatic guardrail" possible — a
fixed program the agent executes *through* rather than a set of judgment
calls it makes *within*. Retiring it applies v4's own thesis to the
framework's own entry point, not just to the artifacts it produces.

There's a practical case alongside the philosophical one: the CLI wasn't
used, by its author or by anyone else consuming DevSpark, and unused
tooling that's constantly updated without a real test case is a liability
on maintenance grounds alone, independent of what it symbolized.

**Scripts are not the same thing as a CLI, and are actively encouraged.**
The distinguishing test: a script executes one deterministic operation with
no judgment involved, invoked directly by the prompt that needs it, when it
needs it. A CLI is a standing interface implying a strategy for interacting
with the framework, independent of any single prompt's need — competing
with prompts as the way work gets done, rather than serving them. Scripts
are the mechanical, no-judgment tier (same tier as `verified_by: execution`
evidence); prompts own everything requiring judgment; a CLI tries to
straddle both, which is exactly why it kept accumulating complexity nobody
was actually using.

The existing pilot already proves the pattern out:
`build_knowledge_index.py` and the migration scripts
(`migrate-to-four-root.py`, `migrate-knowledge-to-entities.py`) are all
small, single-purpose, testable in isolation, and invoked directly by name
— no dispatcher, no shared state between them, no subcommands. Nothing
about retiring the CLI changes their status; they were never the CLI's
concern. Scripts like these are the concrete mechanism that runs the
gap-report and evidence-accuracy checks `pr-review` and audit rely on.

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

## What's still open

One item remains genuinely unresolved — not because it wasn't designed, but
because it's a judgment problem by nature, not a design gap:

- **What counts as a contradiction versus an acceptable nuance**, once
  audit has a scoped, graph-adjacent set of objects to compare (same
  entity, entities sharing a `governs` decision, objects citing the same
  evidence). Scoping the search space is closed; judging semantic
  contradiction within that scope is not mechanized and isn't meant to be —
  it stays a permanent **warning surfaced for human review**, the same tier
  as a missing `fallback_reason`. This was deliberately kept simple rather
  than split into a structured/gate-eligible claims format: one discipline
  to remember (audit surfaces, human disposes) beats maintaining two
  contradiction-detection code paths for a narrow mechanical win.

## Retrieval — closed

Retrieval is resolved end to end by giving design time and runtime
different budgets, on the principle that complexity should be worked out
before code is written, not discovered while writing it:

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
  hop during implement is now an attributable signal rather than a vague
  shortfall: frequent escalation on one entity pair means the ontology's
  relations are too sparse and an edge should be added directly; escalation
  despite a passing `context_resolved` means critic isn't catching
  sufficiency gaps and that prompt needs tightening; an analyze failure
  means the spec itself named stale or hallucinated context, a spec-quality
  problem rather than a gate problem.

## Practical checklist for evolving the current implementation

- Does spec archival require verification to have already succeeded, or is
  archival a separate step that could fire on incomplete work?
- Are any ADRs numbered or chained by supersession? Rekey by domain/topic
  and collapse each chain to one current file, moved to
  `.knowledge/governance/decisions/` as markdown with frontmatter.
- Does `_derived.yaml` exist yet as a sibling to `_entity.yaml`, and does
  the generator regenerate it wholesale on `--write` and drift-check it
  otherwise?
- Does the evidence field distinguish `execution` from `inspection`
  verification, and does a code-only entry require `test_attempted` /
  `fallback_reason`?
- Does implement populate `code_ref` / `knowledge_ref` per task in
  `.devspark.work`, and does spec archival check every task has both
  populated (or an explained `n/a`) before proceeding?
- Does plan/tasks write `context_resolved` into the spec package, does
  analyze validate it resolves against the current ontology, and does
  critic check it for sufficiency?
- Do PR review and audit both check for repo-internal ephemeral references
  (spec IDs, task IDs) in code and knowledge, and reject on rule 1?
- Does audit's contradiction scan stay scoped to graph-adjacent objects
  (shared entity, shared `governs` decision, shared evidence) and surface
  findings as warnings for human review, rather than attempting to
  mechanize contradiction judgment or brute-force pairwise comparison?
- Is there any lingering "history" content anywhere in the repo — old
  specs kept "just in case," decision chains, changelog-style entries —
  that violates current-truth-only?
