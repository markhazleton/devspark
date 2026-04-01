#!/usr/bin/env bash
set -euo pipefail

# create-release-packages.sh (workflow-local)
# Build Spec Kit template release archives for each supported AI assistant and script type.
# Usage: .github/workflows/scripts/create-release-packages.sh <version>
#   Version argument should include leading 'v' (e.g., v1.0.0).
#   Optionally set AGENTS and/or SCRIPTS env vars to limit what gets built.
#     AGENTS  : space or comma separated subset of: claude gemini copilot cursor-agent qwen opencode windsurf codex amp shai bob (default: all)
#     SCRIPTS : space or comma separated subset of: sh ps (default: both)
#   Examples:
#     AGENTS=claude SCRIPTS=sh $0 v1.0.0
#     AGENTS="copilot,gemini" $0 v1.0.0
#     SCRIPTS=ps $0 v1.0.0

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <version-with-v-prefix>" >&2
  exit 1
fi
NEW_VERSION="$1"
if [[ ! $NEW_VERSION =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Version must look like v1.0.0 (standard semantic versioning)" >&2
  exit 1
fi

echo "Building release packages for $NEW_VERSION"

# Create and use .genreleases directory for all build artifacts
GENRELEASES_DIR=".genreleases"
mkdir -p "$GENRELEASES_DIR"
rm -rf "$GENRELEASES_DIR"/* || true

rewrite_paths() {
  # Spec Kit Spark uses .documentation/ instead of .specify/ to distinguish from upstream
  sed -E \
    -e 's@(/?)\.specify/@\1.documentation/@g' \
    -e 's@(^|[[:space:]]|`)/specs/@\1/.documentation/specs/@g' \
    -e 's@(^|[[:space:]]|`)/memory/@\1/.documentation/memory/@g' \
    -e 's@(^|[[:space:]]|`)/scripts/@\1/.documentation/scripts/@g' \
    -e 's@(^|[[:space:]]|`)/templates/@\1/.documentation/templates/@g'
}

generate_canonical_commands() {
  # Generate canonical command files in .documentation/commands/ (agent-agnostic)
  local output_dir=$1 script_variant=$2
  mkdir -p "$output_dir"
  for template in templates/commands/*.md; do
    [[ -f "$template" ]] || continue
    local name description script_command agent_script_command body
    name=$(basename "$template" .md)
    
    # Normalize line endings
    file_content=$(tr -d '\r' < "$template")
    
    # Extract description and script command from YAML frontmatter
    description=$(printf '%s\n' "$file_content" | awk '/^description:/ {sub(/^description:[[:space:]]*/, ""); print; exit}')
    script_command=$(printf '%s\n' "$file_content" | awk -v sv="$script_variant" '/^[[:space:]]*'"$script_variant"':[[:space:]]*/ {sub(/^[[:space:]]*'"$script_variant"':[[:space:]]*/, ""); print; exit}')
    
    if [[ -z $script_command ]]; then
      echo "Warning: no script command found for $script_variant in $template" >&2
      script_command="(Missing script command for $script_variant)"
    fi
    
    # Extract agent_script command from YAML frontmatter if present
    agent_script_command=$(printf '%s\n' "$file_content" | awk '
      /^agent_scripts:$/ { in_agent_scripts=1; next }
      in_agent_scripts && /^[[:space:]]*'"$script_variant"':[[:space:]]*/ {
        sub(/^[[:space:]]*'"$script_variant"':[[:space:]]*/, "")
        print
        exit
      }
      in_agent_scripts && /^[a-zA-Z]/ { in_agent_scripts=0 }
    ')
    
    # Replace {SCRIPT} placeholder with the script command
    body=$(printf '%s\n' "$file_content" | sed "s|{SCRIPT}|${script_command}|g")
    
    # Replace {AGENT_SCRIPT} placeholder with the agent script command if found
    if [[ -n $agent_script_command ]]; then
      body=$(printf '%s\n' "$body" | sed "s|{AGENT_SCRIPT}|${agent_script_command}|g")
    fi
    
    # Remove the scripts: and agent_scripts: sections from frontmatter while preserving YAML structure
    body=$(printf '%s\n' "$body" | awk '
      /^---$/ { print; if (++dash_count == 1) in_frontmatter=1; else in_frontmatter=0; next }
      in_frontmatter && /^scripts:$/ { skip_scripts=1; next }
      in_frontmatter && /^agent_scripts:$/ { skip_scripts=1; next }
      in_frontmatter && /^[a-zA-Z].*:/ && skip_scripts { skip_scripts=0 }
      in_frontmatter && skip_scripts && /^[[:space:]]/ { next }
      { print }
    ')
    
    # Apply argument substitution (canonical uses $ARGUMENTS as default) and path rewriting
    body=$(printf '%s\n' "$body" | sed 's/{ARGS}/$ARGUMENTS/g' | rewrite_paths)
    
    echo "$body" > "$output_dir/speckit.$name.md"
  done
}

generate_shims() {
  # Generate thin platform shims that redirect to canonical commands in .documentation/commands/
  local agent=$1 ext=$2 arg_format=$3 output_dir=$4
  mkdir -p "$output_dir"
  for template in templates/commands/*.md; do
    [[ -f "$template" ]] || continue
    local name description handoffs_block
    name=$(basename "$template" .md)
    
    # Normalize line endings
    file_content=$(tr -d '\r' < "$template")
    
    # Extract description from YAML frontmatter
    description=$(printf '%s\n' "$file_content" | awk '/^description:/ {sub(/^description:[[:space:]]*/, ""); print; exit}')
    
    # Extract handoffs block from YAML frontmatter (for Copilot)
    handoffs_block=$(printf '%s\n' "$file_content" | awk '
      /^handoffs:/ { in_handoffs=1; print; next }
      in_handoffs && /^  / { print; next }
      in_handoffs && /^[a-zA-Z]/ { in_handoffs=0 }
    ')
    
    case $ext in
      toml)
        cat > "$output_dir/speckit.$name.$ext" <<SHIMEOF
