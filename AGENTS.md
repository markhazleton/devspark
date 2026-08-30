# DevSpark Development Guidelines

## Product Surface

DevSpark is a prompt-first lifecycle toolkit. The product is the markdown prompt
set, helper scripts, templates, schemas, quickstart prompts, and generated agent
shims.

There is no DevSpark command-line application in this repository. Do not add one.
The only approved way to install, upgrade, or repair DevSpark in a consumer
repository is to run the appropriate quickstart prompt from `quickstart/`.

## Repository Layout

```text
.devspark/       Framework version stamp and local installed stock assets
.knowledge/      Current truth: entities, governance, decisions, ontology reports
.documentation/  Guides, media, and site content
quickstart/      Install, upgrade, and repair prompts
templates/       Stock prompts, skills, schemas, and helper templates
scripts/         Bash and PowerShell context helpers used by prompts
tests/           Prompt, script, documentation, and packaging contracts
```

## Development Rules

- Keep install, upgrade, and repair behavior in quickstart prompts only.
- Keep framework-owned stock files under `.devspark/` and durable project truth
  under `.knowledge/`.
- Keep temporary work under `.devspark.work/`.
- Maintain Bash and PowerShell parity for helper scripts.
- Update quickstart command/script inventories whenever templates or scripts
  change.
- Preserve generated agent shims as thin prompt resolvers only.

## Validation

Run focused repository contracts after changes:

```bash
pytest tests/ -q
python tests/test_documentation_audit.py
python tests/test_script_parity_contract.py
```
