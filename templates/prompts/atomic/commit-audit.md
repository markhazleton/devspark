---
id: commit-audit
name: commit-audit
audience: expert
exposed: false
category: prompt-adapter
description: Atomic shim for /devspark.commit-audit. Resolves to templates/commands/commit-audit.md.
inputs: []
outputs: []
command: commit-audit
---

## Outline

This atomic prompt is a thin prompt adapter. Its execution is delegated to the current canonical command file at `templates/commands/commit-audit.md`.

The prompt host resolves this id through the standard 3-tier override chain (personal -> team -> stock) and forwards execution to the current command body.
