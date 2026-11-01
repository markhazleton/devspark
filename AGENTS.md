# DevSpark Development Guidelines

<!-- DevSpark — © 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com -->

Auto-generated from all feature plans. Last updated: 2026-07-26

## Active Technologies

- Markdown; Python 3.11+ for existing validation and tests; PowerShell 7+ and Bash 4+ where scripts are changed + Existing repository scripts, PyYAML, pytest, and JSON Schema tooling; no new dependencies (009-spec-lean-shift-left)
- Repository files only (009-spec-lean-shift-left)
- PowerShell 7+ and Bash 4+ (Git Bash at `C:\Program Files\Git\bin\bash.exe` for Bash twins on Windows) for scripts and packagers; Python 3.11+ for tests (`.venv\Scripts\python.exe` with `PYTHONPATH=src`); Markdown with YAML frontmatter for commands, contracts and docs. + existing only: `jq`, `zip`, PyYAML, `jsonschema`, pytest, ruff, docfx (local tool), `npx --yes markdownlint-cli2@0.20.0`. No new package. (008-spec-agent-skills-distribution)
- Files only. One new committed generated tree (`templates/consumer-skills/`), one new manifest category, one new registry field (`skills_dir`). No state store, no version-stamp field. (008-spec-agent-skills-distribution)
- Python 3.11+ (`judge.py`, tests), PowerShell 7+, Bash 4+ (Git Bash on Windows for twin tests) + PyYAML (already used by `judge.py`), `jq` (already required by the Bash `next` script); no new package (006-spec-planning-edge-freshness)
- Files only (one plan frontmatter field; no state store) (006-spec-planning-edge-freshness)
- Python 3.11+ (tests), PowerShell 7+, Bash 4+ (Git Bash on Windows for twin tests) + PyYAML (already used by `judge.py`), existing `common.*` helpers; no new package (005-spec-knowledge-consumption)
- Files only (`knowledge/feature.md` links) (005-spec-knowledge-consumption)
- Python 3.11+, PowerShell 7+, Bash 4+ (Git Bash on Windows for twin tests) + PyYAML (already used by `judge.py`), existing `common.*` helpers; no new package (005-spec-knowledge-consumption)
- Files only (`plan.md` frontmatter field, `knowledge/feature.md` links) (005-spec-knowledge-consumption)
- Markdown command and contract templates; Python 3.11+ for the contract test + pytest (existing); no new package (004-spec-qa-acceptance-planning)
- Files only (004-spec-qa-acceptance-planning)
- Python 3.11+, PowerShell 7+, Bash 4+ + Python standard library (`hashlib`, `tokenize`, `pathlib`, `subprocess`, `tempfile`, `json`), PyYAML, existing shared shell helpers; no new package (002-spec-knowledge-drift-detection)
- YAML frontmatter, generated JSON reports, and canonical baseline byte files under `.knowledge/evidence/source-baselines/` (002-spec-knowledge-drift-detection)
- PowerShell 7+ and Bash 4+ for helpers; Markdown with YAML frontmatter for command templates; Python 3.11+ for contract tests + Azure CLI (`az`) with the `azure-devops` extension; `jq` for the Bash helper; existing `scripts/{powershell,bash}/common.*` and `platform.*`; no new Python packages (001-spec-azdo-work-tracking)
- Filesystem only — `.devspark.work/devspark.json` for configuration and the temporary feature record under `.devspark.work/specs/<feature>/` for the linkage record. No database. (001-spec-azdo-work-tracking)
- PowerShell 7+ and Bash (dual-language scripts, Principle VI parity); Python + Existing shared helpers `scripts/{powershell,bash}/common.*` (003-spec-agent-knowledge-ontology)
- Filesystem only — markdown with YAML frontmatter (knowledge nodes), JSON Schema (003-spec-agent-knowledge-ontology)

