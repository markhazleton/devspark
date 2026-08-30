---
evidence:
  - type: code
    ref: templates/commands
    verified_by: inspection
    test_attempted: true
    fallback_reason: "Prompt behavior is prose-driven and requires review plus frontmatter contract tests"
---

# Command Template Architecture

Command templates remain the canonical prompt source. Generated atomic prompt
shims and agent-specific command shims derive from these templates, while v4
changes the lifecycle semantics from durable spec history to ephemeral work
packages and current-truth knowledge.
