---
name: devspark.harvest
description: Harvest knowledge from completed specs and stale docs into living documentation, rewrite stale spec-linked comments, then archive obsolete artifacts
---

# DevSpark Harvest Agent

This is a GitHub Copilot agent shim that delegates to the DevSpark
3-tier command override system.

## Resolution Order

1. `.documentation/{user}/commands/devspark.harvest.md` (personal override)
2. `.documentation/commands/devspark.harvest.md` (team override)
3. `.devspark/defaults/commands/devspark.harvest.md` (stock command)

Use whichever version of the harvest command is found first in the
resolution order above. Follow its instructions exactly.