description = "$description"

prompt = """
## Prompt Resolution

Determine the current git user by running \`git config user.name\`.
Normalize to a folder-safe slug: lowercase, replace spaces with hyphens, strip non-alphanumeric/hyphen chars.

Read and execute the instructions from the **first file that exists**:
1. \`.documentation/{git-user}/commands/speckit.$name.md\` (personalized override)
2. \`.documentation/commands/speckit.$name.md\` (shared default)

Where \`{git-user}\` is the normalized slug from step above.

## User Input

\`\`\`text
${arg_format}
\`\`\`

Pass the user input above to the resolved prompt.
"""
SHIMEOF
        ;;
      md|agent.md)
        {
          echo "---"
          echo "description: $description"
          if [[ -n $handoffs_block ]]; then
            echo "$handoffs_block"
          fi
          echo "---"
          echo ""
          echo "## Prompt Resolution"
          echo ""
          echo "Determine the current git user by running \`git config user.name\`."
          echo "Normalize to a folder-safe slug: lowercase, replace spaces with hyphens, strip non-alphanumeric/hyphen chars."
          echo ""
          echo "Read and execute the instructions from the **first file that exists**:"
          echo "1. \`.documentation/{git-user}/commands/speckit.$name.md\` (personalized override)"
          echo "2. \`.documentation/commands/speckit.$name.md\` (shared default)"
          echo ""
          echo "Where \`{git-user}\` is the normalized slug from step above."
          echo ""
          echo "## User Input"
          echo ""
          echo '```text'
          echo "$arg_format"
          echo '```'
          echo ""
          echo "Pass the user input above to the resolved prompt."
        } > "$output_dir/speckit.$name.$ext"
        ;;
    esac
  done
}

