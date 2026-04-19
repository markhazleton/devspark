# Quickstart: Harness Delivery Integrity

## Prerequisites

- Python 3.11+ environment active
- Feature branch checked out: `001-harness-delivery-integrity`
- Adapter available for chosen execution mode

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
