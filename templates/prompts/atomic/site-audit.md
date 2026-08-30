---
id: site-audit
name: site-audit
audience: expert
exposed: false
category: prompt-adapter
description: Atomic shim for /devspark.site-audit. Resolves to templates/commands/site-audit.md.
inputs: []
outputs: []
command: site-audit
---

## Outline

This atomic prompt is a thin prompt adapter. Its execution is delegated to the current canonical command file at `templates/commands/site-audit.md`.

The prompt host resolves this id through the standard 3-tier override chain (personal -> team -> stock) and forwards execution to the current command body.
