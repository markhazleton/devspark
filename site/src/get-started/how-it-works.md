# How It Works

DevSpark separates thinking aids from durable truth. A plan helps produce a change; the verified change, its tests, and the knowledge that explains it are what remain.

<ol class="devspark-delivery__stages" aria-label="Delivery lifecycle">
  <li class="devspark-delivery__stage devspark-delivery__stage--plan">
    <span class="devspark-delivery__number">01</span>
    <h2>Understand the change</h2>
    <p>Start or resume with no route to choose. Add a plan, tasks or a focused review only when a specific risk justifies it.</p>
    <code>/devspark-specify</code>
    <span class="devspark-delivery__kind">Branch first; notes only when needed</span>
  </li>
  <li class="devspark-delivery__stage devspark-delivery__stage--build">
    <span class="devspark-delivery__number">02</span>
    <h2>Implement together</h2>
    <p>Update the behavior, its executable evidence, and the knowledge that explains it.</p>
    <code>/devspark-implement</code>
    <span class="devspark-delivery__kind">One coherent change</span>
  </li>
  <li class="devspark-delivery__stage devspark-delivery__stage--prove">
    <span class="devspark-delivery__number">03</span>
    <h2>Verify the outcome</h2>
    <p>Choose proof in proportion to the risk, run it, and report what was observed, assumed, and unobtainable. Repeat implement and verify until the work is finished.</p>
    <code>/devspark-verify</code>
    <span class="devspark-delivery__kind">Evidence, not ceremony</span>
  </li>
  <li class="devspark-delivery__stage devspark-delivery__stage--release">
    <span class="devspark-delivery__number">04</span>
    <h2>Deliver the change</h2>
    <p>Open the PR once the evidence and any required obligations are in place, then review the durable Git delta against current knowledge.</p>
    <code>/devspark-create-pr</code> + <code>/devspark-pr-review</code>
    <span class="devspark-delivery__kind">Reviewed, mergeable delivery</span>
  </li>
</ol>

Type the full hyphenated slash command, for example `/devspark-plan`. Short names and the retired 8.x dotted form are not aliases. Every change follows the same path, whether it starts from an idea, a defect, or an existing diff: understand the delta, validate its credible impact, and report the evidence. See the [invocation-format note](../guides/prompt-lifecycle-mapping.md#invocation-format).

A **skill** defines the workflow, a **slash command** invokes it, the **agent** performs the work,
and the **prompt** supplies its instructions. See [Terminology](../guides/prompt-lifecycle-mapping.md#terminology).

## Four roots

| Root | Owner | Purpose | Retention |
|---|---|---|---|
| `.devspark/` | Framework | Stock prompts, scripts, templates, and skills | Refreshed on upgrade |
| `.devspark.work/` | Repository workflow | Active plans, overrides, and operational work products | Temporary or replaceable |
| `.knowledge/` | Repository team | Current technical and governance truth, plus published guidance under `.knowledge/guides/` | Current state only |
| `.archive/` | Repository team | Old work products, grouped by release | Write-only; no skill reads it |

`.archive/` is the only archive root. Do not create ADR, rationale, or completed-plan trees elsewhere; use Git history when prior state matters.

## What each stage owns

**Before implementation.** Start new work with `/devspark-specify`, or resume with `/devspark-next`. It creates a work branch and, by default, no planning file; a short `work.md` resume note appears only when intent or decisions would otherwise be lost between sessions. A plan, a task list, or a focused review (`/devspark-critic`, `/devspark-analyze`) is optional and added only when a specific uncertainty or risk justifies it; none of them changes the route or adds a gate. An existing v9.3 specification keeps its recorded route, including tasks and a [planning review](../guides/planning-review.md). These files are working context, so they may use requirement and task ids.

**During implementation.** `/devspark-implement` owns the whole change:

- production code and configuration;
- tests proportionate to the changed behavior;
- affected `.knowledge/` nodes and published guidance;
- required verification and repair loops;
- removal of planning identifiers from durable outputs;
- a recorded test run (see the Test Evidence Record) so later review can reuse it.

Checked boxes do not make a plan complete; a consistent durable repository and passing checks do. Implement never archives the bundle.

**After implementation.** `/devspark-verify` produces proof and closes out the work. PR creation, PR review, and site audit then judge the Git diff, current code, test evidence, current knowledge, and the constitution, not prose written earlier. See [Review and Audit](../guides/review-and-audit.md).

**At release.** `/devspark-release` derives the release from the previous tag through HEAD, verifies the durable delta, writes notes, and is the sole skill that archives bundles marked `Complete` under `.archive/{YYYY-MM-DD}/` with a journaled, non-overwriting archive step, and reports anything ambiguous for a decision. A bundle can stay live across more than one release.

Knowledge is mutated in place, never archived; Git keeps earlier versions. For what counts as knowledge and how it stays current, see [Knowledge](../guides/knowledge-management.md) and [Philosophy](../why/philosophy.md).

## Assurance as needed

Most changes need only ordinary verification. Additional assurance is added for a specific reason and answers that reason only.

| Assurance | When it applies | What it decides |
|---|---|---|
| Tests and verification evidence | Every change | `/devspark-verify` reports what was observed, assumed, and unobtainable, and whether the work is delivered, verified, and eligible |
| `/devspark-analyze` or `/devspark-critic` | A named consistency concern or material risk | A finding and a disposition (continue, pause the affected work, or a decision is needed), then back to implementation |
| Judge | Findings genuinely conflict | Adjudicates the conflict; it never discovers new issues or triggers another review |
| Required obligation | An applicable mandatory control, such as a security, privacy, or compliance sign-off | Recorded in `work.md` under `## Required Obligations` with its authority; delivery is refused until it is satisfied |
| Human approval and risk acceptance | The decision belongs to a person with that authority | DevSpark records the reference; it never grants, waives, or overrides the decision |

A checked required obligation is complete only when it names its `Authority:` and a traceable reference to the evidence or decision that satisfied it: a repository path, commit, review or approval id, or link. Prose alone or a `<placeholder>` does not count. Until then `/devspark-next` reports `delivery-blocked` and `/devspark-create-pr` refuses to open or update the PR:

```markdown
## Required Obligations

- [x] Privacy review of the export fields — Authority: Privacy Office — Approval: SEC-000000
```

The check confirms that a reference is recorded, not that the approval behind it is authentic, so reviewers still confirm the referenced evidence. Policy that exists only outside the repository is not mechanically enforced.

## Recovery

- **Verification failed:** fix the durable outputs and rerun; the bundle stays in place.
- **Completed plan still exists:** rerun `/devspark-implement` finalization.
- **Plan archived too early:** copy it back from `.archive/{YYYY-MM-DD}/` by hand (no skill reads `.archive/`) or use Git, then re-archive after verification.
- **Prior rationale needed:** inspect Git history. Do not add a history node to `.knowledge/`.

## Human control

Agents may analyze and prepare changes autonomously while running skills, but branch creation, external publication, commits, tags, pushes, and destructive operations keep explicit confirmation boundaries.
