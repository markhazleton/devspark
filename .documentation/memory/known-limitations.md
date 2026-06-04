---
document: known-limitations
version: "1.0.0"
created: "2026-06-03"
related: .documentation/memory/constitution.md
---

# DevSpark — Known Governance Limitations

This document catalogues what DevSpark does **not** govern, with honest rationale for each
gap. It exists so adopters can make informed decisions about complementary tooling before
discovering a gap in production.

## What DevSpark Governs

DevSpark governs the **development process** that produces AI-assisted software: it provides
spec-driven workflows, constitution-based quality gates, and right-sized execution paths.
A human developer is always in the loop. DevSpark reviews artifacts (specs, plans, tasks,
PRs) — it does not enforce runtime behavior of the systems those artifacts describe.

## Known Limitations

### L-001 — Runtime Agent Behavior

**Scope**: DevSpark does not govern what AI agents do at runtime in production systems.

**Rationale**: DevSpark operates in developer workflows where a human is always present.
Runtime enforcement (cryptographic identity, policy engines, execution rings, audit chains)
is infrastructure suited to autonomous multi-agent production environments — not to
spec-driven development tooling. Adding such machinery would violate §V Simplicity.

**Complementary tooling**: [Microsoft Agent Governance Toolkit (AGT)](https://github.com/microsoft/agent-governance-toolkit)
for production-grade runtime enforcement of AI agent behavior.

---

### L-002 — Outcome Verification

**Scope**: DevSpark records compliance attempts, not whether implementations actually
achieved their stated goals in production.

**Rationale**: DevSpark verifies that the correct process was followed (spec present, plan
complete, review done) and that artifacts are internally consistent. It cannot verify that
the shipped feature works correctly in production — that is the domain of testing, monitoring,
and observability tooling.

**Complementary tooling**: Feature flagging systems, A/B testing platforms, production
monitoring (Datadog, Grafana, etc.), and post-deployment validation runbooks.

---

### L-003 — Cross-Session Workflow Sequences

**Scope**: DevSpark validates individual PR compliance, not sequences of PRs or whether
a multi-PR epic was delivered in the correct order.

**Rationale**: Each `/devspark.pr-review` run is stateless — it evaluates the PR in
isolation against the constitution and the current spec lifecycle. Tracking whether PR #3
should not have merged before PR #1 was complete requires project-management tooling,
not a development-process governance framework.

**Complementary tooling**: GitHub Projects, Linear, Jira, or similar project tracking
tools for epic-level sequencing and dependency management.

---

### L-004 — Technical Enforcement

**Scope**: DevSpark's quality gates are advisory (AI-evaluated), not technically enforced.
A contributor can merge a PR without running any DevSpark command.

**Rationale**: DevSpark is designed to work with any AI coding assistant and any team
culture. Mandatory CI gates would require framework-specific CI configuration and would
conflict with §I Backward Compatibility for repositories that already have CI pipelines.
Enforcement relies on team culture, optional CI hooks, and the positive incentive
created by trust-tiered review depth.

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

**Rationale**: The `/devspark.evolve-constitution` workflow enforces registry and
limitations updates via Review Checklist items (FR-009, FR-006). However, a contributor
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
