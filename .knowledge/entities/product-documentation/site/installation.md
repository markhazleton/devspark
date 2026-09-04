# Install DevSpark

## Current Release

[![Current Release](https://img.shields.io/github/v/release/markhazleton/devspark?label=current%20release)](https://github.com/markhazleton/devspark/releases/latest)

**Current version:** [v4.2.0](https://github.com/markhazleton/devspark/releases/tag/v4.2.0)

DevSpark is installed through quickstart prompts. There is no separate DevSpark
program to install.

## Approved Install Path

1. Open your AI coding assistant in the target repository.
2. Paste the raw quickstart prompt for your assistant:
   - [GitHub Copilot](https://raw.githubusercontent.com/markhazleton/devspark/main/quickstart/devspark_quickstart_copilot.md)
   - [Claude Code](https://raw.githubusercontent.com/markhazleton/devspark/main/quickstart/devspark_quickstart_claudecode.md)
   - [Cursor](https://raw.githubusercontent.com/markhazleton/devspark/main/quickstart/devspark_quickstart_cursor.md)
   - [Codex](https://raw.githubusercontent.com/markhazleton/devspark/main/quickstart/devspark_quickstart_codex.md)
   - [Antigravity](https://raw.githubusercontent.com/markhazleton/devspark/main/quickstart/devspark_quickstart_antigravity.md)
   - [Generic agent](https://raw.githubusercontent.com/markhazleton/devspark/main/quickstart/devspark_quickstart_generic.md)
3. Let the agent detect the repository state, preview the plan, and install the
   framework-owned files.
4. Start with `/devspark.specify`.

The quickstart prompt installs stock command prompts, helper scripts, templates,
schemas, skills, `.devspark/VERSION`, and agent-specific shims. It also checks
`.knowledge/entities/` and `.knowledge/ontology/` on every execution, repairs
missing scaffold files, runs ontology generation when possible, and preserves
authored repository-owned `.knowledge/` content.

## Repair

Run the same quickstart prompt again. If expected stock files are missing or
stale, the prompt enters repair mode, refreshes framework-owned assets, and
rechecks the knowledge scaffold.

## Upgrade

Run the same quickstart prompt again. It compares `.devspark/VERSION` with the
latest GitHub release and refreshes framework-owned assets when a newer release
is available. If `.documentation/` or `.documenation/` exists, the quickstart
classifies each document as staged for release, in-flight `.devspark.work/`, or
durable `.knowledge/` current truth before moving it.
