---
id: always-install-both-powershell-and-bash-script-sets
status: current
last_verified: "2026-08-30"
governs:
- command-templates
- agent-shims
evidence:
- type: test
  ref: tests/test_script_parity_contract.py
  verified_by: execution
- type: code
  ref: quickstart/README.md
  verified_by: inspection
  test_attempted: true
---

# Always Install Both PowerShell and Bash Script Sets

## Current Decision

Every DevSpark quickstart install, upgrade, and repair flow delivers both
`scripts/bash/` and `scripts/powershell/` to `.devspark/scripts/`, regardless
of the developer's current operating system.

Command templates and agent shims may choose the appropriate script at execution
time, but installed repositories must already contain both script families.

## Rationale

DevSpark command prompts declare both shell variants in their frontmatter. If a
repository receives only one platform's scripts, the same checkout can fail when
opened on another operating system. Installing both sets makes a repository
portable immediately after quickstart setup and keeps repair behavior
OS-agnostic.

## Alternatives Rejected

Installing only the detected OS script set is rejected because it creates a
machine-dependent repository state.

Fetching missing scripts on demand is rejected because prompt execution must not
depend on network access after installation.

## Consequences

Quickstart prompts validate both script sets. Script parity tests ensure each
Bash script has a matching PowerShell script and each PowerShell script has a
matching Bash script.

The extra files are accepted as the cost of deterministic cross-platform use.
