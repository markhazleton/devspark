---
id: knowledge-framework-contract
type: governance
title: "Knowledge Framework Contract"
appliesTo:
  - templates/schemas/knowledge-node.schema.json
  - templates/schemas/entity-node.schema.json
  - templates/schemas/knowledge-ontology.json
  - scripts/build_knowledge_index.py
  - scripts/context-projection.py
  - scripts/explain-context.py
  - scripts/discover-knowledge.py
  - scripts/knowledge-integrity.py
  - templates/commands/pr-review.md
links:
  references:
    - governance-constitution
    - governance-devspark-philosophy
    - content-lifecycle
    - developer-guide
---

<!-- markdownlint-disable MD025 -->

# Knowledge Framework Contract

This is the authoritative contract for DevSpark Knowledge. Every command, prompt, script, schema,
indexer, discovery process, bootstrap workflow, and review gate that creates, validates, indexes,
retrieves, projects, or consumes Knowledge conforms to this document. Where a surface needs to
behave differently, it declares the difference and the reason rather than encoding a private
variant.

Governing authority is [constitution.md](constitution.md), Principle X (Knowledge Currency). The
reasoning behind the model is in [devspark-philosophy.md](devspark-philosophy.md). Authoring
mechanics live in [../tooling/developer-guide.md](../tooling/developer-guide.md) and
[../tooling/content-lifecycle.md](../tooling/content-lifecycle.md). This document sits between
them: it defines the invariants both must satisfy.

## 1. Purpose

Knowledge exists to give a coding agent **the smallest trustworthy set of current software context
necessary to safely and effectively perform the job at hand.**

Optimize for correctness, relevance, current truth, evidence, consistency, and bounded context.
Do not optimize for maximum documentation, maximum retrieval recall, maximum graph traversal, or
maximum context volume.

The measure of a healthy Knowledge corpus is not how much of the system it describes. It is whether
an agent can start a task without rediscovering the architecture, and finish it without reading
material unrelated to the change. It must remain accurate after both planned and Code First Deltas.
When a Delta makes Knowledge obsolete or redundant, update or retire that current truth in the same
change; do not preserve a misleading node for the sake of historical coverage.

## 2. What Knowledge is

**Knowledge means durable current software truth stored under `.knowledge/`.**

Knowledge MAY describe architecture, business and domain behavior, integrations, operational
behavior, engineering patterns, source ownership, relationships between durable concepts, and
governance decisions.

Knowledge MUST NOT exist merely to preserve implementation history. Knowledge MUST NOT carry
ephemeral traceability — a spec number, a requirement identifier of the form `FR-<number>`, a task
identifier of the form `T<number>`, a quickfix identifier, a pull-request number, or a branch name
— unless that identifier is itself part of the durable software contract.

Traceability is one-directional:

```text
temporary work artifact
        │ references
        ▼
  Code / Tests / Knowledge
```

The inverse is prohibited. Durable content never depends on a temporary planning record, because
that record is swept out of the working roots once its delta has landed, and anything pointing at
it would be left dangling.

## 3. Reserved terminology

The term **Knowledge** is reserved for authoritative `.knowledge/` current truth.

Spec-local feature, requirement, and task documents generated into a feature's folder under
`.devspark.work/specs/` are **work products**, not Knowledge. They are ephemeral by construction:
they carry planning identifiers, they hold a lifecycle state, and they are swept out at release.
Calling them Knowledge collides with the reserved term and makes every statement in this contract
ambiguous.

The current repository ships a work-product schema that uses the reserved term. Recommended
disposition, in preference order:

1. **Retire it.** Durable traceability is carried by the temporary planning record citing code,
   tests, and Knowledge. No command prompt invokes the work-product validators today.
2. **Rename it** if a consuming team depends on the format — to a name that does not use the word
   Knowledge — preserving behavior at a documented framework-version boundary per Principle I.

Either disposition is a follow-up, recorded in §24. This contract does not perform it, and it does
not change the behavior of any existing script.

## 4. The canonical Knowledge Model

```text
            AUTHORITATIVE SOURCE
          .knowledge/ source files
                    │
                    ▼
         shared canonical builder
                    │
                    ▼
        Canonical Knowledge Model
          ┌─────────┼──────────┐
          ▼         ▼          ▼
      retrieval  integrity  projection
                    │
                    ▼
       deterministic serialization
          ├── index.json
          └── ontology/coverage.json
```

- `.knowledge/` source files are **authoritative**. Nothing else is.
- The in-memory model produced by the shared builder is the **canonical interpretation** of those
  files. Validation, typing, edge materialization, coverage, and ownership resolution happen there
  and only there.
