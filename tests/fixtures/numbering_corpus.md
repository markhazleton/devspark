# T027 Numbering Baseline (golden fixtures)

**Task**: T027 · **Date**: 2026-07-24 · **Purpose**: freeze the CURRENT numbering behavior BEFORE the allocator is refactored, so the `verify:snapshot-neutral` equivalence test (T008) asserts against these frozen values rather than the soon-removed `Get-NextBranchNumber` (resolves: critic-003).

## Current algorithm (as of commit before refactor)

`Get-NextBranchNumber` (PowerShell) / `get_next_branch_number` (Bash):

1. best-effort `git fetch --all --prune`
2. `highestBranch` = max integer from local+remote branches matching `^(\d+)-` (strip `remotes/<remote>/`)
3. `highestSpec` = max integer from `.devspark.work/specs/` dir names matching `^(\d+)`
4. return `max(highestBranch, highestSpec) + 1`

Padding: `('{0:000}' -f $n)` → 3-digit zero-pad.

## Golden cases — LEGACY allocator (must stay equivalent, FR-012)

| # | Branches (`^\d+-`) | Spec dirs (`^\d+`) | Expected next |
|---|--------------------|--------------------|---------------|
| L1 | (none) | (none) | `001` |
| L2 | `001-foo`, `007-bar` | `003-x` | `008` |
| L3 | (none) | `012-y` | `013` |
| L4 | `005-a` | `005-a` | `006` |
| L5 | `0042-z` | (none) | `043` (int 42) |
| L6 | `003-a`, `feature/misc` | `003-a` | `004` (non-numeric branch ignored) |

## Golden cases — UNIFIED allocator (NEW scan set adds quickfix records, FR-003)

The unified `Get-NextUnifiedIndex` extends the scan to include quickfix records: legacy `QF-YYYY-(\d+)` and new `^(\d+)-fix-`. For any input set that contains NO quickfix records, it MUST return the SAME value as the legacy allocator (equivalence).

| # | Branches | Spec dirs | Quickfix records | Expected next |
|---|----------|-----------|------------------|---------------|
| U1 | `007-spec-foo` | `007-spec-foo` | `QF-2026-003.md` | `008` (QF #3 counted, max is 7) |
| U2 | `009-fix-x` | (none) | `009-fix-x.md` | `010` |
| U3 | (none) | (none) | `QF-2026-005.md` | `006` (QF now advances the index) |
| U4 | `002-spec-a` | `002-spec-a` | (none) | `003` (equals legacy L-style) |

**Equivalence invariant (T008)**: for cases with no quickfix records (L1–L6, U4), `Get-NextUnifiedIndex == Get-NextBranchNumber`.
