---
description: Find gaps, weak mappings, missing relationships, aliases, contradictions, and historical leakage in current .knowledge, and apply only the findings a human approves
handoffs:
  - label: Explain a Topic
    agent: devspark.explain
    prompt: Explain one topic from code and tests and verify its knowledge
  - label: Audit Current Truth
    agent: devspark.site-audit
    prompt: Audit source code and knowledge for current-truth gaps
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding.

## Purpose

`/devspark.discover-knowledge` helps humans improve the quality and
navigability of the repository's current authoritative `.knowledge`. It finds
gaps, weak or over-broad source mappings, missing relationships, legitimate
aliases, contradictions, and historical leakage, and proposes the smallest
evidence-backed changes.

> Discovery proposes. Evidence supports. Humans approve.

It is an authoring and maintenance aid. It is not agent memory, automatic
documentation generation, historical reconstruction, a replacement for
`/devspark.explain` (which answers one topic), or a runtime retrieval
mechanism. It may derive candidate knowledge from repository evidence, but it
never silently promotes inferred information into `.knowledge`.

## Lifecycle Position

Not a lifecycle gate and never required for a feature or spec. Use it:

- when adopting DevSpark in an existing repository (`--bootstrap`);
- periodically as the repository evolves, or after a major refactor;
- when retrieval or `/devspark.explain` repeatedly misses relevant knowledge;
- before improving the `context_resolved` quality that plan relies on.

`/devspark.site-audit` may recommend it when it detects structural knowledge
gaps.

## Scope

| Input | Behavior |
|---|---|
| `<entity-id>` | That node and its declared neighbors |
| `<path>` (for example `app/logic_handlers`) | Code under the path and the nodes that map it |
| `<term>` (for example `conversations`) | Nodes the knowledge engine ranks for the term, plus code whose paths match it |
| no argument | Repository-wide. It is more expensive, so ask once — `Run repository-wide discovery? (yes/no)` — then use `--all` |
| `--all` | Repository-wide without asking |
| `--check-only` | Report findings only; skip the application step |
| `--bootstrap` | First-time setup for a repository with no entities (see Bootstrap) |

## Rules

- Evidence surface: current code, tests, `.knowledge` (entities, entity
  documents, flat nodes, governance decisions, `index.json`), registered
  applications, and each node's `source_of_truth`, `appliesTo`, relations,
  `constrains` / `constrained_by`, and `links.references`.
- Git metadata (for example recent commit counts) is supporting evidence only,
  never current behavioral truth.
- Never read, list, or glob `.archive/`, and never treat `.devspark.work/`,
  archived specs, or historical documentation as current authority.
- Every finding cites repository evidence (paths, and line numbers where
  useful). Do not emit generic advice that the evidence does not support.
- Do not write to `.knowledge` until the user selects a finding and explicitly
  confirms the exact proposed change. Do not bulk-apply all findings by
  default. Never commit.
- Out of scope: embeddings, vector stores, persistent agent memory, automatic
  documentation generation, automatic relationships, aliases, or semantic
  rewrites, mandatory entity migration, deletion of knowledge, and autonomous
  commits.

## Procedure

### 1. Gather signals

Resolve the scripts directory: `.devspark/scripts/`, or `scripts/` only when the
framework copy is absent. Then run, from the repository root:

```text
python <scripts>/build_knowledge_index.py --check
python <scripts>/discover-knowledge-context.py <entity-id | path | term>   # or --all
```

`discover-knowledge-context.py` is deterministic and read-only. It returns
mechanical signals only — `source_clusters`, `mapping_breadth`,
`ownership_overlaps`, `relationship_signals`, `alias_signals`,
`stale_references`, `historical_signals`, and `node_shape` — and never judges
them. Engine errors appear in `engine_findings`; report them, but do not repair
them silently.

### 2. Verify before you report

