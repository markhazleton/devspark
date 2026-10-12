# Constitution Guide

The project constitution defines your principles, standards, and governance rules. Every DevSpark skill that reviews, audits, or plans work reads it, and every finding cites the section it comes from. It lives at `.knowledge/governance/constitution.md`.

Participant metadata in specs, plans, or tasks is advisory context only. It never weakens the constitution, app-level governance, quality gates, or prompt and script resolution.

## Create it

```text
/devspark-constitution Security-first. TDD required, 80% coverage. All public APIs documented.
```

- **Greenfield:** you know the principles; use `/devspark-constitution` directly.
- **Brownfield:** the code already has implicit patterns. Run `/devspark-discover-constitution` (optionally with focus areas). It scans for patterns with confidence levels, asks 8 to 10 validating questions, and writes a temporary draft to `.devspark.work/governance/constitution-draft.md`. Review it, then finalize with `/devspark-constitution`.

To amend it later, use `/devspark-evolve-constitution`, which proposes changes from recurring PR review patterns.

## Structure

Named, numbered principles with requirement levels, plus a governance section:

```markdown
### II. Security First (MANDATORY)

- All user input MUST be validated
- SQL queries MUST use parameterized statements
- No hardcoded secrets or credentials

**Rationale**: Prevents injection and credential leaks.

## Governance

- The constitution supersedes other practices
- Amendments require documentation and approval
- All PRs MUST verify compliance

**Version**: 1.0.0 | **Ratified**: 2025-01-15 | **Last Amended**: 2025-01-15
```

| Term | Meaning | Severity when violated |
|---|---|---|
| MUST, MUST NOT | Non-negotiable | Critical |
| SHOULD, SHOULD NOT | Strongly recommended | High |
| MAY | Optional | Low or informational |

## Who reads it

| Skill | How it uses the constitution |
|---|---|
| `/devspark-plan`, `/devspark-planning-review` | Plans align with principles; violations surface as findings |
| `/devspark-implement` | Follows principles while generating code |
| `/devspark-pr-review`, `/devspark-site-audit` | Evaluate changes and the codebase against each principle (no spec required) |

## Write principles that can be checked

- **Be specific and measurable.** Not "write good code" but "functions MUST NOT exceed 50 lines".
- **Reserve MUST for the non-negotiable.** Overusing it dilutes it.
- **Keep it to 5 to 10 principles** that matter most, each with a rationale for edge cases.
- **Version it**, so past reviews can be tied to the version they used.

Principles verifiable from code work best in automated review:

| Works well | Harder to verify (flagged for human review) |
|---|---|
| "No hardcoded secrets or API keys" | "Code should be readable" |
| "Public functions MUST have doc comments" | "Use appropriate design patterns" |
| "SQL MUST be parameterized" | "Performance must be acceptable" |
| "Test files MUST exist for all source files" | "Follow team conventions" |

Name patterns, paths, thresholds, and prohibited constructs explicitly (for example, "MUST NOT use `eval()`" or "tests MUST be named `*.test.ts`").

## What belongs in it

Put it in the constitution if violating it would block a PR regardless of other merits and it applies project-wide. Everything else belongs elsewhere:

| Document | Holds | Example |
|---|---|---|
| Constitution | Non-negotiable principles | "All input MUST be validated" |
| `.knowledge/` | Current supported behavior and constraints | "Services validate requests with Zod" |
| `.knowledge/guides/` | Published how-to guidance | "Use `validateRequest()` from `/lib/validation.ts`" |
| `CONTRIBUTING.md` | How to contribute | Branch naming, commit format |

## Multiple applications

In a [multi-app repository](monorepo-guide.md#layered-governance), an app can add its own constitution at `{app-path}/.knowledge/governance/constitution.md`. App constitutions are additive: they can add or tighten rules but never weaken the repository-wide ones, and attempts to weaken them are detected. Most repositories only need the repo-wide constitution.

## Working with agent instruction files

Agent instruction files (`.github/copilot-instructions.md`, `CLAUDE.md`, `AGENTS.md`, Cursor and Windsurf rules, and so on) should reference the constitution rather than copy it. The constitution states what must be true; agent instruction files state how to work, such as preferred libraries and error formats. They provide context to the agent; they are not agents or invocable skills.

```markdown
## Foundational documents

Before generating or reviewing code, consult:

1. `.knowledge/governance/constitution.md`: non-negotiable principles; violations block PR review.
2. `.knowledge/`: current supported behavior and constraints.
3. `.knowledge/guides/`: published usage guidance.
```

If an agent instruction file conflicts with the constitution, the constitution wins. Fix the instruction file, or propose an amendment if the agent's guidance is better. Each agent's context file path is listed in `agents-registry.json`.

## Troubleshooting

| Symptom | Fix |
|---|---|
| "Constitution not found" | Run `/devspark-constitution` |
| Findings seem irrelevant | The principles are too vague; add measurable criteria |
| Too many violations | Start with fewer MUSTs; move guidelines that allow exceptions to SHOULD |
| Team disagrees with a finding | Update the constitution rather than ignoring the finding |

## Next steps

- [Review and Audit](review-and-audit.md): how the constitution drives reviews.
- [Planning Review](planning-review.md): how it constrains plans.
