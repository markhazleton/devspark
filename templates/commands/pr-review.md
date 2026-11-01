---
source: "DevSpark — © 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com"
description: Perform constitution-aware pull request review with actionable feedback for any PR in the repository
handoffs:
  - label: Address Current Findings
    agent: devspark-address-pr-review
    prompt: Address the current unresolved review findings.
scripts:
  sh: .devspark/scripts/bash/get-pr-context.sh $ARGUMENTS --json
  ps: .devspark/scripts/powershell/get-pr-context.ps1 $ARGUMENTS -Json
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Overview

Load and obey the shared preamble contract core at `/.devspark/templates/command-preamble-contract.md` (installed repos) or `templates/command-preamble-contract.md` (source repos) before step 1 — in particular §9 (Genuine Fix Discipline) when reviewing a PR that claims to resolve a lint/test/code-smell finding. Preamble modules: `finding-fix`, `convergence`, `provenance`, `configuration`.

This command reviews the durable Pull Request delta against current code, tests, `.knowledge/`,
published documentation, and the constitution. It works for any PR regardless of how the change was
planned. One replaceable working report is stored at `/.devspark.work/pr-review/pr-{id}.md`; Git and
the hosting platform are the sole review history.

**IMPORTANT**: This command **only provides suggestions** - it does not make any code changes.

Reviews are advisory. The agent must explain constitution or lifecycle issues, recommend a disposition, and let the human decide the next action.

Planning artifacts are neither required nor valid review evidence. Missing plans are normal. Do not
recover, recreate, inspect, or score them; review the resulting delta.

## Prerequisites

- Project constitution at `/.knowledge/governance/constitution.md` (REQUIRED)
- A hosted repository with PR context (GitHub or Azure DevOps)
- Platform CLI installed and authenticated — `gh` for GitHub, `az` (with the `azure-devops` extension) for Azure DevOps (required). The host is resolved automatically from `.devspark.work/devspark.json` → `platform` or the `origin` remote; `{SCRIPT}`/get-pr-context handle PR detection per platform.
- **HARD RULE — Branch Sync**: The source (head) branch **MUST** be fully in sync with the target (base) branch. Do **NOT** proceed with review or approval if the source branch is behind the target. Instruct the user to rebase or merge the target branch into the source branch first.

## Definition of Done

Done when: the report is written to `/.devspark.work/pr-review/pr-{PR_NUMBER}.md` (step 9) and the step-10 chat summary is printed. The execution limits in §1 (max 20 findings, max 25 files, "stop once evidence is sufficient") are the convergence condition for the analysis itself — don't expand scope beyond them speculatively. Chat output is the step-10 template only; the full report (all tables, all sections) lives in the file — don't re-paste it into chat.

## Outline

Multi-app scope and the 2-tier override check for scripts are defined by the shared preamble contract already loaded above.

### 1. Initialize Review Context

Run `{SCRIPT}` to extract PR context and parse JSON output for:

- `PR_CONTEXT`: PR metadata (number, title, branches, commit SHA, files, diff)
- `CONSTITUTION_PATH`: Path to constitution file
- `REVIEW_DIR`: Directory where review will be saved

Treat script JSON as bounded context:

- `files_changed` may be sampled for large PRs.
- Use `files_changed_total` and `files_changed_truncated` to decide whether to zoom in further.
- Do not expand to all files unless user explicitly requests a full exhaustive review.
- `unmapped_files` (changed files matching no `.knowledge/` node's `appliesTo` pattern) is a
  computed hint for §6 `PRD5`, not itself a finding — see that step for how to use it.

Execution limits (required):

- Max findings in report: 20 highest-signal items
- Max files to inspect deeply: 25
- Max follow-up searches/reads beyond provided context: 8
- Stop once evidence is sufficient for high-confidence conclusions
- **Time budget**: an ordinary review (`short` or `standard` report form, no escalation trigger in §5 Testing Validation) should finish in about 2–5 minutes: read the PR context, read P0/P1 diffs, judge existing evidence, write the report. Larger or high-risk deltas legitimately take longer — say so in the Executive Summary rather than cutting a check. Never approve an incompletely reviewed change to meet the budget.
- If confidence is low for a specific area, ask one clarifying question
- `PR_CONTEXT.risk` carries the per-file tiers, rating, and `report_form`; when `report_form` is
  `short`, spend no more than P0/P1 reads and skip additional-dimension scans (§5) that no risk
  flag or finding calls for
**Iteration Detection**:
Before running a full review, check whether the user's input contains iteration keywords: "update", "re-review", "check my fixes", "revised", "changes made", "addressed". If detected:

1. Load the existing review file and inspect its `review_state` through `scripts/pr-review-state.py`.
2. Preserve every canonical identity, alias, original concern, evidence, disposition, and historical outcome. Never infer closure from a changed diff, author fix, or unchecked/checked legacy status.
3. Evaluate only each submitted correction against its original expectation and directly affected behavior. Do not restart unrelated discovery for a focused UPDATE.
4. Record the reviewer context, role, actual proof performed, evidence, conclusion, correction commit, and evaluated commit. The evaluator must be distinct from the remediation author's actual execution context under the existing reviewer arrangement; changing a role label does not establish independence.
5. Use the shared engine to apply the result, render all derived views, and validate the same resulting revision. If no distinct evaluator or required proof is available, retain pending verification and state what is missing.
6. Add a newly legitimate concern only when directly observed in the bounded scope. Preserve existing governed accepted/deferred/withdrawn decisions and retain earlier outcomes in Git history.
7. Do not cast a hosted approval vote or authorize merge. This bounded UPDATE is the closeout
   operation; do not require an additional reconciliation command or normalization-only cycle.

**PR Number Detection**: an explicit `#123`/`123` argument, then `GITHUB_PR_NUMBER`/`PR_NUMBER`, then `gh pr view` for the current branch; otherwise ask for the number.

**Script failures**: constitution missing → `/devspark-constitution`; `gh` missing or unauthenticated, or PR not found → say what to fix (`gh auth status`, PR number). **Branch out of sync** (`is_behind_target: true`): **STOP.** Do not review or approve; tell the user the source branch is behind the target and to run `gh pr update-branch {PR_NUMBER}` or `git fetch origin && git rebase origin/{target_branch}`.

For single quotes in args like "I'm reviewing", use escape syntax: e.g 'I'\''m reviewing' (or double-quote if possible: "I'm reviewing").

### 1b. Delta Boundary Classification

Classify the PR only by changed durable paths and risk. Identify production code, tests,
`.knowledge/`, infrastructure, generated files, and temporary `.devspark.work/`
artifacts. A PR's own `.devspark.work/` planning bundle (the spec/plan/tasks/gates for the feature
this PR delivers) is expected to ride in the diff — `command-preamble-contract.md` §0 documents
that the bundle stays live under `.devspark.work/` through merge and is archived only later, by
`/devspark-release`. Do not flag that as a scope finding, and never use its presence or absence to
adjust trust. Only flag `.devspark.work/` content that is genuinely unrelated to this PR's own
feature (e.g. an unrelated bundle's files caught up by an errant `git add`, or files whose
`spec_path`/feature id doesn't match this PR's source branch) as a scope finding.

