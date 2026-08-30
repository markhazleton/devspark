# DevSpark Knowledge Ontology

DevSpark v4 stores current truth under `.knowledge`.

- Entities live under `.knowledge/entities/<id>/`.
- Decisions live under `.knowledge/governance/decisions/<topic>.md`.
- Generated reports live under `.knowledge/ontology/`.
- In-flight work lives under `.devspark.work/` and is deleted after
  verify-before-delete succeeds.

Permanent code and `.knowledge` files may reference each other, but must not
reference repo-internal ephemeral artifacts such as `.devspark.work`,
`.documentation/specs`, `.documentation/releases`, `.archive`, quickfix records,
or PR review files.
