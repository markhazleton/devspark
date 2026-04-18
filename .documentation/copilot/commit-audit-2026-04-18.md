# Commit Audit Report

## Audit Metadata

- **Audit Date**: 2026-04-18 16:30 UTC
- **Branch**: main
- **Date Range**: 2025-08-21 to 2026-04-18 (≈8 months)
- **Total Commits Analyzed**: 787
- **Auditor**: devspark.commit-audit
- **Note**: No `commit-audit.ps1` script present — analysis derived directly from `git log`. Privacy: contributors anonymized to role IDs.

## Executive Summary

| Metric | Value | Status |
|--------|-------|--------|
| Total Commits | 787 | — |
| Active Contributors | 86 unique emails (top 4 = 73.7% of commits) | — |
| Bus Factor (80% threshold) | ~6 | ⚠️ Low |
| Commit Hygiene Score | 50/100 | Fair |
| AI Adoption Level | Level 3 — Collaborative | — |
| Deployment Frequency (est.) | ≈23 merges/month | High (sub-Elite) |
| Change Failure Rate (est.) | ≈9.5% | Medium (above 5% Elite threshold) |
| Test:Source touch ratio | 177:96 ≈ 1.84:1 | ✅ Healthy |

## Contributor Census (Anonymized)

| Role | Commit Count | Share | Notes |
|------|--------------|-------|-------|
| Contributor A | 361 | 45.9% | Primary maintainer (likely upstream lineage; this repo is a fork) |
| Contributor B | 139 | 17.7% | Repo owner / release manager |
| Contributor C (AI agent) | 40 | 5.1% | Identified as automated agent ("Copilot" account) |
| Contributor D (test/CI identity) | 40 | 5.1% | Synthetic CI identity |
| Long tail | 207 | 26.3% | 82 occasional contributors (<5% each) |

- **Bus factor (80% of commits)**: ~6 contributors. Low — concentrated knowledge in A + B.
- 82 of 86 unique authors are occasional contributors (likely fork upstream + co-author tags).

## Monthly Velocity

| Month | Commits | Merges | Notes |
|-------|---------|--------|-------|
| 2025-08 | 22 | 5 | Bootstrap (partial month — fork created Aug 21) |
| 2025-09 | **255** | 78 | Peak — initial rebuild |
| 2025-10 | 184 | 55 | Sustained build |
| 2025-11 | 51 | 16 | Cooling |
| 2025-12 | 16 | 7 | Holiday lull |
| 2026-01 | 10 | 0 | Quiet |
| 2026-02 | 29 | 0 | Re-engagement |
| 2026-03 | 36 | 3 | Ramping |
| 2026-04 | **184** | 20 | Pre-release burst (v2.0.0) |

Aggregate diff over window: **2,669 files changed, +116,296 insertions, −56,453 deletions** (net +59,843).

## Development Phases

| Phase | Period | Avg/Month | Characterization |
|-------|--------|-----------|------------------|
| Bootstrap | 2025-08 | 22 | Fork seeded |
| Rapid Build | 2025-09 → 2025-10 | 220 | Major feature delivery (harness, runner, atomic shims) |
| Stabilization | 2025-11 → 2026-01 | 26 | Bug fixes, holiday lull |
| Re-engagement / v2 push | 2026-02 → 2026-04 | 83 | Workflow runner, address-pr-review, v2.0.0 release prep |

**Inflection points**:

- **2025-08 → 2025-09 (+1059%)**: rebuild kickoff after fork.
- **2025-10 → 2025-11 (−72%)**: feature freeze / stabilization.
- **2026-01 → 2026-04 (+1740%)**: v2.0.0 release sprint (matches CHANGELOG `[2.0.0] - 2026-04-16`).

## Commit Hygiene Score: 50/100 — Fair

| Dimension | Weight | Raw | Weighted |
|-----------|--------|-----|----------|
| Conventional Commits | 40% | 38% (232/603 non-merge commits use `feat\|fix\|docs\|chore\|refactor\|test\|ci\|build\|perf\|style\|review\|spec`) | 15.2 |
| Subject Line Quality | 25% | ~75% (heuristic — most subjects are concise, imperative) | 18.8 |
| Body Usage | 15% | ~50% (estimated; merge commits inflate empty bodies) | 7.5 |
| Reference Linking | 10% | 21% (169/787 commits reference an issue/PR) | 2.1 |
| WIP / Fix-Up Penalty | 10% | 7.9% noisy ("WIP/oops/temp/squash!/fixup!" → score 92) | 9.2 |
| **Total** | — | — | **52.8 → rounded 50** |

### Drag Examples (representative, anonymized)