### 2. Load Constitution

Read and parse `/.knowledge/governance/constitution.md`:

- Extract all core principles with their names
- Identify MUST requirements (non-negotiable/mandatory)
- Identify SHOULD requirements (recommended)
- Note constitution version and amendment date
- If `.knowledge/governance/severity-registry.md` exists, load it and use its `§{section}.{LEVEL}` entries to validate finding codes when emitting findings
- Build a checklist of principles to evaluate

If constitution doesn't exist:

- **STOP** and inform user that constitution is required
- Provide guidance: "Run `/devspark-constitution` to create project principles first"
- Do not proceed with review

### 3. Analyze PR Changes

Using the PR_CONTEXT data from the script:

#### A. Risk-Tiered File Triage

The script has already tiered every changed file. Use `PR_CONTEXT.risk` as the source of truth;
do not re-derive tiers, flags, or the score by reading paths.

- `risk.files[]` — `path`, `tier` (P0–P3), `delta_class`, and (when available) `added`/`deleted`/`change`;
  `promoted_by` names the domain or integration entity (from `.knowledge/`) that made a file P0
- `risk.rating`, `risk.risk_score`, `risk.factors[]` — the auditable floor for risk; an
  `unmapped_production` factor means changed production code no knowledge node claims (a PRD5 lead)
- `risk.report_form` — `short`, `standard`, or `full` (see §7 Report Forms)
- `risk.tables.changed_files` and `risk.tables.test_files` — ready-made markdown, paste verbatim

Review depth by tier:

| Tier | Meaning | Review Depth |
|------|---------|--------------|
| **P0** | Auth, routes/handlers, middleware, data access, schema, infra | Full line-by-line review |
| **P1** | Business logic, domain models, integrations (the default) | Function-level review |
| **P2** | Tests, config, scripts, build files | Spot-check only |
| **P3** | Documentation, markdown, generated content | Scan for obvious errors |

Tiers are a floor. If a file the script placed in P1 is demonstrably critical (it gates safety, money,
access, or data integrity), review it as P0 and say so in the Executive Summary. Never lower a tier
or the rating. When `PR_CONTEXT.risk` is null, assign tiers yourself using the table above.

Per file:

- Read the diff at the depth its tier requires
- Identify the type of change (new file, modified, deleted) and its scope

Prioritization policy:

- Always start with P0 files regardless of context budget
- Do not read the diff of P3 files unless a finding needs it; the script's counts suffice
- If `files_changed_truncated` is true, limit P2 to a quick scan and focus on P0/P1
- Expand beyond sampled files only if necessary to validate a top-severity finding

#### B. Examine PR Diff

Identify new, removed and modified behavior, and separate refactoring from feature change. Take churn stats (`lines_added`, `lines_deleted`) from `PR_CONTEXT` for the Stats section on every revision. Read commit messages only for intent and breaking-change indicators.

### 4. Perform Constitution-Based Review

Start the review with a gate result block:

```yaml
gate: pr-review
devspark_version: "<installed version, or `unknown`>"
generated: "<ISO-8601 timestamp of this run>"
status: pass | warn | fail
blocking: true | false
severity: info | warning | error | showstopper
summary: "<concise outcome>"
```

For **each principle** in the constitution:

#### A. Compliance Check

Review changed files against the principle; decide violates, partially complies or fully complies, with file, line and snippet evidence.

#### B. Severity Classification

Assign severity from demonstrated impact and consequence, not from whether the issue blocks. A binding non-waivable obligation stays blocking regardless of its severity label; HIGH or CRITICAL severity alone does not establish a blocker. Decide blocking separately, from the obligation and the validated finding state. Accepting a waivable limitation requires a named, authorized human and a reason; silence is never approval.

Each finding quotes the code, cites the exact constitution section, says why it is an issue, and gives a specific, actionable recommendation.

#### C. Finding Legitimacy Check (required before any numbered finding)

Severity inflation is the reviewer-side mirror of a gamed fix (§9, Genuine Fix Discipline): both
swap a surface signal — a clean metric there, a superficially alarming pattern here — for the
behavioral question the check exists to answer. Failing a test relocates the finding to a
lower-friction form (see destinations); it does not authorize an inflated severity to stand.

A concern is only a **candidate** until it passes this check; only validated concerns become
numbered findings (internal reasoning: no artifact, no extra pass). A true observation is not
necessarily a defect.

**Basic legitimacy — every numbered finding, including Low.** It needs a concrete observation, a
violated expectation (requirement, invariant, contract, documented intent, or engineering
obligation), relevance to *this* PR, and a correction that belongs in this PR. Behavior that matches
approved intent, is merely surprising, or is unrelated inherited debt is not a defect: record it
under `### Observations` (§7) with no ID and no severity.

CRITICAL, HIGH, and MEDIUM findings must also pass the tests below (Test 5: behavioral claims only).

1. **Intent** — An approved, documented design decision is not a defect. If the PR context, the
   constitution, or `.knowledge/` shows the behavior was deliberately chosen and signed off (not
   merely unremarked), disagreeing with that decision is at most a `CON-NN` finding proposing a
   governance amendment, or no finding at all. A defect in *how* an approved intent was
   implemented is still fair game at full severity.
   - Standing example: a service refusing to start on incomplete configuration is the contract,
     not a risk to be flagged.
2. **Actionability** — The finding must name a concrete change to the diff. If the only available
   remediation is "confirm / verify / coordinate with / ensure before deploy," it is not a code
   finding — move it to the report's **Deployment Notes** section, not a Findings Detail table.
