# ASLCD Toolkit: Tangible Next Steps

> **Document Status**: Draft v0.1
> **Created**: 2026-02-03
> **Purpose**: Define concrete implementation steps for the next phase of development

---

## Overview

This document outlines the specific features, commands, and infrastructure needed to implement the **Governance Phase** (v1.2-1.5) of the ASLCD Toolkit. It covers:

1. The Landmark System (PR-gated checkpoints)
2. The Harvest Command (knowledge extraction + cleanup)
3. The Library Structure (pattern storage)
4. Supporting Commands and Infrastructure
5. Scalability Configurations (adapting to project size)

### Scalability Principle

Every feature in this phase must support the full spectrum of project sizes:

| Project Type | Expected Configuration |
|--------------|----------------------|
| Solo/Hobby | Landmarks disabled, harvest optional, minimal constitution |
| Startup (2-5) | Spec landmarks only, quickfix-heavy, growing constitution |
| Growing Team (5-20) | Full landmarks, active harvest, mature constitution |
| Enterprise (20+) | Multi-level landmarks, mandatory harvest, inherited constitution |

**Implementation rule**: Features should degrade gracefully. A solo developer should never see "landmark required" errors—the system should detect context and suggest appropriate rigor.

---

## Implementation Roadmap

```
v1.2.0 - Landmark Foundation
├── /speckit.landmark command
├── /speckit.status command
├── Configuration system (.speckit/config.yaml)
├── Profile system (solo, startup, team, enterprise)
└── PR template generation

v1.3.0 - Harvest System
├── /speckit.harvest command
├── Library directory structure
├── Harvest decision tree
├── Harvest logging
└── Context optimization (right-sized delivery)

v1.4.0 - Scalability & Brownfield
├── /speckit.compliance-score command
├── Constitution discovery integration
├── Incremental adoption workflow
├── Constitution inheritance (multi-repo)
└── Pattern usage analytics

v1.5.0 - Polish & Integration
├── CI/CD integration examples
├── IDE extension hooks
├── Documentation site updates
├── Migration guide from v1.1
├── Scaling guide (solo → enterprise)
└── Brownfield adoption guide
```

---

## Part 1: The Landmark System

### 1.1 Command Specification: `/speckit.landmark`

#### Purpose

Create PR-gated checkpoints that require team review and pass automated status checks before progression.

#### Usage

```bash
/speckit.landmark {type} [options]

# Examples
/speckit.landmark spec                    # Create spec review PR
/speckit.landmark plan                    # Create plan review PR
/speckit.landmark ready                   # Validate pre-implementation
/speckit.landmark spec --draft            # Create as draft PR
/speckit.landmark plan --reviewers @arch  # Assign specific reviewers
```

#### Landmark Types

| Type | Trigger Point | PR Contains | Required Checks |
|------|---------------|-------------|-----------------|
| `spec` | After `/speckit.specify` | `spec.md` | Constitution alignment, scope validation |
| `plan` | After `/speckit.plan` | `plan.md`, `data-model.md`, `contracts/` | Architecture review, spec coverage |
| `ready` | Before `/speckit.implement` | Nothing (validation only) | All prior landmarks, task readiness |

#### Command Flow: `landmark spec`

```markdown
## Execution Steps

1. **Verify Prerequisites**
   - Spec exists at `.documentation/specs/{name}/spec.md`
   - Current branch is feature branch (not main)
   - No uncommitted changes in spec directory

2. **Run Status Checks**
   - [ ] Constitution principles addressed (grep for principle keywords)
   - [ ] Acceptance criteria defined (look for "## Acceptance Criteria")
   - [ ] No conflicting active specs (check other spec directories)
   - [ ] Scope assessment (line count, complexity heuristics)

3. **Generate PR**
   - Title: `[SPEC] {spec-name}: {first-line-of-spec}`
   - Body: Status check results + review checklist
   - Labels: `spec-landmark`, `needs-review`
   - Base: main (or configured base branch)

4. **Output**
   ```
   Landmark: Spec Review

   ✓ Prerequisites met
   ✓ Status checks passed (4/4)

   PR Created: #142
   URL: https://github.com/org/repo/pull/142

   Awaiting review. Merge to proceed to planning.
   ```
```

#### Command Flow: `landmark plan`

```markdown
## Execution Steps

1. **Verify Prerequisites**
   - Spec landmark PR merged (check git history or PR state)
   - Plan exists at `.documentation/specs/{name}/plan.md`
   - Supporting artifacts exist (data-model.md, contracts/ if applicable)

2. **Run Status Checks**
   - [ ] All spec requirements have plan coverage
   - [ ] Data model is complete (if data-model.md exists)
   - [ ] API contracts valid JSON/YAML (if contracts/ exists)
   - [ ] Dependencies identified (check for ## Dependencies section)
   - [ ] No constitution violations in planned approach

3. **Generate PR**
   - Title: `[PLAN] {spec-name}: Technical approach`
   - Body: Architecture summary + check results
   - Labels: `plan-landmark`, `needs-arch-review`
   - Reviewers: From CODEOWNERS or config

4. **Output**
   ```
   Landmark: Plan Review

   ✓ Spec landmark: PR #142 merged
   ✓ Status checks passed (5/5)

   PR Created: #147
   URL: https://github.com/org/repo/pull/147

   Awaiting architecture review. Merge to proceed to implementation.
   ```
```

