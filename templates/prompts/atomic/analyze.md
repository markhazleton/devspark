---
id: analyze
name: analyze
audience: expert
exposed: false
category: prompt-adapter
description: Atomic shim for /devspark.analyze. Resolves to templates/commands/analyze.md.
inputs: []
outputs: []
command: analyze
---

## Outline

This atomic prompt is a thin prompt adapter. Its execution is delegated to the current canonical command file at `templates/commands/analyze.md`.

The prompt host resolves this id through the standard 3-tier override chain (personal -> team -> stock) and forwards execution to the current command body.
