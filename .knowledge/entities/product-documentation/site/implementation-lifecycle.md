# DevSpark Implementation Lifecycle

This guide defines the recommended DevSpark lifecycle for teams. For the
principles behind the mechanics, see the [DevSpark Philosophy](philosophy.md).

Primary approach: prompt-first workflows through your AI agent using remote
prompt files.

## Lifecycle at a Glance

At any point, run `/devspark.next` to detect the current branch, artifacts,
gates, and PR state and receive one recommended next command. Use
`/devspark.next --auto` to chain safe steps until a human-owned Git or merge
boundary is reached.

1. Bootstrap with the matching quickstart prompt.
2. Establish the repository constitution.
3. Run `specify → clarify when needed → plan → tasks → required gates → implement`.
4. Run focused verification when the change needs explicit behavioral proof.
5. Commit and synchronize the branch, then run `create-pr → pr-review ↔ address-pr-review → merge`.
6. Run `release` as a separate human-triggered event to revalidate and archive completed packages.
7. Re-run the matching quickstart prompt whenever installation, upgrade, or repair is needed.

## 1. Bootstrap (Primary)

Open your AI agent in the target repository and run the matching quickstart prompt:

- Copilot: `@workspace Follow the instructions at https://raw.githubusercontent.com/markhazleton/devspark/main/quickstart/devspark_quickstart_copilot.md`
- Claude Code: `Follow the instructions at https://raw.githubusercontent.com/markhazleton/devspark/main/quickstart/devspark_quickstart_claudecode.md`
- Cursor: `Follow the instructions at https://raw.githubusercontent.com/markhazleton/devspark/main/quickstart/devspark_quickstart_cursor.md`
- Other agents: `Follow the instructions at https://raw.githubusercontent.com/markhazleton/devspark/main/quickstart/devspark_quickstart_generic.md`

The quickstart prompt installs stock framework files into `.devspark/` and
preserves repository-owned current truth in `.knowledge/`.

This is the standard installation path for DevSpark and the only approved
maintenance path.

## 2. Implement Features

After bootstrap, run the standard implementation lifecycle in chat:

1. `/devspark.constitution`
2. `/devspark.specify` (route-aware intake: one-off fix, quick spec, or full spec)
3. `/devspark.clarify` (optional but recommended)
4. `/devspark.plan`
5. `/devspark.tasks`
6. Run the gates named by spec frontmatter: `/devspark.checklist`, `/devspark.analyze`, and `/devspark.critic` as required
7. `/devspark.implement`
8. `/devspark.verify` when focused behavioral or evidence proof is needed
9. Commit and synchronize the branch
10. `/devspark.create-pr`
11. `/devspark.pr-review`
12. `/devspark.address-pr-review` when findings are open
13. `/devspark.pr-review UPDATE`
14. Merge the PR after approval
15. `/devspark.release` at the selected release event, not automatically after merge

### Lifecycle Terminology

DevSpark uses distinct terms for workflow concepts:

- **Prompt**: the workflow command surface that owns lifecycle orchestration.
- **Agent**: an AI runtime or client integration that executes prompts.
- **Skill**: a portable capability package a prompt may delegate to.
- **Participant**: a human or AI-filled team member with responsibility in a
  workflow.
- **Role**: a responsibility label for a participant, such as owner, planner,
  implementer, reviewer, critic, or scribe.

Participant metadata is advisory and artifact-only. It can record responsibility
context in specs, plans, or tasks, but it does not affect command execution,
prompt resolution, script resolution, gate enforcement, or command output.
Customization layers and precedence are unchanged.

### Route-Aware Intake

`/devspark.specify` is the canonical starting point for new work. It classifies the request, explains the recommendation, and asks the user to confirm or override it.

- `one-off-fix` redirects to `/devspark.quickfix`
- `quick-spec` creates a lightweight spec with frontmatter metadata
- `full-spec` creates the full specification workflow

Downstream commands must read the spec frontmatter first and treat that metadata as authoritative.

### Ephemeral Work-Package Lifecycle

Specs, plans, tasks, and gates are temporary work-package files under
`.devspark.work/`. They remain there after implementation, verification, and PR
review. Release validates their code, test, knowledge, and governance linkage,
then moves eligible packages to `.archive/YYYY-MM-DD/<topic>/`.

```text
/devspark.specify     -->  Status: Draft
/devspark.clarify     -->  (no change, still Draft)
/devspark.plan        -->  (no change, still Draft)
/devspark.tasks       -->  (no change, still Draft)
/devspark.implement   -->  Status: In Progress (at start)
                      -->  Status: Complete   (when all tasks marked [X])
/devspark.create-pr   -->  Draft or update the PR using spec, task, and gate context
/devspark.pr-review   -->  Reviewer findings and disposition
/devspark.address-pr-review -->  Author applies fixes with commit-isolation gates
/devspark.pr-review UPDATE -->  Focused re-review against latest fix iteration
/devspark.verify      -->  Confirms evidence and task linkage; package remains live
/devspark.release     -->  Revalidates and archives eligible work packages
```

Quality gate outputs are written inside the in-flight work package:

- `gates/analyze.md` for cross-artifact consistency review
- `gates/critic.md` for adversarial technical risk review
- `gates/checklist.md` as the current checklist gate summary across checklist files

Downstream commands treat those gate files as temporary implementation state,
not durable repository knowledge.

Valid status values: `Draft`, `In Progress`, `Complete`. A complete package
remains in `.devspark.work/` until release.

**Key rules:**

- A work package cannot leave `.devspark.work/` before release, even after it
  passes verification.
- `/devspark.pr-review` flags missing code/knowledge linkage as a blocking
  current-truth issue.
- `/devspark.site-audit` flags stale `.devspark.work/` packages on main as
  anti-patterns.
