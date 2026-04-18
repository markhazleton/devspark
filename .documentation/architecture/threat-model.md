# Threat Model — Tiered Workflow Engine

Concise threat surface for the v2 workflow engine. Each row lists the threat,
the implementing mitigation, and the file that enforces it.

| Threat | Mitigation | Enforced by |
|--------|------------|-------------|
| Prompt-output-as-untrusted-input — model emits `--repo evil/owner` as the issue title; downstream `gh` re-targets the issue. | Issue adapter constructs the payload as a Python dict and pipes JSON to `gh api repos/markhazleton/devspark/issues -X POST --input -`. No model-generated content ever appears in argv. | `src/devspark_cli/issues.py`, `tests/test_issue_adapter_contract.py` |
| Pause-state corruption — partial write or truncation between pause and resume. | Atomic write: `<file>.tmp` → `fsync` → `os.replace`; resume verifies SHA-256 `context_checksum` and `schema_version`; mismatch → `EXIT_RESUME_FAILED` (25). | `src/devspark_cli/runner/executor.py`, `tests/test_pause_resume_contract.py` |
| Telemetry concurrent-write — two `devspark run` invocations append to the same JSONL and produce interleaved/truncated lines. | OS-level exclusive lock around each append (`fcntl.flock` POSIX, `msvcrt.locking` Windows); per-event size cap (4 KB) and per-context cap (1 KB). | `src/devspark_cli/runner/telemetry.py`, `tests/test_telemetry_concurrency_contract.py` |
| `gh` token over-scope — the running token can write to repos the user did not intend. | Pre-call confirmation prints repo + title + labels and requires interactive `y/yes`. `--yes` bypass requires explicit operator action; non-interactive without `--yes` exits 20. | `src/devspark_cli/issues.py`, `tests/test_issue_adapter_contract.py` |
| Dirty-working-tree assumption — guardrail diff baseline is wrong if uncommitted changes precede the run. | `devspark run` refuses to start when `git status --porcelain` is non-empty unless `--allow-dirty` is supplied (FR-015a). | `src/devspark_cli/run_commands.py` |
| Workflow definition tampering — an untrusted contributor edits a workflow in `templates/workflows/`. | All workflow definitions live in the repo and pass `devspark workflows validate` in CI; resolver trusts only files under repo-relative tiers (no `../`). | `src/devspark_cli/runner/loader.py`, `src/devspark_cli/resolution.py` |

Out of scope for this release: malicious atomic-prompt content already merged
to `templates/prompts/atomic/` (covered by normal code review and constitution
gates); compromise of the `gh` binary itself.
