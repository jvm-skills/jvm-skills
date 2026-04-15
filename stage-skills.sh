#!/usr/bin/env bash
#
# Stage local skills into the SkillsJars packaging dir.
#
# Reads skills/<category>/*.yaml in the repo, keeps entries where
# `repo: jvm-skills/jvm-skills`, resolves `skill_path`, and copies each
# source skill directory to <staging>/<skill-name>/.
#
# Usage: stage-skills.sh <repo-root> <staging-dir>

set -euo pipefail

REPO_ROOT="${1:?repo root required}"
STAGING_DIR="${2:?staging dir required}"
OWNER_REPO="jvm-skills/jvm-skills"

rm -rf "$STAGING_DIR"
mkdir -p "$STAGING_DIR"

shopt -s nullglob
yaml_files=( "$REPO_ROOT"/skills/*/*.yaml "$REPO_ROOT"/skills/*/*.yml )
shopt -u nullglob

staged=0
for yaml in "${yaml_files[@]}"; do
    if ! grep -Eq "^repo:[[:space:]]*${OWNER_REPO}[[:space:]]*$" "$yaml"; then
        continue
    fi

    # Extract skill_path value, stripping quotes and whitespace.
    skill_path="$(awk -F: '/^skill_path:/ {
        sub(/^[^:]*:[[:space:]]*/, "", $0);
        gsub(/^["'\''[:space:]]+|["'\''[:space:]]+$/, "", $0);
        print; exit
    }' "$yaml")"

    if [[ -z "$skill_path" ]]; then
        echo "SKIP $(basename "$yaml"): no skill_path" >&2
        continue
    fi

    src_dir="$REPO_ROOT/$(dirname "$skill_path")"
    if [[ ! -f "$src_dir/SKILL.md" ]]; then
        echo "SKIP $(basename "$yaml"): $src_dir/SKILL.md not found" >&2
        continue
    fi

    skill_name="$(basename "$src_dir")"
    dest_dir="$STAGING_DIR/$skill_name"
    mkdir -p "$dest_dir"
    cp -R "$src_dir"/. "$dest_dir"/
    echo "staged $skill_name ($(basename "$yaml"))"
    staged=$((staged + 1))
done

echo "Staged $staged skill(s) to $STAGING_DIR"
if [[ "$staged" -eq 0 ]]; then
    echo "ERROR: no skills staged" >&2
    exit 1
fi
