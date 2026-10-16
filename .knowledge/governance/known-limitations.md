---
document: known-limitations
version: "1.3.0"
created: "2026-06-03"
related: .knowledge/governance/constitution.md
---

# DevSpark — Known Governance Limitations

This document catalogues what DevSpark does **not** govern, with honest rationale for each
gap. It exists so adopters can make informed decisions about complementary tooling before
discovering a gap in production.

## What DevSpark Governs

DevSpark supports software engineering Deltas through multiple legitimate entry points,
including specification-led planning and lightweight change workflows. Its purpose is to establish
confidence in an intentional change and its credible blast radius through code, tests, current
Knowledge, and review evidence—not to certify that a preferred sequence of artifacts was followed.
Accountable human participants define standing assurance expectations and authorize exceptions
within their remit. DevSpark evaluates development evidence; it does not enforce the runtime
behavior of applications built with it or independently observe production outcomes.

## Known Limitations

### L-001 — Runtime Agent Behavior

**Scope**: DevSpark does not govern what AI agents do at runtime in production systems.

**Rationale**: DevSpark operates in developer workflows where a human is always present.
Runtime enforcement (cryptographic identity, policy engines, execution rings, audit chains)
is infrastructure suited to autonomous multi-agent production environments — not to
spec-driven development tooling. Adding such machinery would violate §V Simplicity.

**Complementary tooling**: Microsoft Agent Governance Toolkit (AGT)
for production-grade runtime enforcement of AI agent behavior.

---

### L-002 — Outcome Verification

**Scope**: DevSpark records compliance attempts, not whether implementations actually
achieved their stated goals in production.

**Rationale**: DevSpark can inspect the Delta, run or assess tests, challenge credible
regression risks, and record what verification actually established. That is stronger than
checking whether planning documents are complete, but it is not an independent observation of a
released system in production. Deployment outcomes require authorized operational telemetry,
monitoring, and post-release validation owned by the corresponding teams.

**Complementary tooling**: Feature flagging systems, A/B testing platforms, production
monitoring (Datadog, Grafana, etc.), and post-deployment validation runbooks.

**Deployment-dependent obligations**: A requirement declared `stage: post-deploy` stays
visible at closeout as deferred work with an owner and an existing durable `captured_as` record
until deployed evidence exists. DevSpark tracks that the obligation is open; it does not
observe the deployed result, and it never creates an external work item to hold it.

---

### L-003 — Cross-Session Workflow Sequences

**Scope**: DevSpark validates individual PR compliance, not sequences of PRs or whether
a multi-PR epic was delivered in the correct order.

**Rationale**: Each `/devspark-pr-review` run evaluates the PR and its credible impact boundary
against current governance and available evidence. It does not assert the correctness of an
entire multi-PR initiative or substitute for release-dependency management. Cross-PR sequencing
belongs to the team and its existing planning/release tools.

**Complementary tooling**: GitHub Projects, Linear, Jira, or similar project tracking
tools for epic-level sequencing and dependency management.

---

### L-004 — Technical Enforcement

**Scope**: DevSpark's quality gates are advisory (AI-evaluated), not technically enforced.
A contributor can merge a PR without running any DevSpark command.

**Rationale**: DevSpark's local review evidence does not automatically become an enforceable
Azure DevOps or GitHub merge policy. Required CI, branch protection, independent human review,
and deployment-source restrictions must be configured in their owning services. The developer's
chosen modality does not waive any such existing controls; the framework must not claim to have
enforced a hosted policy it only recommended.

**Complementary tooling**: GitHub branch protection rules, required status checks, and
optional DevSpark CI hooks (documented in `quickstart/`) for teams that want harder gates.

---

### L-005 — AI Context Provenance

**Scope**: DevSpark reviews artifacts (specs, code, PRs) but does not audit what context
an AI agent used when generating those artifacts.

**Rationale**: There is no reliable mechanism to reconstruct the full context window an
AI agent operated in when producing a given artifact. DevSpark can evaluate the output
(is the spec complete? does the code comply with the constitution?) but cannot detect
whether the agent was given misleading context, outdated documentation, or prompt-injected
instructions during generation.

**Complementary tooling**: Prompt audit logging (where supported by the AI platform),
code review for AI-generated artifacts, and red-teaming practices.

---

### L-006 — Direct Constitution Edit Bypass

