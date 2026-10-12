# How to Evaluate

Evaluate DevSpark by observable delivery outcomes, not by the number of planning files it retains. Counts of specs, tasks, or review files do not measure adoption, quality, or traceability; they can rise while the implementation is wrong. The real question is whether code, tests, current knowledge, and published documentation agree at review and release.

## What can be verified

| Question | Evidence source |
|---|---|
| Did the change pass required checks? | CI results and recorded command output |
| What behavior shipped? | Git diff, release tag, current code, and tests |
| Is technical guidance current? | `.knowledge/` nodes and the generated index |
| Is user guidance current? | `site/src/` and the published site build |
| Were review findings resolved? | Hosting-platform review state and the final diff |
| How did the system change? | Git log, blame, tags, and release history |

Temporary specs, task lists, and gate reports help implementation but are not durable evidence.

## Recommended measures

Establish a baseline and compare:

- lead time from accepted work to verified merge;
- escaped defects and rollback frequency;
- review findings by severity and recurrence;
- percentage of behavior changes with proportionate tests;
- stale-knowledge findings from site audit or release;
- failed verification repaired before PR creation;
- deployment frequency and change-failure rate.

Report the collection window, repository scope, exact query, exclusions, and limitations. Avoid claims that cannot be reproduced from accessible durable systems.

## Evaluation pattern

1. Select one representative task and record the normal delivery baseline.
2. Use the lightest appropriate DevSpark route.
3. Require the same build, test, security, and review gates.
4. Compare elapsed effort, findings, rework, and clarity of the final delta.
5. Repeat across different risk levels before drawing conclusions.

See [Evaluate One Task](../get-started/evaluate-one-task.md) for a practical start and [About, Architecture and Controls](about.md) for operating boundaries.