3. **Ownership** — If remediation is outside the PR author's control (DevOps sequencing, product
   sign-off, an upstream team's change), it is a handoff, not a finding against the author — move
   it to the report's **Handoff Notes** section.
4. **Self-consistency** — A row in the Behavioral Changes table marked `Intentional? Yes` cannot
   itself back a CRITICAL or HIGH finding. If the same behavior also has an implementation defect,
   name that defect explicitly and cite it, separately from the intentional-change row.
5. **Consumer trace** (behavioral concern at MEDIUM or higher) — Name the reader of the changed
   value and show that *this* instance can reach the claimed consequence, using the nearest
   evidence (consumer, caller, callee, helper, existing test, runtime condition, design note),
   including whatever nearby evidence would prove the concern wrong. Not exhaustive tracing. If it
   disproves the concern, drop it (an Observation if useful) — do not keep a defeated concern at
   lower severity. If the consequence cannot be established, it is an unconfirmed risk: label it,
   never block on it, never rate it above Low. Uncertainty alone is not evidence of a defect.
6. **Attribution** — When the issue is not obviously introduced by this PR, say in prose whether
   it is *introduced* (normal finding), *exposed* (judge materiality), *pre-existing but material*
   (the PR depends on it, expands its risk, or leaves the change unverifiable — may block), or
   *pre-existing and unrelated* (never blocks; Observation or deferred work). Pre-existing is never
   automatically ignorable.

An item that fails Test 2 or 3 is not discarded — it is relocated so the question stays visible in
the report, just not as a finding against the author. An item that fails basic legitimacy or Test 1
is dropped, recorded as an Observation, or recast as `CON-NN`. If a finding of this kind was already
emitted in a prior revision, withdraw it per the Iteration Detection rule above rather than
deleting it.

#### D. Generate Findings

Create structured findings with **stable IDs** that persist across re-reviews. Use zero-padded identifiers so status changes across revisions instead of being deleted:

- **ID**: Stable identifier with zero-padded number. The prefix maps to severity tier:
  - `C-NN` = Critical
  - `H-NN` = High priority
  - `M-NN` = Medium priority
  - `L-NN` = Low priority
  - `CON-NN` = Constitution (code may be correct; governance needs updating)
- **Status**: `🔴 Open` | `✅ Resolved` | `⚠️ Partial` | `➡️ Carried` (for re-reviews) | `🚫 Withdrawn` (failed the Finding Legitimacy Check after being emitted; kept with a one-line reason, never deleted)
- **Principle**: Name of constitution principle
- **File:Line**: Exact location in code
- **Issue**: Specific description of the problem, including broken code snippet for CRITICAL/HIGH
- **Fix**: Concrete code fix for CRITICAL/HIGH findings (required); recommendation for others.
  State the defect, then the required outcome, then the least-complex sufficient correction first —
  a risk does not prescribe architecture. Discovery alone does not make work mandatory: classify
  what is found as a blocking defect, accepted limitation, deferred work, learning, or observation.

### 5. Additional Review Dimensions

#### Security Analysis

Check for hardcoded secrets, missing input validation, wrong authentication/authorization, unsafe queries (SQL injection), unescaped web output (XSS), and newly added dependencies. Report a security concern only when one is found: name it and the file. Otherwise the Executive Summary count is enough.

#### Behavioral Regression Detection

Scan the diff for silent behavioral changes that may break callers or remove safety guarantees: changed default parameter values (including a required argument that gains a default), changed return types (including a new implicit `None`), and removed defensive code.

**Removed Defensive Code (4-Step Verification)**:
Before flagging a removed safety guard, complete all 4 steps:

1. **Identify the guard**: Quote the removed code and describe what it was protecting against
2. **Check if condition can still occur**: Determine whether the protected scenario is still possible based on what is observable in the PR diff and the PR context script output — do not speculate about runtime state not visible in the provided context
3. **Check if protection moved elsewhere**: Search the PR diff for equivalent protection at a different layer (middleware, validator, caller site)
4. **Flag only if genuinely removed**: Only create a finding if steps 2 and 3 confirm the protection is missing and the risk remains real

Include behavioral regression findings in the Critical or High section as appropriate. A behavioral
finding at MEDIUM or higher must also pass §4C Test 5 (consumer trace).

If the constitution has code-quality principles, also check naming, code organization and error handling against them.

#### Accidental Complexity & Duplication Review

Evaluate whether avoidable accidental complexity remains in the diff, rather than merely certifying that the implementation followed a plan:

- **Architectural fitness**: For changes with material design, state, persistence, compatibility,
  or data-integrity impact, inspect the changed code for coupling across established
  responsibilities, blurred responsibilities, duplicated behavior or parallel mechanisms,
  unnecessary abstractions, accumulating conditional complexity, fragile state, and hidden
  temporal or persistence assumptions. Passing functional tests is evidence for the behavior they
  exercise; it does not establish that historical evidence, compatibility, or data integrity is
  preserved outside those tests.
- **Change sensitivity**: Consider at most one or two reasonably foreseeable next changes only
  when grounded in current contracts, observed consumers, established domain behavior, or other
  concrete repository evidence. Explain how the changed design would make that change unnecessarily
  difficult. Do not invent future requirements or treat hypothetical flexibility as an obligation.
- **Material finding threshold**: A numbered architectural finding must cite the actual changed
  code, name the applicable expectation or demonstrated engineering obligation, explain a concrete
  consequence on this PR's path, and recommend the smallest justified correction within the Delta's
  blast radius. Apply §4C legitimacy, attribution, and validated-blocking rules unchanged. A
  stylistic preference, speculative future need, or merely imperfect design is not a blocker; keep
  a useful non-defect as an Observation or omit it. Prefer local simplification when it preserves
  existing behavior and guarantees; do not redesign for architectural perfection.

- **Evaluate Proportionality**: when the diff shows duplication or complexity disproportionate to the feature, evaluate whether a simpler repository-native implementation is reasonably available. Particularly inspect:
  - **Repeated wiring**: multiple constructors, handlers, or call sites wired individually for a single behavior where an existing seam, middleware, or orchestration boundary could suffice.
  - **Redundant processing**: repeated validation, transformation, or sorting of already validated, sanitized, or ordered data.
  - **Duplicate or excessive abstraction**: new abstractions, wrappers, or helper hierarchies that duplicate established capabilities or add indirection without isolation benefit.
  - **Speculative extension**: excessive configuration options, unused flags, or speculative extension points not justified by actual requirements.
  - **Unnecessary indirection**: artificial layers or delegation chains that obscure control flow without architectural necessity.
