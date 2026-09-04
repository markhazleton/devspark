# Quick Start Guide

## Current Release

[![Current Release](https://img.shields.io/github/v/release/markhazleton/devspark?label=current%20release)](https://github.com/markhazleton/devspark/releases/latest)

**Current version:** [v4.2.0](https://github.com/markhazleton/devspark/releases/tag/v4.2.0)

## Step 1: Bootstrap DevSpark

Open a chat with your AI agent inside the target repository and paste the command for your agent:

### GitHub Copilot

```text
@workspace Follow the instructions at https://raw.githubusercontent.com/markhazleton/devspark/main/quickstart/devspark_quickstart_copilot.md
```

### Claude Code

```text
Follow the instructions at https://raw.githubusercontent.com/markhazleton/devspark/main/quickstart/devspark_quickstart_claudecode.md
```

### Cursor

```text
Follow the instructions at https://raw.githubusercontent.com/markhazleton/devspark/main/quickstart/devspark_quickstart_cursor.md
```

### Codex

```text
Follow the instructions at https://raw.githubusercontent.com/markhazleton/devspark/main/quickstart/devspark_quickstart_codex.md
```

For Codex-specific workflow guidance, see [DevSpark and Codex](devspark-and-codex.md).

### Antigravity

```text
Follow the instructions at https://raw.githubusercontent.com/markhazleton/devspark/main/quickstart/devspark_quickstart_antigravity.md
```

For Antigravity-specific workflow guidance, see [DevSpark and Antigravity](devspark-and-antigravity.md).

### Any Other Agent

```text
Follow the instructions at https://raw.githubusercontent.com/markhazleton/devspark/main/quickstart/devspark_quickstart_generic.md
```

The agent first asks only the install-critical questions, checks for existing
DevSpark or legacy layouts, and only asks for project name, tech stack, and core
principles when a constitution still needs to be created.

Run the same quickstart prompt again for upgrades or repairs. Every run checks
`.knowledge/entities/` and `.knowledge/ontology/`, initializes missing scaffold
files, and classifies `.documentation/` intake when that folder exists.

---

## Step 2: Build Your First Feature

Once bootstrapped, run these slash commands in your AI agent's chat.

### 2a. Define Your Constitution

```text
/devspark.constitution Security-first. TDD required. All public APIs must have documentation.
```

### 2b. Create the Spec

Describe **what** you want to build and **why** -- no tech stack yet. Keep it product-focused.

```text
/devspark.specify Build a photo album organizer. Albums grouped by date, drag-and-drop reordering, tile-based photo previews.
```

`/devspark.specify` is route-aware. It recommends a one-off fix, quick spec, or full spec path, explains why, and asks you to confirm before it creates artifacts.

> Anti-pattern: `/devspark.specify Build a React app with Redux and PostgreSQL for photo management` -- this locks you into a solution before the problem is fully understood.

### 2c. Refine the Spec (Optional)

Ask about user needs and constraints, not implementation details.

```text
/devspark.clarify Focus on security and performance requirements.
```

> Anti-pattern: `/devspark.clarify Should we use WebSockets or SSE?` -- save technology choices for the plan phase.

### 2d. Create the Implementation Plan

**Now** provide your tech stack. The plan translates product requirements into architecture.

```text
/devspark.plan Use Vite with vanilla HTML/CSS/JS. Images stored locally, metadata in SQLite.
```

### 2e. Generate Tasks and Implement

```text
/devspark.tasks
```

Run every gate named in the spec frontmatter. A full spec normally requires:

```text
/devspark.checklist
/devspark.analyze
/devspark.critic
```

Then implement:

```text
/devspark.implement
```

Use `/devspark.verify` after implementation when the change needs a focused
behavioral or evidence check. Release performs the final mandatory revalidation.

---

## Step 3: Review and Release

After implementation completes (spec status becomes `Complete`), draft the PR and review it:

```text
/devspark.create-pr
/devspark.pr-review
```

When review finds issues, run `/devspark.address-pr-review`, synchronize the
branch as needed, refresh the description with `/devspark.update-pr`, and run
`/devspark.pr-review UPDATE` against the current commit.

The review checks that the spec is `Complete` and all tasks are done before recommending approval. Merge the PR after approval.

At release time, validate code, tests, knowledge, governance, and task linkage;
archive completed work; update the version; and generate release notes:

```text
/devspark.release
```

See the [Release Guide](release-usage.md) for release validation and archival,
and [Implementation Lifecycle](implementation-lifecycle.md) for the complete
delivery flow.

---

## What's Next

- [Upgrade Guide](upgrade.md) -- keep DevSpark current
- [DevSpark and Codex](devspark-and-codex.md) -- best practices for using Codex with DevSpark
- [Implementation Lifecycle](implementation-lifecycle.md) -- full workflow overview
- [Release Guide](release-usage.md) -- final validation and release-only archival
- [Constitution Guide](constitution-guide.md) -- writing effective project principles
- [FAQ](faq.md) -- common questions answered
- [Command Reference](index.md#command-categories) -- all DevSpark commands
