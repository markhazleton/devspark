---
description: Harvest knowledge from completed specs and stale docs into CHANGELOG and guides, clean stale code comments, then archive
handoffs:
  - label: Run a site audit after harvesting
    agent: speckit.site-audit
    prompt: Run a site audit to confirm the project is in good health after harvesting
  - label: Archive remaining stale docs
    agent: speckit.archive
    prompt: Archive any remaining outdated documentation that was not covered by the harvest
  - label: Evolve the constitution
    agent: speckit.evolve-constitution
    prompt: Review the constitution in light of the cleaned-up documentation and harvested knowledge
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

---

## Goal

Harvest valuable knowledge from completed specs, stale documentation, and in-process drafts — then archive or remove them. This is a **knowledge-preserving cleanup**: information is captured in living documents (CHANGELOG, Guide.md, copilot-instructions) before source material moves to `.archive/`.

Additionally, scan source code for comments that reference completed specs, plans, or tasks and rewrite them as self-contained code documentation.

The output is:
1. Updated living documents (CHANGELOG, Guide.md) with harvested knowledge
2. Cleaned code comments (spec references → self-contained descriptions)
3. Stale files moved to `.archive/` with preserved folder structure
4. A harvest summary report at `.documentation/copilot/harvest-YYYY-MM-DD.md`

**CRITICAL: Never read from `.archive/` during this or any other command.** The archive is write-only from an operational perspective.

---

## Scope Options

By default (no arguments), perform a **full harvest**. Optional scope presets allow targeted runs:

| Scope Argument | Description |
|----------------|-------------|
| *(none)* | Full harvest — all phases enabled |
| `--scope=specs` | Completed specs only — harvest and archive |
| `--scope=docs` | Stale docs only — harvest and archive |
| `--scope=comments` | Code comment cleanup only — no file moves |
| `--scope=changelog` | CHANGELOG update only — no archival |
| `--scope=scan` | Scan and report only — no modifications (dry run) |

Multiple scopes can be combined: `--scope=specs,comments`

---

## Operating Constraints

- **Constitution Authority**: `/.documentation/memory/constitution.md` governs this process — read it first
- **Knowledge Preservation**: Information MUST be harvested into living documents BEFORE archival
- **No Data Loss**: Files move to `.archive/` — never deleted outright
- **CHANGELOG Is Append-Only**: New entries prepend; existing entries are never modified
- **Confirmation Required**: The harvest plan MUST be presented to the user for approval before any file moves or code edits

---

## Execution Phases

### Phase 1: Pre-Scan and Context Loading

1. **Run the harvest pre-scan script** to gather inventory:

   ```powershell
   .documentation/scripts/powershell/harvest.ps1 -Json
   ```

   Parse the JSON output. Key fields:
   - `harvest_date` — Use for the report filename
   - `specs` — All spec folders with status (`completed`, `completed-needs-changelog`, `in-progress`, `draft`)
   - `docs` — All doc files categorized (living_reference, completed_reviews, stale_drafts, session_notes, etc.)
   - `code_comments` — Spec/task references found in source files
   - `changelog_gaps` — Specs with all tasks done but no CHANGELOG entry
   - `bak_files` — Backup files to clean
   - `archive_existing` — What's already in `.archive/` (skip these)

2. **Load governance documents**:
   - Read `/.documentation/memory/constitution.md`
   - Read `CHANGELOG.md` (repo root) — identify what's already documented
   - Read `.documentation/Guide.md` — identify what may need updating

3. **Parse scope arguments** from `$ARGUMENTS`:
   - If empty or `--scope=full`: enable all phases
   - If `--scope=scan`: run phases 1–2 only, write summary report, stop before any modifications

---

### Phase 2: Classify All Artifacts

#### 2a. Classify Specs

For each folder in `.documentation/specs/` (excluding `pr-review/`):

| Status | Criteria | Action |
|--------|----------|--------|
| **COMPLETED** | All tasks `[X]` in tasks.md AND in CHANGELOG | Harvest → Archive |
| **COMPLETED-NEEDS-CHANGELOG** | All tasks `[X]` but not in CHANGELOG | Add CHANGELOG entry → Archive |
| **IN-PROGRESS** | Some tasks incomplete | Leave in place |
| **DRAFT** | No tasks.md, or no tasks started | Leave in place |

