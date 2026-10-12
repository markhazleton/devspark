# Philosophy: Plan Temporarily, Review the Delta

## The core shift

A spec is not a record. A spec is a **temporary definition of a delta** — the change intended for
code and for knowledge. It exists only to produce that delta correctly. Once the delta has landed —
code changed, knowledge updated, governance updated if affected — the spec has completed its purpose
and is archived out of `.devspark.work/` into `.archive/{YYYY-MM-DD}/`. It is never
referenced again by code, by knowledge, or by an agent, and nothing about it influences current
behavior once archived — its content is retained only as an inert historical copy, not as active
planning state.

This is a stronger claim than "we choose not to keep spec history in active view." The spec was
never meant to be *active* history in the first place — once archived, it is inert. There is no
spec-vs-code drift to manage, because nothing in the active repository state persists that could
drift — and there is no such thing as cross-spec drift either, because archived specs don't have
enough identity to have interacted with one another. What's left to check is always synchronic:
does the current state hold together, never "did these two past changes conflict."

## Current truth, not lifecycle history

The repository reflects **what is true now** — current code, current knowledge, current governance.
Historical content ("how we used to do this") does not live in the repo. It doesn't help an agent
execute today's task; at best it's noise, at worst it actively misleads an agent into thinking a
rejected approach is still valid.

History isn't deleted from existence — it lives in Git. Version control is the *only* place "what we
used to do" is recoverable. Nothing in the day-to-day repo structure exists to serve that need.

## Three categories of current truth, not one

Everything durable in the system answers one of three different questions. Confusing these
categories is what produces the ADR/spec/knowledge muddle this model removes:

| Category | Question it answers | Who mainly needs it | Change model |
|---|---|---|---|
| `.knowledge/` (entities) | What is true now? | Agent, to act correctly today | Mutated in place |
| Governance: Constitution | What are the rules of the game? | Agent and human, rarely changes | Mutated in place, amended explicitly |
| Governance: Decisions | What did we choose, and why not the alternatives? | Human, revisiting a choice; agent, checking a constraint | Mutated in place |

Governance — the constitution and decisions — lives *inside* `.knowledge/governance/`, not as a
fourth, separate root. All three categories are current-state documents. None is an archive. They
differ in content, not in lifecycle discipline.

## Decisions are current governance, not history

A decision doc is not "here's everything we tried." It is "here is what we do, and here is why we
don't do the alternatives" — a present-tense claim.

- When the reasoning behind a decision changes, **the decision file is edited in place.** A new file
  never takes over for it. There is no chain of "decision 1, revisited in decision 2" — exactly one
  current file may exist per topic at any time.
- Decisions are keyed by **domain/topic** (`governance/decisions/auth-strategy.md`), never by
  sequential creation order. Sequential numbering (`0001-`, `ADR-003-`) is a historical-tracking
  device baked directly into the naming convention, and it is rejected outright.
- If a decision becomes moot entirely, it is deleted — not archived. Git still has it.

Decisions are cross-cutting by nature — they constrain multiple entities, or the framework itself —
so they live in governance rather than inside any single entity's folder. The mechanism that keeps
entities complete without duplicating governance content into them: a decision declares which
entities it `constrains`, and each constrained entity carries a lightweight pointer back
(`constrained_by`) in its own metadata, generated rather than hand-written. The existence of a
constraint is always visible from the entity itself, without the entity owning the reasoning behind
it — that stays singular in governance.

## Evidence: every claim must be checkable

Every knowledge object and every decision must cite at least one piece of evidence — something that
lets an agent verify the claim is still true rather than taking it on faith:

- **Test evidence** (`verified_by: execution`) — the claim holds if and only if the cited test
  currently passes. Mechanical, cheap, no interpretation required.
- **Code evidence** (`verified_by: inspection`) — the claim requires a human or agent to read the
  code and judge whether it still matches. Slower, and still needs human oversight.

A test reference is preferred over a bare code reference wherever practical, because it converts a
judgment call into a mechanical check — encouraged, not enforced. A code-only entry must record
whether a test was attempted and, if not used, why:

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

A code-only entry **missing** `fallback_reason` is a warning, surfaced independently by both site
audit and PR review — never a gate. *Which* evidence type is a quality question; *that* evidence
exists at all is not.

