"""Clean test-directory entries from the manifest and deduplicate source_dirs/exclude_dirs."""
import json
from pathlib import Path

MANIFEST_PATH = Path(__file__).resolve().parents[1] / "raw_pdfs" / "pdf_sources.json"

with open(MANIFEST_PATH, encoding="utf-8") as f:
    manifest = json.load(f)

old_count = len(manifest["pdfs"])

# Remove entries pointing to the old test directory (E:\Desktop\Desktop\test\)
def _entry_path(value):
    return value if isinstance(value, str) else value["path"]

manifest["pdfs"] = {
    key: value
    for key, value in manifest["pdfs"].items()
    if "Desktop" not in _entry_path(value) and "test" not in Path(_entry_path(value)).parts
}

# Deduplicate source_dirs (keep only the real literature directory)
manifest["source_dirs"] = [
    d for d in manifest["source_dirs"]
    if "literature" in d.lower()
]

# Deduplicate exclude_dirs (the script merges old + new, producing duplicates)
seen = set()
unique_excludes = []
for d in manifest["exclude_dirs"]:
    normalized = str(Path(d).resolve())
    if normalized not in seen:
        seen.add(normalized)
        unique_excludes.append(d)
manifest["exclude_dirs"] = unique_excludes

new_count = len(manifest["pdfs"])

with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2, ensure_ascii=False)
    f.write("\n")

print(f"Cleaned: {old_count} → {new_count} entries")
print(f"Removed: {old_count - new_count} test-directory entries")
print(f"source_dirs: {len(manifest['source_dirs'])} entries")
print(f"exclude_dirs: {len(manifest['exclude_dirs'])} entries (deduplicated from {len(manifest['exclude_dirs']) + (old_count + len(manifest['source_dirs']) - new_count - len(manifest['source_dirs']))})")