- `index.json` and `coverage.json` are **derived deterministic artifacts**, used for inspection,
  diagnostics, and interoperability. They are regenerated, never hand-edited, and byte-stable
  across operating systems.

The invariant is **one authoritative corpus, one canonical interpretation of it** — not "every
consumer loads the same JSON file". A consumer MAY rebuild the model through the shared builder
instead of reading the serialized artifacts, and that satisfies this contract. What a consumer MUST
NOT do is parse `.knowledge/` frontmatter itself, apply its own typing or validation rules, or
construct its own notion of an edge. Exactly one implementation interprets the corpus.

The serialized artifacts are build output, not authority. Regenerating them is optional and a stale
or missing copy never blocks a change; the check that matters is that the Knowledge builds
(`build_knowledge_index.py --check`).

## 5. Two supply workflows

Knowledge reaches the corpus through exactly two workflows, and they answer different questions.

### Baseline bootstrap

```text
Existing Code + Tests + Docs + Decisions
                │
                ▼
         baseline analysis
                ▼
       proposed Knowledge model
                ▼
          review / approval
                ▼
      authoritative .knowledge/
```

For a mature repository adopting DevSpark. It asks: *given an established Code and Test corpus,
what authoritative baseline should exist before new specs begin?* It runs once, and may be resumed
across sessions until the baseline is trustworthy.

### Continuous maintenance

```text
intentional Delta (planned or already implemented)
      ▼
Code changes · Tests change · Knowledge changes when durable truth changed
      ▼
   Delta-scoped verification / PR review
```

For a repository already operating under DevSpark. It asks nothing; it is an obligation that
attaches to every change that alters durable behavior.

Two rules follow, and they are the reason both workflows exist:

> **Knowledge maintenance is continuous; Knowledge discovery is periodic.**
>
> **The best time to author Knowledge is when the code makes the truth evident. Discovery exists
> for the truths we missed.**

Bootstrap is not discovery, and discovery is not a substitute for bootstrap. A repository that
never bootstraps will accumulate advisory findings it has no baseline to reconcile against.

## 6. Flat documents and entities

Both forms are first-class and permanent. Neither is a transitional state toward the other.

**Use a flat document** when the truth is self-contained and narrow, is unlikely to need multiple
semantic layers, and is unlikely to participate meaningfully in architectural relationships. Most
governance, reference, and operational guidance is flat and should stay flat.

**Use an entity** when a durable concept benefits from one or more of: multiple Knowledge layers,
explicit source ownership, aliases, relationships to other concepts, governance constraints, or
Context Projection.

Entity boundaries reflect **software concepts**, not folders. Directory size MUST NOT define an
entity. Filesystem location MUST NOT be the primary semantic test. A repository is not required to
convert any subsystem into an entity, and a mostly-flat corpus is a legitimate steady state.

**Flat Knowledge is the default.** An entity exists only when a durable concept benefits from
multiple independently useful facets, graph identity, or distinct ownership and drift accounting.
File count and directory spread are evidence that a concept might be significant; neither is
justification on its own. A concept MUST NOT become an entity merely because an automated process
found enough files to fill one.

### 6.1 Classification: form and role

Every Knowledge artifact carries **two independent classifications**. Collapsing them into a single
`type` field is what previously made a valid entity layer permanently unclassifiable: its form is
`entity-layer` while the truth it carries is the layer it documents, and one field cannot hold both.

**Form** is the structural kind of artifact. It is derived from the artifact's location and shape,
is never assignable by the taxonomy registry, and is not an editorial choice:

| Form | Where it lives |
|---|---|
| `flat-document` | A standalone document under `.knowledge/` |
| `entity-layer` | A facet document under `.knowledge/entities/<id>/` |
| `governance-decision` | A present-tense decision under `.knowledge/governance/decisions/` |

**Role** is the kind of truth the artifact carries. Each form draws its role from its own domain:

| Form | Role vocabulary |
|---|---|
| `flat-document` | `authoritative-reference`, `engineering-pattern`, `reference-data`, `operations-runbook`, `research-or-context`, `architecture`, `governance` |
| `entity-layer` | its `layer` — `architecture`, `business`, `integration`, `operations`, `pattern`, `plan` |
| `governance-decision` | `governance` |

**Only a flat document's role is assignable by the taxonomy registry.** An entity layer's role is
its layer and a decision's role is governance — both structural. A path mapping therefore cannot
disagree with them, and reporting such a disagreement is a defect in the reporter, not a finding
about the corpus.

