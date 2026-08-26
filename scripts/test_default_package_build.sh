#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
skill_file="$root_dir/SKILL.md"
skill_name="$(sed -n 's/^name: *//p' "$skill_file" | head -n 1)"

if [[ -z "$skill_name" ]]; then
  echo "ERROR: Could not read the skill name from $skill_file" >&2
  exit 1
fi

python3 "$root_dir/scripts/validate_skill.py" --repository "$root_dir"
bash "$root_dir/scripts/build_package.sh"
python3 "$root_dir/scripts/validate_skill.py" "$root_dir/dist/$skill_name"

echo "Default package-build regression check passed: dist/$skill_name"