- PowerShell 7+ and Bash (existing dual-script convention); Python 3.11+ for the test suite that asserts script contract parity + existing shared helpers `scripts/{powershell,bash}/common.*`; no new external packages (005-spec-okf-knowledge-docs)
- filesystem — markdown files with YAML frontmatter under `.devspark.work/specs/<feature>/knowledge/`; N/A for a database (005-spec-okf-knowledge-docs)

- PowerShell 7+ and Bash (dual-language scripts); Python 3.11+ for the test suite + `git`; existing shared helpers in `scripts/{powershell,bash}/common.*`; reused functions `ConvertTo-CleanBranchName`, collision-guard logic (001-unified-new-branch)

## Project Structure

```text
src/
tests/
```

## Commands

cd src; pytest; ruff check .

## Code Style

PowerShell 7+ and Bash (dual-language scripts); Python 3.11+ for the test suite: Follow standard conventions

## Recent Changes

- 009-spec-lean-shift-left: Added Markdown; Python 3.11+ for existing validation and tests; PowerShell 7+ and Bash 4+ where scripts are changed + Existing repository scripts, PyYAML, pytest, and JSON Schema tooling; no new dependencies

- 008-spec-agent-skills-distribution: Added PowerShell 7+ and Bash 4+ (Git Bash at `C:\Program Files\Git\bin\bash.exe` for Bash twins on Windows) for scripts and packagers; Python 3.11+ for tests (`.venv\Scripts\python.exe` with `PYTHONPATH=src`); Markdown with YAML frontmatter for commands, contracts and docs. + existing only: `jq`, `zip`, PyYAML, `jsonschema`, pytest, ruff, docfx (local tool), `npx --yes markdownlint-cli2@0.20.0`. No new package.

- 006-spec-planning-edge-freshness: Added Python 3.11+ (`judge.py`, tests), PowerShell 7+, Bash 4+ (Git Bash on Windows for twin tests) + PyYAML (already used by `judge.py`), `jq` (already required by the Bash `next` script); no new package

<!-- MANUAL ADDITIONS START -->

## Verification Command Discipline

Constitution Principle IX governs every command you run to verify your own work. The rules below
are the operational form of it. They exist because the expensive failure mode in this repo is not a
wrong edit — it is a verification loop that burns minutes proving something already known.

**Start narrow, widen only on green.**

- Invoke the thing under test directly before you reach for a suite. Running a helper once takes
  seconds; the workitem contract file takes roughly three minutes serially.
- When a suite is genuinely needed, filter it: a single file, then `-k` for the affected tests.
- Pass `-x` so the run stops at the first failure instead of finishing the remainder.
- Reserve the full suite for final confirmation, never for iterating on a change. Run it in
  parallel, as CI does: `pytest tests -n auto --dist loadgroup` (about 3.5 minutes locally versus
  roughly 27 serially).

**Bound every command.**

- Every command must be non-interactive and carry a timeout. `subprocess.run` calls in tests pass
  an explicit `timeout=`; keep them tight enough that a hang surfaces as a failure.
- If a command runs past what you expected, stop it and report that, rather than waiting it out.

**Stay offline.**

- Tests run against the recorded fixtures under `tests/fixtures/`. Nothing may reach a live
  service, require credentials, or depend on the network.

**Show the output.**

- Stream it. Do not pipe through `Select-Object -Last`, `tail`, or `Out-File` — those buffer until
  the command finishes, which hides both progress and the first failure, and makes a running
  command look hung. Use `Tee-Object` when you also want a log on disk.
- `Select-Object -First` terminates a pipeline early, which corrupts `$LASTEXITCODE`. Capture the
  exit code from an unpiped invocation.

## Running Things In This Repo

- Python is `.venv\Scripts\python.exe`, and pytest needs `$env:PYTHONPATH="src"`.
- The `bash` on PATH is WSL and cannot see `jq`. Run Bash twins with Git Bash at
  `C:\Program Files\Git\bin\bash.exe`.
- This pwsh session echoes late. Prefer single-line `;`-joined commands, and confirm a result with
  a separate read rather than trusting an empty inline response.
