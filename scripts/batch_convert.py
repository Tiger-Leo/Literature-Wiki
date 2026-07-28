#!/usr/bin/env python3
"""Batch-convert the first N unconverted PDFs from the manifest via MinerU."""
import json, os, subprocess, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "raw_pdfs" / "pdf_sources.json"
CONVERTER = REPO_ROOT / "scripts" / "convert_pdf_to_markdown.py"

N = int(sys.argv[1]) if len(sys.argv) > 1 else 20

with open(MANIFEST_PATH, encoding="utf-8") as f:
    manifest = json.load(f)

# Collect first N unconverted entries
todo = []
for name, info in manifest["pdfs"].items():
    if isinstance(info, dict) and not info.get("converted"):
        todo.append((name, info))
    if len(todo) >= N:
        break

print(f"Converting {len(todo)} PDFs via MinerU...\n")

success = 0
fail = 0
for i, (name, info) in enumerate(todo, 1):
    real_path = info["path"]
    slug = info["slug"]
    print(f"[{i}/{len(todo)}] {slug}")
    print(f"       file: {Path(real_path).name[:70]}")

    # Skip if already converted (check filesystem directly)
    md_path = REPO_ROOT / "raw_markdown" / "papers" / f"{slug}.md"
    if md_path.exists():
        print(f"       SKIP — .md already exists, marking converted")
        manifest["pdfs"][name]["converted"] = True
        success += 1
        continue

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        ["python", str(CONVERTER), name, "--converter", "mineru", "--overwrite"],
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

# Save updated manifest
with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2, ensure_ascii=False)
    f.write("\n")

print(f"Done. Success: {success}, Failed: {fail}")
print(f"Manifest updated.")
