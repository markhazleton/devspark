# Fork Divergence Tracking

**Fork**: github.com/MarkHazleton/spec-kit (Spec Kit Spark)  
**Upstream**: github.com/github/spec-kit  
**Last Sync**: 2026-02-20  
**Upstream Commit**: `b562438` (base divergence point)  
**Current Upstream**: `aeed11f`

---

## Overview

This document tracks how **Spec Kit Spark** has diverged from and absorbed changes from the upstream spec-kit repository. We maintain this fork to provide enhanced features for Adaptive System Life Cycle Development (ASLCD) while staying aware of upstream improvements.

## Fork Identity: Spec Kit Spark

**Version Scheme**: v1.x.x (vs upstream v0.x.x)  
**Core Philosophy**: Adaptive, lightweight processes for varying task complexity  
**Directory Structure**: `.documentation/` (vs upstream `docs/` and `.specify/`)

### Major Enhancements (Spark-Specific)

1. **New Commands**
   - `/speckit.critic` - Adversarial risk analysis
   - `/speckit.pr-review` - Constitution-based PR reviews
   - `/speckit.site-audit` - Website health analysis
   - `/speckit.evolve-constitution` - Constitution amendment proposals
   - `/speckit.quickfix` - Lightweight fixes without full spec overhead
   - `/speckit.release` - Release documentation management

2. **Documentation Structure**
   - Renamed `.specify/` → `.documentation/` for clarity
   - Extensive migration guides and tooling
   - Constitution guide, critic usage guide, PR review implementation
   - Adaptive lifecycle documentation

3. **Scripts & Automation**
   - `evolution-context.sh/ps1` - Constitution evolution support
   - `get-pr-context.sh/ps1` - PR context extraction
   - `quickfix-context.sh/ps1` - Lightweight fix workflow
   - `release-context.sh/ps1` - Release management
   - `site-audit.sh/ps1` - Website auditing

4. **Repository Health**
   - Git Spark reports (HTML/MD)
   - Enhanced branch protection documentation
   - Fork-specific release management

---

## Decision Criteria for Upstream Changes

### 🟢 AUTO-CHERRY-PICK (Apply automatically)

**Bug Fixes**
- Dependency version conflicts (e.g., click>=8.1 pinning)
- Path resolution errors
- CLI argument parsing issues
- Template syntax errors

**Security Fixes**
- Dependency vulnerabilities
- Path traversal fixes (Zip Slip, etc.)
- Input validation improvements

