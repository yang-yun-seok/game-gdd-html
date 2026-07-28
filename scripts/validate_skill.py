#!/usr/bin/env python3
"""Validate the repository's SKILL.md without third-party dependencies."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


MAX_SKILL_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024
ALLOWED_PROPERTIES = {
    "name",
    "description",
    "license",
    "allowed-tools",
    "metadata",
}


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _parse_simple_frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", text, re.DOTALL)
    if not match:
        raise ValueError("SKILL.md must start with valid YAML frontmatter")

    fields: dict[str, str] = {}
    for line_number, raw_line in enumerate(match.group(1).splitlines(), start=2):
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if raw_line[:1].isspace():
            raise ValueError(
                f"line {line_number}: nested YAML is not supported by this validator"
            )
        if ":" not in raw_line:
            raise ValueError(f"line {line_number}: expected 'key: value'")

        key, value = raw_line.split(":", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"line {line_number}: frontmatter key is empty")
        if key in fields:
            raise ValueError(f"line {line_number}: duplicate frontmatter key '{key}'")
        fields[key] = _unquote(value)

    return fields


def validate_skill(skill_path: Path) -> list[str]:
    errors: list[str] = []
    skill_md = skill_path / "SKILL.md" if skill_path.is_dir() else skill_path

    if not skill_md.is_file():
        return [f"SKILL.md not found: {skill_md}"]

    try:
        text = skill_md.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return ["SKILL.md must be valid UTF-8"]

    try:
        frontmatter = _parse_simple_frontmatter(text)
    except ValueError as exc:
        return [str(exc)]

    unexpected = sorted(set(frontmatter) - ALLOWED_PROPERTIES)
    if unexpected:
        errors.append(
            "unexpected frontmatter keys: "
            + ", ".join(unexpected)
            + "; allowed: "
            + ", ".join(sorted(ALLOWED_PROPERTIES))
        )

    name = frontmatter.get("name", "").strip()
    description = frontmatter.get("description", "").strip()

    if not name:
        errors.append("frontmatter 'name' is required")
    elif not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
        errors.append(
            "frontmatter 'name' must use lowercase hyphen-case without "
            "leading, trailing, or consecutive hyphens"
        )
    elif len(name) > MAX_SKILL_NAME_LENGTH:
        errors.append(
            f"frontmatter 'name' exceeds {MAX_SKILL_NAME_LENGTH} characters"
        )

    if not description:
        errors.append("frontmatter 'description' is required")
    else:
        if "<" in description or ">" in description:
            errors.append("frontmatter 'description' cannot contain angle brackets")
        if len(description) > MAX_DESCRIPTION_LENGTH:
            errors.append(
                f"frontmatter 'description' exceeds "
                f"{MAX_DESCRIPTION_LENGTH} characters"
            )

    license_name = frontmatter.get("license", "").strip()
    if license_name and license_name != "MIT":
        errors.append("frontmatter 'license' must match the repository MIT license")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the game-gdd-html SKILL.md manifest."
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        type=Path,
        help="Skill directory or SKILL.md path (default: current directory)",
    )
    args = parser.parse_args()

    errors = validate_skill(args.path.resolve())
    if errors:
        for error in errors:
            print(f"[ERROR] {error}", file=sys.stderr)
        return 1

    print("[OK] SKILL.md manifest is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