- **Compare Alternatives Before Recommending Simplification**: compare the candidate alternative's behavior, validation guarantees, failure semantics, error propagation, and operational constraints against the current diff. A smaller implementation that drops validation guarantees or changes exception behavior is NOT equivalent and must not be recommended as a pure simplification.
- **Finding Classification for Complexity**:
  - **Blocking defect**: A validated correctness, contract, security, or maintainability defect that prevents advancement under an applicable obligation or demonstrated consequence. Severity alone does not determine blocking.
  - **Advisory (MEDIUM/LOW or Observation)**: A reasonable simplification opportunity that preserves all contract and validation guarantees without a demonstrated defect.
  - **No finding**: Complexity that is genuinely justified by actual requirements, lifecycle boundaries, or architectural constraints.
  Line count, file count, or abstraction count are NEVER automatic failure conditions. Do not turn PR review into a mandatory redesign exercise.

**Gamed-fix detection** (command-preamble-contract.md §9): when a diff claims to resolve a lint rule, complexity metric, or test failure, verify the fix addresses the underlying behavioral intent, not just the mechanical check. Branches merely moved into helpers without reducing total branching, or an `except` narrowed while the handler still swallows the error, "satisfy the check without changing behavior": raise an `H-NN` finding ("resolves the check, not the root cause"), not a style nit.

#### Testing Validation

**Evidence first; run only what the evidence does not cover.**

1. **Find existing evidence** for the reviewed commit: `FEATURE_DIR/gates/test-evidence.md`, your own earlier `## Test Evidence` in the review file, CI results for the head SHA, and any author record in the PR description.
2. **Judge each record** by the reuse rules in `verification-contract.md` §4.1 (same commit or only planning/review paths changed since, clean tree, exit 0, scope covers the changed tests). Cite a valid record by location; do not re-run what it covers.
3. **Run the scoped tests yourself** (changed test files; the full suite only when a scoped run is not possible) when any of these holds, and name the trigger in the report: no valid record covers the changed tests; the only evidence is author-reported and the delta is high-risk (security, data integrity, clinical or externally visible contracts); the constitution or a repository policy requires the reviewer's own run (including when CI does not run the tests); or the diff changes behavior the evidence scope did not exercise.
4. **Record** every run in a `## Test Evidence` section (§4.1 shape) and put the command, or `reused: <location>`, plus the result in the Revision Log row. On re-review, keep the command from the first row.
5. **Failing tests are an automatic HIGH finding.** Evidence you could not validate, or tests that did not run, are stated plainly as not verified; never imply a pass, and never approve on evidence you could not validate.

Also check that new or modified code has tests of adequate quality.

**Planned Tests delta** (when the spec bundle has `qa-acceptance.md`): verify proportionately that each planned `update` or `retire` was applied, from the source diff for repository-owned tests or from the durable reference for externally owned ones. Do not require a new permanent test for a `none` disposition. Never execute manual QA, require deployment, invent scenarios, or convert observations into current-spec scope.

#### Documentation Review

If the constitution requires documentation, check the README, API docs, complex-logic comments and CHANGELOG as it requires.

### 6. Durable Delta Consistency Validation