- Do not embed multi-step Python/YAML/Markdown parsing in a PowerShell `python -c` one-liner.
  PowerShell quoting and Markdown backticks make that form brittle. Prefer an existing contract
  test or validator; if custom parsing is genuinely needed, use a dedicated script file and run it
  once. After one shell-quoting failure, change command shape instead of retrying the same form.
- Markdown gate: `npx --yes markdownlint-cli2@0.20.0 "**/*.md"`.

## Writing Code Here

- Planning records are temporary. Never write a spec number, requirement id, or task id into
  shipped code, tests, or `.knowledge/`. Linkage points one way: planning documents cite code.
- Constitution VI: a PowerShell script and its Bash twin change in the same commit, always.
- Tests must stay safe to run in parallel. Write only under `tmp_path` or a fixture-owned
  directory, never the repository tree. Expensive shared setup belongs in a `session` or `module`
  fixture: `tests/conftest.py` keeps every test of such a fixture on one xdist worker, so it is
  built once. A module-level result cache needs `pytestmark = pytest.mark.xdist_group(...)` for
  the same reason. Before adding a subprocess call, check whether an existing test already
  produces that exact output and assert against it instead of invoking the shell again.

<!-- MANUAL ADDITIONS END -->

<!-- markdownlint-disable MD012 MD025 -->

<!-- DEVSPARK SHARED CONTEXT:START -->
# AGENTS.md

## About DevSpark

**DevSpark** is an Adaptive System Life Cycle Development (ASLCD) toolkit. It provides specification-driven workflows with constitution-powered quality gates, right-sized execution paths, and operational lifecycle guidance.

There is no DevSpark CLI or installable package. It is entirely prompt-first: an agent installs and
upgrades the framework by following the per-agent quickstart guide, which fetches stock prompts,
scripts, and templates directly from the release manifest into a project's `.devspark/` directory.

The toolkit supports multiple AI coding assistants, allowing teams to use their preferred tools while maintaining consistent project structure and development practices.

---

## Canonical Layout and Platform Shims

DevSpark uses a strict four-root ownership model:

- `.devspark/` holds framework-managed stock prompts, scripts, and templates
- `.devspark.work/` holds temporary plans, operations, configuration, and overrides
- `.knowledge/` holds current authoritative technical and governance truth, plus published
  user-facing guidance under `.knowledge/guides/`
- `.archive/` holds the landing place for all old work products, grouped by release

Platform-specific directories (`.claude/`, `.github/`, `.cursor/`, etc.) contain only thin shims plus hydrated agent context.

### Agent Registry (`agents-registry.json`)

To prevent hardcoding AI agent identifiers across different workflow scripts and command templates, DevSpark leverages a centralized `agents-registry.json` file located in the repository root.

**Key Features:**

1. **Centralized Configuration**: Defines available agents (e.g., Copilot, Claude Code, Cursor) and their capabilities.
2. **Cross-Editor Support**: Simplifies extending DevSpark to support new IDEs or agent implementations.
3. **Workflow Integration**: Used dynamically by `create-pr` and other workspace scripts to understand which agent platforms are available or active.

When adding a new AI assistant integration to DevSpark, simply append the agent's definition and configuration details to `agents-registry.json`.

### File Layout

```text
`.devspark/`
├── defaults/commands/           ← Stock command prompts (framework-managed)
├── scripts/                     ← Stock helper scripts
└── templates/                   ← Stock templates

.devspark.work/
├── commands/                    ← Team command overrides
├── scripts/                     ← Team script overrides
├── specs/                       ← Temporary planning bundles
├── devspark.json                ← Repository configuration
├── devspark.registry.json       ← Optional multi-app registry
└── {git-user}/commands/         ← Personal command overrides

.knowledge/                      ← Current authoritative project truth

site/
├── src/                         ← Authored public-site content
├── templates/                   ← DocFX presentation customizations
└── _site/                       ← Generated output (ignored)

.claude/commands/                ← Thin shims only
.github/skills/                  ← Thin skills only
.cursor/commands/                ← Thin shims only
```