| # | Subject pattern observed | Issue | Suggested rewrite |
|---|--------------------------|-------|-------------------|
| 1 | `Merge pull request #N from owner/branch` (×184) | Default GitHub merge subject — no semantic info | Use squash-merge with conventional subject, or amend merge subject |
| 2 | `review(pr-28): rev 3 ΓÇö confirmation re-review at e19b902 (no code delta)` | Mojibake (`ΓÇö` for em-dash) — encoding issue | `review(pr-28): rev 3 — confirmation re-review at e19b902 (no code delta)` |
| 3 | `fix(ci): remove hard tabs in spec.md (MD010) + align bash shim generator to single backticks` | Two changes in one commit | Split into two commits |
| 4 | `feat(cli): add devspark run / resume / workflows / runs / help subcommands; gh issue adapter` | Multi-feature commit; semicolon as bullet | Decompose; add body |
| 5 | Subjects with `WIP`/`oops` (62 commits) | Should not reach main history | Squash before merge |

### Recommendation

Adopt **squash-merge by default** plus a `commit-msg` hook enforcing Conventional Commits. Expect hygiene score to climb to 75+ within one release cycle.

## DORA Metrics

| Metric | Git Signal | Estimated Value | Elite Benchmark | Status |
|--------|-----------|-----------------|----------------|--------|
| Deployment Frequency | Merge commits to main | ≈23/month (peak 78/mo Sept) | On-demand (multi/day) | **High** |
| Lead Time for Changes | PR open → merge duration | n/a from local git | <1 day | Requires GitHub API |
| Change Failure Rate | `fix\|hotfix\|revert` / total | 75/787 = **9.5%** | <5% | **Medium** |
| Time to Restore | Avg time revert → fix | n/a (0 reverts in window) | <1 hour | Insufficient signal |

> Lead-time and TTR estimates require PR/CI data not present in local git history. Recommend instrumenting with `gh pr list --json mergedAt,createdAt` for the next audit.

## AI Adoption Level

**Level 3 — Collaborative**

Evidence:

- 159 commits (≈20%) contain AI-related signals (`copilot`, `claude`, `chatgpt`, `co-authored-by`).
- Dedicated automated agent identity (Contributor C) authored 40 commits (5.1%).
- AI tool config files present: [.github/copilot-instructions.md](.github/copilot-instructions.md), [CLAUDE.md](CLAUDE.md), [.devspark/](.devspark/) (the framework being dogfooded), `.github/prompts/`, `.github/agents/`.
- Pattern matches Level 3: high-volume AI-authored content with systematic human review (PR-review commits, address-pr-review commits, isolated review-file commits per Principle VII).
- Not Level 4 because human-authored review/curation commits dominate the long tail and the constitution mandates explicit human governance.

## Architecture Maturity Indicators

| Indicator | Signal | Reading |
|-----------|--------|---------|
| Test investment | 177 test-file touches vs 96 source-file touches (1.84:1) | ✅ Strong testing culture |
| Modularization | Major refactors visible (harness/runner extraction; atomic shim generation) | ✅ Active modularization |
| Dependency churn | 175 manifest touches over 8 months (~22/mo) | ⚠️ Elevated — active build-system iteration |
| Configuration drift | Many `.devspark/`, `.documentation/` config touches paired with code | ✅ Coupled, not drifting |
| Migration patterns | No DB migration signals (not applicable — CLI tool) | n/a |
| Refactoring cycles | Net +59,843 lines but 56,453 deletions = del:ins ratio 0.49 | ✅ Healthy refactor activity |
| Spec-driven discipline | Many `spec(NNN):`, `review(pr-NN):` prefix commits | ✅ Constitution-aligned |

**Summary**: The repository shows mature spec-driven, test-first discipline with deliberate modularization. Dependency churn is the only mild concern — likely tied to packaging the framework and adding the harness runtime; expected to taper post-v2.0.0.

## Recommendations

Top 5, ranked by impact:

1. **Add `commit-audit.ps1` + `commit-audit.sh` to `.devspark/scripts/`** (parity per Principle VI). The prompt expects a context script; current absence forces manual `git log` queries and weakens reproducibility.
2. **Adopt squash-merge with Conventional Commits enforcement.** Will lift hygiene score from 50 → 75+ and eliminate the 184 generic "Merge pull request" subjects that dominate history.
3. **Instrument PR lead-time capture** via `gh pr list --json` in the commit-audit script so future runs can populate Lead Time and Time to Restore DORA cells.
4. **Investigate the 9.5% Change Failure Rate.** Above the 5% Elite threshold. Sample the 75 `fix:` commits to determine whether they reflect (a) genuine post-merge bugs (action: tighten CI gates) or (b) intra-PR iteration that escaped squash (action: enforce squash-merge — see #2).
5. **Fix mojibake in commit subjects** (`ΓÇö` instead of `—`). Set git config `i18n.commitencoding=utf-8` and `core.quotepath=false`; ensure the PowerShell shells producing commits use UTF-8 (`$OutputEncoding = [System.Text.UTF8Encoding]::new()`).

---

*Commit audit generated by devspark.commit-audit (manual fallback mode — no script available)*
*Privacy: contributor identities anonymized as Contributor A/B/C/D + long tail*
*Next audit recommended: after the v2.0.0 release ships, to capture lead-time deltas*
