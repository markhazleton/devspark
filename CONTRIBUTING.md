# Contributing to Spec Kit

Hi there! We're thrilled that you'd like to contribute to Spec Kit. Contributions to this project are [released](https://help.github.com/articles/github-terms-of-service/#6-contributions-under-repository-license) to the public under the [project's open source license](LICENSE).

Please note that this project is released with a [Contributor Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project you agree to abide by its terms.

## Prerequisites for running and testing code

These are one time installations required to be able to test your changes locally as part of the pull request (PR) submission process.

1. Install [Python 3.11+](https://www.python.org/downloads/)
1. Install [uv](https://docs.astral.sh/uv/) for package management
1. Install [Git](https://git-scm.com/downloads)
1. Have an [AI coding agent available](README.md#-supported-ai-agents)

<details>
<summary><b>💡 Hint if you are using <code>VSCode</code> or <code>GitHub Codespaces</code> as your IDE</b></summary>

<br>

Provided you have [Docker](https://docker.com) installed on your machine, you can leverage [Dev Containers](https://containers.dev) through this [VSCode extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers), to easily set up your development environment, with aforementioned tools already installed and configured, thanks to the `.devcontainer/devcontainer.json` file (located at the root of the project).

To do so, simply:

- Checkout the repo
- Open it with VSCode
- Open the [Command Palette](https://code.visualstudio.com/docs/getstarted/userinterface#_command-palette) and select "Dev Containers: Open Folder in Container..."

On [GitHub Codespaces](https://github.com/features/codespaces) it's even simpler, as it leverages the `.devcontainer/devcontainer.json` automatically upon opening the codespace.

</details>

## Submitting a pull request

> [!NOTE]
> If your pull request introduces a large change that materially impacts the work of the CLI or the rest of the repository (e.g., you're introducing new templates, arguments, or otherwise major changes), make sure that it was **discussed and agreed upon** by the project maintainers. Pull requests with large changes that did not have a prior conversation and agreement will be closed.

1. Fork and clone the repository
1. Configure and install the dependencies: `uv sync`
1. Make sure the CLI works on your machine: `uv run specify --help`
1. Create a new branch: `git checkout -b my-branch-name`
1. Make your change, add tests, and make sure everything still works
1. Test the CLI functionality with a sample project if relevant
1. Push to your fork and submit a pull request
1. Wait for your pull request to be reviewed and merged.

Here are a few things you can do that will increase the likelihood of your pull request being accepted:

- Follow the project's coding conventions.
- Write tests for new functionality.
- Update documentation (`README.md`, `spec-driven.md`) if your changes affect user-facing features.
- Keep your change as focused as possible. If there are multiple changes you would like to make that are not dependent upon each other, consider submitting them as separate pull requests.
- Write a [good commit message](http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html).
- Test your changes with the Spec-Driven Development workflow to ensure compatibility.

## Development workflow

When working on spec-kit:

1. Test changes with the `specify` CLI commands in your coding agent of choice:
   - Core: `/speckit.specify`, `/speckit.plan`, `/speckit.tasks`, `/speckit.implement`
   - Quality: `/speckit.pr-review`, `/speckit.site-audit`, `/speckit.critic`
2. Verify templates are working correctly in `templates/` directory
3. Test script functionality in the `scripts/` directory
4. Ensure memory files (`memory/constitution.md`) are updated if major process changes are made

### Testing template and command changes locally

Running `uv run specify init` pulls released packages, which won’t include your local changes.  
To test your templates, commands, and other changes locally, follow these steps:

1. **Create release packages**

   Run the following command to generate the local packages:

   ```bash
   ./.github/workflows/scripts/create-release-packages.sh v1.0.0
   ```

2. **Copy the relevant package to your test project**

   ```bash
   cp -r .genreleases/sdd-copilot-package-sh/. <path-to-test-project>/
   ```

3. **Open and test the agent**

   Navigate to your test project folder and open the agent to verify your implementation.

## Fork Maintenance

**Spec Kit Spark** is a maintained fork of [github.com/github/spec-kit](https://github.com/github/spec-kit). We track and selectively incorporate upstream improvements using documented decision criteria.

### Syncing with Upstream

**Monthly Reviews** (or as needed): Check for valuable upstream changes.

**Interactive Mode** (Recommended for thorough review):

```powershell
# PowerShell - Interactive review with explanations
.\scripts\powershell\sync-upstream.ps1 -Mode interactive

# Bash - Interactive review with explanations
./scripts/bash/sync-upstream.sh --mode interactive
```

Interactive mode provides:
- Detailed commit analysis (author, date, files changed, diff stats)
- Implications explained for each category (AUTO/ADAPT/IGNORE/EVALUATE)
- Conflict detection with Spark-specific files
- Options: Apply, Skip, Defer (with notes), View full diff, Quit
- Checkpoint branches for safe rollback

**Quick Review** (for overview):

```powershell
# PowerShell - Quick categorized view
.\scripts\powershell\sync-upstream.ps1 -Mode review

# Bash - Quick categorized view
./scripts/bash/sync-upstream.sh --mode review
```

This categorizes upstream commits into:

- 🟢 **AUTO** - Safe to auto-apply (bug fixes, security patches)
- 🟡 **ADAPT** - Requires path adaptation (docs/ → .documentation/)
- 🔴 **IGNORE** - Not applicable to Spark
- 🔵 **EVALUATE** - Major features needing team discussion
- ⚪ **REVIEW** - Needs manual categorization

### Auto-Applying Safe Changes

After reviewing, auto-apply bug fixes and security patches:

```powershell
# PowerShell
.\scripts\powershell\sync-upstream.ps1 --mode auto

# Bash
./scripts/bash/sync-upstream.sh --mode auto
```

This will:

- Create a checkpoint branch for rollback safety
- Cherry-pick all AUTO-categorized commits
- Report successes and failures
- Update FORK_DIVERGENCE.md

### Adapting Changes Manually

For ADAPT commits that need path adjustments:

1. **Cherry-pick to feature branch**:

   ```bash
   git checkout -b sync/adapt-<hash>
   git cherry-pick <commit-hash>
   ```

2. **Resolve path conflicts**:

   - Change `docs/` → `.documentation/`
   - Change `.specify/` → `.documentation/`
   - Update any hardcoded references

3. **Test commands**: Verify all `/speckit.*` commands still work

4. **Merge when validated**:

   ```bash
   git checkout main
   git merge sync/adapt-<hash>
   ```

### Evaluating Major Features

For EVALUATE commits (extension system, etc.):

1. **Create RFC or discussion** in GitHub Issues
2. **Test in isolated branch**: `git checkout -b evaluate/<feature-name>`
3. **Document implications**: How does it fit with Spark architecture?
4. **Team decision**: Integrate, adapt, or defer

### Decision Criteria Summary

Use these patterns when manually reviewing commits:

**AUTO (🟢)** - Apply automatically:

- Bug fixes (typos, path errors, dependency conflicts)
- Security patches
- Agent CLI compatibility fixes

**ADAPT (🟡)** - Requires modification:

- Template wording improvements
- Documentation updates
- Script enhancements (common.sh, etc.)

**IGNORE (🔴)** - Skip these:

- Upstream version bumps
- Changes to `docs/` folder (we use `.documentation/`)
- Workflow changes specific to github/github

**EVALUATE (🔵)** - Team discussion needed:

- Extension system
- Generic agent support
- Major architectural changes

### Updating FORK_DIVERGENCE.md

After applying changes, document them:

1. **Auto-updates**: The sync script updates metadata automatically
2. **Manual entries**: Add to "Absorbed Changes Log" section
3. **Include**: Commit hash, category, and brief description

Example entry:

```markdown
### 2026-02-20: Auto-Applied Cherry-Picks

**Upstream Commit**: `aeed11f`  
**Applied**: 5 commits

- `fc3b98e` - fix: rename Qoder CLI key
- `6fca5d8` - fix: pin click>=8.1 dependency
- `c78f842` - fix: typo in plan-template.md
- ...
```

### Contributing Back to Upstream

Developed something valuable that could help the broader community?

1. **Create upstream-compatible branch**:

   ```bash
   git checkout -b upstream/feature-name
   ```

2. **Adjust to upstream structure**:
   - Change `.documentation/` → `docs/`
   - Remove Spark-specific commands
   - Follow upstream conventions

3. **Test with upstream templates**

4. **Submit PR** to [github.com/github/spec-kit](https://github.com/github/spec-kit)

5. **Document** in FORK_DIVERGENCE.md → "Contributed to Upstream"

### Resources

- **[FORK_DIVERGENCE.md](./FORK_DIVERGENCE.md)** - Complete tracking document
- **[sync-upstream.ps1](./scripts/powershell/sync-upstream.ps1)** - PowerShell sync script
- **[sync-upstream.sh](./scripts/bash/sync-upstream.sh)** - Bash sync script
- **[Upstream Repository](https://github.com/github/spec-kit)** - Original spec-kit

## AI contributions in Spec Kit

> [!IMPORTANT]
>
> If you are using **any kind of AI assistance** to contribute to Spec Kit,
> it must be disclosed in the pull request or issue.

We welcome and encourage the use of AI tools to help improve Spec Kit! Many valuable contributions have been enhanced with AI assistance for code generation, issue detection, and feature definition.

That being said, if you are using any kind of AI assistance (e.g., agents, ChatGPT) while contributing to Spec Kit,
**this must be disclosed in the pull request or issue**, along with the extent to which AI assistance was used (e.g., documentation comments vs. code generation).

If your PR responses or comments are being generated by an AI, disclose that as well.

As an exception, trivial spacing or typo fixes don't need to be disclosed, so long as the changes are limited to small parts of the code or short phrases.

An example disclosure:

> This PR was written primarily by GitHub Copilot.

Or a more detailed disclosure:

> I consulted ChatGPT to understand the codebase but the solution
> was fully authored manually by myself.

Failure to disclose this is first and foremost rude to the human operators on the other end of the pull request, but it also makes it difficult to
determine how much scrutiny to apply to the contribution.

In a perfect world, AI assistance would produce equal or higher quality work than any human. That isn't the world we live in today, and in most cases
where human supervision or expertise is not in the loop, it's generating code that cannot be reasonably maintained or evolved.

### What we're looking for

When submitting AI-assisted contributions, please ensure they include:

- **Clear disclosure of AI use** - You are transparent about AI use and degree to which you're using it for the contribution
- **Human understanding and testing** - You've personally tested the changes and understand what they do
- **Clear rationale** - You can explain why the change is needed and how it fits within Spec Kit's goals
- **Concrete evidence** - Include test cases, scenarios, or examples that demonstrate the improvement
- **Your own analysis** - Share your thoughts on the end-to-end developer experience

### What we'll close

We reserve the right to close contributions that appear to be:

- Untested changes submitted without verification
- Generic suggestions that don't address specific Spec Kit needs
- Bulk submissions that show no human review or understanding

### Guidelines for success

The key is demonstrating that you understand and have validated your proposed changes. If a maintainer can easily tell that a contribution was generated entirely by AI without human input or testing, it likely needs more work before submission.

Contributors who consistently submit low-effort AI-generated changes may be restricted from further contributions at the maintainers' discretion.

Please be respectful to maintainers and disclose AI assistance.

## Resources

- [Spec-Driven Development Methodology](./spec-driven.md)
- [How to Contribute to Open Source](https://opensource.guide/how-to-contribute/)
- [Using Pull Requests](https://help.github.com/articles/about-pull-requests/)
- [GitHub Help](https://help.github.com)