Path mappings resolve **most-specific-first**, independent of declaration order. A repository
override outranks a built-in default only as a tiebreak at equal specificity. Two mappings of the
same origin and specificity that assign different roles are genuinely ambiguous and MUST fail
loudly rather than resolve by list position.

**Form is derived, never authored.** It is computed in this order:

1. a recognized entity-layer location — `.knowledge/entities/<id>/`
2. a recognized governance-decision location — `.knowledge/governance/decisions/`, excluding
   navigational filenames (`README.md`, `index.md`)
3. `flat-document`

A file that indexes a directory is **navigation, not a member of it**. That is why a `README.md`
beside a set of decisions is a flat document, and it is recognized by filename rather than by
anything the document asserts about itself. Frontmatter MAY restate the resulting form but MUST
NOT select it: a declared form contradicting the artifact's location MUST fail the build. Authored
metadata outranks inference on an axis the author owns, but it may never override a structural
fact — otherwise any file could claim to be an entity layer without belonging to an entity.

**Role may be authored** where the author owns the axis. On a flat document an explicit `type`
means the role and nothing else, and it outranks the taxonomy. An entity layer's role is its
`layer` and a decision's is `governance`; neither may be overridden.

| Form | Role comes from | Author may override |
|---|---|---|
| `flat-document` | explicit `type`, else taxonomy, else `authoritative-reference` | Yes |
| `entity-layer` | the document's `layer` | No |
| `governance-decision` | always `governance` | No |

The single `type` field remains in derived artifacts for compatibility, carrying its exact
historical values — the role for a flat document, the form otherwise. `form` and `role` are
canonical. A consumer reading structure MUST read `form`; a consumer reading the kind of truth MUST
read `role`. No consumer should have to decide which meaning of `type` was intended.

| Concept | Canonical | Compatibility | New authors write |
|---|---|---|---|
| Form | `node.form` | `node.type`, when not a flat document | nothing — derived |
| Role | `node.role` | `node.type`, when a flat document | `type` on flat docs; `layer` on layers |
| Entity type | `entity.type` | `entity.type` — never overloaded | `_entity.yaml` `type` |

These combinations are settled:

| Combination | Verdict |
|---|---|
| `flat-document` with role `entity-layer` | Invalid — a form is not a role |
| Frontmatter declaring a form its location contradicts | Invalid — build fails |
| `entity-layer` declaring `links` | Invalid — build fails |
| `governance-decision` with a role other than `governance` | Invalid — role is structural |
| Entity layer without a parent `_entity.yaml` | Invalid — build fails |
| Unknown entity type | Invalid — materialization blocked |
| Entity type with no corresponding layer | Valid — type never mandates coverage |
| `appliesTo` and `source_of_truth` naming the same path | Valid — different claims |
| Two entities owning one path | Valid but reported for review |
| Explicit role differing from a broad taxonomy glob | Valid — the precedence rule working |

### 6.2 Entity type

An entity declares a `type` from a closed vocabulary. It classifies **what kind of concept the
entity is**, and is distinct from the `layer` of any document inside it:

| Entity type | Meaning |
|---|---|
| `subsystem` | An internal capability of the system this repository builds |
| `domain` | A business or problem-space concept whose rules originate outside the code |
| `integration` | A boundary with an external system, protocol, or third-party service |
| `tooling` | Developer-facing automation that supports delivery rather than being shipped |

`integration` deliberately appears as both an entity type and a layer name: an entity may *be* a
boundary, or merely *have* an integration facet. The names coincide; the axes do not.

Entity type is **advisory and never mandates layer coverage**. Layer coverage stays evidence-driven:
a layer exists because evidence supports it, not because a type implies it. An authoring tool MUST
require an explicit, valid entity type rather than guessing one, and MUST NOT invent a placeholder
owner — placeholder metadata is indistinguishable from authored truth once written.

**When no type can be chosen confidently, the entity is not materialized.** There is no fallback
type and nothing silently becomes a `subsystem`. Uncertain classification blocks entity
materialization, not concept discovery: the concept may still stand as a proposal awaiting a human
decision, or be authored as flat Knowledge. What is withheld is authoritative identity, not
recognition of the idea.

The vocabulary is **closed to tooling and open to deliberate change**. No tool may mint a new
entity type at runtime. Adding one requires repository evidence that the concept recurs, a semantic
distinction no existing type already carries, no overlap with an existing type, a schema update,
contract tests, and an amendment to this section.

The authoritative machine-readable form of every vocabulary in this section is
`templates/schemas/knowledge-ontology.json`. Tooling reads it rather than restating these lists.

