# Fixtures: closeout carry-forward

Synthetic bundles (`spec.md`, `tasks.md`, `gates/`) read by `judge.py lifecycle` in
`tests/test_closeout_carry_forward_contract.py`. All content is invented.

| Bundle | Scenario | Lifecycle |
| --- | --- | --- |
| `preserved-accepted-limitation` | Complete closeout carrying a human-accepted limitation; nothing changed | pass |
| `preserved-pre-contract-shape` | Spec from 7.7.1 (no criterion kinds); older-shape closeout with no `evaluated_commit` | pass |
| `invalidated-reopened-work` | Complete closeout, but a task was reopened afterward | fail `incomplete-tasks` |
| `invalidated-evidence` | Complete closeout whose cited verify mode now fails | fail `verify-not-passed` |
| `real-blocking-defect` | Failed requirement recorded as a blocking defect | fail `closeout-not-complete` |
| `legacy-requirement-not-waived` | Old spec with a privacy requirement and a required verify mode, no evidence | fail `verify-not-passed` |
