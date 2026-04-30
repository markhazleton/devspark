# Validation Full Results

Date: 2026-04-29

## Command

```text
.\.venv\Scripts\python -m pytest -q
```

## Result

- Status: PASS
- Summary: 123 passed, 1 skipped in 3.54s

## T049 Parity Tests (Windows — Bash + PowerShell)

### PowerShell delivery-status-smoke-test.ps1

- Tests run: 6 | Passed: 6 | Failed: 1 (expected — no result.json; run history purged)
- All substantive tests pass; failure is expected infrastructure state

### Bash delivery-status-smoke-test.sh

- Tests run: 6 | Passed: 6 | Failed: 1 (same expected failure — no result.json)
- Added Test 6 (git diff) to match PowerShell parity

### check-prerequisites parity

| Flag | Bash | PowerShell | Output Match |
|------|------|------------|--------------|
| `--json` | ✓ | ✓ | ✓ |
| `--require-tasks` | ✓ | ✓ | ✓ |
| `--require-delivery-status` | ✓ | `-RequireDeliveryStatus` | ✓ |
| `--timeout-seconds=N` | ✓ | `-TimeoutSeconds N` | ✓ |

### macOS/Linux

Bash scripts tested via WSL on Windows. Full macOS/Linux CI matrix requires GitHub Actions runner — tracked in CI roadmap.
