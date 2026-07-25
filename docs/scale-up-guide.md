# Scale-Up Guide

Practical guide for growing the literature-wiki from a small pilot (5–10 papers) to a large collection (50+ papers).

---

## Scale-Up Philosophy

The wiki grows by **build pass**, not by per-paper ingest. Each `/wiki-build` run:

1. Adds source pages for any new papers
2. Plans which synthesis pages need to be created or updated based on the current corpus
3. Writes / revises those synthesis pages in parallel via cluster writers, reviewers, and revisers
4. Lints the result

Quality over quantity: a well-built page that integrates the full literature on its topic is worth more than many shallow per-paper summaries. The system rewards letting a build pass go to completion before adding more papers.

---

## Pilot Phase (5–10 papers)

Goal: validate the pipeline produces Wikipedia-style pages on your actual corpus.

- [ ] 5–10 representative PDFs in `raw_pdfs/`
- [ ] Run `/wiki-build 2` (default round count)
- [ ] After Phase 6, spot-check 3 synthesis pages by reading:
  - Does the lead paragraph make sense on its own?
  - Are section headings sub-topics (good) or paper names (FAIL)?
  - Are claims integrated across multiple papers per section?
  - Are spot-check anchors verifiable against the raw papers?
- [ ] Run `/wiki-query` with a cross-paper question; confirm the answer cites multiple sources in integrated prose
- [ ] Fix any persistent issues (e.g., curator briefs too generic; cluster theme labels off) before scaling

The pilot is complete when:
- All papers have source pages with `status: canonical`
- At least 5 synthesis pages exist (mix of concept / mechanism / debate)
- Lint passes cleanly
- A typical `/wiki-query` returns a coherent answer drawing on multiple sources

---

## Round-Count Policy

| Corpus size | Default round count |
|---|---|
| ≤6 papers | 1 round (quick) |
| 7–20 papers | 2 rounds (default) |
| 20–50 papers | 2 rounds; 3 if reviews still flag many issues after round 2 |
| 50+ papers | 2–3 rounds; consider running build passes on subsets defined by domain themes |

Override at invocation: `/wiki-build 1` or `/wiki-build 3`.

---

## "Fully Integrated" Per-Paper Checklist

After `/wiki-build` completes, a paper is fully integrated when **all** of these are true:

- [ ] Source page exists at `wiki/sources/<slug>.md` with `status: canonical`
- [ ] YAML frontmatter complete (all required fields per `wiki/schema/frontmatter-schema.md`)
- [ ] Provenance link to `raw_markdown/papers/<slug>.md` present
- [ ] The paper appears in the `papers:` frontmatter array of ≥2 synthesis pages
- [ ] Source page wikilinks resolve
- [ ] `wiki/sources/_index.md` entry added
- [ ] `wiki/log.md` entry appended

If a paper has been built into source-page form but never appears in any synthesis page, the curator did not find it relevant to any topic in scope. Either that's correct (the paper is genuinely off-topic for the current corpus) or the curator missed it — check `agent_tasks/wikipedia-rewrite_*/round-N/page-briefs/` to see which briefs ranked it.

---

## "Good Enough to Stop Revising" Criteria for Synthesis Pages

A synthesis page is `status: active` and done when, against `.claude/skills/wiki-build/rubric.md`:

- Encyclopedic lead paragraph (no bullets, no single-paper-only citation)
- Section headings name sub-topics, not papers
- ≥2 papers cited inline with non-trivial roles in the body
- `papers:` frontmatter matches body citations
- Cross-paper patterns appear as italicised generalisations with multi-citation
- A `> **Current assessment (YYYY-MM):** ...` callout is present where the wiki has a stance
- `## See also` cross-links resolve
- No placeholder text

This is enforced by the cluster reviewer's three lenses during `/wiki-build`. Pages that exit Phase 4 with `VERDICT: PASS` meet this bar.

---

## Stub Upgrade Protocol

`status: stub` pages can persist when a build pass declined to build them (e.g., not enough corpus support). Run monthly to find them:

```bash
grep -r "status: stub" wiki/ --include="*.md" -l
```

For each stub:

1. Check the `papers:` array. If ≥2 papers in the current corpus engage the topic, the stub is upgradeable.
2. Add the stub to the next `/wiki-build` round's scope. The simplest way: drop a note in the round plan after the planner produces it.
3. Or: invoke `/wiki-synthesis` to write that single page surgically.