**Scope**: DevSpark's severity registry and this limitations document are not automatically
updated when `constitution.md` is amended by a direct file edit.

**Rationale**: The `/devspark-evolve-constitution` workflow enforces registry and
limitations updates via its review checklist. However, a contributor
who edits `constitution.md` directly (without using that command) bypasses those checklist
gates entirely. DevSpark cannot detect this bypass automatically — it would require
comparing file modification timestamps and commit history on every run, which violates
§V Simplicity.

**Mitigation**: `severity-registry.md` carries an inline maintenance note reminding
direct-edit authors to update companion documents in the same PR. This is a process
control, not a technical gate.

**Complementary tooling**: Git pre-commit hooks or CI checks that detect modifications to
`constitution.md` and emit a warning to also check `severity-registry.md` and
`known-limitations.md`.

---

### L-007 — Legacy `last_verified` Staleness Granularity (Superseded by Opt-In Object Claims)

**Scope**: A repository that has not opted in still gets only the original signal:
`build_knowledge_index.py` flags an entity-layer doc as stale when any path in its `source_of_truth`
has a newer git commit date than the doc's `last_verified`. This is whole-file, commit-date
granularity — it cannot distinguish a change to the described behavior from an unrelated edit
elsewhere in the same file (a comment, a typo, an unconnected function). This legacy signal, its
`index.json` `stale_entities` output, and the optional `--fail-on-stale` currency check are
preserved indefinitely, unchanged, for every repository that does not explicitly opt in — no
existing repository is forced onto the newer mechanism below.

**Resolution available via opt-in**: a repository may migrate a `source_of_truth` string claim to
an object claim (`--migrate-source-claims`, then `--write`) and set
`knowledge_drift.enforcement: pinned-claims` in `.devspark.work/devspark.json`. Once opted in, the
commit-date heuristic is replaced for that claim by a content-addressed comparison: a retained
canonical baseline under `.knowledge/evidence/source-baselines/`, compared through a versioned
comparison profile (`python-token-v1`, `exact-text-v1`, or `binary-v1`), only reports a finding when
the claimed source's canonical content actually changed — an unrelated edit elsewhere in the file no
longer produces a false positive, and profile-proven non-behavioral differences (e.g. a Python
comment or layout-only edit under `python-token-v1`) stay quiet. This is bounded to explicit,
validated Git scope (`--base`/`--head`, or history-free `--full-inventory`); it fails closed with no
findings on unresolvable scope, and never asserts a claim is human-verified on its own — clearing a
finding still goes through `/devspark-explain <topic>`, which shows the retained-baseline diff before
recording a new verification. See `.knowledge/tooling/developer-guide.md` for the full workflow.

**Complementary tooling**: none needed for either mechanism; the legacy commit-date signal remains a
deliberate coarseness tradeoff for repositories that stay on it, and the opt-in object-claim
mechanism is the closure of that tradeoff for repositories that choose it.

---

### L-008 — Comparison Profile Suppression Scope

**Scope**: A source claim's comparison profile decides which differences a drift check may
suppress as non-behavioral. Only `python-token-v1`'s comment/trivia normalization on a `.py` file
is suppressed with a deterministic proof; every other case — an unsupported file extension, a
file `python-token-v1` cannot tokenize or parse, or a profile that is not one of `python-token-v1`
/ `exact-text-v1` / `binary-v1` — is either an exact byte-for-byte comparison (conservative
fallback) or a hard `CanonicalizationError`. No profile suppresses a difference it cannot
deterministically prove non-behavioral.

**Rationale**: A false "non-behavioral" suppression is worse than an occasional noisy exact-text
finding on a comment-only change, so the evaluator only ever narrows what counts as drift when it
can prove the narrowing safe (token-level equivalence under Python's own tokenizer); every other
case falls back to the widest, safest comparison rather than guessing.

**Related widening limitation**: a claim naming a symbolic region (a Python function or class)
widens to the whole file, with a non-blocking `region-widened` advisory, whenever that region name
cannot be resolved (renamed, removed, syntax error). Widening never suppresses a difference; it
only enlarges what is compared, so a real change outside the originally-intended region can also
surface as drift until the claim's region name is corrected.

**Complementary tooling**: none needed; see `.knowledge/tooling/developer-guide.md#choosing-a-comparison-profile`
for the profile-selection guidance this limitation constrains.
