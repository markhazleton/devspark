# DevSpark Guidance for Claude

DevSpark is prompt-first. Work in this repository as a collection of prompts,
scripts, templates, schemas, quickstart prompts, documentation, and current-truth
knowledge files.

Do not add or use a DevSpark command-line application. Install, upgrade, and
repair flows belong only in the quickstart prompts under `quickstart/`.

Important paths:

- `.knowledge/` stores durable governance, decisions, entities, and ontology
  reports.
- `.devspark/` stores the framework version stamp and local framework assets.
- `.devspark.work/` stores temporary lifecycle work and must stay out of git.
- `templates/commands/` stores stock `/devspark.*` command prompts.
- `scripts/bash/` and `scripts/powershell/` must stay behaviorally paired.

Validation:

```bash
pytest tests/ -q
python tests/test_documentation_audit.py
python tests/test_script_parity_contract.py
```
