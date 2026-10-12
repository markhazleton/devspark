---
id: developer-guide
type: authoritative-reference
title: "Knowledge Authoring Developer Guide"
---

<!-- markdownlint-disable MD025 -->

# Knowledge Authoring Developer Guide

Practical guidance for adding or changing content under `.knowledge/`. Governance rules live in
[content-lifecycle.md](content-lifecycle.md) and [../governance/constitution.md](../governance/constitution.md);
this page is the how-to.

## Two coexisting models

- **Flat type-folder docs** (`architecture/`, `governance/`, `reference/`) — classify with `type:`
  frontmatter from the enum in `templates/schemas/knowledge-node.schema.json`. This is the default
  and requires no extra setup.
- **Entity-ontology docs** (`entities/<id>/`) — opt-in. Each entity folder holds one `_entity.yaml`
  node plus one or more layer docs (`architecture.md`, `business.md`, `integration.md`,
  `operations.md`, `pattern.md`, `plan.md`), each with `type: entity-layer` and required `layer`,
  `source_of_truth`, `last_verified` frontmatter.

Adopt entities per-domain, incrementally — you don't need to migrate everything at once. Use
`scripts/migrate-knowledge-to-entities.py --dry-run --json` to preview moving existing
`architecture/`, `patterns/`, `operations/` docs into entity folders, or run
`/devspark-migrate-knowledge-entities` to drive the same script (dry-run, confirm, apply, rebuild the
index) as a guided command.

## Adding a new entity

1. Create `.knowledge/entities/<id>/_entity.yaml` by hand with `id`, `type`, `owner`.
2. Add one layer doc per applicable layer, e.g. `.knowledge/entities/<id>/architecture.md`:

   ```yaml
   ---
   type: entity-layer
   layer: architecture
   title: "<Entity> architecture"
   source_of_truth:
     - scripts/<module>.py
   last_verified: 2026-08-30
   ---
   ```

3. Run `python scripts/build_knowledge_index.py --repo-root .` to regenerate `index.json` and
   `.knowledge/ontology/coverage.json`. Fix any validation errors before committing.
4. If a layer legitimately doesn't apply (e.g. no external consumers, so no `integration` layer),
   add a `coverage_overrides` entry to `_entity.yaml` with a `justification` instead of leaving it
   silently missing.

**Assisted (scaffold script)**: instead of hand-writing steps 1-2, run
`python scripts/scaffold-entity.py --entity-id <id> --type <type> --owner <owner> --source
<path> --layer <layer>` to print a draft `_entity.yaml` + layer doc(s) grounded in the cited
source path(s) (dry-run by default). Review the draft, then re-run with `--write` to create the
files — it refuses to overwrite an existing entity without `--force`. This is an authoring aid
only: it never fabricates a behavioral claim, and the drafted body is a placeholder (or a
best-effort Python docstring) that still needs human review before it's accurate. Continue with
steps 3-4 above afterward.

## Keeping `source_of_truth` honest

Legacy string claims remain supported, including their `stale_entities` output and the optional
`--fail-on-stale` currency check. That date-based signal is advisory during ordinary generation
and is not proof that behavior changed. Do not clear it by hand-editing a date; use
`/devspark-explain <topic>` to inspect the cited source and update the knowledge document.

For content drift detection, migrate a claim with
`python scripts/build_knowledge_index.py --migrate-source-claims` and review the preview before
using `--write`. Migration records a canonical digest and retained baseline with
`verification.state: pinned-unverified`; it does not assert human review or enable enforcement.
Opt in explicitly through `.devspark.work/devspark.json`:

```json
{
   "knowledge_drift": {
      "enforcement": "pinned-claims"
   }
}
```

Run full inventory when Git history is unavailable:

```powershell
python scripts/build_knowledge_index.py --repo-root . --detect-drift --full-inventory \
   --report-output drift-report.json
```

Run routine evaluation only with explicit, resolvable `--base` and `--head` commits. The engine
derives the complete three-dot change set, rejects missing or incomplete scope, and fails closed
without findings when it cannot establish trustworthy inputs. `--report-output` is a versioned,
atomic JSON envelope; drift findings contain paths and digests, never source or baseline bodies.

Pinned-unverified claims are advisory: they appear with matching counts and document items in the
human summary and machine report, are never labeled verified-current, do not become blocking drift,
and return exit code `0` when they are the only condition. Verified claims whose canonical content
changed return exit code `1`; invalid inputs or runtime controls return `2` with zero findings.

