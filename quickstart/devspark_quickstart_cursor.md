# DevSpark Quickstart — Cursor

<!-- DevSpark — © 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com -->

> DevSpark is a Make Bold Solutions project. Install and update the framework from
> `https://dev.makeboldspark.com/raw` using the canonical distribution manifest.

You are bootstrapping **DevSpark**, a spec-driven development process, into this repository.
No CLI installation is required. You will pull prompt files from the DevSpark repo and place them in the correct directories.

## Preview Prompt — See Exactly What Will Happen Before You Trust It (recommended)

> **You should never run instructions you can't inspect.** "Why should I trust this?" is the right question to ask. DevSpark is designed to be *previewed before it is trusted* — every instruction the agent follows, and every `/devspark-*` skill it installs, is plain text you can read in full **before a single file is created**. Nothing below writes to your repository until you explicitly say so. Use either preview path — or both.

### Path A — Preview the prompt yourself (no agent, no changes)

Print the exact instructions, the full install list, and the stock prompt behind any individual `/devspark-*` skill to your terminal and read them for yourself:

```powershell
# 1. This guide, verbatim — the complete set of instructions the agent will follow
Invoke-WebRequest -Uri "https://dev.makeboldspark.com/raw/quickstart/devspark_quickstart_cursor.md?cb=$([DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds())" -Headers @{ 'Cache-Control'='no-cache'; 'Pragma'='no-cache' } | Select-Object -ExpandProperty Content

# 2. The manifest — the authoritative list of every file that would be installed, and where
$manifest = Invoke-RestMethod -Uri "https://dev.makeboldspark.com/dist/manifest.json?cb=$([DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds())" -Headers @{ 'Cache-Control'='no-cache'; 'Pragma'='no-cache' }
$manifest.install | ForEach-Object { "{0,-12} {1}" -f $_.category, $_.dest }

# 3. The stock prompt behind any individual skill, printed in full BEFORE you install it (example: /devspark-specify)
$src = ($manifest.install | Where-Object { $_.category -eq 'command' -and $_.dest -like '*devspark.specify.md' }).source
Invoke-WebRequest -Uri "$($manifest.raw_base)/$src?cb=$([DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds())" -Headers @{ 'Cache-Control'='no-cache'; 'Pragma'='no-cache' } | Select-Object -ExpandProperty Content
```

```bash
# 1. This guide, verbatim
curl -fsS -H 'Cache-Control: no-cache' "https://dev.makeboldspark.com/raw/quickstart/devspark_quickstart_cursor.md?cb=$(date +%s%N)"

# 2. The manifest — every file that would be installed, and where
curl -fsS -H 'Cache-Control: no-cache' "https://dev.makeboldspark.com/dist/manifest.json?cb=$(date +%s%N)" -o /tmp/devspark-manifest.json
jq -r '.install[] | "\(.category)\t\(.dest)"' /tmp/devspark-manifest.json

# 3. The stock prompt behind any individual skill, printed in full BEFORE you install it (example: /devspark-specify)
raw_base=$(jq -r .raw_base /tmp/devspark-manifest.json)
src=$(jq -r '.install[] | select(.category=="command" and (.dest|endswith("devspark.specify.md"))) | .source' /tmp/devspark-manifest.json)
curl -fsS -H 'Cache-Control: no-cache' "$raw_base/$src?cb=$(date +%s%N)"
```

### Path B — Ask the agent to preview (dry run, no writes)

Paste this to your agent before anything else:

> **Preview Prompt (dry run):** Before creating, modifying, or deleting anything, fetch this guide and the manifest, then show me (1) the mode you would run, (2) the full list of files you would create/modify/delete, and (3) the actual contents of the stock prompts behind the core `/devspark-*` skills you would install. Make **no changes**. Stop and wait for my explicit `proceed` before touching my repository.

When operating in **Preview Prompt Mode**, the agent must:

- Treat the run as **read-only** — no file writes, no directory creation, no deletions, no `.gitignore` edits.
- Fetch (cache-busted, per Step 0) and **display** the manifest-driven install list and the raw text of the stock prompts behind the key skills it would install.
- Present the mode banner and plan preview shown before any files are written **without executing** them.
- End by asking for explicit confirmation — e.g., "Reply `proceed` to install, or `cancel` to stop" — and do nothing until the user confirms.

