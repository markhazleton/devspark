---
id: tasks
name: tasks
audience: expert
exposed: false
category: prompt-adapter
description: Atomic shim for /devspark.tasks. Resolves to templates/commands/tasks.md.
inputs: []
outputs: []
command: tasks
---

## Outline

This atomic prompt is a thin prompt adapter. Its execution is delegated to the current canonical command file at `templates/commands/tasks.md`.

The prompt host resolves this id through the standard 3-tier override chain (personal -> team -> stock) and forwards execution to the current command body.
