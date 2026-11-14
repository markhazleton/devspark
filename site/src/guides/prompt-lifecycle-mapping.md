# Skill Catalog

Every `/devspark-*` skill in one place. Names below are the exact slash commands to type.
Start with the at-a-glance tables; the lifecycle detail
further down is the maintainer-level reference and a companion to [Philosophy](../why/philosophy.md).

## Terminology

| Term | Meaning | Example |
|---|---|---|
| **Skill** | A reusable DevSpark capability that defines a workflow | The `/devspark-specify` skill |
| **Slash command** | The exact text you type in chat to invoke a skill | `/devspark-specify Add a login page` |
| **Agent** | The AI coding assistant that follows the skill's instructions and performs the work | GitHub Copilot, Claude Code, or Codex |
| **Prompt** | Instruction text supplied to the agent, either by you or by a skill | A bootstrap request or the instructions behind `/devspark-specify` |

Use **skill** when naming a DevSpark capability and **slash command** when explaining how to invoke
it. A skill is not an agent; it supplies instructions to the agent. **Command** alone refers to
terminal commands or a platform's technical command format, not another name for a DevSpark skill.

GitHub Copilot packages these capabilities as native **Agent Skills**. Other agents expose the same
capabilities through their own command or prompt entry points. This packaging difference does not
change the user-facing skill names. Directory and file names, including `.devspark.work/`,
`commands/`, and `prompts/`, describe storage, not invocable skills.

## At a glance

### Normal path

Understand, implement and verify, deliver. These are the only skills a typical change needs.

| Skill | Use it to |
|---|---|
| `/devspark-specify` | Understand new work and start the single implementation path |
| `/devspark-next` | Detect where you are and run the single next step |
| `/devspark-implement` | Change code, tests, and current knowledge together |
| `/devspark-verify` | Produce proof and close out the work |
| `/devspark-create-pr`, `/devspark-pr-review`, `/devspark-address-pr-review` | Open, review, and fix a PR: [Review and Audit](review-and-audit.md) |
| `/devspark-release` | Seal the release and archive finished planning work |

### Optional when justified

Use one of these only when a specific uncertainty, coordination need, or risk earns it. None is a stage, and none triggers another.

| Skill | Use it to |
|---|---|
| `/devspark-plan` | Record a material design or contract decision |
| `/devspark-tasks` | Coordinate dependencies, parallel ownership, or work that spans sessions |
| `/devspark-critic` | Challenge one named concern about the real system |
| `/devspark-analyze` | Check one named consistency or knowledge-reference concern |
| `/devspark-quickfix` | Keep a WHAT/WHY/HOW record for a defect you have already diagnosed |
| `/devspark-update-pr` | Refresh an open PR description after more commits |
| `/devspark-closeout` | Re-decide completion without re-running verification (advanced; `/devspark-verify` normally does this) |

### Existing v9.3 specifications

These keep their recorded behavior for a specification bundle created before v9.4. On a work branch they never create a specification or a gate document.

| Skill | Use it to |
|---|---|
| `/devspark-clarify` | Resolve underspecified areas in an existing `spec.md`; on a work branch, ask the material questions in conversation |
| `/devspark-checklist` | Test whether the written requirements are clear and complete; on a work branch, answer one named concern in conversation |
| `/devspark-planning-review` | Run the planning gate on an existing full specification; on a work branch, Judge runs only for a genuine conflict: [Planning Review](planning-review.md) |

### Knowledge and governance

| Skill | Use it to |
|---|---|
| `/devspark-explain` | Trace "how is X done?" against code and knowledge, fixing drift: [Knowledge](knowledge-management.md) |
| `/devspark-discover-knowledge`, `/devspark-context-projection`, `/devspark-migrate-knowledge-entities` | Find knowledge gaps, inspect the knowledge graph, or adopt the entity layout |
| `/devspark-constitution`, `/devspark-discover-constitution`, `/devspark-evolve-constitution` | Create, discover, and amend project principles: [Constitution Guide](constitution-guide.md) |
| `/devspark-site-audit` | Audit the whole repository against the constitution and knowledge |

### Optional and operational

| Skill | Use it to | Opt-in? |
|---|---|---|
| `/devspark-add-application`, `/devspark-list-applications`, `/devspark-validate-registry`, `/devspark-migrate-registry` | Manage a multi-app registry: [Monorepo Guide](monorepo-guide.md) | Yes, via a registry file |
| `/devspark-workitem-review`, `/devspark-workitem-create` | Read and write Azure DevOps work items: [Azure DevOps](azure-devops-work-tracking.md) | Yes, via `work_tracking` config |
| `/devspark-personalize` | Customize a skill's prompt for yourself only; the copy lives in `.devspark.work/{git-user}/commands/` | Yes |
| `/devspark-upgrade` | Check for stale framework files: [Upgrade](../get-started/upgrade.md) | No |
| `/devspark-repo-story`, `/devspark-commit-audit` | Narrate the commit history (saved under `.knowledge/guides/repo-story/`) or analyze commit patterns, DORA metrics, and AI adoption | No |
| `/devspark-taskstoissues` | Explains why temporary tasks are not exported as issues | No |
| `/devspark-merge-from-main` | Script-first merge of remote `main` into the current branch; the agent only resolves conflicts | No |

