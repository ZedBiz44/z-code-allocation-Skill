#!/usr/bin/env python3
"""Validate the shared cross-platform structure of an Agent Skill."""

from __future__ import annotations

import re
import sys
from pathlib import Path


NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def fail(message: str, errors: list[str]) -> None:
    errors.append(message)


def parse_frontmatter(text: str, errors: list[str]) -> tuple[dict[str, str], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        fail("SKILL.md must start with YAML frontmatter.", errors)
        return {}, text
    try:
        end = lines.index("---", 1)
    except ValueError:
        fail("SKILL.md frontmatter is not closed.", errors)
        return {}, text

    values: dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip():
            continue
        if ":" not in line:
            fail(f"Unsupported frontmatter line: {line}", errors)
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if not key or not value:
            fail(f"Frontmatter key and value are required: {line}", errors)
        values[key] = value
    return values, "\n".join(lines[end + 1 :])


def main() -> int:
    args = sys.argv[1:]
    repository_mode = False
    if args and args[0] == "--repository":
        repository_mode = True
        args = args[1:]
    if len(args) > 1:
        print("Usage: validate_skill.py [--repository] [skill-directory]")
        return 2

    root = Path(args[0] if args else ".").resolve()
    skill_file = root / "SKILL.md"
    errors: list[str] = []

    if not skill_file.is_file():
        print(f"ERROR: {skill_file} does not exist.")
        return 1

    text = skill_file.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(text, errors)

    expected_keys = {"name", "description"}
    if set(frontmatter) != expected_keys:
        fail(
            "Shared frontmatter must contain exactly name and description; "
            f"found: {', '.join(sorted(frontmatter)) or 'none'}.",
            errors,
        )

    name = frontmatter.get("name", "")
    description = frontmatter.get("description", "")

    if not NAME_RE.fullmatch(name):
        fail("name must use lowercase letters, numbers, and single hyphens.", errors)
    if len(name) > 64:
        fail("name must not exceed 64 characters.", errors)
    if not repository_mode and root.name != name:
        fail(f"folder name '{root.name}' must match name '{name}'.", errors)
    if not description:
        fail("description is required.", errors)
    if len(description) > 160:
        fail("description must not exceed 160 characters for shared OpenClaw compatibility.", errors)
    if "TODO" in text:
        fail("SKILL.md contains a TODO placeholder.", errors)
    if len(text.splitlines()) > 500:
        fail("SKILL.md must stay under 500 lines.", errors)

    if repository_mode:
        readme_file = root / "README.md"
        if not readme_file.is_file():
            fail("README.md is required at the repository root.", errors)
        else:
            readme = readme_file.read_text(encoding="utf-8").strip()
            if not readme.startswith("# "):
                fail("README.md must begin with one H1 heading.", errors)
            if len(readme) < 200:
                fail("README.md is too short to document the skill responsibly.", errors)
            if readme.count("\n## ") < 3:
                fail("README.md must contain at least three H2 sections.", errors)
            if "SKILL.md" not in readme:
                fail("README.md must identify SKILL.md as the authoritative runtime guide.", errors)

    for target in LINK_RE.findall(body):
        if "://" in target or target.startswith("#"):
            continue
        path = (root / target.split("#", 1)[0]).resolve()
        if not path.exists():
            fail(f"Referenced file does not exist: {target}", errors)

    openai_yaml = root / "agents" / "openai.yaml"
    if openai_yaml.is_file():
        yaml_text = openai_yaml.read_text(encoding="utf-8")
        if f"${name}" not in yaml_text:
            fail(f"agents/openai.yaml default_prompt must mention ${name}.", errors)

    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Validation passed: {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
