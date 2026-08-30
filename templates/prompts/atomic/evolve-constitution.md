---
id: evolve-constitution
name: evolve-constitution
audience: expert
exposed: false
category: prompt-adapter
description: Atomic shim for /devspark.evolve-constitution. Resolves to templates/commands/evolve-constitution.md.
inputs: []
outputs: []
command: evolve-constitution
---

## Outline

This atomic prompt is a thin prompt adapter. Its execution is delegated to the current canonical command file at `templates/commands/evolve-constitution.md`.

The prompt host resolves this id through the standard 3-tier override chain (personal -> team -> stock) and forwards execution to the current command body.