## 7. Entity evidence

Entity identification MUST be layout-independent. A concept spread across a feature folder tree
with its tests in a separate project is the normal shape of a real system, not an edge case.

Admissible evidence:

- repeated domain terminology across multiple implementation locations;
- tests referring to the same concept, wherever those tests physically live;
- the concept appearing in multiple architectural roles;
- a public or exported API surface;
- durable data or business behavior;
- an integration boundary;
- configuration or operational responsibility;
- governance that applies to the concept.

Two requirements:

1. **Cluster by concept first.** Group candidate files by the durable concept their names, types,
   namespaces, routes, and public surface point at. Only then measure how that cluster is
   distributed. Directory spread MAY support an entity decision; it MUST NOT be the clustering
   mechanism, because clustering by directory makes spread unmeasurable by construction.
2. **Require multiple independent signals.** One signal is a flat-document candidate. Proposing an
   entity requires at least two signals that do not restate one another.

Locating tests by path proximity is not a substitute for locating them by symbol or name
reference. A proposal mechanism that can only see colocated tests is blind to most real
repositories and MUST NOT be the sole basis for a flat-versus-entity recommendation.

## 8. Layers

An entity's Knowledge is divided into layers so that an agent can be given the view its task needs
rather than everything known about the concept.

| Layer | Answers | Class |
|---|---|---|
| `architecture` | Structural responsibility, boundaries, major internal components, architectural shape | Expected |
| `business` | Durable domain behavior, rules, concepts, terminology, invariants | Expected |
| `integration` | External and internal system interactions, contracts, clients, APIs, messages, dependencies | Expected |
| `operations` | Runtime behavior, configuration, observability, deployment and runtime concerns, failure handling | Expected |
| `pattern` | A reusable engineering pattern associated with the entity | Auxiliary |
| `plan` | Durable forward-looking technical direction, only when that direction is genuinely current truth | Auxiliary |

- **Expected** layers are reported by the coverage report when absent. **Auxiliary** layers are
  never reported as a gap.
- Every layer is **optional to author**. Coverage describes the corpus; it does not command it.

The governing rule:

> **Create a layer only when repository evidence supports useful content for it.**

Do not author an empty layer for completeness. A heading with no substance costs an agent context
and returns nothing. When an expected layer genuinely does not apply to a concept — an internal
utility with no integration surface — record a coverage waiver on the entity rather than writing a
document that says so.

Baseline bootstrap creates the **minimum useful authoritative model**, never a documentation
skeleton.

## 9. Source ownership

`source_of_truth` answers exactly one question:

> Which repository artifacts provide the evidence for this Knowledge?

It supports individual files, directories, explicit globs, source projects, and test projects.
There MUST be **one canonical path-expansion implementation**, shared by every tool that needs to
turn a mapping into a concrete file set. Validation, overlap detection, unmapped-file detection,
and freshness all consume that one implementation, so that a mapping means the same thing
everywhere it appears.

Treatment by artifact class:

| Artifact class | Ownership |
|---|---|
| Production source | Yes — the primary case |
| Tests, including a separate test project | Yes — tests are evidence and are first-class ownership |
| Recorded fixtures that are themselves the contract | Yes |
| Generated source | Normally no; permitted only with a justification recorded on the document |
| Build output | Never |
| Vendored dependencies | Never |

Prefer the **narrowest mapping that accurately owns the concept**. A mapping broad enough to claim
files the document does not actually describe produces false staleness, false overlap, and
misleading context selection — it is worse than a missing mapping, because it looks like coverage.

Each mapping form carries its own currency mechanism: a path mapping is current relative to the
newest change to the artifacts it claims; a pinned content claim is current relative to a retained
canonical baseline. Both are `source_of_truth`. A surface that reports on either MUST say which
mechanism it evaluated, because "stale" otherwise names unrelated conditions — a currency date
older than its sources, and a pinned claim whose content moved.

### 9.1 Ownership is not applicability

Knowledge may reference a repository path in exactly two ways, and they are **not
interchangeable**:

| Claim | Declared on | Asserts |
|---|---|---|
| `source_of_truth` | Entity layers | Evidence ownership — changing this artifact may make the document stale |
| `appliesTo` | Any document | Applicability scope — this document governs or must be considered for that artifact |

Only `source_of_truth` is ownership. A governance document that applies to a file an entity owns is
**normal co-existence**, not competing ownership, and MUST NOT be reported as an ownership
conflict. Two entities claiming the same file as `source_of_truth` is a genuine conflict and MUST
still be reported.

