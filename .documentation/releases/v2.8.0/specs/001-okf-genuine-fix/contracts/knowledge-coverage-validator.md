# Contract: Knowledge Coverage Validator

## Commands

```bash
scripts/bash/validate-knowledge-coverage.sh --feature-dir <absolute-feature-dir> --json
```

```powershell
scripts/powershell/validate-knowledge-coverage.ps1 -FeatureDir <absolute-feature-dir> -Json
```

## Success Behavior

The validator exits successfully for advisory mode in all normal cases:

- `status: ok` when knowledge documents are present and coverage is complete.
- `status: warn` when knowledge documents exist but coverage or schema gaps are found.
- `status: skipped` when `knowledge/` is absent.

## JSON Output

```json
{
  "status": "warn",
  "feature_dir": "C:/path/.documentation/specs/001-feature",
  "knowledge_dir": "C:/path/.documentation/specs/001-feature/knowledge",
  "requirements_total": 3,
  "tasks_total": 4,
  "gate_evidence_total": 2,
  "requirements_covered": 2,
  "requirements_uncovered": ["FR-003"],
  "tasks_without_requirements": [],
  "evidence_without_requirements": [],
  "messages": ["FR-003 has tasks but no gate evidence"]
}
```

## Analyze and Critic Integration

Analyze and critic prompts must run the validator as an additive pass after loading feature artifacts. They must report validator output under advisory coverage and must not fail the gate when `status` is `skipped`.
