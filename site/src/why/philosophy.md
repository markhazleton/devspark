# Vision and Engineering Manifesto

**Better software. Multiple journeys. One engineering commitment.**

## Our vision

DevSpark helps developers use intelligent tools to create trustworthy, maintainable software,
regardless of how their development journey begins.

AI amplifies engineering judgment; it does not replace software engineering. Code First, Model First,
exploratory development, defect investigation, and formal specification can all be appropriate.
The journey depends on the problem. The obligation to deliver a well-understood, appropriately
verified change does not.

**DevSpark is methodology-independent, but engineering-discipline-dependent.**

## Our central principle

> **Stop measuring process compliance as a proxy for software quality.**

A complete specification does not prove that code works. A signed-off plan does not prove the
architecture is appropriate. Conversely, a change discovered through coding is not inferior
because no specification preceded it.

Process earns its place by improving engineering outcomes. **The Delta is the unit of engineering
value, not the workflow used to produce it.**

A **Delta** is an intentional change to the software: a feature, bug fix, simplification, reliability
improvement, or removal of unnecessary complexity. Every journey converges on five questions.

## Five questions for every Delta

### 1. What changed, and why?

Establish the intended result and what must remain true. Work may begin with a requirement, an
existing code diff, an experiment, or an observed failure. Do not invent a prior specification,
planning decision, or approval to legitimize a Code First change.

An accountable participant owns the intended outcome and any material scope decision. The AI
assistant may investigate and recommend but cannot manufacture human acceptance.

### 2. What could this change affect?

The **Delta** defines what we intend to change. Its **blast radius** defines what we must
investigate and validate: affected callers, consumers, dependencies, contracts, data, and credible
failure paths.

The blast radius can extend beyond edited files, but it must follow evidence of actual impact.
Discovering unrelated work is not permission to expand the Delta. Surface it separately when
appropriate.

**Validate the blast radius, not the entire universe.**

### 3. How do we know the affected software still works?

All Deltas have a minimum assurance obligation: understand intended behavior, assess credible
impact, perform relevant checks, report actual results and unknowns, reconcile findings, and honor
applicable security, contractual, organizational, and review controls.

Accountable humans establish standing assurance expectations. Routine changes operate within
those expectations without requiring new approvals at every step. Agents may propose verification
scope, but cannot lower required assurance, waive evidence, or quietly classify uncertain risks as
inconsequential. Material exceptions and uncertainty return to an authorized participant.

An accepted limitation requires an explicit, recorded decision by a named, authorized person.
Silence is not acceptance.

A second model reviewing independently supplied context can provide a useful reasoning cross-check.
Executed tests, different environments, real devices, and human observations offer different forms
of evidence. None should be presented as something it is not. A test not run is not a passing test.

**Confidence comes from credible evidence, not declarations of compliance.**

### 4. What enduring Knowledge must we preserve?

DevSpark protects three enduring engineering assets:

- **Code:** the implemented behavior of the software.
- **Tests:** executable evidence of intended behavior, contracts, and regressions.
- **Durable Knowledge:** current architecture, domain constraints, important decisions, and
  relationships not sufficiently apparent from code and tests.

Specifications, plans, tasks, and quickfix records are working artifacts. Their lasting value should
be reflected in the enduring assets, not duplicated as competing versions of current truth.
Completed working records follow the repository's retention and archive rules; they are not active
engineering instructions.

If a Delta makes Knowledge obsolete or misleading, update or retire it. If no enduring truth
changed, do not invent Knowledge just to populate a field.

**Preserve understanding, not paperwork.**

### 5. Is the Delta ready to advance?

DevSpark should present a concise, inspectable account of intent, changed behavior, blast radius,
checks performed, outstanding uncertainty, Knowledge reconciliation, and any decisions needing
human authorization.

Unresolved blocking defects and mandatory obligations stop advancement. Unrelated enhancement ideas
do not. Human attention is scarce: investigate first, present the evidence, and elevate only decisions
that require the accountable participant's judgment.

Once the Delta is supported by sufficient evidence, applicable controls are met, and required
human decisions are recorded: **recommend proceeding, and stop.**

## How we know this is working

We do not substitute counts of specs, tasks, gates, or reports for engineering outcomes. Useful
signals include demonstrably correct changes, reproducible checks, fewer escaped regressions,
less repeated investigation, and less process-generated rework.

The strongest practical test comes later:

> **When the next Delta begins, does the software—and the Knowledge surrounding it—make that
> change easier to understand, implement, and verify?**

See [How to Evaluate](evidence.md) for observable ways to test that claim.

## Philosophy, governance, and implementation

This is the guiding vision, not an additional approval gate. The repository's
`.knowledge/governance/devspark-philosophy.md` holds the complete governing manifesto.
The repository Constitution remains authoritative for enforceable controls; individual contracts
and skills define their mechanics.

DevSpark already offers lighter and fuller development routes. Converging those routes on the same
blast-radius-driven assurance—particularly accepting an existing Code First Delta without
reconstructing a fictional plan—is an **evolution goal**. Do not assume every installed skill or
version implements that model today.

For the operational boundaries and current controls, see
[About, Architecture and Controls](about.md) and the [FAQ](faq.md).
