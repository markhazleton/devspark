# Quickstart: Harness Delivery Integrity

## Feature Overview

The Harness Delivery Integrity feature solves a critical problem: harness runs can complete successfully while reporting the workflow executed, even when **no actual implementation work occurred**. This leads to false-positive "ready to create PR" signals and unreliable automation.

**Solution**: Dual-outcome run semantics that track both workflow completion and implementation evidence:

- **`workflow_status`**: Did the harness execute all specified steps? (Yes/No)
- **`delivery_status`**: Did implementation work actually occur? (Met/Unmet)
- **`create_pr_ready`**: Is this run safe to auto-promote to PR creation? (True/False, gated by delivery_status)

A run is only `create_pr_ready=true` when **both** workflow completes **AND** delivery evidence (e.g., source file mutations) is confirmed.

## Prerequisites

- Python 3.11+ environment active
- Feature branch checked out: `001-harness-delivery-integrity`
- Adapter available for chosen execution mode

## Quick Start: Testing Delivery Integrity in Your Workflow

### Step 1: Run a Basic Harness with Delivery Tracking

```bash
# Create a simple harness spec that runs without making changes
devspark run --harness-spec path/to/no-op-run.yaml

# Review the run outcome:
cat .documentation/devspark/runs/latest/result.json | jq '.delivery_status, .create_pr_ready'

# Expected output for no-op run:
# "unmet"
# false
```

### Step 2: Review the No-Change Explainer

When a run completes workflow but creates no source changes, a detailed explainer is generated:

```bash
# View the no-change explainer artifact
cat .documentation/devspark/runs/latest/artifacts/no-change-explainer.md
```

This explains why despite successful workflow execution, `delivery_status` is `unmet` (e.g., "No mutations detected in src/ or test/").

### Step 3: Create a Harness with Source Changes

```bash
# Create a run that modifies src/ files
devspark run --harness-spec path/to/with-changes.yaml

# Review the delivery status
cat .documentation/devspark/runs/latest/result.json | jq '.delivery_status, .create_pr_ready'

# Expected output for successful implementation run:
# "met"
# true
```

### Step 4: Verify Create-PR Gating

The system enforces gating before PR creation:

```bash
# Try to create PR from unmet delivery run (will be rejected)
devspark create-pr --run-id <run-id-with-no-changes>

# Error: "Delivery status is unmet. Implement required changes before creating PR."

# Try to create PR from met delivery run (will succeed)
devspark create-pr --run-id <run-id-with-changes>

# Success: PR created with implementation evidence attached
```

## 1. Validate Baseline

```powershell
pytest -q
```

## 2. Implement Core Contracts

- Add/extend run outcome model to include `workflow_status`, `delivery_status`, and `create_pr_ready` semantics.
- Add delivery checks including default `src/**|test/**` mutation evidence.
- Add adapter doctor/preflight capability profile and fail-fast write-incompatibility behavior.

## 3. Implement Iterative Analyze/Critic Loops

- Enforce max-pass default (3)
- Re-run checks after each pass
- Persist iteration records and convergence status
- Fail with convergence report when unresolved blocking findings remain

## 4. Implement Hands-Off Lifecycle Mode

- Add single-run mode chaining: `plan -> tasks -> analyze -> critic -> implement -> create-pr -> pr-review`
- Enforce hard gates and explicit reason codes
- Emit final decision packet for human PR decision

## 5. Update Templates, Scripts, and Docs

- Add strict harness template with mutation-aware defaults
- Keep Bash/PowerShell behavior equivalent
- Update docs for adapter readiness, gate semantics, and no-change explainers

## 6. Validate

```powershell
pytest -q
```

## 7. Smoke Test Hands-Off Behavior

- Run preflight/doctor for selected adapter
- Execute a hands-off run in a controlled feature branch
- Confirm run artifacts include delivery checks, iteration records, and decision packet

## Troubleshooting

### "Delivery status is unmet" but I made changes

The delivery check looks for mutations in `src/` and `test/` directories. If your implementation modifies other paths (docs, config, etc.), the delivery check won't detect them. Customize the delivery evidence rule by editing `.documentation/specs/001-harness-delivery-integrity/contracts/run-outcome-contract.md`.

### "No-change explainer" appears but I expected changes

Review the harness spec and adapter configuration:

1. Does the adapter support write operations in your environment?
2. Did the harness spec include implementation stages that create source mutations?
3. Check adapter doctor output: `devspark adapter-doctor --adapter <name>`

### Tests fail with decode errors on Windows

This is expected with PowerShell output containing non-UTF bytes. The system uses `errors="replace"` to handle this gracefully. If tests fail, check that telemetry includes a `harness.decode.replacement` event recording the incident.

## Implementation Checklist for Integration

When adopting this feature in your DevSpark instance:

- [ ] Update `.documentation/memory/constitution.md` to reference delivery integrity policies
- [ ] Create a custom harness spec using `templates/workflows/harness-strict-template.md` as reference
- [ ] Add delivery evidence rules matching your repository structure (src/test paths)
- [ ] Configure adapter doctor probe results for your chosen adapters
- [ ] Run full test suite: `pytest tests/test_delivery_status_contract.py -v`
- [ ] Document any custom delivery evidence policies in team documentation
- [ ] Test hands-off mode in a controlled branch before using in CI/CD
