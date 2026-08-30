#!/usr/bin/env bash
set -euo pipefail

# create-release-packages.sh (workflow-local)
# Build DevSpark template release archives for each supported AI assistant and script type.
# Usage: .github/workflows/scripts/create-release-packages.sh <version>
#   Version argument should include leading 'v' (e.g., v1.0.0).
#   Optionally set AGENTS and/or SCRIPTS env vars to limit what gets built.
#     AGENTS  : space or comma separated subset of: claude gemini copilot cursor-agent qwen opencode windsurf codex amp shai bob antigravity (default: all)
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

AGENT_REGISTRY_FILE="agents-registry.json"

if [[ ! -f "$AGENT_REGISTRY_FILE" ]]; then
  echo "Missing agent registry: $AGENT_REGISTRY_FILE" >&2
  exit 1
fi

# Create and use .genreleases directory for all build artifacts
GENRELEASES_DIR=".genreleases"
mkdir -p "$GENRELEASES_DIR"
rm -rf "${GENRELEASES_DIR:?}"/* || true

rewrite_paths() {
  # DevSpark uses .devspark/ for framework files, .knowledge/ for current truth,
  # and .devspark.work/ for in-flight work packages.
  sed -E \
    -e 's@(/?)\.specify/@\1.documentation/@g' \
    -e 's@(^|[[:space:]]|`)/specs/@\1/.devspark.work/specs/@g' \
    -e 's@(^|[[:space:]]|`)/memory/@\1/.knowledge/governance/@g' \
    -e 's@(^|[[:space:]]|`)/scripts/@\1/.devspark/scripts/@g' \
    -e 's@(^|[[:space:]]|`)/templates/@\1/.devspark/templates/@g'
}

copy_relative_files() {
  local source_root=$1 destination_root=$2
  shift 2

  while IFS= read -r relative_path; do
    [[ -n $relative_path ]] || continue
    mkdir -p "$destination_root/$(dirname "$relative_path")"
    cp "$source_root/$relative_path" "$destination_root/$relative_path"
  done < <(find "$source_root" "$@" -print | sed "s#^$source_root/##")
}

get_registered_agents() {
  jq -r '.agents[].key' "$AGENT_REGISTRY_FILE"
}

get_agent_release_field() {
  local agent_key=$1 field=$2
  jq -r --arg key "$agent_key" --arg field "$field" '.agents[] | select(.key == $key) | .release[$field] // empty' "$AGENT_REGISTRY_FILE"
}

copy_agent_support_files() {
  local agent_key=$1 base_dir=$2
  jq -r --arg key "$agent_key" '.agents[] | select(.key == $key) | .release.support_files[]? | [.source, .destination] | @tsv' "$AGENT_REGISTRY_FILE" |
    while IFS=$'\t' read -r source_file destination_file; do
      [[ -n $source_file && -n $destination_file ]] || continue
      [[ -f $source_file ]] || continue
      mkdir -p "$base_dir/$(dirname "$destination_file")"
      cp "$source_file" "$base_dir/$destination_file"
    done
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
    
    echo "$body" > "$output_dir/devspark.$name.md"
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
        cat > "$output_dir/devspark.$name.$ext" <<SHIMEOF
description = "$description"

prompt = """
## Prompt Resolution

Determine the current git user by running \`git config user.name\`.
Normalize to a folder-safe slug: lowercase, replace spaces with hyphens, strip non-alphanumeric/hyphen chars.

Read and execute the instructions from the **first file that exists**:
1. \`.documentation/{git-user}/commands/devspark.$name.md\` (personalized override)
2. \`.documentation/commands/devspark.$name.md\` (team customization)
3. \`.devspark/defaults/commands/devspark.$name.md\` (stock default)

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
          echo "1. \`.documentation/{git-user}/commands/devspark.$name.md\` (personalized override)"
          echo "2. \`.documentation/commands/devspark.$name.md\` (team customization)"
          echo "3. \`.devspark/defaults/commands/devspark.$name.md\` (stock default)"
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
        } > "$output_dir/devspark.$name.$ext"
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
        { echo "description = \"$description\""; echo; echo "prompt = \"\"\""; echo "$body"; echo "\"\"\""; } > "$output_dir/devspark.$name.$ext" ;;
      md)
        echo "$body" > "$output_dir/devspark.$name.$ext" ;;
      agent.md)
        echo "$body" > "$output_dir/devspark.$name.$ext" ;;
    esac
  done
}

generate_copilot_prompts() {
  local agents_dir=$1 prompts_dir=$2
  mkdir -p "$prompts_dir"
  
  # Generate a .prompt.md file for each .agent.md file
  for agent_file in "$agents_dir"/devspark.*.agent.md; do
    [[ -f "$agent_file" ]] || continue
    
    local basename
    basename=$(basename "$agent_file" .agent.md)
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
  
  # Framework files go into .devspark/ (removable installation)
  DEVSPARK_DIR="$base_dir/.devspark"
  mkdir -p "$DEVSPARK_DIR"
  RELEASE_DATE=$(date +%F)
  {
    echo "version: ${NEW_VERSION#v}"
    echo "installed: $RELEASE_DATE"
    echo "method: release-package"
    echo "migrated-from: fresh"
  } > "$DEVSPARK_DIR/VERSION"

  # Current truth is user-owned and never included as repository content.
  mkdir -p "$base_dir/.knowledge/entities" "$base_dir/.knowledge/governance/decisions" "$base_dir/.knowledge/ontology" "$base_dir/.devspark.work/specs"
  
  # ADR-001: Always copy both script sets regardless of build variant.
  # The sh|ps variant only controls which {SCRIPT} path gets baked into command files.
  if [[ -d scripts ]]; then
    mkdir -p "$DEVSPARK_DIR/scripts"
    [[ -d scripts/bash ]] && { cp -r scripts/bash "$DEVSPARK_DIR/scripts/"; echo "Copied scripts/bash -> .devspark/scripts"; }
    [[ -d scripts/powershell ]] && { cp -r scripts/powershell "$DEVSPARK_DIR/scripts/"; echo "Copied scripts/powershell -> .devspark/scripts"; }
    find scripts -maxdepth 1 -type f -exec cp {} "$DEVSPARK_DIR/scripts/" \; 2>/dev/null || true
  fi
  
  [[ -d templates ]] && {
    copy_relative_files templates "$DEVSPARK_DIR" -type f -not -path "templates/commands/*" -not -name "vscode-settings.json"
    echo "Copied templates -> .devspark/templates"
  }
  
  # Generate canonical command prompts in .devspark/defaults/commands/ (stock, upgrade-safe)
  # Team customizations live in .documentation/commands/ and are never overwritten.
  generate_canonical_commands "$DEVSPARK_DIR/defaults/commands" "$script"
  echo "Generated canonical commands -> .devspark/defaults/commands"

  # Generate thin platform shims in agent-specific directories
  # Shims redirect to .documentation/commands/ with user-override resolution
  local commands_dir extension arg_format prompt_dir
  commands_dir=$(get_agent_release_field "$agent" commands_dir)
  extension=$(get_agent_release_field "$agent" extension)
  arg_format=$(get_agent_release_field "$agent" arg_format)
  prompt_dir=$(get_agent_release_field "$agent" prompt_dir)

  if [[ -z $commands_dir || -z $extension || -z $arg_format ]]; then
    echo "Incomplete release metadata for agent '$agent'" >&2
    exit 1
  fi

  generate_shims "$agent" "$extension" "$arg_format" "$base_dir/$commands_dir"

  if [[ -n $prompt_dir ]]; then
    generate_copilot_prompts "$base_dir/$commands_dir" "$base_dir/$prompt_dir"
  fi

  copy_agent_support_files "$agent" "$base_dir"
  ( cd "$base_dir" && zip -r "../devspark-template-${agent}-${script}-${NEW_VERSION}.zip" . )
  echo "Created $GENRELEASES_DIR/devspark-template-${agent}-${script}-${NEW_VERSION}.zip"
}

# Determine agent list
mapfile -t ALL_AGENTS < <(get_registered_agents)
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
ls -1 "$GENRELEASES_DIR"/devspark-template-*-"${NEW_VERSION}".zip
