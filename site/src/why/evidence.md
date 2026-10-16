# How to Evaluate

Evaluate DevSpark by the **quality and changeability of the software it helps deliver**, not
by the number of specifications, tasks, reports, or gates completed.

The essential question is whether a Delta achieves its intended purpose without introducing
regressions in its credible blast radius—and whether code, tests, and durable Knowledge make the
**next** Delta easier to understand and verify.

## Evaluate the Delta, not the ceremony

| Question | Evidence to inspect |
|---|---|
| What changed, and why? | Intended outcome, actual Git diff, relevant contracts, accountable scope decisions |
| What could it affect? | Callers, consumers, dependencies, data flow, failure paths, and reasons for the chosen validation boundary |
| Does the affected software still work? | Relevant test executions, CI, contract checks, environment or device results, and known untested cases |
| Is durable Knowledge current? | Owning `.knowledge/` content, links to code and tests, and updates or retirement of obsolete guidance |
| Is the Delta ready to advance? | Remaining blockers, accepted limitations, named authorized decisions, PR diff, and required repository checks |

A test **not run** is not a passing test. A separate model's assessment is a reasoning cross-check,
not evidence of execution. A simulated user is not a real human tester. Acceptance of a limitation
requires an explicit, recorded decision from a named person with authority; silence is not
acceptance.

## Validate the credible blast radius

A small diff can affect many callers; a large diff may leave externally observable behavior
unchanged. Scope assurance from demonstrated impact, not file count or the desire to revisit every
nearby subsystem.

Inspect affected contracts, behavior, integrations, error handling, and relevant regression tests.
Mandatory repository-wide CI and security checks still apply, even when focused local tests are
sufficient for day-to-day investigation. Do not quietly treat unrelated pre-existing failures as
new Delta defects—or dismiss an introduced regression as unrelated.

## Useful outcome measures

Establish baselines and compare like-for-like changes where possible:

- **Correctness:** failed required tests, escaped regressions, rollbacks, and change-failure rate.
- **Assurance:** applicable tests and contracts exercised, unexplained validation gaps, and findings
  repaired before merge.
- **Continuity:** whether a later Delta actually located and reused current Knowledge and tests,
  rather than rediscovering the same constraints.
- **Changeability:** rework caused by stale Knowledge, unclear contracts, or avoidable complexity.
- **Efficiency:** time to verified merge, repeated review cycles, and work added solely to satisfy
  an artifact or workflow requirement.

Raw counts are context, not conclusions. Report the collection window, repository scope, baseline,
query or measurement method, exclusions, and limitations. Never call a measure observed if it was
only estimated or inferred.

## A practical evaluation

1. Choose a representative small Delta with understandable intent and observable risk.
2. Record a baseline for normal delivery or select a comparable prior change.
3. Use an appropriate DevSpark journey available in the **installed version**; do not assume an
   aspirational Code First entry point is already supported end to end.
4. Inspect the actual blast radius and apply the same mandatory build, security, test, and human
   approval requirements that would otherwise apply.
5. Compare review clarity, actual test evidence, elapsed effort, rework, and Knowledge quality.
6. On a later Delta, check whether the previous work's Knowledge and tests were useful in practice.

Repeat with different kinds of changes before drawing broad conclusions. A successful demo does
not by itself prove maintained software quality or production outcomes.

See [Evaluate One Task](../get-started/evaluate-one-task.md) for a starting point,
[Vision and Manifesto](philosophy.md) for the governing ideas, and
[About, Architecture and Controls](about.md) for operating boundaries.
