# Legacy 8.x entry-point fixtures

Captured forms of the managed 8.x agent entry points, used to characterize what the retirement
logic must recognize. All content is synthetic or generated; nothing here contains real names,
addresses, credentials or health information.

## Layout

| Directory | Contents |
| --- | --- |
| `branch-base/<agent>/` | Generator output from the unchanged release packager at the branch base (version 8.3.0) |
| `v8.2.0/<agent>/` | Generator output from the unchanged packager extracted from tag `v8.2.0` |
| `quickstart/<family>/` | Shims synthesized from the 8.x quickstart shim templates (identical across 8.x) |
| `foreign/` | Files and skill folders the retirement logic must never delete |

Agents captured: `copilot` (`.github/agents/*.agent.md` plus `.github/prompts/*.prompt.md`),
`claude` (`.claude/commands/*.md`) and `gemini` (`.gemini/commands/*.toml`). The files keep their
native repository paths so a fixture can be copied onto a tree unchanged.

## Subset

Ten of the stock commands are captured instead of all of them to keep the fixtures small: five with
`handoffs:` frontmatter (`next`, `specify`, `implement`, `explain`, `pr-review`) and five without
(`upgrade`, `personalize`, `list-applications`, `add-application`, `taskstoissues`). The tests are
data-driven over whatever is present, and a separate test renders every stock command for every
agent target, so coverage of the full command set does not depend on the subset.

## Capture commands

```powershell
git archive --format=tar -o .tmp-capture\base.tar HEAD
git archive --format=tar -o .tmp-capture\v820.tar v8.2.0
# extract each archive, then in each extraction (Git Bash, offline):
AGENTS=copilot,claude,gemini SCRIPTS=sh bash eng/release/create-release-packages.sh v8.3.0
```

The packager writes one tree per agent under `.genreleases/`; the managed entry-point files were
copied from those trees. `.tmp-capture/` is git-ignored scratch space and is deleted afterwards.

## Notes

- One captured Gemini file (`explain`) has quotes in its description that the packager does not
  escape. It is kept as captured because the recognition rule must accept what was shipped.
- The version 8.2.0 tag has 37 commands and the branch base has 38; only one captured file differs
  between the two sets.
- Line endings are stored as LF. CRLF variants, edited variants (added paragraph, foreign `name`,
  unknown frontmatter key) and quarantine collisions are generated at run time by the tests.
- `foreign/` includes a team-authored skill that reuses a managed name, an orphan generated skill
  whose command is no longer shipped, a generated skill that is still managed, and an unrelated
  team skill.