- `/devspark.release` fails when completed work packages lack valid code, test,
  knowledge, or governance linkage and is the sole archive writer.

### Release Events and Sprint Reporting

The implementation loop repeats per feature. A release is a human-selected
business event, not an automatic sprint boundary:

```text
+--- Repeat per feature until ready to merge ----------+
|  /specify -> /clarify when needed -> /plan -> /tasks     |
|  -> required gates -> /implement -> focused /verify      |
|  -> commit/push -> /create-pr -> /pr-review               |
|  <-> /address-pr-review -> merge                          |
+--------------------------------------------------------+
                         |
               (human-selected release event)
                         |
                    /devspark.release
```

- **Per feature**: Run the route-defined lifecycle from specify through required gates and implement, gather focused verification evidence when needed, draft the PR with `/devspark.create-pr`, review it, and merge.
- **At the selected release event**: Run `/devspark.release` once to validate
  current truth, generate release notes, bump the version, and archive eligible
  completed packages.
- **Anytime**: Run `/devspark.site-audit` as a health check to catch lifecycle violations.
- **Blocked packages**: Release leaves incomplete or invalid packages in
  `.devspark.work/` and reports their blockers.

Sprint reporting is layered on top of this lifecycle. Query released dates and
Git history when a team needs a sprint view; DevSpark does not maintain sprint
state as another source of truth.

### When to Use Technical Details vs. Product Language

Each phase has a different audience and purpose. Mixing technical decisions into the wrong phase creates specs that lock you into solutions before you understand the problem, or plans that lack the detail needed to build anything.

#### Specify and Clarify: Product language only

These phases define **what** users need and **why**. Write as if explaining to a product manager. No frameworks, no databases, no APIs.

| Anti-pattern (too technical) | Better (product-focused) |
|------------------------------|--------------------------|
| `/devspark.specify Build a React app with Redux state management and a PostgreSQL backend for managing tasks` | `/devspark.specify Build a task manager where teams create projects, assign tasks to members, and track progress on a Kanban board` |
| `/devspark.specify Create a REST API with JWT auth that serves photo metadata from S3` | `/devspark.specify Build a photo album organizer. Albums grouped by date, drag-and-drop reordering, tile-based photo previews` |
| `/devspark.clarify Should we use WebSockets or SSE for the real-time updates?` | `/devspark.clarify When a team member moves a task, how quickly should other users see the change? Instant, or is a short delay acceptable?` |
| `/devspark.clarify Should the Redis cache TTL be 5 minutes or 15 minutes?` | `/devspark.clarify How fresh does the dashboard data need to be? Real-time, or is a few minutes of delay acceptable?` |

**Why this matters:** If you say "use React" in the spec, the AI treats it as a requirement and won't consider whether Svelte, Vue, or vanilla JS might be a better fit. The spec becomes a solution document instead of a problem document. Keep the spec technology-agnostic so the plan phase can make informed technical choices.

#### Plan: Technical details belong here

This phase translates product requirements into architecture and technology choices. Now is the time for frameworks, databases, protocols, and infrastructure decisions.

| Good plan input | Why it works |
|-----------------|--------------|
| `/devspark.plan Use Vite + vanilla JS, SQLite for local storage, no server needed` | Provides clear technology direction while the spec already defined what to build |
| `/devspark.plan .NET Aspire with Blazor Server frontend, Postgres database, REST APIs for projects/tasks/notifications` | Specific stack choices that the plan phase can evaluate against the spec's requirements |
| `/devspark.plan Existing Next.js app. Add this feature using the existing Prisma ORM and tRPC patterns` | Constrains the plan to work within an existing codebase's patterns |

#### Tasks and Implement: Implementation specifics

These phases work with concrete code. File paths, function signatures, migration scripts, test fixtures, and dependency versions all belong here.

#### Quick reference: What goes where

| Phase | Language | Example |
|-------|----------|---------|
| **Specify** | Product/user outcomes | "Users can drag tasks between columns" |
| **Clarify** | Requirements and constraints | "Is there a maximum number of team members per project?" |
| **Plan** | Architecture and technology | "Use Blazor Server with SignalR for real-time Kanban updates" |
| **Tasks** | Implementation details | "Create `TaskCard.razor` component with drag-and-drop via `SortableJS`" |

### Multi-App Workflows (Optional)

If your repository contains multiple applications, you can scope any command to a specific application:

- Use `--app <id>` with any command to target a specific application
- Use `--repo-scope` for repository-wide operations
- Run `/devspark.add-application` to register new applications in the multi-app registry

Multi-app support is entirely optional. Single-application repositories use the standard workflow above with no changes.

## 3. Upgrade and Repair

Re-run the same quickstart prompt in the target repository.

Recommended cadence:

1. Run dry-run first
2. Review proposed stock changes
3. Apply upgrade

Upgrade behavior:

- Updates stock framework files in `.devspark/`
- Preserves team and personal customizations in `.knowledge/`
- Preserves current-truth knowledge in `.knowledge/`
- Initializes missing `.knowledge/entities/` and `.knowledge/ontology/` scaffold files
- Classifies `.documentation/` intake into `.archive/`, `.devspark.work/`, or `.knowledge/`
- Warns when `.knowledge/overrides/commands/` overrides may hide structural changes in updated stock prompts

This is the standard update and repair path for DevSpark.

## 4. Version Stamping Rules

Quickstart flows must keep `.devspark/VERSION` authoritative.

- The `version:` value must be the latest DevSpark semantic version (`X.Y.Z`)
- Do not write `quickstart` as a version value
- If missing or invalid, treat installed version as unknown and refresh from latest

Do not use a separate DevSpark installer, updater, or repair command. Keep those
flows in quickstart prompts.
