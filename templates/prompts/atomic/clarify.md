---
id: clarify
name: clarify
audience: expert
exposed: false
category: prompt-adapter
description: Atomic shim for /devspark.clarify. Resolves to templates/commands/clarify.md.
inputs: []
outputs: []
command: clarify
---

## Outline

This atomic prompt is a thin prompt adapter. Its execution is delegated to the current canonical command file at `templates/commands/clarify.md`.

The prompt host resolves this id through the standard 3-tier override chain (personal -> team -> stock) and forwards execution to the current command body.
