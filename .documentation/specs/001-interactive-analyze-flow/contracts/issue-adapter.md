# Contract: Issue Adapter

The `suggest-improvement` workflow's `create-issue` step invokes the issue adapter implemented in `src/devspark_cli/issues.py`. Validated by `tests/test_issue_adapter_contract.py`.

## Behavior

- Always targets `markhazleton/devspark` regardless of the cwd repo or any caller-supplied override.
- Invokes `gh api repos/markhazleton/devspark/issues -X POST --input -` with a JSON payload on stdin. The adapter MUST NOT pass model-generated content via `--title`/`--body` flags because repeated flags allow prompt-injection re-targeting (the `gh` CLI honors the last `--repo` flag). Using the typed `gh api` endpoint with a JSON body removes the flag-parsing surface entirely.
- Returns the issue URL on success; populates `context.issue_url` for subsequent steps.
- Before invocation, the adapter MUST print the resolved repo, title, classification, and labels to stderr and require interactive confirmation. `--yes` skips confirmation; `--non-interactive` without `--yes` aborts with `EXIT_AUTONOMY_REQUIRED`.

| Key | Required | Description |
|-----|----------|-------------|
| `proposal.title` | yes | Issue title; truncated to 200 chars if longer |
| `proposal.classification` | yes | Mapped to label: `bug` → `bug`, `enhancement` → `enhancement`, `prompt-quality` → `area:prompts`, `workflow-design` → `area:workflows`, `documentation` → `documentation` |
| `proposal.context` | yes | Body section "Context" |
| `proposal.current_behavior` | yes | Body section "Current behavior" |
| `proposal.expected_behavior` | yes | Body section "Expected behavior" |
| `proposal.suggested_fix` | no | Body section "Suggested fix" (omitted if absent) |

## Body template

```markdown
> Filed by `/devspark.suggest-improvement` (workflow run `<run_id>`)

### Classification

`<classification>`

### Context

<context>

### Current behavior

<current_behavior>

### Expected behavior

<expected_behavior>

### Suggested fix

<suggested_fix>
```

## Failure modes

| Condition | Exit code | Behavior |
|-----------|-----------|----------|
| `gh` not installed | `EXIT_GH_UNAVAILABLE` (10) | Print install URL `https://cli.github.com/`, abort workflow |
| `gh` not authenticated | `EXIT_GH_UNAUTHENTICATED` (11) | Print `gh auth login` guidance, abort |
| GitHub API error | `EXIT_GH_API` (12) | Surface `gh` stderr, abort, emit `failed` telemetry event |
| Network unreachable | `EXIT_GH_NETWORK` (13) | Suggest retry, abort |

## Security

- Title and body are passed via stdin JSON to `gh api`, never as CLI flags. The adapter MUST construct the payload as a Python dict and JSON-serialize it; it MUST NOT format strings into the argv. This eliminates prompt-injection re-targeting via embedded `--repo` or other flags.
- Labels list is fixed by the classification mapping; the adapter MUST NOT accept arbitrary user-supplied labels.
- The adapter MUST display the resolved repo, title, and labels and require interactive confirmation before invoking `gh`. Bypass with `--yes` for trusted automation only.

## Non-goals (explicitly out of scope)

- Multi-platform support (AzDO, GitLab) — deferred to a future feature.
- Per-call repo override — by clarification, the canonical target is fixed to `markhazleton/devspark`.
- Issue update / comment — `suggest-improvement` only creates new issues.
