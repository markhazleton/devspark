#!/usr/bin/env bash
# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
# Note: pipefail is intentionally NOT set. This script uses many
# `printf ... | awk '... exit'` first-match extractions; under pipefail the
# producer can receive SIGPIPE (exit 141) when the reader exits early, causing
# intermittent build failures. errexit + nounset still catch real errors.
set -eu

# create-release-packages.sh (workflow-local)
# Build DevSpark template release archives for each supported AI assistant and script type.
# Usage: eng/release/create-release-packages.sh <version>
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
  # DevSpark separates framework, temporary work, current truth (plus published guidance), and archive.
  sed -E \
    -e 's@(/?)\.specify/@\1.knowledge/guides/@g' \
    -e 's@(^|[[:space:]]|`)/specs/@\1/.devspark.work/specs/@g' \
    -e 's@(^|[[:space:]]|`)/memory/@\1/.knowledge/governance/@g' \
    -e 's@(^|[[:space:]]|`)/scripts/@\1/.devspark/scripts/@g' \
    -e 's@(^|[[:space:]]|`)/templates/@\1/.devspark/templates/@g'
}

copy_relative_files() {
  local source_root=$1 destination_root=$2
  shift 2

  local relative_dir
  while IFS= read -r relative_path; do
    [[ -n $relative_path ]] || continue
    relative_dir=.
    [[ $relative_path == */* ]] && relative_dir=${relative_path%/*}
    [[ -d "$destination_root/$relative_dir" ]] || mkdir -p "$destination_root/$relative_dir"
    cp "$source_root/$relative_path" "$destination_root/$relative_path"
  done < <(find "$source_root" "$@" -print | sed "s#^$source_root/##")
}

get_registered_agents() {
  jq -r '.agents[].key' "$AGENT_REGISTRY_FILE" | tr -d '\r'
}

get_agent_release_field() {
  local agent_key=$1 field=$2
  jq -r --arg key "$agent_key" --arg field "$field" '.agents[] | select(.key == $key) | .release[$field] // empty' "$AGENT_REGISTRY_FILE" | tr -d '\r'
}

copy_agent_support_files() {
  local agent_key=$1 base_dir=$2
  jq -r --arg key "$agent_key" '.agents[] | select(.key == $key) | .release.support_files[]? | [.source, .destination] | @tsv' "$AGENT_REGISTRY_FILE" |
    tr -d '\r' | while IFS=$'\t' read -r source_file destination_file; do
      [[ -n $source_file && -n $destination_file ]] || continue
      [[ -f $source_file ]] || continue
      mkdir -p "$base_dir/$(dirname "$destination_file")"
      cp "$source_file" "$base_dir/$destination_file"
    done
}

generate_canonical_commands() {
  # Generate canonical command files in .devspark.work/commands/ (agent-agnostic)
  local output_dir=$1 script_variant=$2
  mkdir -p "$output_dir"
  for template in templates/commands/*.md; do
    [[ -f "$template" ]] || continue
    local name script_command agent_script_command body commands sed_args
    name=${template##*/}
    name=${name%.md}

    # Extract the script command (first matching line anywhere) and the agent_script command
    # (within the agent_scripts: block) from YAML frontmatter in one pass, one per line.
    # Line endings are normalized here and by tr below; each fork is costly on Windows.
    commands=$(awk -v re="^[[:space:]]*${script_variant}:[[:space:]]*" '
      { gsub(/\r/, "") }
      !script_done && $0 ~ re { script=$0; sub(re, "", script); script_done=1 }
      !agent_done {
        if ($0 ~ /^agent_scripts:$/) in_agent_scripts=1
        else if (in_agent_scripts && $0 ~ re) { agent=$0; sub(re, "", agent); agent_done=1 }
        else if (in_agent_scripts && $0 ~ /^[a-zA-Z]/) in_agent_scripts=0
      }
      script_done && agent_done { exit }
      END { printf "%s\n%s\n", script, agent }
    ' "$template")
    script_command=${commands%%$'\n'*}
    agent_script_command=${commands#*$'\n'}
    [[ $commands == *$'\n'* ]] || agent_script_command=

    if [[ -z $script_command ]]; then
      echo "Warning: no script command found for $script_variant in $template" >&2
      script_command="(Missing script command for $script_variant)"
    fi

    # Replace {SCRIPT}, {AGENT_SCRIPT} and {ARGS} (canonical uses $ARGUMENTS as default), remove
    # the scripts: and agent_scripts: sections from frontmatter while preserving YAML structure,
    # then rewrite paths. Frontmatter removal never depends on the substituted text.
    sed_args=(-e "s|{SCRIPT}|${script_command}|g")
    [[ -n $agent_script_command ]] && sed_args+=(-e "s|{AGENT_SCRIPT}|${agent_script_command}|g")
    sed_args+=(-e 's/{ARGS}/$ARGUMENTS/g')
    body=$(
      tr -d '\r' < "$template" | sed "${sed_args[@]}" |
        awk '
          /^---$/ { print; if (++dash_count == 1) in_frontmatter=1; else in_frontmatter=0; next }
          in_frontmatter && /^scripts:$/ { skip_scripts=1; next }
          in_frontmatter && /^agent_scripts:$/ { skip_scripts=1; next }
          in_frontmatter && /^[a-zA-Z].*:/ && skip_scripts { skip_scripts=0 }
          in_frontmatter && skip_scripts && /^[[:space:]]/ { next }
          { print }
        ' | rewrite_paths
    )

    echo "$body" > "$output_dir/devspark.$name.md"
  done
}

generate_shims() {
  # Generate thin platform shims that redirect to canonical commands in .devspark.work/commands/
  local agent=$1 ext=$2 arg_format=$3 output_dir=$4
  mkdir -p "$output_dir"
  awk -v ext="$ext" -v arg_format="$arg_format" -v outdir="$output_dir" '
    function toml_escape(s,   out, i, c) {
      out = ""
      for (i = 1; i <= length(s); i++) {
        c = substr(s, i, 1)
        if (c == "\\" || c == "\"") out = out "\\"
        out = out c
      }
      return out
    }
    FNR == 1 {
      name = FILENAME
      sub(/.*\//, "", name)
      sub(/\.md$/, "", name)
      desc = ""
      handoffs = ""
      in_handoffs = 0
      desc_done = 0
    }
    { sub(/\r$/, "") }
    !desc_done && /^description:/ {
      desc = $0
      sub(/^description:[[:space:]]*/, "", desc)
      desc_done = 1
    }
    /^handoffs:/ { in_handoffs = 1; handoffs = handoffs $0 "\n"; next }
    in_handoffs && /^  / { handoffs = handoffs $0 "\n"; next }
    in_handoffs && /^[a-zA-Z]/ { in_handoffs = 0 }
    FNR > 1 && /^---/ {
      outfile = outdir "/devspark-" name "." ext
      if (ext == "toml") {
        print "description = \"" toml_escape(desc) "\"\n\nprompt = \"\"\"" > outfile
        print "## Prompt Resolution\n" > outfile
        print "Determine the current git user by running `git config user.name`." > outfile
        print "Normalize to a folder-safe slug: lowercase, replace spaces with hyphens, strip non-alphanumeric/hyphen chars.\n" > outfile
        print "Read and execute the instructions from the **first file that exists**:" > outfile
        print "1. `.devspark.work/{git-user}/commands/devspark." name ".md` (personalized override)" > outfile
        print "2. `.devspark.work/commands/devspark." name ".md` (team customization)" > outfile
        print "3. `.devspark/defaults/commands/devspark." name ".md` (stock default)\n" > outfile
        print "Where `{git-user}` is the normalized slug from step above.\n" > outfile
        print "## User Input\n\n```text\n" arg_format "\n```\n\nPass the user input above to the resolved prompt.\n\"\"\"" > outfile
      } else {
        print "---\ndescription: " desc > outfile
        if (handoffs != "") printf "%s", handoffs > outfile
        print "---\n\n## Prompt Resolution\n" > outfile
        print "Determine the current git user by running `git config user.name`." > outfile
        print "Normalize to a folder-safe slug: lowercase, replace spaces with hyphens, strip non-alphanumeric/hyphen chars.\n" > outfile
        print "Read and execute the instructions from the **first file that exists**:" > outfile
        print "1. `.devspark.work/{git-user}/commands/devspark." name ".md` (personalized override)" > outfile
        print "2. `.devspark.work/commands/devspark." name ".md` (team customization)" > outfile
        print "3. `.devspark/defaults/commands/devspark." name ".md` (stock default)\n" > outfile
        print "Where `{git-user}` is the normalized slug from step above.\n" > outfile
        print "## User Input\n\n```text\n" arg_format "\n```\n\nPass the user input above to the resolved prompt." > outfile
      }
      close(outfile)
    }
  ' templates/commands/*.md
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

build_variant() {
  local agent=$1 script=$2
  local base_dir="$GENRELEASES_DIR/sdd-${agent}-package-${script}"
  echo "Building $agent ($script) package..."
  mkdir -p "$base_dir"
  
  # Framework files go into .devspark/ (removable installation)
  DEVSPARK_DIR="$base_dir/.devspark"
  mkdir -p "$DEVSPARK_DIR"

  # Constitution is user-owned and never included in release packages.
  # Users create it via /devspark-constitution or /devspark-discover-constitution.
  
  # ADR-001: Always copy both script sets regardless of build variant.
  # The sh|ps variant only controls which {SCRIPT} path gets baked into command files.
  if [[ -d scripts ]]; then
    mkdir -p "$DEVSPARK_DIR/scripts"
    [[ -d scripts/bash ]] && { cp -r scripts/bash "$DEVSPARK_DIR/scripts/"; echo "Copied scripts/bash -> .devspark/scripts"; }
    [[ -d scripts/powershell ]] && { cp -r scripts/powershell "$DEVSPARK_DIR/scripts/"; echo "Copied scripts/powershell -> .devspark/scripts"; }
    find scripts -maxdepth 1 -type f -exec cp {} "$DEVSPARK_DIR/scripts/" \; 2>/dev/null || true
  fi
  
  [[ -d templates ]] && {
    copy_relative_files templates "$DEVSPARK_DIR" -type f -not -path "templates/commands/*" -not -path "templates/consumer-skills/*" -not -name "vscode-settings.json"
    echo "Copied templates -> .devspark/templates"
  }
  
  # Generate canonical command prompts in .devspark/defaults/commands/ (stock, upgrade-safe)
  # Team customizations live in .devspark.work/commands/ and are never overwritten.
  # Cached per script variant so multiple agents share one canonical generation run.
  local canonical_cache="$GENRELEASES_DIR/.canonical-cache-$script"
  if [[ ! -d "$canonical_cache" ]]; then
    generate_canonical_commands "$canonical_cache" "$script"
  fi
  mkdir -p "$DEVSPARK_DIR/defaults/commands"
  cp "$canonical_cache"/* "$DEVSPARK_DIR/defaults/commands/"
  echo "Generated canonical commands -> .devspark/defaults/commands"

  # Native Agent Skills (Copilot) are copied byte-identically from the committed consumer skills;
  # every other agent gets thin hyphenated entry points that resolve developer > team > default.
  local commands_dir extension arg_format skills_dir
  skills_dir=$(get_agent_release_field "$agent" skills_dir)

  if [[ -n $skills_dir ]]; then
    copy_relative_files templates/consumer-skills "$base_dir/$skills_dir" -type f -name SKILL.md
    echo "Copied consumer skills -> $skills_dir"
  else
    commands_dir=$(get_agent_release_field "$agent" commands_dir)
    extension=$(get_agent_release_field "$agent" extension)
    arg_format=$(get_agent_release_field "$agent" arg_format)

    if [[ -z $commands_dir || -z $extension || -z $arg_format ]]; then
      echo "Incomplete release metadata for agent '$agent' (commands_dir='${commands_dir:-}', extension='${extension:-}', arg_format='${arg_format:-}')" >&2
      exit 1
    fi

    generate_shims "$agent" "$extension" "$arg_format" "$base_dir/$commands_dir"
  fi
  copy_agent_support_files "$agent" "$base_dir"
  ( cd "$base_dir" && zip -r "../devspark-template-${agent}-${script}-${NEW_VERSION}.zip" . )
  echo "Created $GENRELEASES_DIR/devspark-template-${agent}-${script}-${NEW_VERSION}.zip"
}

# Determine agent list
# bash 3.2 compatible (macOS system bash lacks mapfile/readarray).
ALL_AGENTS=()
while IFS= read -r line; do
  [[ -n $line ]] && ALL_AGENTS+=("$line")
done < <(get_registered_agents)
ALL_SCRIPTS=(sh ps)

norm_list() {
  # convert comma+space separated -> line separated unique while preserving order of first occurrence
  tr ',\n' '  ' | awk '{for(i=1;i<=NF;i++){if(!seen[$i]++){printf((out?"\n":"") $i);out=1}}}END{printf("\n")}'
}

validate_subset() {
  # bash 3.2 compatible (macOS system bash lacks namerefs): pass allowed values as one space-separated string
  local type=$1; shift; local allowed_list=$1; shift; local items=("$@")
  local invalid=0
  for it in "${items[@]}"; do
    local found=0
    for a in $allowed_list; do [[ $it == "$a" ]] && { found=1; break; }; done
    if [[ $found -eq 0 ]]; then
      echo "Error: unknown $type '$it' (allowed: $allowed_list)" >&2
      invalid=1
    fi
  done
  return $invalid
}

if [[ -n ${AGENTS:-} ]]; then
  AGENT_LIST=()
  while IFS= read -r line; do
    [[ -n $line ]] && AGENT_LIST+=("$line")
  done < <(printf '%s' "$AGENTS" | norm_list)
  validate_subset agent "${ALL_AGENTS[*]}" "${AGENT_LIST[@]}" || exit 1
else
  AGENT_LIST=("${ALL_AGENTS[@]}")
fi

if [[ -n ${SCRIPTS:-} ]]; then
  SCRIPT_LIST=()
  while IFS= read -r line; do
    [[ -n $line ]] && SCRIPT_LIST+=("$line")
  done < <(printf '%s' "$SCRIPTS" | norm_list)
  validate_subset script "${ALL_SCRIPTS[*]}" "${SCRIPT_LIST[@]}" || exit 1
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

rm -rf "${GENRELEASES_DIR:?}"/.canonical-cache-*

echo "Archives in $GENRELEASES_DIR:"
ls -1 "$GENRELEASES_DIR"/devspark-template-*-"${NEW_VERSION}".zip