Any analysis that evaluates ownership MUST preserve the claim kind rather than flattening claims
into an undifferentiated path-to-documents map, and any finding it emits MUST state which claim
kind it concerns so a reader can tell the two apart without re-deriving them.

The test for ownership is: **if this artifact changed materially, could this Knowledge become stale
or incorrect?** If not, it is not `source_of_truth`. Temporary work products, archived specs, build
output, and files that merely mention the concept all fail that test. **A mention is not
applicability either** — `appliesTo` states where Knowledge governs, not where it is cited.

Multiple ownership is **not automatically invalid**. A genuinely cross-cutting artifact may
implement more than one concept, so two owners is surfaced for review rather than prohibited; the
risk it carries is unclear responsibility, not illegality.

The two claim kinds drive tooling differently:

| Behavior | `source_of_truth` | `appliesTo` |
|---|---|---|
| Source navigation | Yes | No |
| Drift and staleness | Yes | No |
| Ownership overlap | Yes | No |
| Governance applicability | No | Yes |
| Context relevance | Yes | Yes |

## 10. Relationships

A relationship is **accepted architectural truth**. Authoring one is a claim, not an observation.

| Field | Declared on | Direction | Strictness |
|---|---|---|---|
| `relations: [{to, rel}]` | `_entity.yaml` | declaring entity → named entity | Strict — the target MUST resolve; a build fails otherwise |
| `constrains` | governance decision | decision → entity | Strict, and reciprocal |
| `constrained_by` | `_entity.yaml` | entity → decision | Strict, and reciprocal |
| `links.references` | any node except an entity layer | declaring node → named node | Lenient — an unresolved target is reported, not fatal |

**Semantic relationships belong to the entity, never to one of its layers.** A layer describes one
facet of its parent and has no independent conceptual identity, so it has nothing to relate *from*.
A layer declaring `links` MUST fail rather than be ignored: an accepted-but-unused field looks
authored while reaching nothing, which is worse than a rejection. A layer MAY carry aliases, which
are a retrieval affordance rather than graph identity.

The `entity → has-layer → layer` edge is **composition the framework materializes**, not an
authored semantic relation. An entity *is* its layers, so nobody restates that adjacency by hand.

- Canonical relation keys are **`to` and `rel`**. The default predicate is `relates-to`; `depends-on`
  is the common explicit alternative. A repository MAY define further predicates.
- `constrains` and `constrained_by` are both hand-authored and validated against each other in both
  directions. Neither is generated from the other, because a governance link that only one side
  knows about is exactly the failure this pair exists to prevent.
- `links.references` is deliberately lenient so a document may point forward at Knowledge not yet
  authored. That leniency is why it MUST NOT be used to assert architectural dependency.
- Projection traverses every relationship in both directions and labels the reverse direction
  distinctly. An inverse edge is a **traversal affordance, not an authored claim**; nothing may
  report an inverse edge as something a human asserted.

The distinction that makes the graph trustworthy:

```text
discovery relationship  =  proposal
authoritative relationship  =  accepted current truth
```

Only authoritative relationships participate in Context Projection.

## 11. Governance

A governance decision is current Knowledge for as long as it constrains current software behavior.
It records what we do and why we do not do the alternatives, in the present tense. That rationale —
including the alternatives rejected — is current content, because it is what prevents the same
question being reopened. It is not a change log: exactly one current decision document exists per
topic, edited in place, keyed by topic rather than by creation order.

Governance participates in the graph through `constrains` / `constrained_by`, and MUST be reachable
by Context Projection. An agent about to modify a concept should learn that something constrains it
without having to go looking.

Governance that applies to flat Knowledge is as legitimate as governance that applies to an entity.
Where the current field vocabulary only admits entity targets, that is a limitation of the
implementation and is recorded as a follow-up in §24 — not a statement that flat Knowledge is
ungovernable.

## 12. Discovery

Discovery is an **advisory reconciliation tool**. Its purpose:

> Find plausible current-truth Knowledge that the repository may have failed to author or maintain.

It MAY propose Knowledge gaps, entity candidates, layer candidates, source mappings, aliases,
relationships, governance links, leakage of non-current material, and ownership overlap.

The canonical flow:

```text
discovery finding → evidence → review → accept or reject → authoritative Knowledge
```

Discovery MUST NOT promote a heuristic finding into authoritative truth on its own initiative. A
finding is never an edge, never a node, and never traversable. Where a discovery surface offers a
mechanical apply step, that step takes explicit human-supplied targets and an explicit write flag —
it does not consume its own finding output.

Discovery is **not** the baseline authoring workflow. A future bootstrap workflow may reuse
discovery primitives, but it answers a different question and carries different obligations.

