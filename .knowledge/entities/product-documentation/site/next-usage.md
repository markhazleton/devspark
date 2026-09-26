# Next Command Navigator

`/devspark.next` detects where the current repository and branch are in the
DevSpark lifecycle and recommends one next action with one reason.

## When to Use It

Use Next when:

- returning to work after a break;
- finishing a lifecycle step without remembering what follows;
- switching among repositories or branches;
- checking whether plan, tasks, gates, implementation, PR, or review work is
  still outstanding.

## Basic Usage

```text
/devspark.next
```

The command reports a compact orientation:

```text
Repository: example-service
Branch: 014-refresh-tokens
Platform: github
State: analyze-required
Recommended: /devspark.analyze
Reason: Tasks exist, but the required cross-artifact analysis gate has not run.
```

Next only recommends. It never runs, dispatches, or chains the recommended
command; you run it when ready and rerun Next for a fresh recommendation. The
underlying detection script is read-only and derives the recommendation from
Git, spec artifacts, task completion, required gates, PR state, and local review
state—not from conversational memory.

## Human Boundaries

When the next step is creating a branch, committing, pushing, pulling,
rebasing, addressing review findings through a flow that may commit, merging,
or releasing, Next prints the exact command for the human to run. It never
executes anything itself.

## Detected Lifecycle

For a full specification, the navigator recognizes:

```text
constitution -> specify -> clarify when needed -> plan -> tasks -> required gates -> implement
-> commit/push -> create-pr -> pr-review -> address findings -> merge
```

The required gates come from spec metadata. For the stock full-spec template,
they are checklist, analyze, and critic. A failed gate is a stop condition, not
an invitation to rerun it until it turns green.

Quickfix records linked to the current branch can resume at implementation, but
Next never chooses quickfix instead of specify on the user's behalf.

## Release Boundary

A merged PR completes the development flow detected by Next. The command does
not automatically invoke `/devspark.release`: releases are separate,
human-triggered events, and release remains the only command that sweeps
`.devspark.work/` into `.archive/`.