When a topic is missing from knowledge or has drifted from code, `/devspark-explain` asks for
clarification if ownership, scope, or intent is unclear. Once the finding is understood and the
human confirms the proposal, it updates the owning knowledge document and its durable references,
or creates a typed node when no owner exists. Durable knowledge cites durable code and tests only;
the temporary spec, plan, task, or quickfix record carries the inverse traceability through its
linkage fields.

## What triggers assimilation

Assimilation — merging a completed delta's knowledge into the permanent record — is not a periodic
sweep decoupled from any individual unit of work:

- **Plan & build** (specify, plan, tasks, analyze, critic) produces the ephemeral spec package.
- **Implementation** (implement) applies the delta to code and knowledge together, in one
  disciplined pass. It never tracks specs, requirements, or tasks as comments in code.
- **Validation** (PR review, site audit, explain) pivots to validate and enforce
  knowledge/code linkage and consistency, rather than checking spec completion. Explain is the one
  skill in this phase that also remediates a drift it finds, topic-scoped, after confirmation —
  the others only report it.

PR review is the natural trigger point because nothing merges without one — the PR diff itself (not
the spec, which may already be gone) is what proves a delta's code and knowledge changes actually
landed together. Site audit's job is different in kind: not per-diff consistency, but scanning
current knowledge for internal contradiction and for claims whose cited evidence no longer holds.

## The five non-negotiable rules

A rule belongs on this list only if violating it falsifies the core guarantee — that the permanent
record is current-truth-only, checkable, and contains no trace of the ephemeral scaffolding that
produced it. Everything else is quality, and belongs in "encourage," not "gate."

1. **Closed reference graph, one direction only.** The permanent record — code and
   knowledge/governance documents — may only reference each other, never a spec, task, plan, PR
   thread, or any other repo-internal ephemeral artifact. The inverse direction is encouraged: an
   ephemeral artifact referencing the permanent record is safe by construction, because the
   reference goes inert with it once it's archived out of `.devspark.work/`. References to anything
   *outside* the repository are unrestricted in either direction.
2. **Verify before archive.** A spec cannot be archived until its delta is verified as landed in
   code, knowledge, and governance (if touched). Recovery after archiving is a human action: manually
   copying the file back out of `.archive/{YYYY-MM-DD}/` (no DevSpark skill reads `.archive/`),
   not reconstructing it from nothing.
3. **Evidence required, always.** Every knowledge object and every decision cites at least one piece
   of evidence.
4. **One current file per decision topic.** Never a chain, never two files both claiming to govern
   the same topic at once.
5. **No ephemeral-artifact references in code.** No code comment references a spec ID, task ID, or
   plan identifier.

## Verify-before-archive, in practice

Every task tracked during implementation carries a live pointer to where it landed:

```yaml
- id: task_003
  description: "Add token refresh retry logic"
  status: complete
  code_ref: src/Auth/TokenService.cs::RefreshToken
  knowledge_ref: entities/token_service/architecture.md
```

No spec is archived while any task lacks a populated `code_ref` and `knowledge_ref` (or an explicit
`n/a` with a reason). The task list itself *is* the tracked state, and its pointers are what
verification checks before the whole package is moved to `.archive/{YYYY-MM-DD}/`.

## Retrieval budget: resolved at design time, consumed at implement time

Complexity is worked out before code is written, not discovered while writing it:

- **Design time** (specify → plan → tasks) projects to a maximum of two hops from its lexical seeds
  and pins the result down as an explicit `context_resolved` list in the ephemeral spec package.
  Flat documents, entities, entity layers, and decisions are all first-class entries.
- **Analyze** gates on resolution *validity* — every id and relation named in `context_resolved`
  must actually resolve against the current knowledge corpus, whatever its kind. A stale or
  hallucinated reference fails outright.
- **Critic** gates on resolution *sufficiency* — does `context_resolved` look complete for the delta
  being planned. Judgment-based, not a hard stop.
- **Implement** takes at most one additional hop past `context_resolved`. An escalation past that
  hop is logged as an attributable signal, not a silent failure.

## See also

- [Skill Catalog](../guides/prompt-lifecycle-mapping.md) for how each `/devspark-*` skill
  carries this philosophy forward.
- [Evidence and Evaluation](evidence.md) for how to evaluate a repository under this model.
