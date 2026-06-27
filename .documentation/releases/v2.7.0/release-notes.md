# Release Notes: v2.7.0

## Release Metadata

- **Version**: v2.7.0
- **Release Date**: 2026-06-27
- **Release Window**: 2026-06-20 → 2026-06-27
- **Previous Version**: v2.6.0
- **Commit Range**: `fd80ba76fda4c044431f8795eb342d24a71f368c..4acdefa0b54e28296681db87fd5479755cfff0ee` (`v2.6.0..HEAD`)
- **Commits**: 4
- **Contributors**: 1
- **Merged PRs**: 0

## Highlights

This release closes a real gap users hit chaining `specify → plan → tasks → critic → analyze` by hand: critic and analyze findings now have a path back into `tasks.md`. Re-running `/devspark.tasks` after `tasks.md` already exists merges both gate reports (deduped, severity-sorted) into a `## Gate Remediation` task phase, and `/devspark.implement` marks each resolved finding back in its originating gate file — so re-running critic/analyze converges instead of re-reporting the same issues.

A new `full-cycle` workflow/alias chains the entire lifecycle with `autonomy.level: autonomous` and guardrails instead of mandatory pauses, for users who want fewer checkpoints. It ships in two forms: `templates/workflows/full-cycle.yaml` (sequenced via `devspark run full-cycle`, still expects an agent driving the conversation) and `full-cycle.harness.yaml` (a HarnessSpec for genuinely unattended execution via `devspark harness run --hands-off`). Eight command prompts (`implement`, `tasks`, `create-pr`, `quickfix`, `analyze`, `address-pr-review`, `specify`, `clarify`) now recognize a `--auto` autonomy convention that auto-selects the recommended option at each gate instead of waiting — while still hard-stopping on constitution/SHOWSTOPPER violations.

The rest of the cycle was a documentation accuracy pass: every command prompt that runs long now states its completion condition and chat-output budget up front instead of only at the final step, `implement.md` had three redundant steps merged into two, and a sweep across README/CHANGELOG/FAQ/index/harness docs corrected several pre-existing staleness issues found along the way — a missing `codex` adapter in three docs, a stale "27 commands" count in four places, a missing `/devspark.taskstoissues` row, a broken link to a file that never existed, and an `autonomy-model.md` claim that didn't match the actual `executor.py` behavior.

## New Features

### Gate Remediation Merge and Finding Resolution Sync

`/devspark.tasks` detects whether `tasks.md` already exists; on a re-run it merges `gates/critic.md` + `gates/analyze.md` findings into a deduped, severity-sorted `## Gate Remediation` task phase with elaborated recommendations. `/devspark.implement` flips a finding's `status` to `resolved` (and fills `outcome`) in its originating gate file when the task tagged `(resolves: <finding_id>)` completes.

### `--auto` Autonomy Convention

`implement.md`, `tasks.md`, `create-pr.md`, `quickfix.md`, `analyze.md`, `address-pr-review.md`, `specify.md`, and `clarify.md` recognize a standing `--auto` instruction and auto-select the recommended option at "ask the user" gates, recording `auto-selected: true` under `## Gate Acknowledgements`. Constitution/SHOWSTOPPER violations, quickfix FAIL findings, and `execution_mode: manual` findings are never auto-bypassed; PR creation under `--auto` defaults to `--draft`.

### `full-cycle` Workflow, Alias, and Harness Spec

A fourth workflow/alias pair chaining all nine lifecycle steps with `autonomy.level: autonomous` and guardrails (`max_files_changed`, `restricted_paths`, `max_total_lines_changed`) instead of `pause_after` checkpoints. `full-cycle.harness.yaml` provides the same chain as `agent_task` steps for execution via `devspark harness run --adapter claude_code --hands-off`, with validation rules that resolve the active feature directory dynamically instead of hardcoding a path.

## Bug Fixes

- Removed unused `logo_large.webp` and `logo_small.webp` from `.documentation/media/`.
- Updated the release-notes generator's agent count to 18+.
- Corrected `.documentation/autonomy/autonomy-model.md`'s `autonomous` level description, a stale "27 commands" count (4 files), a missing `codex` adapter listing (3 files), a missing `/devspark.taskstoissues` row in README.md, and a broken `templates/README.md` link.

## Breaking Changes

None.

## Deprecations

None.

## Architectural Decisions

- **ADR-008**: Prompt-Level Autonomy Override and the full-cycle Lifecycle — [View](../../decisions/ADR-008.md)

## Deferred Features

None — no pending specs at release time.

## Upgrade Guide

No breaking changes. Consumer projects receive the new version stamp and the `full-cycle` workflow/alias/harness-spec files the next time they run `devspark upgrade`. The `--auto` convention is prompt-level — no CLI flag parsing changed, so existing automation is unaffected; opt in by including `--auto` in a command invocation or stating a standing autonomy instruction in the conversation.

## Metrics

| Metric | Value |
|--------|-------|
| Features Delivered | 3 |
| Bugs Fixed | 6 |
| PRs Merged | 0 |
| Files Changed | 32 |
| Tests Added | 0 |
| Breaking Changes | 0 |
| ADRs Created | 1 |
| Contributors | 1 |
| Commits | 4 |

---

Release documentation generated by /devspark.release
