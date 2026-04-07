# Repository Constitution (Full Monorepo Fixture)

## Core Principles

### I. Backward Compatibility (NON-NEGOTIABLE)

Existing single-application repositories must continue to work without restructure or behavior changes.
New capabilities are additive; they must never force migration on repositories that do not opt in.

### II. Explicit Over Implied (NON-NEGOTIABLE)

Application scope, review scope, and governance scope must be declared explicitly.
DevSpark must not silently infer scope from working directory, branch naming, or heuristic detection.
Ambiguous context must produce a clear error, not a guess.

### III. Ownership Boundary (NON-NEGOTIABLE)

`.devspark/` is the installed framework payload and the only directory DevSpark installs, upgrades, or
removes. `.documentation/` directories at repo and app level are repository-owned work product.
Install and upgrade flows must never add, remove, or modify files under any `.documentation/` directory.

### IV. Governance Authority

Repository-wide governance is authoritative over all applications.
Application-level governance may extend or strengthen repo-wide rules but MUST never weaken MANDATORY
repo-wide rules. Constitution violations are showstopper severity in reviews.

### V. Simplicity

Prefer conventions over configuration. Prefer simple resolution models over flexible ones.

### VI. Platform Parity

Bash and PowerShell script behavior MUST remain functionally equivalent.

## Additional Constraints

- All API endpoints MUST include health check routes
- All production services MUST have structured logging
- All deployable applications MUST pass integration tests before release
