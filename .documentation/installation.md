# Other Ways to Get Started

> [!TIP]
> **Recommended**: For most users the [Prompt Bootstrap](quickstart.md) is the fastest, zero-install way to get DevSpark running. This page covers alternatives, ordered from lightest to heaviest.

---

## Option 1 — Manual File Copy (No tools required)

Clone or download the DevSpark repository and copy only the files you need into your project. This requires nothing beyond Git.

```bash
# Clone the DevSpark repo temporarily
git clone https://github.com/MarkHazleton/devspark.git devspark-tmp

# Copy the framework files into your project
cp -r devspark-tmp/templates/commands   your-project/.devspark/defaults/commands
cp -r devspark-tmp/templates            your-project/.devspark/defaults/templates
cp -r devspark-tmp/scripts/bash         your-project/.devspark/scripts/bash
cp -r devspark-tmp/scripts/powershell   your-project/.devspark/scripts/powershell

# Clean up
rm -rf devspark-tmp
```

Then create your `.documentation/` folder and add the agent shims for your AI agent by hand per the [quickstart guides](https://github.com/MarkHazleton/devspark/tree/main/quickstart).

---

## Option 2 — One-Shot CLI via `uvx` (No global install)

Run the DevSpark CLI once without permanently installing it. Requires [uv](https://docs.astral.sh/uv/) and [Python 3.11+](https://www.python.org/downloads/).

### Prerequisites

- [uv](https://docs.astral.sh/uv/) — Python package manager
- [Python 3.11+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)
- Any [supported AI coding agent](https://github.com/MarkHazleton/devspark#-supported-ai-agents)

### Greenfield (New Project)

```bash
uvx --from git+https://github.com/MarkHazleton/devspark.git devspark init <PROJECT_NAME>
```

### Brownfield (Existing Project)

```bash
cd /path/to/your-existing-project
uvx --from git+https://github.com/MarkHazleton/devspark.git devspark init --here
```

> [!TIP]
> **Brownfield Tip**: After initialization, use `/devspark.discover-constitution` to analyze your existing codebase and draft a constitution that reflects how your project already works.

### Specify AI Agent

```bash
uvx --from git+https://github.com/MarkHazleton/devspark.git devspark init <PROJECT_NAME> --ai claude
uvx --from git+https://github.com/MarkHazleton/devspark.git devspark init <PROJECT_NAME> --ai gemini
uvx --from git+https://github.com/MarkHazleton/devspark.git devspark init <PROJECT_NAME> --ai copilot
```

### Force Script Type

```bash
uvx --from git+https://github.com/MarkHazleton/devspark.git devspark init <PROJECT_NAME> --script ps  # PowerShell
uvx --from git+https://github.com/MarkHazleton/devspark.git devspark init <PROJECT_NAME> --script sh  # POSIX shell
```

---

## Option 3 — Installed CLI (Global install)

Install the DevSpark CLI globally so `devspark` is always available in your terminal. This is the heaviest option and is best suited for teams that run DevSpark frequently across many projects.

### Install

```bash
uv tool install devspark-cli --from git+https://github.com/MarkHazleton/devspark.git
```

### Initialize a project

```bash
# New project
devspark init my-project --ai claude

# Existing project
cd /path/to/existing-project
devspark init --here --ai claude
```

### Upgrade the CLI

```bash
uv tool install devspark-cli --force --from git+https://github.com/MarkHazleton/devspark.git
```

### Upgrade DevSpark in a project

```bash
# Safe guided upgrade (recommended)
devspark upgrade

# Preview changes without modifying files
devspark upgrade --dry-run

# Back up constitution before upgrade
devspark upgrade --backup

# Override detected agent
devspark upgrade --ai claude

# Skip automatic migration check
devspark upgrade --skip-migration
```

The `upgrade` command will:

- Auto-detect your AI assistant from existing setup
- Check for uncommitted Git changes
- Detect old structure and offer migration
- Download and apply latest templates
- Preserve your specs and customizations

See the [Upgrade Guide](upgrade.md) for detailed instructions.

---

## Verification

After any installation method, you should see these commands available in your AI agent:

### Core Spec Workflow

- `/devspark.constitution` — Create project principles
- `/devspark.specify` — Create specifications
- `/devspark.plan` — Generate implementation plans
- `/devspark.tasks` — Break down into actionable tasks
- `/devspark.implement` — Execute the implementation plan
- `/devspark.critic` — Adversarial risk analysis
- `/devspark.analyze` — Cross-artifact consistency checking
- `/devspark.checklist` — Generate quality validation checklists
- `/devspark.clarify` — Clarify underspecified areas

### Constitution-Powered Commands (No Spec Required)

- `/devspark.pr-review` — Review pull requests against constitution
- `/devspark.site-audit` — Comprehensive codebase audit

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
