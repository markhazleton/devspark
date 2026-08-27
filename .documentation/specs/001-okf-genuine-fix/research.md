# Research: OKF Traceability and Genuine Fix Discipline

## Decision: Use Dual-Written Markdown Knowledge Documents

**Rationale**: Markdown with YAML frontmatter gives humans a readable artifact while allowing tools to validate structured metadata. Keeping the layer parallel to existing JSON preserves backward compatibility.

**Alternatives considered**:

- Extend existing JSON contracts: rejected due to migration risk for current consumers.
- Store traceability only in comments inside spec/tasks/gates: rejected because comments are harder to validate and easier to drift.
- Maintain a single central registry: rejected because it adds coordination overhead and creates merge pressure across unrelated features.

## Decision: Validate Frontmatter With JSON Schema

**Rationale**: The repository already depends on `jsonschema` and `PyYAML`, so contract tests can validate YAML frontmatter without adding dependencies. A JSON Schema is also easy for downstream tools to consume.

**Alternatives considered**:

- Custom ad hoc validators only: rejected because schema drift would be harder to detect.
- Full Markdown AST validation: rejected for initial scope because frontmatter and link coverage are the critical contract.

## Decision: Make Coverage Advisory and Fail-Soft

**Rationale**: Existing features do not have knowledge documents. Analyze and critic should report coverage information where present and skip cleanly when absent.

**Alternatives considered**:

- Hard gate missing knowledge: rejected because it blocks historical features.
- Do not surface coverage until all features migrate: rejected because it delays value for new features.

## Decision: Put Genuine Fix Discipline in Shared Command Guidance

**Rationale**: Fix, review, audit, and verification commands need one canonical rule: state behavioral intent first, then metrics. Pinning this in the preamble contract and tests prevents command-specific drift.

**Alternatives considered**:

- Add guidance only to verify: rejected because findings must carry intent before fixes and proof are generated.
- Rely on reviewer judgment: rejected because the acceptance criteria require deterministic command-surface behavior.

## Decision: Use Shared Python Coverage Logic Behind Platform Wrappers

**Rationale**: The constitution requires Bash and PowerShell parity, while YAML frontmatter arrays and quoting are risky to parse independently in shell languages. Implement the schema validation and coverage aggregation once in Python using existing `PyYAML` and `jsonschema`; keep Bash and PowerShell scripts as thin wrappers that preserve the platform entry points.

**Alternatives considered**:

- Python-only CLI validator without platform scripts: rejected because installed template users expect Bash and PowerShell helpers.
- Native Bash and PowerShell parsers: rejected because equivalent YAML parsing across platforms would require a larger fixture matrix and still carry drift risk.

## Resolved Unknowns

- Schema location: `templates/schemas/okf-knowledge-document.schema.json`.
- Knowledge folder location: `.documentation/specs/<feature>/knowledge/`.
- Validator names: `scripts/bash/validate-knowledge-coverage.sh` and `scripts/powershell/validate-knowledge-coverage.ps1`.
- Parser strategy: shared Python module with Bash and PowerShell wrappers.
- Advisory behavior: absent `knowledge/` exits successfully with a skip result.
- Anti-gaming behavior: `/devspark.verify` fails proof that only demonstrates metric decrease and unchanged behavior.
