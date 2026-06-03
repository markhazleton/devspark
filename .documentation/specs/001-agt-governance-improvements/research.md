# Research: AGT-Inspired Governance Improvements

**Branch**: `001-agt-governance-improvements` | **Date**: 2026-06-03

## Constitution Severity Inventory

Scanning `constitution.md` v1.4.0 for all explicit severity markers:

| Section | Marker | Severity | Trigger |
|---|---|---|---|
| §VI Platform Parity | "Violations are HIGH severity in PR review" | HIGH | Any script updated in one language without matching update in the other |
| §VII PR Review Artifact Commit Discipline | "Violations are MEDIUM severity process findings in PR review" | MEDIUM | Review file committed in same commit as production code |
| §VIII Markdown Quality | "Violations are HIGH severity in PR review when they block CI" | HIGH | Markdown file with lint errors merged to default branch |
| §VIII Markdown Quality | "MEDIUM when caught locally before push" | MEDIUM | Markdown lint error caught pre-push |
| §IV Governance Authority | "Constitution violations are showstopper severity in reviews" | SHOWSTOPPER | Any MUST/NON-NEGOTIABLE principle violated |
| §I Backward Compatibility | NON-NEGOTIABLE (implicit showstopper) | SHOWSTOPPER | Existing repo restructured without opt-in |
| §II Explicit Over Implied | NON-NEGOTIABLE (implicit showstopper) | SHOWSTOPPER | Scope inferred rather than declared |
| §III Ownership Boundary | NON-NEGOTIABLE (implicit showstopper) | SHOWSTOPPER | `.devspark/` or `.documentation/` written during install/upgrade |

**Finding**: 3 NON-NEGOTIABLE sections carry implicit SHOWSTOPPER severity (§I, §II, §III) but have no explicit severity label in the text — they rely on §IV's "showstopper severity in reviews" statement. The registry must make this mapping explicit.

## Command Template Audit — Required Section Presence

Sampling 6 command templates to verify which sections are consistently present:

| Template | `## Constitution Authority` | `handoffs` in frontmatter | Artifact output statement |
|---|---|---|---|
| `specify.md` | ✅ | ✅ | ✅ (SPEC_FILE write) |
| `plan.md` | ✅ | ✅ | ✅ (plan.md, research.md) |
| `pr-review.md` | ✅ ("Guidelines > Constitution Authority") | ✅ | ✅ (pr-NNN.md write) |
| `evolve-constitution.md` | ❌ (has "## Lifecycle Position" not "## Constitution Authority") | ✅ | ✅ (CAP-YYYY-NNN.md) |
| `quickfix.md` | ✅ | ✅ | ✅ |
| `checklist.md` | ✅ | ✅ | ✅ |

**Finding**: `evolve-constitution.md` uses "## Lifecycle Position" rather than a "## Constitution Authority" section heading. The conformance manifest must accommodate this variant or require normalization. Decision: the manifest should check for *functional* constitution authority content (a block referencing the constitution as non-negotiable), not a hard heading string match — the agent performing the check can evaluate semantic presence.

## Shared Review Resolution Contract — Current Adoption

The contract schema (finding_id, severity, description, recommended_action, execution_mode, status, outcome) is already defined in:

- `templates/commands/clarify.md` (Section: "Shared Review Resolution Contract Output")
- `templates/commands/pr-review.md` (Section: "Shared Review Resolution Contract Output")
- `templates/commands/analyze.md` (to verify — pattern is established)

**Finding**: The schema is already cross-command standard. Updating pr-review to emit this for ALL findings (not just optionally) is a targeted tightening, not a new concept.

## Trust Tier — Detection Logic Research

Branch naming convention in use: `NNN-short-name` (verified from current branch `001-agt-governance-improvements`).

Spec artifact paths follow: `.documentation/specs/{branch-name}/`

Detection algorithm:

1. Extract branch name from PR context (`head_branch`)
2. Derive spec dir: `.documentation/specs/{head_branch}/`
3. Check file existence:
   - `spec.md` → exists?
   - `plan.md` → exists?
   - `tasks.md` → exists?
4. Classify:
   - All 3 present → `full-compliance`
   - `spec.md` only, or `spec.md` + `plan.md` → `partial-compliance`
   - None present → `no-compliance`
   - Branch name doesn't match `NNN-*` pattern → `no-compliance` (note naming gap)

**Finding**: Detection is entirely file-system based — no git history analysis, no GitHub API calls beyond what the existing pr-context script already provides. Can be added as an inline step within the pr-review command without a new script.

## Decisions

| Decision | Rationale | Alternatives Considered |
|---|---|---|
| Registry as YAML frontmatter + Markdown table | Matches DevSpark conventions, human-readable, script-parseable, no new tooling | Pure YAML (less readable), pure prose (not parseable) |
| SHOWSTOPPER as 4th severity tier in registry | §I/II/III carry implicit showstopper severity per §IV — making it explicit prevents ambiguity | Map §I/II/III to HIGH (rejected: understates severity of NON-NEGOTIABLE violations) |
| Conformance manifest: semantic check, not heading-string match | `evolve-constitution.md` uses variant heading; string match would false-positive | Require heading normalization (rejected: breaks §I backward compatibility for installed repos) |
| Trust tier inline in pr-review (no new script) | No §VI parity concern, minimal footprint, fully reversible | New script pair (rejected: §VI would require Bash+PowerShell parity, adds maintenance burden for a simple file-presence check) |
| `known-limitations.md` co-located with constitution | Adopter reads constitution → naturally finds limitations beside it | In README (rejected: README gets stale; memory/ is authoritative) |
