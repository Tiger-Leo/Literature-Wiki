"""Reconcile the 13 existing markdown papers with the new manifest.

For each paper in raw_markdown/papers/:
1. Compute its canonical slug
2. Find matching manifest entries (same slug, or fuzzy match on authors+year)
3. If found: update metadata JSON with the new source_pdf path
4. If not found: report as orphan
"""
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from pipeline_utils import canonical_slug_from_filename, resolve_pdf_path

MANIFEST_PATH = REPO_ROOT / "raw_pdfs" / "pdf_sources.json"
PAPERS_DIR = REPO_ROOT / "raw_markdown" / "papers"
METADATA_DIR = REPO_ROOT / "raw_markdown" / "metadata"

with open(MANIFEST_PATH, encoding="utf-8") as f:
    manifest = json.load(f)

def _entry_path(value):
    return value if isinstance(value, str) else value["path"]

# Build slug→(key, value) map from manifest
slug_to_manifest = {}
for key, value in manifest["pdfs"].items():
    slug = canonical_slug_from_filename(key)
    slug_to_manifest[slug] = (key, value)

manifest_modified = False

print(f"Manifest: {len(manifest['pdfs'])} entries, {len(slug_to_manifest)} unique slugs")
print()

updated = 0
not_found = 0
already_ok = 0

for md_path in sorted(PAPERS_DIR.glob("*.md")):
    slug = md_path.stem
    meta_path = METADATA_DIR / f"{slug}.json"

    if slug in slug_to_manifest:
        manifest_key, manifest_value = slug_to_manifest[slug]
        manifest_path = _entry_path(manifest_value)

        # Mark entry as converted in the manifest
        if isinstance(manifest["pdfs"][manifest_key], dict):
            if not manifest["pdfs"][manifest_key].get("converted"):
                manifest["pdfs"][manifest_key]["converted"] = True
                manifest_modified = True

        if meta_path.exists():
            with open(meta_path, encoding="utf-8") as f:
                meta = json.load(f)
            old_source = meta.get("source_pdf", "")
            if old_source != manifest_path:
                meta["source_pdf"] = manifest_path
                meta["manifest_key"] = manifest_key
                if "conversion_notes" not in meta:
                    meta["conversion_notes"] = []
                meta["conversion_notes"].append(
                    "2026-07-28: updated source_pdf from regenerated manifest"
                )
                with open(meta_path, "w", encoding="utf-8") as f:
                    json.dump(meta, f, indent=2, ensure_ascii=False)
                    f.write("\n")
                print(f"  UPDATED: {slug}")
                print(f"       old: {old_source[:80]}...")
                print(f"       new: {manifest_path[:80]}...")
                updated += 1
            else:
                print(f"  OK (no change): {slug}")
                already_ok += 1
        else:
            print(f"  WARN: {slug} has manifest entry but no metadata file")
    else:
        print(f"  NOT FOUND in manifest: {slug}")
        not_found += 1

# Write back manifest if converted flags were updated
if manifest_modified:
    from pipeline_utils import manifest_sort_key
    manifest["pdfs"] = dict(
        sorted(manifest["pdfs"].items(), key=lambda kv: manifest_sort_key(kv[0]))
    )
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"\nUpdated converted flags in manifest.")

print(f"\n--- Summary ---")
print(f"Updated: {updated}")
print(f"Already OK: {already_ok}")
print(f"Not found: {not_found}")
print(f"Total papers: {updated + already_ok + not_found}")
