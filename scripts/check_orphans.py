#!/usr/bin/env python3
"""Find orphan wiki pages — pages not linked from any other page.

An orphan page is a wiki page whose stem / relative path appears in no
wikilink and no local markdown link across the entire repository.

_index.md router files and wiki/templates/* are excluded from the
orphan check because they are structural, not content pages.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from pipeline_utils import REPO_ROOT


WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
FENCED_CODE_RE = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`]*`")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "roots",
        nargs="*",
        default=[str(REPO_ROOT / "wiki")],
        help="Directories to scan for orphan pages (default: wiki/).",
    )
    parser.add_argument(
        "--all-roots",
        action="store_true",
        help="Also scan raw_markdown/ for outbound links.",
    )
    return parser


def strip_code(text: str) -> str:
    text = FENCED_CODE_RE.sub("", text)
    return INLINE_CODE_RE.sub("", text)


def collect_referenced_targets(search_roots: list[Path]) -> set[str]:
    """Return every wikilink page name and local link target mentioned."""
    targets: set[str] = set()
    for root in search_roots:
        for md in root.rglob("*.md"):
            text = strip_code(md.read_text(encoding="utf-8", errors="replace"))
            for raw in WIKILINK_RE.findall(text):
                page = raw.split("#", 1)[0].split("|", 1)[0].strip()
                if page:
                    targets.add(page)
                    targets.add(page.lower())
            for raw in MD_LINK_RE.findall(text):
                t = raw.split("#", 1)[0].strip()
                if t and not t.startswith(("http://", "https://")):
                    stem = Path(t).stem
                    targets.add(stem)
                    targets.add(stem.lower())
                    # Also store the relative path without extension
                    targets.add(t)
    return targets


def is_structural(path: Path) -> bool:
    """True for _index.md files and wiki/templates/* pages."""
    if path.name == "_index.md":
        return True
    try:
        rel = path.relative_to(REPO_ROOT)
        parts = rel.parts
        if len(parts) >= 2 and parts[0] == "wiki" and parts[1] == "templates":
            return True
    except ValueError:
        pass
    return False


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    scan_roots = [Path(r).resolve() for r in args.roots]
    link_roots = list(scan_roots)
    if args.all_roots:
        link_roots.append(REPO_ROOT / "raw_markdown")

    referenced = collect_referenced_targets(link_roots)

    orphans: list[Path] = []
    for root in scan_roots:
        for md in sorted(root.rglob("*.md")):
            if is_structural(md):
                continue
            stem = md.stem
            rel = md.relative_to(REPO_ROOT).with_suffix("").as_posix()
            rel_parts = rel.split("/")
            # Build a set of all possible matching identifiers for this page
            identifiers: set[str] = {stem, stem.lower(), rel, md.name, md.name.lower()}
            # Also add every suffix sub-path, e.g. "schema/naming-rules" for "wiki/schema/naming-rules"
            for i in range(len(rel_parts)):
                identifiers.add("/".join(rel_parts[i:]))
                identifiers.add("/".join(rel_parts[i:]).lower())
            if identifiers & referenced:
                continue
            orphans.append(md)

    if orphans:
        print(f"Found {len(orphans)} orphan page(s):")
        for p in orphans:
            print(f"  {p.relative_to(REPO_ROOT)}")
        return 1

    print("No orphan pages found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
