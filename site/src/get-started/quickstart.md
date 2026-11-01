# Quick Start Guide

There are two ways to start:

- **Path A — Evaluate One Task.** The minimal, reversible path for a first-time user trying DevSpark on one real task. Start on the [Evaluate One Task](evaluate-one-task.md) page instead of this one if that's your goal.
- **Path B — Initialize the full workflow.** For teams ready to establish repository-level configuration: a constitution, and ongoing specification, planning, task, implementation, review, and release workflows. This page covers Path B.

Both paths install the same files using the same bootstrap step below — the difference is what you do with them afterward. Nothing below writes to your repository until the agent has shown you what it plans to do and you have approved it (see **Preview before you trust**, at the end of Step 1).

## Step 1: Bootstrap DevSpark

Open a chat with your AI agent inside the target repository and paste the bootstrap prompt for your agent:

### GitHub Copilot

```text
@workspace Follow the instructions at https://dev.makeboldspark.com/raw/quickstart/devspark_quickstart_copilot.md
```

Copilot loads DevSpark as native Agent Skills, each invoked with a `/devspark-<command>` slash command. Acceptance was observed in VS Code Insiders 1.142.0 with the built-in Copilot Chat, running locally on Windows: typing `/devspark` lists each of the 38 skills once, and text typed after the slash command (for example `/devspark-specify add a login page`) is passed as input to the skill. Older VS Code builds were not tested.

### Claude Code

```text
Follow the instructions at https://dev.makeboldspark.com/raw/quickstart/devspark_quickstart_claudecode.md
```

### Cursor

```text
Follow the instructions at https://dev.makeboldspark.com/raw/quickstart/devspark_quickstart_cursor.md
```

### Codex

```text
Follow the instructions at https://dev.makeboldspark.com/raw/quickstart/devspark_quickstart_codex.md
```

For Codex-specific workflow guidance, see [DevSpark and Codex](devspark-and-codex.md).

### Antigravity

```text
Follow the instructions at https://dev.makeboldspark.com/raw/quickstart/devspark_quickstart_antigravity.md
```

For Antigravity, prompt shims live in `.gemini/commands/` and the context file is `ANTIGRAVITY.md`; stock prompts stay in `.devspark/defaults/commands/`.

### Any Other Agent

```text
Follow the instructions at https://dev.makeboldspark.com/raw/quickstart/devspark_quickstart_generic.md
```

The agent first asks only the install-critical questions, checks for existing DevSpark or legacy layouts, and only asks for project name, tech stack, and core principles when a constitution still needs to be created. No CLI required.

### Preview before you trust (trust but verify)

You should never run instructions you can't inspect. Every quickstart guide opens with a **Preview Prompt** section so you can *see exactly what will happen before you decide to do it* — nothing is written to your repository until you approve. Two ways to verify first:

- **Read it yourself (no agent, no changes).** The guide, the manifest's full list of every file that would be installed, and the prompt instructions for any `/devspark-*` skill are all plain text you can print to your terminal and read before a single file is created.
- **Ask the agent for a dry run.** Tell it: *"Preview only — show me the mode you'd run, every file you'd create/modify/delete, and the actual skill prompt instructions you'd install. Make no changes and wait for my `proceed`."* In this read-only Preview Prompt Mode the agent displays the plan and stops until you confirm.

See the **Preview Prompt** section at the top of your agent's quickstart guide for copy-paste bootstrap prompts.

---

## Step 2: Build Your First Feature

Once bootstrapped, invoke these skills with their slash commands in your AI agent's chat.
See [Terminology](../guides/prompt-lifecycle-mapping.md#terminology) for the distinction between a skill,
a slash command, an agent, and a prompt.

### 2a. Define Your Constitution

```text
/devspark-constitution Security-first. TDD required. All public APIs must have documentation.
```

### 2b. Start the Work

Describe **what** you want and **why**. Keep it product-focused.

```text
/devspark-specify Build a photo album organizer. Albums grouped by date, drag-and-drop reordering, tile-based photo previews.
```

`/devspark-specify` establishes the outcome and the first useful increment, checks whether any
material risk or mandatory obligation needs assurance, and creates a work branch. There is no route
to choose and no planning file by default; a short `work.md` resume note appears only when intent or
decisions would otherwise be lost. Use the same command for features, fixes, and refactors. In a
later session, `/devspark-next` resumes where you left off.

> Anti-pattern: `/devspark-specify Build a React app with Redux and PostgreSQL for photo management` -- this locks you into a solution before the problem is fully understood.

### 2c. Implement and Verify

The slash-command examples on this page use the DevSpark 9.0 convention, `/devspark-<command>`. If your repository still has 8.x installed, see [Upgrading from 8.x](upgrade.md#upgrading-from-8x).

```text
/devspark-implement
/devspark-verify
```

`/devspark-implement` changes code, tests, and current knowledge together. `/devspark-verify`
produces executable proof and decides whether the work is finished; repeat both until it is.

### 2d. Add Assurance Only When It Earns Its Place (Optional)

None of these is a required step, and none of them triggers another:

- `/devspark-plan Use Vite with vanilla HTML/CSS/JS. Images stored locally, metadata in SQLite.`
  records design decisions when a material uncertainty justifies it. Implementation may follow it but never requires it.
- `/devspark-tasks` persists dependency-ordered deliverables when work spans sessions or people.
- `/devspark-critic` or `/devspark-analyze` examines one specific concern, then returns to implementation.

Existing v9.3 specifications keep their recorded route (plan, tasks, planning review); `/devspark-next` resolves them.

---

## Step 3: Review and Release

After `/devspark-verify` decides the work is finished, draft the PR and review the durable delta. Any
planning record stays live under `.devspark.work/` until `/devspark-release` later archives it under
`.archive/{YYYY-MM-DD}/`:

```text
/devspark-create-pr
/devspark-pr-review
```

If you push more commits after review feedback or a rebase, refresh the description with `/devspark-update-pr` before re-reviewing.

The review checks code, tests, current knowledge, documentation, executable evidence, and the
constitution. It does not require or recover planning files. Merge the PR after approval.

At the end of the release window, verify the durable delta, archive the completed planning bundle,
and generate release notes:

```text
/devspark-release
```

See [How It Works](how-it-works.md) for the one flow, finalization, and
delta-based review.

---

## What's Next

- [Upgrade Guide](upgrade.md) -- keep DevSpark current
- [DevSpark and Codex](devspark-and-codex.md) -- best practices for using Codex with DevSpark
- [How It Works](how-it-works.md) -- full workflow overview
- [Constitution Guide](../guides/constitution-guide.md) -- writing effective project principles
- [FAQ](../why/faq.md) -- common questions answered
