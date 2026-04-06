# Quick Start Guide

**The fastest way to get DevSpark running is the Prompt Bootstrap — no install required.**

> [!TIP]
> **Agent-Agnostic**: DevSpark works identically with any of 17+ supported AI agents. All canonical prompts live in `.documentation/commands/` — your agent gets lightweight shims that redirect there.

---

## Step 1: Bootstrap with a Prompt

Open a chat with your AI agent inside the target repository and paste one of the commands below. The agent asks a few questions about your project, then pulls and installs all DevSpark prompts automatically.

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

### Any other agent

```text
Follow the instructions at https://raw.githubusercontent.com/markhazleton/devspark/main/quickstart/devspark_quickstart_generic.md
```

The agent will ask about your project name, tech stack, script preference, and core principles — then scaffold the full DevSpark structure with no CLI needed.

> [!NOTE]
> Need terminal-driven setup instead? See [Other Ways to Get Started](installation.md) for advanced manual and CLI options.

---

## The DevSpark Workflow (6 Steps)

Once DevSpark is bootstrapped, use these slash commands in your AI agent's chat.

> [!TIP]
> **Context Awareness**: DevSpark commands automatically detect the active feature based on your current Git branch (e.g., `001-feature-name`). Switch Git branches to switch between specs.

### Step 1: Define Your Constitution

**In your AI agent's chat**, use `/devspark.constitution` to establish the core rules and principles for your project. Provide your project's specific principles as arguments.

```markdown
/devspark.constitution This project follows a "Library-First" approach. All features must be implemented as standalone libraries first. We use TDD strictly. We prefer functional programming patterns.
```

### Step 2: Create the Spec

**In the chat**, use `/devspark.specify` to describe what you want to build. Focus on the **what** and **why**, not the tech stack.

```markdown
/devspark.specify Build an application that can help me organize my photos in separate photo albums. Albums are grouped by date and can be re-organized by dragging and dropping on the main page. Albums are never in other nested albums. Within each album, photos are previewed in a tile-like interface.
```

### Step 3: Refine the Spec

**In the chat**, use `/devspark.clarify` to identify and resolve ambiguities in your specification. You can provide specific focus areas as arguments.

```bash
/devspark.clarify Focus on security and performance requirements.
```

### Step 4: Create a Technical Implementation Plan

**In the chat**, use `/devspark.plan` to provide your tech stack and architecture choices.

```markdown
/devspark.plan The application uses Vite with minimal number of libraries. Use vanilla HTML, CSS, and JavaScript as much as possible. Images are not uploaded anywhere and metadata is stored in a local SQLite database.
```

### Step 5: Break Down and Implement

**In the chat**, use the `/devspark.tasks` slash command to create an actionable task list.

```markdown
/devspark.tasks
```

Optionally, validate the plan with `/devspark.analyze`:

```markdown
/devspark.analyze
```

For adversarial risk analysis, run `/devspark.critic` to identify potential failure modes:

```markdown
/devspark.critic
```

Then, use the `/devspark.implement` slash command to execute the plan.

```markdown
/devspark.implement
```

## Optional: Personalize Your Workflow

If you want to customize any command for your individual working style without affecting your team:

```markdown
/devspark.personalize plan          # Personalize how you write plans
/devspark.personalize plan          # Personalize your planning approach
/devspark.personalize implement     # Personalize implementation behavior
```

This creates a copy of the shared prompt in `.documentation/{your-git-user}/commands/` that takes priority when you run the command. Your team sees the same shared defaults; you get your version. Delete the file to revert.

---

## Upgrading DevSpark

For normal use, update DevSpark with the remote upgrade prompt in your AI agent chat:

```text
Follow the instructions at https://raw.githubusercontent.com/markhazleton/devspark/main/templates/commands/upgrade.md
```

That keeps stock DevSpark files current without requiring CLI installation. If you explicitly prefer terminal-driven automation, `devspark upgrade` remains available as an advanced option. See the [Upgrade Guide](upgrade.md) for details.

---

## Detailed Example: Building Taskify

Here's a complete example of building a team productivity platform:

### Step 1: Define Constitution

Initialize the project's constitution to set ground rules:

```markdown
/devspark.constitution Taskify is a "Security-First" application. All user inputs must be validated. We use a microservices architecture. Code must be fully documented.
```

### Step 2: Define Requirements with `/devspark.specify`

```text
Develop Taskify, a team productivity platform. It should allow users to create projects, add team members,
assign tasks, comment and move tasks between boards in Kanban style. In this initial phase for this feature,
let's call it "Create Taskify," let's have multiple users but the users will be declared ahead of time, predefined.
I want five users in two different categories, one product manager and four engineers. Let's create three
different sample projects. Let's have the standard Kanban columns for the status of each task, such as "To Do,"
"In Progress," "In Review," and "Done." There will be no login for this application as this is just the very
first testing thing to ensure that our basic features are set up.
```

### Step 3: Refine the Specification

Use the `/devspark.clarify` command to interactively resolve any ambiguities in your specification. You can also provide specific details you want to ensure are included.

```bash
/devspark.clarify I want to clarify the task card details. For each task in the UI for a task card, you should be able to change the current status of the task between the different columns in the Kanban work board. You should be able to leave an unlimited number of comments for a particular card. You should be able to, from that task card, assign one of the valid users.
```

You can continue to refine the spec with more details using `/devspark.clarify`:

```bash
/devspark.clarify When you first launch Taskify, it's going to give you a list of the five users to pick from. There will be no password required. When you click on a user, you go into the main view, which displays the list of projects. When you click on a project, you open the Kanban board for that project. You're going to see the columns. You'll be able to drag and drop cards back and forth between different columns. You will see any cards that are assigned to you, the currently logged in user, in a different color from all the other ones, so you can quickly see yours. You can edit any comments that you make, but you can't edit comments that other people made. You can delete any comments that you made, but you can't delete comments anybody else made.
```

### Step 4: Validate the Spec

Validate the specification checklist using the `/devspark.checklist` command:

```bash
/devspark.checklist
```

### Step 5: Generate Technical Plan with `/devspark.plan`

Be specific about your tech stack and technical requirements:

```bash
/devspark.plan We are going to generate this using .NET Aspire, using Postgres as the database. The frontend should use Blazor server with drag-and-drop task boards, real-time updates. There should be a REST API created with a projects API, tasks API, and a notifications API.
```

### Step 6: Validate and Implement

Have your AI agent audit the implementation plan using `/devspark.analyze`:

```bash
/devspark.analyze
```

Finally, implement the solution:

```bash
/devspark.implement
```

## Key Principles

- **Be explicit** about what you're building and why
- **Don't focus on tech stack** during specification phase
- **Iterate and refine** your specifications before implementation
- **Validate** the plan before coding begins
- **Let the AI agent handle** the implementation details
- **Review and audit** code regularly for constitution compliance

## Constitution-Powered Commands (No Spec Required)

These commands only need a constitution—no specs required. Use them on any codebase:

### PR Review

Review any GitHub Pull Request against your constitution:

```bash
/devspark.pr-review #123
```

### Site Audit

Perform comprehensive codebase audit:

```bash
/devspark.site-audit
```

### Critic (Spec Workflow Only)

Run adversarial risk analysis (requires spec.md, plan.md, and tasks.md):

```bash
/devspark.critic
```

## Next Steps

- Read the [complete methodology](https://github.com/MarkHazleton/devspark/blob/main/spec-driven.md) for in-depth guidance
- Check out [more examples](https://github.com/MarkHazleton/devspark/tree/main/templates) in the repository
- Explore the [source code on GitHub](https://github.com/MarkHazleton/devspark)
