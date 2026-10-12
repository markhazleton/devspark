# Evaluate One Task

You do not need to adopt the complete DevSpark methodology to find out whether it helps. This page is a low-friction evaluation path for one real, current task — not a tour of every skill.

## Before you start

- Use a disposable branch in a real repository. Do not use a throwaway sandbox — the point is to see how it behaves on your actual code and standards.
- Pick one item you would be doing anyway: an open bug, a small feature, or an active work item. Avoid anything architecturally sensitive for this first pass.
- Plan for a single working session. If it does not add value, stop — nothing here commits your team to future use.

## The six-step path

1. **Open a disposable branch** in a real repository.
2. **Send the bootstrap prompt in preview-only mode.** Ask the agent to show the workflow it would run and every file it would create, modify, or delete — without writing anything yet.
3. **Review every proposed file and instruction** before approving anything. Read the actual skill prompt instructions, not just a summary.
4. **Select one existing bug or small work item** as the task, and let the agent generate the requirements, plan, and tasks for it.
5. **Compare the proposed approach with how you would normally handle the task.** Would the specification, plan, or generated tests have caught something you'd have missed? Would they have added time without adding value?
6. **Proceed or stop.** If it helped, continue using it on that task through review and PR. If it didn't, discard the branch — you have lost nothing but the session.

## What to skip on this first pass

Do not introduce these on your first evaluation — they add overhead without changing whether the core workflow is useful to you:

- Release and versioning workflows
- Multi-user personalization
- Multi-application monorepo registries
- The full skill reference

The goal of this page is a single useful experience with the core specify → plan → implement → review loop, not complete understanding of the methodology.

## Getting the preview

Every quickstart guide opens with a **Preview Prompt** step:

> *"Preview only — show me the mode you'd run, every file you'd create/modify/delete, and the actual skill prompt instructions you'd install. Make no changes and wait for my `proceed`."*

See the [Quick Start Guide](quickstart.md) for the exact bootstrap prompt for your AI agent, and the **Preview Prompt** section at the top of your agent's quickstart guide.

## After the trial

- **It helped:** Continue through `/devspark-create-pr` and `/devspark-pr-review` for this task, using your existing pull-request and release process unchanged.
- **It didn't help, but might elsewhere:** Discard the branch. Try again on a different kind of task (a bug fix instead of a feature, or vice versa).
- **It's not a fit:** Discard the branch. The methodology files sit inertly in the repo unless a developer chooses to invoke them.

## Related

- [How to Evaluate](../why/evidence.md) — what to measure across repeated use, not a single trial
- [Review Architecture and Controls](../why/about.md) — how the workflow is hosted, versioned, and controlled
- [Quick Start Guide](quickstart.md) — full bootstrap and first-feature walkthrough
