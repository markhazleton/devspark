# T024 Audit: consumers of the branch/dir `NNN-` and `QF-` format

**Task**: T024 · **Date**: 2026-07-24 · **Purpose**: enumerate every consumer of the branch-name / spec-dir / quickfix-record format before changing it (resolves critic-001).

## A. Feature-path resolution (the critic-001 core path)

| Consumer | Location | Assumption | Impact of `NNN-<type>-slug` |
|----------|----------|-----------|------------------------------|
| `Find-FeatureDirByPrefix` | `scripts/powershell/common.ps1:118` (`^(\d{3})-`, matches `specs/NNN-*`) | 3-digit prefix → one `specs/NNN-*` dir | **BREAKS for `fix`**: routes `NNN-fix-*` branches to `specs/` instead of `quickfixes/` |
| `find_feature_dir_by_prefix` | `scripts/bash/common.sh:113` | same | same |
| Callers | `common.ps1:154` (`Get-FeaturePathsEnv`), `create-pr.ps1:292`, `create-pr.sh:370`, `common.sh:165/201/657` | via resolver | inherit the misroute |

**Fix (T025)**: make the resolver type-aware — `NNN-fix-*` → `.devspark.work/quickfixes/`, else `specs/`.

## B. Quickfix record filename convention (NEW — beyond critic-001)

| Consumer | Location | Assumption | Impact |
|----------|----------|-----------|--------|
| next-context | `next-context.ps1:143`, `next-context.sh:137` | `QUICKFIX_RECORD = quickfixes/$CURRENT_BRANCH.md` | Works if record is named after branch (`NNN-fix-slug.md`) — must ensure the writer matches |
| create-pr quickfix lookup | `create-pr.ps1:135`, `create-pr.sh:147` | `quickfixes/` scan | verify it finds `NNN-fix-*.md` |

## C. `QF-*.md` glob consumers (NEW — beyond critic-001) ⚠️

These scan for **`QF-*.md`** literally and will **silently miss** new `NNN-fix-*.md` quickfix records:

| Consumer | Location |
|----------|----------|
| release-context | `release-context.ps1:103` (`-Filter 'QF-*.md'`), `release-context.sh:212/217` |
| release-history-context | `release-history-context.ps1`, `.sh:224` (`QF-[^/]+` regex) |
| harvest | `harvest.ps1:91`, `harvest.sh:294` (path-based, OK) |

**Implication**: release/changelog + harvest would not see new-format quickfixes.

## D. Tests asserting the format

| Test | Location |
|------|----------|
| create-pr preflight | `tests/test_create_pr_preflight.py:149`, `_debug.py:121` (`QF-001.md`) |
| release recovery | `tests/test_release_context_recovery.py` (`QF-2026-001.md`) |
| parity | `tests/test_script_parity_contract.py` |

## Scope Finding (routed to /devspark.tasks)

The audit found consumers **beyond** the current tasks:

- **B + C** (quickfix record filename convention + `QF-*.md` globs in release/history/harvest) are **not** covered by T025 (resolver only).
- New tasks needed: (1) update `QF-*.md` glob consumers to also match `NNN-fix-*.md`; (2) verify next-context/create-pr quickfix record lookup handles the new filename.

Per the implement contract ("scope grows mid-implementation → halt, route back"), this is surfaced rather than silently expanded.
