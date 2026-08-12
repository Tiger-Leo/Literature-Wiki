#!/usr/bin/env python3
"""Shared helpers for deterministic wiki pipeline scripts."""

from __future__ import annotations

import functools
import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def ascii_slugify(text: str) -> str:
    """Convert arbitrary text into lowercase kebab-case, preserving CJK characters."""
    text = unicodedata.normalize("NFKD", text)
    # Remove combining diacritical marks (e.g. í → i + ´ → i)
    text = re.sub(r"[̀-ͯ]+", "", text)
    text = text.lower().strip()
    # Preserve ASCII alphanumerics AND CJK Unified Ideographs (U+4E00–U+9FFF)
    # Everything else becomes a hyphen separator.
    text = re.sub(r"[^a-z0-9一-鿿]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "untitled"


def _is_cjk(ch: str) -> bool:
    """Return True if *ch* is a CJK Unified Ideograph."""
    return '一' <= ch <= '鿿'


def manifest_sort_key(name: str) -> tuple[int, str]:
    """Sort key for manifest entries: Chinese (pinyin) first, then English.

    Returns ``(0, pinyin_lower)`` for Chinese names, ``(1, name_lower)`` for English,
    so Chinese entries sort before English entries.
    """
    if any(_is_cjk(c) for c in name):
        try:
            from pypinyin import lazy_pinyin  # type: ignore[import-untyped]
        except ImportError:
            return (0, name.lower())
        pinyin = ''.join(lazy_pinyin(name, errors='ignore')).lower()
        return (0, pinyin)
    else:
        return (1, name.lower())


def parse_pdf_filename(pdf_path: str | Path) -> dict[str, str]:
    """Extract a best-effort authors/year/title guess from a paper filename.

    Expected input format is usually:
    `Author and Author - 2024 - Paper Title.pdf`
    """

    stem = Path(pdf_path).stem.replace("\u00a0", " ").strip()
    parts = [part.strip() for part in re.split(r"\s+-\s+", stem) if part.strip()]

    authors = ""
    year = ""
    title = stem

    if len(parts) >= 3 and re.fullmatch(r"\d{4}", parts[1]):
        authors = parts[0]
        year = parts[1]
        title = " - ".join(parts[2:])
    elif len(parts) >= 2 and re.fullmatch(r"\d{4}", parts[0]):
        year = parts[0]
        title = " - ".join(parts[1:])
    elif len(parts) >= 2:
        authors = parts[0]
        title = " - ".join(parts[1:])

    return {
        "authors": authors,
        "year": year,
        "title": title,
        "stem": stem,
    }


def canonical_slug_from_filename(pdf_path: str | Path) -> str:
    """Build the canonical lowercase kebab-case slug used across raw_markdown."""

    parsed = parse_pdf_filename(pdf_path)
    slug_parts = []
    if parsed["authors"]:
        slug_parts.append(ascii_slugify(parsed["authors"]))
    if parsed["year"]:
        slug_parts.append(parsed["year"])
    if parsed["title"]:
        slug_parts.append(ascii_slugify(parsed["title"]))
    return "-".join(part for part in slug_parts if part)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_markdown_headings(text: str) -> int:
    return sum(1 for line in text.splitlines() if line.lstrip().startswith("#"))


def count_words(text: str) -> int:
    return len(re.findall(r"\b\S+\b", text))


def relative_to_repo(path: Path) -> str:
    resolved = path.resolve()
    return str(resolved.relative_to(REPO_ROOT)).replace("\\", "/")


# ---------------------------------------------------------------------------
# PDF source manifest — supports PDFs stored outside raw_pdfs/
# ---------------------------------------------------------------------------

_MANIFEST_CACHE: dict[str, str] | None = None


def _manifest_value_path(value: str | dict) -> str:
    """Extract the file-system path from a manifest entry value.

    Handles both legacy format (plain string) and current format
    (dict with a ``path`` key).
    """
    if isinstance(value, str):
        return value
    return value["path"]


def load_pdf_manifest(repo_root: Path | None = None) -> dict[str, str]:
    """Load ``raw_pdfs/pdf_sources.json``, returning ``{name: real_path}``.

    Handles both legacy (string value) and current (dict value) formats.
    The result is cached in-process so repeated calls don't re-read the file.
    Pass a different *repo_root* to bypass the cache.
    """
    global _MANIFEST_CACHE
    if repo_root is not None:
        # Explicit root — don't cache
        manifest_path = repo_root / "raw_pdfs" / "pdf_sources.json"
        if not manifest_path.exists():
            return {}
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        raw = data.get("pdfs", {})
        return {k: _manifest_value_path(v) for k, v in raw.items()}

    if _MANIFEST_CACHE is not None:
        return _MANIFEST_CACHE

    manifest_path = REPO_ROOT / "raw_pdfs" / "pdf_sources.json"
    if not manifest_path.exists():
        _MANIFEST_CACHE = {}
        return _MANIFEST_CACHE

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    raw = data.get("pdfs", {})
    _MANIFEST_CACHE = {k: _manifest_value_path(v) for k, v in raw.items()}
    return _MANIFEST_CACHE


def resolve_pdf_path(pdf_path: str | Path) -> Path:
    """Resolve a PDF path to a real file on disk.

    1. If *pdf_path* exists as a file, return it resolved.
    2. Otherwise, look up its filename in the manifest (``raw_pdfs/pdf_sources.json``).
    3. Also try the full path as a manifest key.
    4. Raise ``FileNotFoundError`` if nothing matches.
    """
    pdf_path = Path(pdf_path)
    if pdf_path.is_file():
        return pdf_path.resolve()

    manifest = load_pdf_manifest()

    # Try filename-only match first
    name = pdf_path.name
    if name in manifest:
        return Path(manifest[name])

    # Try full path as manifest key
    key = str(pdf_path).replace("\\", "/")
    if key in manifest:
        return Path(manifest[key])

    raise FileNotFoundError(
        f"PDF not found: {pdf_path}\n"
        f"  Checked: file system and {REPO_ROOT / 'raw_pdfs' / 'pdf_sources.json'}"
    )


# ---------------------------------------------------------------------------
# Manifest entry helpers — page counting, doc-type classification & canonical field order
# ---------------------------------------------------------------------------

# Publisher imprints commonly found in directory names — used to distinguish
# books / book-chapters from journal articles.
_PUBLISHER_DIR_KW = [
    "press", "springer", "routledge", "wiley", "elsevier", "palgrave",
    "cambridge university", "oxford university", "harvard", "mit press",
    "princeton", "chicago", "mcgraw", "pearson", "sage", "thomson",
    "kluwer", "birkhauser", "world scientific", "crc", "academic press",
    "edward elgar", "now publishers", "the free press", "free press",
    "atlantis press", "stata press", "harvard business",
    "abo akademi",  # Åbo Akademi University Press
]

# Filename / path keywords that strongly indicate a dissertation
_THESIS_KW = [
    "博士", "硕士", "学位论文", "dissertation", "thesis",
    "doctoral", "ph.d.", "phd thesis",
]


def classify_doc_type(pdf_path: str | Path, pages: int) -> str:
    """Classify a PDF into one of four document types.

    Returns one of: ``"journal-article"``, ``"dissertation"``,
    ``"book"``, ``"book-chapter"``.

    Heuristics (in priority order):
    1. Directory named after a publisher + pages ≥ 200 → ``"book"``
    2. Directory named after a publisher + pages < 60 → ``"book-chapter"``
    3. Directory named after a publisher → ``"book"`` (catch-all)
    4. Filename contains thesis keywords → ``"dissertation"``
    5. 100 ≤ pages < 200 and NOT a publisher directory → ``"dissertation"``
    6. pages ≥ 200 → ``"book"``
    7. Everything else → ``"journal-article"``
    """
    path_str = str(pdf_path)
    dirname_lower = Path(pdf_path).parent.name.lower()
    is_publisher_dir = any(kw in dirname_lower for kw in _PUBLISHER_DIR_KW)

    # Publisher directory → book or book-chapter
    if is_publisher_dir:
        if pages >= 200:
            return "book"
        if pages < 60:
            return "book-chapter"
        return "book"

    # Thesis keywords in filename
    fname_lower = Path(pdf_path).name.lower()
    if any(kw in fname_lower for kw in _THESIS_KW):
        return "dissertation"

    # University directory + substantial page count → likely dissertation
    _UNIV_DIR_KW = ["大学", "学院", "university", "college"]
    if any(kw in dirname_lower for kw in _UNIV_DIR_KW) and pages >= 50:
        return "dissertation"

    # Page-count heuristics (non-publisher paths)
    if 100 <= pages < 200:
        return "dissertation"
    if pages >= 200:
        return "book"

    return "journal-article"


def get_pdf_page_count(pdf_path: str | Path) -> int:
    """Extract page count from a PDF using PyMuPDF.

    Returns 0 if the file is missing, unreadable, or not a valid PDF.
    """
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(str(pdf_path))
        pages = doc.page_count
        doc.close()
        return pages
    except Exception:
        return 0


def normalize_manifest_entry(entry: dict) -> dict:
    """Rebuild a manifest entry with canonical field order.

    Canonical order: ``path``, ``slug``, ``type``, ``pages``, ``converted``.

    If ``type`` is missing it is inferred via :func:`classify_doc_type`.
    If ``pages`` is missing or ``None``, it is extracted from the PDF
    on disk via :func:`get_pdf_page_count`.  Other fields fall back to
    sensible defaults when absent.
    """
    path = entry.get("path", "")
    pages = entry.get("pages")
    if pages is None:
        pages = get_pdf_page_count(path)
    doc_type = entry.get("type")
    if doc_type is None:
        doc_type = classify_doc_type(path, pages)
    return {
        "path": path,
        "slug": entry.get("slug", ""),
        "type": doc_type,
        "pages": pages,
        "converted": entry.get("converted", False),
    }
