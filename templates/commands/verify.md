---
description: Verify implemented work against behavioral intent, evidence, and Genuine Fix Discipline.
scripts:
  sh: .devspark/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: .devspark/scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## DevSpark v4 Override

This command is the execution-evidence engine for v4 current truth. When any
later section conflicts with this section, the v4 section wins.

- Run each cited `verified_by: execution` test directly with the repository's
  native test command, and record the passing proof as a `test_ref` pointer
  that `/devspark.implement` consumes for `verified_by: execution` evidence.
- Validate current truth after evidence runs by checking `.knowledge` entity
  metadata, decision evidence, the `constrains` / `constrained_by` pair, and the
  absence of permanent references to ephemeral work packages.
- Run the knowledge engine with `--check`: `python
  .devspark/scripts/build_knowledge_index.py --check`, falling back to `python
  scripts/build_knowledge_index.py --check` only when the framework copy is
  absent. When pinned claims are in use, also run `--detect-drift --base
  <target-branch>` and report drifted claims.
- Report code-only evidence missing `fallback_reason` as a warning; report
  missing evidence as a failure.
- Treat inspection evidence as skipped execution, not as a pass.
- Verification proves behavior and current-truth linkage, but never archives a
  work package. A successful result leaves the package in `.devspark.work/` for
  `/devspark.release`, which revalidates it before archival.
- This command never archives a work package and never writes to `.archive/`.

## Overview

Verify that implemented work satisfies the relevant spec, tasks, gates, and
behavioral intent. This command is stricter than "tests ran": it evaluates
whether the submitted proof demonstrates the intended behavior changed or was
preserved.

## Genuine Fix Discipline

Apply `templates/command-preamble-contract.md` §9 before accepting any proof.
Metrics are supporting evidence only; the behavior named by the finding or task
must be proven first.

### Genuine Fix Guard

Fail verification when a proof is metric-only with unchanged behavior:

- The proof only shows a metric decreasing or improving.
- The proof states or demonstrates unchanged behavior.
- No behavioral evidence supports the intended repair.

When the guard fails, emit `status: fail` and require a behavioral proof such as
a targeted regression test, reproduction before/after, fixture, contract check,
manual verification note, or runtime signal tied to the intent.

## Outline

1. Run `{SCRIPT}` from repo root and parse `FEATURE_DIR`, `SPEC_FILE`, and
   available documents.
2. Load `spec.md`, `tasks.md`, gate artifacts, and any `knowledge/` documents if
   present. Missing knowledge documents do not block verification.
3. Run the ontology generator in `--check` mode and treat stale generated
   ontology files as a verification failure when `.knowledge/` exists.
4. Extract open findings, task IDs, requirement IDs, and intent cues from the
   available artifacts.
5. Compare the user-provided proof and local evidence against each relevant
   intent.
6. Produce a concise verdict:

```yaml
verification:
  status: pass | fail | conditional
  checked:
    - requirement_id: <FR-### or empty>
      task_id: <T### or empty>
      finding_id: <stable finding id or empty>
      intent: <behavioral intent checked>
      evidence: <test, fixture, reproduction, audit, or manual proof>
      result: pass | fail | conditional
      notes: <why the evidence is or is not sufficient>
```

## Output Rules

- If every checked item has behavioral evidence, report `status: pass`.
- If evidence is partial but behavior is plausibly repaired, report
  `status: conditional` and list missing proof.
- If any item relies only on metric movement with unchanged behavior, report
  `status: fail`.
- Do not mark a task complete from this command; `/devspark.implement` owns task
  state.
