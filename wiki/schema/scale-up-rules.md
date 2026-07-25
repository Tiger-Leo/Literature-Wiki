---
title: Scale-Up Rules
type: schema
---

# Scale-Up Rules

Operational rules for production-scale build and maintenance. The user-facing version is at `docs/scale-up-guide.md`.

---

## 1. Round Count for `/wiki-build`

**Default: 2 rounds.**

| Corpus size | Round count |
|---|---|
| ≤6 papers | 1 (quick) |
| 7–20 papers | 2 (default) |
| 20–50 papers | 2; 3 if reviews still flag substantive issues |
| 50+ papers | 2–3; consider running on subsets defined by domain themes |

Override at invocation: `/wiki-build 1`, `/wiki-build 3`.

Rationale: round 1 produces foundational Wikipedia-style pages; round 2 deepens pages flagged thin and adds page types deferred from round 1 (e.g., methods, measures). Round 3 is for cross-link repair and final polish on persistent REVISE pages.

---

## 2. Parallelism Caps

| Phase | Cap |
|---|---|
| Phase 2 source-page writers | 8 parallel per batch |
| Phase 2 source-page reviewers | 8 parallel per batch |
| Phase 4 cluster writers | 8 parallel per batch |
| Phase 4 cluster reviewers | 8 parallel per batch |
| Phase 4 revisers | 8 parallel per batch |
| Revise rounds per source page | 1 |
| Revise rounds per synthesis page | 3 |

Larger jobs are processed in successive batches.

---

## 3. When Is a Paper "Fully Integrated"?

A paper is fully integrated after a `/wiki-build` pass when **all** hold:

1. Source page exists at `wiki/sources/<slug>.md` with `status: canonical`.
2. Frontmatter complete (`title`, `authors`, `year`, `slug`, `raw_markdown`, `status`).
3. No broken wikilinks for this page (`check_links.py`).
4. Slug appears in `papers:` arrays of ≥2 synthesis pages.
5. Log entry exists in `wiki/log.md` for the build run.

If a paper has a source page but appears in 0 or 1 synthesis pages, either it is genuinely off-topic for the current corpus (acceptable) or the curator missed relevant topics (open the workspace's `page-briefs/` to investigate).

---

## 4. When Is a Synthesis Page "Good Enough"?

A synthesis page does not need further revision when all of the rubric's PASS indicators hold (see `.claude/skills/wiki-build/rubric.md`):

- Encyclopedic lead paragraph
- Section headings name sub-topics, not papers
- ≥2 papers cited inline with non-trivial roles
- Frontmatter `papers:` matches body citations
- Cross-paper patterns appear as italicised generalisations with multi-citation
- `> **Current assessment (YYYY-MM):** ...` callout present where the wiki has a stance
- `## See also` cross-links resolve
- No "Paper Claims" or "Cross-Paper Patterns" top-level sections
- No placeholder text
- All 3 spot-check anchors from the curator's brief verify against the raw paper

Pages that exit Phase 4 with `VERDICT: PASS` meet this bar by construction. Pages capped at 3 revise rounds without PASS are logged in the workspace's `unresolved.md` and accepted as-is until a future build.

---

## 5. Stub Pages

A `status: stub` page is acceptable when:
- 0–1 papers in the corpus engage the topic
- The page exists to anchor wikilinks but has no substantive body yet

Stubs get upgraded to `active` when:
- ≥2 papers engage the topic, AND
- A `/wiki-build` round (or `/wiki-synthesis` call) writes a Wikipedia-style body that passes the rubric

Monthly stub scan:
```bash
grep -r "status: stub" wiki/ --include="*.md" -l
```

---

## 6. Maintenance Rhythm

| Cadence | Action |
|---|---|
| Per build | Phase 6 lint runs automatically. No manual step required. |
| Monthly | `/wiki-update-db` + stub scan + stale-assessment review |
| Quarterly | `/wiki-build 1` over the whole corpus to refresh synthesis pages; debate resolution check |

A `> **Current assessment**` callout becomes stale when a recently-added paper contradicts or extends it. The monthly review catches these; the quarterly refresh ensures all pages reflect the current corpus.

---

## 7. Local Search Tooling Decision

| Corpus size | Recommended tooling |
|---|---|
| <50 papers | `grep` and Claude Code's built-in search |
| 50–100 papers | SQLite export from `exports/raw-markdown-metadata.json` for metadata queries |
| 100+ papers | Obsidian Dataview (if browsing in Obsidian); vector index over `wiki/synthesis/` (not over raw_markdown) |

The wiki synthesis layer remains the primary interface regardless of corpus size. Search tooling is supplementary.

At 50+ papers, extend `export_metadata.py` with a `--sqlite` flag that writes `exports/wiki.db` with tables: `sources`, `concepts`, `mechanisms`, `debates`, `methods`, `measures`, `synthesis`, `links`.

---

## 8. Read-Raw-Markdown Invariant

Across all writers and reviewers in `/wiki-build`, the hardest rule to enforce is also the most important: **substantive claims trace to `raw_markdown/papers/<slug>.md`, never to `wiki/sources/<slug>.md`**.

Source pages are derived summaries. They can flatten nuance. The cluster reviewer's spot-check anchors are designed to catch claims that match the source page but not the raw paper.

This is restated in every prompt template in `.claude/skills/wiki-build/prompts/`.