### Shim Behavior

Each platform shim:

1. Resolves the current git user (`git config user.name`, slug-normalized)
2. Checks for a personalized override at `.devspark.work/{git-user}/commands/devspark.{cmd}.md`
3. Falls back to the shared default at `.devspark.work/commands/devspark.{cmd}.md`
4. Falls back again to `.devspark/defaults/commands/devspark.{cmd}.md`
5. Passes through user input (`$ARGUMENTS` / `{{args}}`) to the resolved prompt

### Multi-User Personalization

Team members can customize any command prompt without affecting others:

- Run `/devspark-personalize {command}` to create a user-scoped copy
- Personalized prompts live in `.devspark.work/{git-user}/commands/`
- Committed to git so team members can share and review customizations
- Delete the personalized file to revert to the shared default

### Personalize Command

The `/devspark-personalize` command creates per-user prompt overrides:

```bash
/devspark-personalize specify       # Personalize the /devspark-specify command
/devspark-personalize plan          # Personalize the /devspark-plan command
/devspark-personalize implement     # Personalize the /devspark-implement command
```

---

## General practices

- Any changes to `__init__.py` for the DevSpark CLI require a version rev in `pyproject.toml` and addition of entries to `CHANGELOG.md`.

## Lightweight Workflow Commands

These commands support the Adaptive System Life Cycle Development (ASLCD) approach, providing right-sized processes for tasks of varying complexity.

### Quickfix Command

The `/devspark-quickfix` command enables rapid fixes without full spec overhead:

**Key Features:**

1. **Auto-Classification**: Automatically classifies tasks as bug-fix, hotfix, minor-feature, config-change, or docs-update
2. **Targeted Validation**: Only validates against constitution principles relevant to the task type
3. **Lightweight Records**: Creates minimal documentation at `/.devspark.work/quickfixes/QF-{YYYY}-{NNN}.md`
4. **Completion Tracking**: Supports marking quickfixes complete with commit/PR references
5. **Scope Detection**: Warns when work expands beyond classification limits

**Usage:**

```bash
/devspark-quickfix fix null pointer in UserService
/devspark-quickfix urgent: payment timeout in checkout
/devspark-quickfix complete QF-2026-001
/devspark-quickfix list
```

### Release Command

The `/devspark-release` command verifies and packages the durable Git delta at release boundaries:

**Key Features:**

1. **Durable Delta**: Builds release context from Git commits and durable changed files
2. **Planning Leak Check**: Blocks release when temporary plans remain in the durable delta
3. **Current-Truth Check**: Verifies affected `.knowledge/` content
4. **CHANGELOG Generation**: Updates release notes from shipped behavior
5. **Version Calculation**: Determines MAJOR/MINOR/PATCH from the durable change
6. **Dry Run Mode**: Previews release changes before committing
7. **Work Retention & Cleanup**: Sweeps `.devspark.work/` retention, archives completed specs/quickfixes, flags orphaned in-flight state, and backstops current-knowledge currentness. Release is the **sole** command that ever moves anything into `.archive/{YYYY-MM-DD}/`.

**Usage:**

```bash
/devspark-release              # Auto-calculate version
/devspark-release 2.0.0        # Explicit version
/devspark-release --dry-run    # Preview only
```

### Constitution Evolution Command

The `/devspark-evolve-constitution` command facilitates constitution amendments:

**Key Features:**

1. **Pattern Analysis**: Scans PR reviews and audits for recurring violation patterns
2. **Gap Detection**: Identifies issues not mapped to existing principles
3. **Proposal Generation**: Creates CAP (Constitution Amendment Proposal) documents
4. **Current-Truth Update**: Applies an approved amendment directly to the constitution and affected knowledge
5. **Proposal Cleanup**: Archives applied or rejected proposals under `.archive/{YYYY-MM-DD}/governance/` instead of retaining a history tree in `.devspark.work/`

**Usage:**