#### Command Flow: `landmark ready`

```markdown
## Execution Steps

1. **Verify All Prior Landmarks**
   - Spec PR merged
   - Plan PR merged (if configured as required)
   - Tasks generated

2. **Run Readiness Checks**
   - [ ] tasks.md exists and has tasks
   - [ ] No blocking issues in spec or plan
   - [ ] Constitution compliance verified
   - [ ] /speckit.critic run (optional, configurable)

3. **Output (No PR Created)**
   ```
   Landmark: Implementation Ready

   ✓ Spec approved: PR #142
   ✓ Plan approved: PR #147
   ✓ Tasks generated: 12 tasks
   ✓ Readiness checks passed

   Ready to implement. Run /speckit.implement to begin.
   ```
```

#### PR Templates

**Spec Review PR Body:**

```markdown
## Spec Review: {spec-name}

### Summary
{First paragraph of spec.md}

### Status Checks

- [x] Constitution alignment verified
- [x] Acceptance criteria defined
- [x] No conflicting specs
- [x] Scope: {small|medium|large}

### Review Checklist

- [ ] Requirements are clear and testable
- [ ] Scope is appropriate for single feature
- [ ] No obvious missing requirements
- [ ] Aligns with project direction

### Artifacts

- [`spec.md`](.documentation/specs/{name}/spec.md)

---
*Generated by /speckit.landmark spec*
```

**Plan Review PR Body:**

```markdown
## Plan Review: {spec-name}

### Architecture Summary
{Summary extracted from plan.md}

### Status Checks

- [x] Spec requirements covered
- [x] Data model complete
- [x] API contracts valid
- [x] Dependencies identified
- [x] Constitution compliance

### Review Checklist

- [ ] Technical approach is sound
- [ ] No over-engineering
- [ ] Dependencies are acceptable
- [ ] Aligns with existing architecture

### Artifacts

- [`plan.md`](.documentation/specs/{name}/plan.md)
- [`data-model.md`](.documentation/specs/{name}/data-model.md)
- [`contracts/`](.documentation/specs/{name}/contracts/)

---
*Generated by /speckit.landmark plan*
```

### 1.2 Command Specification: `/speckit.status`

#### Purpose

Show current spec state, landmark progress, and next recommended action.

#### Usage

```bash
/speckit.status                    # Current spec status
/speckit.status --all              # All active specs
/speckit.status 004-notifications  # Specific spec
```

#### Output Format

```markdown
## Spec Status: 004-notifications

### Landmarks

| Landmark | Status | PR | Date |
|----------|--------|-----|------|
| Spec Review | ✓ Merged | #142 | 2026-01-28 |
| Plan Review | ✓ Merged | #147 | 2026-01-30 |
| Implementation | ⏳ In Progress | #152 | - |
| Harvest | ○ Pending | - | - |

### Current State

- **Branch**: feature/004-notifications
- **Tasks**: 8/12 complete (67%)
- **Last Activity**: 2 hours ago

### Next Action

→ Complete remaining tasks, then merge PR #152

### Quick Commands

- View tasks: `cat .documentation/specs/004-notifications/tasks.md`
- Continue implementing: `/speckit.implement`
- Check compliance: `/speckit.site-audit --scope=constitution`
```

### 1.3 Configuration System

#### File: `.speckit/config.yaml`

