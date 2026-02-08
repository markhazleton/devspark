# Installation Guide

## Prerequisites

- **Linux/macOS** (or Windows; PowerShell scripts now supported without WSL)
- AI coding agent: [Claude Code](https://www.anthropic.com/claude-code), [GitHub Copilot](https://code.visualstudio.com/), [Codebuddy CLI](https://www.codebuddy.ai/cli) or [Gemini CLI](https://github.com/google-gemini/gemini-cli)
- [uv](https://docs.astral.sh/uv/) for package management
- [Python 3.11+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)

## Installation

Spec Kit supports two installation scenarios:

| Scenario | Description | Command |
|----------|-------------|--------|
| **Greenfield** | Starting a brand new project from scratch | `specify init <PROJECT_NAME>` |
| **Brownfield** | Adding Spec Kit to an existing codebase | `specify init --here` or `specify init .` |

### Greenfield: Initialize a New Project

Starting fresh? Create a new project directory with all Spec Kit scaffolding:

```bash
uvx --from git+https://github.com/MarkHazleton/spec-kit.git specify init <PROJECT_NAME>
```

This creates a new directory with the complete Spec Kit structure ready for development.

### Brownfield: Add to Existing Project

Already have a codebase? Navigate to your project root and initialize in place:

```bash
cd /path/to/your-existing-project
uvx --from git+https://github.com/MarkHazleton/spec-kit.git specify init --here
# or equivalently
uvx --from git+https://github.com/MarkHazleton/spec-kit.git specify init .
```

This adds the Spec Kit structure (`.documentation/`, `.documentation/memory/`, templates, scripts) to your existing project without disrupting your current files.

> [!TIP]
> **Brownfield Tip**: After initialization, use the `/speckit.discover-constitution` command to help create a constitution from your existing codebase patterns. This analyzes your code conventions, architecture decisions, and established practices to draft a constitution that reflects how your project already works.

### Specify AI Agent

You can proactively specify your AI agent during initialization:

```bash
uvx --from git+https://github.com/MarkHazleton/spec-kit.git specify init <project_name> --ai claude
uvx --from git+https://github.com/MarkHazleton/spec-kit.git specify init <project_name> --ai gemini
uvx --from git+https://github.com/MarkHazleton/spec-kit.git specify init <project_name> --ai copilot
uvx --from git+https://github.com/MarkHazleton/spec-kit.git specify init <project_name> --ai codebuddy
```

### Specify Script Type (Shell vs PowerShell)

All automation scripts now have both Bash (`.sh`) and PowerShell (`.ps1`) variants.

Auto behavior:

- Windows default: `ps`
- Other OS default: `sh`
- Interactive mode: you'll be prompted unless you pass `--script`

Force a specific script type:

```bash
uvx --from git+https://github.com/MarkHazleton/spec-kit.git specify init <project_name> --script sh
uvx --from git+https://github.com/MarkHazleton/spec-kit.git specify init <project_name> --script ps
```

### Ignore Agent Tools Check

If you prefer to get the templates without checking for the right tools:

```bash
uvx --from git+https://github.com/MarkHazleton/spec-kit.git specify init <project_name> --ai claude --ignore-agent-tools
```

## Upgrading Spec Kit

To upgrade an existing Spec Kit project to the latest version:

### Upgrade CLI Tool

First, upgrade the Specify CLI tool:

```bash
uv tool install specify-cli --force --from git+https://github.com/MarkHazleton/spec-kit.git
```

### Upgrade Project Files (Recommended)

Use the `specify upgrade` command for a safe, guided upgrade:

```bash
# Simple upgrade (auto-detects AI assistant and migration needs)
specify upgrade

# Preview changes without modifying files
specify upgrade --dry-run

# Override detected agent
specify upgrade --ai claude

# Create backup of constitution before upgrade
specify upgrade --backup

# Skip automatic migration check
specify upgrade --skip-migration
```

The `upgrade` command will:
- ✅ Auto-detect your AI assistant from existing setup
- ✅ Check for uncommitted Git changes
- ✅ Detect old structure (`.specify/`, root-level directories) and offer migration
- ✅ Download and apply latest templates
- ✅ Preserve your specs and customizations

See the [Upgrade Guide](upgrade.md) for detailed instructions.

### Migration from Old Structure

If you're using the old `.specify/` directory or root-level `memory/`, `scripts/`, `templates/` directories, see the [Migration Guide](migration-guide.md) for automated migration to the new `.documentation/` structure.

## Verification

After initialization, you should see the following commands available in your AI agent:

### Core Spec Workflow Commands

These commands are used for the Spec-Driven Development process:

- `/speckit.constitution` - Create project principles
- `/speckit.specify` - Create specifications
- `/speckit.plan` - Generate implementation plans  
- `/speckit.tasks` - Break down into actionable tasks
- `/speckit.implement` - Execute the implementation plan
- `/speckit.critic` - Adversarial risk analysis (requires spec, plan, tasks)
- `/speckit.analyze` - Cross-artifact consistency and coverage analysis
- `/speckit.checklist` - Generate quality validation checklists
- `/speckit.clarify` - Clarify underspecified areas

### Constitution-Powered Commands (No Spec Required)

These commands only need a constitution and work independently on any codebase:

- `/speckit.pr-review` - Review pull requests against constitution
- `/speckit.site-audit` - Comprehensive codebase audit for security, quality, and compliance

The `.documentation/scripts` directory will contain both `.sh` and `.ps1` scripts.

## Troubleshooting

### Git Credential Manager on Linux

If you're having issues with Git authentication on Linux, you can install Git Credential Manager:

```bash
#!/usr/bin/env bash
set -e
echo "Downloading Git Credential Manager v2.6.1..."
wget https://github.com/git-ecosystem/git-credential-manager/releases/download/v2.6.1/gcm-linux_amd64.2.6.1.deb
echo "Installing Git Credential Manager..."
sudo dpkg -i gcm-linux_amd64.2.6.1.deb
echo "Configuring Git to use GCM..."
git config --global credential.helper manager
echo "Cleaning up..."
rm gcm-linux_amd64.2.6.1.deb
```
