---
description: Explain existing functionality from code and verify the matching current-truth knowledge
handoffs:
  - label: Specify Missing Behavior
    agent: devspark.specify
    prompt: Turn the missing behavior identified by explain into a new specification
scripts:
  sh: .devspark/scripts/bash/explain-context.sh $ARGUMENTS --json
  ps: .devspark/scripts/powershell/explain-context.ps1 $ARGUMENTS -Json
---

## User Input

```text
$ARGUMENTS
```

The input is a free-text question or topic about existing functionality, for
example `how is authentication done`. The optional `--dry-run` flag guarantees
read-only execution and suppresses every confirmation prompt.

## Purpose and Lifecycle Position

`/devspark.explain` is an ad-hoc, read-mostly current-truth utility. It may run
at any time and is not part of the `specify -> plan -> tasks -> implement` gate chain.

- **Owns**: a code-grounded explanation, topic-scoped knowledge matching,
  evidence verification, DELTA/KNOW findings, and proposed knowledge repairs.
- **Does not own**: planning, implementing, changing application behavior, or
  creating spec, plan, task, quickfix, release, or archive records.
- If the requested behavior is genuinely absent, explain what exists today and
  hand the missing-behavior request to `/devspark.specify`. Do not design the
  missing feature inside this command.

## Non-Negotiable Rules

- Treat current code, tests, configuration, `.knowledge/entities`, and
  `.knowledge/governance` as the evidence surface.
- Never read, list, enumerate, or glob `.archive/` or `.devspark.work/`.
- Never infer implementation from a filename, knowledge claim, or common
  pattern alone. Trace the actual code path before explaining it.
- Every material statement in `## Answer` must cite repository evidence as
  `path:line` (or `path::symbol` plus a line citation when available).
- Existing knowledge is a claim to verify, not authority over contradictory
  code. Report disagreement; do not silently choose language that hides it.
- If no knowledge matches, draft proposed knowledge only from cited code and
  test evidence. Never fill gaps with plausible-sounding claims.
- Do not modify any file until the user explicitly confirms the exact proposed
  changes. Confirmation from an earlier, different run does not carry forward.
- With `--dry-run`, make no writes, do not ask for confirmation, and mark every
  proposal as preview-only.

## Procedure

### 1. Parse and Validate the Question

Remove command flags from the topic. If no meaningful topic remains, stop and
ask for one concise question. Detect `--dry-run` before doing any analysis.

### 2. Gather Topic Context

> **Script Resolution**: Before running `{SCRIPT}`, apply the 2-tier override
> check. A matching file under
> `.knowledge/overrides/scripts/{bash|powershell}/` takes priority over the
> stock file under `.devspark/scripts/`.

Run `{SCRIPT}` and parse its JSON. Use its normalized terms and bounded
`knowledge_matches`, `code_matches`, and `test_matches` as discovery leads, not
as proof. The script is deterministic and read-only.

If the script fails, report the command and error inside `## Findings`. Do not
replace missing evidence with an uncited answer.

### 3. Resolve the Actual Implementation

Starting from the strongest code candidates:

1. Locate the public entry point, caller, handler, configuration, or interface
   relevant to the question.
2. Trace only the code paths necessary to answer the topic. Follow imports and
   callees when they materially change the behavior.
3. Locate focused tests that exercise those paths. Run the smallest practical
   test selection when execution is safe and available; distinguish passing,
   failing, not run, and absent evidence.
4. Capture precise citations. A search hit is not evidence until its surrounding
   code has been inspected.

Keep the investigation topic-scoped: at most 8 code/config reads, 6 knowledge
reads, and 4 test reads unless the user explicitly requests a deeper pass.

### 4. Match and Verify Current Knowledge

Inspect semantically relevant matches under `.knowledge/entities/` and
`.knowledge/governance/`; lexical matches from the script may be rejected.
Follow only directly cited or graph-adjacent current-truth objects needed for
this topic.

For each matched object:

- compare every relevant behavioral claim with the traced code;
- resolve each cited code/test/document reference;
- run cited execution evidence when practical;
- check that important observed behavior, boundaries, failure modes, and
  configuration are covered;