Validate the changed behavior, affected tests, and current knowledge together. This is a **strong,
blocking gate** — the primary control point on what reaches main — not an advisory note. Every item
below produces a stable `PRD{N}-{seq}` finding (e.g. `PRD1-01`), tracked in its own Findings
Detail table (§7) exactly like Critical/High constitution findings, and every open one belongs in
the Immediate Actions (Blocking) list. (`PRD` = PR Delta, distinct from `/devspark-site-audit`'s
repo-wide `DELTA{N}`/`KNOW{N}` IDs — same class of check, diff-scoped instead of repo-wide, kept
separately named so the two commands' findings are never ambiguous when read side by side.)

1. Identify the truth nodes this diff bears on with `explain-context.py --files <changed files>`
   (`.devspark/scripts/bash/explain-context.sh` or `.devspark/scripts/powershell/explain-context.ps1`
   in installed repos; read-only). It reports, per file, each node that applies to it or cites it
   through `source_of_truth`, and the unmapped files. The owners to inspect are nodes the PR touched,
   nodes citing a changed source, and nodes applying to a changed surface. Do not read the
   Knowledge corpus; read only what a claim check below needs.
   - **Build the review's applicable Knowledge context.** In addition to those file owners, use
     canonical `explain-context.py` topic retrieval for the PR's actual domain and changed
     mechanism. Treat lexical matches as seeds, not as resolved context. Where a relevant seed has
     accepted relationships, use bounded `context-projection.py` (or the existing combined
     `--project` path) and retain only candidates the code, tests, or contract show are applicable.
     Expand one evidence-led step at a time; do not scan or paste the corpus, every neighbor, or
     unrelated nodes into the report. For each retained invariant or boundary, read its authoritative
     source and cite the Knowledge path and heading; follow its code/test references only as needed.
     Prefer a concise packet of applicable invariants, architectural boundaries, contracts, and
     change-sensitive risks over an inventory of documents.
   - **Qualify Knowledge evidence.** A missing source or an uncertain claim is a limitation to resolve or disclose, not current truth. A matching retrieval result or a recent date does not prove semantic accuracy; never present an unaccepted projection candidate or unsupported inference as authoritative.
   - **Carry durable learning forward.** Identify durable architectural truths the Delta establishes
     or corrects, then compare them with the existing owning Knowledge. When the existing owner
     needs correction, recommend updating that owner in this Delta; when no owner exists and the
     behavior is durable and material, apply the conservative `PRD5` threshold below. State the
     invariant and its authoritative Knowledge reference in the report so the next relevant agent
     can find it promptly. Do not copy source code, test details, ephemeral history, or speculative
     predictions into Knowledge.
   - **Claim-targeted check.** For each owner, find the material claims describing the changed
     mechanism — especially enumerable contracts: operators, enums, state values, configuration
     keys, public fields, status codes, allowed values, defaults, endpoint behaviors, invariant
     tables. When the diff adds or changes a member of such a set, take one existing sibling and
     the new member and search each owner with a **word-bounded** match (substring matching lets
     `field_eq` hit `field_equals`). An owner that lists the siblings but omits the new member names
     a candidate section: read it and compare the claim with the implementation. A search hit alone
     proves nothing; a promoted `PRD1` rests on a claim you read.
   - **No unsupported "matches".** Do not write "Knowledge matches" or "PRD1: none" because a node was touched or looked right. For a Code ↔ Knowledge surface this PR materially changes, that conclusion must rest on claims you actually compared.
2. **`PRD1` — Code/knowledge contradiction (BLOCKING).** The diff's code or configuration
   contradicts what an existing `.knowledge/` node (flat doc or entity) claims about that behavior.
   It needs a material claim you read, that contradicts the changed implementation or required
   behavior, and that is relevant to this PR; a stale-looking node about an untouched mechanism is
   not `PRD1`. `PRD1` is semantic truth, judged from claims you read.
   Fix is either: correct the code to match an intentional, still-valid claim, or correct the
   knowledge node in the same PR to match the new, intentional behavior — never merge with the two
   disagreeing.
3. **`PRD2` — Unsupported knowledge claim (BLOCKING).** A `.knowledge/` node touched by this diff
   (new or edited) claims behavior the diff's own code and tests do not actually support — an
   aspirational or inaccurate claim introduced by this PR itself, distinct from `PRD1` (existing
   code vs. existing knowledge) because the claim is new.
4. **`PRD3` — Insufficient test depth (BLOCKING, severity by risk).** Changed durable behavior
   lacks executable coverage proportionate to its risk. Floor severity MEDIUM; escalate to HIGH for
   security, data-integrity, or public-API surface changes. Proportionate means relative to the
   changed behavior and to existing coverage at the layer that carries it: does the PR introduce
   externally observable behavior, is it already covered where a directly tested helper owns it, are
   the changed call sites simple delegation (which does not require duplicated caller tests), is a
   contract-level assertion needed to establish the actual change, or is the PR merely passing
   through unrelated historical test debt (an Observation, §4C Test 6)? `PRD3` blocks only when the
   changed behavior lacks coverage at a layer proportionate to its acceptance risk.
5. **`PRD4` — Planning-identifier leak (BLOCKING).** Durable code, tests, or
   `.knowledge/` in this diff references a spec ID, task ID, `FR-###`, plan link, gate file, or a
   path into `.devspark.work/` or `.archive/` — an archived path is just as forbidden as a live one,
   since it still points at ephemeral state. Rewrite as self-contained current truth. The inverse
   direction (an ephemeral artifact pointing at durable code/knowledge) is fine by construction and
   is not flagged.
6. **`PRD5` — Knowledge completeness for this diff (BLOCKING for architecturally significant
   behavior, otherwise a non-blocking suggestion).** The diff introduces or materially changes
   durable behavior — a new module/integration/pattern, a changed contract, a new operational
   procedure — but touches **no** `.knowledge/` node at all: neither an existing one nor a new one.
   This is the completeness half of the gate (`PRD1`/`PRD2` only catch *contradictions* between
   what's touched; `PRD5` catches behavior that should have been captured in `.knowledge/` and
   simply wasn't). The preflight JSON's `unmapped_files` list (changed files matching no node's
   `appliesTo` pattern) is a computed starting hint for this judgment — it is not itself a
   finding, since plenty of unmapped files are routine (tests, config, generated output); use it to
   focus attention, then judge significance conservatively — do not flag routine internal
   refactors, bugfixes with no behavior-contract change, or test-only diffs.
7. Confirm `.knowledge/guides/` describes only the current supported behavior (non-blocking unless a
   published page now makes a false claim, which escalates to `PRD1`).
8. Report every `PRD{N}` with direct evidence (file:line, the specific contradiction or gap) and a
   concrete repair — never a vague "knowledge may be out of date."
9. Base approval only on the durable delta, validation evidence, constitution, and unresolved
   findings — including every open `PRD{N}` finding. Missing planning artifacts are expected and
   must never substitute for or excuse an open `PRD{N}` finding.

### 6b. PR Scope Validation (Multi-App Mode)

If `.devspark.work/devspark.json` has `mode: "multi-app"`, compare the changed paths with the PR's declared scope (`single-app`, `cross-app`, `repo-scope`, with `primary_app` and `affected_apps`); with no declaration, infer it from the changed files and the registry at `.devspark.work/devspark.registry.json`. Map each file to its owning app by `app.path` prefix; `.knowledge/`, `.github/`, `.devspark/` and root config are shared paths. A `single-app` PR touching another app's path, or a `cross-app` PR touching an undeclared app, is a **HIGH** scope finding: name the files and recommend a scope update or a split. Note valid scope in the Executive Summary; add a Constitution Alignment row only when scope is partial or failing.

### 6c. Knowledge Structure & Contradiction Warnings

For every `.knowledge/entities/<id>/` this PR's changed paths map to (via `appliesTo` or a direct path
under `entities/<id>/`), judge from content, at the PR head commit (check it out or stop; never judge
Knowledge against a different commit):

1. A touched entity with a missing required layer doc, or a `source_of_truth` that points nowhere, is
   **blocking** — the same tier as a constitution violation.
2. Never regenerate Knowledge during review, and never judge a PR on whether derived index files
   (`.knowledge/index.json`, `coverage.json`) are committed or current; they are build output.
3. A code-only evidence entry (`type: code`) with no note on why a test was not used is a
   **non-blocking warning**.
4. Scan for contradiction candidates among graph-adjacent objects only (same entity, entities sharing
   a `constrains` decision, objects citing the same `source_of_truth`) — never pairwise across the
   repo. Whether a candidate is a real contradiction is a human call; surface it as a
   **non-blocking warning**.

### 6d. Closeout Consumption (review the convergence decision, don't restart it)

If the PR's planning bundle contains `gates/closeout.md`, read it. Your job here is to judge whether
the **convergence decision is defensible** — not to rediscover the route's findings from zero, and
not to treat a classified finding as unfinished work. The contract governing that artifact is
`/.devspark/templates/closeout-contract.md` (or `templates/closeout-contract.md` in source repos);
§9 of it defines exactly this exchange.

| Closeout state | Response |
|---|---|
| An `unclassified` finding remains | **`PRD6` (BLOCKING)** — the route never converged |
| A `blocking-defect` finding is unresolved | **`PRD6` (BLOCKING)** |
| A `requirement` is `not-satisfied`, or an `invariant` is violated, but the finding was classified as anything other than `blocking-defect` | **`PRD6` (BLOCKING)** — laundering, per contract §3/§4 |
| `accepted-limitation` with a real `accepted_by` | OK — do not reopen |
| `deferred-work` with a `captured_as` pointing at a record that actually exists | OK — do not reopen |
| `learning` retaining original expectation, evidence, and revised understanding | OK — do not reopen |
| `decision: complete` whose counts contradict the `findings:` list | **`PRD6` (BLOCKING)** — the arithmetic must hold |

`PRD6 — Unconverged or indefensible closeout (BLOCKING)` joins the `PRD{N}` family: stable `PRD6-{seq}` id, Findings Detail row, Immediate Actions entry.

Bounds in the other direction: **An improvement you noticed is not a reason to reopen the spec** — record it as a Recommended Improvement or route it to `/devspark-specify`. **A genuine defect still reopens the work** (failed requirement, violated invariant, correctness defect, regression from this diff): raise it under its own code and severity; a classification only immunizes a disagreement of preference, never a real defect.

**No closeout artifact** is a non-blocking note, not a finding — many routes legitimately produce none. Judge the durable delta as §6 requires and never require the author to run a command to satisfy this section.

### 7. Generate Review Report

Create comprehensive report at `/.devspark.work/pr-review/pr-{PR_NUMBER}.md`:

#### Handle Existing Reviews

If file already exists:

1. Inspect the current structured record with the shared state engine and retain all canonical
   identities, aliases, original concerns, evidence, dispositions, and prior outcomes.
2. For UPDATE, examine only the prior finding's correction and directly affected behavior unless
   the user explicitly requests a full review. Do not decide that a finding is resolved from a new
   diff, author-supplied fix suffix, or changed checkbox.
3. Record reviewer remediation results as pending or independently evaluated through the state
   engine. On an unchanged commit, an identical event is a no-op; do not create a new revision or
   verification event merely because the command was repeated.
4. Add findings only for newly observed, legitimate concerns. Retain prior closed outcomes and
   earlier report snapshots through Git history; do not replace or append a contradictory report.

#### Report Forms

The report's length follows risk. Use `PR_CONTEXT.risk.report_form` (`short` for low, `standard`
for medium, `full` for high; `standard` when absent). A re-review keeps the first review's form
unless the rating rose.