**Agent Compatibility**
- New agent support (if doesn't conflict with our structure)
- Agent CLI tool name fixes
- Agent configuration improvements

**Criteria**: ✅ Apply if:
- Pure bug fix with no structural dependencies
- No conflicts with `.documentation/` structure
- Improves stability or security
- Small, focused change

---

### 🟡 ADAPT & MERGE (Require adaptation)

**Template Changes**
- Wording improvements
- Bias removal (OpenAPI/GraphQL → generic)
- New template sections

**Script Enhancements**
- Improvements to shared scripts (check-prerequisites, common, etc.)
- New utility functions
- Enhanced error handling

**Documentation Updates**
- README improvements
- CONTRIBUTING updates
- New documentation patterns

**Criteria**: ⚠️ Adapt if:
- Core concept applies but paths/structure differ
- Can be modified to work with `.documentation/` folder
- Improves user experience without breaking Spark features
- Requires manual merge but valuable

**Adaptation Process**:
1. Cherry-pick to temporary branch
2. Adjust paths: `docs/` → `.documentation/`, `.specify/` → `.documentation/`
3. Verify no conflicts with Spark commands
4. Test and merge to main

---

### 🔴 IGNORE (Skip these)

**Structural Changes**
- Changes to `docs/` folder structure (we use `.documentation/`)
- Removal of files we've enhanced
- Directory reorganizations that conflict

**Version Management**
- Version bumps (we maintain independent versioning)
- Changelog entries (we maintain separate changelog)

**Workflow Changes**
- Release workflows tied to upstream structure
- CI/CD specific to github.com/github/spec-kit

**Feature Conflicts**
- Features that duplicate our Spark commands
- Templates that override our enhanced versions

**Criteria**: 🚫 Ignore if:
- Incompatible with our directory structure
- Duplicates existing Spark functionality
- Tied to upstream-specific infrastructure
- Would require extensive refactoring of Spark features

---

### 🔵 EVALUATE (Manual review required)

**Major Features**
- Extension system (#1551) - Modular plugin architecture
- Generic agent support (#1639) - Bring-your-own-agent
- AI Skills system (#1632) - Skills/prompts framework

**Infrastructure**
- New GitHub Actions workflows
- Testing frameworks (pytest, ruff)
- New release processes

**Criteria**: 🤔 Evaluate when:
- Large feature that might benefit Spark
- Requires significant testing
- May conflict with existing Spark architecture
- Needs team/maintainer decision

**Evaluation Process**:
1. Create RFC or discussion
2. Test in feature branch
3. Document compatibility implications
4. Decide: integrate, adapt, or defer

---

## Sync History

### 2026-02-20: Initial Sync Analysis

**Upstream Range**: `b562438` (base) → `aeed11f` (current)  
**Commits Analyzed**: 30  
**Action**: Setup tracking and criteria

#### Commits by Category

**🟢 Auto Cherry-Pick Candidates** (7):
```
fc3b98e - fix: rename Qoder AGENT_CONFIG key (qoder → qodercli)
6fca5d8 - fix: pin click>=8.1 dependency for Python 3.14
465acd9 - fix: include 'src/**' in release workflow triggers
04fc3fd - chore(deps): bump github/codeql-action 3→4
c78f842 - fix: typo in plan-template.md
36d9723 - fix: .specify.specify path error
4afbd87 - fix: preserve constitution.md during reinit
```

**🟡 Adapt & Merge Candidates** (6):
```
12405c0 - refactor: remove OpenAPI/GraphQL bias from templates
aeed11f - Add V-Model Extension Pack to catalog
0f7d04b - feat: add pull request template
686c91f - feat: add dependabot configuration
2203673 - Remove Maintainers section from README
b562438 - fix: resolve markdownlint errors
```

**🔴 Ignore** (5):
```
d410d18 - chore(deps): bump actions/stale 9→10
9a1e303 - Add stale workflow
76cca34 - Add new agent: Google Anti Gravity
[version bumps and upstream-specific changes]
```

**🔵 Evaluate** (3):
```
6150f1e - Add generic agent support with customizable directories
9402ebd - Feat/ai skills (prompt/skill system)
f14a47e - Add modular extension system
```

#### Action Items
- [ ] Cherry-pick 7 bug fixes
- [ ] Adapt 6 template/doc improvements
- [ ] Evaluate extension system integration
- [ ] Evaluate generic agent support
- [ ] Evaluate AI skills system

---

## Absorbed Changes Log

*Track successful cherry-picks and adaptations here*

### Applied Changes

#### 2026-02-20: GitHub Issue Templates

**Status**: ✅ Adapted & Merged  
**Upstream Commit**: `68d1d3a`  
**PR**: [#1655](https://github.com/github/spec-kit/pull/1655)  
**Category**: 🟡 ADAPT & MERGE

**Changes Applied**:
- Added `bug_report.yml` with Spark-specific URLs and agent list (17 agents)
- Added `feature_request.yml` with Spark-specific URLs and agent list
- Added `agent_request.yml` with Spark-specific URLs and current agent list
- Added `config.yml` with Spark contact links (removed Extension Development Guide link)

**Changes Deferred**:
- `extension_submission.yml` - Awaiting extension system implementation (upstream feature not yet in Spark)

**Adaptations Made**:
- All `github.com/github/spec-kit` → `github.com/MarkHazleton/spec-kit`
- All `github.com/manfredseee/spec-kit` → `github.com/MarkHazleton/spec-kit`
- Removed "Antigravity" agent (not yet supported in Spark)
- Updated agent lists to match current AGENTS.md (17 agents)
- Branding updated from "Spec Kit" to "Spec Kit Spark" where appropriate
- Removed extension development guide link (feature not yet available)

**Validation**:
- [ ] Templates render correctly on GitHub (requires push to verify)
- [ ] All links resolve to correct Spark repository locations
- [ ] Agent dropdowns match AGENTS.md exactly
- [ ] Blank issues disabled per config.yml

---

#### 2026-02-20: Template Bias Removal

**Status**: ✅ Applied (Cherry-picked)  
**Upstream Commit**: `12405c0` → Spark commit `a5f9773`  
**PR**: [#1652](https://github.com/github/spec-kit/pull/1652)  
**Category**: 🟡 ADAPT & MERGE  
**Applied**: 2026-02-20 17:07:22

**Changes Applied**:
- Removed OpenAPI/GraphQL-specific language from templates
- Updated terminology: "API contracts" → "interface contracts"
- Updated: "endpoints" → "interfaces" (in generic contexts)
- Expanded Project Type field: "web/mobile" → "library/cli/web-service/mobile-app/compiler/desktop-app"
- Made templates applicable to CLI tools, libraries, compilers, desktop apps

**Files Modified**:
- `templates/commands/plan.md` - Interface contracts section
- `templates/commands/specify.md` - Integration patterns defaults
- `templates/commands/tasks.md` - Contract/endpoint references
- `templates/plan-template.md` - Project Type field

**Adaptations Made**:
- None required - upstream changes compatible with Spark structure
- All Spark-specific enhancements preserved

**Validation**:
- [x] Templates use generic "interface contracts" terminology
- [x] Project Type field includes diverse categories
- [x] Web service backward compatibility maintained
- [x] CLI/library project types properly supported
- [x] No Spark-specific features removed

**Notes**:
Cherry-picked directly from upstream without modification. Changes align perfectly with Spark's goal of supporting diverse project types through Adaptive System Life Cycle Development (ASLCD).

---

#### 2026-02-20: Extension System and Qoder CLI Fix

**Status**: ✅ Applied  
**Upstream Commits**: `aeed11f` (extensions), `07077d0` (V-Model v0.2.0), `fc3b98e` (Qoder fix)  
**PRs**: [#1640](https://github.com/github/spec-kit/pull/1640), [#1656](https://github.com/github/spec-kit/pull/1656), [#1651](https://github.com/github/spec-kit/pull/1651)  
**Category**: 🟡 ADAPT & MERGE + 🟢 AUTO

**Changes Applied**:
- Created `extensions/` directory structure for community extensions
- Added `extensions/README.md` with Spark-specific branding
- Added `extensions/catalog.community.json` with V-Model Extension Pack v0.1.0
- Updated V-Model Extension Pack v0.1.0 → v0.2.0 (07077d0, added system-design and system-test commands)
- Fixed Qoder CLI tool name: `qoder` → `qodercli` in `create-github-release.ps1`

**Adaptations Made**:
- Updated README links: `github.com/github/spec-kit` → `github.com/MarkHazleton/spec-kit`
- Updated catalog URL to point to Spark's fork
- Enhanced README with Spark-specific context about extensions working alongside built-in commands

**Integration Decisions**:
- **Extension System**: Approved for integration. Enables community contributions without core modifications.
- **V-Model v0.2.0 Update** (07077d0): Applied - Updated catalog to v0.2.0 with 5 commands (added system-design, system-test).

**Validation**:
- [x] Extension directory created successfully
- [x] JSON validates correctly
- [x] No conflicts with Spark's `.documentation/` structure
- [x] Qoder CLI reference updated correctly
- [x] V-Model v0.2.0 catalog updated
- [x] Download URL verified (v0.2.0 tag)
- [x] Command count reflects new capabilities (5 commands)
- [ ] Test extension installation workflow (future work)

---

### Planned (Not Yet Applied)

**Bug Fixes**:
- `6fca5d8` - click>=8.1 dependency pin
- `c78f842` - plan-template.md typo
- `36d9723` - path error fix
- `4afbd87` - preserve constitution.md

**Template Improvements**:
- `b562438` - Markdownlint fixes

**Extension Updates**:
- `07077d0` - V-Model v0.2.0 update (deferred, blocked by extension system testing)

**Documentation**:
- `0f7d04b` - PR template for contributions

---

## Divergence Points

### File Structure

| Upstream | Spark | Status |
|----------|-------|--------|
| `docs/` | `.documentation/` | DIVERGED |
| `.specify/` | `.documentation/` | DIVERGED |
| `templates/` | `templates/` (enhanced) | ALIGNED |
| `scripts/` | `scripts/` (extended) | COMPATIBLE |
| `src/specify_cli/` | `src/specify_cli/` | MOSTLY ALIGNED |

### Commands

| Upstream | Spark | Notes |
|----------|-------|-------|
| `/specify` | `/speckit.specify` | Different namespace |
| `/plan` | `/speckit.plan` | Core commands aligned |
| `/tasks` | `/speckit.tasks` | Core commands aligned |
| - | `/speckit.critic` | Spark-only |
| - | `/speckit.pr-review` | Spark-only |
| - | `/speckit.site-audit` | Spark-only |
| - | `/speckit.evolve-constitution` | Spark-only |
| - | `/speckit.quickfix` | Spark-only |
| - | `/speckit.release` | Spark-only |

### Version Numbering

| Repository | Scheme | Current |
|------------|--------|---------|
| Upstream | v0.x.x | v0.1.4 |
| Spark | v1.x.x | v1.1.1 |

*Spark maintains independent semantic versioning to reflect major enhancements.*

---

## Maintenance Guidelines

### When to Sync

**Monthly Review**: Check upstream for valuable changes
**On Major Upstream Release**: Evaluate new features
**When Bugs Reported**: Check if upstream has fix
**Before Spark Release**: Ensure up-to-date with critical fixes

### Sync Workflow

1. **Fetch upstream**: `git fetch upstream`
2. **Run sync script**: `./scripts/powershell/sync-upstream.ps1` or `./scripts/bash/sync-upstream.sh`
3. **Choose workflow**:
   - **Interactive** (recommended): Review each commit with detailed implications and choose actions
   - **Review**: Quick categorized overview
   - **Auto**: Apply safe fixes automatically
4. **Manual adaptation**: Adapt template/doc changes as needed
5. **Update this document**: Record absorbed changes

### Conflict Resolution

**Path Conflicts** (docs/ vs .documentation/):
```bash
# During cherry-pick conflict
git show :3:docs/file.md > .documentation/file.md
git add .documentation/file.md
git cherry-pick --continue
```

**Template Conflicts**:
- Preserve Spark enhancements
- Merge upstream improvements manually
- Test commands after resolution

**Script Conflicts**:
- Favor upstream for shared scripts (common.sh, check-prerequisites.sh)
- Preserve Spark-only scripts
- Test all commands after merge

---

## Contributing Back to Upstream

### Candidates for Upstream Contribution

**Commands** (if generalized):
- `/speckit.pr-review` - Valuable for any constitution-based review
- `/speckit.site-audit` - Generic web accessibility/SEO tool
- `/speckit.quickfix` - Lightweight workflow pattern

**Documentation Improvements**:
- Constitution guide patterns
- Migration tooling concepts

**Bug Fixes**:
- Any bugs found in shared code paths

### Contribution Process

1. Create upstream-compatible branch
2. Remove Spark-specific dependencies
3. Adjust to upstream structure (docs/, .specify/)
4. Submit PR to github.com/github/spec-kit
5. Track in "Contributed to Upstream" section

---

## Contributed to Upstream

*Track PRs submitted back to upstream*

### Pending

- None yet

### Merged

- None yet

---

## Future Considerations

### Features to Watch

1. **Extension System** (f14a47e) - May complement our Spark commands
2. **Generic Agent Support** (6150f1e) - Could strengthen agent compatibility
3. **AI Skills Framework** (9402ebd) - Might enhance our command system

### Integration Opportunities

- Adapt extension system for Spark command distribution
- Use generic agent as fallback for unsupported agents
- Integrate AI skills with constitution/critic commands

### Long-term Strategy

- **Maintain Fork**: Continue Spark as enhanced variant
- **Selective Sync**: Cherry-pick valuable improvements
- **Contribute Back**: Share generalized innovations
- **Community**: Build Spark-specific community and extensions

---

## Quick Reference

### Sync Commands

```bash
# Fetch latest upstream
git fetch upstream

# View new commits
git log --oneline main..upstream/main

# Interactive review (recommended) - explains implications and prompts for action
./scripts/bash/sync-upstream.sh --mode interactive
# or PowerShell:
.\scripts\powershell\sync-upstream.ps1 -Mode interactive

# Quick categorized review
./scripts/bash/sync-upstream.sh --mode review

# Auto-apply safe fixes
./scripts/bash/sync-upstream.sh --mode auto

# Generate detailed report
./scripts/bash/sync-upstream.sh --mode report > sync-report.md

# Manual cherry-pick if needed
git cherry-pick <commit-hash>
# Fix conflicts: docs/ → .documentation/
git cherry-pick --continue
```

### Paths to Watch

When adapting upstream changes, adjust these paths:
- `docs/*` → `.documentation/*`
- `.specify/*` → `.documentation/*`
- Any hardcoded references to `docs/` folder

### Files Modified in Both

These files frequently change in both repos:
- `README.md` - Merge changes carefully
- `AGENTS.md` - Agent additions compatible
- `src/specify_cli/__init__.py` - Core CLI logic
- `templates/commands/*` - Enhance, don't replace
- `scripts/bash/*` - Usually compatible
- `scripts/powershell/*` - Usually compatible

---

**Last Updated**: 2026-02-20  
**Maintained By**: Mark Hazleton  
**Next Review**: 2026-03-20
