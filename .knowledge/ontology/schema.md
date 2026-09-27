# DevSpark Knowledge Ontology

DevSpark stores current truth under `.knowledge`. The ontology makes that truth
navigable and checkable while temporary work packages stay outside permanent
context. The contract is enforced by the single knowledge engine,
`build_knowledge_index.py`, against `templates/schemas/entity-node.schema.json`
and `templates/schemas/knowledge-node.schema.json`.

## Roots

| Root | Purpose | Managed By |
|---|---|---|
| `.knowledge/entities/<id>/` | Durable current-truth entity records | Humans, assisted by prompts |
| `.knowledge/governance/constitution.md` | Current rules of the game | Humans, amended explicitly |
| `.knowledge/governance/decisions/<topic>.md` | Current governance decisions, one file per topic | Humans, assisted by prompts |
| `.knowledge/ontology/index.json` | Generated discovery index | Knowledge engine |
| `.knowledge/ontology/coverage.json` | Generated existence and gap report | Knowledge engine |
| `.knowledge/ontology/baselines/` | Retained canonical baselines for pinned claims | Knowledge engine (`--pin-claim`) |
| `.knowledge/knowledge.config.yaml` | Repository knowledge settings | Humans |
| `.devspark.work/` | In-flight work packages only | DevSpark prompts |
| `.archive/YYYY-MM-DD/` | Write-only retention for retired planning artifacts | Written by release (and constitution proposals); purged by humans |

No DevSpark command reads, lists, enumerates, or globs `.archive/`.

## Resolving the engine

Every entry point resolves the engine through `resolve_knowledge_engine`
(`common.sh`) or `Resolve-KnowledgeEngine` (`common.ps1`):

1. `.devspark/scripts/build_knowledge_index.py` (framework-managed; preferred)
2. `scripts/build_knowledge_index.py` (legacy repository-root copy; used only
   when the framework-managed copy is absent)

When both exist, helper JSON reports the extra copy under `legacy_copies` and
the quickstart upgrade flow reconciles it.

## Entity folders

Each entity folder contains:

- `_entity.yaml`: hand-authored entity-node metadata.
- One or more layer documents, usually `architecture.md`.

Entity ids are lowercase slugs matching `^[a-z0-9][a-z0-9._-]*$`.

### `_entity.yaml` fields

| Field | Required | Meaning |
|---|---:|---|
| `id` | yes | Stable entity id matching the folder name |
| `name` | yes | Human-readable name |
| `kind` | yes | Entity kind from the allowed kind registry |
| `summary` | yes | Present-tense current-truth summary |
| `evidence` | yes | At least one evidence entry supporting the entity |
| `constrained_by` | no | Decision ids that constrain this entity (hand-authored reciprocal of `constrains`) |
| `aliases` | no | Concept names this entity is reachable by |
| `owner` | no | Responsible role or team |
| `root` | no | Primary repository root or path this entity describes |
| `managed_by` | no | `human`, `prompt`, `script`, `generated`, or `mixed` |
| `required_layers` | no | Required layer documents (default `architecture.md`) |
| `relations` | no | Typed edges to other entities |

### Layer document frontmatter

Every Markdown file under an entity folder, including subfolders such as a
documentation site or asset guides, is a knowledge node and carries the
currency pair. Top-level files are the entity's layers:

| Field | Required | Meaning |
|---|---:|---|
| `source_of_truth` | yes | Paths (or pinned claim objects) this document describes |
| `last_verified` | yes | Date the document was last confirmed against its sources |
| `title` | no | Title; defaults to the first H1 |
| `aliases` | no | Concept names used by discovery |
| `appliesTo` | no | Paths or globs the document applies to |
| `evidence` | no | Additional evidence entries |

## Flat knowledge nodes

Not every piece of current truth justifies an entity. A simple guide or a
single-purpose architectural note is a flat knowledge node:

- `.knowledge/<topic>.md` or `.knowledge/guides/**/<topic>.md`
- Node id: frontmatter `id`, else the filename stem; unique across entities,
  decisions, and flat nodes.
- Same currency rules as entity layers (`source_of_truth`, `last_verified`),
  optional `aliases`, `appliesTo`, `evidence`, and `links`.

Prefer a flat node until a concept earns an entity through several signals: a
durable named domain concept, clear ownership, multiple meaningful layers,
specific source ownership, relationships to other entities, and value from
coverage or drift validation.

## Links

Any knowledge node (`_entity.yaml`, entity documents, flat nodes, decisions)
may declare:

```yaml
links:
  references:
    - token-service          # a node id (entity, decision, or flat node)
    - src/Auth/TokenService.cs   # or an existing repository path
```

References are validated: each must be a known node id, an existing path, or an
external URL, and never temporary work. They record that two current truths
relate without asserting a typed entity relation.

## Banned keys

`status`, `lifecycle`, `supersedes`, `superseded-by`, `replaced`, and
`obsolete` are banned on every current-knowledge document, decisions included.
There is no deprecated state: current knowledge is edited in place or deleted.
Git holds the history.

## Entity kinds

| Kind | Use |
|---|---|
| `knowledge-model` | Ontology, evidence, current-truth model |
| `framework-template-set` | Prompt and template source files |
| `generated-integration-files` | Agent shims or generated adapter outputs |
| `repository-configuration` | Durable repository configuration |
| `ephemeral-state` | Temporary work-state model, not permanent work contents |
| `knowledge-site` | Product documentation site source |
| `design-asset-set` | Brand/design assets and media |
| `integration-catalog` | Extension or integration catalog |
| `contributor-practice` | Contributor workflow and dogfooding guidance |

## Relation types

