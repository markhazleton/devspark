---
id: list-applications
name: list-applications
audience: expert
exposed: false
category: prompt-adapter
description: Atomic shim for /devspark.list-applications. Resolves to templates/commands/list-applications.md.
inputs: []
outputs: []
command: list-applications
---

## Outline

This atomic prompt is a thin prompt adapter. Its execution is delegated to the current canonical command file at `templates/commands/list-applications.md`.

The prompt host resolves this id through the standard 3-tier override chain (personal -> team -> stock) and forwards execution to the current command body.
