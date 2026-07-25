#!/usr/bin/env python3
"""Convert PDF papers into canonical raw_markdown outputs using markitdown.

Output conventions:
- `raw_markdown/papers/<canonical-slug>.md`
- `raw_markdown/metadata/<canonical-slug>.json`
- canonical slugs are lowercase kebab-case and derived from the filename
"""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path

from pipeline_utils import (
    REPO_ROOT,
    canonical_slug_from_filename,
    count_markdown_headings,
    count_words,
    parse_pdf_filename,
    relative_to_repo,
    sha256_file,
)


def run_markitdown(pdf_path: Path, md_path: Path) -> tuple[list[str], subprocess.CompletedProcess[str], str]:
    cmd = ["markitdown", str(pdf_path), "-o", str(md_path)]
    completed = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return cmd, completed, "markitdown"


def run_pdftotext_fallback(pdf_path: Path, md_path: Path) -> tuple[list[str], subprocess.CompletedProcess[str], str]:
    cmd = ["pdftotext", "-layout", str(pdf_path), "-"]
    completed = subprocess.run(cmd, capture_output=True, text=True, check=True)
    md_path.write_text(completed.stdout, encoding="utf-8")
    return cmd, completed, "pdftotext-fallback"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdfs", nargs="+", help="PDF files to convert")
    parser.add_argument("--output-root", default=str(REPO_ROOT / "raw_markdown"), help="raw_markdown root")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing outputs")
    return parser


def convert_one(pdf_path: Path, output_root: Path, overwrite: bool) -> dict[str, object]:
    slug = canonical_slug_from_filename(pdf_path)
    papers_dir = output_root / "papers"
    metadata_dir = output_root / "metadata"
    papers_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)

    md_path = papers_dir / f"{slug}.md"
    meta_path = metadata_dir / f"{slug}.json"

    if md_path.exists() and not overwrite:
        raise FileExistsError(f"{md_path} already exists; use --overwrite to replace it")

    conversion_notes: list[str] = []
    try:
        cmd, completed, conversion_tool = run_markitdown(pdf_path, md_path)
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        if "MediaBox" not in stderr:
            raise
        conversion_notes.append("markitdown failed with MediaBox error; used pdftotext fallback")
        cmd, completed, conversion_tool = run_pdftotext_fallback(pdf_path, md_path)

    markdown_text = md_path.read_text(encoding="utf-8", errors="replace")
    parsed = parse_pdf_filename(pdf_path)
    source_bytes = pdf_path.stat().st_size

    metadata = {
        "canonical_slug": slug,
        "source_pdf": relative_to_repo(pdf_path),
        "source_pdf_name": pdf_path.name,
        "markdown_file": relative_to_repo(md_path),
        "metadata_file": relative_to_repo(meta_path),
        "conversion_tool": conversion_tool,
        "conversion_command": cmd,
        "converted_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source_sha256": sha256_file(pdf_path),
        "source_size_bytes": source_bytes,
        "markdown_size_bytes": md_path.stat().st_size,
        "line_count": len(markdown_text.splitlines()),
        "heading_count": count_markdown_headings(markdown_text),
        "word_count": count_words(markdown_text),
        "title_guess": parsed["title"],
        "authors_guess": parsed["authors"],
        "year_guess": parsed["year"],
        "conversion_notes": conversion_notes,
        "markitdown_stdout": completed.stdout.strip(),
        "markitdown_stderr": completed.stderr.strip(),
    }
    meta_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return metadata


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    output_root = Path(args.output_root)
    results = []
    for pdf in args.pdfs:
        pdf_path = Path(pdf)
        results.append(convert_one(pdf_path, output_root, args.overwrite))
    for result in results:
        print(f"{result['canonical_slug']}\t{result['markdown_file']}\t{result['metadata_file']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
