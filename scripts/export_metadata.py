#!/usr/bin/env python3
"""Export raw_markdown metadata sidecars into a single deterministic snapshot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pipeline_utils import REPO_ROOT


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata-dir", default=str(REPO_ROOT / "raw_markdown" / "metadata"))
    parser.add_argument("--output", default="-", help="Output file path or - for stdout")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    metadata_dir = Path(args.metadata_dir)
    rows = []
    for json_file in sorted(metadata_dir.glob("*.json")):
        rows.append(json.loads(json_file.read_text(encoding="utf-8")))
    payload = json.dumps(rows, indent=2, ensure_ascii=True) + "\n"
    if args.output == "-":
        print(payload, end="")
    else:
        Path(args.output).write_text(payload, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
