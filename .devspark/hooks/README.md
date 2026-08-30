# DevSpark Optional Hooks

## pre-commit-review-isolation.ps1

Guards DevSpark v4 current-truth discipline by blocking commits that stage:

- `.devspark.work/*`

`.devspark.work` contains temporary lifecycle state. Assimilate durable results
into code, tests, and `.knowledge/` before committing.

### Option 1: Native git hook

1. Copy this script into `.git/hooks/pre-commit` (or invoke it from that file).
2. Ensure PowerShell is available (`pwsh`).
3. Example `.git/hooks/pre-commit` shim:

```bash
#!/usr/bin/env bash
pwsh -File .devspark/hooks/pre-commit-review-isolation.ps1
```

### Option 2: pre-commit framework

Invoke `pwsh -File .devspark/hooks/pre-commit-review-isolation.ps1` from your pre-commit framework config as a local hook.

If the hook blocks a commit, unstage the `.devspark.work` paths and commit only
the durable current-truth changes.
