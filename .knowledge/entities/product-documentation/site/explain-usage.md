# Explain Existing Functionality

`/devspark.explain` answers questions about how the repository works today. It
traces current code, checks relevant tests, matches the corresponding
`.knowledge` content, and reports whether those surfaces still agree.

## Usage

```text
/devspark.explain how is authentication done
/devspark.explain where are release eligibility checks enforced
/devspark.explain --dry-run how does tenant routing work
```

The input is a free-text topic or question. `--dry-run` keeps the run read-only,
shows any proposed knowledge repairs as previews, and does not ask for write
confirmation.

## What It Checks

The command runs the platform-specific `explain-context` helper to gather a
bounded set of lexical candidates. It then inspects the actual implementation
and uses those candidates only as leads.

For the requested topic it:

1. traces relevant code and configuration;
2. finds focused tests and runs the smallest practical selection;
3. matches semantically relevant entity and governance documents;
4. resolves cited evidence and repository links;
5. checks for contradiction, staleness, missing tests, broken links, and
   incomplete knowledge.

It uses the same `DELTA1`-`DELTA4` and `KNOW1`-`KNOW4` finding taxonomy as
`/devspark.site-audit`, but limits the investigation to the question instead of
auditing the whole repository.

## Output

Every run returns exactly three sections:

- `## Answer` — a human-readable explanation with `path:line` citations.
- `## Findings` — a DELTA/KNOW table, or one clean-result line when no issue is
  found.
- `## Agent Summary` — valid JSON that another agent or command can consume.

When no matching knowledge exists but the behavior is implemented, the command
reports `KNOW1` and drafts a source-grounded document proposal. It never fills
unknowns with assumed behavior.

## Write Safety

The initial run never writes. If a current-truth repair is appropriate, the
findings identify the exact files and proposed edits and ask for confirmation.
Only those confirmed knowledge or documentation edits may be applied. The
command never changes application code or tests.

The command also never creates specs, plans, tasks, or quickfix records. If the
question reveals genuinely missing behavior, it explains what exists now and
hands the requested addition to `/devspark.specify`.

## Lifecycle Position

Explain is an ad-hoc utility usable at any time. It is deliberately outside the
`specify → clarify when needed → plan → tasks → required gates → implement`
chain and does not archive work.
