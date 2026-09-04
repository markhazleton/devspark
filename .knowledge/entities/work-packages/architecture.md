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
links to the permanent code, tests, and knowledge where its delta landed. A
completed or verified package remains there until release. Release is the sole
archive writer and moves a package intact only after all task references are
populated and resolve, or are explicitly marked not applicable with a reason.
