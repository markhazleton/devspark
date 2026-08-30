---
id: add-application
name: add-application
audience: expert
exposed: false
category: prompt-adapter
description: Atomic shim for /devspark.add-application. Resolves to templates/commands/add-application.md.
inputs: []
outputs: []
command: add-application
---

## Outline

This atomic prompt is a thin prompt adapter. Its execution is delegated to the current canonical command file at `templates/commands/add-application.md`.

The prompt host resolves this id through the standard 3-tier override chain (personal -> team -> stock) and forwards execution to the current command body.
