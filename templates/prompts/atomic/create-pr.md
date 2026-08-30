---
id: create-pr
name: create-pr
audience: expert
exposed: false
category: prompt-adapter
description: Atomic shim for /devspark.create-pr. Resolves to templates/commands/create-pr.md.
inputs: []
outputs: []
command: create-pr
---

## Outline

This atomic prompt is a thin prompt adapter. Its execution is delegated to the current canonical command file at `templates/commands/create-pr.md`.

The prompt host resolves this id through the standard 3-tier override chain (personal -> team -> stock) and forwards execution to the current command body.