Discovery MUST document its own narrowness. A check that examines only one signal, or only one
document shape, states that plainly, so a clean run is not misread as a broad assurance.

### 12.1 What a finding means

**A finding is a condition that deserves attention now.** That standard governs what any analysis
surface reports. Three conditions must be told apart:

| Condition | Reported |
|---|---|
| Unresolved anomaly — something may be wrong and nobody has decided | Yes |
| Intentional override — an author exercised a precedence the contract grants | No |
| Accepted exception — a discrepancy consciously settled as current truth | No |

A permanent finding nobody can act on is not a safeguard; it trains readers to skim past the report
that was supposed to protect them. An override the contract explicitly permits is the framework
working, not a defect to re-report on every run.

The distinction has a concrete form in role classification. A taxonomy glob states a directory's
default, so a document inside it declaring a different role is an intentional override and is not
reported. An exact-path mapping is a statement about one specific file, so a document contradicting
it means two deliberate statements disagree — an unresolved anomaly someone must settle.

## 13. Baseline bootstrap

This section is the contract for a future `bootstrap-knowledge` workflow. It is not implemented.

Bootstrap asks: *given an established repository with significant Code and Tests but little
DevSpark Knowledge, what authoritative baseline should exist before new specs begin?*

Required responsibilities, in order:

1. Inspect repository structure and build configuration.
2. Inspect production code.
3. Inspect tests **across projects**, located by symbol and name reference rather than path
   proximity.
4. Inspect existing documentation and decision records.
5. Cluster by durable software concept (§7).
6. Propose flat document versus entity (§6).
7. Propose evidence-backed layers only (§8).
8. Propose source ownership at the narrowest accurate mapping (§9).
9. Propose aliases from observed naming variants.
10. Propose relationships only where a concrete code reference supports the claim (§10).
11. Propose governance connections (§11).
12. Cite concrete Code and Test evidence for every proposal.
13. Present one reviewable proposal.
14. Allow item-by-item acceptance; the default disposition is reject.
15. Materialize accepted items only, complete with the ownership and currency metadata the builder
    requires — never a partially-authored document that fails validation on the next build.
16. Build the canonical Knowledge Model.
17. Run integrity validation.
18. Audit graph fan-out for both emptiness and explosion.
19. Run representative context-resolution smoke tests and show the resulting working set.

Required properties: **reviewable, resumable, idempotent, evidence-based, and safe on a
partially-authored repository.**

Bootstrap MUST NOT invent architecture. Where evidence is absent or contradictory, it reports that
and proposes nothing.

## 14. The consumption pipeline

Every lifecycle stage that needs task-specific Knowledge uses the same conceptual pipeline:

```text
Task / Spec / Change
        ▼
 canonical retrieval
        ▼
  likely Knowledge seeds
        ▼
  Context Projection
        ▼
  candidate context
        ▼
 task-specific judgment
        ▼
   context_resolved
```

A command MAY use a cheaper subset of this pipeline where the cost is not justified — an early
conflict check does not need full projection. When it does, it MUST say so and say why.

What a command MUST NOT do is invent an incompatible private definition of Knowledge relevance: its
own scan, its own matching rules, its own notion of what "related" means. A private search path
produces context that no other stage can validate, reproduce, or bound.

The long-term goal is one context-building model across specify, plan, tasks, analyze, critic,
implement, verify, and review.

## 15. Retrieval

Retrieval answers: *what Knowledge is likely relevant to this job?*

There is **one canonical lexical retrieval engine**. It may consider title, aliases, headings, body,
source mappings, entity metadata, and governance metadata, and it ranks deterministically so the
same query over the same corpus returns the same order.

Retrieval produces **likely starting points**. It does not determine the working context, and it
MUST NOT be treated as having assembled architectural context. A high-scoring match is a seed.

## 16. Context Projection

Projection answers: *what accepted architectural truth is adjacent to the likely starting points?*

It traverses only authoritative relationships (§10). It MUST be **bounded, deterministic,
cycle-safe, and provenance-preserving** — every candidate it returns carries the path and relation
by which it was reached. It MUST NOT perform lexical or semantic search of its own, and it MUST NOT
traverse an advisory discovery finding.

**Canonical hop policy.** One policy, stated once:

- Plan performs projection to a maximum of **2 hops** from its lexical seeds.
- Planned implementation consumes `context_resolved` and MAY take **at most 1 additional hop**,
  which MUST be explicitly logged.