generate_commands() {
  local agent=$1 ext=$2 arg_format=$3 output_dir=$4 script_variant=$5
  mkdir -p "$output_dir"
  for template in templates/commands/*.md; do
    [[ -f "$template" ]] || continue
    local name description script_command agent_script_command body
    name=$(basename "$template" .md)
    
    # Normalize line endings
    file_content=$(tr -d '\r' < "$template")
    
    # Extract description and script command from YAML frontmatter
    description=$(printf '%s\n' "$file_content" | awk '/^description:/ {sub(/^description:[[:space:]]*/, ""); print; exit}')
    script_command=$(printf '%s\n' "$file_content" | awk -v sv="$script_variant" '/^[[:space:]]*'"$script_variant"':[[:space:]]*/ {sub(/^[[:space:]]*'"$script_variant"':[[:space:]]*/, ""); print; exit}')
    
    if [[ -z $script_command ]]; then
      echo "Warning: no script command found for $script_variant in $template" >&2
      script_command="(Missing script command for $script_variant)"
    fi
    
    # Extract agent_script command from YAML frontmatter if present
    agent_script_command=$(printf '%s\n' "$file_content" | awk '
      /^agent_scripts:$/ { in_agent_scripts=1; next }
      in_agent_scripts && /^[[:space:]]*'"$script_variant"':[[:space:]]*/ {
        sub(/^[[:space:]]*'"$script_variant"':[[:space:]]*/, "")
        print
        exit
      }
      in_agent_scripts && /^[a-zA-Z]/ { in_agent_scripts=0 }
    ')
    
    # Replace {SCRIPT} placeholder with the script command
    body=$(printf '%s\n' "$file_content" | sed "s|{SCRIPT}|${script_command}|g")
    
    # Replace {AGENT_SCRIPT} placeholder with the agent script command if found
    if [[ -n $agent_script_command ]]; then
      body=$(printf '%s\n' "$body" | sed "s|{AGENT_SCRIPT}|${agent_script_command}|g")
    fi
    
    # Remove the scripts: and agent_scripts: sections from frontmatter while preserving YAML structure
    body=$(printf '%s\n' "$body" | awk '
      /^---$/ { print; if (++dash_count == 1) in_frontmatter=1; else in_frontmatter=0; next }
      in_frontmatter && /^scripts:$/ { skip_scripts=1; next }
      in_frontmatter && /^agent_scripts:$/ { skip_scripts=1; next }
      in_frontmatter && /^[a-zA-Z].*:/ && skip_scripts { skip_scripts=0 }
      in_frontmatter && skip_scripts && /^[[:space:]]/ { next }
      { print }
    ')
    
    # Apply other substitutions
    body=$(printf '%s\n' "$body" | sed "s/{ARGS}/$arg_format/g" | sed "s/__AGENT__/$agent/g" | rewrite_paths)
    
    case $ext in
      toml)
        body=$(printf '%s\n' "$body" | sed 's/\\/\\\\/g')
        { echo "description = \"$description\""; echo; echo "prompt = \"\"\""; echo "$body"; echo "\"\"\""; } > "$output_dir/speckit.$name.$ext" ;;
      md)
        echo "$body" > "$output_dir/speckit.$name.$ext" ;;
      agent.md)
        echo "$body" > "$output_dir/speckit.$name.$ext" ;;
    esac
  done
}

generate_copilot_prompts() {
  local agents_dir=$1 prompts_dir=$2
  mkdir -p "$prompts_dir"
  
  # Generate a .prompt.md file for each .agent.md file
  for agent_file in "$agents_dir"/speckit.*.agent.md; do
    [[ -f "$agent_file" ]] || continue
    
    local basename=$(basename "$agent_file" .agent.md)
    local prompt_file="$prompts_dir/${basename}.prompt.md"
    
    # Create prompt file with agent frontmatter
    cat > "$prompt_file" <<EOF
---
agent: ${basename}
---
EOF
  done
}

