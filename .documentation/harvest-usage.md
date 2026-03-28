# Harvest Command Guide

<!-- markdownlint-disable MD040 -->

## Overview

The `/speckit.harvest` command performs **knowledge-preserving cleanup** of your repository: completed specs, stale documentation, and draft artifacts are triaged and archived, while their valuable content is extracted into living documents (CHANGELOG, Guide.md, copilot-instructions) before anything moves.

Additionally, `/speckit.harvest` scans source code for comments that reference completed specs, plans, or tasks — and rewrites them as self-contained code documentation.

> **Note**: This command modifies files. Use `--scope=scan` to preview all harvest candidates without making any changes.

## Prerequisites

- A Git repository (recommended; required for accurate branch and merge detection)
- PowerShell 7+ (for pre-scan script)
- `.documentation/` directory with at least some content to triage

## Quick Start

### Preview Before Harvesting

```bash
/speckit.harvest --scope=scan
```

Runs the full pre-scan and presents a harvest plan — no files are moved or edited.

### Full Harvest

```bash
/speckit.harvest
```

Performs all phases: spec archival, doc cleanup, comment rewriting, CHANGELOG updates, and archival.

## Harvest Scopes

Control what the harvest covers using the `--scope` flag:

### Full Harvest (Default)

```bash
/speckit.harvest
```

All phases enabled: specs, docs, comments, and CHANGELOG updates.

### Completed Specs Only

```bash
/speckit.harvest --scope=specs
```

Finds specs with all tasks marked `[x]` in `tasks.md`, harvests their knowledge into CHANGELOG, then archives the spec folder.

### Stale Documentation Only

```bash
/speckit.harvest --scope=docs
```

Triages `.documentation/` for completed reviews, stale drafts, session notes, impl plans, backup files, and orphaned assets. Archives eligible files.

### Code Comment Cleanup Only

```bash
/speckit.harvest --scope=comments
```

Finds spec/task references in source code (e.g., `# FR-013`, `# spec 026 Phase 5`, `# T006`) and rewrites them as self-contained behavior descriptions. No file moves.

### CHANGELOG Update Only

```bash
/speckit.harvest --scope=changelog
```

Adds CHANGELOG entries for completed specs that lack them. No archival.

### Scan / Dry Run

```bash
/speckit.harvest --scope=scan
```

Runs the full pre-scan and presents the plan — reads only, no writes.

### Combined Scopes

```bash
/speckit.harvest --scope=specs,comments
```

Harvest completed specs and rewrite code comments in one pass.

## What Gets Harvested

### Spec Completion Criteria

A spec is eligible for harvest when **all** of the following are true:

| Criterion | Check |
|-----------|-------|
| `tasks.md` exists | All tasks marked `[x]` |
| No incomplete tasks | `incomplete_tasks == 0` |
| Work reflected in CHANGELOG | Already documented, or added now |

Specs with any incomplete tasks are left in place.

### Documentation Categories

| Category | Path Pattern | Default Action |
|----------|-------------|----------------|
| Completed PR reviews | `.documentation/specs/pr-review/*.md` | Archive |
| Completed audits | `.documentation/copilot/audit/*.md` | Archive |
| Stale drafts | `.documentation/drafts/*.md` | Archive |
| Session notes | `.documentation/copilot/session*/` | Archive (if merged) |
| Impl plans (completed) | `*-implementation-plan.md` | Archive |
| Superseded release docs | `.documentation/releases/` (older versions) | Archive |
| Quickfix records | `.documentation/quickfixes/` | Archive |
| Backup files | `*.bak`, `*.backup`, `*.old` | Archive |
| **Living reference** | Top-level `.documentation/*.md`, Guide.md | Keep / update |

**Never archived:**

- `/.documentation/memory/constitution.md`
- `/.documentation/scripts/` and `/.documentation/templates/`
- `CHANGELOG.md`
- `.documentation/Guide.md` (updated instead)

### Code Comment Patterns Detected

The pre-scan identifies comments matching these patterns across Python, TypeScript, C#, Go, Rust, and JavaScript source files:

| Pattern | Example | Rewrite Action |
|---------|---------|---------------|
| `# spec NNN` | `# spec 026 Phase 5` | Rewrite as behavior description |
| `# FR-NNN` | `# FR-013: always send transcript` | Strip prefix; keep/rewrite description |
| `# T-NNN` / `# TNNN:` | `# T006: audit trail` | Rewrite as self-contained comment |
| `# Phase N` | `# Phase 3 implementation` | Remove or rewrite |
| `# TODO(spec-NNN)` | `# TODO(spec-018): migrate later` | Remove if spec is complete |

**Rewrite rule**: Replace the spec/task reference with a description of WHAT the code does and WHY — no spec document reference needed.

## Understanding Harvest Output

### Harvest Report

