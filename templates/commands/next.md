---
description: Detect the current DevSpark workflow state and recommend one next command without running it
scripts:
  sh: .devspark/scripts/bash/next-context.sh $ARGUMENTS --json
  ps: .devspark/scripts/powershell/next-context.ps1 $ARGUMENTS -Json
---

## User Input

```text
$ARGUMENTS
```

## Purpose

`/devspark.next` is an ad-hoc workflow navigator. It removes the need to
remember the lifecycle order by detecting repository state and returning one
plain-English recommendation. It may be used at any point and does not create a
parallel lifecycle or its own work record.

`/devspark.next` recommends; it never runs, dispatches, or chains another
command. The context script gathers facts and reduces them to a suggested next
step; the human decides whether to run it. A navigator that executed commands
based on framework state would be a harness in a script's clothes, which
DevSpark deliberately does not have.

The canonical full-spec sequence it recognizes is:

```text
constitution -> specify -> plan -> tasks -> required checklist/analyze/critic
-> implement -> commit/push -> create-pr -> pr-review -> address findings
-> merge
```

Release is deliberately not auto-appended after merge. A release is a separate,
human-triggered event and remains the only command that sweeps
`.devspark.work/` into `.archive/`.

## Safety Contract

- The context script is deterministic and read-only. Use its state fields as
  the source of truth; do not guess based on chat history.
- Never execute, dispatch, or chain the recommended command, and never ask
  permission to run it. Present it and stop.
- Never perform branch creation, commits, pushes, pulls, rebases, branch sync,
  merges, releases, or any other action; show the exact command for the human.
- Stop on failed/blocking gates. Show the gate path and exact `MANUAL_COMMAND`.
- Do not read `.archive/`. Current workflow state lives in Git,
  `.devspark.work`, and the platform PR service.

## Procedure

### 1. Gather State

> **Script Resolution**: Before running `{SCRIPT}`, apply the 2-tier override
> check. A matching file under
> `.knowledge/overrides/scripts/{bash|powershell}/` takes priority over the
> stock file under `.devspark/scripts/`.

Run `{SCRIPT}` once from the repository root and parse its JSON. At minimum use:

- `REPO_ROOT`, `BRANCH`, `PLATFORM`, `GIT_DIRTY`, `UPSTREAM`, `AHEAD`, `BEHIND`
- `WORK_KIND`, `FEATURE_DIR`, `HAS_SPEC`, `HAS_PLAN`, `HAS_TASKS`, `SPEC_STATUS`
- `TASKS`, `GATES`, `PR`, and `REVIEW`
- `ORIENTATION_STATE`, `RECOMMENDED_COMMAND`, `RECOMMENDATION_REASON`
- `ACTION_KIND`, `HUMAN_BOUNDARY`, and `MANUAL_COMMAND`

The script may query the detected platform CLI for PR state, but it never
creates, changes, synchronizes, or merges anything.

### 2. Present One Recommendation

Print a compact orientation block—never dump the raw JSON:

```text
Repository: <repo name or path>
Branch: <branch>
Platform: <platform>
State: <plain-English ORIENTATION_STATE>
Recommended: <RECOMMENDED_COMMAND>
Reason: <RECOMMENDATION_REASON>
```

Include a single short warning when the tree is dirty, the branch is ahead or
behind, a gate is blocking, or platform state could not be verified.

If `ACTION_KIND` is `complete`, report completion and stop. Do not ask a
confirmation and do not recommend new work merely to keep the chain moving.

If `ACTION_KIND` is `manual`, print:

```text
Human boundary: <HUMAN_BOUNDARY>
Run: <MANUAL_COMMAND>
```

Then stop. Do not execute it and do not ask permission to execute it.

### 3. Hand Off to the Human

When `ACTION_KIND` is `devspark`, print:

```text
Next: <RECOMMENDED_COMMAND>
```

Then stop. The human runs the command when ready; rerun `/devspark.next`
afterwards for a fresh recommendation. Never predict the following step from a
hard-coded list without checking the repository again.

## Recommendation Semantics

- `/devspark.constitution` and `/devspark.specify` require human participation
  and are recommended with their human boundary.
- `/devspark.address-pr-review` is a commit boundary.
- Git commands and platform merge commands are instructions for the human, not
  actions `/devspark.next` may perform.
- Release is recommended only when the human asks about releasing; it is never
  appended after merge.

Do not substitute a different command because it seems more useful. If the
detected recommendation looks wrong given the facts, explain the conflicting
evidence and say which command the facts support instead; judgment stays with
this prompt and the human, not the script.
