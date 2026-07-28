#!/usr/bin/env python3
"""Convert PDF papers into canonical raw_markdown outputs.

Converters:
  markitdown  – fast, local; good for simple text PDFs (default)
  mineru      – cloud API; high-quality for formulas, tables, complex layouts

Output conventions:
- `raw_markdown/papers/<canonical-slug>.md`
- `raw_markdown/metadata/<canonical-slug>.json`
- canonical slugs are lowercase kebab-case and derived from the filename
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

from pipeline_utils import (
    REPO_ROOT,
    canonical_slug_from_filename,
    count_markdown_headings,
    count_words,
    normalize_manifest_entry,
    parse_pdf_filename,
    relative_to_repo,
    resolve_pdf_path,
    sha256_file,
)

# Path to the MinerU converter script (installed as a Claude Code skill)
_MINERU_SCRIPT = Path.home() / ".claude" / "skills" / "mineru-pdf-converter" / "scripts" / "mineru_convert.py"


# ---------------------------------------------------------------------------
# Converter implementations
# ---------------------------------------------------------------------------

def run_markitdown(pdf_path: Path, md_path: Path) -> tuple[list[str], subprocess.CompletedProcess[str], str]:
    cmd = ["markitdown", str(pdf_path), "-o", str(md_path)]
    completed = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return cmd, completed, "markitdown"


def run_pdftotext_fallback(pdf_path: Path, md_path: Path) -> tuple[list[str], subprocess.CompletedProcess[str], str]:
    cmd = ["pdftotext", "-layout", str(pdf_path), "-"]
    completed = subprocess.run(cmd, capture_output=True, text=True, check=True)
    md_path.write_text(completed.stdout, encoding="utf-8")
    return cmd, completed, "pdftotext-fallback"


def run_mineru(pdf_path: Path, md_path: Path, language: str = "ch") -> tuple[list[str], subprocess.CompletedProcess[str], str]:
    """Convert a PDF via MinerU cloud API.

    MinerU outputs to a subfolder; we point it at a temp directory, locate the
    generated .md file, and copy it to *md_path*.
    """
    if not _MINERU_SCRIPT.is_file():
        raise FileNotFoundError(
            f"MinerU script not found at {_MINERU_SCRIPT}. "
            "Install the mineru-pdf-converter skill first."
        )

    tmp_dir = Path(tempfile.mkdtemp(prefix="mineru_"))

    cmd = [
        "python", str(_MINERU_SCRIPT),
        "--input", str(pdf_path),
        "--output-dir", str(tmp_dir),
        "--language", language,
    ]

    try:
        completed = subprocess.run(cmd, capture_output=True, text=True, check=True)

        # MinerU produces <stem>.md inside the output dir
        stem = pdf_path.stem
        candidate = tmp_dir / f"{stem}.md"
        if not candidate.exists():
            # Fallback: find any .md file
            md_files = list(tmp_dir.glob("**/*.md"))
            if md_files:
                candidate = md_files[0]
            else:
                raise FileNotFoundError(
                    f"MinerU completed but no .md file found in {tmp_dir}"
                )

        shutil.copy2(candidate, md_path)

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return cmd, completed, "mineru"


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdfs", nargs="+", help="PDF files to convert")
    parser.add_argument(
        "--converter",
        choices=["markitdown", "mineru"],
        default="mineru",
        help="Backend converter (default: mineru).",
    )
    parser.add_argument(
        "--language",
        default="ch",
        help="Document language for MinerU (default: ch). Ignored for markitdown.",
    )
    parser.add_argument("--output-root", default=str(REPO_ROOT / "raw_markdown"), help="raw_markdown root")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing outputs")
    parser.add_argument(
        "--update-manifest",
        action="store_true",
        help="After conversion, mark the PDF as converted=true in raw_pdfs/pdf_sources.json.",
    )
    return parser


# ---------------------------------------------------------------------------
# Core conversion
# ---------------------------------------------------------------------------

def convert_one(pdf_path: Path, output_root: Path, overwrite: bool, converter: str = "mineru", language: str = "ch", update_manifest: bool = False) -> dict[str, object]:
    # Resolve to the real file on disk (may be in an external directory via manifest).
    # The slug and source_pdf_name always come from the presented name, not the real file.
    real_path = resolve_pdf_path(pdf_path)

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

    if converter == "mineru":
        cmd, completed, conversion_tool = run_mineru(real_path, md_path, language=language)
    else:
        # markitdown with pdftotext fallback
        try:
            cmd, completed, conversion_tool = run_markitdown(real_path, md_path)
        except subprocess.CalledProcessError as exc:
            stderr = (exc.stderr or "").strip()
            if "MediaBox" not in stderr:
                raise
            conversion_notes.append("markitdown failed with MediaBox error; used pdftotext fallback")
            cmd, completed, conversion_tool = run_pdftotext_fallback(real_path, md_path)

    markdown_text = md_path.read_text(encoding="utf-8", errors="replace")
    parsed = parse_pdf_filename(pdf_path)
    source_bytes = real_path.stat().st_size

    metadata = {
        "canonical_slug": slug,
        "source_pdf": str(real_path),
        "source_pdf_name": pdf_path.name,
        "markdown_file": relative_to_repo(md_path),
        "metadata_file": relative_to_repo(meta_path),
        "conversion_tool": conversion_tool,
        "conversion_command": cmd,
        "converted_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source_sha256": sha256_file(real_path),
        "source_size_bytes": source_bytes,
        "markdown_size_bytes": md_path.stat().st_size,
        "line_count": len(markdown_text.splitlines()),
        "heading_count": count_markdown_headings(markdown_text),
        "word_count": count_words(markdown_text),
        "title_guess": parsed["title"],
        "authors_guess": parsed["authors"],
        "year_guess": parsed["year"],
        "conversion_notes": conversion_notes,
        "mineru_stdout": completed.stdout.strip() if converter == "mineru" else "",
        "mineru_stderr": completed.stderr.strip() if converter == "mineru" else "",
        "markitdown_stdout": completed.stdout.strip() if converter != "mineru" else "",
        "markitdown_stderr": completed.stderr.strip() if converter != "mineru" else "",
    }
    meta_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    # Optionally mark the PDF as converted in pdf_sources.json
    if update_manifest:
        _mark_converted_in_manifest(real_path)

    return metadata


def _mark_converted_in_manifest(real_path: Path) -> bool:
    """Mark a single PDF as converted=true in raw_pdfs/pdf_sources.json.

    Matches by the resolved real path.  Normalises the matched entry
    and all other entries to canonical field order on write.
    """
    manifest_path = REPO_ROOT / "raw_pdfs" / "pdf_sources.json"
    if not manifest_path.exists():
        return False

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    found = False
    for _name, entry in manifest.get("pdfs", {}).items():
        entry_path = Path(entry.get("path", ""))
        try:
            if entry_path.resolve() == real_path.resolve():
                entry["converted"] = True
                found = True
                break
        except OSError:
            continue

    if found:
        # Normalise all entries to canonical field order before writing
        manifest["pdfs"] = {
            name: normalize_manifest_entry(e)
            for name, e in manifest["pdfs"].items()
        }
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

    return found


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    output_root = Path(args.output_root)
    results = []
    for pdf in args.pdfs:
        pdf_path = Path(pdf)
        results.append(convert_one(pdf_path, output_root, args.overwrite, args.converter, language=args.language, update_manifest=args.update_manifest))
    for result in results:
        print(f"{result['canonical_slug']}\t{result['markdown_file']}\t{result['metadata_file']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