Optional capabilities are never required for a first evaluation, and they have no effect on a
single-app repository that does not turn them on.

## Invocation format

DevSpark 9.0 invokes every skill with its full hyphenated slash command, exactly as shown, for example `/devspark-specify`, `/devspark-clarify`, or `/devspark-plan`. GitHub Copilot installs each one as a native Agent Skill (`.github/skills/devspark-<command>/SKILL.md`); other agents install entry points with the same hyphenated names in their own platform directories. Short names and the retired 8.x dotted form are not aliases. See [Upgrading from 8.x](../get-started/upgrade.md#upgrading-from-8x).

New work follows one start/resume path; existing v9.3 specification bundles retain their recorded stages and obligations.

## Lifecycle detail

Each skill grouped by lifecycle phase, with what the lifecycle requires of its purpose beyond its
one-line description.

## Universal start and existing planning capabilities

| Skill | Current behavior |
|---|---|
| `/devspark-specify` | Starts new work without route classification or a planning bundle. It establishes the outcome, inspects relevant code/tests/Knowledge, performs lightweight assurance discovery, offers work-item grounding only for a developer-named item when tracking is configured, and creates a `work` branch with no file by default. A minimal `work.md` exists only when needed to preserve material context across sessions. DevSpark no longer creates new full-spec or quick-spec bundles; existing bundles continue. |
| `/devspark-clarify` | Retained for existing v9.3 specifications. On a work branch it asks at most five material questions in conversation, creates no `spec.md`, and records an answer in `work.md` only when it must survive the session. |
| `/devspark-plan` | Retained for active v9.3 bundles and available on request when a material design or contract decision needs a durable record. Not a new-work prerequisite. |
| `/devspark-tasks` | Retained for active v9.3 bundles and optional coordination where dependencies or parallel ownership justify a task list. |
| `/devspark-analyze` | Validates that every id and relation named in `context_resolved` actually resolves against the current knowledge corpus — flat documents, entities, entity layers, and decisions alike. Mechanical, hard-stop — a stale or hallucinated reference fails outright. It also reports a Plan whose mechanism contradicts a decision or declared behavior recorded in the spec, without proposing a redesign. |
| `/devspark-critic` | Judges whether `context_resolved` is *sufficient* for the delta being planned — not whether it resolves (analyze's job), but whether something the spec obviously touches was never resolved at all. Judges coverage, never which kinds appear. Also flags a proposed new mechanism when a closer existing implementation would do. Judgment-based, not a hard stop. |
| `/devspark-checklist` | An ephemeral planning aid for existing v9.3 specifications. On a work branch it writes no checklist file and no gate document; it answers one named concern in conversation. |
| `/devspark-planning-review` | Retained for active v9.3 bundles or invoked for a specific planning concern. Not a default pre-implementation sequence for new work; existing Judge and freshness behavior is unchanged. |
| `/devspark-quickfix` | Retained as a direct legacy entry point. `/devspark-next` no longer asks developers to choose it over Specify. |
| `/devspark-roadmap` | Optional product-direction planning. It maintains right-sized Prospective Specs but never starts delivery or adds a gate: [Roadmap Guide](roadmap-guide.md). |

### Planning Review in one place

New work follows `/devspark-specify` → `/devspark-implement` ↔ focused verification → `/devspark-create-pr` → `/devspark-pr-review`. Existing v9.3 bundles retain `/devspark-plan` → `/devspark-tasks` → `/devspark-planning-review` → `/devspark-implement` and all recorded obligations. Closeout remains inside `/devspark-verify`. Judge does not discover or remediate; each adjudicated concern still cites its existing child finding. Four finding terms stay separate:

| Term | Meaning |
|---|---|
| **classification** | The finding's convergence state: `blocking-defect`, `accepted-limitation`, `deferred-work`, `learning` |
| **resolution** | The smallest valid remediation choice: `require`, `simplify`, `accept`, `defer` |
| **route** | A later phase (`/devspark-verify`, `/devspark-closeout`, `/devspark-pr-review`) owns the proof. A routed obligation is still part of this spec's completion — it is not deferred |
| **future work** | A real discovery intentionally removed from scope, preserved outside the spec as a Future Work Plan. DEFER is a disposition, not a task status |

Judge does not discover and Judge does not remediate. Only `require` and `simplify` become planning tasks. Create PR means DevSpark believes the spec is complete: a pull request represents completed spec work offered for acceptance, and merge terminates the spec lifecycle. It also means DevSpark believes the committed revision is complete, internally consistent, and ready for other people to review: the deterministic checks it can run against the pushed HEAD (generated Knowledge matches that commit, and no Knowledge entity the PR touches is stale) must pass, and a known failure stops it. PR Review independently evaluates a change that already claims readiness; it is not completion detection, and it re-checks the same Knowledge state read-only.

### Acceptance planning and the Tests pillar

When independent acceptance validation is warranted, `/devspark-plan` creates one conditional, ephemeral `qa-acceptance.md` in the spec bundle: Given/When/Then scenarios traced to the spec, a free-text surface, an automated, manual or hybrid runner, and a regression disposition (`add`, `update`, `retire` or `none`). Absence is valid. No new skill, stage or gate is involved.

| Skill | Role |
|---|---|
| `/devspark-tasks` | Derives only Tests work that can finish before the PR, and never assumes every change adds tests. |
| `/devspark-implement` | Applies the planned durable Tests delta: add, update or retire, plus a durable manual-regression reference where planned. |
| `/devspark-analyze` | Checks scenario trace validity, scope, and uncovered external success criteria. |
| `/devspark-critic` | Challenges scenario quality and proportionality. |

PR review does not read the acceptance artifact; it judges the Tests delta from the durable diff.

Tests are a durable pillar beside code and knowledge: every behavior change considers its Tests impact, and the regression baseline is curated rather than only accumulated. The spec owns defining and preparing acceptance; post-deployment QA execution is outside spec completion, and a failure there creates new work.

## Implementation — applies the delta

| Skill | Current behavior |
|---|---|
| `/devspark-implement` | Carries the heaviest discipline: (1) consumes `context_resolved` as already-resolved context and takes at most **one additional hop** itself — escalation past that hop is logged and attributable, not silent; (2) updates code and knowledge together in one pass, preferring test evidence over code-only evidence, recording `test_attempted`/`fallback_reason` when it falls back; (3) records each test run so later review can reuse valid evidence instead of re-running it; (4) never writes a spec, task, or plan identifier into code, tests, or `.knowledge/`; (5) never archives the spec package itself — it stays live under `.devspark.work/` so `/devspark-release` can later archive it once it is marked `Complete`. |

## Validation — carries assimilation forward, enforces the permanent record

| Skill | Current behavior |
|---|---|
| `/devspark-pr-review` | The primary assimilation trigger — nothing merges without it. §6 (Durable Delta Consistency) tracks ID-tracked findings, each blocking under its own stated rule: `PRD1` code/knowledge contradiction, `PRD2` unsupported knowledge claim introduced by the diff, `PRD3` insufficient test depth, `PRD4` planning-identifier leak, `PRD5` knowledge completeness (significant new/changed behavior touching no `.knowledge/` node at all). Named `PRD` rather than reusing site-audit's `DELTA`/`KNOW` prefixes, since the two skills check the same class of thing at different scope and should never be ambiguous read side by side. §6c judges the diff's touched entities from content at the PR head commit — a missing required layer doc or a `source_of_truth` that points nowhere blocks — never regenerates Knowledge and never judges derived index files, and surfaces as non-blocking warnings missing `fallback_reason` entries and contradiction candidates among graph-adjacent objects touched by the diff. Testing validation is evidence-first: it reuses a valid Test Evidence Record and runs tests itself only on a named trigger (no valid record, high-risk delta with author-only evidence, a repository policy, or behavior the evidence did not exercise). An existing review continues as a terminal UPDATE that evaluates submitted corrections and relevant intervening changes, then stops without initial-review discovery. |
| `/devspark-address-pr-review` | Unchanged in mechanism (commit isolation between fixes and review-file updates), but fixes remain subject to rule 1 — a fix that patches code must not introduce a spec/task reference to explain what review comment it addresses. Under `--auto` it selects only open critical/high or blocking PR-delta findings; ordinary Medium/Low findings are reported, constitution findings route to `/devspark-evolve-constitution`, and a suggested fix is evidence, so anything beyond the approved Plan's shape stops for explicit authority. |
| `/devspark-create-pr`, `/devspark-update-pr` | Surface evidence and readiness in the PR description itself — the test evidence record (or why none applies) and the Knowledge readiness result (`ready`, `not-applicable`, `unknown` or `blocked`) — so a human reviewer sees the checklist state without digging for it. |
| `/devspark-verify` | The evidence mechanism's engine. Its purpose — produce empirical proof-of-change evidence for declared verification modes, not document review — is the `verified_by: execution` discipline in practice: it runs cited tests and produces the pass/fail result written into a knowledge object's or decision's evidence entry. Records a `test_ref: <path>::<test name>` pointer alongside any mode passed via a named test — the citable reference `/devspark-implement` needs, captured where the proof actually ran. Selects its verification modes from the shape of the change rather than applying one fixed depth, and states which shapes it matched. |
| `/devspark-closeout` | Decides whether the route is finished, and runs automatically inside `/devspark-verify` — it is an optional, advanced re-entry point, not a normal-path step. Applies the convergence rule: a spec completes when its stated objective is resolved and every remaining finding is classified, not when every observation generated along the way has been eliminated. Classifies each open finding as Blocking Defect, Accepted Limitation, Deferred Work, or Learning / Changed Assumption — only the first creates mandatory work inside the active route, and an unclassified finding is itself blocking. Reads each acceptance criterion by its declared kind (`requirement`, `invariant`, `hypothesis`, `target`; undeclared reads as `requirement`), so a disproven hypothesis records as a result rather than a defect — while a failed requirement or violated invariant can never be relabelled into a softer kind once the evidence is in. |
| `/devspark-site-audit` | Repo-wide, not diff-scoped. Runs the accuracy pass (resolve every `execution`-type evidence entry and re-run its test — existence and accuracy are separate reports) and the contradiction scan, scoped to graph-adjacent objects (same entity, entities sharing a `constrains` decision, objects citing the same evidence) rather than brute-force comparison. Contradiction findings are warnings for human review, always — never a gate. **Also the repo-wide knowledge-completeness owner**: runs `build_knowledge_index.py --check` (stale index/coverage is `KNOW1`), reads the full `ontology/coverage.json` for every entity (`KNOW2`), confirms every `appliesTo`/`source_of_truth` path still exists (`KNOW3` — the knowledge/code mapping-accuracy check), resolves every `relations[].object` and `constrains`/`constrained_by` pair (`KNOW4`), and cross-checks `taxonomy-registry.json` plus central-module coverage (`KNOW5`/`KNOW6`) — the repo-wide counterpart to pr-review's diff-scoped §6c gate. |
| `/devspark-explain` | Topic-scoped, read-only by default. Grounds its answer and findings in current code and tests. Only a developer-requested Knowledge correction or draft may be written after its own explicit approval; saving a trace needs separate approval. Confirmed code defects route to Quickfix and missing behavior to Specify. Discovery never creates work. |
| `/devspark-taskstoissues` | Already fully aligned — its entire purpose is explaining why ephemeral tasks don't get exported as durable records, which is rule 1 stated as a user-facing explanation rather than an enforcement mechanism. |

## Governance & framework — constitution, framework lifecycle

| Skill | Current behavior |
|---|---|
| `/devspark-constitution` | The constitution is one of three current-truth categories, not documentation, and dependent templates being kept "in sync" includes the `.knowledge/governance/decisions/` contract, not just prose templates. |
| `/devspark-discover-constitution` | Unchanged in mechanism — discovering implicit patterns is a different activity than maintaining the current-truth categories. |
| `/devspark-evolve-constitution` | A constitution amendment that contradicts an existing current decision must trigger updating that decision in place, not leaving two governance documents making incompatible claims — the same one-current-file-per-topic rule extended to the constitution/decision boundary. |
| `/devspark-release` | Archives only bundles marked `Complete` and leaves in-flight ones where they are; legacy `code_ref`/`knowledge_ref` fields are ignored. Also requires a current site-audit knowledge result (`KNOW1`–`KNOW6` clean) for the window, and that the `.knowledge/` tree builds (`KNOWLEDGE_BUILDS`). |
| `/devspark-commit-audit`, `/devspark-repo-story` | Read Git history, not the repo's current-truth layer — naturally exempt from current-truth-only, since Git is explicitly where history is supposed to live. |
| `/devspark-upgrade` | A framework-version concern, orthogonal to the knowledge model. Mentions `/devspark-migrate-knowledge-entities` as an optional follow-up after a four-root migration, since that migration only moves directories and never touches document content. |

## App/framework operations — unaffected

`/devspark-add-application`, `/devspark-list-applications`, `/devspark-migrate-registry`, `/devspark-validate-registry`, `/devspark-personalize`, `/devspark-next` — these
manage the multi-app registry and framework mechanics, not the knowledge/spec lifecycle. `/devspark-next` stays
aware of the gate order (`/devspark-plan` → `/devspark-tasks` → `/devspark-planning-review` → `/devspark-implement`, with `context_resolved`
threaded through `/devspark-analyze` and `/devspark-critic`) when it decides what the next skill is.

`/devspark-migrate-knowledge-entities` — alongside the entity-ontology. Drives
`scripts/migrate-knowledge-to-entities.py` to move existing flat `.knowledge/` docs into
`entities/<id>/` folders, then rebuilds the index. Optional and human-confirmed, same as
`/devspark-migrate-registry` — never runs automatically and no other skill depends on it.
