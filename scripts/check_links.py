#!/usr/bin/env python3
"""Check markdown links and wikilinks against files in the repository."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from pipeline_utils import REPO_ROOT


WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
FENCED_CODE_RE = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`]*`")
LOCAL_FILE_SUFFIXES = (".md", ".pdf", ".json", ".png", ".jpg", ".jpeg", ".webp", ".svg")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("roots", nargs="*", default=[str(REPO_ROOT / "wiki"), str(REPO_ROOT / "raw_markdown")])
    return parser


def known_files() -> set[str]:
    names = set()
    for path in REPO_ROOT.rglob("*.md"):
        names.add(path.name)
        names.add(path.stem)
        names.add(path.relative_to(REPO_ROOT).with_suffix("").as_posix())
    return names


def resolve_wikilink(target: str) -> Path | None:
    target = target.split("#", 1)[0].split("|", 1)[0].strip()
    if not target:
        return None
    candidates = []
    for path in REPO_ROOT.rglob("*.md"):
        rel = path.relative_to(REPO_ROOT).with_suffix("")
        if (
            rel.as_posix() == target
            or rel.as_posix().endswith("/" + target)
            or path.stem == target
            or path.name == target
        ):
            candidates.append(path)
    return candidates[0] if candidates else None


def resolve_link(base: Path, target: str) -> Path:
    target = target.split("#", 1)[0].split("|", 1)[0].strip()
    return (base / target).resolve()


def strip_code(text: str) -> str:
    text = FENCED_CODE_RE.sub("", text)
    return INLINE_CODE_RE.sub("", text)


def should_check_markdown_target(target: str) -> bool:
    target = target.split("#", 1)[0].split("|", 1)[0].strip()
    if not target or target.startswith("#"):
        return False
    if target.startswith(("http://", "https://", "mailto:", "cid:", "data:")):
        return False
    if target.startswith(".") or "/" in target:
        return True
    return target.endswith(LOCAL_FILE_SUFFIXES)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    known = known_files()
    problems = []
    for root in args.roots:
        for md in Path(root).rglob("*.md"):
            # Skip wiki/templates — placeholder wikilinks are intentional
            try:
                rel_parts = md.resolve().relative_to(REPO_ROOT).parts
                if len(rel_parts) >= 2 and rel_parts[0] == "wiki" and rel_parts[1] == "templates":
                    continue
            except ValueError:
                pass
            text = strip_code(md.read_text(encoding="utf-8", errors="replace"))
            for target in WIKILINK_RE.findall(text):
                page = target.split("#", 1)[0].split("|", 1)[0].strip()
                if page and resolve_wikilink(page) is None and page not in known:
                    problems.append(f"{md}: missing wikilink target [[{target}]]")
            for target in MD_LINK_RE.findall(text):
                if not should_check_markdown_target(target):
                    continue
                resolved = resolve_link(md.parent, target)
                if not resolved.exists():
                    problems.append(f"{md}: missing markdown link ({target})")
    if problems:
        for problem in problems:
            print(problem)
        return 1
    print("No broken links found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
