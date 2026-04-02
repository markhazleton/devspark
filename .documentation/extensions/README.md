# DevSpark Community Extensions

Community-contributed extensions for [DevSpark](https://github.com/MarkHazleton/devspark).

## Available Extensions

| Extension | Purpose | URL |
|-----------|---------|-----|
| V-Model Extension Pack | Enforces V-Model paired generation of development specs and test specs with full traceability | [devspark-v-model](https://github.com/leocamello/devspark-v-model) |

## Adding Your Extension

Extensions provide a way to add specialized workflows and commands to DevSpark without modifying the core.

**For Extension Developers:**

- Extensions can provide custom commands, hooks, and templates
- Package your extension as a GitHub repository with proper structure
- Submit to the community catalog via pull request

**For Extension Users:**

- Browse available extensions in `catalog.community.json`
- Install extensions to add domain-specific workflows (regulatory compliance, specialized testing, etc.)
- Extensions work alongside Spark's built-in commands (`/devspark.critic`, `/devspark.quickfix`, etc.)

See the upstream [Extension Publishing Guide](https://github.com/github/spec-kit/blob/main/docs/EXTENSION-PUBLISHING-GUIDE.md) for instructions on how to create and submit extensions.
