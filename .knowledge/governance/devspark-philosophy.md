# DevSpark — Vision and Engineering Manifesto

## Our Vision

DevSpark helps developers use intelligent tools to create trustworthy, maintainable software—
regardless of how the development journey begins.

AI amplifies engineering judgment rather than replacing it. Code First, Model First, experimental
probes, defect investigation, and formal specification are legitimate approaches. DevSpark does not
prescribe the sequence through which a developer discovers or implements a change. It helps
establish whether the result is understood, appropriately verified, and ready to become part of
the software.

**DevSpark is methodology-independent, but engineering-discipline-dependent.**

## Our Manifesto

### Stop measuring process compliance as a proxy for software quality

A completed specification does not prove that software works. An approved plan does not prove
that the implementation is well designed. Completing a prescribed sequence does not establish that
a change is safe or maintainable. Conversely, software discovered through exploratory coding is
not inferior because it did not begin with a formal specification.

Process must earn its place by improving engineering outcomes.

**The Delta is the unit of engineering value—not the workflow used to produce it.**

Every development journey ultimately answers five questions.

### 1. What changed, and why?

A **Delta** is an intentional change to an existing software system. It can add behavior, correct
a defect, retire complexity, or improve reliability. The accountable participant establishes the
intended outcome and authorizes material changes in scope. Agents may investigate and propose but
must not invent intent, approval, or a planning history that did not occur.

A developer may begin with requirements, with an existing diff, or with a bounded experiment.
These are different entry points, not different standards of engineering quality.

**The journey is flexible. The intent must be understood.**

### 2. What could this change affect?

The Delta identifies **what we intend to change**. Its **blast radius** identifies what we must
investigate and verify: directly affected behavior, callers, consumers, dependencies, contracts,
data, and credible failure paths. Blast radius can extend beyond changed files but must follow
supported impact, not proximity or speculation.

An unrelated finding is reported or routed separately unless it demonstrates a defect introduced
by the Delta, a violated applicable invariant, or an unmet obligation. Discovering an improvement
does not, by itself, authorize expanding implementation scope.

**Validate the blast radius, not the entire universe.**

### 3. How do we know the affected software still works?

Every Delta has an assurance floor: establish intended behavior; assess the credible blast radius;
perform applicable verification; report what actually ran and what did not; reconcile material
findings; and satisfy mandatory security, contractual, organizational, and independent-review
obligations. Requirements that must be decided **before** a change still apply before that change,
whatever journey was chosen.

Accountable humans set **standing assurance expectations**. Routine Deltas operate within those
expectations without a fresh human approval at every step. An agent may propose a risk class or
verification scope, but it may not reduce required assurance, waive mandatory evidence, or decide
that an uncertain risk classification is inconsequential. Material exceptions and uncertain
classifications go to an authorized human. A limitation is accepted only by an explicit, recorded
decision from a named person with authority; silence is not acceptance.

Independent assurance offers a meaningful cross-check: deterministic tests, a separate model
reasoning over independently supplied context, a different execution environment, a physical
device, or an attributable human observation. These prove **different things**. An independent
model opinion never substitutes for an execution result or real-world observation when those are
required. A test not run is not a passed test; simulated play is not human testing.

**Confidence comes from credible evidence, not declarations of compliance.**

### 4. What enduring Knowledge must we preserve?

DevSpark protects three enduring engineering assets:

- **Code** implements the behavior of the software.
- **Tests** provide executable evidence of expected behavior, contracts, and regressions.
- **Durable Knowledge** under `.knowledge/` preserves current architecture, domain constraints,
  decisions, and relationships not sufficiently expressed by code and tests.

Specifications, plans, tasks, and quickfix records are **working artifacts**, not competing
sources of permanent software truth. When their purpose has been served and necessary decisions
and evidence are preserved, they may be archived or discarded subject to the Constitution's
retention and traceability rules. Their historical presence does not make them current guidance.

A Delta that makes durable Knowledge wrong, redundant, or obsolete must update, replace, or retire
that Knowledge with the code and tests. Do not create Knowledge merely to satisfy a linkage field;
when no durable truth changed, an explained `n/a` is legitimate.

**Preserve understanding, not paperwork.**

### 5. Is the Delta ready to advance?

DevSpark presents the actual changed behavior, impact boundary, verification evidence, uncovered
risk, Knowledge reconciliation, and any outstanding binding decisions. An unresolved blocking
defect stops the Delta. A genuine uncovered mandatory requirement stops it. An unrelated improvement
opportunity does not.

Human attention is scarce. Agents should do the investigation, present concise, inspectable
evidence, and surface meaningful decisions for the accountable participant to ratify. Routine
cases use established expectations. Independent assurance challenges consequences, not mere
completion of the author's workflow.

Once the Delta and its credible blast radius are sufficiently verified, mandatory obligations are
satisfied, and necessary decisions are authorized, recommend proceeding—**and stop**.

## How We Measure Success

Do not substitute counts of documents, tasks, gates, findings, commits, or tests for outcomes.
Look instead for evidence that:

- **Correctness:** the intended behavior works without demonstrated regressions in the blast radius.
- **Confidence:** checks are reproducible, accurately attributed and proportionate to actual risk.
- **Continuity:** the next Delta locates and reuses relevant Knowledge, tests, and decisions rather
  than rediscovering the system.
- **Changeability:** the next change does not need to work around avoidable complexity or stale truth.
- **Efficiency:** repeated reviews and process-generated rework decline without bypassing assurance.

**When the next Delta begins, does the software—and the Knowledge surrounding it—make that change
easier to understand, implement, and verify?**

## How the Manifesto Fits Governance

This document explains **why** DevSpark exists and how to interpret engineering tradeoffs. It is
**not a new gate** and it does not override [the Constitution](constitution.md), which remains the
highest enforceable repository authority. [The Knowledge Framework Contract](knowledge-framework-contract.md)
owns durable Knowledge mechanics; existing verification, assurance, closeout, and review contracts
own their technical obligations. [The prompt mapping](devspark-prompt-mapping.md) describes what
commands actually do, rather than demanding that each command implement the same journey.

The enduring operating model is **current truth, not active historical scaffolding**. Code, tests,
Knowledge, and current governance describe the present system. Working artifacts may document the
Delta that produced it but must not be promoted into durable truth merely because they exist.
Historical spec bundles follow the Constitution's archive policy; Git preserves revision history.

**Engineering rigor is outcome-oriented and bounded.** Use the smallest complete change that
satisfies actual requirements, invariants, and operating constraints. Validate the credible blast
radius and stop when the change is ready. The developer's choice of journey never removes
mandatory obligations.

## In One Sentence

**DevSpark helps developers turn changes into trustworthy, maintainable software through any
appropriate development journey—validating each Delta and its blast radius while preserving the
code, tests, and Knowledge that make future change possible.**
