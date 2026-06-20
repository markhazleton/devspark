---
description: Learn how DevSpark integrates with Antigravity as a first-class AI coding assistant.
---

# DevSpark and Antigravity

DevSpark offers first-class support for **Antigravity**, a powerful agentic AI coding assistant designed by the Google DeepMind team.

Antigravity uses a markdown-based shim interface placed inside the `.gemini/commands/` directory, mirroring the structure used by other leading assistants like Claude Code and GitHub Copilot. This allows you to drive the Spec-Driven Development (SDD) process natively through Antigravity.

## Installation

Since Antigravity operates natively within the environment, no external CLI tool needs to be installed. DevSpark automatically recognizes Antigravity using the `.gemini/commands/` folder structure and the `ANTIGRAVITY.md` context file.

### Bootstrapping DevSpark

To initialize DevSpark with Antigravity:

```bash
devspark init --ai antigravity
```

This command will:

1. Scaffold the DevSpark architecture (memory, specs, scripts).
2. Generate the markdown command shims into `.gemini/commands/`.
3. Create the `ANTIGRAVITY.md` context file to provide Antigravity with persistent instructions about the DevSpark methodology.

## How it Works

DevSpark uses a multi-tier shim resolution strategy for Antigravity:

- **Stock commands** are placed in `.gemini/commands/` and give Antigravity the ability to run DevSpark operations (like `plan`, `tasks`, `implement`).
- Antigravity parses these markdown files for instructions on how to call the DevSpark CLI in the background to execute tasks securely and autonomously.

Because Antigravity integrates so deeply with your local workspace, DevSpark helps maintain strict architectural boundaries by enforcing limits on where code can be modified and requiring explicit approvals for architectural changes.
