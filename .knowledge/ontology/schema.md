# DevSpark Knowledge Ontology

DevSpark v4 stores current truth under `.knowledge`. The ontology makes that
truth navigable while temporary work packages remain outside permanent context.

## Roots

| Root | Purpose | Managed By |
|---|---|---|
| `.knowledge/entities/<id>/` | Durable current-truth entity records | Humans, assisted by prompts |
| `.knowledge/governance/decisions/<topic>.md` | Current governance decisions | Humans, assisted by prompts |
| `.knowledge/ontology/*.generated.md` | Generated ontology reports | `scripts/python/build_knowledge_index.py` |
| `.devspark.work/` | In-flight work packages only | DevSpark prompts |
| `.archive/YYYY-MM-DD/<topic>/` | Human-only short-term holding area | Humans only |

DevSpark commands must not read, list, enumerate, or glob `.archive/`.

## Entity Folders

Each entity folder must contain:

- `_entity.yaml`: hand-authored metadata.
- `_derived.yaml`: generated metadata written by the ontology generator.
- One or more layer documents, usually `architecture.md`.

Entity ids are lowercase slugs matching `^[a-z0-9][a-z0-9._-]*$`.

## Entity Metadata

`_entity.yaml` fields:

| Field | Required | Meaning |
|---|---:|---|
| `id` | yes | Stable entity id matching the folder name |
| `name` | yes | Human-readable name |
| `kind` | yes | Entity kind from the allowed kind registry |
| `summary` | yes | Present-tense current-truth summary |
| `owner` | no | Responsible role or team |
| `lifecycle` | no | `current` or `transitional`; remove entities that no longer describe current truth |
| `root` | no | Primary repository root or path this entity describes |
| `managed_by` | no | `human`, `prompt`, `script`, `generated`, or `mixed` |
| `required_layers` | no | Required layer documents for this entity |
| `relations` | no | Typed edges to other entities |
| `evidence` | yes | Evidence entries supporting the entity |

If `required_layers` is omitted, `architecture.md` is expected.

## Entity Kinds

Allowed entity kinds:

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

## Relation Types

Allowed relation types:

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

Decision files live at `.knowledge/governance/decisions/<topic>.md`. Each
current decision must contain frontmatter with:

- `id`
- `status: current`
- `governs`
- `evidence`
- `last_verified` when evidence requires inspection recency

`governs` lists entity ids. The generator inverts that list into each entity's
`_derived.yaml` as `constrained_by`.

## Evidence

Evidence entries must include `type`, `ref`, and `verified_by`.

Allowed evidence types:

| Type | Expected Verification |
|---|---|
| `test` | `verified_by: execution` |
| `code` | `verified_by: inspection` |
| `doc` | `verified_by: inspection` |
| `schema` | `verified_by: inspection` |

Local evidence refs must resolve to files or directories unless they are external
URLs. Code-inspection evidence should include `test_attempted` and
`fallback_reason` when executable test evidence was not practical.

## Generated Reports

`scripts/python/build_knowledge_index.py --write` owns:

- `.knowledge/entities/*/_derived.yaml`
- `.knowledge/ontology/coverage.generated.md`
- `.knowledge/ontology/evidence.generated.md`
- `.knowledge/ontology/relations.generated.md`
- `.knowledge/ontology/governance.generated.md`
- `.knowledge/ontology/gaps.generated.md`

Run `scripts/python/build_knowledge_index.py --check` to fail when generated
metadata or reports are stale.
