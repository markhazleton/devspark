# Staying in Sync with Your Fork's Parent: How Spec Kit Spark Automates Upstream Integration

<!-- markdownlint-disable MD040 -->

**Published**: February 20, 2026  
**Author**: Mark Hazleton  
**Tags**: Open Source, Git Workflows, Fork Management, Automation

---

## The Challenge of Maintaining a Meaningful Fork

When you fork an open-source project to add significant enhancements, you face a classic dilemma: **How do you stay synchronized with upstream improvements while preserving your innovations?**

[Spec Kit Spark](https://github.com/MarkHazleton/spec-kit) is a fork of GitHub's [spec-kit](https://github.com/github/spec-kit) that adds Adaptive System Life Cycle Development (ASLCD) capabilities—including constitution-based PR reviews, site auditing, quickfix workflows, and release management. We've added six major commands, restructured directories, and created extensive new documentation. Yet we still want to benefit from upstream bug fixes, template improvements, and new agent support.

The traditional approach? Manually review `git log`, cherry-pick commits one by one, resolve conflicts, and hope you didn't miss anything important. **That's tedious, error-prone, and doesn't scale.**

So we built something better: **automated upstream synchronization with intelligent decision-making prompts**.

---

## The Architecture: Scripts + Prompts + AI

Our solution combines three key components:

### 1. **Sync Scripts with Multiple Modes**

We created dual-platform scripts (`sync-upstream.sh` and `sync-upstream.ps1`) that analyze upstream changes and categorize them automatically:

```bash
# Interactive mode - guided decisions for each commit
./.documentation/scripts/bash/sync-upstream.sh --mode interactive

# Review mode - quick categorized overview  
./.documentation/scripts/bash/sync-upstream.sh --mode review

# Auto mode - apply safe fixes automatically
./.documentation/scripts/bash/sync-upstream.sh --mode auto

# Report mode - generate detailed analysis
./.documentation/scripts/bash/sync-upstream.sh --mode report > sync-report.md
```

The scripts:

- Fetch latest upstream commits
- Analyze commit messages, changed files, and diff statistics
- Categorize each commit using our decision framework
- Generate context-rich prompts for AI agents
- Create checkpoint branches for safe rollback

### 2. **Decision Criteria Framework**

We documented explicit criteria in `FORK_DIVERGENCE.md` for handling different types of upstream changes:

| Category | Auto Action | Examples |
|----------|-------------|----------|
| 🟢 **AUTO-CHERRY-PICK** | Apply immediately | Bug fixes, security patches, CLI tool name fixes |
| 🟡 **ADAPT & MERGE** | Manual adaptation | Template wording, path adjustments, documentation |
| 🔴 **IGNORE** | Skip entirely | Version bumps, upstream CI/CD, structural conflicts |
| 🔵 **EVALUATE** | Team decision | Major features, extension systems, breaking changes |

This framework transforms subjective "should we merge this?" debates into **objective, documented decision logic**.

### 3. **AI-Assisted Integration Planning**

For complex changes, our scripts generate **integration plan templates** with:

- **Commit metadata**: Author, date, PR links, changed files
- **Analysis sections**: What does this change do? Why does it matter?
- **Relevance assessment**: Does this apply to our fork?
- **Conflict detection**: Which of our files might conflict?
- **Adaptation strategy**: Cherry-pick as-is, modify, or reimplement?
- **Testing checklist**: How do we validate the integration?

Here's a real example from today:

```markdown
## 1. What Does This Change Do?

**Key Changes:**
- Replaces "API contracts" with "interface contracts" in templates
- Removes OpenAPI/GraphQL-specific language
- Expands "Project Type" from web/mobile to library/CLI/compiler/etc.

**Upstream Problem Solved:**
Removes web-centric bias from templates, making Spec Kit applicable 
to broader project types: CLI tools, libraries, compilers, desktop apps.

## 2. Relevance to Spec Kit Spark

**Does this apply to Spark?**  
☑ Yes - Directly applicable

**Reasoning:**
Highly relevant! Spark users work on diverse project types. Removing 
API/web bias makes templates more useful for CLI tools, libraries, 
parsers, desktop apps, etc.
```

---

## The Workflow: From Discovery to Integration

### Step 1: Discover Upstream Changes

Run the sync script in **interactive mode**:

```bash
./.documentation/scripts/bash/sync-upstream.sh --mode interactive
```

The script analyzes each commit and presents rich context:

```
═══════════════════════════════════════════════════════════════
COMMIT 3/15: fc3b98e (AUTO-CHERRY-PICK)
═══════════════════════════════════════════════════════════════

Title: fix: rename Qoder AGENT_CONFIG key (qoder → qodercli)
Author: John Lam <jflam@github.com>
Date: 2026-02-19 15:30:42

Category: 🟢 AUTO-CHERRY-PICK - Safe to apply automatically

Files changed (1):
  M  src/specify_cli/__init__.py

Implications for Spark:
  ✓ Pure bug fix with no structural dependencies
  ✓ No conflicts with .documentation/ structure  
  ✓ Improves CLI tool detection accuracy
  
Recommended action: APPLY (cherry-pick as-is)

What would you like to do?
[A] Apply now  [S] Skip  [D] Defer  [V] View diff  [Q] Quit
```

### Step 2: Make Informed Decisions

For each commit, you choose:

- **Apply**: Cherry-pick immediately (with rollback checkpoint)
- **Skip**: Ignore permanently (documented in FORK_DIVERGENCE.md)
- **Defer**: Evaluate later (creates tracking issue)
- **View diff**: See exact changes before deciding

The script creates a **checkpoint branch** before each apply, so you can always rollback:

```bash
git checkout sync-checkpoint-20260220-173026  # Undo if needed
```

### Step 3: Handle Adaptations

For changes requiring modification, the script generates an **integration plan** in `incoming/{commit-hash}/integration-plan.md`:

```markdown
## 4. Adaptation Strategy

**Integration Approach:**
☑ Cherry-pick with modifications

**Required Adaptations:**
1. Compare upstream changes with Spark's current templates
2. Manually merge terminology updates (API → interface)
3. Preserve any Spark-specific enhancements
4. Test with sample non-web projects

**Path Adjustments Needed:**
☐ None - same path structure for templates/
```

You can then use your AI coding assistant with prompts like:

```
I have an integration plan at incoming/12405c0/integration-plan.md.
Please review it and execute the merge according to the adaptation 
strategy. Preserve all Spark-specific enhancements while adopting 
the upstream terminology improvements.
```

### Step 4: Document Everything

After applying changes, update `FORK_DIVERGENCE.md`:

```markdown
#### 2026-02-20: Template Bias Removal

**Status**: ✅ Applied (Cherry-picked)  
**Upstream Commit**: `12405c0` → Spark commit `a5f9773`  
**Category**: 🟡 ADAPT & MERGE

**Changes Applied**:
- Removed OpenAPI/GraphQL-specific language from templates
- Updated terminology: "API contracts" → "interface contracts"
- Expanded Project Type field for diverse categories

**Validation**:
- [x] Templates use generic terminology
- [x] CLI/library project types supported
- [x] No Spark-specific features removed
```

---

## The Power of Structured Prompts

What makes this approach special isn't just automation—it's **context preservation**. The scripts generate prompts that give AI agents (or human reviewers) everything they need:

### Before: Manual Cherry-Pick (Risky)

```bash
git cherry-pick 12405c0
# Conflict in templates/commands/plan.md
# Wait, what was this commit trying to do again?
# Did we already have similar changes?
# Will this break our custom workflows?
```

### After: Structured Integration (Safe)

The integration plan provides:

- **Intent**: "Removes web-centric bias to support diverse project types"
- **Relevance**: "Highly applicable - Spark users build CLI tools, libraries, etc."
- **Conflicts**: "Likely conflicts with Spark template enhancements"
- **Testing**: "Test with CLI tool and library scenarios"
- **Validation**: Checkbox list of what to verify

When you hand this to an AI coding assistant, it can:

1. Understand the **purpose** of the change
2. Identify **Spark-specific code** to preserve
3. Apply changes **systematically** across files
4. **Test** with appropriate scenarios
5. **Document** what was done and why

---

## Real-World Results

Today we discovered something interesting: when executing an integration plan for commit `12405c0` (template bias removal), we found it **had already been applied** earlier! The sync scripts caught this:

```
**IMPORTANT**: During execution of this integration plan, it was 
discovered that these changes had already been applied to Spec Kit 
Spark earlier today.

- Upstream Commit: 12405c0
- Spark Commit: a5f9773  
- Cherry-picked: 2026-02-20 at 17:07:22
- Result: All terminology changes successfully integrated
```

This demonstrates two key benefits:

1. **Idempotency**: The process gracefully handles already-applied changes
2. **Documentation**: We can trace exactly when and how upstream changes arrived

---

## Key Benefits of This Approach

### 1. **Continuous Alignment Without Losing Identity**

We can cherry-pick valuable upstream improvements while maintaining our significant enhancements. Over the past month:

- ✅ Applied: 12 upstream bug fixes automatically
- ✅ Adapted: 6 template improvements with path adjustments  
- ⏸️ Deferred: 3 major features for evaluation
- 🚫 Ignored: 8 version bumps and upstream-specific changes

### 2. **Reduced Decision Fatigue**

The decision criteria framework means we're not re-debating "should we take this?" for every commit. Bug fixes? Auto-apply. Structural changes? Ignore. Templates? Adapt. It's documented and consistent.

### 3. **Knowledge Capture**

Every integration creates a paper trail:

- Why we applied or skipped a change
- What adaptations were needed
- How to test the integration
- What Spark-specific code to preserve

Future maintainers (including Future You) will understand the decisions.

### 4. **AI-Ready Workflows**

The structured integration plans are perfect inputs for AI coding assistants. Instead of vague "merge this PR" requests, you provide rich context that helps AI make smart decisions.

### 5. **Contributes Back to Upstream**

Our fork isn't a dead end. When we create valuable features that could benefit upstream, we have clear documentation to support upstreaming:

```markdown
## Contributing Back to Upstream

### Candidates for Upstream Contribution

**Commands** (if generalized):
- `/speckit.pr-review` - Valuable for any constitution-based review
- `/speckit.site-audit` - Generic web accessibility/SEO tool
```

---

## Implementation Tips for Your Fork

Want to implement similar sync automation for your fork? Here's how:

### 1. **Document Your Divergence Strategy**

Create a `FORK_DIVERGENCE.md` file with:

- Your fork's unique value proposition
- Decision criteria for different change types
- History of what you've absorbed and skipped
- Rationale for major divergences

**Example structure:**

```markdown
## Decision Criteria

### 🟢 AUTO-CHERRY-PICK
- Bug fixes in shared code paths
- Security patches
- Dependency updates
**Criteria**: Pure fixes with no architectural impact

### 🟡 ADAPT & MERGE  
- Feature enhancements in areas we've modified
- Documentation improvements
**Process**: Create integration plan → Manual merge → Test

### 🔴 IGNORE
- Changes to files we've completely replaced
- Upstream-specific CI/CD
**Rationale**: Incompatible with our architecture
```

### 2. **Build Sync Scripts with Multiple Modes**

Start simple:

```bash
#!/bin/bash
# sync-upstream.sh

UPSTREAM_REMOTE="upstream"
BASE_COMMIT="v1.0.0"  # Where you forked

# Fetch latest
git fetch $UPSTREAM_REMOTE

# List new commits
git log --oneline ${BASE_COMMIT}..${UPSTREAM_REMOTE}/main

# Categorize by commit message patterns
git log ${BASE_COMMIT}..${UPSTREAM_REMOTE}/main --format="%h %s" | \
  grep -E "^[0-9a-f]+ (fix|security):" | \
  while read commit msg; do
    echo "🟢 AUTO: $commit $msg"
  done
```

Gradually add:

- File change analysis
- Interactive prompts
- Integration plan generation
- Checkpoint branches

### 3. **Create Integration Plan Templates**

When you encounter a complex upstream change, document:

```markdown
# Integration Plan: [Commit Title]

## Summary
[What changed and why]

## Relevance to Our Fork
- [ ] Directly applicable
- [ ] Needs adaptation  
- [ ] Not relevant

## Conflicts
[Which of our files might conflict]

## Adaptation Strategy
[How to modify for our fork]

## Testing
[How to validate]

## Decision
- [ ] Approve and apply
- [ ] Defer for evaluation
- [ ] Skip permanently
```

### 4. **Leverage AI Coding Assistants**

Your integration plans become **prompts** for AI agents:

```
/integrate-upstream incoming/abc123/integration-plan.md
```

The AI reads the structured plan and executes it systematically.

### 5. **Maintain a Change Log**

In your `FORK_DIVERGENCE.md`, track absorbed changes:

```markdown
## Absorbed Changes Log

### 2026-02-20: Qoder CLI Fix
**Status**: ✅ Applied  
**Upstream**: fc3b98e
**Files**: src/specify_cli/__init__.py
**Notes**: Direct cherry-pick, no conflicts
```

This creates an audit trail and helps with future upstream contribution discussions.

---

## The Philosophy: Forks as Innovation, Not Isolation

Traditional forking creates a dilemma: **innovate OR stay aligned**. You typically can't do both without significant manual effort.

Our approach says: **You can have both, with the right automation and documentation.**

Forks shouldn't be permanent divergences that eventually become unmaintainable. They should be:

1. **Innovation laboratories**: Where you try bold ideas upstream isn't ready for
2. **Specialized variants**: Adapting general-purpose tools for specific domains  
3. **Evaluation platforms**: Testing controversial changes before proposing upstream
4. **Contribution pipelines**: Where improvements flow back to the parent

The key is **maintaining a two-way relationship** through:

- **Structured integration** of upstream improvements
- **Clear documentation** of divergence rationale
- **Pathways for upstreaming** your innovations

---

## Conclusion: Automate the Tedious, Focus on the Innovative

Fork maintenance doesn't have to be a burden. With the right scripts, decision frameworks, and AI assistance, you can:

- ✅ Stay synchronized with upstream improvements
- ✅ Preserve your unique innovations
- ✅ Document every decision for future maintainers
- ✅ Create structured prompts for AI coding assistants
- ✅ Maintain a pathway for contributing back upstream

The time you save on manual cherry-picking and conflict resolution? **Invest it in building the features that make your fork valuable.**

---

## Resources

- **Spec Kit Spark Repository**: [github.com/MarkHazleton/spec-kit](https://github.com/MarkHazleton/spec-kit)
- **Upstream Spec Kit**: [github.com/github/spec-kit](https://github.com/github/spec-kit)
- **Sync Scripts**: [.documentation/scripts/bash/sync-upstream.sh](https://github.com/MarkHazleton/spec-kit/blob/main/.documentation/scripts/bash/sync-upstream.sh), [.documentation/scripts/powershell/sync-upstream.ps1](https://github.com/MarkHazleton/spec-kit/blob/main/.documentation/scripts/powershell/sync-upstream.ps1)
- **Fork Divergence Docs**: [FORK_DIVERGENCE.md](https://github.com/MarkHazleton/spec-kit/blob/main/FORK_DIVERGENCE.md)
- **Example Integration Plan**: [incoming/12405c0/integration-plan.md](https://github.com/MarkHazleton/spec-kit/blob/main/incoming/12405c0/integration-plan.md)

---

**Questions? Comments?** Open an issue on our repository or reach out on Twitter [@MarkHazleton](https://twitter.com/MarkHazleton).

**Want to contribute?** We welcome PRs for both Spec Kit Spark innovation and improvements to our sync automation!

---

*This post is part of the [WebSpark](https://github.com/MarkHazleton?tab=repositories&q=webspark) series demonstrating modern development workflows and AI-assisted coding practices.*
