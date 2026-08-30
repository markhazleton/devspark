---
id: repo-story
name: repo-story
audience: expert
exposed: false
category: prompt-adapter
description: Atomic shim for /devspark.repo-story. Resolves to templates/commands/repo-story.md.
inputs: []
outputs: []
command: repo-story
---

## Outline

This atomic prompt is a thin prompt adapter. Its execution is delegated to the current canonical command file at `templates/commands/repo-story.md`.

The prompt host resolves this id through the standard 3-tier override chain (personal -> team -> stock) and forwards execution to the current command body.
