---
evidence:
  - type: code
    ref: templates/commands
    verified_by: inspection
    test_attempted: true
    fallback_reason: "Prompt behavior is prose-driven and requires review plus frontmatter contract tests"
---

# Command Template Architecture

Command templates are the canonical prompt source. Generated atomic prompts and
agent-specific shims remain thin resolvers. Temporary lifecycle artifacts live
in `.devspark.work/`; code, tests, and `.knowledge/` hold current truth; release
alone moves validated completed packages to the human-only archive buffer.