A signal is a lead, not a finding. For each signal worth reporting, read the
cited code, tests, and knowledge and confirm the evidence yourself. Drop
signals that do not hold up (for example, a repeated term that is language
syntax, or an overlap that is a deliberate shared kernel). Record why a strong
signal was dropped when a reader would expect it.

### 3. Classify findings

**Knowledge Gaps** — meaningful code areas with no knowledge ownership
(`source_clusters` with empty or over-broad-only `mapped_by`). Do not require
every file to have knowledge. Report a cluster only when durable behavior
exists, several files implement one concept, tests reveal important behavior,
or missing knowledge is likely to cause implementation mistakes. Example:

```text
KNOWLEDGE GAP
Area: app/foo/**
Evidence: 14 production files; 22 tests; repeated concept "foo routing";
          no source_of_truth mapping; no entity or flat node
Recommendation: consider current knowledge for Foo Routing (flat knowledge document)
```

**Mapping Gaps** — knowledge clearly describes code it does not map (the prose
names paths or symbols absent from its `source_of_truth` / `appliesTo`).

**Mapping Ambiguities** — over-broad mappings (large `code_files` with low
`concept_density` in `mapping_breadth`: only a narrow part supports the
concept) and competing ownership (`ownership_overlaps`). Overlap is not wrong by
default: explain why this overlap may or may not be meaningful, noting
`declared_related`.

**Relationship Candidates** — existing entities with strong evidence of
participating in the same durable behavior (`relationship_signals`: direct
dependencies, orchestration, shared contracts, tests exercising both,
documentation naming both). Use an existing relation type (`describes`,
`derives_from`, `extends`, `generated_for`, `scopes`, `supports`, `uses`,
`validates`, `validated_by`) or `links.references`. Propose a new relation type
only when the ontology cannot represent a recurring, clearly useful
relationship. Example:

```text
RELATIONSHIP CANDIDATE
order_checkout → payment_authorization
Evidence: src/orders/checkout.py imports authorize_payment; tests/test_checkout.py
          exercises both; order_checkout guide describes authorization
Suggested relation: uses
```

**Alias Candidates** — terminology developers or code genuinely use for the same
current concept (domain abbreviations, renamed concepts still in common use,
operational or external-system vocabulary) from `alias_signals`. The alias must
be supported by current repository evidence. Never add an alias only because
retrieval performed poorly, and never add obsolete terms that are no longer
useful vocabulary. Example:

```text
ALIAS CANDIDATE
Entity: payment_authorization
Candidate: PSP capture
Evidence: src/payments/psp_capture.py, tests/test_psp_capture.py
Confidence: high | medium | low
```

**Contradictions** — knowledge that disagrees with the constitution or a
decision, with code behavior, with tests, or with another knowledge node
(`stale_references` and your own reading; scope comparisons to
`index.json` `contradiction_scopes`). Label each one:

- `PROVEN CONTRADICTION` — repository evidence settles it (for example, a test
  asserts `MAX_RETRIES == 5` while knowledge says 3, or a cited file no longer
  exists).
- `POSSIBLE INCONSISTENCY — HUMAN REVIEW REQUIRED` — the evidence is ambiguous.
  Do not decide the semantic dispute.

**Historical Leakage** — content that is primarily history rather than needed to
understand current behavior (`historical_signals`: retired implementation
details, old requirement identifiers, migration narratives, superseded
approaches, long "previously…" passages). Recommend one of: keep (current
understanding requires it), move to the team's documentation or history
repository, or remove because Git already preserves it. Never delete it
yourself.

**Potential Entity Candidates** — only when several signals justify an entity
(`node_shape`): a durable named domain concept, clear ownership, multiple
meaningful documentation layers, specific source ownership, relationships to
other entities, and value from coverage or drift validation. Do not encourage
entity proliferation. Classify every recommendation for new knowledge as a
**flat knowledge document** (`.knowledge/<topic>.md` or
`.knowledge/guides/<topic>.md`) or an **entity candidate**. A simple guide or a
single-purpose architectural note stays flat; leave well-shaped flat nodes
alone.

