---
title: Build Workflow
type: schema
---

# Build Workflow

This file documents the **contract** for `/wiki-build` from the wiki's perspective. The implementation lives in `.claude/skills/wiki-build/SKILL.md`; the page-quality bar lives in `.claude/skills/wiki-build/rubric.md`. This file states what the wiki layer expects to see after a build.

## When to Run

- After new PDFs are added to `raw_pdfs/`
- To rebuild / upgrade the synthesis layer ("rebuild concept pages", "re-synthesize the wiki")
- Explicit round-count: `/wiki-build`, `/wiki-build 1`, `/wiki-build 3`

For one-off insight saving, use `/wiki-synthesis` instead. For lint-only passes, use `/wiki-update-db`.

## What `/wiki-build` Produces

After a successful build run:

1. Every paper in `raw_pdfs/` has:
   - A converted markdown at `raw_markdown/papers/<slug>.md`
   - A metadata sidecar at `raw_markdown/metadata/<slug>.json` (when generated)
   - A source page at `wiki/sources/<slug>.md` with `status: canonical`
2. Every topic in the round plan has a synthesis page at `wiki/<type>/<slug>.md`, where:
   - The page meets `.claude/skills/wiki-build/rubric.md` PASS criteria
   - Frontmatter `papers:` array lists every slug cited in the body
   - `status: active`
3. Every `_index.md` is updated.
4. `wiki/log.md` has an entry of the form:
   ```
   ## [YYYY-MM-DD] wiki-build | <N_rounds> rounds, <N_pages> pages
   - Workspace: agent_tasks/wikipedia-rewrite_<DATE><HHMM>/
   - ...
   ```
5. A full lint suite has been run and any deterministic issues fixed.

## Workspace Layout

Every build run creates a workspace at `agent_tasks/wikipedia-rewrite_<DATE><HHMM>/`:

```
agent_tasks/wikipedia-rewrite_<DATE><HHMM>/
├── scope.md
├── conversion-notes.md
├── source-reviews/
├── status/                            ← all subagent ≤200-word status returns
├── round-1/
│   ├── plan.md                        ← Phase 3 planner output
│   ├── page-briefs/<slug>.md          ← Stage A curator briefs
│   ├── rewritten-wiki/<type>/<slug>.md   ← Stage B writer drafts
│   ├── reviews/cluster-<label>.md     ← Stage C reviewer output
│   ├── round-output/<type>/<slug>.md  ← Stage D revised + PASS pages
│   ├── lint-report.md
│   └── logs/
├── round-2/   (same structure, only if needed)
├── round-3/   (same structure, only if needed)
└── final/round-output/                ← copied from last round; goes into wiki/
```

The workspace is the authoritative record of the build. If a reviewer's verdict disagrees with what ended up in `wiki/`, the workspace shows where the decision was made.

## Knowledge Separation Inside Synthesis Pages

Every synthesis page maintains three claim levels **inline**, never as separate top-level sections:

| Level | Inline marker |
|---|---|
| Paper claim | Inline `[[slug]]` citation |
| Cross-paper pattern | Italicised generalisation + multi-citation parenthetical |
| Current assessment | Short `> **Current assessment (YYYY-MM):** ...` callout |

A section titled "Paper Claims", "Cross-Paper Patterns", or similar listing structure is an automatic REVISE trigger (see `.claude/skills/wiki-build/rubric.md`).

## Source vs. Synthesis Pages

Source pages and synthesis pages have different rubrics.

- **Source pages** are bibliographic records. Per-paper structure (Research Question / Model / Results / ...). One review pass. Not the wiki's deliverable.
- **Synthesis pages** are encyclopedic articles. Subject-matter backbone. Multi-round write → review → revise.

Synthesis-page invariants (full list in the rubric):
- Encyclopedic lead paragraph
- Section headings name sub-topics, not papers
- Multi-citation where claims converge
- Three knowledge levels visible but not dominant
- Every paper in the curator's `key_sources_ranked` appears in body
- Cross-links resolve
- Substantive claims trace to `raw_markdown/papers/<slug>.md`, not source pages

## Hand-off

After `/wiki-build` returns, the user can:

- Open `agent_tasks/wikipedia-rewrite_<DATE><HHMM>/final/round-output/` for the final pages produced.
- Open `wiki/log.md` for the run summary.
- Run `/wiki-query` to test the new state of the wiki.
- Run `/wiki-update-db` if any deterministic issues remain.