Currency is separate from drift. Use `--currency-report --currency-days <days>` for an advisory
age report; its result cannot change the drift exit code. To re-verify a changed claim, run
`/devspark-explain <topic>` and inspect the retained-baseline diff before confirming. The workflow
atomically rotates the digest and baseline and removes only unreferenced evidence.

## Choosing a comparison profile

Use `python-token-v1` for Python when comment and layout-only edits should remain quiet. A named
function or class region can narrow the comparison; if that region cannot be resolved, evaluation
widens to the whole source and emits a non-blocking `region-widened` advisory. Behavioral token
changes still drift.

Use `exact-text-v1` when every normalized text change matters. Line-ending normalization is
deterministic, but content changes remain visible. Use `binary-v1` for byte-exact content. For an
unsupported format or a profile failure, the evaluator falls back conservatively to exact text and
does not suppress a difference it cannot prove non-behavioral.

## Adding or updating a governance decision

1. Create or open `.knowledge/governance/decisions/<topic>.md` (topic-keyed filename, e.g.
   `auth-strategy.md` — never a numbered or `ADR-NNN` filename).
2. Frontmatter needs `type: governance-decision` and a non-empty `constrains` array of entity ids:

   ```yaml
   ---
   id: auth-strategy
   type: governance-decision
   title: "Authentication strategy"
   constrains:
     - identity-service
   ---
   ```

3. Add `constrained_by: [auth-strategy]` to every listed entity's `_entity.yaml`. The builder
   rejects a decision whose `constrains` entity is missing the reciprocal pointer, and rejects an
   entity `constrained_by` entry that isn't backed by a matching decision.
4. When the reasoning changes, edit the file in place — do not create a new dated or numbered file
   and do not add version-chain language; sequential filenames and that language are both
   rejected by the builder. Delete the file (git preserves the history) once the decision is moot.
5. Run the same index regeneration command as below and fix any validation errors.

## Making a document discoverable

Knowledge that cannot be found is indistinguishable from knowledge that does not exist. Retrieval
therefore reads a document by the concepts it explains, not only by its filename or mappings. Three
discovery fields feed ranking:

| Field | Source | Where it lives |
| --- | --- | --- |
| `headings` | ATX headings in the body | Indexed; headings inside fenced code blocks are ignored |
| `aliases` | Optional `aliases:` frontmatter | Indexed; only present when declared |
| Body prose | Normalized body text | Rebuilt per query, never committed |

Body text is deliberately absent from `index.json`. Committing it inflates a file that is reviewed
on every documentation change by roughly an order of magnitude, and forces a regeneration for edits
that change no structure. Retrieval instead re-reads the Markdown it already knows about, which
costs a fraction of a second on a full corpus and can never go stale.

All three are derived data rebuilt from the Markdown; the file stays authoritative, so never edit
discovery fields in `index.json`. Frontmatter is never indexed as body content, so declaring
metadata does not pad a document's body relevance.

Ranking is deterministic and identical for every agent. A keyword scores once per field — never
once per occurrence — so relevance comes from *where* a term appears, not how often, and a long
document cannot outrank a precise one by repetition. Fields are weighted in this order, strongest
first:

1. The whole query matching a node's `id` or `title` exactly
2. A declared alias appearing verbatim in the query
3. `id`, then `title` keywords
4. Alias keywords
5. Heading keywords
6. Path metadata — `path`, `appliesTo`, `source_of_truth`
7. Body content

Each match reports why it ranked, as evidence entries like `heading: Disconnect and Abandonment`
or `body: abandoned, outcome`. A result with a score and no explanation is a bug.

### When to add aliases

Add `aliases` when readers reliably reach for vocabulary the document does not itself use — a
retired product name, a colloquial term for a modeled concept, or the phrasing that shows up in
support tickets:

```yaml
aliases:
  - abandoned conversation
  - user disconnect
  - session termination
```

Aliases are discovery metadata only. They do not alter the knowledge taxonomy, create ontology
relationships, change a document's identity, or become a source of authoritative behavioral truth.
If a term needs to *mean* something, write it in the body — that is what gets read.

Reach for the body first. A concept explained clearly in prose is already discoverable; an alias is
for the gap between how the author writes and how the reader asks.

## Regenerating the index

Never hand-edit `.knowledge/index.json` or `.knowledge/ontology/coverage.json` — both are fully
generated:

```powershell
.devspark/scripts/powershell/generate-knowledge-index.ps1
```

```bash
.devspark/scripts/bash/generate-knowledge-index.sh
```

Both wrappers call `scripts/build_knowledge_index.py`, which is the single source of truth for
index/coverage generation across languages (constitution Principle VI).
