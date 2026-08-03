#!/usr/bin/env python3
"""Batch-convert the first N unconverted PDFs from the manifest via MinerU.

Usage:
  python scripts/batch_convert.py [N] [--language ch|en]

Examples:
  python scripts/batch_convert.py          # convert first 20 unconverted PDFs (default language=ch)
  python scripts/batch_convert.py 5        # convert first 5
  python scripts/batch_convert.py 10 --language en  # 10 PDFs, English
"""
import argparse, json, os, subprocess, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "raw_pdfs" / "pdf_sources.json"
CONVERTER = REPO_ROOT / "scripts" / "convert_pdf_to_markdown.py"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from pipeline_utils import normalize_manifest_entry


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("n", nargs="?", type=int, default=20, help="Number of PDFs to convert (default: 20)")
    parser.add_argument("--language", default="ch", help="Document language for MinerU: ch (default) or en")
    parser.add_argument(
        "--only", default="",
        help="Only convert these doc types (comma-separated). --only and --skip are mutually exclusive.",
    )
    parser.add_argument(
        "--skip", default="",
        help="Skip these doc types (comma-separated): dissertation, book, book-chapter. --only takes precedence.",
    )
    args = parser.parse_args()

    N = args.n
    language = args.language
    only_types = {t.strip() for t in args.only.split(",") if t.strip()}
    skip_types = {t.strip() for t in args.skip.split(",") if t.strip()}

    with open(MANIFEST_PATH, encoding="utf-8") as f:
        manifest = json.load(f)

    # Collect first N unconverted entries, applying type filters
    todo = []
    for name, info in manifest["pdfs"].items():
        if isinstance(info, dict) and not info.get("converted"):
            doc_type = info.get("type", "journal-article")
            if only_types and doc_type not in only_types:
                continue
            if not only_types and skip_types and doc_type in skip_types:
                continue
            todo.append((name, info))
        if len(todo) >= N:
            break

    if not todo:
        print("No unconverted PDFs found in manifest (after filtering).")
        return 0

    # Sort by page count ascending (thin papers first — faster to convert, quicker feedback)
    todo.sort(key=lambda x: x[1].get("pages", 0))

    if only_types:
        filter_msg = f", only: {','.join(sorted(only_types))}"
    elif skip_types:
        filter_msg = f", skipping: {','.join(sorted(skip_types))}"
    else:
        filter_msg = ""
    print(f"Converting {len(todo)} PDFs via MinerU (language={language}{filter_msg})...\n")

    success = 0
    fail = 0
    for i, (name, info) in enumerate(todo, 1):
        real_path = info["path"]
        slug = info["slug"]
        pages = info.get("pages", "?")
        doc_type = info.get("type", "?")
        print(f"[{i}/{len(todo)}] [{doc_type}] {slug}  ({pages} pp.)")
        print(f"       file: {Path(real_path).name[:70]}")

        # Skip if already converted (check filesystem directly)
        md_path = REPO_ROOT / "raw_markdown" / "papers" / f"{slug}.md"
        if md_path.exists():
            print(f"       SKIP — .md already exists, marking converted")
            manifest["pdfs"][name]["converted"] = True
            success += 1
            continue

        # Skip files with 0 pages (missing or unreadable)
        if pages == 0:
            print(f"       SKIP — 0 pages (missing or unreadable file)")
            fail += 1
            continue

        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        result = subprocess.run(
            ["python", str(CONVERTER), name, "--converter", "mineru", "--language", language, "--overwrite"],
            capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=600,
            encoding="utf-8", errors="replace", env=env,
        )

        if result.returncode == 0 and md_path.exists():
            print(f"       OK ({md_path.stat().st_size:,} bytes)")
            manifest["pdfs"][name]["converted"] = True
            success += 1
        else:
            print(f"       FAILED")
            if result.stderr:
                print(f"       stderr: {result.stderr.strip()[:200]}")
            fail += 1

        print()

    # Normalise all entries to canonical field order before saving
    manifest["pdfs"] = {
        name: normalize_manifest_entry(e)
        for name, e in manifest["pdfs"].items()
    }

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Done. Success: {success}, Failed: {fail}")
    print(f"Manifest updated ({MANIFEST_PATH}).")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
