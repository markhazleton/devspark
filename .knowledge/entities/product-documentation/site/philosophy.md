# DevSpark Philosophy

DevSpark is agile product development made explicit enough for an AI agent to
participate correctly. The agent is a real teammate in the process: discovery,
priority, refinement, planning, implementation, review, and release all leave
the context needed for the next participant to act well.

## Start with external pressure

Nothing enters exploration or the roadmap because it merely seems interesting.
Work starts from a real signal: a business request, a user problem, or a
constraint the system has revealed. Explore is a partnership between a human
and an agent. It may include spikes or multiple model perspectives, but its
durable outcome is understanding. Roadmap turns that understanding into a
prioritized shortlist.

Specify completes refinement: it records both what should be built and the
constraints that shape how it will be built. Plan, tasks, analyze, and critic
compress sprint planning and code review into an explicit commitment. Implement
then executes that commitment; ambiguity belongs earlier in the lifecycle.

The close is assimilation, not implementation. Release validates that the
change landed in code, knowledge, and governance, and makes the result part of
the system's current truth. The next exploration starts from that richer
grounding, while the next pressure still comes from outside the system.

## Current truth, not lifecycle history

The repository is optimized for what is true now:

| Surface | Answers | Lifecycle |
|---|---|---|
| `.knowledge/` entities | What is true now? | Mutated in place |
| `.knowledge/governance/constitution.md` | What rules govern the work? | Amended explicitly |
| `.knowledge/governance/decisions/` | What did we choose, and why? | One current file per topic |
| `.devspark.work/` | What work is in flight? | Temporary |

Entities and governance are current-state records, not an archive. Decisions
are keyed by domain or topic, not creation order; when the reasoning changes,
edit the decision in place. Git preserves committed history. Completed work
products leave the active work surface only through the release boundary.

## Evidence and closed references

Every durable knowledge or governance claim needs checkable evidence. Use test
evidence when execution proves the claim and inspection evidence when a human or
agent must compare the claim with code. Code-only evidence should explain why a
test was not used when a practical test was attempted or unavailable.

Permanent code and knowledge may reference one another, but they must not point
to specifications, tasks, plans, spikes, pull-request threads, or other
ephemeral artifacts. Ephemeral work may point inward to current truth. This
one-way boundary keeps the permanent graph usable after a work package is gone.

## Release and rollover

Verification makes tasks and their code/knowledge linkage eligible; it does not
archive them. A spec stays whole in `.devspark.work/` until every task is
verified. Release is the sole command that validates and archives eligible
packages, so incomplete packages remain intact for the next release. Release
cadence is a human-selected business event; sprint reporting can be derived
from dates and Git history rather than becoming another state DevSpark must
track.

The short-term archive is a safety buffer. Git remains the durable history, and
teams may later move older completed release material to a separate planning or
documentation repository as a human workspace convention. DevSpark prompts do
not depend on that second repository.

## No CLI or harness

DevSpark is prompt-first. It has no standalone CLI and no programming harness.
Quickstart prompts are the only approved way to install, upgrade, or repair it.
Small deterministic scripts are encouraged when a prompt needs one focused
operation; a coordinating dispatcher would recreate the harness the project is
deliberately avoiding.
