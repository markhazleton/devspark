---
id: address-pr-review
name: address-pr-review
audience: expert
exposed: false
category: prompt-adapter
description: Atomic shim for /devspark.address-pr-review. Resolves to templates/commands/address-pr-review.md.
inputs: []
outputs: []
command: address-pr-review
---

## Outline

This atomic prompt is a thin prompt adapter. Its execution is delegated to the current canonical command file at `templates/commands/address-pr-review.md`.

The prompt host resolves this id through the standard 3-tier override chain (personal -> team -> stock) and forwards execution to the current command body.
