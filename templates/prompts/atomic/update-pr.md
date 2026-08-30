---
id: update-pr
name: update-pr
audience: expert
exposed: false
category: prompt-adapter
description: Atomic shim for /devspark.update-pr. Resolves to templates/commands/update-pr.md.
inputs: []
outputs: []
command: update-pr
---

## Outline

This atomic prompt is a thin prompt adapter. Its execution is delegated to the current canonical command file at `templates/commands/update-pr.md`.

The prompt host resolves this id through the standard 3-tier override chain (personal -> team -> stock) and forwards execution to the current command body.