#### 2b. Classify Docs

For each file in `.documentation/` (recursive, never `.archive/`):

| Category | Path Pattern | Action |
|----------|-------------|--------|
| **Completed Reviews** | `.documentation/specs/pr-review/*.md` | Harvest → Archive |
| **Completed Audits** | `.documentation/copilot/audit/*.md` | Harvest → Archive |
| **Stale Drafts** | `.documentation/drafts/*.md` | Archive |
| **Session Notes** | `.documentation/copilot/session*/` | Archive if work is merged |
| **Impl Plans** | `*-implementation-plan.md`, `*-plan.md` (completed) | Harvest → Archive |
| **Release Docs** | `.documentation/releases/` (superseded) | Archive |
| **Quickfix Records** | `.documentation/quickfixes/` | Archive |
| **Backup Files** | `*.bak`, `*.backup`, `*.old` | Archive |
| **Living Reference** | Top-level `.documentation/*.md`, Guide.md, CHANGELOG.md | Keep — may update |

**Never archive:**
- `/.documentation/memory/constitution.md`
- `/.documentation/scripts/` and `/.documentation/templates/`
- `/.documentation/Guide.md` — update it instead
- `CHANGELOG.md` — append to it, never move it

#### 2c. Classify Code Comments

Search source files for spec/task references. The pre-scan output's `code_comments` array lists these. For each:

| Pattern Example | Action |
|----------------|--------|
| `# spec 026 Phase 5` | Rewrite as behavior description |
| `# FR-013: always send transcript` | Strip prefix, keep or rewrite the behavior description |
| `# T006: audit trail` | Rewrite as self-contained comment |
| `# Phase 3 implementation` | Remove or rewrite |
| `# TODO(spec-018): migrate later` | Remove entirely if spec-018 is completed |

**Rewrite rule**: Replace any spec/task reference with a self-contained description of WHAT the code does and WHY, without referencing the spec document. The comment must make sense to a reader who has never seen any spec.

```python
# BEFORE: # FR-013: transcript always sent regardless of CRM engagement
# AFTER:  # Always send transcript — CRM cases need complete clinical context for closure

# BEFORE: # spec 026 Phase 5 — isolated handler contract
# AFTER:  # Handler receives only (data, step_data, step, answer) — no document access
```

---

### Phase 3: Present Harvest Plan

**STOP and present the full plan to the user for approval before proceeding.** Format:

```markdown
## Harvest Plan — YYYY-MM-DD

### Specs to Archive (N)
| Spec | CHANGELOG? | Action |
|------|------------|--------|
| 001-example-spec | ✅ Yes | Archive |
| 033-another-spec | ⚠️ No | Add CHANGELOG entry → Archive |

### Docs to Archive (N)
| File | Category | Action |
|------|----------|--------|
| .documentation/specs/pr-review/pr-12345.md | Completed review | Archive |
| .documentation/drafts/old-draft.md | Stale draft | Archive |

### CHANGELOG Updates Needed (N)
| Spec | Summary |
|------|---------|
| 033-another-spec | Brief description of what was delivered |

### Code Comments to Rewrite (N)
| File | Line | Current | Proposed |
|------|------|---------|----------|
| src/helpers.py | 142 | # FR-013 always send | # Always send transcript for CRM closure |

### Files to Clean (N)
| File | Type |
|------|------|
| .documentation/drafts/scratch.bak | Backup file |

### Not Changing
- .documentation/specs/019-in-progress/ (tasks incomplete)
- .documentation/Guide.md (current — will update after archival)
```

Wait for: **"Proceed with harvest? (yes/no/modify)"**

If the user says **modify**, apply their changes to the plan and re-present before executing.

---

### Phase 4: Harvest Knowledge → Living Documents

**Execute only after user approval.**

#### 4a. Update CHANGELOG.md

For each completed spec NOT already in CHANGELOG:
1. Read the spec's `spec.md`, `plan.md`, and `tasks.md`
2. Extract: spec number, key changes, what was delivered
3. Prepend a new entry above existing content:

