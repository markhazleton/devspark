# How It Works

DevSpark separates thinking aids from durable truth. A plan helps produce a change; the verified change, its tests, and the knowledge that explains it are what remain.

<ol class="devspark-delivery__stages" aria-label="Delivery lifecycle">
  <li class="devspark-delivery__stage devspark-delivery__stage--plan">
    <span class="devspark-delivery__number">01</span>
    <h2>Shape the change</h2>
    <p>Choose a one-off, quickfix, quick spec, or full spec based on uncertainty and risk.</p>
    <code>.devspark.work/</code>
    <span class="devspark-delivery__kind">Temporary intent and plan</span>
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
    <h2>Verify and review</h2>
    <p>Run the required checks, then review the durable Git delta against current knowledge.</p>
    <code>/devspark-verify</code> + <code>/devspark-pr-review</code>
    <span class="devspark-delivery__kind">Evidence before release</span>
  </li>
  <li class="devspark-delivery__stage devspark-delivery__stage--release">
    <span class="devspark-delivery__number">04</span>
    <h2>Release the delta</h2>
    <p>Seal and publish the verified change. Archive eligible planning work only after its linkage is complete.</p>
    <code>/devspark-release</code>
    <span class="devspark-delivery__kind">Durable delivery</span>
  </li>
</ol>

Type the full hyphenated slash command, for example `/devspark-plan`. Short names and the retired 8.x dotted form are not aliases. Development journeys vary with the change: some benefit from specifications and plans, while others may begin from an existing diff or defect. In every route, the engineering obligation remains to understand the Delta, validate its credible impact, and report the evidence. See the [invocation-format note](../guides/prompt-lifecycle-mapping.md#invocation-format).

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

**Before implementation.** Use the smallest route that makes uncertainty manageable (see the route explorer on the [home page](../index.md)). A quickfix may need one record; a high-risk change may need a spec, plan, tasks, and a [planning review](../guides/planning-review.md). These files are working context, so they may use requirement and task ids.

**During implementation.** `/devspark-implement` owns the whole change:

- production code and configuration;
- tests proportionate to the changed behavior;
- affected `.knowledge/` nodes and published guidance;
- required verification and repair loops;
- removal of planning identifiers from durable outputs;
- `code_ref` and `knowledge_ref` linkage on every task, so the bundle stays validatable while it is live.

Checked boxes do not make a plan complete; a consistent durable repository and passing checks do. Implement never archives the bundle.

**After implementation.** `/devspark-verify` produces proof and closes out the work. PR creation, PR review, and site audit then judge the Git diff, current code, test evidence, current knowledge, and the constitution, not prose written earlier. See [Review and Audit](../guides/review-and-audit.md).

**At release.** `/devspark-release` derives the release from the previous tag through HEAD, verifies the durable delta, writes notes, and is the sole skill that archives completed, linkage-verified bundles under `.archive/{YYYY-MM-DD}/` with a journaled, non-overwriting archive step, and reports anything ambiguous for a decision. A bundle can stay live across more than one release.

Knowledge is mutated in place, never archived; Git keeps earlier versions. For what counts as knowledge and how it stays current, see [Knowledge](../guides/knowledge-management.md) and [Philosophy](../why/philosophy.md).

## Recovery

- **Verification failed:** fix the durable outputs and rerun; the bundle stays in place.
- **Completed plan still exists:** rerun `/devspark-implement` finalization.
- **Plan archived too early:** copy it back from `.archive/{YYYY-MM-DD}/` by hand (no skill reads `.archive/`) or use Git, then re-archive after verification.
- **Prior rationale needed:** inspect Git history. Do not add a history node to `.knowledge/`.

## Human control

Agents may analyze and prepare changes autonomously while running skills, but branch creation, external publication, commits, tags, pushes, and destructive operations keep explicit confirmation boundaries.