```bash
/devspark-evolve-constitution                          # Full analysis
/devspark-evolve-constitution --from-pr #123           # From specific PR
/devspark-evolve-constitution suggest "API versioning" # Manual suggestion
/devspark-evolve-constitution approve CAP-2026-001     # Approve proposal
/devspark-evolve-constitution reject CAP-2026-002 "Too restrictive"
```

---

## PR Review Command

The `/devspark-pr-review` command is a special command that works independently of the spec-driven development workflow:

### Unique Characteristics

1. **Constitution-Only**: Requires only `/.knowledge/governance/constitution.md` - no spec, plan, or tasks needed
2. **Repository-Wide**: Works for any PR in any branch (main, develop, feature, etc.)
3. **Persistent Storage**: Reviews saved to `/.devspark.work/pr-review/pr-{id}.md` with metadata
4. **Version Tracking**: Tracks commit SHA and timestamp for each review
5. **Update Logic**: Handles multiple reviews of same PR with history
6. **GitHub Integration**: Uses GitHub CLI (`gh`) for PR data extraction

### Implementation Notes

- **Script**: Uses dedicated `get-pr-context.{sh,ps1}` scripts (not `check-prerequisites`)
- **No Feature Context**: Doesn't require feature branch or spec directory
- **JSON Output**: Scripts return PR metadata including commit SHA, files changed, diff availability
- **Error Handling**: Graceful degradation when constitution missing or GitHub CLI unavailable

### Agent Integration

When adding new agents, include `/devspark-pr-review` following the same pattern as other commands:

- Markdown format for most agents
- TOML format for Gemini/Qwen
- Script placeholders: `{SCRIPT}` replaced with `get-pr-context` script path
- Argument placeholder: `$ARGUMENTS` for PR number

See `templates/commands/pr-review.md` for the canonical template.

---

## Adding New Agent Support

This section explains how to add support for new AI agents/assistants to the DevSpark CLI. Use this guide as a reference when integrating new AI tools into the Spec-Driven Development workflow.

### Overview

Specify supports multiple AI agents by generating agent-specific command files and directory structures when initializing projects. Each agent has its own conventions for:

- **Command file formats** (Markdown, TOML, etc.)
- **Directory structures** (`.claude/commands/`, `.windsurf/workflows/`, etc.)
- **Command invocation patterns** (slash commands, CLI tools, etc.)
- **Argument passing conventions** (`$ARGUMENTS`, `{{args}}`, etc.)

### Current Supported Agents

> `agents-registry.json` is the source of truth (`release.commands_dir` per agent). This table is a human-readable mirror — if it ever disagrees with the registry, trust the registry and fix this table.

| Agent                      | Directory              | Format   | CLI Tool        | Description                 |
| -------------------------- | ---------------------- | -------- | --------------- | --------------------------- |
| **Claude Code**            | `.claude/commands/`    | Markdown | `claude`        | Anthropic's Claude Code CLI |
| **Gemini CLI**             | `.gemini/commands/`    | TOML     | `gemini`        | Google's Gemini CLI         |
| **GitHub Copilot**         | `.github/skills/` (`SKILL.md`)         | Markdown | N/A (IDE-based) | GitHub Copilot in VS Code   |
| **Cursor**                 | `.cursor/commands/`    | Markdown | `cursor-agent`  | Cursor CLI                  |
| **Qwen Code**              | `.qwen/commands/`      | TOML     | `qwen`          | Alibaba's Qwen Code CLI     |
| **opencode**               | `.opencode/command/`   | Markdown | `opencode`      | opencode CLI                |
| **Codex CLI**              | `.codex/prompts/`      | Markdown | `codex`         | Codex CLI                   |
| **Windsurf**               | `.windsurf/workflows/` | Markdown | N/A (IDE-based) | Windsurf IDE workflows      |
| **Kilo Code**              | `.kilocode/workflows/` | Markdown | N/A (IDE-based) | Kilo Code IDE               |
| **Auggie CLI**             | `.augment/commands/`   | Markdown | `auggie`        | Auggie CLI                  |
| **Roo Code**               | `.roo/commands/`       | Markdown | N/A (IDE-based) | Roo Code IDE                |
| **CodeBuddy CLI**          | `.codebuddy/commands/` | Markdown | `codebuddy`     | CodeBuddy CLI               |
| **Qoder CLI**              | `.qoder/commands/`     | Markdown | `qodercli`      | Qoder CLI                   |
| **Amazon Q Developer CLI** | `.amazonq/prompts/`    | Markdown | `q`             | Amazon Q Developer CLI      |
| **Amp**                    | `.agents/commands/`    | Markdown | `amp`           | Amp CLI                     |
| **SHAI**                   | `.shai/commands/`      | Markdown | `shai`          | SHAI CLI                    |
| **IBM Bob**                | `.bob/commands/`       | Markdown | N/A (IDE-based) | IBM Bob IDE                 |
| **Antigravity**            | `.gemini/commands/`    | Markdown | N/A (built-in)  | DeepMind Antigravity        |