```yaml
# Spec Kit Spark Configuration
# Place in repository root

version: "1.0"

# Project Profile (determines defaults for all other settings)
# Options: solo, startup, team, enterprise, custom
# Using a profile sets sensible defaults; override individual settings below
profile: "team"

# Profile Defaults Reference:
# ┌──────────┬─────────────┬──────────────┬──────────────┬─────────────┐
# │ Setting  │ solo        │ startup      │ team         │ enterprise  │
# ├──────────┼─────────────┼──────────────┼──────────────┼─────────────┤
# │ landmarks│ disabled    │ spec only    │ spec + plan  │ full chain  │
# │ harvest  │ optional    │ prompted     │ required     │ mandatory   │
# │ approvals│ 0           │ 1            │ 1-2          │ 2+          │
# │ quickfix │ always      │ default      │ available    │ restricted  │
# └──────────┴─────────────┴──────────────┴──────────────┴─────────────┘

# Landmark Configuration
landmarks:
  enabled: true  # Set to false for solo/hobby projects

  spec:
    required: true
    approvals: 1
    auto_assign_reviewers: true
    reviewers_from: "CODEOWNERS"  # or explicit list
    checks:
      - constitution-alignment
      - scope-validation
      - acceptance-criteria
    labels:
      - "spec-landmark"
      - "needs-review"

  plan:
    required: true
    approvals: 2
    reviewers:
      - "@org/architecture"
      - "@tech-lead"
    checks:
      - spec-coverage
      - data-model-complete
      - contract-validation
      - dependency-check
      - constitution-compliance
    labels:
      - "plan-landmark"
      - "needs-arch-review"

  implementation:
    checks:
      - all-tasks-complete
      - tests-pass
      - constitution-compliance

# Harvest Configuration
harvest:
  enabled: true
  require_merged_pr: true
  prompt_for_constitution: true
  prompt_for_patterns: true
  auto_delete_artifacts: false  # Require confirmation

  # What to harvest
  extract:
    patterns: true
    contracts: true  # External-facing only
    amendments: true

  # What to always delete
  delete:
    - "spec.md"
    - "plan.md"
    - "tasks.md"
    - "research.md"
    - "data-model.md"
    - "checklists/"

# Library Configuration
library:
  patterns_dir: ".documentation/library/patterns"
  contracts_dir: ".documentation/library/contracts"
  max_pattern_length: 50  # lines
  require_when_to_use: true
  require_see_also: true

# Branch Configuration
branches:
  main: "main"
  feature_prefix: "feature/"
  spec_prefix: "spec/"  # For spec-only branches

# Integration
integrations:
  github:
    enabled: true
    create_prs: true
    use_labels: true

  # Future integrations
  # jira:
  #   enabled: false
  #   project_key: "PROJ"

# Context Optimization (for AI agents)
context:
  # How much constitution to include in AI context
  # Options: minimal, relevant, full
  constitution_scope: "relevant"

  # Maximum patterns to include in context
  max_patterns: 5

  # Include pattern library index for discoverability
  include_pattern_index: true

  # Modular constitution sections (only include relevant ones)
  modular_sections: true

# Scalability Settings
scalability:
  # Auto-detect appropriate rigor based on change size
  auto_detect_scope: true

  # Suggest (not require) full workflow for changes over this threshold
  full_workflow_threshold:
    files_changed: 10
    lines_changed: 500

  # Allow quickfix for changes under this threshold
  quickfix_threshold:
    files_changed: 3
    lines_changed: 100

  # Constitution inheritance (for multi-repo organizations)
  inherit_from: null  # URL or path to parent constitution

  # Override inherited sections (if inherit_from is set)
  override_sections: []
```

#### Profile-Based Configuration Examples

**Solo Developer Config:**
```yaml
version: "1.0"
profile: "solo"

# Everything else uses solo defaults:
# - No landmarks
# - Optional harvest
# - Quickfix for everything
# - Minimal context delivery
```

**Startup Config:**
```yaml
version: "1.0"
profile: "startup"

# Override just what's different:
landmarks:
  spec:
    required: true
    approvals: 1
  plan:
    required: false  # Skip plan landmarks until team grows
```

**Enterprise Config:**
```yaml
version: "1.0"
profile: "enterprise"

scalability:
  inherit_from: "https://github.com/org/standards/constitution.md"
  override_sections:
    - "testing"  # This project has different testing requirements
```

### 1.4 Script Requirements

#### New Script: `landmark-context.sh` / `landmark-context.ps1`

**Inputs:**
- Landmark type (spec, plan, ready)
- Spec name (optional, auto-detect from branch)
- Options (--draft, --reviewers)

**Outputs (JSON):**
```json
{
  "SPEC_NAME": "004-notifications",
  "SPEC_DIR": ".documentation/specs/004-notifications",
  "LANDMARK_TYPE": "spec",
  "PRIOR_LANDMARKS": {
    "spec": { "status": "pending", "pr": null },
    "plan": { "status": "pending", "pr": null }
  },
  "STATUS_CHECKS": {
    "constitution_alignment": true,
    "acceptance_criteria": true,
    "no_conflicts": true,
    "scope": "medium"
  },
  "CONFIG": { ... },
  "BRANCH": "feature/004-notifications",
  "BASE_BRANCH": "main"
}
```

---

## Part 2: The Harvest System

### 2.1 Command Specification: `/speckit.harvest`

#### Purpose

Extract reusable wisdom from completed specs, then delete scaffolding artifacts.

#### Usage

```bash
/speckit.harvest                           # Harvest current spec
/speckit.harvest 004-notifications         # Harvest specific spec
/speckit.harvest --dry-run                 # Preview without changes
/speckit.harvest --skip-prompts            # Use defaults (no harvest, just delete)
/speckit.harvest --force                   # Skip PR merge check (dangerous)
```

#### Command Flow

```markdown
## Execution Steps

### 1. Verify Prerequisites

- Spec directory exists
- Implementation PR merged (landmark L3 complete)
- All tasks marked complete in tasks.md

If PR not merged:
```
Cannot harvest: Implementation PR not merged.

