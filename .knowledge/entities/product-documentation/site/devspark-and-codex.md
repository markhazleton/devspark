# DevSpark and Codex

Codex is strongest when it has clear task context, durable repository guidance, and a verification loop. DevSpark supplies that operating system: command prompts, specs, plans, tasks, gates, scripts, and release artifacts that keep Codex focused from idea through merge.

Use this guide when you want Codex to do more than answer a one-off coding question. It explains how to combine Codex best practices with the DevSpark lifecycle.

## What Each Tool Owns

| Layer | Codex owns | DevSpark owns |
|-------|------------|---------------|
| Reasoning and edits | Reads code, proposes changes, runs commands, applies patches | Gives Codex the workflow and acceptance criteria |
| Durable guidance | Loads `AGENTS.md` and scoped instructions | Writes and references constitution, specs, plans, tasks, and gates |
| Reusable workflow | Uses prompts, skills, plugins, and `codex exec` | Provides `/devspark.*` command shims and stock prompt resolution |
| Verification | Runs tests, lint, builds, and reviews | Defines when to run validation and where to record outcomes |
| Team memory | Uses project files as context | Preserves decisions and current truth under `.knowledge/` |

The practical rule is simple: let Codex execute work, and let DevSpark shape the work into a reviewable lifecycle.

## Configure Codex for DevSpark

Start with the [Codex quickstart prompt](../../../../quickstart/devspark_quickstart_codex.md). It installs:

- `.devspark/defaults/commands/` - stock DevSpark command prompts
- `.codex/prompts/` - Codex prompt shims for `/devspark.*`
- `.knowledge/` - project-owned current truth, governance, entities, and overrides
- `AGENTS.md` - repository guidance Codex can load automatically

Keep `AGENTS.md` short and durable. It should tell Codex where DevSpark files live, how prompt resolution works, and which files are user-owned. Avoid putting long process manuals in `AGENTS.md`; link to DevSpark docs instead.

Recommended `AGENTS.md` guidance:

```markdown
# AGENTS.md

## DevSpark

- Framework files live in `.devspark/`.
- Project documentation and team overrides live in `.knowledge/`.
- Current truth lives in `.knowledge/`.
- Resolve DevSpark commands through the first existing file:
  1. `.knowledge/overrides/{git-user}/commands/devspark.{name}.md`
  2. `.knowledge/overrides/commands/devspark.{name}.md`
  3. `.devspark/defaults/commands/devspark.{name}.md`
- Preserve `.knowledge/`; quickstart upgrades refresh `.devspark/`.
```

Codex discovers `AGENTS.md` from global and project scopes, then merges files from the repository root down to the current directory. More specific files override broader guidance, so nested `AGENTS.md` files are useful for monorepos with different service rules.

## Prompt Codex Through DevSpark

Codex prompts work best when they include goal, context, constraints, and done criteria. DevSpark commands force that shape by turning vague requests into explicit artifacts.

Use this pattern:

```text
/devspark.specify Add account lockout after five failed login attempts.
Done when the API returns a clear lockout response, audit events are recorded,
and existing successful-login behavior is unchanged.
```

Then continue:

```text
/devspark.plan Use the existing auth service and current test framework.
/devspark.tasks
/devspark.implement
```

For ambiguous work, ask Codex to plan before coding:

```text
/plan Read the current spec and plan files. Identify unknowns before implementation.
```

For narrow fixes, let `/devspark.specify` route the work. It can recommend a one-off fix, quick spec, or full spec and ask for confirmation before artifacts are created.

## Use The Right Reasoning Level

Codex supports different reasoning levels. Match the setting to the DevSpark stage:

| DevSpark stage | Codex setting | Why |
|----------------|---------------|-----|
| Small typo, copy, or isolated test fix | Low | Fast turnaround and low risk |
| Normal feature implementation | Medium or High | Enough reasoning for code and tests |
| Architecture, migration, or hard debugging | High or Extra High | Better for long-horizon work |
| Review and risk analysis | High | Finds cross-file regressions and missing tests |

Use lower effort for well-scoped tasks after `/devspark.tasks`. Use higher effort for `/devspark.plan`, `/devspark.critic`, `/devspark.pr-review`, and complex `/devspark.implement` runs.

