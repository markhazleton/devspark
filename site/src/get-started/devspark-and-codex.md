# DevSpark and Codex

Codex is strongest when it has clear task context, durable repository guidance, and a verification loop. DevSpark supplies the lifecycle around it: reusable skills, temporary plans, verification, and release. Use this guide to combine Codex best practices with that lifecycle.

## What Each Tool Owns

| Layer | Codex owns | DevSpark owns |
|-------|------------|---------------|
| Reasoning and edits | Reads code, proposes changes, runs commands, applies patches | Gives Codex the workflow and acceptance criteria |
| Durable guidance | Loads `AGENTS.md` and scoped instructions | Keeps current truth under `.knowledge/` |
| Reusable workflow | Uses prompts, skills, plugins, and `codex exec` | Provides `/devspark-*` skills through Codex prompt shims and stock prompt resolution |
| Verification | Runs tests, lint, builds, and reviews | Defines when to run validation and where to record outcomes |
| Work context | Uses project files as context | Keeps temporary plans and gates under `.devspark.work/` |

The practical rule is simple: let Codex execute work, and let DevSpark shape the work into a reviewable lifecycle.

## Configure Codex for DevSpark

Start with the [Codex quickstart prompt](https://dev.makeboldspark.com/raw/quickstart/devspark_quickstart_codex.md). It installs:

- `.devspark/defaults/commands/` - stock prompt instructions for DevSpark skills
- `.codex/prompts/` - Codex prompt shims that expose `/devspark-*` skills as slash commands
- `.devspark.work/` - temporary plans, gates, retained work products, and team overrides
- `.knowledge/` - current authoritative project truth, plus published user-facing guidance under `.knowledge/guides/`
- `AGENTS.md` - repository guidance Codex can load automatically

Type the full hyphenated slash command shown in this guide, such as `/devspark-specify`. DevSpark 9.0 uses these names across agents; the retired dotted form has no aliases or fallback. See the [invocation-format note](../guides/prompt-lifecycle-mapping.md#invocation-format).

In this guide, **skill** names the DevSpark capability, **slash command** names its invocation,
**agent** means Codex, and **prompt** means instruction text. Codex prompt shims are the platform
entry points, not separate DevSpark capabilities. See [Terminology](../guides/prompt-lifecycle-mapping.md#terminology).

Keep `AGENTS.md` short and durable. It should tell Codex where DevSpark files live, how prompt resolution works, and which files are user-owned. Avoid putting long process manuals in `AGENTS.md`; link to DevSpark docs instead.

Recommended `AGENTS.md` guidance:

```markdown
# AGENTS.md

## DevSpark

- Framework files live in `.devspark/`.
- Temporary plans and overrides live in `.devspark.work/`.
- Current truth lives in `.knowledge/`; published guidance lives in `.knowledge/guides/`.
- Resolve the prompt instructions for DevSpark skills through the first existing file:
  1. `.devspark.work/{git-user}/commands/devspark.{name}.md`
  2. `.devspark.work/commands/devspark.{name}.md`
  3. `.devspark/defaults/commands/devspark.{name}.md`
- Preserve `.devspark.work/`, `.knowledge/`, and `.archive/`; upgrades refresh `.devspark/` only.
```

Codex discovers `AGENTS.md` from global and project scopes, then merges files from the repository root down to the current directory. More specific files override broader guidance, so nested `AGENTS.md` files are useful for monorepos with different service rules.

## Invoke DevSpark Skills in Codex

Codex prompts work best when they include goal, context, constraints, and done criteria. DevSpark skills force that shape by turning vague requests into explicit artifacts.

Use this pattern:

```text
/devspark-specify Add account lockout after five failed login attempts.
Done when the API returns a clear lockout response, audit events are recorded,
and existing successful-login behavior is unchanged.
```

Then continue:

```text
/devspark-plan Use the existing auth service and current test framework.
/devspark-tasks
/devspark-implement
```

For ambiguous work, ask Codex to plan before coding:

```text
/devspark-plan Read the current spec and plan files. Identify unknowns before implementation.
```

For narrow fixes, let `/devspark-specify` route the work. It can recommend one-off-fix, quick-spec, full-spec, refactor, or prompt-change and ask for confirmation before artifacts are created.

## Use The Right Reasoning Level

Codex supports different reasoning levels. Match the setting to the DevSpark stage:

| DevSpark stage | Codex setting | Why |
|----------------|---------------|-----|
| Small typo, copy, or isolated test fix | Low | Fast turnaround and low risk |
| Normal feature implementation | Medium or High | Enough reasoning for code and tests |
| Architecture, migration, or hard debugging | High or Extra High | Better for long-horizon work |
| Review and risk analysis | High | Finds cross-file regressions and missing tests |

Use lower effort for well-scoped tasks after `/devspark-tasks`. Use higher effort for `/devspark-plan`, `/devspark-critic`, `/devspark-pr-review`, and complex `/devspark-implement` runs.

## Keep Context Lean

DevSpark creates many artifacts. Give Codex the smallest set that can answer the current question.

Good context sets:

- For planning: `spec.md`, constitution, relevant app docs, and current architecture files
- For implementation: `tasks.md`, `plan.md`, target source files, and related tests
- For review: PR diff, constitution, current knowledge, affected tests, and actual command output
- For release: the Git range, current knowledge and docs, validation output, and changelog

Avoid pasting entire directories into one prompt. Ask Codex to read the relevant files itself, then summarize what it loaded before making changes.

## Run A Tight Validation Loop

The best DevSpark and Codex workflow is evidence-driven:

Run the route [How It Works](how-it-works.md) picks for the change. For a full spec:

1. `/devspark-specify`, `/devspark-plan`, `/devspark-tasks` define the outcome and approach.
2. `/devspark-planning-review` checks the plan before code is written.
3. `/devspark-implement` changes code, tests, and current knowledge, and leaves the linked planning
   bundle under `.devspark.work/`. `/devspark-release` later archives it.
4. `/devspark-verify` produces proof and closes out the work.
5. `/devspark-create-pr`, `/devspark-pr-review`, and `/devspark-address-pr-review` review the durable result.
6. `/devspark-release` verifies the Git delta and updates release notes.

Tell Codex exactly what verification is required before it stops:

```text
Run the focused tests for the files you changed. If they fail, fix the issue.
If a full suite is too expensive, explain what was run and what remains.
```

For frontend work, add visual verification. For API work, add contract or integration checks. For shared libraries, add both unit tests and at least one caller-facing check.

## Automate Stable Workflows

For repeatable terminal automation, use Codex non-interactive mode.

Codex non-interactive mode:

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

Native Codex skills package task-specific instructions, scripts, references, and assets. DevSpark
skills define reusable workflows; this integration exposes them through Codex prompt shims. Calling
a DevSpark capability a skill does not mean it is installed as a native Codex skill.

Create or install a skill when:

- A team repeats the same investigation or implementation workflow
- The workflow has stable reference material
- Scripts can gather context more reliably than a pasted prompt
- The instructions should be reused across repositories

Invoke DevSpark lifecycle skills with their `/devspark-*` slash commands. Additional native
Codex skills can provide specialist execution patterns, such as auditing an API surface or gathering
domain-specific context. A slash command is an invocation, not an alternative to a skill.

## Team Practices

Use these conventions for reliable Codex outcomes:

- Commit `AGENTS.md` with concise DevSpark rules.
- Commit `.codex/prompts/devspark-*.md` if your team uses Codex prompt discovery.
- Keep team overrides in `.devspark.work/commands/`.
- Keep personal overrides in `.devspark.work/{git-user}/commands/`.
- Do not commit Codex auth files, tokens, or machine-local configuration.
- Use `/devspark-personalize` for repeated prompt adjustments instead of editing stock prompts.

## Common Failure Modes

| Failure mode | Fix |
|--------------|-----|
| Codex starts coding before scope is clear | Use `/devspark-specify` first |
| Codex edits too many unrelated files | Add constraints and done criteria before `/devspark-implement` |
| Context gets too large | Point Codex to specific artifacts and ask it to summarize loaded context |
| Review feedback is mixed into feature commits | Use `/devspark-address-pr-review` for isolated fixes |
| Upgrade overwrites team work | Keep team work under `.devspark.work/`; DevSpark upgrades only refresh `.devspark/` |
| `/devspark-*` does not appear in Codex CLI | Restart Codex, or set session-scoped `CODEX_HOME` to `.codex` |

## Reference Links

- [Codex Quickstart](https://developers.openai.com/codex/quickstart)
- [Codex best practices](https://developers.openai.com/codex/learn/best-practices)
- [Custom instructions with AGENTS.md](https://developers.openai.com/codex/guides/agents-md)
- [Codex non-interactive mode](https://developers.openai.com/codex/noninteractive)
- [Codex skills](https://developers.openai.com/codex/skills)
- [DevSpark Quick Start](quickstart.md)