Spec: 004-notifications
Expected: PR merged to main
Found: PR #152 still open

Complete the implementation and merge PR before harvesting.
To override (not recommended): /speckit.harvest --force
```

### 2. Analyze for Harvestable Content

Scan spec artifacts for potential extractions:

#### Constitution Analysis
- Look for comments like "NOTE:", "LEARNING:", "PRINCIPLE:"
- Check if any constitution violations were resolved
- Identify patterns that could become principles

#### Pattern Analysis
- Identify reusable architectural approaches
- Look for solutions to recurring problems
- Check research.md for generalizable findings

#### Contract Analysis
- Identify external-facing API contracts
- Check if contracts are reusable by other features

### 3. Interactive Harvest Prompts

#### Constitution Prompt
```
Constitution Learnings

Did this spec reveal anything that should change how we
approach ALL future development?

Examples:
- A principle we violated and regretted
- A missing principle we needed
- A principle that blocked good work

[y] Yes, I have a constitution learning
[n] No, nothing to add (DEFAULT)

> n
```

If yes:
```
Describe the constitution learning (or 'skip'):
> We discovered that our "no external dependencies" rule
  blocked us from using a well-tested auth library,
  causing us to write insecure custom code.

Creating amendment proposal: AMEND-2026-004
Location: .documentation/memory/amendments/AMEND-2026-004.md

Amendment created. Requires review before merging to constitution.
```

#### Pattern Prompt
```
Reusable Patterns

Did this spec solve a problem in a way that future
features should reuse?

The "Would I Search For This?" Test:
In 6 months, working on a different feature, would you
search for how this was solved?

[y] Yes, there's a reusable pattern
[n] No, it's specific to this feature (DEFAULT)

> n
```

If yes:
```
Pattern name (short, descriptive):
> webhook-retry-strategy

When should this pattern be used? (1-2 sentences):
> When integrating with unreliable external services that
  require eventual delivery guarantees.

Creating pattern: PAT-008-webhook-retry-strategy.md
Location: .documentation/library/patterns/PAT-008-webhook-retry-strategy.md

Pattern created.
```

### 4. Delete Artifacts

```
Deleting Spec Artifacts

