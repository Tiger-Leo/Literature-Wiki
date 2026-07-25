#!/usr/bin/env python3
"""Normalize raw PDF filenames into canonical lowercase kebab-case slugs."""

from __future__ import annotations

import argparse
from pathlib import Path

from pipeline_utils import canonical_slug_from_filename


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="PDF paths or filenames to normalize")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    for raw_path in args.paths:
        print(f"{raw_path}\t{canonical_slug_from_filename(raw_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

