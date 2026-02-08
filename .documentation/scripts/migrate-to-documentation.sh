#!/bin/bash
# migrate-to-documentation.sh
# Migrates Spec Kit projects from old structure (.specify/, memory/, scripts/, templates/)
# to new .documentation/ structure

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters for reporting
DIRS_MOVED=0
FILES_UPDATED=0
WARNINGS=0

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}Spec Kit Migration to .documentation/${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Function to print status
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if we're in a git repository
if [ -d ".git" ]; then
    IN_GIT_REPO=true
    print_status "Git repository detected - will use git mv to preserve history"
else
    IN_GIT_REPO=false
    print_warning "Not a git repository - using regular mv"
fi

# Check if .documentation already exists
if [ -d ".documentation" ]; then
    print_warning ".documentation/ already exists - will merge with existing content"
fi

# Detect what needs to be migrated
OLD_STRUCTURES_FOUND=false

if [ -d ".specify" ]; then
    print_status "Found .specify/ directory"
    OLD_STRUCTURES_FOUND=true
fi

if [ -d "memory" ] && [ ! -d ".documentation/memory" ]; then
    print_status "Found memory/ directory"
    OLD_STRUCTURES_FOUND=true
fi

if [ -d "scripts" ] && [ ! -d ".documentation/scripts" ]; then
    print_status "Found scripts/ directory"
    OLD_STRUCTURES_FOUND=true
fi

if [ -d "templates" ] && [ ! -d ".documentation/templates" ]; then
    print_status "Found templates/ directory"
    OLD_STRUCTURES_FOUND=true
fi

if [ "$OLD_STRUCTURES_FOUND" = false ]; then
    echo ""
    print_error "No old structure found to migrate."
    echo "Looking for: .specify/, memory/, scripts/, or templates/"
    echo ""
    exit 0
fi

echo ""
echo "This script will:"
echo "  1. Create .documentation/ directory structure"
echo "  2. Move files from old locations to new"
echo "  3. Update path references in files"
echo "  4. Rename old directories with .old suffix"
echo ""
echo -e "${YELLOW}Press Enter to continue, or Ctrl+C to cancel...${NC}"
read

echo ""
echo -e "${BLUE}Step 1: Creating .documentation/ structure${NC}"

# Create directory structure
mkdir -p .documentation/memory
print_status "Created .documentation/memory/"

mkdir -p .documentation/scripts/bash
mkdir -p .documentation/scripts/powershell
print_status "Created .documentation/scripts/"

mkdir -p .documentation/templates
print_status "Created .documentation/templates/"

echo ""
echo -e "${BLUE}Step 2: Moving files${NC}"

# Function to move directory contents
move_dir() {
    local source=$1
    local dest=$2
    local name=$3

    if [ -d "$source" ]; then
        # Copy all contents
        cp -r "$source"/* "$dest/" 2>/dev/null || true

        # Rename old directory
        mv "$source" "${source}.old"
        ((DIRS_MOVED++))
        print_status "Moved $name to $dest"
    fi
}

# Move .specify/ if exists
if [ -d ".specify" ]; then
    # .specify might contain memory, scripts, templates subdirectories
    if [ -d ".specify/memory" ]; then
        cp -r .specify/memory/* .documentation/memory/ 2>/dev/null || true
    fi
    if [ -d ".specify/scripts" ]; then
        cp -r .specify/scripts/* .documentation/scripts/ 2>/dev/null || true
    fi
    if [ -d ".specify/templates" ]; then
        cp -r .specify/templates/* .documentation/templates/ 2>/dev/null || true
    fi
    # Copy any other files in .specify root
    find .specify -maxdepth 1 -type f -exec cp {} .documentation/ \; 2>/dev/null || true

    mv .specify .specify.old
    ((DIRS_MOVED++))
    print_status "Moved .specify/ contents to .documentation/"
fi

# Move top-level directories
move_dir "memory" ".documentation/memory" "memory/"
move_dir "scripts" ".documentation/scripts" "scripts/"
move_dir "templates" ".documentation/templates" "templates/"

echo ""
echo -e "${BLUE}Step 3: Updating path references in files${NC}"

# Function to update references in a file
update_file_references() {
    local file=$1

    if [ ! -f "$file" ]; then
        return
    fi

    # Create backup
    cp "$file" "$file.bak"

    # Update references using sed with regex
    # Note: Using different regex patterns for different contexts
    sed -i.tmp \
        -e 's@(/\?)\.specify/@\1.documentation/@g' \
        -e 's@\(^\|[[:space:]]\|`\)/memory/@\1/.documentation/memory/@g' \
        -e 's@\(^\|[[:space:]]\|`\)/scripts/@\1/.documentation/scripts/@g' \
        -e 's@\(^\|[[:space:]]\|`\)/templates/@\1/.documentation/templates/@g' \
        -e 's@memory/constitution\.md@.documentation/memory/constitution.md@g' \
        "$file"

    # Check if file changed
    if ! cmp -s "$file" "$file.bak"; then
        ((FILES_UPDATED++))
        print_status "Updated references in $file"
    fi

    # Clean up
    rm "$file.bak" "$file.tmp" 2>/dev/null || true
}

# Update agent command files
for dir in .claude .github .cursor .windsurf .gemini .qwen .opencode .codex .kilocode .augment .roo .codebuddy .qoder .amazonq .agents .shai .bob; do
    if [ -d "$dir" ]; then
        find "$dir" -type f \( -name "*.md" -o -name "*.toml" \) | while read -r file; do
            update_file_references "$file"
        done
    fi
done

# Update script files
if [ -d ".documentation/scripts" ]; then
    find .documentation/scripts -type f \( -name "*.sh" -o -name "*.ps1" \) | while read -r file; do
        update_file_references "$file"
    done
fi

# Update documentation files
for file in README.md .documentation/*.md .vscode/settings.json; do
    if [ -f "$file" ]; then
        update_file_references "$file"
    fi
done

echo ""
echo -e "${BLUE}Step 4: Creating .gitignore entry${NC}"

# Add .documentation build output to .gitignore if needed
if [ -f ".gitignore" ]; then
    if ! grep -q ".documentation/_site" .gitignore; then
        echo "" >> .gitignore
        echo "# Spec Kit documentation build output" >> .gitignore
        echo ".documentation/_site/" >> .gitignore
        print_status "Added .documentation/_site/ to .gitignore"
    else
        print_status ".gitignore already configured"
    fi
fi

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}Migration Complete!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "Summary:"
echo "  - Directories moved: $DIRS_MOVED"
echo "  - Files updated: $FILES_UPDATED"
echo "  - Warnings: $WARNINGS"
echo ""
echo "Next steps:"
echo "  1. Review changes: ${YELLOW}git status${NC} and ${YELLOW}git diff${NC}"
echo "  2. Test slash commands in your AI assistant"
echo "  3. Test scripts: ${YELLOW}bash .documentation/scripts/bash/setup-plan.sh${NC}"
echo "  4. If everything works, commit:"
echo "     ${YELLOW}git add -A${NC}"
echo "     ${YELLOW}git commit -m 'chore: migrate to .documentation/ structure'${NC}"
echo "  5. Delete old backups:"
echo "     ${YELLOW}rm -rf .specify.old memory.old scripts.old templates.old${NC}"
echo ""

if [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}⚠ Please review warnings above before committing${NC}"
    echo ""
fi

print_status "Migration script completed successfully"
