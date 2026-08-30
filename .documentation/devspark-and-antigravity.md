---
description: Learn how DevSpark integrates with Antigravity as a first-class AI coding assistant.
---

# DevSpark and Antigravity

DevSpark offers first-class support for **Antigravity**, a powerful agentic AI coding assistant designed by the Google DeepMind team.

Antigravity uses a markdown-based shim interface placed inside the `.gemini/commands/` directory, mirroring the structure used by other leading assistants like Claude Code and GitHub Copilot. This allows you to drive the Spec-Driven Development (SDD) process natively through Antigravity.

## Installation

### Bootstrapping DevSpark

Open Antigravity in the target repository and run the Antigravity quickstart
prompt:

```text
Follow the instructions at https://raw.githubusercontent.com/markhazleton/devspark/main/quickstart/devspark_quickstart_antigravity.md
```

The quickstart prompt will:

1. Scaffold the DevSpark prompt architecture.
2. Generate markdown command shims into `.gemini/commands/`.
3. Create the `ANTIGRAVITY.md` context file with durable DevSpark guidance.
4. Install or refresh framework-owned assets under `.devspark/`.

## How it Works

DevSpark uses a multi-tier shim resolution strategy for Antigravity:

- **Stock commands** are placed in `.devspark/defaults/commands/`.
- **Antigravity shims** are placed in `.gemini/commands/` and resolve to the
  personal, team, or stock prompt.

Because Antigravity integrates so deeply with your local workspace, DevSpark helps maintain strict architectural boundaries by enforcing limits on where code can be modified and requiring explicit approvals for architectural changes.
