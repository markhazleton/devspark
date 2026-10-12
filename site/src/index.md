# DevSpark

DevSpark is Make Bold Solutions' adaptive software-delivery toolkit for AI-assisted engineering. It gives an
AI coding assistant enough structure to clarify intent, plan proportionately, implement with current
knowledge and tests, and review the result without turning planning paperwork into permanent truth.
Its reusable workflows are **skills**: invoke one with a `/devspark-*` slash command, and your
AI agent follows its prompt instructions. See the [terminology](guides/prompt-lifecycle-mapping.md#terminology).

<div class="devspark-release-status" aria-label="Current release information">
<span><strong>Current release</strong> <span data-devspark-version>Loading...</span></span>
<span><strong>Build date</strong> <time data-devspark-build-date>Loading...</time></span>
</div>

## Find Your Route

Pick the kind of change, then click any step to see what it does and why it is there. A one-off edit
needs no planning at all; the routes below add only as much structure as the risk calls for.

<div data-devspark-flow><noscript>Enable JavaScript for the interactive route explorer. The routes are
one-off (no planning), quickfix, quick spec, and full spec, and all converge on
<code>/devspark-implement</code>.</noscript></div>

## Plan Temporarily, Review the Delta

Plans help produce a change; they are not release evidence or a second source of truth. Git records
how the repository changed, and `.knowledge/` states how it works now. Code, tests, and current
knowledge change together, and `/devspark-release` later archives the completed planning bundle.

## Start Here

- [Evaluate One Task](get-started/evaluate-one-task.md): try it on one real task, reversibly.
- [Quick Start](get-started/quickstart.md): install it for your AI agent.
- [How It Works](get-started/how-it-works.md): the lifecycle, the four roots, and what each stage owns.
- [Skill Catalog](guides/prompt-lifecycle-mapping.md): every `/devspark-*` skill, with the exact slash command to type.
- [FAQ](why/faq.md)
