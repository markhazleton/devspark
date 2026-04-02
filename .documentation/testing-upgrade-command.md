# Testing Guide: `devspark upgrade` Command

<!-- markdownlint-disable MD040 -->

This guide helps test the new `devspark upgrade` command implementation.

## Setup Test Environment

### 1. Install Development Version

```bash
cd /path/to/devspark
uv tool install --force --editable .
```

### 2. Create Test Projects

```bash
# Create a fresh test directory
mkdir ~/devspark-test
cd ~/devspark-test

# Test 1: New project with old structure
mkdir test-old-structure
cd test-old-structure
git init
mkdir -p memory scripts templates
echo "Old memory" > memory/constitution.md
echo "Old script" > scripts/test.sh
cd ..

# Test 2: New project with current structure
mkdir test-current-structure
cd test-current-structure
git init
devspark init --here --ai claude
cd ..

# Test 3: Project without git
mkdir test-no-git
cd test-no-git
devspark init --here --ai copilot
cd ..
```

## Test Cases

### Test 1: Dry Run Mode

```bash
cd test-current-structure
devspark upgrade --dry-run
```

**Expected:**

- ✅ Shows "DRY RUN COMPLETE - No changes made"
- ✅ Shows what would be updated
- ✅ No files are actually modified

### Test 2: Auto-Detection

```bash
cd test-current-structure
devspark upgrade --dry-run
```

**Expected:**

- ✅ Auto-detects Claude as AI assistant
- ✅ Shows "Detected AI assistant: Claude Code (claude)"

### Test 3: Old Structure Migration

```bash
cd test-old-structure
devspark upgrade --dry-run
```

**Expected:**

- ✅ Detects old structure
- ✅ Offers to run migration
- ✅ Shows migration would happen in actual run

### Test 4: Constitution Backup

```bash
cd test-current-structure
devspark upgrade --backup --dry-run
```

**Expected:**

- ✅ Shows would create constitution backup
- ✅ No actual backup created in dry run

### Test 5: Force Mode

```bash
cd test-current-structure
# Make uncommitted changes
echo "test" >> README.md
devspark upgrade --force --dry-run
```

**Expected:**

- ✅ Detects uncommitted changes
- ✅ With --force, doesn't prompt for confirmation

### Test 6: Agent Override

```bash
cd test-current-structure
devspark upgrade --ai copilot --dry-run
```

**Expected:**

- ✅ Uses copilot instead of detected claude
- ✅ Shows "Using AI assistant: GitHub Copilot (copilot)"

### Test 7: Skip Migration

```bash
cd test-old-structure
devspark upgrade --skip-migration --dry-run
```

**Expected:**

- ✅ Doesn't check for old structure
- ✅ Proceeds without migration

### Test 8: Non-DevSpark Project

```bash
mkdir ~/temp-test
cd ~/temp-test
devspark upgrade
```

**Expected:**

- ✅ Shows error: "Current directory is not a DevSpark project"
- ✅ Exits with code 1

### Test 9: No AI Agent Detected

```bash
cd test-no-git
rm -rf .github
devspark upgrade --dry-run
```

**Expected:**

- ✅ Shows "Could not auto-detect AI assistant"
- ✅ In actual run, would prompt for selection
- ✅ In dry run, uses default

### Test 10: Actual Upgrade (Non-Destructive)

```bash
cd test-current-structure
git add -A
git commit -m "before upgrade"
devspark upgrade
```

**Expected:**

- ✅ Detects clean working tree
- ✅ Auto-detects agent
- ✅ Downloads and applies templates
- ✅ Shows success message
- ✅ specs/ directory untouched
- ✅ Can view changes with `git diff`

### Test 11: Actual Upgrade with Backup

```bash
cd test-current-structure
git add -A
git commit -m "before upgrade with backup"
devspark upgrade --backup
```

**Expected:**

- ✅ Creates timestamped backup of constitution
- ✅ Backup file exists in .documentation/memory/
- ✅ Upgrade completes successfully

## Manual Verification

After each test, verify:

### File Safety Checks

```bash
# Check specs directory is untouched
ls -la specs/

# Check constitution exists
cat .documentation/memory/constitution.md

# Check git status
git status
git diff
```

### Agent Detection

```bash
# Test claude detection
ls -la .claude/commands/

# Test copilot detection
ls -la .github/agents/

# Test cursor detection
ls -la .cursor/commands/
```

### Migration Integration

```bash
# After migration, verify new structure
ls -la .documentation/
ls -la .documentation/memory/
ls -la .documentation/scripts/
ls -la .documentation/templates/

# Verify old backups exist
ls -la | grep .old
```

## Edge Cases

### Edge Case 1: Multiple Agent Directories

```bash
# Create project with multiple agents
mkdir test-multi-agent
cd test-multi-agent
git init
mkdir -p .claude/commands .github/agents
devspark upgrade --dry-run
```

**Expected:**

- ✅ Detects first agent found (claude)
- ✅ Works without errors

### Edge Case 2: Partial Structure

```bash
# Create project with partial old structure
mkdir test-partial
cd test-partial
git init
mkdir -p .documentation/memory memory
devspark upgrade --dry-run
```

**Expected:**

- ✅ Detects old memory/ needs migration
- ✅ Doesn't re-migrate .documentation/memory

### Edge Case 3: Constitution Already Backed Up

```bash
cd test-current-structure
devspark upgrade --backup
# Run again
devspark upgrade --backup
```

**Expected:**

- ✅ Creates second backup with different timestamp
- ✅ Both backups preserved

## Cleanup

```bash
cd ~
rm -rf ~/devspark-test
```

## Automated Test Script

```bash
#!/bin/bash
# test-upgrade.sh - Quick automated test of upgrade command

set -e

echo "Testing devspark upgrade command..."
echo ""

# Test 1: Help
echo "Test 1: Help message"
devspark upgrade --help
echo "✓ Help works"
echo ""

# Test 2: Version check
echo "Test 2: Version"
devspark version
echo "✓ Version works"
echo ""

# Test 3: Check command still works
echo "Test 3: Check command"
devspark check
echo "✓ Check works"
echo ""

# Test 4: Non-spec project
echo "Test 4: Non-spec project detection"
cd /tmp
devspark upgrade 2>&1 | grep -q "not a DevSpark project" && echo "✓ Correctly detects non-spec project" || echo "✗ Failed"
echo ""

echo "Basic tests complete!"
```

## Success Criteria

The upgrade command passes if:

1. ✅ `--dry-run` never modifies files
2. ✅ Auto-detection works for all agent types
3. ✅ Old structure migration is offered when detected
4. ✅ `--backup` creates timestamped backups
5. ✅ `--force` skips confirmations
6. ✅ Non-spec projects are rejected with clear error
7. ✅ specs/ directory is never touched
8. ✅ Git status checks work correctly
9. ✅ All help text is clear and accurate
10. ✅ Error messages are helpful

## Reporting Issues

If you find issues, report with:

1. Command used
2. Expected behavior
3. Actual behavior
4. Output/error messages
5. Project structure (ls -la output)

Example:

```
Command: devspark upgrade --dry-run
Expected: Shows dry run preview
Actual: Error "module not found"
Output: [paste output]
```
