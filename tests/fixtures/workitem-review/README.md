# Work-item review calibration corpus

<!-- DevSpark — © 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com -->

`calibration-corpus.json` is the acceptance target for the shared work-item review standard. The
standard is a rubric applied by a language model, so "we wrote the rubric down" is not evidence that
it grades consistently. This corpus is that evidence: a fixed set of synthetic work items with the
verdict each one must receive.

The dependency runs one way. The corpus constrains the standard, not the reverse. When the standard
and the corpus disagree, the standard is wrong until a reviewer decides otherwise and changes the
expected verdict deliberately, in the same commit.

## What a case asserts

Each case carries an `expected` map holding one verdict per dimension. That vector is the assertion
— it is discrete and reproducible, unlike the prose a grader emits.

Failing cases also carry `expected_deficiencies`. Those describe what the named deficiency has to
identify, not the words it has to use. Matching a grader's prose verbatim produces a test that
breaks on rewording while still passing on a wrong verdict, which is worse than no test.

## Case design

`WI-CAL-001` passes every dimension and is the baseline the others are perturbed from. A standard
that fails the baseline is over-strict, and the corpus catches that as readily as it catches a
standard that is too lenient.

`WI-CAL-002` through `WI-CAL-006` each fail exactly one dimension. Single-dimension failures are the
discriminating cases: a grader that collapses to a single overall impression will fail several
dimensions at once and be caught here, not in production.

`WI-CAL-007` fails three dimensions simultaneously and exists to prove every failing dimension is
reported rather than the first one found.

## Scope of this corpus

These items are plain text and deliberately unremarkable. They calibrate judgement, not transport —
quoting, encoding, and multi-byte handling belong to the hostile round-trip fixture that covers the
payload path, and mixing the two concerns would make a transport regression look like a grading
regression.

All content is synthetic. Work items describe fictional software changes and contain no personal or
health information.

## How calibration is run

The corpus is checked at two different levels, because no single mechanism can check both.

The structural half runs in `pytest`. It asserts that the corpus parses, that every case's
`expected` map carries exactly the dimensions named in the corpus `dimensions` list, that the
verdict vocabulary in the corpus matches the vocabulary the standard defines, that the standard
enumerates the same five dimensions in the same order, and that the standard records the
`corpus_version` it was calibrated against. These are static facts about files, which is what this
repository's test suite is able to check. Running them costs nothing and catches the most common
breakage, which is the standard and the corpus drifting apart after an edit to one of them.

The grading half cannot run in `pytest`. The standard is a markdown rubric that only a language
model can apply, and there is no harness here that executes a prompt — every test in this
repository is a static contract test over files and script subprocesses. So the grading half runs
as part of the end-to-end verification gate, where an agent is already the executor. The gate
applies the standard to all seven cases and records the resulting verdict vector for each.

**Pass condition.** For all seven cases, the full five-dimension verdict vector must match the
case's `expected` map exactly. The vector is the assertion, not an overall pass/fail summary of it.
Collapsing to an overall verdict would defeat the corpus design: `WI-CAL-002` through `WI-CAL-006`
each fail exactly one named dimension, so a grader that failed the wrong dimension would still
produce the right overall answer and slip through. One wrong cell in any vector fails the run.

`expected_deficiencies` is reviewed but is not part of the pass condition. It describes what a
deficiency has to identify, not the words it has to use, and asserting on prose produces a check
that breaks on rewording while still passing on a wrong verdict.

**Determinism.** One run, at temperature 0. A rubric that needs resampling to land on a stable
answer is a rubric that is not specific enough yet, so the single deterministic run is deliberately
the strict choice rather than the cheap one.

**Evidence.** The per-case verdict vectors are recorded in the verification gate artifact. A
calibration that was never run is therefore visibly absent rather than silently assumed, which is
the failure mode this corpus exists to prevent.

## Adding a case

Perturb the baseline along one dimension and leave the rest intact. A case that changes several
things at once cannot tell you which change moved the verdict, which defeats the purpose of having
a corpus at all.
