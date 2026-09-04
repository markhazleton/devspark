---
id: explain
name: explain
audience: expert
exposed: false
category: prompt-adapter
description: Atomic shim for /devspark.explain. Resolves to templates/commands/explain.md.
inputs: []
outputs: []
command: explain
---

## Outline

This atomic prompt is a thin prompt adapter. Its execution is delegated to the current canonical command file at `templates/commands/explain.md`.

The prompt host resolves this id through the standard 3-tier override chain (personal -> team -> stock) and forwards execution to the current command body.