| Type | Meaning |
|---|---|
| `describes` | Subject documents or explains another entity |
| `derives_from` | Subject is generated from another entity |
| `extends` | Subject adds to another entity |
| `generated_for` | Subject produces outputs for another entity |
| `scopes` | Subject defines valid scope for another entity |
| `supports` | Subject materially supports another entity |
| `uses` | Subject depends on another entity during normal work |
| `validates` | Subject validates another entity |
| `validated_by` | Subject is validated by another entity |

Relation objects must resolve to existing entity ids.

## Decisions

Decision files live at `.knowledge/governance/decisions/<topic>.md`, keyed by
domain or topic, never by sequential number. The filename equals the `id`.
Exactly one current file may govern a topic. Frontmatter:

| Field | Required | Meaning |
|---|---:|---|
| `id` | yes | Topic slug equal to the filename |
| `type` | yes | `governance-decision` |
| `title` | yes | Topic title (must be unique) |
| `constrains` | yes | Non-empty list of entity ids this decision constrains |
| `evidence` | yes | At least one evidence entry |
| `last_verified` | yes | Date the decision was last confirmed |

No `layer` key: a decision is one document, one topic. Each entity a decision
`constrains` must list the decision in its own `constrained_by`, and vice
versa; the engine fails on any unreciprocated pointer.

## Evidence

Evidence entries include `type`, `ref`, and `verified_by`.

| Type | Expected verification |
|---|---|
| `test` | `verified_by: execution` |
| `code` | `verified_by: inspection` |
| `doc` | `verified_by: inspection` |
| `schema` | `verified_by: inspection` |

Missing evidence on an entity or decision is an error: a claim with nothing
behind it is not checkable. Code-only evidence without `test_attempted` and
`fallback_reason` is a warning, never a gate. Local refs must resolve, and no
evidence or `source_of_truth` entry may point into `.devspark.work/` or
`.archive/`.

## Pinned claims and drift

`.knowledge/knowledge.config.yaml`:

```yaml
knowledge_drift:
  enforcement: last-verified   # or pinned-claims
```

A `source_of_truth` entry may be a plain path or an object claim:

```yaml
source_of_truth:
  - path: src/Auth/TokenService.cs
    profile: text                     # text (whitespace-normalized) or exact
    region: {start_marker: "RefreshToken(", end_marker: "}"}   # or {lines: "10-40"}
    digest: sha256:<hex>
    baseline: .knowledge/ontology/baselines/<hex>.txt
    verification: {state: verified}   # or unverified
```

- `--pin-claim <path>` retains the canonical baseline and prints a claim with
  `verification.state: unverified`. Only `/devspark.explain` records
  `verified`, after the human confirms the retained-baseline diff. Baselines no
  claim references are reported as `orphan-baseline` warnings and are never
  deleted by the engine; remove them by hand once they are truly unused.
- `--detect-drift` compares each claim's current canonical content with its
  retained baseline, bounded to `--base <ref> [--head <ref>]` or a history-free
  `--full-inventory`. It is read-only and never asserts human verification.
- Under `pinned-claims`, drift fails the run and plain-path entries warn.

## Discovery

The engine indexes each document's id, title, `aliases`, headings, and path
metadata (`appliesTo`, `source_of_truth`) into `index.json`. Body prose is
searched only at query time by `explain-context.py`. Ranking is deterministic:

| Evidence class | Weight |
|---|---:|
| Exact id/title | 100 |
| Alias | 60 |
| Heading | 30 |
| Path/`appliesTo`/`source_of_truth` metadata | 15 |
| Body | 5 |

Each class contributes its weight at most once per query term; every match
reports `matched_on` explaining why it scored.

## Engine commands

| Command | Effect |
|---|---|
| `build_knowledge_index.py` | Validate and write `index.json` and `coverage.json` |
| `build_knowledge_index.py --check [--entity <id>]` | Fail on stale output or gating errors; never writes |
| `build_knowledge_index.py --search "<query>"` | Ranked discovery over index classes (JSON) |
| `build_knowledge_index.py --detect-drift --base <ref>` | Pinned-claim drift for changed paths (JSON) |
| `build_knowledge_index.py --detect-drift --full-inventory` | Pinned-claim drift for every claim (JSON) |
| `build_knowledge_index.py --pin-claim <path>` | Retain a baseline and print a claim (JSON) |
| `explain-context.py "<topic>"` | Ranked discovery including body prose (JSON) |
| `migrate-knowledge-to-entities.py [--dry-run] [--force]` | Migrate older `.knowledge` layouts to this contract; reports conflicts (YAML comments, disagreeing `governs`/`constrains`) and skips them unless `--force` |
| `discover-knowledge-context.py <entity \| path \| term> \| --all` | Read-only discovery signals (gaps, mapping breadth, overlaps, relationship and alias candidates, stale references, historical leakage) for `/devspark.discover-knowledge` |
| `scan-ephemeral-refs.py --base <ref> \| --full-inventory` | Fail when code comments name spec, task, requirement, proposal, or archive identifiers |

`index.json` and `coverage.json` are committed so reviewers and `--check` see the
same index, and they change whenever knowledge headings, aliases, or mappings
change. Mark them `linguist-generated=true` in `.gitattributes` so pull requests
collapse their diffs, and on a merge conflict regenerate them by running the
engine instead of hand-merging.

`coverage.json` answers existence (required layers, evidence counts, findings).
`/devspark.site-audit` owns accuracy: it re-runs `execution` evidence and
judges `inspection` evidence. `index.json` includes `contradiction_scopes`
(same entity, entities sharing a decision, objects citing the same evidence)
that bound audit's contradiction scan; judging a contradiction stays human.