A harvest report is written to: `/.documentation/copilot/harvest-YYYY-MM-DD.md`

It contains:

- Summary counts (specs archived, docs archived, comments rewritten, CHANGELOG entries added)
- Full table of archived specs with CHANGELOG status
- Full table of archived docs with destination paths
- Before/after for every rewritten code comment
- List of items left in place with reasons

### Archive Structure

Archived files are moved to date-stamped folders under `.archive/`:

```
.archive/
└── YYYY-MM-DD/
    ├── .documentation/
    │   ├── specs/NNN-completed-spec/
    │   ├── specs/pr-review/
    │   ├── drafts/
    │   └── copilot/
```

The directory structure mirrors the source tree, preserving full traceability.

## Common Workflows

### Workflow 1: Post-Release Cleanup

After a release, archive completed specs and their review artifacts:

```bash
# Preview what would be archived
/speckit.harvest --scope=scan

# Review the plan, then execute
/speckit.harvest --scope=specs,docs
```

### Workflow 2: Code Comment Cleanup Sprint

Clean up accumulated spec references in source code without moving any files:

```bash
# Scan first to see all references
/speckit.harvest --scope=scan

# Then clean just the comments
/speckit.harvest --scope=comments
```

### Workflow 3: CHANGELOG Catch-Up

Add CHANGELOG entries for completed specs that were missed:

```bash
/speckit.harvest --scope=changelog
```

### Workflow 4: Quarterly Full Harvest

Regular, comprehensive cleanup at the end of a development cycle:

```bash
# 1. Preview everything
/speckit.harvest --scope=scan

# 2. Review and approve the plan
# 3. Execute full harvest
/speckit.harvest

# 4. Run a site audit to confirm health
/speckit.site-audit
```

## Approval Gate

`/speckit.harvest` always presents a **harvest plan** before making any changes:

```markdown
## Harvest Plan — YYYY-MM-DD

### Specs to Archive (N)
| Spec | CHANGELOG? | Action |
...

### Docs to Archive (N)
| File | Category | Action |
...

### Code Comments to Rewrite (N)
| File | Line | Current | Proposed |
...
```

You must confirm before execution. You can also respond with **"modify"** to adjust the plan before it runs.

## Best Practices

### 1. Scan Before Every Harvest

Always preview first with `--scope=scan`. The harvest plan shows exactly what will change — review it carefully before approving.

### 2. Harvest After Each Release Cycle

Run a full harvest after each release to keep `.documentation/` clean and CHANGELOG current.

### 3. Never Delete — Always Archive

All files go to `.archive/YYYY-MM-DD/` — never deleted. Git history is preserved as an additional safety net.

### 4. Harvest Preserves Knowledge

The value of harvest is knowledge extraction, not disk cleanup. If the CHANGELOG or Guide.md wouldn't be enriched by archiving something, reconsider whether to archive it.

### 5. Keep `.archive/` Write-Only

Never reference archived files from active prompts, scripts, or documentation. The archive is for audit and traceability only.

## Troubleshooting

### "harvest.ps1 not found"

**Problem**: The pre-scan script is missing.

**Solution**: Run `specify upgrade` to install the latest scripts, or copy `harvest.ps1` from the source repo's `scripts/powershell/` to `/.documentation/scripts/powershell/`.

### "No specs found to harvest"

**Problem**: No completed specs detected.

**Possible causes**:

- Specs don't have a `tasks.md`, or tasks are not yet all marked `[x]`
- Specs are already in `.archive/`

### "Script execution failed"

**Problem**: PowerShell script cannot execute.

**Solutions**:

1. Ensure PowerShell 7+ is installed
2. Check execution policy: `Get-ExecutionPolicy`
3. Run from repository root directory

### Harvest archived something it shouldn't have

**Solution**: Files are in `.archive/YYYY-MM-DD/` — move them back with `Move-Item`. Nothing is deleted.

## Integration with Development Workflow

### After Feature Work

```bash
# When all tasks in a spec are complete and PR is merged
/speckit.harvest --scope=specs

# Clean up any code comments added during development
/speckit.harvest --scope=comments
```

### Before Release

```bash
# Ensure CHANGELOG is up to date for all completed specs
/speckit.harvest --scope=changelog

# Then run release workflow
/speckit.release
```

### Regular Maintenance

```bash
# Monthly cleanup
/speckit.harvest --scope=docs

# Monitor for accumulated spec comments
/speckit.harvest --scope=comments
```

## Support

If you encounter issues:

- Check [Troubleshooting](#troubleshooting) section above
- Review [Spec Kit Issues](https://github.com/MarkHazleton/spec-kit/issues)

---

*Part of Spec Kit Spark - Adaptive System Life Cycle Development (ASLCD) Toolkit*
*For more information: <https://github.com/MarkHazleton/spec-kit>*
