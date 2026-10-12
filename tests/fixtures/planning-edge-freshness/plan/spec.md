---
classification: full-spec
required_gates: checklist, analyze, critic
---
# Export Report

**Status**: Draft

## Requirements

- The system MUST export one report as a CSV file.

## Constraints

- Exports MUST NOT call any network service.

## Context

- Reports are small; a few hundred rows at most.
