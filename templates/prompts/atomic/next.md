---
id: next
name: next
audience: expert
exposed: false
category: prompt-adapter
description: Atomic shim for /devspark.next. Resolves to templates/commands/next.md.
inputs: []
outputs: []
command: next
---

## Outline

This atomic prompt is a thin prompt adapter. Its execution is delegated to the current canonical command file at `templates/commands/next.md`.

The prompt host resolves this id through the standard 3-tier override chain (personal -> team -> stock) and forwards execution to the current command body.
