# Review-Stage Resolution Contract

The five review-oriented prompts—`clarify`, `analyze`, `critic`, `pr-review`,
and `address-pr-review`—share one structured finding contract while retaining
stage-specific prose and behavior.

## Current status

No review stage declares a shim-level divergence. Structured `findings[]`
output conforms to the fields enforced by
`tests/test_review_resolution_contract.py`.

All atomic prompts under `templates/prompts/atomic/` are thin resolvers. The
canonical command files under `templates/commands/` own command behavior, and
the standard personal → team → stock resolution chain selects the active body.

## Divergence marker

A review command that requires a documented adapter exception must place this
marker in its atomic prompt:

```html
<!-- DIVERGENT: <one-line reason> -->
```

The same command must appear below. The contract test fails when a marker and
this table disagree.

| Stage | Marker text | Contract reason |
|---|---|---|
| *none* | *n/a* | All review commands use the shared resolver contract. |