- validate relative Markdown links and repository-path references;
- identify unsupported or mutually inconsistent current-truth claims.

Use the shared `/devspark.site-audit` current-truth finding codes exactly:

| Code | Meaning |
|---|---|
| `DELTA1` | A documented current-truth claim contradicts current code, runtime configuration, or verified behavior. |
| `DELTA2` | A cited code, test, configuration, or document evidence target is stale, missing, or unresolvable. |
| `DELTA3` | A material documented behavior lacks adequate test evidence, or its focused test fails. |
| `DELTA4` | A knowledge link or current-truth cross-reference is broken. |
| `KNOW1` | Existing implemented behavior has no matching current-truth knowledge. |
| `KNOW2` | Matching knowledge exists but is materially incomplete for the observed behavior or boundary. |
| `KNOW3` | A knowledge claim is unsupported, or code-only evidence lacks the required test-attempt/fallback context. |
| `KNOW4` | Current-truth objects for the topic are ambiguous, duplicated, or mutually inconsistent. |

Do not emit a finding merely because wording differs. Every finding must name
the specific claim, the conflicting or missing evidence, and a bounded proposed
repair. Report a clean result only when relevant references resolve and focused
tests pass, or when the absence of test evidence is explicitly justified by the
knowledge evidence contract; otherwise use a finding or an inconclusive status.

### 5. Handle Missing Knowledge or Behavior

- **No knowledge match, implementation exists**: emit `KNOW1` and include a
  proposed new or updated knowledge document grounded only in cited code/tests.
- **Knowledge exists but is stale/incomplete**: propose the smallest in-place
  correction. Do not create historical or superseding copies.
- **Requested behavior does not exist**: say so plainly, cite the nearest
  relevant current behavior, and set the handoff to `/devspark.specify`. Do not
  create a spec or quickfix record.
- **Evidence is inconclusive**: state what could and could not be established;
  do not fabricate a complete answer.

### 6. Confirmation and Writes

The initial run is always read-only. When a knowledge or documentation repair
is warranted, list the exact target files and intended edits in `## Findings`,
including generated ontology paths when metadata would change, then ask this
exact question there: `No files were changed. Apply the proposed knowledge
changes above?` Do not write while awaiting the answer.

After explicit confirmation, apply only those proposed knowledge/documentation
edits, refresh generated ontology artifacts when metadata changed, re-check the
affected evidence and links, and return the same three-section output contract.
This command never changes application code or tests.

When `--dry-run` is present, show preview proposals but omit the confirmation
question and keep `confirmation_required` false.

## Required Output Contract

Return exactly these three level-two sections, in this order, on every completed
run. Do not add another level-two section.

### `## Answer`

Give a concise, human-readable answer grounded in the implementation. Cite every
material claim using repository-relative `path:line` references. Clearly label
anything not established by evidence.

### `## Findings`

When findings exist, use:

| ID | Severity | Knowledge | Code/Test Evidence | Finding | Proposed Action |
|---|---|---|---|---|---|

Use stable topic-local IDs such as `DELTA1-01` and `KNOW2-01`. Follow the table
with either the exact confirmation question (normal mode) or a note that the
preview is dry-run only. When clean, collapse this section to exactly one line:

```text
No DELTA/KNOW findings for this topic.
```

### `## Agent Summary`

Return one fenced `json` object with this minimum shape:

```json
{
  "topic": "string",
  "status": "clean|findings|inconclusive|missing-behavior|updated",
  "answer_refs": ["path:line"],
  "knowledge_matches": ["path"],
  "findings": [
    {"id": "KNOW1-01", "severity": "MEDIUM", "path": null}
  ],
  "proposals": [
    {"path": "path", "action": "create|update", "summary": "string"}
  ],
  "dry_run": false,
  "writes_performed": false,
  "confirmation_required": true,
  "handoff": null
}
```

Use `"handoff": "/devspark.specify"` only for genuinely missing behavior.
Set `confirmation_required` to true only when an unapplied write proposal is
awaiting confirmation in normal mode; it is false for clean, dry-run,
inconclusive, missing-behavior, and completed-update results.
The JSON must agree with the prose and remain valid for downstream chaining.
