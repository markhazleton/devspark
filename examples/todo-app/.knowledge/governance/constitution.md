# Todo App Constitution

## Core Principles

### I. Simplicity First

Every feature must be achievable with the simplest possible implementation. No frameworks, no ORMs, no build tools unless the complexity is justified by a concrete user need.

### II. Test Coverage

All business logic must have automated tests. No PR merges without passing tests. Manual-only testing is not acceptable for any feature that handles user data.

### III. Accessibility

The app must be usable with keyboard-only navigation and screen readers. WCAG 2.1 AA compliance is non-negotiable.

## Technology Stack

- **Language**: TypeScript
- **Runtime**: Node.js 20+
- **Storage**: SQLite (file-based, no server)
- **Testing**: Vitest

## Governance

**Version**: 1.0 | **Ratified**: 2026-04-02
