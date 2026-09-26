# Decisions

Decisions are topic-keyed current governance documents: "here is what we do,
and why not the alternatives", in the present tense. Use exactly one Markdown
file per topic, named by domain or topic (for example `auth-strategy.md`),
never by sequential number.

Decision frontmatter must include `id` (equal to the filename), `type:
governance-decision`, `title`, `constrains` (non-empty entity ids), `evidence`,
and `last_verified`. Each constrained entity lists the decision back in its
`_entity.yaml` `constrained_by`.

When the reasoning changes, edit the decision in place. When the subsystem it
governs no longer exists, delete it. There is no deprecated state.
