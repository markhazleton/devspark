# Frequently Asked Questions

## What is DevSpark?

Make Bold Solutions' adaptive software-delivery toolkit for AI coding assistants: proportionate planning, implementation discipline, current knowledge, executable verification, and delta-based review through reusable skills, prompt instructions, and helper scripts.

## How do skills, slash commands, agents, and prompts differ?

A **skill** is a reusable DevSpark workflow. A **slash command**, such as `/devspark-specify`, is what
you type to invoke it. The **agent** is the AI coding assistant that performs the work. A **prompt**
is the instruction text the agent follows, whether supplied by you or by a skill. They are related,
not interchangeable. See [Terminology](../guides/prompt-lifecycle-mapping.md#terminology).

## Is it still spec-driven development?

Specs remain useful when a change needs them, but they are implementation aids, not permanent records. The model is **Plan Temporarily, Review the Delta**: plan enough to reduce uncertainty, implement code, tests, and knowledge together, verify, review what will ship, then let `/devspark-release` archive the plan. See [Philosophy](philosophy.md).

## Where do files go?

See the four-root table in [How It Works](../get-started/how-it-works.md): `.devspark/` (framework), `.devspark.work/` (temporary work), `.knowledge/` (current truth and published guides), `.archive/` (old work products by release).

## When does a plan get archived?

A completed plan stays under `.devspark.work/` with its `code_ref` and `knowledge_ref` linkage populated, sometimes across more than one release, until `/devspark-release` confirms the linkage and moves it to `.archive/{YYYY-MM-DD}/`. The archived plan is never read back as current truth; that lives in code, tests, and `.knowledge/`.

## What happens when verification fails?

The planning bundle stays. `/devspark-implement` repairs the same slice and reruns the required check. Nothing is deleted.

## Is `.knowledge/` an ADR library?

No, but it does hold decisions. It holds current-state typed nodes, including one current decision per topic that records the rationale and the entities it constrains. Do not store supersession chains, task records, or feature timelines there; Git is the history.

## How does a reviewer know the intent without the plan?

The PR describes the current user outcome and the durable delta in self-contained language, and reviewers check that against code, tests, knowledge, and the constitution. If intent cannot be explained without a planning ID, the PR description is incomplete.

## Do PR review and release require a spec?

No. Missing planning files are expected after implementation. PR review checks the diff and release checks the delta; neither recovers plans from Git or archives. A completed plan still present is a finalization warning.

## Do quickfixes finish differently?

They use less planning, not a weaker finish. Quickfix, quick-spec, and full-spec routes all converge on `/devspark-implement` for code, tests, knowledge, and verification.

## Can teams customize skills?

Yes, by customizing the skill's prompt instructions. Team and personal overrides under `.devspark.work/` resolve before stock prompts in `.devspark/`, and upgrades never overwrite them.

## Where should I start?

[Evaluate One Task](../get-started/evaluate-one-task.md), then [How It Works](../get-started/how-it-works.md).
