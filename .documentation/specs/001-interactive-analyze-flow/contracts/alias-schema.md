# Contract: Alias Entrypoint Schema

YAML files under `templates/aliases/<id>.yaml`. Validated by `tests/test_alias_resolution_contract.py`.

```yaml
id: create-spec                          # required, must equal filename minus .yaml
target_workflow: create-spec             # required, MUST resolve to templates/workflows/<target_workflow>.yaml
description: >                           # required
  Single entrypoint for spec → plan → tasks → analyze.
```

## Rules

| Rule | Error code |
|------|------------|
| `target_workflow` resolves through 3-tier chain | `ALIAS_TARGET_UNKNOWN` |
| Aliases MUST NOT point to other aliases | `ALIAS_CHAIN_FORBIDDEN` |
| Alias `id` MUST be unique across the alias namespace | `ALIAS_DUPLICATE` |
| Alias `id` MUST NOT collide with an atomic prompt `id` | `ALIAS_NAME_COLLISION` |

## Resolution semantics

`devspark run create-spec` resolves in this order:

1. Alias lookup → `templates/aliases/create-spec.yaml`
2. `target_workflow` lookup → `templates/workflows/create-spec.yaml`
3. Workflow execution begins

If step 1 misses, runner falls back to direct workflow lookup. If step 2 misses, runner aborts with `ALIAS_TARGET_UNKNOWN`.