build_variant() {
  local agent=$1 script=$2
  local base_dir="$GENRELEASES_DIR/sdd-${agent}-package-${script}"
  echo "Building $agent ($script) package..."
  mkdir -p "$base_dir"
  
  # Copy base structure but filter scripts by variant
SPEC_DIR="$base_dir/.documentation"
  mkdir -p "$SPEC_DIR"

  [[ -d memory ]] && { cp -r memory "$SPEC_DIR/"; echo "Copied memory -> .documentation"; }
  
  # Only copy the relevant script variant directory
  if [[ -d scripts ]]; then
    mkdir -p "$SPEC_DIR/scripts"
    case $script in
      sh)
        [[ -d scripts/bash ]] && { cp -r scripts/bash "$SPEC_DIR/scripts/"; echo "Copied scripts/bash -> .documentation/scripts"; }
        # Copy any script files that aren't in variant-specific directories
        find scripts -maxdepth 1 -type f -exec cp {} "$SPEC_DIR/scripts/" \; 2>/dev/null || true
        ;;
      ps)
        [[ -d scripts/powershell ]] && { cp -r scripts/powershell "$SPEC_DIR/scripts/"; echo "Copied scripts/powershell -> .documentation/scripts"; }
        # Copy any script files that aren't in variant-specific directories
        find scripts -maxdepth 1 -type f -exec cp {} "$SPEC_DIR/scripts/" \; 2>/dev/null || true
        ;;
    esac
  fi
  
  [[ -d templates ]] && { mkdir -p "$SPEC_DIR/templates"; find templates -type f -not -path "templates/commands/*" -not -name "vscode-settings.json" -exec cp --parents {} "$SPEC_DIR"/ \; ; echo "Copied templates -> .documentation/templates"; }
  
  # Generate canonical command prompts in .documentation/commands/ (agent-agnostic)
  generate_canonical_commands "$SPEC_DIR/commands" "$script"
  echo "Generated canonical commands -> .documentation/commands"

  # Generate thin platform shims in agent-specific directories
  # Shims redirect to .documentation/commands/ with user-override resolution
  case $agent in
    claude)
      mkdir -p "$base_dir/.claude/commands"
      generate_shims claude md "\$ARGUMENTS" "$base_dir/.claude/commands" ;;
    gemini)
      mkdir -p "$base_dir/.gemini/commands"
      generate_shims gemini toml "{{args}}" "$base_dir/.gemini/commands"
      [[ -f agent_templates/gemini/GEMINI.md ]] && cp agent_templates/gemini/GEMINI.md "$base_dir/GEMINI.md" ;;
    copilot)
      mkdir -p "$base_dir/.github/agents"
      generate_shims copilot agent.md "\$ARGUMENTS" "$base_dir/.github/agents"
      # Generate companion prompt files
      generate_copilot_prompts "$base_dir/.github/agents" "$base_dir/.github/prompts"
      # Create VS Code workspace settings
      mkdir -p "$base_dir/.vscode"
      [[ -f templates/vscode-settings.json ]] && cp templates/vscode-settings.json "$base_dir/.vscode/settings.json"
      ;;
    cursor-agent)
      mkdir -p "$base_dir/.cursor/commands"
      generate_shims cursor-agent md "\$ARGUMENTS" "$base_dir/.cursor/commands" ;;
    qwen)
      mkdir -p "$base_dir/.qwen/commands"
      generate_shims qwen toml "{{args}}" "$base_dir/.qwen/commands"
      [[ -f agent_templates/qwen/QWEN.md ]] && cp agent_templates/qwen/QWEN.md "$base_dir/QWEN.md" ;;
    opencode)
      mkdir -p "$base_dir/.opencode/command"
      generate_shims opencode md "\$ARGUMENTS" "$base_dir/.opencode/command" ;;
    windsurf)
      mkdir -p "$base_dir/.windsurf/workflows"
      generate_shims windsurf md "\$ARGUMENTS" "$base_dir/.windsurf/workflows" ;;
    codex)
      mkdir -p "$base_dir/.codex/prompts"
      generate_shims codex md "\$ARGUMENTS" "$base_dir/.codex/prompts" ;;
    kilocode)
      mkdir -p "$base_dir/.kilocode/workflows"
      generate_shims kilocode md "\$ARGUMENTS" "$base_dir/.kilocode/workflows" ;;
    auggie)
      mkdir -p "$base_dir/.augment/commands"
      generate_shims auggie md "\$ARGUMENTS" "$base_dir/.augment/commands" ;;
    roo)
      mkdir -p "$base_dir/.roo/commands"
      generate_shims roo md "\$ARGUMENTS" "$base_dir/.roo/commands" ;;
    codebuddy)
      mkdir -p "$base_dir/.codebuddy/commands"
      generate_shims codebuddy md "\$ARGUMENTS" "$base_dir/.codebuddy/commands" ;;
    qodercli)
      mkdir -p "$base_dir/.qoder/commands"
      generate_shims qodercli md "\$ARGUMENTS" "$base_dir/.qoder/commands" ;;
    amp)
      mkdir -p "$base_dir/.agents/commands"
      generate_shims amp md "\$ARGUMENTS" "$base_dir/.agents/commands" ;;
    shai)
      mkdir -p "$base_dir/.shai/commands"
      generate_shims shai md "\$ARGUMENTS" "$base_dir/.shai/commands" ;;
    q)
      mkdir -p "$base_dir/.amazonq/prompts"
      generate_shims q md "\$ARGUMENTS" "$base_dir/.amazonq/prompts" ;;
    bob)
      mkdir -p "$base_dir/.bob/commands"
      generate_shims bob md "\$ARGUMENTS" "$base_dir/.bob/commands" ;;
  esac
  ( cd "$base_dir" && zip -r "../spec-kit-spark-template-${agent}-${script}-${NEW_VERSION}.zip" . )
  echo "Created $GENRELEASES_DIR/spec-kit-spark-template-${agent}-${script}-${NEW_VERSION}.zip"
}

