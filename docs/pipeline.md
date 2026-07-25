# PDF-to-Wiki Build Pipeline

**Technical Reference**

The full pipeline that transforms a folder of PDFs into a Wikipedia-style literature wiki, run end-to-end by `/wiki-build`.

---

## Overview

```
raw_pdfs/
    └─► raw_markdown/papers/<slug>.md           (Phase 1)
              └─► wiki/sources/<slug>.md         (Phase 2 — bibliographic record)
                        └─► wiki/concepts/<slug>.md
                            wiki/mechanisms/<slug>.md
                            wiki/debates/<slug>.md
                            wiki/methods/<slug>.md
                            wiki/measures/<slug>.md
                            wiki/synthesis/<slug>.md
                                  ─ Wikipedia-style synthesis pages (Phases 3–4)
                        └─► _index.md, log.md, lint (Phase 5–6)
```

The deliverable is the **synthesis layer** — Wikipedia-style pages, each on one topic, integrating evidence from across the whole collection. Source pages are bibliographic anchors, not the deliverable.

---

## Triggers

```
/wiki-build          # default — 2 rounds
/wiki-build 1        # quick pass, 1 round
/wiki-build 3        # deeper pass, 3 rounds
```

Phrases that also trigger: "build the wiki", "rebuild wiki pages", "synthesize the collection", "process all PDFs", "make Wikipedia-style pages from the papers", "ingest these papers".

---

## Phase 0 — Workspace Setup

A fresh workspace is created at:

```
agent_tasks/wikipedia-rewrite_<DATE><HHMM>/
├── scope.md
├── conversion-notes.md
├── source-reviews/
├── status/                     ← all subagent ≤200-word status summaries
├── round-1/
│   ├── plan.md
│   ├── page-briefs/<slug>.md   ← Stage A curator output
│   ├── rewritten-wiki/<type>/<slug>.md   ← Stage B writer drafts
│   ├── reviews/cluster-<label>.md         ← Stage C reviewer output
│   ├── round-output/<type>/<slug>.md      ← Stage D final for this round
│   ├── logs/
│   └── lint-report.md
├── round-2/   (same structure, only if needed)
├── round-3/   (same structure, only if needed)
└── final/round-output/                    ← copied from last round; goes into wiki/
```

Existing `wiki/sources/` is compared against `raw_pdfs/`. Any unmatched PDFs become `NEW_PAPERS`; the rest are `EXISTING_PAPERS`.

---

## Phase 1 — PDF to Raw Markdown

For each PDF in `NEW_PAPERS`:

```bash
python scripts/normalize_filename.py "<pdf_filename>"
# → author-and-author-year-short-title

python scripts/convert_pdf_to_markdown.py "raw_pdfs/<pdf>" \
  --output raw_markdown/papers/<slug>.md
```

**Slug rules** (`scripts/normalize_filename.py`):
- Lowercase kebab-case
- Format: `author-and-author-year-short-title`
- Input filename expected: `Author and Author - YYYY - Paper Title.pdf`

**Quality check** after conversion: title, authors, ≥3 section headings, references section. Anomalies go in `agent_tasks/<workspace>/conversion-notes.md`.

**Conversion failure modes** (documented in `wiki/schema/conversion-notes.md`):

| Failure mode | Symptom | Mitigation |
|---|---|---|
| Mathematical notation degrades | Symbols garbled or missing | LaTeX markup where recoverable |
| Tables collapse | Structure lost, data runs inline | Flag in conversion-notes; reconstruct if critical |
| Multi-column layout interleaves | Columns alternate line-by-line | Flag; manual reflow for key sections |
| Figures become empty placeholders | Image content absent; caption may survive | Note; retain caption text |

---

## Phase 2 — Source Pages (Parallel Writers + Light Review)

Source pages are **bibliographic records**, not encyclopedic synthesis. One writer per new paper, in parallel.

### 2a. Writers

Each writer uses `.claude/skills/wiki-build/prompts/source-writer.md`. Output: `wiki/sources/<slug>.md` with frontmatter and the standard source-page sections (Research Question / Model or Design / Main Results / Mechanisms Identified / Methods and Measures / Concepts Engaged / Connection to Debates / Theoretical or Empirical Significance / Notes and Caveats).

Frontmatter required: `title`, `authors`, `year`, `slug`, `raw_markdown`, `status: canonical`.

Cap: 8 parallel writers per batch.

