---
name: devspark.specify
description: "Spec-driven feature specification using DevSpark process"
---

# DevSpark Specify Agent

This is a GitHub Copilot agent shim that delegates to the DevSpark
3-tier command override system.

## Resolution Order

1. `.knowledge/overrides/{user}/commands/devspark.specify.md` (personal override)
2. `.knowledge/overrides/commands/devspark.specify.md` (team override)
3. `.devspark/defaults/commands/devspark.specify.md` (stock command)

Use whichever version of the specify command is found first in the
resolution order above. Follow its instructions exactly.