- **All forms**: frontmatter, Revision Log, Stats, Executive Summary, Action Items, Findings
  Detail, and Constitution Alignment (failures and partials only).
- **standard and full** add Changed Files (script table) and a Testing section; **short** gives
  Testing one line in the Executive Summary.
- **Only when something was found or resolved**: Behavioral Changes, Security, Applicable
  Knowledge (concise), and Deployment & Handoff Notes.

In every form, the Approval Decision is the Recommendation and one sentence of reasoning. A
section that has nothing to report is omitted, never written as "None found." — except
`Immediate Actions`, which states "None found." so a reader can see blocking was checked.

#### Machine-Readable Frontmatter

The report opens with a YAML frontmatter block so tools can read outcomes without parsing prose.
Keep the versioned `review_state` authoritative and derive all count/status/recommendation views
from it on every write. Keep unrelated metadata and risk checks:

- `devspark_version` is the version that produced **this** review (preamble contract §12). Copy
  the script's top-level `DEVSPARK_VERSION`; write `unknown` when absent, never guess. A re-review
  stamps the version that ran the re-review, so progress across versions stays comparable.
- `reviewed_commit` is the full SHA (no backticks, no truncation); `revision` matches the latest
  Revision Log row.
- `findings` and `max_severity` equal the counts in that latest Revision Log row, as raised in that
  review as historical unique concerns. `current_findings`, `current_state_counts`,
  `unresolved_blockers`, `recommendation` and `gate_status` are derived from the current record.
  `max_severity` is `none` when every count other than `con` is zero.
- `risk_rating` and `risk_score` come from `PR_CONTEXT.risk` when present, so predicted risk can be
  compared with the findings above. If `PR_CONTEXT.risk` is null, omit `risk_score` and set
  `risk_rating` to your own assessment.
- You may raise the rating above the supplied one when evidence warrants it, and must then set
  `risk_escalated: true` and state the reason in the Executive Summary. Never lower it.

#### Report Structure

Use this format. Keep `review_state` as the only finding authority and include each generated
section's matching begin/end markers exactly once. The state engine rewrites only these marked
regions: `ACTION`, `DETAIL`, `SUMMARY`, and `DECISION`. Keep narrative evidence, risk analysis,
observations, and unrelated report content outside the markers. Every finding's source evidence and
expected outcome must also be preserved in its structured record.
Put every unresolved blocking finding, regardless of severity, in Immediate Actions. Put validated
nonblocking findings, including any HIGH or CRITICAL findings, in Recommended Improvements. The
severity prefix and detail-section heading classify impact only.