### 2b. Reviewers

Each reviewer uses `.claude/skills/wiki-build/prompts/source-reviewer.md`. Checks: frontmatter complete, all template sections substantive, one main-result claim spot-checked against the raw paper.

### 2c. Revise (max 1 round)

REVISE pages get one revision pass. Source pages are factual records; if still REVISE after one pass, accept and log.

---

## Phase 3 — Round Plan

One planner subagent (`prompts/round-planner.md`) produces `agent_tasks/<workspace>/round-N/plan.md`.

The plan contains:

1. **Goal of this round** — round 1 = foundational rewrite; round 2 = deepen flagged pages, add deferred page types; round 3 = polish.
2. **Pages in scope** — explicit list by type. Methods and measures may be deferred to round 2.
3. **Cluster map** — pages grouped into 6–10 clusters of 2–3 pages each. Clusters have **emergent themes** that reflect the actual corpus (not pre-set labels). Pages whose source papers overlap go in the same cluster so one writer is efficient.
4. **Domain axes** — does the corpus have a coherent **frontier extension** sub-literature (AI-era / replication / behavioural / etc.)? If yes, which pages must include a Frontier section. If no, set NONE. Do not force.
5. **Mandatory cross-cutting rule** — every writer and reviewer reads `raw_markdown/papers/<slug>.md`, never `wiki/sources/<slug>.md`.
6. **Stage list** — A (curator) → B (cluster writers) → C (cluster reviewers) → D (revisers).

The orchestrator shows the plan summary to the user (5–10 lines) before continuing. The user may edit `plan.md`.

---

## Phase 4 — Round Execution

### Stage A — Curator (1 subagent)

The curator (`prompts/curator.md`) reads the plan + the raw markdown of every candidate paper, then writes one **brief** per scope page at `round-N/page-briefs/<slug>.md` using the schema in `prompts/page-brief-template.md`.

Each brief contains:
- `page_type`, `cluster`
- `working_definition`, `why_it_matters`
- `wikipedia_outline` — section list (≥7 sections) with one-line scope and **per-section source allocation** (≥4 papers per major section where the corpus allows); subject-matter backbone, not paper-by-paper
- `key_sources_ranked` — ≤10 slugs with one-line rationale and the explicit raw-markdown path
- `cross_link_targets` — other wiki pages to wikilink (12–15 by default)
- `callout_target` — number/placement of knowledge-level callouts (2–4)
- `length_target` (words; default band 1700–2200, up to 2800 for major synthesis — degrade for thin corpora, never pad)
- `writing_constraints` — including the read-raw-markdown rule and any frontier-axis requirement
- `spot_check_anchors` — exactly 3 specific claims the reviewer will verify against the raw paper

The curator also writes a master `_index.md` listing the cluster map.

### Stage B — Cluster Writers (parallel)

One writer per cluster (`prompts/cluster-writer.md`), all spawned in a single tool-call message. Each writer takes ~2–3 pages from one cluster and produces Wikipedia-style pages to `round-N/rewritten-wiki/<type>/<slug>.md`.

Writer constraints (full rubric in `.claude/skills/wiki-build/rubric.md`):
- **Encyclopedic lead paragraph** — defines the topic, says why it matters, previews the page. No bullets.
- **Subject-matter backbone** — section headings name sub-topics, formal-model components, evolutionary stages — NOT papers. No "Paper Claims" section.
- **Integrated citations** — multi-cite where claims converge; name papers in flow only where distinct contribution matters.
- **Three knowledge levels visible but not dominant** — inline `[[slug]]` for paper claims, italicised generalisations with multi-citation for cross-paper patterns, short `> **Current assessment (YYYY-MM):** ...` callouts for assessments. NOT separate top-level sections.
- **Frontmatter** with `papers:` array matching every slug cited in the body.
- **Cross-links** at the end with the brief's `cross_link_targets`.
- **READ THE RAW PAPER**, never the source page. Every substantive claim traces to `raw_markdown/papers/<slug>.md`.

Cap: 8 cluster writers per parallel batch.

### Stage C — Cluster Reviewers (parallel)

Reviewers cover ~2 clusters each (~5 pages). Use `prompts/cluster-reviewer.md`. Four lenses per page:

1. **Synthesis quality** — Wikipedia article or list? Subject-matter backbone? No "Paper Claims" section?
2. **Fidelity** — Spot-check all 3 `spot_check_anchors` against `raw_markdown/papers/<slug>.md`. Also spot-check 2 randomly chosen citations.
3. **Coverage and cross-links** — Every paper in `key_sources_ranked` appears in body with non-trivial role; wikilinks resolve; frontmatter `papers:` matches body.
4. **Density and depth** — Word band, 7–10 sections, each body section ≥150 words / ≥4 papers where corpus allows, 2–4 callouts, 12–15 cross-links. REVISE on any shortfall the corpus could fill (skeletal sections, single-paper major sections, trivial-role citations); PASS on density when the corpus is genuinely thin.

Output: `round-N/reviews/cluster-<label>.md` with `VERDICT: PASS` or `VERDICT: REVISE` per page, and fix lists (≤8 items per page) for REVISE.

**Automatic REVISE triggers** (from `rubric.md`):
- Section named "Paper Claims" or equivalent listing structure
- ≥2 consecutive paragraphs organised paper-by-paper
- Bullet-only lead paragraph
- Any `key_sources_ranked` paper absent from body
- Any spot-check anchor fails
- Frontmatter `papers:` ≠ body citations
- Frontier-axis section present when plan said NONE, or absent when plan said REQUIRED
- Wikilinks to pages not scheduled this round
- Page skeletal relative to the density defaults while the corpus could support more (under the word band, <7 sections, a body section under ~150 words, single-paper major section, zero callouts where assessment exists)

### Stage D — Revisers (parallel)

One reviser per cluster that has any REVISE page (`prompts/reviser.md`). Each reviser:
- Reads the review's fix list
- Re-reads the relevant raw papers for fidelity fixes
- Applies the fixes
- Writes the revised page to `round-N/round-output/<type>/<slug>.md`
- Copies PASS pages from `rewritten-wiki/` to `round-output/` unchanged

After all revisers finish: `round-N/round-output/` contains the final round output, complete.

### End-of-round lint preview

A tmp overlay of `round-N/round-output/` on `wiki/` is linted with `check_links.py` and `validate_frontmatter.py`; results go to `round-N/lint-report.md`. Substantive issues trigger a targeted reviser; deterministic issues are fixed inline.

---

## Phase 5 — Decide on Another Round

If round-count < requested AND review files still flag substantive issues (still-thin, missing-X, shallow-on-Y), the orchestrator starts round N+1 (back to Phase 3). Otherwise → Phase 6.

Round 2 typically:
- Deepens pages flagged thin in round 1
- Adds page types deferred from round 1 (e.g., methods/measures)
- Repairs cross-links across the now-existing page set

Round 3 typically:
- Final polish on remaining REVISE pages
- Gap-fill where round 2 surfaced new needed pages
- Hard cross-link audit

---

## Phase 6 — Finalise

1. Copy the last round's `round-output/` to `final/round-output/`.
2. Show the user a `git diff --stat wiki/` summary before overwriting.
3. Copy `final/round-output/*` into `wiki/`.
4. Full lint:
   ```bash
   python -m py_compile scripts/*.py
   python scripts/check_links.py wiki raw_markdown
   python scripts/check_orphans.py wiki
   python scripts/validate_frontmatter.py wiki
   python scripts/export_metadata.py --output exports/raw-markdown-metadata.json
   ```
5. Update `_index.md` files where new pages were added.
6. Append to `wiki/log.md`:
   ```
   ## [YYYY-MM-DD] wiki-build | <N_rounds> rounds, <N_pages> pages
   - Workspace: agent_tasks/wikipedia-rewrite_<DATE><HHMM>/
   - New papers: <N>
   - Source pages added: <list>
   - Synthesis pages created: <list>
   - Synthesis pages updated: <list>
   - Unresolved (revise cap hit): <list or none>
   - Lint: <pass/issue summary>
   ```
7. Update `wiki/_index.md` "Current Status".

---

## Quality Bar (Synthesis Pages)

Read `.claude/skills/wiki-build/rubric.md` — the single source of truth — before any writing or review. Summary of the bar:

