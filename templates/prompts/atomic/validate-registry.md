---
id: validate-registry
name: validate-registry
audience: expert
exposed: false
category: prompt-adapter
description: Atomic shim for /devspark.validate-registry. Resolves to templates/commands/validate-registry.md.
inputs: []
outputs: []
command: validate-registry
---

## Outline

This atomic prompt is a thin prompt adapter. Its execution is delegated to the current canonical command file at `templates/commands/validate-registry.md`.

The prompt host resolves this id through the standard 3-tier override chain (personal -> team -> stock) and forwards execution to the current command body.