```markdown
## [Spec NNN] Title — YYYY-MM-DD

One-paragraph summary of what was delivered and why.

- Key change bullet point
- Another significant change
- Tests added: +NN tests (if applicable)
```

Never modify existing CHANGELOG entries.

#### 4b. Update .documentation/Guide.md

If completed specs introduced:
- New patterns or conventions → update the relevant section
- New directories or files in `.documentation/` → update the directory map
- Deprecated old patterns → note the deprecation

The guide describes the **current state only** — no historical content.

#### 4c. Update .github/copilot-instructions.md (if it exists)

If completed specs introduced:
- New import paths, module names, or architectural patterns
- New document schemas or field names
- Deprecations of old patterns

---

### Phase 5: Clean Code Comments

For each spec/task reference identified in the pre-scan:

1. Read 10 lines of surrounding context to understand the code's purpose
2. Rewrite the comment as a self-contained behavioral description
3. Apply the edit

**Rules**:
- Never remove a comment without understanding its purpose first
- If the comment accurately describes behavior but just has a spec prefix, strip only the prefix
- If the comment is a pure task marker with no behavioral value, remove it entirely
- If uncertain about the code's behavior, leave the comment unchanged and note it in the harvest report

---

### Phase 6: Archive Files

1. Determine today's archive folder: `.archive/YYYY-MM-DD/`
2. Create it if it does not exist
3. Mirror the source directory structure inside the archive:
   - `.documentation/specs/NNN-name/` → `.archive/YYYY-MM-DD/.documentation/specs/NNN-name/`
   - `.documentation/drafts/foo.md` → `.archive/YYYY-MM-DD/.documentation/drafts/foo.md`
4. Move (never copy or delete) each approved file
5. Remove empty parent directories left behind only if they have no remaining files
6. After moving, verify no active file references the archived paths

**Do not move:**
- `/.documentation/memory/constitution.md`
- `/.documentation/scripts/`
- `/.documentation/templates/`
- `/.documentation/Guide.md`
- `CHANGELOG.md`

#### Update .archive/README.md

Create or append to `.archive/README.md`:

```markdown
# Archive

Completed and historical documentation. **Do not reference files from here in prompts, scripts, or active docs.**

## Contents

| Folder | Date | Description |
|--------|------|-------------|
| YYYY-MM-DD/ | YYYY-MM-DD | Harvest run — N specs, N docs archived |
```

---

### Phase 7: Write Harvest Report

Create `.documentation/copilot/harvest-YYYY-MM-DD.md`:

```markdown
# Harvest Report — YYYY-MM-DD

## Summary
- Specs archived: N
- Docs archived: N
- Code comments rewritten: N
- CHANGELOG entries added: N
- Guide.md updated: yes/no

## Specs Archived
| Spec | CHANGELOG Entry Added |
|------|-----------------------|
| NNN-name | ✅ / ➕ Added now |

## Docs Archived
| File | Category | Destination |
|------|----------|-------------|
| ... | ... | .archive/YYYY-MM-DD/... |

## Code Comments Rewritten
| File | Line | Before | After |
|------|------|--------|-------|
| ... | ... | ... | ... |

## Knowledge Harvested Into
| Document | Changes |
|----------|---------|
| CHANGELOG.md | Added Spec NNN entry |
| .documentation/Guide.md | Updated directory map |

## Still Active (Not Archived)
| Item | Reason |
|------|--------|
| .documentation/specs/NNN-name/ | In-progress |
```

---

## Anti-Patterns (DO NOT)

1. **Archive without harvesting** — Capture knowledge in living docs first
2. **Delete files** — Always use `Move-Item` to `.archive/`; never `Remove-Item`
3. **Modify existing CHANGELOG entries** — Only append new entries
4. **Archive in-progress specs** — Only specs with all tasks complete are eligible
5. **Leave stale code comments** — Spec references must be rewritten or removed
6. **Skip user confirmation** — The harvest plan must be approved before any execution
7. **Update constitution directly** — Constitution changes require the `/speckit.evolve-constitution` process
8. **Read from `.archive/`** — The archive is write-only from an operational perspective
