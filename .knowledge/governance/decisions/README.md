---
id: decisions-readme
type: governance
title: "Governance Decisions"
---

<!-- markdownlint-disable MD025 -->

# Governance Decisions

A decision doc answers "what did we choose, and why not the alternatives?" as a **present-tense
claim** — it is current governance, not a change log. One file per domain/topic
(`auth-strategy.md`, not `0001-auth-strategy.md` or `ADR-003-auth-strategy.md`): when the reasoning
behind a decision changes, edit the existing file in place instead of adding a second, competing
file for the same topic or a note pointing at an earlier version. Sequential filenames and any
chain-of-versions language are both rejected by `scripts/build_knowledge_index.py`, which also
rejects the same prohibited frontmatter keys as any other current-knowledge doc (see
`templates/schemas/knowledge-node.schema.json`).

## Frontmatter contract

```yaml
---
id: auth-strategy
type: governance-decision
title: "Authentication strategy"
constrains:
  - identity-service
---
```

`constrains` lists the `.knowledge/entities/<id>/` this decision constrains. Each listed entity's
`_entity.yaml` must carry a reciprocal `constrained_by: [auth-strategy]` pointer — the decision owns
the reasoning, the entity only carries a lightweight pointer back, so an agent reading the entity
always sees that a constraint exists without governance content being duplicated into the entity.
Cross-cutting decisions that don't map to a single entity yet should still be written here (empty
`constrains` is not permitted — capture the affected entity even if the fit is imperfect, or file it
once the entity exists).

## Lifecycle

- **Create** when a real choice is made between alternatives that a future change could get wrong
  by "going back" to a rejected option.
- **Edit in place** whenever the reasoning changes, a new alternative is considered, or an
  `/devspark-implement` delta touches something the decision claims about.
- **Delete** when the decision becomes moot (the constrained entity or subsystem no longer exists).
  Git history is the only place a deleted decision is recoverable — never move it to an archive.
