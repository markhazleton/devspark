# DevSpark Copilot Instructions

DevSpark is a prompt-first lifecycle toolkit. Treat the markdown prompts,
quickstart prompts, helper scripts, templates, schemas, and `.knowledge/` files
as the product.

There is no DevSpark command-line application. The only approved way to install,
upgrade, or repair DevSpark is to run the appropriate quickstart prompt from
`quickstart/` in the target repository.

Preserve these boundaries:

- `.devspark/` is framework-owned.
- `.knowledge/` is current truth.
- `.knowledge/` is repository-owned documentation.
- `.devspark.work/` is temporary work state and should not be committed.

When changing scripts, maintain Bash and PowerShell parity.
