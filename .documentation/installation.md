# Other Ways to Get Started

## Current Release: v2.3.0

> For most users the [Prompt Bootstrap](quickstart.md) is all you need. This page covers advanced CLI alternatives only.

---

## Option 1: Manual File Copy

Clone or download DevSpark and copy the files you need. No tools required beyond Git.

```bash
# Clone temporarily
git clone https://github.com/MarkHazleton/devspark.git devspark-tmp

# Copy framework files
cp -r devspark-tmp/templates/commands   your-project/.devspark/defaults/commands
cp -r devspark-tmp/templates/*.md       your-project/.devspark/templates/
cp -r devspark-tmp/templates/*.json     your-project/.devspark/templates/
cp -r devspark-tmp/scripts/bash         your-project/.devspark/scripts/bash
cp -r devspark-tmp/scripts/powershell   your-project/.devspark/scripts/powershell
cp devspark-tmp/agents-registry.json    your-project/agents-registry.json

# Clean up
rm -rf devspark-tmp
```

Then create `.documentation/`, add agent shims by hand per the [quickstart guides](https://github.com/MarkHazleton/devspark/tree/main/quickstart), and keep `agents-registry.json` at the repository root so shared agent metadata remains available to context-generation scripts.

---

## Option 2: One-Shot CLI via `uvx`

Run the CLI once without permanently installing it. Requires [uv](https://docs.astral.sh/uv/) and Python 3.11+.

### New project

```bash
uvx --from git+https://github.com/MarkHazleton/devspark.git devspark init <PROJECT_NAME>
```

### Existing project

```bash
cd /path/to/your-existing-project
uvx --from git+https://github.com/MarkHazleton/devspark.git devspark init --here
```

### Specify agent or script type

```bash
uvx --from git+https://github.com/MarkHazleton/devspark.git devspark init <PROJECT_NAME> --ai claude
uvx --from git+https://github.com/MarkHazleton/devspark.git devspark init <PROJECT_NAME> --script ps
```

> After initialization on an existing codebase, use `/devspark.discover-constitution` to generate a constitution from your existing code patterns.

---

## Option 3: Global CLI Install

Install `devspark` permanently. Best for teams that run it across many projects.

```bash
# Install
uv tool install devspark-cli --from git+https://github.com/MarkHazleton/devspark.git

# New project
devspark init my-project --ai claude

# Existing project
cd /path/to/existing-project
devspark init --here --ai claude
```

For CLI upgrades and project file updates, see the [Upgrade Guide](upgrade.md).

Once the CLI is installed, you also get the optional harness runtime:

```bash
devspark doctor
devspark harness validate sample.harness.yaml
devspark harness run sample.harness.yaml --dry-run
devspark harness trace latest
devspark adapter list
```

See [Harness Engineering](harness-engineering.md) for the runtime model and command details.

---

## Troubleshooting

### Git Credential Manager on Linux

```bash
wget https://github.com/git-ecosystem/git-credential-manager/releases/download/v2.6.1/gcm-linux_amd64.2.6.1.deb
sudo dpkg -i gcm-linux_amd64.2.6.1.deb
git config --global credential.helper manager
rm gcm-linux_amd64.2.6.1.deb
```
