# DevSpark

DevSpark is Make Bold Solutions' adaptive software-delivery toolkit for AI-assisted engineering. It gives an
AI coding assistant enough structure to understand intent, implement with current knowledge and
tests, verify the result, and deliver it without turning planning paperwork into permanent truth.
Its reusable workflows are **skills**: invoke one with a `/devspark-*` slash command, and your
AI agent follows its prompt instructions. See the [terminology](guides/prompt-lifecycle-mapping.md#terminology).

<div class="devspark-release-status" aria-label="Current release information">
<span><strong>Current release</strong> <span data-devspark-version>Loading...</span></span>
<span><strong>Build date</strong> <time data-devspark-build-date>Loading...</time></span>
</div>

## One Flow

Version 9.5.2 makes PR re-review a bounded, terminal update. Read the
[release notes](releases.md#952-2026-11-12) and
[upgrade guidance](get-started/upgrade.md#upgrading-to-952).

**One Flow. Assurance as Needed. Deliver Software.** DevSpark helps you understand the problem,
implement the software, verify the outcome, and deliver a reliable change.

Start new work with `/devspark-specify`, or resume with `/devspark-next`. Every change follows the
same path: understand, implement and verify, then deliver. There is no route to choose. A plan, a
task list or a focused review is added only when a specific uncertainty or risk justifies it.
Existing v9.3 specifications continue on their recorded route. Click any step to see what it does
and why it is there.

<div data-devspark-flow><noscript>Enable JavaScript for the interactive flow explorer. New work starts
with <code>/devspark-specify</code>; a quickfix record is optional for a diagnosed defect; existing
v9.3 specifications continue on their route. All of them converge on
<code>/devspark-implement</code>.</noscript></div>

## Plan Temporarily, Review the Delta

Plans help produce a change; they are not release evidence or a second source of truth. Git records
how the repository changed, and `.knowledge/` states how it works now. Code, tests, and current
knowledge change together, and `/devspark-release` later archives any completed planning record.

## Start Here

- [Evaluate One Task](get-started/evaluate-one-task.md): try it on one real task, reversibly.
- [Quick Start](get-started/quickstart.md): install it for your AI agent.
- [How It Works](get-started/how-it-works.md): the lifecycle, the four roots, and what each stage owns.
- [Skill Catalog](guides/prompt-lifecycle-mapping.md): every `/devspark-*` skill, with the exact slash command to type.
- [FAQ](why/faq.md)