```markdown
---
pr: [NUMBER]
devspark_version: "[DEVSPARK_VERSION from script output, or `unknown`]"
reviewed_commit: [FULL_COMMIT_SHA]
revision: [N]
findings:
  critical: [N]
  high: [N]
  medium: [N]
  low: [N]
  con: [N]
historical_findings: {critical: [N], high: [N], medium: [N], low: [N], con: [N]}
current_findings: {critical: [N], high: [N], medium: [N], low: [N]}
current_state_counts: {open: [N], remediated: [N], awaiting-verification: [N], reopened: [N], resolved: [N]}
unresolved_blockers: [N]
recommendation: approve | request-changes
gate_status: pass | pending | fail
max_severity: [none|low|medium|high|critical]
risk_rating: [low|medium|high]
risk_score: [N]
risk_escalated: [true|false]
review_state:
  format_version: 1
  findings:
    - finding_id: H-01
      aliases: []
      severity: high
      category: general
      blocking: false
      description: "[Original substantive concern]"
      expected_outcome: "[Observable expected correction]"
      evidence: ["[Original file, line, or proof reference]"]
      recommended_action: "[Actionable recommendation]"
      execution_mode: manual
      status: open
      outcome: ""
      provenance: {kind: native, location: "[review evidence location]"}
      remediation: null
      verification: null
      disposition: null
      reopen_reason: null
  conditions: []
  last_change: {operation: initial-review, affected: [H-01], actor_role: reviewer, actor_context: "[execution context]"}
---

# Pull Request Review: [PR_TITLE]

- **PR**: #[NUMBER] — [HEAD_BRANCH] → [BASE_BRANCH] — [@AUTHOR] — [OPEN/CLOSED/MERGED]
- **Reviewed Commit**: [COMMIT_SHA]
- **Review Date**: [YYYY-MM-DD HH:MM:SS UTC] (last updated [YYYY-MM-DD HH:MM:SS UTC])
- **Constitution Version**: [VERSION from constitution]

## Revision Log

| Rev | Commit | Date | Critical | High | Medium | Low | CON | Test Command | Result |
|-----|--------|------|----------|------|--------|-----|-----|--------------|--------|
| 1 | [SHA_SHORT] | [DATE] | [N] | [N] | [N] | [N] | [N] | [scoped command, or reused: location] | [pass/fail/not verified] |

*Add a row for each re-review. Keep the same test command across revisions to prevent flaky baselines.*

## Test Evidence

[One `verification-contract.md` §4.1 record per run you executed in this revision, and one line per record you reused (`reused: <location>`, with the trigger for any run you executed anyway). Write `none` when nothing was run or reused.]

## Stats

| Metric | Value |
|--------|-------|
| Files changed | [COUNT] |
| Commits | [COUNT] |
| Lines | +[ADDITIONS] −[DELETIONS] |
| Tiers (P0/P1/P2/P3) | [from `risk.tier_counts`] |
| Risk | [rating] ([risk_score]) — [factor names from `risk.factors`] |

## Executive Summary

**Overall Assessment**: [1-2 sentences. State any risk escalation and why.]

- Constitution: [PASS/FAIL] ([X]/[Y] principles checked) · Durable delta: [PASS/FAIL] ([X] open PRD findings)
- Security: [X] issues · Quality: [X] recommendations · Testing: [PASS/FAIL/not verified] · Docs: [PASS/FAIL/N/A]
- Constitution Improvements: [X] CON findings

<!-- PR-REVIEW-DERIVED:ACTION:BEGIN -->
## Action Items
<!-- PR-REVIEW-DERIVED:ACTION:END -->
<!-- PR-REVIEW-DERIVED:DETAIL:BEGIN -->
## Findings Detail
<!-- PR-REVIEW-DERIVED:DETAIL:END -->

*Do not hand-write Action Items or Findings Detail: the state engine renders both from
`review_state`. Every unresolved blocking finding, including each open `PRD{N}`, is listed under
Immediate Actions; validated nonblocking findings go under Recommended Improvements; `CON-` items
feed `/devspark-evolve-constitution`. Give each CRITICAL/HIGH finding its broken code and fix in its
`evidence` and `recommended_action`. IDs persist across re-reviews.*

## Constitution Alignment Details

*List only principles that failed or partially passed. Summarize the rest in one line.*

**Passing**: [N] of [Y] principles (N/A: [M])

| Principle | Status | Evidence | Notes |
|-----------|--------|----------|-------|
| [Principle 2] | ❌ Fail | src/api.ts:45 | [Why it fails] |
| [Principle 3] | ⚠️ Partial | Multiple files | [Partial compliance details] |

## Applicable Knowledge

[When relevant Knowledge was resolved, list only the applicable invariants, architectural
boundaries, contracts, and change-sensitive risks. Cite each authoritative `.knowledge/` path and
heading. Briefly state how it applies to this Delta and identify stale, missing, or uncertain source
evidence. Omit unrelated candidates and do not restate code, tests, or the Findings tables.]

## Security

*Include only when a security concern was found. Name the concern (secrets, input validation, authz, injection, XSS, dependencies) and the file; otherwise the Executive Summary count is enough.*

## Testing

**Status**: [ADEQUATE | INADEQUATE | N/A] — [one line; say plainly if tests were not run or the evidence could not be validated]

[Paste `risk.tables.test_files` verbatim.] Removed tests, if any:

- `[test_name]` — **[Justified/Unjustified]**: [reason] → [finding ID if unjustified]

*Unjustified removals are MEDIUM findings.*

## Changed Files

[Paste `risk.tables.changed_files` verbatim. Do not rewrite it or add a Findings column.]

## Behavioral Changes

*Silent behavioral changes detectable from diff analysis. Callers may break without test failures.*

[If none detected, omit this section.]

| Change | Before | After | Intentional? | Risk |
|--------|--------|-------|-------------|------|
| `[function()]` [what changed] | [before value/type] | [after value/type] | [Yes (PR description) / Unclear] | [Impact on callers] |

*A row marked `Intentional? Yes` cannot itself back a CRITICAL/HIGH finding — Finding Legitimacy Check Test 4 (§4C).*

## Deployment & Handoff Notes

*Items that failed the Finding Legitimacy Check (§4C) — Actionability, Ownership, basic
legitimacy, or an unestablished consumer trace. These are visible questions the review raised, not
findings against the author — no finding ID, no severity, and they do not block merge on their own.*

### Deployment Notes

[If none, write "None."]

- [What must be confirmed/verified/coordinated before or during deploy, and who owns confirming it]

### Handoff Notes

[If none, write "None."]

- [Remediation area] — owned by [DevOps / Product / upstream team] — [what's needed from them]

### Observations

*Useful facts that are not defects: behavior matching approved intent, unrelated inherited debt,
unconfirmed risks (labeled unconfirmed), and deployment information that does not affect approval.
No ID, no severity, no remediation required in this PR, and never a reason for REQUEST CHANGES.*

[If none, write "None."]

- [Observation — and why it is not a finding]

<!-- PR-REVIEW-DERIVED:DECISION:BEGIN -->
## Approval Decision

**Recommendation**: [✅ APPROVE | ⚠️ REQUEST CHANGES | ❌ REJECT] — [one sentence tracing it to the blocking findings, or stating none]

*This local recommendation does not cast a hosted approval vote or authorize merge.*
<!-- PR-REVIEW-DERIVED:DECISION:END -->

---

*Re-review after fixes: `/devspark-pr-review #[PR_NUMBER] re-review`. Address findings with `/devspark-address-pr-review {PR_ID}`; commit the review file on its own.*

---

<!-- PR-REVIEW-DERIVED:SUMMARY:BEGIN -->
## Current Review State

Historical unique findings, current lifecycle counts, unresolved blockers, pending independent
verification, applicable condition status, and local recommendation are derived from `review_state`.
The state engine rewrites only marked generated sections; reviewer narrative and evidence outside
those boundaries remain intact.
<!-- PR-REVIEW-DERIVED:SUMMARY:END -->

