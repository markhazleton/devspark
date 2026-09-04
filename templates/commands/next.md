---
description: Detect the current DevSpark workflow state and recommend or safely dispatch the next command
scripts:
  sh: .devspark/scripts/bash/next-context.sh $ARGUMENTS --json
  ps: .devspark/scripts/powershell/next-context.ps1 $ARGUMENTS -Json
---

## User Input

```text
$ARGUMENTS
```

Supported mode: `--auto` chains safe DevSpark steps after one initial
confirmation, stopping as soon as a human-owned boundary is detected.

## Purpose

`/devspark.next` is an ad-hoc workflow navigator. It removes the need to
remember the lifecycle order by detecting repository state and returning one
plain-English recommendation. It may be used at any point and does not create a
parallel lifecycle or its own work record.

The canonical full-spec sequence it recognizes is:

```text
constitution -> specify -> plan -> tasks -> required checklist/analyze/critic
-> implement -> commit/push -> create-pr -> pr-review -> address findings
-> merge
```

Release is deliberately not auto-appended after merge. A release is a separate,
human-triggered event and remains the only archive writer.

## Safety Contract

- The context script is deterministic and read-only. Use its state fields as
  the source of truth; do not guess based on chat history.
- Before dispatching any command in normal mode, ask exactly one yes/no
  confirmation. A non-affirmative answer means stop without changes.
- In `--auto`, ask exactly one yes/no confirmation before starting the chain.
  That approval covers only commands whose latest context sets
  `SAFE_TO_AUTO: true`. Do not ask again for each safe step.
- Never automate branch creation, commits, pushes, pulls, rebases, branch sync,
  review-fix flows that may commit, merges, releases, or any other action whose
  context sets `ACTION_KIND: manual`—even with `--auto`.
- Opening or updating a draft PR through `/devspark.create-pr --auto` is allowed
  after commits are synchronized; its own prompt enforces the draft behavior.
- Stop on failed/blocking gates. Show the gate path and exact `MANUAL_COMMAND`;
  do not loop by rerunning a failed gate without repairs.
- Do not read `.archive/`. Current workflow state lives in Git,
  `.devspark.work`, and the platform PR service.
- Never dispatch `/devspark.next` from itself.

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
- `ACTION_KIND`, `SAFE_TO_AUTO`, `HUMAN_BOUNDARY`, and `MANUAL_COMMAND`

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

### 3. Normal Dispatch

When `ACTION_KIND` is `devspark` and `--auto` is absent, ask:

```text
Run <RECOMMENDED_COMMAND> now? (yes/no)
```

On explicit yes:

1. Resolve the recommended command through the standard personal -> team ->
   stock prompt chain.
2. Read and execute that command body in the current conversation.
3. Do not append `--auto` unless the user supplied it to `/devspark.next`.
4. When the dispatched command finishes, report its normal result and stop.

On no or ambiguous input, stop without dispatching.

### 4. Auto Dispatch Loop

When `--auto` is present and the first recommendation is safe, ask once:

```text
Start automatic progression with <RECOMMENDED_COMMAND>? (yes/no)
```

After explicit yes:

1. Resolve and execute `RECOMMENDED_COMMAND` with `--auto` forwarded.
2. When it completes, rerun `{SCRIPT}` with `--auto --json`.
3. Print one progress line: `<completed command> -> <new recommendation>`.
4. Continue only when `ACTION_KIND` is `devspark` and `SAFE_TO_AUTO` is true.
5. Stop and print the orientation block when the state is complete, manual, a
   command fails, a gate blocks, or a command asks for human judgment.

Convergence guards are mandatory:

- Maximum 10 dispatched commands in one auto run.
- Stop if the same `ORIENTATION_STATE` and `RECOMMENDED_COMMAND` pair appears
  twice consecutively; explain that state did not advance.
- Stop if a dispatched command returns incomplete, blocked, or failed.
- Re-run detection after every command. Never predict the following step from a
  hard-coded list without checking the repository again.

If the first recommendation is unsafe, do not ask to start auto mode. Show the
human boundary and exact command immediately.

## Recommendation Semantics

- `/devspark.constitution` and `/devspark.specify` require human participation;
  they may be confirmed in normal mode but are never auto-dispatched.
- `/devspark.plan`, `/devspark.tasks`, `/devspark.checklist`,
  `/devspark.analyze`, `/devspark.critic`, `/devspark.implement`,
  `/devspark.create-pr`, and `/devspark.pr-review` may auto-dispatch only when
  the latest script result explicitly marks them safe.
- `/devspark.address-pr-review` is a commit boundary and is never
  auto-dispatched.
- Git commands and platform merge commands are instructions for the human, not
  actions `/devspark.next` may perform.

Do not substitute a different command because it seems more useful. If the
detected recommendation looks wrong, report the conflicting evidence and stop
rather than overriding the script silently.
