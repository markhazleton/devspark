---
evidence:
  - type: code
    ref: templates/commands/add-application.md
    verified_by: inspection
    test_attempted: true
    fallback_reason: "Application registry edits are guided by prompt contracts and require repository-specific validation."
---

# Application Registry

The application registry stores current monorepo application metadata at
`.knowledge/entities/application-registry/registry.json` when a repository uses
multi-app mode. Work packages may be app-scoped, but the registry itself is
durable current truth.
