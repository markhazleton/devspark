# Feature Specification: Synthetic Sample

## Requirements *(mandatory)*

- **FR-001**: System MUST copy each source record into its own versioned record.

### Key Entities

- Source record has exactly one versioned record.

## Clarifications

### Session 2000-01-01

- Q: Is a re-copy allowed? → A: Yes, repeating the same copy is acceptable.

## Success Criteria

- SC-001: Every source record has one versioned record.

## Assumptions

- Operators run the copy manually.

## Out of Scope

- Automatic reconciliation.

## Minimum Sufficient Change

- Nothing else is required.
