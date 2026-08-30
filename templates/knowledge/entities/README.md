# Knowledge Entities

Each folder under `.knowledge/entities/` describes one current entity. Entity
metadata lives in `_entity.yaml`; generated metadata lives in `_derived.yaml`;
layer documents describe current behavior only.

Every entity must cite evidence. Use test evidence when practical and code
inspection evidence with `test_attempted` and `fallback_reason` when a test is
not practical.
