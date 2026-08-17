#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
skill_file="$root_dir/SKILL.md"

if [[ ! -f "$skill_file" ]]; then
  echo "ERROR: SKILL.md is missing at $skill_file" >&2
  exit 1
fi

skill_name="$(sed -n 's/^name: *//p' "$skill_file" | head -n 1 | tr -d '"'\''')"
if [[ -z "$skill_name" ]]; then
  echo "ERROR: Could not read the skill name from SKILL.md" >&2
  exit 1
fi

package_dir="$root_dir/dist/$skill_name"
rm -rf "$package_dir"
mkdir -p "$package_dir"
cp "$skill_file" "$package_dir/SKILL.md"

if [[ -d "$root_dir/agents" ]]; then
  cp -a "$root_dir/agents" "$package_dir/agents"
fi

resources=("$@")
if [[ ${#resources[@]} -eq 0 ]]; then
  resources=(assets references scripts)
fi

for resource in "${resources[@]}"; do
  case "$resource" in
    assets|references|scripts)
      if [[ -d "$root_dir/$resource" ]]; then
        cp -a "$root_dir/$resource" "$package_dir/$resource"
      fi
      ;;
    *)
      echo "ERROR: Unsupported resource '$resource'. Use assets, references, or scripts." >&2
      exit 1
      ;;
  esac
done

printf 'Built deployable package: %s\n' "$package_dir"
