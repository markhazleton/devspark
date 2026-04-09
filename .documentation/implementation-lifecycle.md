# DevSpark Implementation Lifecycle

This guide defines the recommended DevSpark lifecycle for teams.

Primary approach: prompt-first workflows through your AI agent using remote prompt files.
Advanced option: CLI automation when you explicitly want terminal-driven operations.

## Lifecycle at a Glance

1. Bootstrap with quickstart prompt (no CLI)
2. Run the implementation workflow (`/devspark.constitution` -> `/devspark.specify` -> `/devspark.plan` -> `/devspark.tasks` -> `/devspark.implement`)
3. Maintain with the remote upgrade prompt (no CLI)
4. Use CLI only for advanced automation

## 1. Bootstrap (Primary)

Open your AI agent in the target repository and run the matching quickstart prompt:

- Copilot: `@workspace Follow the instructions at https://raw.githubusercontent.com/markhazleton/devspark/main/quickstart/devspark_quickstart_copilot.md`
- Claude Code: `Follow the instructions at https://raw.githubusercontent.com/markhazleton/devspark/main/quickstart/devspark_quickstart_claudecode.md`
- Cursor: `Follow the instructions at https://raw.githubusercontent.com/markhazleton/devspark/main/quickstart/devspark_quickstart_cursor.md`
- Other agents: `Follow the instructions at https://raw.githubusercontent.com/markhazleton/devspark/main/quickstart/devspark_quickstart_generic.md`

The quickstart prompt installs stock framework files into `.devspark/` and preserves project work in `.documentation/`.

This is the standard installation path for DevSpark.

## 2. Implement Features

After bootstrap, run the standard implementation lifecycle in chat:

1. `/devspark.constitution`
2. `/devspark.specify`
3. `/devspark.clarify` (optional but recommended)
4. `/devspark.plan`
5. `/devspark.tasks`
6. `/devspark.analyze` and `/devspark.critic` (optional quality gates)
7. `/devspark.implement`
8. Create PR and run `/devspark.pr-review`
9. Merge PR after approval

### Spec Status Lifecycle

Every spec has a `**Status**:` field that tracks where it is in the lifecycle. Status transitions are enforced automatically by the commands:

```text
/devspark.specify     -->  Status: Draft
/devspark.clarify     -->  (no change, still Draft)
/devspark.plan        -->  (no change, still Draft)
/devspark.tasks       -->  (no change, still Draft)
/devspark.implement   -->  Status: In Progress (at start)
                      -->  Status: Complete   (when all tasks marked [X])
/devspark.pr-review   -->  Blocks APPROVE unless Complete + all tasks done
/devspark.release     -->  Archives only Complete specs
```

Valid status values: `Draft`, `In Progress`, `Complete`.

**Key rules:**

- A spec must reach `Complete` before its PR can be approved
- `/devspark.pr-review` will flag incomplete specs as CRITICAL findings
- `/devspark.site-audit` flags Draft or In Progress specs on main as anti-patterns
- `/devspark.release` will not archive specs that are not Complete

### Sprint Cadence

A typical sprint follows this pattern:

```text
+--- Repeat per feature (N times during sprint) ------+
|  /specify -> /clarify -> /plan -> /tasks -> /implement |
|  -> git push -> gh pr create -> /pr-review -> merge    |
+--------------------------------------------------------+
                         |
                    (end of sprint)
                         |
                    /devspark.release
```

- **Per feature**: Run the full lifecycle from specify through implement, create a PR, review it, and merge.
- **End of sprint**: Run `/devspark.release` once to archive all completed specs, generate release notes, and bump the version.
- **Anytime**: Run `/devspark.site-audit` as a health check to catch lifecycle violations.
- **Periodically**: Run `/devspark.harvest` to clean up stale documentation and ensure completed specs are captured in CHANGELOG.

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

## 3. Upgrade (Primary)

Use the remote upgrade prompt in chat (no CLI required):

- `https://raw.githubusercontent.com/markhazleton/devspark/main/templates/commands/upgrade.md`

Recommended cadence:

1. Run dry-run first
2. Review proposed stock changes
3. Apply upgrade

Upgrade behavior:

- Updates stock framework files in `.devspark/`
- Preserves team and personal customizations in `.documentation/`

This is the standard update path for DevSpark.

## 4. Version Stamping Rules

Quickstart and upgrade flows must keep `.devspark/VERSION` authoritative.

- The `version:` value must be the latest DevSpark semantic version (`X.Y.Z`)
- Do not write `quickstart` as a version value
- If missing or invalid, treat installed version as unknown and refresh from latest

## 5. CLI (Advanced Only)

Use CLI if you need terminal-driven automation, scripting, or CI-like control.

- Install/update CLI: `uv tool install devspark-cli --force --from git+https://github.com/markhazleton/devspark.git`
- Upgrade project via CLI: `devspark upgrade`

If your team does not need CLI automation, stay with prompt-first quickstart and prompt-first upgrade.
