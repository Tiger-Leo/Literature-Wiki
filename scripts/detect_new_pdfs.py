#!/usr/bin/env python3
"""Detect new/removed PDFs by comparing manifest against the source directory.

Usage:
  python scripts/detect_new_pdfs.py              # print report to stdout
  python scripts/detect_new_pdfs.py --update     # also update the manifest
  python scripts/detect_new_pdfs.py --json       # JSON output for programmatic use
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from link_pdfs import normalize_filename
from pipeline_utils import canonical_slug_from_filename

MANIFEST_PATH = REPO_ROOT / "raw_pdfs" / "pdf_sources.json"
PAPERS_DIR = REPO_ROOT / "raw_markdown" / "papers"


def load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        return {"source_dirs": [], "exclude_dirs": [], "pdfs": {}}
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        return json.load(f)


def scan_source_dir(source_dir: str, exclude_dirs: list[str]) -> set[str]:
    """Return set of absolute PDF paths in *source_dir* (excluding specified dirs)."""
    source = Path(source_dir)
    if not source.is_dir():
        return set()
    exclude_parts = {Path(d).resolve().parts for d in exclude_dirs}
    result = set()
    for pdf in source.rglob("*.pdf"):
        pdf_parts = pdf.resolve().parts
        if any(set(pdf_parts[:len(ep)]) == set(ep) for ep in exclude_parts if len(ep) <= len(pdf_parts)):
            continue
        result.add(str(pdf.resolve()))
    return result


def _entry_path(value: str | dict) -> str:
    """Extract path from either legacy (string) or current (dict) format."""
    return value if isinstance(value, str) else value["path"]


def detect(manifest: dict, source_dir: str, exclude_dirs: list[str]) -> dict:
    """Return {new: [...], removed: [...], unchanged: N}."""
    manifest_paths = {_entry_path(v) for v in manifest["pdfs"].values()}
    actual_paths = scan_source_dir(source_dir, exclude_dirs)

    new = sorted(actual_paths - manifest_paths)
    removed = sorted(manifest_paths - actual_paths)
    unchanged = len(manifest_paths & actual_paths)

    return {"new": new, "removed": removed, "unchanged": unchanged}


def format_report(result: dict) -> str:
    lines = []
    lines.append(f"Manifest entries: {result['unchanged'] + len(result['removed'])}")
    lines.append(f"Source directory PDFs: {result['unchanged'] + len(result['new'])}")
    lines.append(f"Unchanged: {result['unchanged']}")
    lines.append("")

    if result["new"]:
        lines.append(f"--- NEW ({len(result['new'])}) ---")
        for p in result["new"]:
            name = Path(p).name
            norm = normalize_filename(name)
            slug = canonical_slug_from_filename(norm)
            md_exists = (PAPERS_DIR / f"{slug}.md").exists()
            tag = "[has MD]" if md_exists else "[NEW]"
            lines.append(f"  {tag} {norm}")
            if md_exists:
                lines.append(f"       slug: {slug}")
    else:
        lines.append("--- NEW: 0 ---")

    if result["removed"]:
        lines.append(f"\n--- REMOVED ({len(result['removed'])}) ---")
        for p in result["removed"]:
            name = Path(p).name
            lines.append(f"  {name}")
    else:
        lines.append("\n--- REMOVED: 0 ---")

    return "\n".join(lines)


def update_manifest(manifest: dict, new_pdfs: list[str]) -> int:
    """Add new PDFs to the manifest and write it back. Returns count added."""
    added = 0
    for pdf_path in new_pdfs:
        name = Path(pdf_path).name
        norm = normalize_filename(name)
        if norm in manifest["pdfs"]:
            # Collision — keep existing
            continue
        slug = canonical_slug_from_filename(norm)
        md_exists = (PAPERS_DIR / f"{slug}.md").exists()
        manifest["pdfs"][norm] = {
            "path": pdf_path,
            "slug": slug,
            "converted": md_exists,
        }
        added += 1

    if added:
        # Sort: Chinese (pinyin) first, English alphabetical after
        from pipeline_utils import manifest_sort_key
        manifest["pdfs"] = dict(
            sorted(manifest["pdfs"].items(), key=lambda kv: manifest_sort_key(kv[0]))
        )
        with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
            f.write("\n")
    return added


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--update", action="store_true", help="Add new PDFs to manifest")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    manifest = load_manifest()
    source_dir = manifest.get("source_dirs", [None])[0]
    if not source_dir:
        print("ERROR: no source_dirs in manifest", file=sys.stderr)
        return 1

    exclude_dirs = manifest.get("exclude_dirs", [])
    result = detect(manifest, source_dir, exclude_dirs)

    if args.json:
        print(json.dumps({
            "unchanged": result["unchanged"],
            "new_count": len(result["new"]),
            "removed_count": len(result["removed"]),
            "new": result["new"],
            "removed": result["removed"],
        }, indent=2, ensure_ascii=False))
    else:
        print(format_report(result))

    if args.update and result["new"]:
        added = update_manifest(manifest, result["new"])
        print(f"\nAdded {added} new entries to manifest.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
