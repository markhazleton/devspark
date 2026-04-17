# Release Readiness: v1.6.0

Generated: 2026-04-12

## Verdict

DevSpark v1.6.0 is release-ready for repository-local scope and GitHub release publication.

This release focuses on prompt consistency, quickstart install hardening, and release-surface cleanup. The shipped delta is validated across repository tests, targeted markdown linting, quickstart repair guidance, and release publishing prerequisites.

## Evidence

- `tests/test_agent_registry.py` passes.
- `tests/test_create_pr_preflight_debug.py` passes.
- `tests/test_create_pr_preflight.py` passes.
- `tests/test_documentation_audit.py` passes.
- `tests/test_pr_scope_validation.py` passes.
- `tests/test_prompt_gate_contract.py` passes.
- `tests/test_release_registry_contract.py` passes.
- `tests/test_script_parity_contract.py` passes.
- `tests/test_upgrade_migration_safety.py` passes.
- `tests/test_upgrade_reporting.py` passes.
- `npx markdownlint-cli2 quickstart/devspark_quickstart_generic.md quickstart/devspark_quickstart_copilot.md quickstart/devspark_quickstart_claudecode.md quickstart/devspark_quickstart_cursor.md quickstart/README.md` passes.
- GitHub CLI is installed and authenticated with release-capable scopes.
- The branch was validated on `main` and is ahead of `v1.5.0` by 8 commits.

## Release Scope

### Prompt and Template Alignment

- Installed-repository command templates now resolve helper templates from `.devspark/templates/` consistently.
- Quickstart inventories now include both `quick-spec-template.md` and `update-pr.md`.
- Versioned template markers in discover-constitution and repo-story prompts were rolled forward to 1.6.0.

### Quickstart Installation Hardening

- Same-version installs now verify expected framework files instead of only reporting version status.
- Missing stock prompts, templates, scripts, or shims now trigger an explicit Repair Mode in every quickstart.
- Constitution bootstrap questions are only asked when a new constitution must be created.

### Documentation and Release Packaging

- CHANGELOG and package version are updated for v1.6.0.
- Release notes and metrics are archived under `.documentation/releases/v1.6.0/`.
- Validation Matrix and release guidance now point at v1.6.0 release evidence.

## Judgment Call

No live hosted pull-request mutation was executed as part of release validation because that would create avoidable remote side effects unrelated to the release artifact itself.

GitHub release publication is in scope for this release and is validated separately through authenticated GitHub CLI availability before publication.

## Remaining Work After Readiness

No repository-local validation blockers remain for v1.6.0.

The remaining actions are mechanical release publication steps: commit the versioned release artifacts, create tag `v1.6.0`, and publish the GitHub release from the prepared release notes.
