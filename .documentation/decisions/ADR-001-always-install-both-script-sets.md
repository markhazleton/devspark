# ADR-001: Always Install Both PowerShell and Bash Script Sets

**Status**: Accepted  
**Date**: 2026-05-22  
**Deciders**: markhazleton  
**Related**: Constitution §VI Platform Parity (MUST), Issue #45, CAP-2026-002

---

## Context

DevSpark ships a complete set of context-gathering and workflow scripts in two
languages:

- `scripts/bash/` — for macOS and Linux (21 `.sh` files)
- `scripts/powershell/` — for Windows (21 `.ps1` files)

Every command template (`templates/commands/*.md`) declares both variants in its
frontmatter:

```yaml
scripts:
  sh: .devspark/scripts/bash/create-pr.sh --mode preflight --json
  ps: .devspark/scripts/powershell/create-pr.ps1 -Mode Preflight -Json
```

The AI agent selects the correct variant at **execution time** based on the
active OS. This means both sets must be present on disk for the selection to
work on any machine.

Prior to this decision, all five quickstart guides asked a "script preference"
question (PowerShell or Bash) and installed **only** the matching set. This
worked on single-OS setups but broke immediately when a repo was opened on a
different OS — the commands referenced scripts that were never installed.

---

## Decision

**All install, init, repair, and upgrade flows MUST always deliver both
`scripts/bash/` and `scripts/powershell/` to `.devspark/scripts/`, regardless
of the current developer OS.**

OS detection is retained for cosmetic display only (e.g., noting the active
runtime in the plan preview). It must not gate which script sets are installed.

---

## Alternatives Considered

### Option A: Install only the detected-OS set (previous behaviour)

- **Pro**: Fewer files fetched during install; simpler install step
- **Con**: Breaks immediately when the repo is used on a second OS
- **Con**: No warning is shown — commands silently fail or fall back
- **Con**: Requires a full reinstall or repair cycle to fix
- **Rejected**: The failure mode is silent and the fix is non-obvious

### Option B: Install both sets always (chosen)

- **Pro**: Repo is immediately usable on any OS after a single install
- **Pro**: Upgrade/repair never leaves a machine-dependent gap
- **Pro**: Consistent with how command templates already declare both variants
- **Con**: Slightly more files fetched on initial install (~21 extra files)
- **Accepted**: The overhead is negligible; the correctness gain is significant

### Option C: Detect OS at command execution time and fetch on demand

- **Pro**: No pre-install overhead at all
- **Con**: Requires network access at command execution time
- **Con**: Breaks air-gapped or offline workflows
- **Con**: Much more complex agent-side logic required
- **Rejected**: Complexity cost outweighs the install-size savings

---

## Consequences

### Positive

- A repo cloned on macOS and opened on Windows works without any reinstall
- Upgrade and repair flows are OS-agnostic
- Constitution §VI Platform Parity is enforced at the install level, not just
  the source level
- `test_script_parity_contract.py` structural check catches any future drift
  (file missing from one set but not the other)

### Negative / Trade-offs

- Initial install fetches ~21 additional files compared to the single-set
  approach (minimal overhead on any modern connection)
- Repair mode must verify both directories, not just one (already reflected in
  updated Step 6 validation in all quickstart guides)

### Enforcement

- **Constitution §VI (MUST)**: installs must always deliver both sets;
  violations are HIGH severity in PR review
- **`test_script_parity_contract.py`**: structural assertion that every `.sh`
  has a matching `.ps1` and vice versa; runs in CI
- **Quickstart Step 6 validation**: checks both script-set counts and warns if
  either is 0
