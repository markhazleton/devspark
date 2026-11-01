---
id: content-lifecycle
type: authoritative-reference
title: "Knowledge Content Lifecycle"
---

<!-- markdownlint-disable MD025 -->

# Knowledge Content Lifecycle

Defines where durable knowledge lives and how its currentness is enforced. Authoritative governance
is [../governance/constitution.md](../governance/constitution.md); day-to-day authoring steps are in
[developer-guide.md](developer-guide.md).

## Content roots

`.knowledge/` holds current, authoritative project truth only. There is no archive folder: stale
material is deleted, not moved — git history is the sole record of anything no longer current. See
`templates/commands/release.md` for the maintenance workflow that finds and removes stale content.

## Knowledge index

| Path | Audience | What it holds |
|------|----------|----------------|
| [../governance/](../governance/) | Engineering / architects | Constitution and governance docs |
| [../governance/decisions/](../governance/decisions/) | Engineering / architects | Cross-cutting decisions: what we chose, why not the alternatives — current governance, not history |
| [../architecture/](../architecture/) | Engineering | Flat-type architecture docs (pre-entity-ontology, still supported) |
| [../entities/](../entities/) | Engineering | Entity-ontology nodes: one folder per domain entity, `_entity.yaml` + layer docs |
| [../ontology/](../ontology/) | Engineering | Generated entity coverage/gap report (`coverage.json`) |
| [../reference/](../reference/) | Engineering | Structured reference data and validated samples |
| [../guides/](../guides/) | Developers using DevSpark | Published task-oriented guidance for a capability that has shipped: setup, prerequisites, day-to-day use, failure modes |
| [./](./) | Engineering | Repository tooling and authoring guidance (this folder) |

Both the flat type-folder model and the entity-ontology model are valid simultaneously. Existing
`architecture/` and `governance/` docs do not need to migrate — Principle I (Backward Compatibility)
requires the entity model to be strictly additive and opt-in.

## Where does my new content go?

- **Rules / governance / schema contracts** → `.knowledge/governance/`.
- **A cross-cutting decision ("what did we choose, and why not the alternatives")** →
  `.knowledge/governance/decisions/<topic>.md` (`type: governance-decision`), keyed by domain/topic
  and edited in place — never `.devspark.work/`, never numbered, never a second competing file for
  the same topic. See [../governance/decisions/README.md](../governance/decisions/README.md).
- **A new feature or bug fix** → `/devspark-specify` or `/devspark-quickfix` creates temporary
  planning records under `.devspark.work/`; these are deleted after implementation, never cited from
  `.knowledge/`.
- **"How does subsystem X work?" (internal, has a clear owning domain)** → new or existing
  `.knowledge/entities/<id>/architecture.md` (`layer: architecture`), or `.knowledge/architecture/`
  if you're not adopting entities for this doc yet.
- **A cross-cutting engineering pattern** → `.knowledge/entities/<id>/pattern.md` (`layer: pattern`)
  or `.knowledge/patterns/`.
- **A domain / business-logic guide** → `.knowledge/entities/<id>/business.md` (`layer: business`).
- **"How do I call the API?" (external consumer)** → `.knowledge/entities/<id>/integration.md`
  (`layer: integration`).
- **A runbook / alert / observability query** → `.knowledge/entities/<id>/operations.md`
  (`layer: operations`) or `.knowledge/operations/`.
- **Designed-but-unscheduled future work** → `.knowledge/entities/<id>/plan.md` (`layer: plan`).
- **A validated sample/reference snapshot** → `.knowledge/reference/`.
- **"How do I use capability X?" (task-oriented, aimed at a developer operating the tool)** →
  `.knowledge/guides/<capability>.md`. Publish the guide when the capability ships, not while it is
  still being built — `.knowledge/` holds what is true now, and a guide for unreleased behavior
  reads as current truth to everyone who finds it.

## Knowledge Content Rules

1. **Keep the corpus self-contained.** Do not cite `.devspark.work/` planning-record paths (spec,
   quickfix, task IDs) from `.knowledge/`. Preserve necessary context as local prose instead.
2. **Record durable current truth only.** Frontmatter must not carry lifecycle-state or
   prior-version-pointer keys (see the prohibited-key list in
   `templates/schemas/knowledge-node.schema.json`), and body text must not describe a document as
   no-longer-current or point readers to a decision-log/rationale-archive as authority. Enforced by
   `scripts/build_knowledge_index.py`.
3. **Use the correct home.** Governance in `governance/`; domain entities in `entities/<id>/` with an
   explicit `layer`; validated samples in `reference/`; tooling guidance in `tooling/` (this folder).
4. **Keep source claims narrow and accurate.** Every entity-layer doc must carry `layer` and
   `source_of_truth`; `last_verified` is optional. Every source claim must name an existing regular
   file, not a directory, and object claims must have a unique `(path, profile, region)` tuple. The
   content-drift evaluator reports a missing or directory source as an authoring error rather than
   silently widening the claim. Entity nodes (`_entity.yaml`) declare `id`, `type`, `owner`,
   `relations`, and any justified `coverage_overrides` for layers that don't apply.
5. **Keep decisions current, edited in place.** A `governance-decision` doc is updated in place when
   its reasoning changes — never numbered by creation order and never a second, competing file for
   the same topic — and deleted (not archived) when moot. Its `constrains` array must name real entities, and each named
   entity's `_entity.yaml` must carry the matching `constrained_by` pointer back; both directions are
   validated by `scripts/build_knowledge_index.py`. A delta that touches anything a decision claims
   about must correct that decision in place before the change is considered done.
6. **Link internally and intentionally.** Relative Markdown links must resolve within `.knowledge/`.
7. **Protect sensitive data.** Use only synthetic examples — never personal, health, authentication,
   financial, or deployment-secret data in prose, samples, or reference files.
8. **Preserve generated ownership.** Never hand-edit `.knowledge/index.json` or
   `.knowledge/ontology/coverage.json`. They are optional build output; when you want fresh copies,
   regenerate both via `scripts/build_knowledge_index.py` (wrapped by
   `scripts/powershell/generate-knowledge-index.ps1` and `scripts/bash/generate-knowledge-index.sh`).
   A stale copy never blocks a change.
9. **Treat breadth as guidance.** When a document intentionally names several source files, use
  `--breadth-guidance <count>` to surface a non-blocking advisory and review whether the claims
  can be narrowed; do not replace a missing file with its parent directory.
