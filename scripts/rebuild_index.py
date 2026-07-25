#!/usr/bin/env python3
"""Rebuild simple directory router previews from the repository tree.

By default this prints a preview. Use --write to create missing `_index.md`
files, and `--overwrite-existing` only when you explicitly want to replace an
existing router.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from pipeline_utils import REPO_ROOT


SKIP_DIRS = {".git", ".claude", "__pycache__", "agent_tasks", "raw_pdfs"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(REPO_ROOT), help="Repository root to scan")
    parser.add_argument("--write", action="store_true", help="Write missing _index.md files in place")
    parser.add_argument(
        "--overwrite-existing",
        action="store_true",
        help="Also overwrite existing _index.md files (unsafe for curated routers)",
    )
    return parser


def render_index(directory: Path) -> str:
    entries = []
    for child in sorted(directory.iterdir()):
        if child.name.startswith(".") or child.name == "_index.md" or child.name in SKIP_DIRS:
            continue
        if child.is_dir():
            entries.append(f"- `{child.name}/`")
        elif child.suffix == ".md":
            entries.append(f"- `[[{child.stem}]]`")
    body = "\n".join(entries) if entries else "- (empty)"
    return f"# {directory.name} Router\n\n{body}\n"


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    root = Path(args.root)
    directories = [root]
    for branch in (root / "raw_markdown", root / "wiki"):
        if branch.exists():
            directories.extend(
                sorted(
                    path
                    for path in branch.rglob("*")
                    if path.is_dir() and not any(part in SKIP_DIRS or part.startswith(".") for part in path.parts)
                )
            )
    seen = set()
    for directory in directories:
        if directory in seen:
            continue
        seen.add(directory)
        index_path = directory / "_index.md"
        rendered = render_index(directory)
        if args.write:
            if index_path.exists() and not args.overwrite_existing:
                print(f"SKIP {index_path} (already exists; use --overwrite-existing to replace)")
                continue
            index_path.write_text(rendered, encoding="utf-8")
        else:
            print(f"--- {index_path}")
            print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
