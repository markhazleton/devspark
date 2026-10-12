# Upgrade fixture trees

Compact repository layouts for exercising the retirement of 8.x entry points. Each tree is combined
with `_common/` at test time: `_common/` holds the pre-existing `.devspark/`, `.devspark.work/`,
`.knowledge/` and `.archive/` content that an upgrade must leave untouched, and each tree adds only
what makes it different. All content is synthetic.

| Tree | What it represents |
| --- | --- |
| `plain-copilot` | Unmodified 8.x Copilot install (agent shims and prompt companions) |
| `quickstart-shim` | Shims authored by the 8.x quickstart (Copilot and Claude Code) |
| `customized` | Install with a developer override and a team override under `.devspark.work/` |
| `edited-shim` | Install where one managed shim was edited by the team |
| `interrupted` | Install after a partly completed retirement (companion removed, earlier quarantine present) |
| `foreign-files` | Install that also holds foreign files and skill folders |
| `md-agent` | Markdown agent install (Claude Code) |
| `toml-agent` | TOML agent install (Gemini CLI) |

The managed files are copies of the captured forms in `../legacy-8x/branch-base/` and
`../legacy-8x/quickstart/`, restricted to the `next` and `specify` commands. The edited shim differs
from the captured form by one appended paragraph.
