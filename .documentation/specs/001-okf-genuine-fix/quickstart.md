# Quickstart: OKF Traceability and Genuine Fix Discipline

## Scenario 1: New Feature Emits Knowledge Without JSON Changes

1. Run feature creation in JSON mode for a temporary fixture.
2. Capture the JSON output exactly.
3. Confirm the output still contains only the legacy contract fields expected by current consumers.
4. Confirm `.documentation/specs/<feature>/knowledge/` exists.
5. Validate each knowledge document frontmatter against `templates/schemas/okf-knowledge-document.schema.json`.

Examples:

```bash
scripts/bash/create-new-feature.sh --json "OKF fixture"
scripts/bash/setup-plan.sh --json
```

```powershell
scripts/powershell/create-new-feature.ps1 -Json -FeatureDescription "OKF fixture"
scripts/powershell/setup-plan.ps1 -Json
```

Expected result: JSON consumers remain unaffected and the knowledge document validates.

## Scenario 2: Coverage Validator Reports Existing Knowledge

1. Create a fixture feature with `spec.md`, `tasks.md`, `gates/analyze.md`, and valid `knowledge/*.md`.
2. Run `scripts/bash/validate-knowledge-coverage.sh --feature-dir <fixture> --json`.
3. Run `scripts/powershell/validate-knowledge-coverage.ps1 -FeatureDir <fixture> -Json`.
4. Compare high-level result fields from both outputs.

Examples:

```bash
scripts/bash/validate-knowledge-coverage.sh --feature-dir .documentation/specs/001-okf-genuine-fix --json
```

```powershell
scripts/powershell/validate-knowledge-coverage.ps1 -FeatureDir .documentation/specs/001-okf-genuine-fix -Json
```

Expected result: both validators report equivalent counts and uncovered IDs.

## Scenario 3: Coverage Validator Skips Cleanly

1. Create a fixture feature without a `knowledge/` directory.
2. Run both validators in JSON mode.

Expected result: both validators return `status: skipped` and successful exit codes.

## Scenario 4: Findings Carry Behavioral Intent

1. Inspect analyze and critic command templates.
2. Confirm their finding contract includes `intent_cue`.
3. Inspect site-audit command template.
4. Confirm its finding contract includes `Intent`.

Expected result: all required command surfaces expose behavioral intent before metric-focused remediation.

## Scenario 5: Verify Rejects Metric-Only Proof

1. Inspect verify command guidance.
2. Provide an example proof where complexity decreases but behavior remains unchanged.
3. Confirm the Genuine Fix Guard classifies the proof as failed.

Example:

```text
/devspark.verify Proof: complexity dropped from 14 to 8, but the same inputs,
outputs, authorization behavior, and tests are unchanged.
```

Expected result: metric-only proof with unchanged behavior cannot pass verification.