Once you've reviewed the prompt and you're comfortable, continue with the steps below (or reply `proceed`).

---

## Step 0: Bypass All Caches (do this first — non-negotiable)

> ⚠️ **Webpage-fetch tools serve stale, aggressively cached copies of every `dev.makeboldspark.com` URL** — including this guide, `manifest.json`, and every prompt/template/script. A cached read will install an **old version** and force the user to intervene. **Never** use a webpage-fetch tool for a DevSpark URL. Fetch **everything** with a terminal command that adds a unique cache-buster (`?cb=<timestamp>`) **and** no-cache headers.

**0a. Re-fetch this guide uncached.** Even if you already loaded this quickstart, you may be reading a cached copy. Pull a fresh copy via terminal and follow *that* copy if it differs from what you have:

```powershell
Invoke-WebRequest -Uri "https://dev.makeboldspark.com/raw/quickstart/devspark_quickstart_cursor.md?cb=$([DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds())" -Headers @{ 'Cache-Control'='no-cache'; 'Pragma'='no-cache' } | Select-Object -ExpandProperty Content
```

```bash
curl -fsS -H 'Cache-Control: no-cache' "https://dev.makeboldspark.com/raw/quickstart/devspark_quickstart_cursor.md?cb=$(date +%s%N)"
```

**0b. Define a reusable download helper.** Use this helper for **every** file fetch in Steps 4–7 and the version check in Step 2 — it guarantees a cache-busted, no-cache terminal download. Do not substitute a webpage-fetch tool.

```powershell
function Get-DevSparkFile {
  param([Parameter(Mandatory)][string]$Path, [Parameter(Mandatory)][string]$Dest)
  $cb  = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
  $uri = "https://dev.makeboldspark.com/raw/$Path`?cb=$cb"
  $dir = Split-Path -Parent $Dest
  if ($dir) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  Invoke-WebRequest -Uri $uri -Headers @{ 'Cache-Control'='no-cache'; 'Pragma'='no-cache' } -OutFile $Dest
}
# Example: Get-DevSparkFile 'templates/commands/specify.md' '.devspark/defaults/commands/devspark.specify.md'
```

```bash
get_devspark_file() {  # usage: get_devspark_file <raw-path> <dest>
  local path="$1" dest="$2"
  mkdir -p "$(dirname "$dest")"
  curl -fsS -H 'Cache-Control: no-cache' "https://dev.makeboldspark.com/raw/$path?cb=$(date +%s%N)" -o "$dest"
}
# Example: get_devspark_file 'templates/commands/specify.md' '.devspark/defaults/commands/devspark.specify.md'
```

Throughout this guide, wherever a step says "Fetch … from `https://dev.makeboldspark.com/raw/…`", that means **call this helper in a terminal** — never a webpage-fetch tool.

## Step 1: Gather Project Context

No install-critical questions are needed before proceeding — **both** script sets (PowerShell and Bash) are always installed regardless of OS. Detect the current OS to display in the plan preview.

**OS detection** (in priority order):

