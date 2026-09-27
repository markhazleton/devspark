# Knowledge Entities

Each folder under `.knowledge/entities/` describes one current entity. Entity
metadata lives in the hand-authored `_entity.yaml` (including `constrained_by`,
the reciprocal of each decision's `constrains`). Layer documents describe
current behavior only and carry `source_of_truth` and `last_verified`
frontmatter.

Every entity must cite evidence. Prefer test evidence (`verified_by:
execution`); fall back to code inspection evidence with `test_attempted` and
`fallback_reason` when a test is not practical.

Never use `status`, `lifecycle`, `supersedes`, `superseded-by`, `replaced`, or
`obsolete`: edit current knowledge in place or delete it. Git holds history.
