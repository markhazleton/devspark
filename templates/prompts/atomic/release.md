---
id: release
name: release
audience: expert
exposed: false
category: prompt-adapter
description: Atomic shim for /devspark.release. Resolves to templates/commands/release.md.
inputs: []
outputs: []
command: release
---

## Outline

This atomic prompt is a thin prompt adapter. Its execution is delegated to the current canonical command file at `templates/commands/release.md`.

The prompt host resolves this id through the standard 3-tier override chain (personal -> team -> stock) and forwards execution to the current command body.