## Keep Context Lean

DevSpark creates many artifacts. Give Codex the smallest set that can answer the current question.

Good context sets:

- For planning: `spec.md`, constitution, relevant app docs, and current architecture files
- For implementation: `tasks.md`, `plan.md`, target source files, and related tests
- For review: PR diff, constitution, spec status, completed tasks, and test output
- For release: completed specs, merged PRs, changelog, and prior release notes

Avoid pasting entire directories into one prompt. Ask Codex to read the relevant files itself, then summarize what it loaded before making changes.

## Run A Tight Validation Loop

The best DevSpark and Codex workflow is evidence-driven:

1. `/devspark.specify` defines the outcome.
2. `/devspark.plan` decides the approach.
3. `/devspark.tasks` creates executable work.
4. `/devspark.implement` changes code and runs focused tests.
5. `/devspark.pr-review` checks the result against the constitution and spec.
6. `/devspark.address-pr-review` fixes review findings in isolation.
7. `/devspark.release` archives completed work and updates release notes.

Tell Codex exactly what verification is required before it stops:

```text
Run the focused tests for the files you changed. If they fail, fix the issue.
If a full suite is too expensive, explain what was run and what remains.
```

For frontend work, add visual verification. For API work, add contract or integration checks. For shared libraries, add both unit tests and at least one caller-facing check.

## Automate Stable Codex Workflows

For repeatable terminal automation, use Codex non-interactive mode with explicit
prompts.

```bash
cat prompt.txt | codex exec --sandbox workspace-write -
```

Use non-interactive automation for narrow, stable workflows. Keep prompts explicit: state the goal, files to inspect, allowed changes, validation command, and stopping condition.

Avoid broad prompts such as "improve the project" in automation. Prefer:

```text
Read the failing test output, identify the smallest code change needed,
implement only that change, run the same test command again, and stop.
```

## Use Skills When A Workflow Repeats

Codex skills package task-specific instructions, scripts, references, and assets. DevSpark already uses a command-to-skill model for portable capability instructions.

Create or install a skill when:

- A team repeats the same investigation or implementation workflow
- The workflow has stable reference material
- Scripts can gather context more reliably than a pasted prompt
- The instructions should be reused across repositories

Keep slash commands for DevSpark lifecycle orchestration. Use skills for specialist execution patterns, such as writing a spec, auditing an API surface, or gathering domain-specific context.

## Team Practices

Use these conventions for reliable Codex outcomes:

- Commit `AGENTS.md` with concise DevSpark rules.
- Commit `.codex/prompts/devspark.*.md` if your team uses Codex prompt discovery.
- Keep team overrides in `.knowledge/overrides/commands/`.
- Keep personal overrides in `.knowledge/overrides/{git-user}/commands/`.
- Do not commit Codex auth files, tokens, or machine-local configuration.
- Use `/devspark.personalize` for repeated prompt adjustments instead of editing stock prompts.
- Run `/devspark.harvest` after large efforts to preserve useful findings and reduce stale context.

## Common Failure Modes

| Failure mode | Fix |
|--------------|-----|
| Codex starts coding before scope is clear | Use `/plan` or `/devspark.specify` first |
| Codex edits too many unrelated files | Add constraints and done criteria before `/devspark.implement` |
| Context gets too large | Point Codex to specific artifacts and ask it to summarize loaded context |
| Review feedback is mixed into feature commits | Use `/devspark.address-pr-review` for isolated fixes |
| Upgrade overwrites team work | Keep team work under `.knowledge/`; quickstart upgrades refresh framework-owned files |
| `/devspark.*` does not appear in Codex CLI | Restart Codex, or set session-scoped `CODEX_HOME` to `.codex` |

## Reference Links

- [Codex Quickstart](https://developers.openai.com/codex/quickstart)
- [Codex best practices](https://developers.openai.com/codex/learn/best-practices)
- [Custom instructions with AGENTS.md](https://developers.openai.com/codex/guides/agents-md)
- [Codex non-interactive mode](https://developers.openai.com/codex/noninteractive)
- [Codex skills](https://developers.openai.com/codex/skills)
- [DevSpark Quick Start](quickstart.md)
