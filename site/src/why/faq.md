# Frequently Asked Questions

## What is DevSpark?

DevSpark is an optional toolkit for using AI coding assistants to produce better software.
It offers engineering guidance, skills, and checks to help developers understand a change,
validate its credible blast radius, and maintain code, tests, and durable Knowledge. It is not a
mandated development methodology or a substitute for existing engineering controls.

## What does "stop measuring process compliance as a proxy for software quality" mean?

Specifications, plans, and reviews can be valuable. Completing them is not, by itself, evidence
that software is correct, safe, or maintainable. DevSpark should evaluate the actual change and
its supporting evidence, not reward the completion of paperwork.

## What is a Delta?

A **Delta** is an intentional software change: a feature, defect fix, simplification, or reliability
improvement. Its **blast radius** is the affected behavior, callers, consumers, contracts, data,
and plausible failure paths that need investigation or validation. An unrelated part of the
repository is not automatically in scope.

## Is DevSpark still specification-driven?

Formal specifications remain useful, especially where the problem, architecture, interfaces, or
risk need substantial thinking before implementation. They are one legitimate journey, not the
only legitimate way to produce a good Delta. See [Vision and Manifesto](philosophy.md).

## Can I use Code First, starting from code I've already written?

That is a central direction for DevSpark: understand the actual diff, assess its impact, verify it,
and reconcile Knowledge without inventing a specification or a prior approval. The existing toolkit
has lighter-weight routes, but **full Code First entry and common Delta readiness assurance are
evolution goals**, not guarantees that every installed version already provides. Check the
available skills and version in your repository.

## Does Code First mean I can skip tests, security reviews, or authorization?

No. The journey is flexible; required assurance is not. Accountable humans establish standing
expectations, so routine changes need not seek a fresh approval at every step. An agent cannot
lower that floor or waive mandatory controls. Material exceptions and uncertain risk
classifications return to the authorized participant.

## Who can accept a limitation or unresolved risk?

A named person with the authority to make that decision, through an explicit recorded acceptance.
Silence, an agent's inference, and a completed checklist do not constitute acceptance.

## What counts as independent assurance?

A reviewer or a separate model using independently supplied context can challenge reasoning.
Deterministic tests, a different execution environment, physical-device testing, and actual human
observation can independently test behavior. These are distinct evidence types: a second model's
opinion is not a substitute for running a test or observing a real user when that is needed.

## Should DevSpark inspect the whole system when I make a change?

No. Validate the **credible blast radius** of the Delta. Follow actual dependencies and plausible
risks as far as necessary, but don't expand implementation work just because another improvement
was discovered. Mandatory repository-wide checks still apply where required.

## What are the three enduring engineering assets?

**Code**, **tests**, and **durable Knowledge**. Knowledge under `.knowledge/` describes current
architecture, domain constraints, and consequential decisions not obvious from code and tests.
Temporary plans and task lists can help create those assets but are not competing sources of
current truth.

## Are specs and plans retained forever?

Completed work products follow the repository's current archive and traceability rules, rather
than remaining active engineering instructions. Their value should be reflected in code, tests,
and current Knowledge. Git provides revision history; obsolete Knowledge is updated or retired.

## How do skills, slash commands, agents, and prompts differ?

A **skill** is a reusable DevSpark workflow. A **slash command** such as `/devspark-specify` invokes
a skill. The **agent** is the AI assistant performing the work. A **prompt** is the instruction it
follows, whether written by the developer or provided with a skill. See
[Terminology](../guides/prompt-lifecycle-mapping.md#terminology).

## Where are DevSpark files kept?

`.devspark/` holds installed framework files; `.devspark.work/` holds temporary work products,
configuration, and overrides; `.knowledge/` holds current authoritative truth;
`.archive/` holds inactive historical work products. See
[How It Works](../get-started/how-it-works.md).

## Does PR review or release require a specification for every change?

The engineering principle is no: the actual Delta and its evidence matter more than the
existence of a formal spec. **Individual installed commands may still impose workflow artifact
requirements** while the toolkit evolves. Check the version and command contract instead of
assuming the new philosophy is fully implemented.

## Can teams customize skills?

Yes. Personal and team command overrides under `.devspark.work/` take precedence over installed
stock instructions under `.devspark/`. Framework upgrades must preserve repository-owned
work products and overrides.

## Does DevSpark automatically enforce repository policy or approve a PR?

No. AI-expressed checks and recommendations do not replace CI status checks, branch protections,
organizational approvals, or real human review. DevSpark does not auto-approve or auto-deploy.
See [About, Architecture and Controls](about.md).

## How should we evaluate whether DevSpark is helping?

Look at actual regressions, reproducible verification, scope control, repeated review effort,
current Knowledge, and whether the **next** Delta can reuse understanding rather than rediscover
it. See [How to Evaluate](evidence.md).

## Where should I start?

[Evaluate One Task](../get-started/evaluate-one-task.md), then
[How It Works](../get-started/how-it-works.md).