```text
End of report template
```

### 8. Create Review Directory

Ensure `/.devspark.work/pr-review/` exists.

### 9. Write Review File

Write the report (UTF-8) to `/.devspark.work/pr-review/pr-{PR_NUMBER}.md`.

**Validate before reporting.** Render through the state engine and run
`python scripts/pr-review-validate.py <review file> --repo-root . --range origin/{target_branch}...origin/{source_branch}`
(installed repos: `.devspark/scripts/pr-review-validate.py`). It checks the frontmatter against the
body, every derived view against `review_state`, the recommendation against unresolved blockers,
and that risk was not lowered. If it reports issues, correct the state or its rendered output and
validate the resulting revision; do not re-review. If Python, PyYAML, or the validator is
unavailable, stop with an explicit prerequisite failure. Never silently skip this required check.

### 10. Output Summary to User

Display a concise summary: the review path, reviewed commit and date, counts of Critical, High,
Medium and Low findings and constitution improvements, the Recommendation
(APPROVE / REQUEST CHANGES / REJECT), and, when blocking findings exist, each blocking finding ID
with a one-line description. Blocking findings must be resolved or explicitly dispositioned under
the applicable authority.

## Guidelines

### Constitution Authority

The constitution is the authoritative source for review criteria. Cite the principle and its exact MUST/SHOULD language. If a concern is not in the constitution, flag it LOW or as a CON candidate.

### Evidence-Based Feedback

Every issue has a specific `file:line`, a 2-5 line code quote, the principle it violates, and an actionable fix. Report facts, not taste.

### Approval Semantics

- Observations do not imply REQUEST CHANGES.
- Every REQUEST CHANGES decision must trace to at least one validated blocking finding — several
  interesting concerns without a legitimate blocker are not a blocking verdict.
- APPROVE may coexist with Low observations, deferred work, accepted limitations, and nonblocking
  handoff notes.

### Severity Guidelines

Use this scenario-to-severity mapping table to anchor classification. Severity reflects the
demonstrated consequence, materiality, current-PR responsibility, and confidence in the validated
evidence. When two tiers are plausible, choose the one the evidence supports; uncertainty calls for
more validation or lower confidence, never automatic escalation. Projects may extend this table via
their constitution's anti-pattern appendix.

| Finding Type | Severity | Rationale |
|---|---|---|
| Runtime crash on production path | CRITICAL | Immediate user impact |
| Data corruption / silent data loss | CRITICAL | Breaks data contracts |
| Auth bypass / credential exposure | CRITICAL | Compliance + security |
| Schema violation (frozen fields) | CRITICAL | Pipeline breakage |
| Code, tests, and current knowledge contradict each other | HIGH | Durable truth is unreliable |
| Runtime error on edge path | HIGH | Affects subset of users |
| Silent behavior change (defaults, types) | HIGH | Invisible regression |
| API contract violation (wrong status codes) | HIGH | Breaks consumers |
| Broken test infrastructure | HIGH | Materially impairs developer workflow |
| Test suite failures on changed test files | HIGH | Runtime errors missed by diff |
| Missing tests for new code | MEDIUM | Tech debt, not production risk |
| Unjustified test removal | MEDIUM | Coverage regression |
| Dead code introduced in PR | MEDIUM | Maintenance burden |
| Performance inefficiency | MEDIUM | Latency, not correctness |
| Review file co-mingled with code fixes | MEDIUM | Pollutes iteration diff |
| Stale TODO referencing merged work | LOW | Clutter |
| Style / naming / docs | LOW | Optional improvement |
| Constitution needs updating (not code) | CON | Governance improvement |
| Finding fails the Finding Legitimacy Check but was emitted anyway | MEDIUM (HIGH if repeated after a prior withdrawal) | Severity inflation costs reviewer credibility — mirrors gamed-fix discipline from the reviewer's side |

#### Severity Code Format

Every finding that references a constitution principle MUST include a severity code `§{section}.{LEVEL}`
matching an entry in `.knowledge/governance/severity-registry.md` (for example `§VI.HIGH`). A finding
not mapped to a constitution section is emitted without a `§` code and flagged as a `CON` candidate.

Tiers: **CRITICAL** demonstrated severe impact (production failure, serious security risk, data
loss); **HIGH** demonstrated substantial impact or material risk; **MEDIUM** partial compliance or
maintainability concern; **LOW** minor impact, advisory unless tied to a binding requirement;
**CON** the code may be correct but the constitution lags.

Severity describes impact; it does not decide blocking. A binding non-waivable obligation remains
blocking regardless of severity, while HIGH or CRITICAL alone does not block. REQUEST CHANGES
requires an actual unresolved blocking obligation. Accepting a waivable limitation requires a named,
authorized human and a reason; silence is never approval.

### Graceful Error Handling

Stop with a one-line fix instruction when the constitution is missing (run `/devspark-constitution`), the PR is not found (check the number and `gh auth status`), or `gh` is not installed or authenticated (`gh auth login`). When the PR is sound, say so and name what was done well.

## Context

$ARGUMENTS

<!-- DIVERGENT: pr-review-state -->
## Shared Review Resolution Contract Output

Use `templates/pr-review-state-contract.md` as the PR-specific schema and
`scripts/pr-review-state.py` as the only state interpretation, transition, derivation, and rendering
authority. Preserve the shared finding fields for other review stages; do not export PR-only
lifecycle states into Clarify, Analyze, or Critic.
The shared `execution_mode` values remain `auto`, `selective`, and `manual`; this PR-specific record
does not add another execution mode. The `review_state` record shape is the one in the report
template frontmatter.

Use canonical identities consistently across revisions; explicit aliases belong to one concern and
do not create additional findings. Classification and blocking are substantive decisions, not
identifier-prefix defaults. Preserve original evidence and expected outcomes in the record.

For UPDATE, perform bounded independent evaluation and record its actual result through the shared
engine. The engine can validate completeness, distinctness metadata, and Git context; it cannot
attest that narrative proof is genuine. If the permitted reviewer or required proof is unavailable,
leave the concern pending. Do not treat author remediation as reviewer confirmation.

Create the review through the shared model and run `scripts/pr-review-validate.py` against the resulting file (§9).
Review-file commits remain isolated, and a local recommendation is not a hosted vote or merge.
