# Quickstart: Participant Roles

## Goal

Validate that DevSpark documents participants without changing agent runtime
semantics or existing customization layers.

## Manual Verification

1. Read `README.md`.
2. Confirm `agent` still means supported AI runtime/client integration.
3. Confirm `participant` is introduced as a human or AI-filled team member.
4. Read `.documentation/implementation-lifecycle.md`.
5. Confirm the lifecycle explains that participant concepts do not change
   existing customization layers.
6. Inspect `templates/spec-template.md`, `templates/quick-spec-template.md`,
   `templates/plan-template.md`, and `templates/tasks-template.md`.
7. Confirm each template has optional `participants` YAML frontmatter metadata.
8. Confirm no command output instruction requires printing participant metadata.

## Automated Verification

Run markdown lint on changed markdown:

```powershell
npx markdownlint-cli2 "README.md" ".documentation/**/*.md" "templates/**/*.md"
```

Run focused tests:

```powershell
.\.venv\Scripts\python -m pytest -q tests/test_participant_metadata_contract.py
.\.venv\Scripts\python -m pytest -q tests/test_skill_contract.py tests/test_workflow_schema_contract.py
```

Run the full suite before completion:

```powershell
.\.venv\Scripts\python -m pytest -q
```

## Expected Result

- Tests pass with no fixture requiring participant metadata.
- Markdown lint reports zero errors for changed markdown.
- Existing prompt and script resolution documentation remains unchanged.