### Step-by-Step Integration Guide

Follow these steps to add a new agent (using a hypothetical new agent as an example):

#### 1. Add to the shared registry

**IMPORTANT**: Use the actual CLI tool name as the key, not a shortened version.

Add the new agent to `agents-registry.json`. This is the single source of truth for CLI setup, release packaging, and context generation:

```json
{
  "key": "new-agent-cli",
  "name": "New Agent Display Name",
  "folder": ".newagent/",
  "context_file": "AGENTS.md",
  "requires_cli": true,
  "install_url": "https://example.com/install",
  "release": {
    "commands_dir": ".newagent/commands",
    "extension": "md",
    "arg_format": "$ARGUMENTS"
  }
}
```

**Key Design Principle**: The dictionary key should match the actual executable name that users install. For example:

- ✅ Use `"cursor-agent"` because the CLI tool is literally called `cursor-agent`
- ❌ Don't use `"cursor"` as a shortcut if the tool is `cursor-agent`

This eliminates the need for special-case mappings throughout the codebase.

**Field Explanations**:

- `name`: Human-readable display name shown to users
- `folder`: Directory where agent-specific files are stored (relative to project root)
- `install_url`: Installation documentation URL (set to `None` for IDE-based agents)
- `requires_cli`: Whether the agent requires a CLI tool check during initialization

#### 2. Update CLI Help Text

Update the `--ai` parameter help text in the `init()` command to include the new agent:

```python
ai_assistant: str = typer.Option(None, "--ai", help="AI assistant to use: claude, gemini, copilot, cursor-agent, qwen, opencode, codex, windsurf, kilocode, auggie, codebuddy, new-agent-cli, or q"),
```

Also update any function docstrings, examples, and error messages that list available agents.

#### 3. Update README Documentation

Update the **Supported AI Agents** section in `README.md` to include the new agent:

- Add the new agent to the table with appropriate support level (Full/Partial)
- Include the agent's official website link
- Add any relevant notes about the agent's implementation
- Ensure the table formatting remains aligned and consistent

#### 4. Update Release Package Script

Modify `eng/release/create-release-packages.sh`:

##### Add to ALL_AGENTS array

```bash
ALL_AGENTS=(claude gemini copilot cursor-agent qwen opencode windsurf q)
```

##### Add case statement for directory structure

```bash
case $agent in
  # ... existing cases ...
  windsurf)
    mkdir -p "$base_dir/.windsurf/workflows"
    generate_commands windsurf md "\$ARGUMENTS" "$base_dir/.windsurf/workflows" "$script" ;;
esac
```

#### 5. Update Agent Context Scripts

##### Bash script (`scripts/bash/update-agent-context.sh`)

Add file variable:

```bash
WINDSURF_FILE="$REPO_ROOT/.windsurf/rules/devspark-rules.md"
```

Add to case statement:

```bash
case "$AGENT_TYPE" in
  # ... existing cases ...
  windsurf) update_agent_file "$WINDSURF_FILE" "Windsurf" ;;
  "")
    # ... existing checks ...
    [ -f "$WINDSURF_FILE" ] && update_agent_file "$WINDSURF_FILE" "Windsurf";
    # Update default creation condition
    ;;
esac
```

