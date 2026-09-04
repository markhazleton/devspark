# Repo Story Command Guide

## Overview

The `/devspark.repo-story` command analyzes the full commit history of your repository and produces an evidence-based narrative document. It serves two audiences: **business stakeholders** who need a project summary, and **developers** who need onboarding context.

The repo story keeps your main `README.md` and `CHANGELOG.md` focused and compact. Instead of growing a README with project history, contributor summaries, and architecture overviews, the repo story captures that context in a dedicated, dated document that can be regenerated as the project evolves.

## Prerequisites

- **Required**: Git repository with commit history
- **Required**: PowerShell 7+ or Bash (plus Python 3 for bash variant)
- **Optional**: Constitution at `/.knowledge/governance/constitution.md` (enables governance alignment section)

## When to Use

Run `/devspark.repo-story` when you need to:

- **Onboard new team members** -- the Developer FAQ section answers "where do I start?" with evidence from the actual codebase
- **Brief stakeholders** -- the Executive Summary provides velocity, maturity, and milestone data without jargon
- **Keep README small** -- move project history and contributor context into the repo story instead of bloating the README
- **Audit project health** -- velocity trends, bus factor, test ratios, and governance metrics in one document
- **Prepare for releases** -- capture the state of the project at a point in time

## Quick Start

### Basic Usage

```bash
/devspark.repo-story
```

Generates a full repo story covering all sections as ephemeral work state under
`.devspark.work/repo-story/`. Update durable README guidance only when the user
explicitly asks for a current-truth documentation change.

### Scoped Analysis

```bash
/devspark.repo-story --scope=business    # Executive summary only
/devspark.repo-story --scope=velocity    # Development pace focus
/devspark.repo-story --scope=quality     # Test metrics and governance
/devspark.repo-story --scope=team        # Contributor patterns
/devspark.repo-story --months 6          # Last 6 months only
```

### Compare Against a Baseline

```bash
/devspark.repo-story --compare-baseline 2025-06
```

Shows how current metrics compare to a prior period.

## What It Produces

The command generates a single markdown document with these sections:

### Executive Summary (Business Audience)

Plain-language overview covering project purpose, scale, velocity trends, governance posture, and key milestones. Written for a VP/director reading level.

### Technical Deep Dive

Evidence-backed analysis of:

| Section | What it covers |
|---------|---------------|
| **Development Velocity** | Commits/month trend, lines added/removed, churn ratio |
| **Contributor Dynamics** | Role distribution, bus factor, team growth |
| **Quality Signals** | Test-to-source ratio, conventional commit adoption |
| **Governance Maturity** | PR workflow signals, tag discipline, branch strategy |
| **Architecture** | Language breakdown, CI/CD indicators, config maturity |

### Change Pattern Analysis

Top 5 most-modified files, hotspot directories, and what the churn patterns suggest about active development vs. instability.

### Milestone Timeline

Chronological table of tagged releases with surrounding commit activity context.

### Constitution Alignment (Optional)

If a constitution exists, maps governance metrics to stated principles and notes gaps.

### Developer FAQ

Answers 10 concrete onboarding questions using evidence from the commit history:

1. What does this project do?
2. What tech stack does it use?
3. Where do I start?
4. How do I run it locally?
5. How do I run the tests?
6. What is the branching/PR workflow?
7. Who do I ask when I'm stuck?
8. What areas of the code change most often?
9. Are there coding standards I must follow?
10. What version is currently released?

## How It Keeps README Small

Traditional approach (README grows forever):

```text
README.md
  ## About (3 paragraphs -> 10 paragraphs over time)
  ## Architecture (added after first refactor)
  ## Contributing (grows with each new process)
  ## History (never pruned)
  ## Team (outdated within months)
```

Repo story approach (README stays focused):

```text
README.md
  ## About (stays concise -- one paragraph)
  ## Quick Start (installation and first run)
  ## Contributing (link to CONTRIBUTING.md)
  ## Repo Story (generated under .devspark.work/repo-story/)

.devspark.work/repo-story/repo-story-2026-04-09.md
  ## Executive Summary (project context for stakeholders)
  ## Technical Analysis (architecture, velocity, quality)
  ## Developer FAQ (onboarding answers with evidence)
```

The README stays a quick-start document. The repo story holds the depth. Regenerate it periodically -- each run creates a new dated file so you can compare snapshots over time.

## Output Location

Stories are saved to:

```text
.devspark.work/repo-story/repo-story-YYYY-MM-DD.md
```

The command also adds or updates a link in your root `README.md` pointing to the latest story.

## Related Commands

| Command | Relationship |
|---------|-------------|
| `/devspark.release` | Validates current truth and archives completed work at release time |
| `/devspark.discover-knowledge` | Assimilates source-grounded durable knowledge and documentation intake |
| `/devspark.site-audit` | Code-level quality analysis (complements the commit-level repo story) |
| `/devspark.constitution` | Defines principles that the repo story evaluates alignment against |
