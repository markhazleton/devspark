---
id: verify
name: verify
audience: expert
exposed: false
category: prompt-adapter
description: Atomic shim for /devspark.verify. Resolves to templates/commands/verify.md.
inputs: []
outputs: []
command: verify
---

## Outline

This atomic prompt is a thin prompt adapter. Its execution is delegated to the current canonical command file at `templates/commands/verify.md`.

The prompt host resolves this id through the standard 3-tier override chain (personal -> team -> stock) and forwards execution to the current command body.
