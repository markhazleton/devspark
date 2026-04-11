# Validation Matrix

This matrix tracks the v1.5.0 workflow-evolution scenarios that need explicit validation before release.

| Scenario | Scope | Current Evidence | Status |
|----------|-------|------------------|--------|
| One-off fix in existing repo | `/devspark.quickfix` remains lightweight and advisory | `test_create_pr_preflight.py` validates quickfix-record routing, gate acknowledgement carry-forward, and create-pr preflight handling for one-off fixes | Complete |
| Quick spec in existing repo | `/devspark.specify` can route to quick-spec and continue through implementation | `test_create_pr_preflight.py` validates quick-spec frontmatter, task status, and gate-aware create-pr preflight handling | Complete |
| Full spec in existing repo | Full workflow reaches implementation, PR drafting, and PR review | `test_create_pr_preflight.py` validates full-spec frontmatter and completed-task preflight handling; lifecycle docs and templates are aligned | Complete |
| Persisted gate lifecycle | Analyze, critic, checklist, tasks, and PR drafting share one persisted gate model | Analyze/critic now write `gates/*.md`; checklist refreshes `gates/checklist.md`; tasks template includes `Gate Acknowledgements`; create-pr preflight reads them | Complete |
| Repo with `.documentation/` overrides | Override precedence remains intact after upgrade | `test_upgrade_migration_safety.py` validates that existing `.documentation/commands/` and `.documentation/scripts/` content is preserved while legacy files are reported and moved to `.old/` backups | Complete |
| Repo migrated from `.specify/` | Migration compatibility remains documented and safe | `test_upgrade_migration_safety.py` exercises `.specify/`, root `scripts/`, root `templates/`, and root `specs/` migration into `.documentation/` with preserved backups | Complete |
| Multi-agent install and upgrade | Shared registry drives packaging and agent metadata consistently | `test_agent_registry.py` and `test_release_registry_contract.py` validate registry loading plus registry-driven release packaging and publishing contracts | Complete |
| Upgrade from v1.4.x to v1.5.0 | Prompt-first upgrade preserves repo-owned artifacts and surfaces contract changes | `test_upgrade_reporting.py` and `test_upgrade_migration_safety.py` validate structured version stamps, legacy artifact reporting, override warnings, and safe migration behavior for v1.4-style leftovers | Complete |
| Bash and PowerShell parity for changed scripts | Changed script pairs accept the same inputs and produce comparable output | `test_script_parity_contract.py` validates shared frontmatter helpers, shared-context hydration markers, and create-pr parity contracts; `test_create_pr_preflight.py` validates runtime preflight behavior | Complete |
| Release readiness | v1.5.0 has repository-local release evidence and explicit judgment calls | `.documentation/release-readiness-v1.5.0.md` records the validation set, release judgment, and the hosted-PR side-effect decision | Complete |
| Current-state documentation audit | Public docs, quickstarts, templates, and examples reflect current v1.5.0 behavior | `test_documentation_audit.py` validates 69 in-scope files and `.documentation/docs-audit-2026-04-11.md` records the file-by-file audit | Complete |

## Evidence Collected

- `tests/test_agent_registry.py` passes.
- `tests/test_pr_scope_validation.py` passes.
- `tests/test_upgrade_reporting.py` passes.
- `tests/test_upgrade_migration_safety.py` passes.
- `tests/test_create_pr_preflight.py` passes.
- `tests/test_prompt_gate_contract.py` passes.
- `tests/test_release_registry_contract.py` passes.
- `tests/test_script_parity_contract.py` passes.
- `tests/test_documentation_audit.py` passes.
- `scripts/powershell/create-pr.ps1 -Mode Preflight -Json` returns valid JSON in the repo.
- `scripts/bash/create-pr.sh` passes syntax validation and now fails clearly when `jq` is absent.
- `.documentation/release-readiness-v1.5.0.md` records Step 9 release evidence.
- `.documentation/docs-audit-2026-04-11.md` records the Step 10 file-by-file audit.

## Remaining Validation Work

No repository-local validation gaps remain for v1.5.0.

The only excluded check is a live hosted PR create/update mutation, which is intentionally omitted from automated local validation to avoid remote side effects. That judgment is recorded in `.documentation/release-readiness-v1.5.0.md`.