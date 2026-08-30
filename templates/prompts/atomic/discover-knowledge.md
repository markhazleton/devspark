---
id: discover-knowledge
name: discover-knowledge
audience: expert
exposed: false
category: prompt-adapter
description: Atomic shim for /devspark.discover-knowledge. Resolves to templates/commands/discover-knowledge.md.
inputs: []
outputs: []
command: discover-knowledge
---

## Outline

This atomic prompt is a thin prompt adapter. Its execution is delegated to the current canonical command file at `templates/commands/discover-knowledge.md`.

The prompt host resolves this id through the standard 3-tier override chain (personal -> team -> stock) and forwards execution to the current command body.
