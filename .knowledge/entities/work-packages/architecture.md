---
evidence:
  - type: schema
    ref: templates/schemas/devspark-work-package.schema.json
    verified_by: inspection
    test_attempted: true
    fallback_reason: "Work-package structure is enforced by prompt instructions and schema review."
---

# Work Packages

Work packages are ephemeral state under `.devspark.work`. Each task carries
links to the permanent code and knowledge where its delta landed. The package
can only be deleted after all complete-task references are populated and
resolve, or are explicitly marked not applicable with a reason.