If a stub has 0–1 supporting papers, leave it as a stub. Stubs are a signal that the topic is on the wiki's radar but not yet established.

---

## Maintenance Rhythms

### After every `/wiki-build` pass

Phase 6 of `/wiki-build` already runs the full lint. No manual step needed unless lint reports issues.

### Monthly

```
/wiki-update-db
```

This runs:

```bash
python -m py_compile scripts/*.py
python scripts/check_links.py wiki raw_markdown
python scripts/check_orphans.py wiki
python scripts/validate_frontmatter.py wiki
python scripts/export_metadata.py --output exports/raw-markdown-metadata.json
```

Plus:
- Stub upgrade scan (`grep -r "status: stub" wiki/ --include="*.md" -l`)
- Stale assessment review — check whether recently added papers contradict or extend existing `> **Current assessment**` callouts. Where they do, schedule those pages for the next build's scope.

### Quarterly

- [ ] Run `/wiki-build 1` over the whole corpus to refresh all synthesis pages
- [ ] Debate resolution check — can any debate pages be marked `status: resolved`?
- [ ] Audit for missing concept pages: grep source pages' "Concepts Engaged" sections for topics that lack pages

---

## Search Tooling Thresholds

| Collection size | Recommended tooling |
|---|---|
| < 50 papers | `grep` and Claude Code's built-in search are sufficient |
| 50–100 papers | Add a SQLite export of `exports/raw-markdown-metadata.json` for fast metadata queries |
| 100+ papers | Consider Obsidian's Dataview plugin, the optional Search/Browse web UI, or a vector index over `wiki/synthesis/` (not `raw_markdown/`) |

The wiki layer remains the primary interface regardless. RAG / vector search is supplementary, not a replacement. The optional web layer (client-side Search over `wiki/`, plus an opt-in RAG-backed Chat) ships with this template — see [search-and-browse.md](search-and-browse.md) and [rag-backend.md](rag-backend.md).

---

## Concept Page Growth Pattern

As the corpus grows, a concept page evolves:

| Stage | Papers engaging | Status | Description |
|---|---|---|---|
| Stub | 0–1 | `stub` | Topic on the wiki's radar; thin body |
| Emerging | 2–4 | `active` | Encyclopedic lead, sub-topic sections beginning to integrate; some current assessment |
| Established | 5+ | `active` | Rich Wikipedia-style article; multi-citation throughout; confident current assessment |
| Contested | multiple in tension | `active` | A `wiki/debates/<slug>.md` page is spun out; concept page cross-links to it |

The transition from Stub to Emerging is the most important upgrade. Once a topic is engaged by ≥2 papers, the next `/wiki-build` round should write it as an Emerging page.

---

## Multi-Agent Batch Protocol

`/wiki-build` already implements the multi-agent batch protocol internally. The principles it follows (and that you should mirror if writing custom subagent workflows for this wiki):

1. **File handoff only** — every subagent writes its output to a specific path on disk. The orchestrator never receives full content in messages.
2. **Parallel within phase** — all writers spawn in one tool-call; same for reviewers; same for revisers.
3. **Specify input AND output paths** in every subagent brief.
4. **Confirm file existence** (`ls`) after each phase before moving on.
5. **Status summaries are ≤200 words** — they describe what was done and surface issues; they do not paste content.
6. **Read raw markdown, not source pages** — every writer and reviewer bases substantive claims on `raw_markdown/papers/<slug>.md`.

---

## Scale-Up Rules Summary

| Rule | Value |
|---|---|
| Default round count | 2 |
| Per-round writer cap | 8 parallel cluster writers per batch |
| Per-round reviewer cap | 8 parallel reviewers per batch |
| Revise rounds per page | Up to 3 in Phase 4 (synthesis pages); up to 1 in Phase 2 (source pages) |
| Lint frequency | Automatic in Phase 6 of every build |
| Fully integrated (per paper) | Source page canonical + appears in ≥2 synthesis pages |
| Good enough to stop (per synthesis page) | Passes `.claude/skills/wiki-build/rubric.md` automatic PASS indicators |
| Monthly tasks | `/wiki-update-db` + stub scan + stale-assessment review |
| Quarterly tasks | Full `/wiki-build 1` refresh + debate-resolution check |
| SQLite threshold | 50+ papers |

Full detail: [[wiki/schema/scale-up-rules]].
