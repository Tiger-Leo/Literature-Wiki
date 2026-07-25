#!/usr/bin/env python3
"""Shared helpers for deterministic wiki pipeline scripts."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def ascii_slugify(text: str) -> str:
    """Convert arbitrary text into lowercase kebab-case ASCII."""

    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "untitled"


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