# Determine agent list
ALL_AGENTS=(claude gemini copilot cursor-agent qwen opencode windsurf codex kilocode auggie roo codebuddy amp shai q bob qodercli)
ALL_SCRIPTS=(sh ps)

norm_list() {
  # convert comma+space separated -> line separated unique while preserving order of first occurrence
  tr ',\n' '  ' | awk '{for(i=1;i<=NF;i++){if(!seen[$i]++){printf((out?"\n":"") $i);out=1}}}END{printf("\n")}'
}

validate_subset() {
  local type=$1; shift; local -n allowed=$1; shift; local items=("$@")
  local invalid=0
  for it in "${items[@]}"; do
    local found=0
    for a in "${allowed[@]}"; do [[ $it == "$a" ]] && { found=1; break; }; done
    if [[ $found -eq 0 ]]; then
      echo "Error: unknown $type '$it' (allowed: ${allowed[*]})" >&2
      invalid=1
    fi
  done
  return $invalid
}

if [[ -n ${AGENTS:-} ]]; then
  mapfile -t AGENT_LIST < <(printf '%s' "$AGENTS" | norm_list)
  validate_subset agent ALL_AGENTS "${AGENT_LIST[@]}" || exit 1
else
  AGENT_LIST=("${ALL_AGENTS[@]}")
fi

if [[ -n ${SCRIPTS:-} ]]; then
  mapfile -t SCRIPT_LIST < <(printf '%s' "$SCRIPTS" | norm_list)
  validate_subset script ALL_SCRIPTS "${SCRIPT_LIST[@]}" || exit 1
else
  SCRIPT_LIST=("${ALL_SCRIPTS[@]}")
fi

echo "Agents: ${AGENT_LIST[*]}"
echo "Scripts: ${SCRIPT_LIST[*]}"

for agent in "${AGENT_LIST[@]}"; do
  for script in "${SCRIPT_LIST[@]}"; do
    build_variant "$agent" "$script"
  done
done

echo "Archives in $GENRELEASES_DIR:"
ls -1 "$GENRELEASES_DIR"/spec-kit-spark-template-*-"${NEW_VERSION}".zip

