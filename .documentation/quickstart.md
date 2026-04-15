# Quick Start Guide

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

### Any Other Agent

```text
Follow the instructions at https://raw.githubusercontent.com/markhazleton/devspark/main/quickstart/devspark_quickstart_generic.md
```

The agent first asks only the install-critical questions, checks for existing DevSpark or legacy layouts, and only asks for project name, tech stack, and core principles when a constitution still needs to be created. No CLI required.

> Need terminal-driven setup or execution? See [Other Ways to Get Started](installation.md) for CLI installation options, then use the runtime guidance in [Harness Engineering](harness-engineering.md).

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

Optionally validate first with `/devspark.analyze` or `/devspark.critic`, then:

```text
/devspark.implement
```

---

## Step 3: Review and Release

After implementation completes (spec status becomes `Complete`), draft the PR and review it:

```text
/devspark.create-pr
/devspark.pr-review
```

If you push more commits after review feedback or a rebase, refresh the description with `/devspark.update-pr` before re-reviewing.

The review checks that the spec is `Complete` and all tasks are done before recommending approval. Merge the PR after approval.

At the end of the sprint, archive completed specs and generate release notes:

```text
/devspark.release
```

See [Implementation Lifecycle](implementation-lifecycle.md) for the full spec status lifecycle and sprint cadence.

---

## What's Next

- [Upgrade Guide](upgrade.md) -- keep DevSpark current
- [Implementation Lifecycle](implementation-lifecycle.md) -- full workflow overview
- [Harness Engineering](harness-engineering.md) -- optional CLI runtime for declarative workflows
- [Constitution Guide](constitution-guide.md) -- writing effective project principles
- [FAQ](faq.md) -- common questions answered
- [Command Reference](index.md#command-categories) -- all 27 commands
