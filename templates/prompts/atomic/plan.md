---
id: plan
name: plan
audience: expert
exposed: false
category: prompt-adapter
description: Atomic shim for /devspark.plan. Resolves to templates/commands/plan.md.
inputs: []
outputs: []
command: plan
---

## Outline

This atomic prompt is a thin prompt adapter. Its execution is delegated to the current canonical command file at `templates/commands/plan.md`.

The prompt host resolves this id through the standard 3-tier override chain (personal -> team -> stock) and forwards execution to the current command body.