- A Code First or direct-change command without Plan may establish its initial task-specific
  context through the same canonical retrieval and projection, with at most **2 hops**, recording
  the retained context and its provenance in its existing evidence surface.
- Other diagnostic projection surfaces use at most 2 hops.

No document states a different budget. A range is not a budget.

Projection also bounds total candidates, and reports when that bound was reached. Hitting the bound
is a signal about the graph, not a normal outcome to be ignored.

## 17. `context_resolved`

`context_resolved` is the **authoritative bounded Knowledge working set for a task when that
artifact is present**. On a specification-led route, Plan judgment produces it from projected
candidates and downstream stages consume it. On a Code First or direct-change route without Plan,
the owning command MUST derive bounded, provenanced context through the same canonical retrieval
and projection pipeline, starting from the actual Delta/diff and its credible blast radius.
It MUST NOT fabricate a Plan or use an incompatible private context resolver. A route-specific
minimal context record is sufficient; the four kinds and provenance rules below still apply.

It MUST support four kinds:

| Kind | Meaning |
|---|---|
| `entity` | The concept as a whole |
| `entity-layer` | One layer document of an entity |
| `knowledge` | A flat Knowledge document |
| `decision` | A governance decision |

**Flat Knowledge is first-class resolved context.** A document does not need to belong to an entity
to be given to an agent, and a working set consisting entirely of flat documents is valid and
complete. Any template, validator, or gate that models resolved context as entity-or-decision only
is non-conforming.

Each resolved item preserves provenance sufficient to audit it: its `id`, its `kind`, the `via`
relation or match that reached it, its `hop` count, and a short reason it was retained.

Adjacency is not relevance. The accountable route's context-selection judgment decides what is
retained; projection only says what is reachable. For Model First, Plan owns that judgment.

## 18. Just-right context

For every agent task, provide **the smallest sufficient trustworthy context set.**

- **Start small.** Directly matched current Knowledge first.
- **Expand deliberately.** Follow an authoritative relationship only when the adjacent context can
  materially affect the work.
- **Stop when sufficient.** Do not keep traversing merely because relationships exist.
- **Prefer current evidence.** The Code and Tests owned by selected Knowledge are available to the
  agent.
- **Preserve provenance.** The agent can tell why each item is present.
- **Bound assembly.** Context assembly has explicit limits, and never sends the whole corpus.

## 19. The agent context package

The target context for an implementation agent, as a logical model:

```text
┌──────────────────────────────────────┐
│ Minimal governance                   │
│  - constitution                      │
│  - applicable decisions              │
├──────────────────────────────────────┤
│ context_resolved                     │
│  - relevant entities and layers      │
│  - relevant flat documents           │
│  - relevant governance               │
├──────────────────────────────────────┤
│ Evidence                             │
│  - owned and relevant production code│
│  - relevant tests                    │
├──────────────────────────────────────┤
│ Current Delta                        │
│  - spec / plan / tasks, or actual diff│
└──────────────────────────────────────┘
```

This is a logical model, not necessarily one payload. On a Code First route, the actual diff,
intent evidence, and existing tests replace missing planning artifacts; no fictional spec or Plan
is needed. An agent MAY retrieve the underlying source on demand; what matters is that the set is
bounded, provenanced, and assembled through the canonical context pipeline.

## 20. What must not enter default agent context

Do not inject by default:

- the entire `.knowledge/` corpus;
- the entire generated index;
- every graph neighbor of every seed;
- unaccepted discovery findings;
- archived material, or Knowledge that is no longer current;
- past specs, unrelated tasks, or prior review material;
- broad repository prose standing in for targeted Knowledge;
- Knowledge known to be stale or drifted, without that status attached to it;
- results from a private search path incompatible with the canonical pipeline.

Avoid duplicate copies of the same context. The same document arriving twice by two routes consumes
the budget twice and teaches the agent nothing the second time.

## 21. Code and tests as evidence

Knowledge is not a substitute for source. The division of labor:

| Knowledge tells the agent | Code and Tests tell the agent |
|---|---|
| what this concept means | how it currently works |
| why it exists | |
| where its boundaries are | |
| what constraints apply | |
| where the evidence lives | |

The agent moves **Knowledge → owned Code → relevant Tests**, rather than scanning the repository
blindly. The framework's job is to **reduce the search space, not to hide the implementation
evidence.** Knowledge that cannot be checked against the source it claims to describe is not
Knowledge; every claim cites evidence, and test evidence is preferred over code evidence because it
converts a judgment into a mechanical check.

### 21.1 Tests are a durable pillar