##### PowerShell script (`scripts/powershell/update-agent-context.ps1`)

Add file variable:

```powershell
$windsurfFile = Join-Path $repoRoot '.windsurf/rules/devspark-rules.md'
```

Add to switch statement:

```powershell
switch ($AgentType) {
    # ... existing cases ...
    'windsurf' { Update-AgentFile $windsurfFile 'Windsurf' }
    '' {
        foreach ($pair in @(
            # ... existing pairs ...
            @{file=$windsurfFile; name='Windsurf'}
        )) {
            if (Test-Path $pair.file) { Update-AgentFile $pair.file $pair.name }
        }
        # Update default creation condition
    }
}
```

#### 6. Update CLI Tool Checks (Optional)

For agents that require CLI tools, add checks in the `check()` command and agent validation:

```python
# In check() command
tracker.add("windsurf", "Windsurf IDE (optional)")
windsurf_ok = check_tool_for_tracker("windsurf", "https://windsurf.com/", tracker)

# In init validation (only if CLI tool required)
elif selected_ai == "windsurf":
    if not check_tool("windsurf", "Install from: https://windsurf.com/"):
        console.print("[red]Error:[/red] Windsurf CLI is required for Windsurf projects")
        agent_tool_missing = True
```

**Note**: CLI tool checks are now handled automatically based on the `requires_cli` field in AGENT_CONFIG. No additional code changes needed in the `check()` or `init()` commands - they automatically loop through AGENT_CONFIG and check tools as needed.

## Important Design Decisions

### Using Actual CLI Tool Names as Keys

**CRITICAL**: When adding a new agent to AGENT_CONFIG, always use the **actual executable name** as the dictionary key, not a shortened or convenient version.

**Why this matters:**

- The `check_tool()` function uses `shutil.which(tool)` to find executables in the system PATH
- If the key doesn't match the actual CLI tool name, you'll need special-case mappings throughout the codebase
- This creates unnecessary complexity and maintenance burden

**Example - The Cursor Lesson:**

❌ **Wrong approach** (requires special-case mapping):

```python
AGENT_CONFIG = {
    "cursor": {  # Shorthand that doesn't match the actual tool
        "name": "Cursor",
        # ...
    }
}

# Then you need special cases everywhere:
cli_tool = agent_key
if agent_key == "cursor":
    cli_tool = "cursor-agent"  # Map to the real tool name
```

✅ **Correct approach** (no mapping needed):

```python
AGENT_CONFIG = {
    "cursor-agent": {  # Matches the actual executable name
        "name": "Cursor",
        # ...
    }
}

# No special cases needed - just use agent_key directly!
```

**Benefits of this approach:**

- Eliminates special-case logic scattered throughout the codebase
- Makes the code more maintainable and easier to understand
- Reduces the chance of bugs when adding new agents
- Tool checking "just works" without additional mappings

#### 7. Update Devcontainer files (Optional)

For agents that have VS Code extensions or require CLI installation, update the devcontainer configuration files:

##### VS Code Extension-based Agents

For agents available as VS Code extensions, add them to `.devcontainer/devcontainer.json`:

```json
{
  "customizations": {
    "vscode": {
      "extensions": [
        // ... existing extensions ...
        // [New Agent Name]
        "[New Agent Extension ID]"
      ]
    }
  }
}
```

##### CLI-based Agents

For agents that require CLI tools, add installation commands to `.devcontainer/post-create.sh`:

```bash
#!/bin/bash

# Existing installations...

echo -e "\n🤖 Installing [New Agent Name] CLI..."
# run_command "npm install -g [agent-cli-package]@latest" # Example for node-based CLI
# or other installation instructions (must be non-interactive and compatible with Linux Debian "Trixie" or later)...
echo "✅ Done"

```

**Quick Tips:**