1. If the workspace path contains a drive letter (e.g., `C:\`) or backslash separators → **Windows** (active runtime: PowerShell)
2. If the shell environment is bash/zsh/sh → **macOS/Linux** (active runtime: Bash)

State the detected OS before proceeding:
> *"Detected: Windows — active runtime PowerShell. Installing both PowerShell and Bash scripts."*
> *"Detected: macOS/Linux — active runtime Bash. Installing both PowerShell and Bash scripts."*

---

## Step 2: Detect Existing Installation

Before creating anything, check for prior legacy / DevSpark installations:

| Check for | What it means |
|---|---|
| `.devspark/` exists | **DevSpark already installed.** See "Version Check" below. |
| `.devspark.work/` exists | **Temporary work and overrides exist.** Preserve unless explicitly finalized. |
| `.knowledge/` exists | **Current project truth exists.** Preserve everything — never overwrite. |

**If nothing is found**, skip ahead to Step 3.

### Upgrade cleanup

After refreshing stock files, remove only framework-owned commands absent from the
canonical manifest. Preserve `.devspark.work/`, `.knowledge/`, `.archive/`, and
user overrides. Keep `.devspark/VERSION` as the canonical installed-version stamp.

---

## Step 2b: Announce Mode and Preview Plan

**Before writing any files**, output a mode banner so the user knows exactly what is about to happen.

### Mode Banner

Choose the banner that matches the detected state from Step 2:

| Detected state | Banner to output |
|---|---|
| No `.devspark/` found, no legacy | `▶ Mode: FRESH INSTALL` |
| `.devspark/` found, older version in the same major | `▶ Mode: UPDATE (vX.Y.Z → vX.Y.Y)` |
| `.devspark/` found, version matches latest, all files present | `▶ Mode: ALREADY CURRENT (vX.Y.Z) — nothing to do. Skipping to Step 11.7, then Step 12.` |
| `.devspark/` found, version matches latest, files missing | `▶ Mode: REPAIR (vX.Y.Z — re-fetching missing framework files)` |

Output the banner, then immediately output a brief **plan preview** — one line per action group:

```text
Plan:
  • Create directories: .devspark/, .cursor/commands/, .vscode/
  • Install N canonical files from manifest.install → .devspark/ (commands, templates, skills, both script sets) + agents-registry.json  (category `skill` entries are skipped)
  • Generate N command entry points → .cursor/commands/devspark-<cmd>.md
  • Retire 8.x entry points: delete unmodified, quarantine edited, remove orphans (one confirmation)  [Update/Repair; the 8.x classes only when the installed major version is below 9]
  • Prune any non-canonical .devspark/ entries (manifest.devspark_root)  [Update/Repair]
  • Seed constitution → .knowledge/governance/constitution.md  [if needed]
  • Write VERSION stamp → .devspark/VERSION
  • Update .gitignore
```

For Update and Repair modes, show only the steps that will actually run.

Proceed immediately after outputting the banner and plan — no additional confirmation needed unless you are about to perform a migration that renames or deletes directories.

---

### Constitution bootstrap questions (only if needed)

After detection and any migration work above, check whether `.knowledge/governance/constitution.md` already exists.

- If it exists already, or was migrated into place, **do not** ask for project name, tech stack, or core principles.
- If it does not exist, ask these additional questions before Step 3:
  1. **Project name** — What is this project called?
  2. **Tech stack** — What languages, frameworks, and tools does this project use?
  3. **Core principles** — Name 3–5 non-negotiable principles for this project (e.g., "test-first", "accessibility", "API-first", "simplicity"). If unsure, say "use defaults" and you'll get a starter set.

### If `.devspark/` already exists — Version Check

1. Read `.devspark/VERSION`, the canonical DevSpark stamp. Parse `version:` as semver (`X.Y.Z`). If the stamp is missing or malformed, treat the installed version as `unknown` and refresh the framework files without changing project knowledge or user overrides.
2. **Read the canonical manifest from a fresh, uncached fetch.** `manifest.json` is the **single source of truth** — it carries the latest version (`latest`), the exact list of files a canonical install must place (`install`, an array of `{source, dest, category}`), the `.devspark/` root allowlist (`devspark_root`), and the fetch base (`raw_base`). The agent never has to guess the file list. You MUST bypass every cache (see **Step 0**); do **not** use a webpage-fetch tool. Fetch the whole manifest **once** and reuse it in Step 4 and the prune step:

   - PowerShell:

     ```powershell
     $manifest = Invoke-RestMethod -Uri "https://dev.makeboldspark.com/dist/manifest.json?cb=$([DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds())" -Headers @{ 'Cache-Control'='no-cache'; 'Pragma'='no-cache' }
     $LATEST_VERSION = $manifest.latest
     "Latest: $LATEST_VERSION  |  install entries: $($manifest.install.Count)"
     ```

   - bash:

     ```bash
     curl -fsS -H 'Cache-Control: no-cache' "https://dev.makeboldspark.com/dist/manifest.json?cb=$(date +%s%N)" -o /tmp/devspark-manifest.json
     LATEST_VERSION=$(jq -r .latest /tmp/devspark-manifest.json)
     echo "Latest: $LATEST_VERSION  |  install entries: $(jq '.install | length' /tmp/devspark-manifest.json)"
     ```

   Read the `latest` field as `LATEST_VERSION`. If the value looks older than a release that was just published, re-run with a new `cb` value — never trust a cached read. (If `manifest.install` is absent, you are reading a manifest published before manifest-driven installs — re-fetch with a new cache-buster; the current release always includes it.)
3. Compare and act:

| Installed version | Latest version | Action |
|---|---|---|
| Same as latest | — | Verify framework files. If any stock prompt, template, script, or command shim is missing, run **repair mode** below. Otherwise report: "DevSpark is already at vX.Y.Z — nothing to update." Skip to Step 11.7 (Initialize and Reconcile `.knowledge/`), then Step 12 (Verify & Report). |
| Installed major is lower than latest major | Newer major | Report the version gap, then run **update mode** below. |
| Older than latest within the same major | Newer | Report the version gap, then run **update mode** below. |
| `unknown` (VERSION missing) | Any | Treat as outdated. Run **update mode**. |

#### Update Mode

Tell the user: "Updating DevSpark from vX.Y.Z → vY.Y.Y. Your `.devspark.work/` and `.knowledge/` files will not be touched."

Execute **only** these steps in order, then skip to Step 11.7 (Initialize and Reconcile `.knowledge/`), then Step 12 (Verify & Report):

- **Step 4** — Re-install every file in the manifest `install` array (commands, templates, skills, scripts, registry; not the `skill` category) into its `dest`, overwriting in place
- **Step 7** — Re-create all command entry point files (overwrite — they are framework files)
- **Step 7.5** — Retire 8.x entry points (the 8.x classes only when the installed major version is below 9; orphans on every run)
- **Step 9.5** — Prune any non-canonical `.devspark/` files (uses `manifest.devspark_root`)
- **Step 10** — Update `.devspark/VERSION` with new version and today's date
- **Step 11 (review, advisory — never modify `.devspark.work/`)** — Report three staleness signals so the team can act:
  - **Orphaned overrides** — any file in `.devspark.work/commands/`, `.devspark.work/{git-user}/commands/`, `.devspark.work/scripts/bash/`, or `.devspark.work/scripts/powershell/` whose matching stock default no longer exists under `.devspark/` (only `devspark.*.md` command override files mirror stock). Recommend deleting or re-pointing.
  - **Missing/stale entry points** — cross-check `.devspark/defaults/commands/devspark.*.md` against `.cursor/commands/devspark-*.md`; report stock commands with no entry point (re-run Step 7) and entry points with no stock command (Step 7.5 orphan handling).

**Never touch** `.devspark.work/`, `.knowledge/`, the constitution, `.gitignore`, or platform guide files (`.cursorrules`, etc.), except for the single confirmed action in Step 7.5.

#### Repair Mode

If the installed version matches `LATEST_VERSION` but framework files are missing, tell the user: "DevSpark is already at vX.Y.Z, but the framework install is incomplete. Re-fetching stock files to repair it. Your `.devspark.work/` and `.knowledge/` files will not be touched."

Execute **only** these steps in order, then skip to Step 11.7 (Initialize and Reconcile `.knowledge/`), then Step 12 (Verify & Report):

- **Step 4** — Re-install every file in the manifest `install` array whose `dest` is missing or stale, overwriting in place
- **Step 7** — Re-create all command entry point files (overwrite missing or stale copies)
- **Step 7.5** — Retire 8.x entry points (the 8.x classes only when the installed major version is below 9; orphans on every run)
- **Step 9.5** — Prune any non-canonical `.devspark/` files (uses `manifest.devspark_root`)
- **Step 10** — Re-write `.devspark/VERSION` using the current `LATEST_VERSION` and today's date

---

## Step 3: Create Directory Structure

Create these directories (skip any that already exist):

```text
.devspark/
├── defaults/commands/
├── scripts/
└── templates/

.cursor/
└── commands/
```

---

## Step 4: Install Canonical Framework Files (manifest-driven)

> This single step replaces the former hardcoded "pull prompts / templates / skills / scripts" steps. The manifest's `install` array is the **authoritative** list of every file a canonical DevSpark install must place — stock command prompts, helper templates, the full `templates/` tree (skills, workflows, aliases, prompts, risk-checklists), **both** script sets, and `agents-registry.json`. You never maintain or guess this list; you replay it. It is generated by the release pipeline from the exact same mapping the CLI template package applies, so a prompt-first install is equivalent to the zip install.

The `install` list includes the **Agent Skills** under `.devspark/templates/skills/` — notably `templates/skills/write-spec/SKILL.md`, required by `/devspark-specify` (a missing skill silently degrades it to pre-2.4 behaviour).

The list also carries entries of category `skill` (the Copilot command skills, destined for `.github/skills/`). This agent does not use them: skip every `skill` entry in the replay and in the validation below.

Using the `$manifest` object (PowerShell) / `/tmp/devspark-manifest.json` (bash) captured in **Step 2**, download every other entry from `{raw_base}/{source}` (cache-busted) and write it to `{dest}`, creating parent directories as needed:

- PowerShell:

  ```powershell
  $rawBase = $manifest.raw_base
  $items = @($manifest.install | Where-Object { $_.category -ne 'skill' })
  foreach ($item in $items) {
    $cb  = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
    $dir = Split-Path -Parent $item.dest
    if ($dir) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    Invoke-WebRequest -Uri "$rawBase/$($item.source)?cb=$cb" `
      -Headers @{ 'Cache-Control'='no-cache'; 'Pragma'='no-cache' } -OutFile $item.dest
  }
  "Installed $($items.Count) canonical files."
  ```

- bash:

  ```bash
  raw_base=$(jq -r .raw_base /tmp/devspark-manifest.json)
  jq -r '.install[] | select(.category != "skill") | [.source, .dest] | @tsv' /tmp/devspark-manifest.json |
  while IFS=$'\t' read -r src dest; do
    mkdir -p "$(dirname "$dest")"
    curl -fsS -H 'Cache-Control: no-cache' "$raw_base/$src?cb=$(date +%s%N)" -o "$dest"
  done
  echo "Installed $(jq '[.install[] | select(.category != "skill")] | length' /tmp/devspark-manifest.json) canonical files."
  ```

### Step 4 Validation (required)

Confirm every installed `dest` in the manifest now exists on disk:

```powershell
$missing = $items | Where-Object { -not (Test-Path $_.dest) }
if ($missing) { $missing | ForEach-Object { Write-Host "MISSING: $($_.dest)" } }
else { Write-Host "All $($items.Count) canonical files present." }
```

```bash
miss=0
while IFS= read -r dest; do
  [ -f "$dest" ] || { echo "MISSING: $dest"; miss=$((miss+1)); }
done < <(jq -r '.install[] | select(.category != "skill") | .dest' /tmp/devspark-manifest.json)
echo "Missing files: $miss"
```

If any file is missing, re-fetch that entry before continuing. Both the PowerShell and Bash script sets are always installed (the manifest includes both), so the repository works on Windows, macOS, and Linux with no reinstall when switching machines.

---

## Step 7: Create Cursor Command Shims

For each command in `.devspark/defaults/commands/devspark.{name}.md`, create a file at `.cursor/commands/devspark-{name}.md` (the hyphenated name is what makes the command `/devspark-{name}`; the data paths inside stay dotted). If a file with that name already exists and is not one of the generated forms described in Step 7.5, leave it, and report it there as a conflict; otherwise overwrite it in place:

```markdown
## Prompt Resolution

Determine the current git user by running `git config user.name`.
Normalize to a folder-safe slug: lowercase, replace spaces with hyphens, strip non-alphanumeric/hyphen chars.

Read and execute the instructions from the **first file that exists**:
1. `.devspark.work/{git-user}/commands/devspark.{name}.md` (personalized override)
2. `.devspark.work/commands/devspark.{name}.md` (team customization)
3. `.devspark/defaults/commands/devspark.{name}.md` (stock default)

## User Input

{{input}}

Pass the user input above to the resolved prompt.
```

Replace `{name}` with the actual command name (e.g., `constitution`, `plan`, `implement`).

---

## Step 7.5: Retire 8.x Entry Points

> Runs in **Update** and **Repair** modes. Skip it in a Fresh Install and when the mode is Already Current. The 8.x legacy classes below apply only when the installed version read in Step 2 has a major below 9; the orphan class applies on every Update and Repair run. The mode comes from the installed major version, never guessed. The procedure is stateless: it writes no marker and no flag, so the candidate rule alone decides. A second and third run list nothing and change nothing, and an interrupted run recomputes the list from what remains.

Step 4 and Step 7 have already installed the 9.0 entry points (`.cursor/commands/devspark-<cmd>.md`). This agent installs no native skills: the `skill` category belongs to Copilot only. A retirement problem never blocks that install: report it and continue.

DevSpark 9.0 spells every command `/devspark-<cmd>`. The 8.x dotted entry points would list every command twice, so they are retired here.

### Build the candidate list

For each stock command `<cmd>` in `.devspark/defaults/commands/devspark.<cmd>.md`, examine only `.cursor/commands/devspark.<cmd>.md`. Classify the file if it exists:

| Class | Test | Action |
|---|---|---|
| Unmodified managed entry point | Frontmatter is absent, or has only keys from `description`, `handoffs`, `agent` and `name` (a `name` must equal `devspark.<cmd>` for the file's own command, quoted or not); and the body, after normalizing CRLF and trailing whitespace, is one of the two generated forms below | Delete |
| Edited managed-name file | Anything else: another frontmatter key, a `name` for a different command, or any added, removed or reordered paragraph, path or section | Move to the quarantine; never delete |
| Foreign file | No stock command name | Left untouched |

The two generated body forms, with the command name substituted:

- **Package form** — the Prompt Resolution section (the three resolution paths for the command and the `Where {git-user}` clarification) and a `User Input` section holding one fenced `$ARGUMENTS` or `{{args}}` placeholder.
- **Quickstart form** — the same Prompt Resolution section (the `Where {git-user}` line may be absent) and a `User Input` section holding one `{{input}}`, `$ARGUMENTS` or `{{args}}` placeholder, bare or fenced, followed by `Pass the user input above to the resolved prompt.`

`description` text is free: it varies across 8.x releases. Hashes are not used.

Also build these lists:

- **Conflicts** — every `devspark-<cmd>.md` that Step 7 left unwritten because it is not a generated form. Report them; never overwrite them. A `devspark-<cmd>` skill folder under `.github/skills/` belongs to a Copilot setup and is left untouched.
- **Orphan entry points** — every `.cursor/commands/devspark-<name>.md` that is a generated form but whose `<name>` has no stock command. List them for deletion.

### Show the list and ask once

If every list is empty, report "No 8.x entry points to retire." and continue. Otherwise show the lists and ask for **one confirmation** covering all of the actions: deletions, moves to the quarantine and orphan removals. Without a yes, change nothing and tell the user how to re-run. Act only on the listed files.

### Act and verify

- Delete each unmodified managed entry point and each orphan entry point.
- Quarantine each edited file: move it byte-identical to `.devspark.work/migration/8.x-entry-points/<file name>`. If that name already exists, add a numeric suffix; never overwrite an existing file. Report each one with this remedy: to keep the edit, recreate it as a customization in `.devspark.work/commands/devspark.<cmd>.md` (team) or `.devspark.work/{git-user}/commands/devspark.<cmd>.md` (developer). The 9.0 entry point picks it up through the existing precedence.
- Report conflicts so a human can rename or remove the file.

The quarantine is the only write this procedure makes inside a repository-owned root, and it only adds new files. It never touches, modifies, deletes or overwrites existing files in `.devspark.work/`, `.knowledge/` or `.archive/`, customization files, or lifecycle artifacts.

Then re-run the candidate list: every list must be empty except the reported items, and every stock command must have a `devspark-<cmd>.md` entry point.

---

## Step 8: Create .cursorrules

If `.cursorrules` does not exist in the project root, create it:

```markdown
# DevSpark — Spec-Driven Development

This project uses DevSpark for structured, spec-driven development.

## Constitution
Before making changes, read `.knowledge/governance/constitution.md` — it defines the project's non-negotiable principles.

## Available Commands
Use `/devspark-{command}` to invoke DevSpark workflows:
- /devspark-specify — Define requirements and user stories
- /devspark-plan — Create implementation plan
- /devspark-tasks — Break plan into actionable tasks
- /devspark-implement — Execute tasks
- /devspark-create-pr — Draft or update a pull request
- /devspark-pr-review — Constitution-based PR review
- /devspark-quickfix — Lightweight bug fix workflow

See `.devspark/defaults/commands/` for the full command list.
```

If `.cursorrules` already exists, append the DevSpark section.

---

## Step 9: Seed the Constitution

If `.knowledge/governance/constitution.md` does not already exist, fetch `https://dev.makeboldspark.com/raw/.knowledge/governance/constitution.md` and save it there.

If the file was migrated from `.specify/` or already existed, preserve it and do not overwrite it.

Only when creating a new constitution, use the project name, tech stack, and core principles collected after Step 2 to customize `.knowledge/governance/constitution.md`:

- Replace `[PROJECT_NAME]` with the actual project name
- Fill in the core principles the user provided
- Add the tech stack as a "Technology" or "Stack" section

---

## Step 9.5: Prune Non-Canonical `.devspark/` Files

> Runs in **Update** and **Repair** modes. A Fresh Install starts clean, so skip it there.

The canonical DevSpark `.devspark/` layout has **exactly four** root entries:

- `VERSION`
- `defaults/`
- `templates/`
- `scripts/`

Anything else at the `.devspark/` **root** is an obsolete framework entry and must be removed. Common offenders: root-level `aliases/`, `memory/`, `prompts/`, `risk-checklists/`, `skills/`, `workflows/`, a scratch `tmp/`, and stray root-level template `.md` files (`spec-template.md`, `plan-template.md`, etc.). The engine resolves atomic prompts, workflows, and aliases under `.devspark/templates/…` — **never** at the `.devspark/` root — so root-level copies are always stale.

Prune with an **allowlist** so only the canonical root entries survive. The allowlist comes from `manifest.devspark_root` (captured in **Step 2**); the four-entry default below is the fallback if the manifest field is absent. This only touches the `.devspark/` root and **never** touches `.devspark.work/`, `.knowledge/`, or `.archive/`:

```powershell
$keep = if ($manifest.devspark_root) { @($manifest.devspark_root) + 'VERSION' | Select-Object -Unique }
        else { @('VERSION','defaults','templates','scripts') }
Get-ChildItem .devspark -Force |
  Where-Object { $_.Name -notin $keep } |
  ForEach-Object {
    Write-Host "Removing non-canonical: .devspark/$($_.Name)"
    Remove-Item $_.FullName -Recurse -Force
  }
```

```bash
root=$(jq -r '.devspark_root[]?' /tmp/devspark-manifest.json 2>/dev/null | tr '\n' ' ')
[ -n "$root" ] || root="defaults templates scripts"
keep=" VERSION $root "
shopt -s dotglob nullglob
for entry in .devspark/*; do
  name=$(basename "$entry")
  case "$keep" in *" $name "*) continue;; esac
  echo "Removing non-canonical: .devspark/$name"
  rm -rf "$entry"
done
shopt -u dotglob nullglob
```

> Canonical content **under** `.devspark/templates/` (including `templates/skills/`, `templates/prompts/`) is preserved — only the `.devspark/` root is pruned.

---

## Step 10: Write VERSION Stamp

Use the `LATEST_VERSION` you already fetched in Step 2.

Create `.devspark/VERSION`:

```text
product: DevSpark
edition: Make-Bold
version: {LATEST_VERSION}
installed: {today's date YYYY-MM-DD}
method: cursor-quickstart
migrated-from: {legacy-layout | documentation-defaults | public-devspark | fresh}
```

---

## Step 11: Update .gitignore

Append to `.gitignore` if not already present:

```text
# DevSpark — personal overrides (never commit)
.documentation/*/commands/
```

---

## Step 11.7: Verify `.knowledge/` Index Health

**Always run this step, on every quickstart execution, regardless of mode** — Fresh Install,
Update, Repair, or Already Current. It is never skipped and never gated behind the mode
banner. It is cheap to re-run: if nothing has changed since the last run, it reports that and moves
on.

Run `python .devspark/scripts/build_knowledge_index.py --repo-root . --check`. If it passes with
no drift, report "`.knowledge/` index is current" and continue to Step 12. Otherwise, run
`python .devspark/scripts/build_knowledge_index.py --repo-root .` to regenerate
`.knowledge/index.json` and `.knowledge/ontology/coverage.json`, resolve every reported gap
(missing layer docs, unresolved `relations[].object` references, missing
`constrains`/`constrained_by` reciprocity, a `source_of_truth` path that doesn't exist), and
report a one-line summary of what was regenerated.

`.devspark/scripts/build_knowledge_index.py` is the one authoritative implementation — every
entry point (this step, CI, `/devspark-explain`, `site-audit`, `release`) resolves to it. If a
repo-root `scripts/build_knowledge_index.py` also exists from an older install, see the
reconciliation check below.

**Reconcile a legacy repo-root index builder.** Check whether `scripts/build_knowledge_index.py`
also exists at the repository root. If it does not, skip this. If it does, compare it byte-for-byte
against `.devspark/scripts/build_knowledge_index.py`:

- **Identical**: it is a redundant, framework-owned leftover from before scripts moved under
  `.devspark/`. Delete it and report the removal in your summary.
- **Different**: it may be a genuine project customization. Do not delete it automatically —
  report the diff and ask the repository owner whether to retire it in favor of
  `.devspark/scripts/build_knowledge_index.py` or keep it deliberately as a project override.

Either way, confirm no CI workflow, quickstart-derived doc, or project script in this repository
still invokes the root copy — point every caller at `.devspark/scripts/build_knowledge_index.py`.

---

## Step 12: Verify & Report

Confirm the installation:

- Check that every file in the manifest `install` array exists at its `dest` (commands in `.devspark/defaults/commands/`, templates and skills in `.devspark/templates/`, both script sets in `.devspark/scripts/`, `agents-registry.json` at the repo root)
- Check that the expected command entry point files from Step 7 exist in `.cursor/commands/` as `devspark-<cmd>.md`, and that Step 7.5 left no unmodified `devspark.<cmd>.md` there
- If any expected framework file is missing, stop and run **Repair Mode** before reporting success

- **Upgrade cleanup**: obsolete stock entries removed; `.devspark/VERSION`, project knowledge, temporary work, and user overrides preserved
- Number of stock commands in `.devspark/defaults/commands/`
- Number of command entry points in `.cursor/commands/`
- Retired 8.x entry points: deleted, quarantined, orphans, conflicts, or none
- Constitution status: seeded fresh, or already existed
- Repair status: not needed, or repaired missing framework files
- Explain the 3-tier override system and that `/devspark-personalize {command}` creates personal overrides

Tell the user: type `/devspark-specify` (or any command) in Cursor to start using DevSpark.

Add maintenance guidance (prompt-first):

- Basic (recommended): re-run the canonical quickstart in chat (it detects the existing install and runs Update Mode)
- `Follow the instructions at https://dev.makeboldspark.com/raw/quickstart/devspark_quickstart_cursor.md`

Upgrades refresh `.devspark/` stock files and preserve `.devspark.work/` and `.knowledge/` customizations.

---

## Multi-App Monorepo Support (Optional)

> **This section is entirely optional.** If your repository contains a single application, skip this section — DevSpark works perfectly without it.

For repositories containing **multiple applications** with different platforms, runtimes, or governance rules, DevSpark offers opt-in multi-app support.

### When to Consider Multi-App

- Your monorepo has apps with different tech stacks (e.g., .NET API + React UI)
- Different apps need different governance rules or risk profiles
- You want per-app constitutions, profiles, or code review scopes

### Quick Setup

1. Run `/devspark-add-application` to create a registry at `.devspark.work/devspark.registry.json` interactively
2. Each application gets its own `.knowledge/guides/` directory at `{app-path}/.knowledge/guides/`
3. Use `--app <id>` with any DevSpark command to scope it to a specific application
4. Use `--repo-scope` for repository-wide operations

### Key Concepts

- **Registry**: `.devspark.work/devspark.registry.json` defines all applications, profiles, and dependencies
- **Profiles**: Reusable rule bundles (e.g., `api-profile`, `web-profile`) that apps inherit
- **App-local manifest**: Optional `{app-path}/app.json` for app-specific overrides
- **Scope**: Every workflow runs in `repo`, `single-app`, or `cross-app` scope

### Commands

| Command | Purpose |
|---------|--------|
| `/devspark-add-application` | Register a new application in the registry |
| `/devspark-list-applications` | View all registered applications and profiles |
| `/devspark-validate-registry` | Validate registry schema, references, and consistency |

For details, see the [Multi-App Specification](https://github.com/MarkHazleton/DevSpark/blob/main/.devspark.work/specs/001-multi-app-monorepo-support/spec.md).
