---
id: fix-score
name: fix-score
audience: expert
exposed: false
category: prompt-adapter
description: Atomic shim for /devspark.fix-score. Resolves to templates/commands/fix-score.md.
inputs: []
outputs: []
command: fix-score
---

## Outline

This atomic prompt is a thin prompt adapter. Its execution is delegated to the current canonical command file at `templates/commands/fix-score.md`.

The prompt host resolves this id through the standard 3-tier override chain (personal -> team -> stock) and forwards execution to the current command body.