The following will be removed from the repository:
(They remain in git history via PR #152)

  .documentation/specs/004-notifications/
  ├── spec.md
  ├── plan.md
  ├── tasks.md
  ├── research.md
  ├── data-model.md
  └── contracts/
      └── notification-api.json

Confirm deletion? [y/N]: y

✓ Deleted: .documentation/specs/004-notifications/
```

### 5. Update Harvest Log

Append to `.documentation/memory/harvest-log.md`:

```markdown
## 2026-02-03: 004-notifications

- **Spec**: 004-notifications
- **PR**: #152
- **Commit**: abc123def
- **Harvested**:
  - Pattern: PAT-008-webhook-retry-strategy
- **Deleted**: spec.md, plan.md, tasks.md, research.md, data-model.md, contracts/
```

### 6. Final Output

```
Harvest Complete: 004-notifications

Summary:
├── Constitution amendments: 0
├── Patterns extracted: 1
│   └── PAT-008-webhook-retry-strategy
├── Contracts preserved: 0
└── Artifacts deleted: 6 files

Reference: git show abc123def
Harvest log: .documentation/memory/harvest-log.md

The spec served its purpose. Knowledge preserved. Scaffolding removed.
```
```

#### Dry Run Output

```markdown
## Harvest Preview: 004-notifications

**This is a dry run - no changes will be made**

### Prerequisites
✓ Implementation PR #152 merged
✓ All tasks complete (12/12)

### Potential Harvests

#### Constitution
No obvious learnings detected.
(You'll be prompted to confirm)

#### Patterns
Detected potential pattern in research.md:
- "Webhook retry with exponential backoff"
(You'll be prompted to extract or skip)

#### Contracts
No external-facing contracts detected.

### Files to Delete
- .documentation/specs/004-notifications/spec.md
- .documentation/specs/004-notifications/plan.md
- .documentation/specs/004-notifications/tasks.md
- .documentation/specs/004-notifications/research.md
- .documentation/specs/004-notifications/data-model.md

### To Execute
/speckit.harvest 004-notifications
```

### 2.2 The Harvest Decision Tree (Automated Guidance)

The harvest command should guide users through decisions:

```
┌─────────────────────────────────────────────────────────────────┐
│                    HARVEST DECISION TREE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  CONSTITUTION CHECK                                             │
│  ─────────────────                                              │
│  Did this spec reveal a gap in our principles?                  │
│                                                                 │
│  Indicators (auto-detected):                                    │
│  • Constitution violation in PR review comments                 │
│  • "we should have..." or "next time..." in research.md        │
│  • Exception granted during implementation                      │
│                                                                 │
│  If indicators found → Prompt user                              │
│  If no indicators → Default to "No" (still allow override)     │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  PATTERN CHECK                                                  │
│  ─────────────                                                  │
│  Did we solve a recurring problem in a reusable way?            │
│                                                                 │
│  Indicators (auto-detected):                                    │
│  • Similar patterns in existing library                         │
│  • Generic solution language in plan.md                         │
│  • "this approach can be used for..." in research.md           │
│                                                                 │
│  If indicators found → Prompt user with suggestion              │
│  If no indicators → Default to "No"                             │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  CONTRACT CHECK                                                 │
│  ──────────────                                                 │
│  Are there external-facing API contracts?                       │
│                                                                 │
│  Auto-detect:                                                   │
│  • Files in contracts/ directory                                │
│  • Check if "external" or "public" in contract description      │
│                                                                 │
│  If external contracts → Preserve in library                    │
│  If internal only → Delete with other artifacts                 │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  DEFAULT: Delete all artifacts, harvest nothing                 │
│  This is the HEALTHY default for most features.                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 Library Structure

```
.documentation/
├── library/
│   ├── index.md                    # Library catalog
│   ├── patterns/
│   │   ├── index.md                # Pattern catalog with one-liners
│   │   ├── PAT-001-auth-flow.md
│   │   ├── PAT-002-api-versioning.md
│   │   └── PAT-008-webhook-retry-strategy.md
│   └── contracts/
│       ├── index.md                # Contract catalog
│       └── public-api-v2.json
├── memory/
│   ├── constitution.md
│   ├── constitution-history.md
│   ├── amendments/
│   │   ├── AMEND-2026-001.md       # Pending review
│   │   └── AMEND-2026-004.md       # Pending review
│   └── harvest-log.md              # Record of all harvests
└── specs/                          # Only ACTIVE specs
    └── 005-current-feature/
```

#### Pattern File Format

```markdown
# Pattern: PAT-008 Webhook Retry Strategy

> Harvested from: 004-notifications (PR #152)
> Date: 2026-02-03

## When to Use

- Integrating with unreliable external services
- Async notifications that must eventually succeed
- Any webhook that can't afford to lose messages

## Approach

1. Exponential backoff: 1s → 2s → 4s → 8s → 16s
2. Maximum 5 retry attempts
3. Dead letter queue after max retries
4. Idempotency key required on receiver

## Key Considerations

- Receiver must handle duplicates (idempotency)
- Log all failures for debugging
- Alert on dead letter queue growth

## See Also

- Original spec: `git show abc123def:.documentation/specs/004-notifications/`
- Constitution: Error Handling principles (SEC-003)
```

**Note what's NOT in the pattern:**
- No code samples
- No configuration values
- No step-by-step implementation
- No file paths or class names

#### Amendment File Format

```markdown
# Amendment Proposal: AMEND-2026-004

> Proposed from: 004-notifications harvest
> Date: 2026-02-03
> Status: Pending Review

## Trigger

During the notifications feature, our "minimize external dependencies"
principle led us to implement custom retry logic instead of using a
proven library. This resulted in edge cases we didn't anticipate.

## Current Principle

> **DEP-002**: Minimize external dependencies. Prefer standard library
> solutions over third-party packages.

## Proposed Change

> **DEP-002**: Prefer proven, well-maintained dependencies over custom
> implementations for complex functionality (retry logic, auth, crypto).
> Minimize dependencies for simple functionality.

## Rationale

- Custom implementations of complex patterns introduce bugs
- Well-tested libraries encode years of edge case handling
- The cost of a dependency is lower than the cost of subtle bugs

## Decision

- [ ] Approved - merge to constitution
- [ ] Rejected - close without merge
- [ ] Modified - revise and re-review

## Reviewer Notes

(To be filled during review)
```

### 2.4 Harvest Log Format

```markdown
# Harvest Log

This log records all spec harvests, preserving references to deleted artifacts.

---

## 2026-02-03: 004-notifications

| Field | Value |
|-------|-------|
| Spec | 004-notifications |
| Implementation PR | #152 |
| Merge Commit | abc123def456 |
| Harvest Date | 2026-02-03 |

**Harvested:**
- Pattern: [PAT-008-webhook-retry-strategy](../library/patterns/PAT-008-webhook-retry-strategy.md)

**Deleted:**
- spec.md
- plan.md
- tasks.md
- research.md
- data-model.md
- contracts/notification-api.json

**Git Reference:**
```bash
# View original spec artifacts
git show abc123def:.documentation/specs/004-notifications/spec.md
```

---

## 2026-01-15: 003-user-preferences

| Field | Value |
|-------|-------|
| Spec | 003-user-preferences |
| Implementation PR | #128 |
| Merge Commit | 789xyz |
| Harvest Date | 2026-01-20 |

**Harvested:**
- None

**Deleted:**
- spec.md
- plan.md
- tasks.md

**Git Reference:**
```bash
git show 789xyz:.documentation/specs/003-user-preferences/
```

---
```

---

## Part 2.5: Brownfield Adoption Support

### 2.5.1 Constitution Discovery Integration

For legacy codebases, the harvest system should integrate with constitution discovery:

```markdown
## Brownfield Workflow

1. Run `/speckit.discover-constitution` on existing codebase
   - Extracts implicit patterns, conventions, violations
   - Generates draft constitution

2. Team reviews and refines discovered constitution
   - Remove false positives
   - Add missing principles
   - Mark areas for improvement

3. Begin incremental adoption
   - New features use full spec workflow
   - Bug fixes use quickfix with constitution checks
   - Legacy code gets gradual compliance scoring

4. Harvest learnings back into constitution
   - As legacy areas are modernized, patterns emerge
   - Constitution evolves to reflect actual practices
```

### 2.5.2 Compliance Scoring for Legacy Code

```markdown
## /speckit.compliance-score

Purpose: Quantify technical debt against constitution

Output:
```
Constitution Compliance Score: 73%

By Section:
├── Security (SEC-*):     89% ████████▉░
├── Error Handling (ERR-*): 71% ███████▏░░
├── Testing (TST-*):      62% ██████▏░░░
├── Dependencies (DEP-*): 78% ███████▊░░
└── API Design (API-*):   65% ██████▌░░░

Highest Impact Improvements:
1. Add error boundaries to 12 components (+4% overall)
2. Increase test coverage in /src/legacy (+3% overall)
3. Update 8 deprecated dependencies (+2% overall)

Trend: ↑2% from last month
```

This transforms subjective "code smell" into actionable metrics.
```

### 2.5.3 Incremental Landmark Adoption

For teams transitioning from no process to ASLCD:

```yaml
# Transition Configuration

landmarks:
  # Phase 1: Awareness (weeks 1-4)
  enabled: false  # No blocking, just suggestions
  suggest_for:
    - new_features
    - breaking_changes

  # Phase 2: Opt-in (weeks 5-8)
  enabled: true
  required: false  # Can skip with reason
  skip_reason_required: true

  # Phase 3: Required for new work (weeks 9+)
  enabled: true
  required: true
  legacy_exemption: true  # Legacy fixes can still use quickfix
```

---

## Part 3: Supporting Infrastructure

### 3.1 New Script: `harvest-context.sh` / `harvest-context.ps1`

**Purpose:** Gather context for harvest command

**Outputs (JSON):**
```json
{
  "SPEC_NAME": "004-notifications",
  "SPEC_DIR": ".documentation/specs/004-notifications",
  "ARTIFACTS": [
    "spec.md",
    "plan.md",
    "tasks.md",
    "research.md",
    "data-model.md",
    "contracts/notification-api.json"
  ],
  "IMPLEMENTATION_PR": {
    "number": 152,
    "state": "merged",
    "merge_commit": "abc123def456",
    "merged_at": "2026-02-03T10:30:00Z"
  },
  "TASKS_COMPLETE": true,
  "TASKS_TOTAL": 12,
  "TASKS_DONE": 12,
  "EXISTING_PATTERNS": ["PAT-001", "PAT-002", "PAT-007"],
  "POTENTIAL_PATTERNS": [
    {
      "source": "research.md",
      "indicator": "exponential backoff pattern",
      "confidence": "medium"
    }
  ],
  "CONSTITUTION_INDICATORS": [],
  "EXTERNAL_CONTRACTS": [],
  "CONFIG": { ... }
}
```

### 3.2 Updates to Existing Commands

#### `/speckit.release` Integration

Update release command to prompt for harvest:

```markdown
## After Release Archive

Release v1.3.0 created successfully.

### Harvest Prompt

The following completed specs were included in this release:
- 004-notifications
- 005-settings-sync

Would you like to harvest knowledge and clean up artifacts?

[y] Yes, harvest each spec
[n] No, keep artifacts in releases/ directory
[l] Later, I'll run /speckit.harvest manually

> y

Running harvest for 004-notifications...
Running harvest for 005-settings-sync...
```

#### `/speckit.site-audit` Integration

Add library health check:

```markdown
## Library Health

| Metric | Value | Status |
|--------|-------|--------|
| Total patterns | 8 | ✓ Healthy |
| Patterns used (last 90 days) | 5 | ✓ Active |
| Stale patterns (>1 year unused) | 1 | ⚠ Review |
| Pending amendments | 2 | ⚠ Needs review |

### Recommendations

- Review stale pattern: PAT-002-api-versioning
- Review pending amendments: AMEND-2026-001, AMEND-2026-004
```

### 3.3 Command Template Files to Create

| File | Purpose |
|------|---------|
| `templates/commands/landmark.md` | Landmark command specification |
| `templates/commands/harvest.md` | Harvest command specification |
| `templates/commands/status.md` | Status command specification |
| `templates/commands/library.md` | Library browsing command (optional) |

### 3.4 Context Optimization Implementation

#### Purpose

Ensure AI agents receive right-sized context regardless of codebase size.

#### Context Tiers

```markdown
## Tier 1: Quickfix Context (minimal)

Included:
- Relevant constitution section only (detected by file type/location)
- No patterns unless explicitly related
- No spec history

Example: Fixing a bug in auth module
→ AI receives: SEC-* principles, ERR-* principles
→ AI does NOT receive: API-*, TST-*, full constitution


## Tier 2: Feature Context (standard)

Included:
- Full spec for current feature
- Relevant constitution sections
- Up to 3 related patterns from library
- No other active specs

Example: Building new notification feature
→ AI receives: Full spec, SEC-*, API-*, ERR-*, PAT-003-event-handling


## Tier 3: Architecture Context (comprehensive)

Included:
- Full spec for current feature
- Complete constitution
- All potentially related patterns
- Related active specs (if any)
- Constitution history for relevant sections

Example: Redesigning authentication system
→ AI receives: Everything relevant + historical context
```

#### Implementation in Context Scripts

```bash
# In specify-context.sh / plan-context.sh

# Detect task complexity
if [ "$TASK_TYPE" == "quickfix" ]; then
  CONSTITUTION_SECTIONS=$(detect_relevant_sections "$FILE_PATHS")
  PATTERNS=""
elif [ "$TASK_TYPE" == "feature" ]; then
  CONSTITUTION_SECTIONS=$(get_feature_sections "$SPEC_PATH")
  PATTERNS=$(find_related_patterns "$SPEC_PATH" 3)
else
  CONSTITUTION_SECTIONS="full"
  PATTERNS=$(find_related_patterns "$SPEC_PATH" 10)
fi
```

### 3.5 Documentation Updates

| File | Updates Needed |
|------|----------------|
| `README.md` | Add landmark and harvest sections |
| `.documentation/index.md` | Update command list |
| `.documentation/quickstart.md` | Add governance workflow |
| `.documentation/adaptive-lifecycle.md` | Add harvest philosophy |
| `NEW: .documentation/landmarks.md` | Full landmark documentation |
| `NEW: .documentation/harvest.md` | Full harvest documentation |
| `NEW: .documentation/library-guide.md` | How to use/contribute to library |

---

## Part 4: Implementation Order

### Sprint 1: Foundation (1-2 weeks)

**Goal:** Basic landmark and status commands with profile support

1. Create `.speckit/config.yaml` schema and parser
2. Implement profile system (solo, startup, team, enterprise presets)
3. Implement `/speckit.status` command
4. Implement `/speckit.landmark spec` (spec review PR)
5. Create `landmark-context.sh` / `landmark-context.ps1`
6. Write basic documentation

**Deliverables:**
- Users can create spec review PRs
- Users can check current spec status
- Configuration file structure established
- **Profile selection guides new users to appropriate rigor level**

### Sprint 2: Full Landmarks (1-2 weeks)

**Goal:** Complete landmark system

1. Implement `/speckit.landmark plan`
2. Implement `/speckit.landmark ready`
3. Add status check automation
4. Add PR template generation
5. Integrate with existing commands

**Deliverables:**
- Full landmark workflow operational
- Automated status checks running
- PRs created with proper templates

### Sprint 3: Harvest Foundation (1-2 weeks)

**Goal:** Basic harvest command with context optimization

1. Create library directory structure
2. Implement `/speckit.harvest` (basic flow)
3. Create `harvest-context.sh` / `harvest-context.ps1`
4. Implement harvest log
5. Implement artifact deletion
6. **Implement context optimizer (right-sized AI context delivery)**

**Deliverables:**
- Users can harvest completed specs
- Artifacts properly deleted
- Harvest log maintained
- **AI agents receive appropriately-sized context based on task**

### Sprint 4: Scalability & Brownfield (1-2 weeks)

**Goal:** Smart harvest + brownfield adoption support

1. Implement pattern extraction flow
2. Implement constitution amendment flow
3. Add pattern detection heuristics
4. Add constitution indicator detection
5. Integrate with `/speckit.release`
6. **Implement `/speckit.compliance-score` command**
7. **Integrate with constitution discovery for brownfield**

**Deliverables:**
- Intelligent prompts guide users
- Patterns and amendments created properly
- Release command offers harvest option
- **Legacy codebases can quantify technical debt**
- **Incremental adoption path documented**

### Sprint 5: Polish (1 week)

**Goal:** Production ready for all project sizes

1. Full documentation
2. Migration guide
3. Example workflows for each profile (solo → enterprise)
4. CI/CD integration examples
5. **Scaling guide**: how to grow ceremony with team
6. **Brownfield adoption guide**: legacy system onboarding
7. Testing and bug fixes

**Deliverables:**
- Complete documentation
- Smooth upgrade path from v1.1
- Examples for common scenarios
- **Clear guidance for projects of all sizes**

---

## Part 5: Success Criteria

### Landmark System

| Criterion | Measurement |
|-----------|-------------|
| PRs created successfully | 100% of landmark commands create valid PRs |
| Status checks run | All configured checks execute |
| Clear next actions | `/speckit.status` always shows next step |
| Config respected | All config options work as documented |
| **Profile detection works** | System suggests appropriate profile for new projects |

### Harvest System

| Criterion | Measurement |
|-----------|-------------|
| Safe deletion | Never delete without merged PR (unless --force) |
| Git references work | `git show` commands in harvest log actually work |
| Patterns are lean | Average pattern < 30 lines |
| Default is "harvest nothing" | >80% of harvests extract 0 patterns |
| Constitution amendments rare | <1 amendment per 10 harvests |

### Scalability

| Criterion | Measurement |
|-----------|-------------|
| Solo dev experience | Zero mandatory ceremony for `profile: solo` |
| Startup efficiency | <5 minutes overhead per feature for `profile: startup` |
| Enterprise compliance | Full audit trail for `profile: enterprise` |
| Brownfield adoption | Constitution discovery runs on codebases up to 1M LOC |
| Context optimization | AI receives <20% of constitution for quickfixes |
| Graceful degradation | Missing config = sensible defaults, not errors |

### Overall

| Criterion | Measurement |
|-----------|-------------|
| Repo stays clean | Active specs directory has only in-progress work |
| Knowledge accessible | Patterns searchable and referenced |
| History preserved | Any deleted artifact recoverable from git |
| Process appropriate | Quickfixes skip landmarks, major features use them |
| **Right-sized rigor** | Overhead matches task complexity across all profiles |
| **Business value visible** | Compliance scores quantify technical debt |

---

## Appendix: File Listing

### New Files to Create

```
.speckit/
├── config.yaml                     # Configuration (user creates)
└── profiles/                       # Profile templates
    ├── solo.yaml                   # Solo developer defaults
    ├── startup.yaml                # Startup defaults
    ├── team.yaml                   # Growing team defaults
    └── enterprise.yaml             # Enterprise defaults

templates/
└── commands/
    ├── landmark.md                 # Landmark command
    ├── harvest.md                  # Harvest command
    ├── status.md                   # Status command
    ├── library.md                  # Library command (optional)
    └── compliance-score.md         # Compliance scoring command

scripts/
├── bash/
│   ├── landmark-context.sh         # Landmark context gathering
│   ├── harvest-context.sh          # Harvest context gathering
│   ├── compliance-context.sh       # Compliance scoring context
│   └── context-optimizer.sh        # Right-sized context delivery
└── powershell/
    ├── landmark-context.ps1
    ├── harvest-context.ps1
    ├── compliance-context.ps1
    └── context-optimizer.ps1

.documentation/
├── library/
│   ├── index.md                    # Library catalog
│   ├── patterns/
│   │   └── index.md                # Pattern catalog
│   └── contracts/
│       └── index.md                # Contract catalog
├── memory/
│   ├── amendments/                 # Amendment proposals
│   └── harvest-log.md              # Harvest record
├── landmarks.md                    # Landmark documentation
├── harvest.md                      # Harvest documentation
├── library-guide.md                # Library usage guide
├── scaling-guide.md                # How to scale ASLCD with team growth
└── brownfield-adoption.md          # Legacy codebase adoption guide
```

### Files to Modify

```
README.md                           # Add new sections + scalability
.documentation/index.md             # Update command list
.documentation/quickstart.md        # Add governance workflow + profiles
.documentation/adaptive-lifecycle.md # Add harvest philosophy + scaling
.documentation/roadmap.md           # Update with new features
templates/commands/release.md       # Add harvest integration
templates/commands/quickfix.md      # Add context optimization
templates/commands/specify.md       # Add context tiers
scripts/bash/release-context.sh     # Add harvest prompt logic
scripts/bash/specify-context.sh     # Add context optimization
scripts/powershell/release-context.ps1
scripts/powershell/specify-context.ps1
```

---

## Appendix B: Scalability Quick Reference

### Which Profile Should I Use?

| If you are... | Use profile | Landmarks | Harvest | Typical overhead |
|---------------|-------------|-----------|---------|------------------|
| Building alone or experimenting | `solo` | Disabled | Optional | Seconds per change |
| Small team moving fast | `startup` | Spec only | Prompted | Minutes per feature |
| Established team with standards | `team` | Full | Required | Hours per feature |
| Regulated or large organization | `enterprise` | Full + cross-team | Mandatory | Structured but not slower |

### Transitioning Between Profiles

```
solo → startup:   Enable spec landmarks when second developer joins
startup → team:   Enable plan landmarks when architecture decisions affect multiple people
team → enterprise: Enable inheritance when multiple repos need consistent standards
```

### The Golden Rule

> **Process overhead should match task complexity AND team context—never more, never less.**

A solo developer shouldn't feel bureaucratic burden. An enterprise team shouldn't suffer from process gaps. ASLCD provides the vocabulary; teams compose what fits.

---

*This document provides the tactical implementation plan. See `01-grand-vision-aslcd-toolkit.md` for the strategic vision and philosophy.*
