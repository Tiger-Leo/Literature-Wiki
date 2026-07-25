---
title: Update-DB Workflow
type: schema
---

# Update-DB Workflow

## Repeatable Lint Command Sequence

Run these in order from the project root:

```bash
# 1. Syntax check scripts
python -m py_compile scripts/*.py

# 2. Check for broken Obsidian wikilinks
python scripts/check_links.py wiki raw_markdown

# 3. Check for orphan pages (no inbound links)
python scripts/check_orphans.py wiki

# 4. Validate frontmatter on all wiki pages
python scripts/validate_frontmatter.py wiki

# 5. Export metadata snapshot
python scripts/export_metadata.py --output exports/raw-markdown-metadata.json
```

## Lint Checks

| Check | Script | Expected output |
|---|---|---|
| Broken wikilinks | `check_links.py` | Zero broken links |
| Orphan pages | `check_orphans.py` | Zero orphans (except `_index.md` files) |
| Missing frontmatter | `validate_frontmatter.py` | Zero missing required fields |
| Missing `_index.md` | `check_links.py` | All directories have router files |

## Fix Protocol

After each lint run:

1. Fix broken links by updating the source page wikilinks
2. Fix orphan pages by adding at least one inbound link from a concept/mechanism/debate page or `_index.md`
3. Fix missing frontmatter by adding the required fields
4. Do not use scripts to make substantive academic judgments — only deterministic fixes

## Health Check Items (beyond scripts)

Periodically review:
- Contradictions between pages that newer evidence has resolved
- Stale current-assessment claims
- Concept pages with zero paper evidence (pure stubs)
- Important concepts mentioned in source pages but lacking their own concept page
- Missing cross-references between related pages

## After Fixes

Append a lint entry to `wiki/log.md`:

```
## [YYYY-MM-DD] lint | Full lint pass — N issues found, N fixed
```