- **Extension-based agents**: Add to the `extensions` array in `devcontainer.json`
- **CLI-based agents**: Add installation scripts to `post-create.sh`
- **Hybrid agents**: May require both extension and CLI installation
- **Test thoroughly**: Ensure installations work in the devcontainer environment

## Agent Categories

### CLI-Based Agents

Require a command-line tool to be installed:

- **Claude Code**: `claude` CLI
- **Gemini CLI**: `gemini` CLI
- **Cursor**: `cursor-agent` CLI
- **Qwen Code**: `qwen` CLI
- **opencode**: `opencode` CLI
- **Amazon Q Developer CLI**: `q` CLI
- **CodeBuddy CLI**: `codebuddy` CLI
- **Qoder CLI**: `qodercli` CLI
- **Amp**: `amp` CLI
- **SHAI**: `shai` CLI

### IDE-Based Agents

Work within integrated development environments:

- **GitHub Copilot**: Built into VS Code/compatible editors
- **Windsurf**: Built into Windsurf IDE
- **IBM Bob**: Built into IBM Bob IDE

## Command File Formats

### Markdown Format

Used by: Claude, Cursor, opencode, Windsurf, Amazon Q Developer, Amp, SHAI, IBM Bob

**Standard format:**

```markdown
---
description: "Command description"
---

Command content with {SCRIPT} and $ARGUMENTS placeholders.
```

**GitHub Copilot Agent Skill format** (`.github/skills/devspark-<command>/SKILL.md`):

```markdown
---
name: devspark-command-name
description: "Command description"
user-invocable: true
disable-model-invocation: true
---

Prompt resolution and user-input instructions.
```

### TOML Format

Used by: Gemini, Qwen

```toml
description = "Command description"

prompt = """
Command content with {SCRIPT} and {{args}} placeholders.
"""
```

## Directory Conventions

- **CLI agents**: Usually `.<agent-name>/commands/`
- **IDE agents**: Follow IDE-specific patterns:
  - Copilot: `.github/skills/`
  - Cursor: `.cursor/commands/`
  - Windsurf: `.windsurf/workflows/`

## Argument Patterns

Different agents use different argument placeholders:

- **Markdown/prompt-based**: `$ARGUMENTS`
- **TOML-based**: `{{args}}`
- **Script placeholders**: `{SCRIPT}` (replaced with actual script path)
- **Agent placeholders**: `__AGENT__` (replaced with agent name)

## Testing New Agent Integration

1. **Build test**: Run package creation script locally
2. **Quickstart test**: Run the agent's quickstart guide against a scratch repo and confirm the new agent's shims/prompts install correctly
3. **File generation**: Verify correct directory structure and files
4. **Command validation**: Ensure generated commands work with the agent
5. **Context update**: Test agent context update scripts

## Common Pitfalls

1. **Using shorthand keys instead of actual CLI tool names**: Always use the actual executable name as the AGENT_CONFIG key (e.g., `"cursor-agent"` not `"cursor"`). This prevents the need for special-case mappings throughout the codebase.
2. **Forgetting update scripts**: Both bash and PowerShell scripts must be updated when adding new agents.
3. **Incorrect `requires_cli` value**: Set to `True` only for agents that actually have CLI tools to check; set to `False` for IDE-based agents.
4. **Wrong argument format**: Use correct placeholder format for each agent type (`$ARGUMENTS` for Markdown, `{{args}}` for TOML).
5. **Directory naming**: Follow agent-specific conventions exactly (check existing agents for patterns).
6. **Help text inconsistency**: Update all user-facing text consistently (help strings, docstrings, README, error messages).

## Future Considerations

When adding new agents:

- Consider the agent's native command/workflow patterns
- Ensure compatibility with the Spec-Driven Development process
- Document any special requirements or limitations
- Update this guide with lessons learned
- Verify the actual CLI tool name before adding to AGENT_CONFIG

---

*This documentation should be updated whenever new agents are added to maintain accuracy and completeness.*
<!-- DEVSPARK SHARED CONTEXT:END -->