Tests are all durable, repeatable evidence: developer tests, automated acceptance and regression
tests, and manual acceptance and regression assets kept in the system that owns them. Knowledge is
the claim, Tests are the evidence, Code is the subject. Regression is not Knowledge: a regression
test validates the resulting system and does not describe a concept. Because Tests are a pillar,
each behavior change considers its Tests impact and the baseline is curated (added to, updated or
retired), never only accumulated. This is conceptual ownership, not a directory taxonomy: Tests
stay where the owning tool or repository keeps them.

## 22. Context budget

No universal token number is fixed here; none is supported by evidence today. Budget is defined as
behavior:

| Tier | Content | Bound |
|---|---|---|
| 0 | Always-required governance | Constitution, plus decisions applicable to the working set |
| 1 | Directly matched Knowledge | Retrieval result limit |
| 2 | Authoritative projected Knowledge | Hop policy (§16) and candidate cap |
| 3 | Owned Code and Tests | Retrieved on demand from the mappings of tiers 1 and 2 |

Every tier is bounded. Expansion stops when the agent has enough evidence to perform the requested
job safely. Prefer **small and sufficient** over **large and possibly useful**.

## 23. Lifecycle responsibilities

| Stage | Knowledge responsibility |
|---|---|
| Specify | Canonical retrieval for early conflict and current-behavior grounding. A reduced method is acceptable and is declared; a private search is not. |
| Clarify | Consult selected Knowledge where an ambiguity turns on current behavior or architecture. |
| Plan (when used) | Authoritative Context Resolution for a specification route: retrieval → projection → judgment → `context_resolved`. |
| Tasks (when used) | Name the Knowledge paths a task changes in its description, and create Knowledge-maintenance tasks when durable truth will change. |
| Analyze | Validate that referenced Knowledge exists and that context provenance is legitimate. A nonexistent or unreachable reference is a hard stop. |
| Critic | Judge sufficiency of the working set. Not graph completeness. |
| Implement (planned route) | Consume Plan's `context_resolved`; take at most one logged additional hop; update Code, Tests, and Knowledge together when durable truth changes. |
| Code First / Quickfix (when supported by the actual command) | Derive a minimal provenanced context from the existing Delta/diff through canonical retrieval and projection; update Code, Tests, and Knowledge together when durable truth changes. Never synthesize absent planning history. |
| Verify | Produce test evidence that supports Knowledge claims where relevant. |
| PR review | Start from changed-path ownership and the claims it leads to. Use canonical topic retrieval and bounded projection of accepted relationships only to answer a specific unresolved contract or ownership question; an empty owner lookup alone does not make Knowledge inapplicable. Judge candidates before retaining them, validate the current claims the Delta bears on across flat Knowledge, entities, layers, and governance, and cite the invariants a finding or decision relied on. When the Delta changes durable truth, its existing owner is reconciled in the same change, or a new owner is added when the behavior is material. A focused update evaluates corrections only and resolves no new Knowledge context. Missing or stale sources and unsupported claims are not current truth; do not preserve ephemeral history or speculative predictions as Knowledge. |
| Release | Confirm derived artifacts are current and that no longer-current Knowledge has been left behind. |

## 24. Conformance and open follow-ups

A surface conforms to this contract when it: obtains its model from the shared builder; uses the
canonical retrieval engine or declares a reduced method and why; respects the hop policy; treats
flat documents and entities as equally valid resolved context; treats discovery findings as
proposals; and bounds what it sends to an agent.

Known deviations, carried as follow-ups rather than silently tolerated:

| Follow-up | Class |
|---|---|
| Work-product schema and validators use the reserved term Knowledge (§3) | Terminology cleanup |
| Entity-candidate proposal clusters by directory, making concept spread unmeasurable (§7) | Contract implementation defect |
| Resolved-context template models only entity and decision kinds (§17) | Prompt alignment |
| Hop budget stated inconsistently across prompts and templates (§16) | Prompt alignment |
| Entity migration emits documents without the ownership and currency metadata the builder requires (§8, §13.15) | Contract implementation defect |
| More than one path-expansion implementation for source mappings (§9) | Script alignment |
| Governance constraint targets admit entities only, not flat Knowledge (§11) | Missing capability |
| No baseline bootstrap workflow exists (§13) | Missing capability |
| This repository authors no entities, relationships, or decisions of its own | Dogfood |

## Companion Documents

- [Constitution](constitution.md)
- [DevSpark Philosophy](devspark-philosophy.md)
- [Knowledge Content Lifecycle](../tooling/content-lifecycle.md)
- [Knowledge Authoring Developer Guide](../tooling/developer-guide.md)
- [Severity Registry](severity-registry.md)