| Criterion | Check |
|---|---|
| Encyclopedic lead | One paragraph, no bullets, no single-paper-only citation |
| Subject-matter backbone | Headings name sub-topics, not papers; no "Paper Claims" section |
| Citation integration | Multi-cite where convergent; name papers only where distinct contribution matters |
| Three knowledge levels | Visible inline (italics, callouts) but not as architecture |
| Coverage | Every `key_sources_ranked` paper appears in body |
| Cross-links | `## See also` section with resolving wikilinks; 12–15 by default |
| Frontier axis | Present iff round plan declared it for this page (the plan's declared frontier-extension axis — e.g. AI-era, replication wave, policy translation — only when corpus supports) |
| Frontmatter | Complete; `papers:` list matches body citations |
| Length | 1700–2200 words typical (up to 2800 for major synthesis); no padding |
| Density / depth | 7–10 sections (counting lead + cross-links; ~5–8 substantive body sections — never split one idea or peel the lead/cross-links into headings to pad the count); each body section ≥150 words; ≥4 papers per major section where corpus allows; 2–4 knowledge-level callouts; 12–15 cross-links; no skeletal sections — *degrade gracefully for a thin corpus, never pad* |
| Non-trivial role | Each cited paper contributes a distinct claim/result/mechanism, not a bare name-drop |
| Raw-paper grounding | Every substantive claim traces to `raw_markdown/papers/<slug>.md` |

---

## Knowledge Separation Within Pages

Every wiki page maintains three claim levels, but **not** as architecture:

| Level | What it is | How to mark inline |
|---|---|---|
| **Paper claim** | What one paper asserts | Inline `[[slug]]` citation |
| **Cross-paper pattern** | Pattern across ≥2 papers | Italicised generalisation + multi-citation in parentheses |
| **Current assessment** | Wiki's current best judgment with date | Short `> **Current assessment (YYYY-MM):** ...` callout |

Do not create separate top-level sections for these. That structure produces the paper-listing format the new pipeline replaces.

---

## Directory Reference

```
literature-wiki/
├── raw_pdfs/                          # immutable source PDFs
├── raw_markdown/
│   ├── papers/<slug>.md               # converted markdown
│   └── metadata/<slug>.json           # sidecar metadata
├── wiki/
│   ├── _index.md
│   ├── log.md
│   ├── sources/<slug>.md              # bibliographic anchors
│   ├── concepts/<slug>.md             # Wikipedia-style synthesis
│   ├── mechanisms/<slug>.md           # Wikipedia-style synthesis
│   ├── methods/<slug>.md              # Wikipedia-style synthesis
│   ├── measures/<slug>.md             # Wikipedia-style synthesis
│   ├── debates/<slug>.md              # Wikipedia-style synthesis
│   ├── synthesis/<slug>.md            # Wikipedia-style cross-cutting
│   ├── templates/                     # page templates
│   └── schema/                        # naming rules, frontmatter, workflows
├── scripts/
│   ├── convert_pdf_to_markdown.py
│   ├── normalize_filename.py
│   ├── check_links.py
│   ├── check_orphans.py
│   ├── validate_frontmatter.py
│   ├── export_metadata.py
│   ├── rebuild_index.py
│   └── pipeline_utils.py
├── exports/
├── agent_tasks/                       # multi-agent workspaces
├── docs/
└── .claude/skills/
    ├── wiki-build/
    │   ├── SKILL.md
    │   ├── rubric.md
    │   └── prompts/
    ├── wiki-query/
    ├── wiki-synthesis/
    └── wiki-update-db/
```

---

## Quick-Reference Checklists

### Per-build checklist

- [ ] `raw_pdfs/` populated with `Author and Author - YYYY - Paper Title.pdf` named PDFs
- [ ] `/wiki-build <n>` invoked
- [ ] Round plan reviewed by user before stage A starts
- [ ] All scope pages in `round-N/round-output/` after stage D
- [ ] `round-N/lint-report.md` shows no broken links and no frontmatter issues
- [ ] Each round in the plan executed
- [ ] `final/round-output/` copied to `wiki/`
- [ ] Full lint passes
- [ ] `wiki/log.md` updated

### Per-page (synthesis) checklist

- [ ] Encyclopedic lead, no bullets
- [ ] Section headings name sub-topics, not papers
- [ ] No "Paper Claims" section
- [ ] Multi-citation where claims converge
- [ ] Inline `[[slug]]` for paper-specific claims
- [ ] Italicised generalisations for cross-paper patterns
- [ ] Short callout block for current assessment
- [ ] Every `key_sources_ranked` paper appears in body
- [ ] Frontmatter `papers:` matches body
- [ ] `## See also` cross-links resolve
- [ ] Frontier section only if plan declared
- [ ] All substantive claims traceable to `raw_markdown/papers/<slug>.md`
