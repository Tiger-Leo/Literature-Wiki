---
name: wiki-update-db
description: Use this skill when the user wants to lint, health-check, or maintain the wiki — phrases like "run the lint", "check the wiki", "fix broken links", "check links", "run validation", "validate the wiki", "clean up the wiki", "update the index", "health check", "rebuild the index", "validate frontmatter", "find orphan pages". Runs deterministic scripts and then applies fixes.
---

# Wiki Update-DB

## Lint Command Sequence

Run from project root in order:

```bash
# 1. Syntax check all scripts
python -m py_compile scripts/*.py

# 2. Check broken Obsidian wikilinks
python scripts/check_links.py wiki raw_markdown

# 3. Check orphan pages (no inbound links)
python scripts/check_orphans.py wiki

# 4. Validate frontmatter on all wiki pages
python scripts/validate_frontmatter.py wiki

# 5. Export metadata snapshot (succeeds silently — no output on success)
python scripts/export_metadata.py --output exports/raw-markdown-metadata.json
```

## Fix Protocol

After each run:

| Issue | Fix |
|---|---|
| Broken wikilink | Update the wikilink in the source page |
| Orphan page | Add inbound link from concept/mechanism/debate page or `_index.md` |
| Missing frontmatter field | Add the required field per `wiki/schema/frontmatter-schema.md` |
| Missing `_index.md` | Create a router file for that directory |

Do not use scripts for substantive academic judgments — only deterministic fixes.

## Health Check (beyond scripts)

After the lint pass, review the following:

**Stub upgrades** — A stub can be upgraded to `active` when:
- ≥2 source pages directly cite it (check the `papers:` frontmatter list), AND
- The **Cross-Paper Patterns** section has substantive content (not a placeholder)

To find upgrade candidates: `grep -r "status: stub" wiki/ --include="*.md" -l`, then check each stub's `papers:` list and Cross-Paper Patterns section.

**Stale assessments** — After ingesting new papers, check whether recently ingested papers contradict or extend the **Current assessment** on concept/mechanism/debate pages they are connected to.

**Missing concept pages** — Grep source pages for important concepts mentioned in their text that have no concept page yet: `grep -r "\[\[" wiki/sources/ --include="*.md" | grep -v "wiki/"` to find wikilinks pointing to non-existent pages (already caught by check_links.py, but concepts mentioned in prose without wikilinks may slip through).

**Missing cross-links** — Check that recently upgraded pages link to the synthesis pages that discuss them (`**Related synthesis:**` in Linked Pages).

## After Fixes

Append to `wiki/log.md`:
```
## [YYYY-MM-DD] lint | Full lint pass — N issues found, N fixed
```

## Full Workflow Reference

See `wiki/schema/update-db-workflow.md` for complete details.
