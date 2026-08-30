---
id: discover-constitution
name: discover-constitution
audience: expert
exposed: false
category: prompt-adapter
description: Atomic shim for /devspark.discover-constitution. Resolves to templates/commands/discover-constitution.md.
inputs: []
outputs: []
command: discover-constitution
---

## Outline

This atomic prompt is a thin prompt adapter. Its execution is delegated to the current canonical command file at `templates/commands/discover-constitution.md`.

The prompt host resolves this id through the standard 3-tier override chain (personal -> team -> stock) and forwards execution to the current command body.