### 4. Report

Group findings under these headings, in this order, omitting empty groups:
`Knowledge Gaps`, `Mapping Gaps`, `Mapping Ambiguities`, `Relationship
Candidates`, `Alias Candidates`, `Contradictions`, `Historical Leakage`,
`Potential Entity Candidates`.

Number findings `DK-01`, `DK-02`, … and give each:

- affected node, entity, or area;
- supporting code and test paths;
- reason;
- confidence (`high`, `medium`, `low`);
- recommended action (for new knowledge: flat knowledge document or entity
  candidate);
- whether applying it changes current authoritative truth (`yes` / `no`).

For mapping and relationship findings, also show the deterministic context path
they would give plan's context resolution, so the repository-owned structure
improves without discovery becoming the retrieval engine:

```text
task
 ↓ lexical seed: order_checkout
 ↓ declared relation: payment_authorization
 ↓ source mapping: src/payments/**
```

Write the same report to
`.devspark.work/knowledge-discovery/discover-knowledge-YYYY-MM-DD.md` as
temporary work state (never into `.knowledge`), then ask: `Which findings should
I apply? (list DK ids, or none)`. With `--check-only`, stop after the report.

### 5. Apply approved findings

For each finding the user selects, one at a time:

1. Draft the smallest `.knowledge` change: a frontmatter edit (`aliases`,
   `source_of_truth`, `appliesTo`, `relations`, `links.references`,
   `constrained_by`), an in-place sentence correction, or a new flat node or
   entity with `source_of_truth`, `last_verified`, and evidence.
2. Show the exact change and ask for explicit confirmation. Do not write until
   the user confirms.
3. After writing, run the knowledge engine without flags to refresh
   `index.json` / `coverage.json`, then `--check`, plus any cited tests.
4. Report the result. Keep reciprocal pairs intact (`constrains` ↔
   `constrained_by`) and never write lifecycle keys (`status`, `lifecycle`,
   `supersedes`, `superseded-by`, `replaced`, `obsolete`).

### Bootstrap

Use `--bootstrap` only when `.knowledge/entities/` has no entity yet (the
quickstarts call it on first install).

1. Create any missing roots: `.knowledge/entities/`,
   `.knowledge/governance/decisions/`, `.knowledge/ontology/`,
   `.knowledge/guides/`, `.knowledge/overrides/commands/`, and
   `.devspark.work/knowledge-discovery/`. Seed missing scaffold files from
   `.devspark/templates/knowledge/` without overwriting anything.
2. If the repository still has a pre-contract layout (`_derived.yaml`,
   decisions with `governs` or `status`, or `.knowledge/ontology/*.generated.md`),
   run `python <scripts>/migrate-knowledge-to-entities.py --dry-run`, show the
   plan and any `conflict` lines, and run it after confirmation. Pass `--force`
   only when the user confirms overwriting the conflicting files.
3. Run `discover-knowledge-context.py --all` and propose a minimal initial
   structure: a few entity candidates for clearly durable concepts, flat
   knowledge documents for everything simpler, and gaps for low-confidence
   areas. Show the whole proposal and write it only after one explicit
   confirmation.
4. If `.documentation/` or `.documenation/` exists, propose a classification
   for each intake document: durable current truth (assimilate into the owning
   node), draft or work product (stage under `.devspark.work/documentation/`),
   or obsolete (stage under
   `.devspark.work/release-candidates/documentation/`). Preserve relative
   paths, add a numeric suffix instead of overwriting, never delete intake
   files, and never write to `.archive/`. Apply only after confirmation.
5. Run the knowledge engine without flags, then `--check`.

## Output

Return the grouped findings (or the bootstrap proposal), the report path, what
was applied after confirmation, the engine `--check` result, and any blockers.
