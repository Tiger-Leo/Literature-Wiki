#!/usr/bin/env python3
"""Create symbolic links or a path manifest in raw_pdfs/ for PDFs in an external directory.

Does NOT move, copy, or rename the source files. Only reads the source directory
to discover PDFs.

Two modes:
  --mode symlink   Create Windows symlinks. Requires Developer Mode or admin.
  --mode manifest  Generate raw_pdfs/pdf_sources.json (a name→path map).
                   No special privileges needed. Converter scripts resolve
                   PDF paths through this manifest automatically.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path



REPO_ROOT = Path(__file__).resolve().parents[1]

# Re-use the slug function so --new-only can check for existing conversions
sys.path.insert(0, str(Path(__file__).resolve().parent))
from pipeline_utils import canonical_slug_from_filename, classify_doc_type, get_pdf_page_count, normalize_manifest_entry


def normalize_filename(original_name: str) -> str:
    """Convert a PDF filename to the project naming convention.

    Convention: Author and Author - YYYY - Paper Title.pdf
    (split on whitespace-dash-whitespace; the middle part is a 4-digit year)

    Handles two common source patterns:
      1. Underscore-delimited: Fedyk_Hodson_2022_Title.pdf → Fedyk Hodson - 2022 - Title.pdf
      2. Already dash-delimited but with non-ASCII: Author 等 - 2025 - Title.pdf → Author et al - 2025 - Title.pdf
    """
    # Split off extension
    if original_name.lower().endswith('.pdf'):
        stem = original_name[:-4]
    else:
        stem = original_name.rsplit('.', 1)[0] if '.' in original_name else original_name

    # NFKD normalize — decomposes accented Latin characters (e.g. í → i)
    # but preserves Chinese/CJK characters intact
    stem = unicodedata.normalize('NFKD', stem)

    # If the stem already uses the ' - ' convention (at least two separators), keep it
    if stem.count(' - ') >= 2:
        return stem.strip() + '.pdf'

    # Try the underscore pattern: find a 4-digit year between underscores
    m = re.search(r'_(\d{4})_', stem)
    if m:
        year = m.group(1)
        pos = m.start()
        authors = stem[:pos].replace('_', ' ')
        title = stem[pos + len(year) + 2:]  # after _YYYY_
        return f"{authors} - {year} - {title}.pdf"

    # Fallback: replace all underscores with spaces, no year separation attempted
    return stem.replace('_', ' ') + '.pdf'


def create_symlink(target: Path, link: Path) -> bool:
    """Create a symbolic link. Returns True on success, False on skip."""
    if link.exists() or link.is_symlink():
        print(f"  SKIP: {link.name}  (already exists)")
        return False
    os.symlink(target, link)
    print(f"  LINK: {link.name}")
    return True


MANIFEST_FILENAME = "pdf_sources.json"


def _is_excluded(pdf_path: Path, source_dir: Path, exclude_dirs: set[str]) -> bool:
    """Return True if *pdf_path* is under any excluded directory."""
    if not exclude_dirs:
        return False
    resolved = pdf_path.resolve()
    for excl in exclude_dirs:
        excl_path = Path(excl).resolve()
        try:
            if resolved.is_relative_to(excl_path):
                return True
        except (ValueError, OSError):
            # Different drives or invalid path — can't be excluded
            pass
    return False


def generate_manifest(
    source_dir: Path,
    manifest_path: Path,
    source_dirs: list[str],
    exclude_dirs: set[str] | None = None,
) -> dict:
    """Build or update a pdf_sources.json manifest from a source directory.

    Returns the complete manifest dict (old entries from other source dirs
    are preserved; entries from this source dir are refreshed).

    Directories in *exclude_dirs* are skipped during scanning.
    """
    if exclude_dirs is None:
        exclude_dirs = set()

    # Load existing manifest to preserve entries from other source dirs
    existing: dict[str, dict[str, str]] = {}
    if manifest_path.exists():
        try:
            existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, KeyError):
            existing = {}

    # Merge exclude_dirs from the existing manifest with those passed in
    all_excludes = set(exclude_dirs)
    for excl in existing.get("exclude_dirs", []):
        all_excludes.add(excl)

    # Helper: extract just the path from either old (string) or new (dict) format
    def _entry_path(value: str | dict) -> str:
        return value if isinstance(value, str) else value["path"]

    # Build fresh map for this source_dir (new object format)
    fresh: dict[str, dict] = {}
    source_dir_str = str(source_dir.resolve())
    scanned = 0
    skipped = 0
    for pdf_path in sorted(source_dir.rglob("*.pdf")):
        if _is_excluded(pdf_path, source_dir, all_excludes):
            skipped += 1
            continue
        scanned += 1
        normalized = normalize_filename(pdf_path.name)
        if normalized in fresh:
            print(f"  WARNING: duplicate normalized name '{normalized}' — "
                  f"keeping first: {fresh[normalized]['path']}")
            continue
        slug = canonical_slug_from_filename(normalized)
        pages = get_pdf_page_count(pdf_path)
        fresh[normalized] = {
            "path": str(pdf_path.resolve()),
            "slug": slug,
            "type": classify_doc_type(str(pdf_path), pages),
            "pages": pages,
            "converted": False,
        }

    if skipped:
        print(f"  Excluded {skipped} PDF(s) under excluded directories")

    # Merge: fresh entries from this source_dir, keep entries from elsewhere
    # Preserve existing dict entries and their converted status
    merged_pdfs: dict[str, dict] = {}
    for name, value in existing.get("pdfs", {}).items():
        if isinstance(value, str):
            # Legacy format — upgrade to object format
            pages = get_pdf_page_count(value)
            merged_pdfs[name] = {
                "path": value,
                "slug": canonical_slug_from_filename(name),
                "type": classify_doc_type(value, pages),
                "pages": pages,
                "converted": False,
            }
        else:
            merged_pdfs[name] = value

    # Remove entries that were previously from this source_dir (will be refreshed)
    for name, value in list(merged_pdfs.items()):
        if Path(_entry_path(value)).resolve().is_relative_to(source_dir.resolve()):
            del merged_pdfs[name]

    # Merge fresh entries — preserve converted status of any existing entry with same name
    for name, info in fresh.items():
        if name in merged_pdfs:
            # Keep the existing converted status
            info["converted"] = merged_pdfs[name].get("converted", False)
    merged_pdfs.update(fresh)

    # Normalize all entries to canonical field order (path, slug, pages, converted)
    merged_pdfs = {name: normalize_manifest_entry(entry) for name, entry in merged_pdfs.items()}

    # Rebuild source_dirs list
    all_source_dirs = set(existing.get("source_dirs", []))
    all_source_dirs.add(source_dir_str)

    return {
        "source_dirs": sorted(all_source_dirs),
        "exclude_dirs": sorted(all_excludes),
        "pdfs": merged_pdfs,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create symlinks or a path manifest for external PDFs."
    )
    parser.add_argument(
        "source_dir",
        help="Root directory to scan recursively for PDF files.",
    )
    parser.add_argument(
        "--mode",
        choices=["symlink", "manifest"],
        default="manifest",
        help="symlink = create OS symlinks (needs Developer Mode); "
             "manifest = generate pdf_sources.json (no privileges needed, default).",
    )
    parser.add_argument(
        "--link-dir",
        default=str(REPO_ROOT / "raw_pdfs"),
        help="Directory to create symlinks / manifest in (default: raw_pdfs/).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without writing anything.",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        dest="exclude_dirs",
        help="Directory path to exclude from scanning. Can be passed multiple "
             "times. Use to skip subdirectories you don't want to include.",
    )
    parser.add_argument(
        "--convert",
        action="store_true",
        help="After building the manifest, convert all (or --new-only) PDFs "
             "to markdown via MinerU.",
    )
    parser.add_argument(
        "--new-only",
        action="store_true",
        help="With --convert: skip PDFs that already have a corresponding .md "
             "file in raw_markdown/papers/.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    source_dir = Path(args.source_dir)
    if not source_dir.is_dir():
        print(f"ERROR: source directory not found: {source_dir}")
        return 1

    link_dir = Path(args.link_dir)
    link_dir.mkdir(parents=True, exist_ok=True)

    pdf_paths = sorted(source_dir.rglob("*.pdf"))
    print(f"Found {len(pdf_paths)} PDF(s) in {source_dir}")

    if args.mode == "manifest":
        return _run_manifest_mode(
            source_dir, link_dir, pdf_paths,
            dry_run=args.dry_run,
            do_convert=args.convert,
            new_only=args.new_only,
            exclude_dirs=set(args.exclude_dirs),
        )
    else:
        return _run_symlink_mode(link_dir, pdf_paths, args.dry_run)


def _run_manifest_mode(
    source_dir: Path,
    link_dir: Path,
    pdf_paths: list[Path],
    dry_run: bool = False,
    do_convert: bool = False,
    new_only: bool = False,
    exclude_dirs: set[str] | None = None,
) -> int:
    if exclude_dirs is None:
        exclude_dirs = set()
    manifest_path = link_dir / MANIFEST_FILENAME
    print(f"Manifest: {manifest_path}")
    if dry_run:
        print("[DRY RUN — no files will be written]\n")
    else:
        print()

    manifest = generate_manifest(
        source_dir, manifest_path,
        source_dirs=[str(source_dir.resolve())],
        exclude_dirs=exclude_dirs,
    )

    shown = 0
    for name, path in manifest["pdfs"].items():
        if Path(path).resolve().is_relative_to(source_dir.resolve()):
            if dry_run:
                print(f"  WOULD MAP: {name}")
                print(f"       → from: {path}")
            else:
                print(f"  MAP: {name}")
            shown += 1

    if not dry_run:
        # Sort: Chinese (pinyin) first, English alphabetical after
        from pipeline_utils import manifest_sort_key
        manifest["pdfs"] = dict(
            sorted(manifest["pdfs"].items(), key=lambda kv: manifest_sort_key(kv[0]))
        )
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"\nWrote {shown} entries to {manifest_path}")
    else:
        print(f"\nWould write {shown} entries to {manifest_path}")

    # --- Optional: convert PDFs via MinerU ---
    if do_convert:
        return _convert_from_manifest(manifest, link_dir, dry_run, new_only)

    if not do_convert and not dry_run:
        print("Converter scripts will now resolve PDF names through this manifest.")

    return 0


def _convert_from_manifest(
    manifest: dict, link_dir: Path, dry_run: bool, new_only: bool
) -> int:
    """Call convert_pdf_to_markdown.py for each entry in the manifest."""
    converter_script = REPO_ROOT / "scripts" / "convert_pdf_to_markdown.py"
    papers_dir = REPO_ROOT / "raw_markdown" / "papers"

    # Determine which entries to convert
    todo: list[tuple[str, str]] = []  # [(virtual_name, real_path), ...]
    skipped = 0

    for name, path in sorted(manifest["pdfs"].items()):
        slug = canonical_slug_from_filename(Path(name))
        md_exists = (papers_dir / f"{slug}.md").exists()

        if new_only and md_exists:
            skipped += 1
            continue

        todo.append((name, path))

    if skipped:
        print(f"\nSkipping {skipped} already-converted PDF(s) (--new-only).")
    if not todo:
        print("Nothing to convert.")
        return 0

    print(f"\n{'Would convert' if dry_run else 'Converting'} {len(todo)} PDF(s) via MinerU:")
    print()

    success = 0
    failures = 0

    for name, real_path in todo:
        if dry_run:
            slug = canonical_slug_from_filename(Path(name))
            print(f"  WOULD CONVERT: {name}")
            print(f"          → slug: {slug}")
            print(f"          → from: {real_path}")
            success += 1
            continue

        print(f"  [{success + failures + 1}/{len(todo)}] {name} ... ", end="", flush=True)
        result = subprocess.run(
            ["python", str(converter_script), name, "--converter", "mineru", "--overwrite"],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            print("OK")
            success += 1
        else:
            print("FAILED")
            print(f"       stderr: {result.stderr.strip()}")
            failures += 1

    print(f"\n{'Would convert' if dry_run else 'Converted'}: {success}  "
          f"Failed: {failures}  Skipped: {skipped}")

    return 0 if failures == 0 else 1


def _run_symlink_mode(
    link_dir: Path, pdf_paths: list[Path], dry_run: bool
) -> int:
    print(f"Link directory: {link_dir}")
    if dry_run:
        print("[DRY RUN — no symlinks will be created]\n")
    else:
        print()

    created = 0
    skipped = 0
    errors = 0

    for pdf_path in pdf_paths:
        normalized_name = normalize_filename(pdf_path.name)

        if dry_run:
            print(f"  WOULD LINK: {normalized_name}")
            print(f"       → from: {pdf_path}")
            created += 1
            continue

        link_path = link_dir / normalized_name
        target = pdf_path.resolve()

        try:
            if create_symlink(target, link_path):
                created += 1
            else:
                skipped += 1
        except OSError as exc:
            print(f"  ERROR: {normalized_name} — {exc}")
            errors += 1

    print(f"\n{'Would create' if dry_run else 'Created'}: {created}  "
          f"Skipped: {skipped}  Errors: {errors}")

    if errors > 0:
        print("\nTip: on Windows, symlink creation requires either:")
        print("  * Developer Mode (Settings > Privacy & Security > For developers)")
        print("  * Administrator privileges")
        return 1

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
