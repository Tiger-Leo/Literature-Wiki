#!/usr/bin/env python3
"""Validate YAML frontmatter blocks in markdown files."""

from __future__ import annotations

import argparse
from pathlib import Path

from pipeline_utils import REPO_ROOT


# Aligned with wiki/schema/frontmatter-schema.md
SOURCE_REQUIRED = [
    "title",
    "authors",
    "year",
    "slug",
    "raw_markdown",
    "status",
]

GROUP_REQUIRED = [
    "title",
    "type",
    "status",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", default=[str(REPO_ROOT / "wiki")])
    return parser


def parse_frontmatter(text: str) -> tuple[dict[str, object] | None, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, text
    frontmatter_lines = []
    for idx, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            body = "\n".join(lines[idx + 1 :])
            return parse_yamlish(frontmatter_lines), body
        frontmatter_lines.append(line)
    return None, text


def parse_yamlish(lines: list[str]) -> dict[str, object]:
    data: dict[str, object] = {}
    current_key: str | None = None
    for raw_line in lines:
        line = raw_line.rstrip()
        if not line.strip():
            continue
        if line.startswith("  - ") and current_key:
            data.setdefault(current_key, [])
            if isinstance(data[current_key], list):
                data[current_key].append(line[4:].strip())
            continue
        if ": " in line:
            key, value = line.split(": ", 1)
            current_key = key.strip()
            data[current_key] = value.strip()
        elif line.endswith(":"):
            current_key = line[:-1].strip()
            data[current_key] = []
    return data


def required_fields(path: Path) -> list[str]:
    if path.name in {"_index.md", "log.md"}:
        return []
    if "schema" in path.parts or "templates" in path.parts:
        return []
    if "sources" in path.parts:
        return SOURCE_REQUIRED
    if path.name == "overview.md" or "synthesis" in path.parts or "concepts" in path.parts or "mechanisms" in path.parts or "methods" in path.parts or "measures" in path.parts or "debates" in path.parts:
        return GROUP_REQUIRED
    return []


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    errors = []
    for root in args.paths:
        for md in Path(root).rglob("*.md"):
            text = md.read_text(encoding="utf-8", errors="replace")
            frontmatter, _ = parse_frontmatter(text)
            req = required_fields(md)
            if req and frontmatter is None:
                errors.append(f"{md}: missing frontmatter")
                continue
            if req:
                for field in req:
                    value = frontmatter.get(field) if frontmatter else None
                    if value in (None, "", []):
                        errors.append(f"{md}: missing required field `{field}`")
    if errors:
        for error in errors:
            print(error)
        return 1
    print("Frontmatter validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
