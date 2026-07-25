---
name: wiki-build
description: Use this skill whenever the user wants to build, rebuild, or upgrade the literature wiki from the paper collection — phrases like "/wiki-build", "build the wiki", "rebuild wiki pages", "synthesize the collection", "ingest these papers", "process all PDFs", "make Wikipedia-style pages from the papers", "upgrade wiki coverage", "do a full wiki pass". Orchestrates a multi-round, multi-agent curator → cluster-writer → cluster-reviewer → reviser pipeline that produces true encyclopedic synthesis pages (not paper-listing pages) across the whole collection. Domain-agnostic — adapts to whatever research literature is in `raw_pdfs/` and `raw_markdown/papers/`.
---

# Wiki Build — Multi-Round Multi-Agent Synthesis Orchestrator

You are the **orchestrator**. You do not write wiki pages yourself. You plan the work, spawn subagents in parallel, collect short status summaries from disk, and drive a write → review → revise loop until each page meets the quality bar in `rubric.md`.

The pipeline below is modelled on a working protocol (see "Provenance" at the end) that successfully transformed a paper-listing wiki into a Wikipedia-style synthesis. Keep the protocol's structure; let the planner / curator adapt the content to whatever research domain the paper collection happens to be in.

## What This Skill Produces

A Wikipedia-style literature wiki where each page is an **integrated synthesis** centered on one topic — a concept, debate, mechanism, measure, method, or thematic synthesis — that reads across the whole paper collection in an encyclopedic narrative voice.

**Two output classes:**

| Class | Where | What it is |
|---|---|---|
| **Source pages** | `wiki/sources/<slug>.md` | One per paper. Bibliographic + factual record (research question, model/design, results, mechanisms, methods, cross-links). Built once per new paper. Not the deliverable. |
| **Synthesis pages** | `wiki/concepts/`, `wiki/debates/`, `wiki/mechanisms/`, `wiki/measures/`, `wiki/methods/`, `wiki/synthesis/` | Encyclopedic pages. Each is a focused, integrated treatment of one topic across the full collection. The deliverable. Rebuilt every wiki-build pass. |

Synthesis pages are NOT per-paper summaries, listings of "Paper X says A, Paper Y says B", or annotated bibliographies. Read `rubric.md` before planning.

## Hard Rules (Non-Negotiable)

1. **You never write wiki content yourself.** Every page is produced by a subagent. You only orchestrate.
2. **File handoff only.** Every subagent writes its output to a specific file on disk and returns ≤200 words of status to you. Never let a subagent return a full page in its message.
3. **Run independent subagents in parallel.** In a single tool-call message, spawn all writers at once; same for reviewers; same for revisers.
4. **Specify input AND output paths explicitly** when briefing every subagent.
5. **Confirm files exist on disk** (`ls`) after each phase before moving on.
6. **READ THE RAW PAPER, NOT THE SOURCE PAGE.** Every writer and reviewer must base claims on `raw_markdown/papers/<slug>.md`, never on `wiki/sources/<slug>.md`. Source pages are navigation aids only. This rule is restated in every prompt template.

## Adaptivity (Domain-Agnostic Protocol)

The protocol below is fixed. What flexes with the research domain:

- **What pages exist** — the planner / curator inspects the actual paper collection and decides what concepts, mechanisms, debates, methods, measures, and syntheses deserve standalone pages. No fixed taxonomy.
- **Clustering** — clusters of related pages emerge from the corpus (e.g., "foundational theory", "empirical anchor", "frontier extension"), not from a fixed list. The curator labels clusters.
- **Frontier / extension axis** — optional. If the corpus contains a coherent "frontier" sub-literature (e.g., AI extensions to a classical theory, recent methodological turn, replication crisis literature), the curator marks pages where that axis is required. If not, no such section is added. Do not force one.
- **Section structure of each page** — the curator's outline per page is bespoke to the topic. Concept pages on a formal-theory topic look different from concept pages on a measurement topic.

## Round-Based Execution

```
ROUND 1 — Foundational rewrite of all priority pages
ROUND 2 — Deepen pages flagged thin; add page types deferred from R1 (e.g., methods/measures)
ROUND 3 — Cross-link repair, gap-fill, final polish (only if needed)
FINAL  — Copy round-N/round-output/ to wiki/, run lint, log
```

Default: **2 rounds**. Add round 3 only when round-2 reviews still flag substantive issues. The user may override with `/wiki-build 3` or `/wiki-build 1`.

Each round lives in `agent_tasks/<DATE>-wiki-build/round-N/` and has the same subdirectory structure (see Phase 0).

---

## Phase 0 — Scan and Workspace Setup

1. Get today's date in Beijing time. Call this `<DATE>` (format `YYYYMMDD` for the workspace slug, `YYYY-MM-DD` for log entries).
2. Decide a workspace slug: `wikipedia-rewrite_<DATE><HHMM>` (e.g., `wikipedia-rewrite_2026051713`). Use the timestamp the user invoked the skill.
3. Create the workspace:
   ```
   agent_tasks/<workspace-slug>/
   ├── round-1/
   │   ├── plan.md
   │   ├── page-briefs/        ← Stage A output, one file per page
   │   ├── rewritten-wiki/     ← Stage B writer output (drafts)
   │   ├── reviews/            ← Stage C reviewer output, one file per cluster
   │   ├── round-output/       ← Stage D final output for this round
   │   ├── logs/
   │   └── status/             ← subagent ≤200-word status summaries
   ├── round-2/  (same structure, created in Phase 5)
   ├── round-3/  (only if needed)
   └── final/
       └── round-output/       ← copy from last round; this is what goes into wiki/
   ```
4. Compare `raw_pdfs/` against `wiki/sources/`. Build two lists:
   - `NEW_PAPERS`: PDFs with no source page.
   - `EXISTING_PAPERS`: PDFs that already have a `wiki/sources/<slug>.md`.
5. Write `agent_tasks/<workspace-slug>/scope.md` with: paper counts, scope statement, requested round count, any user-specified narrowing.

If `NEW_PAPERS` is non-empty, run Phase 1 (convert) + Phase 2 (source pages) first. Otherwise skip straight to Phase 3 (round-1 planning).

---

## Phase 1 — Convert New PDFs (deterministic)

For each PDF in `NEW_PAPERS`, run locally (no subagent needed):

```bash
python scripts/normalize_filename.py "<pdf_filename>"
python scripts/convert_pdf_to_markdown.py "raw_pdfs/<pdf>" \
  --output raw_markdown/papers/<slug>.md
```

Eyeball each output: title, authors, ≥3 section headings, references section. Log issues in `agent_tasks/<workspace-slug>/conversion-notes.md`.

---

## Phase 2 — Source Pages (One-Shot per Paper)

Source pages are bibliographic records; they do not need the multi-round Wikipedia-style cycle. Spawn one writer subagent per new paper, all in parallel.

### 2a. Writers (parallel, one per paper)

Use `prompts/source-writer.md`. Fill in:
- `{{SLUG}}`, `{{RAW_MARKDOWN_PATH}}` = `raw_markdown/papers/<slug>.md`
- `{{OUTPUT_PATH}}` = `wiki/sources/<slug>.md`
- `{{STATUS_PATH}}` = `agent_tasks/<workspace-slug>/status/source-<slug>-write.md`
- `{{TEMPLATE_PATH}}` = `wiki/templates/source-template.md`

Spawn ALL writers in a single tool-call message. Cap at 8 parallel; batch larger jobs.

### 2b. Light review (parallel, one per paper)

Use `prompts/source-reviewer.md`. Reviewer checks: frontmatter complete, all sections substantive, wikilinks present, claims traceable to the raw paper. Output to `agent_tasks/<workspace-slug>/source-reviews/<slug>.md` ending with `VERDICT: PASS` or `VERDICT: REVISE`.

### 2c. Revise (parallel)

For REVISE pages, spawn a reviser using `prompts/reviser.md`. Cap at 1 revise round for source pages — they are factual records, not interpretive synthesis. If still REVISE after one round, accept and log.

---

## Phase 3 — Round-N Plan (single planner)

For each round, the orchestrator spawns ONE planner subagent that produces a structured plan for that round.

Use `prompts/round-planner.md`. Fill in:
- `{{ROUND_NUMBER}}`, `{{WORKSPACE_PATH}}`
- `{{PREVIOUS_ROUND_REVIEWS}}` (for rounds ≥2: paths to `round-(N-1)/reviews/`)
- `{{SCOPE_FILE}}` = `agent_tasks/<workspace-slug>/scope.md`

Output: `agent_tasks/<workspace-slug>/round-N/plan.md`. The plan must contain:

```markdown
# Round N Plan — <round purpose>

## Goal of this round
<one-paragraph statement of what this round accomplishes>

## Pages in scope (count)
**Concepts (N):** <slug>, <slug>, ...
**Mechanisms (N):** <slug>, ...
**Debates (N):** <slug>, ...
**Methods (N):** <slug>, ...    ← may be empty in R1
**Measures (N):** <slug>, ...   ← may be empty in R1
**Synthesis (N):** <slug>, ...

## Cluster Map
| Cluster | Theme (label) | Pages (slug + type) |
|---|---|---|
| 1 | <emergent theme> | <2-3 pages> |
| 2 | <emergent theme> | <2-3 pages> |
| ...

(Aim for 6–10 clusters of 2–3 pages each. Each cluster groups pages whose papers and concepts overlap, so one writer can be efficient.)

## Domain Axes (optional, set only if corpus warrants it)
- Frontier extension axis: <e.g., "AI extension", "post-2020 replication wave", "policy translation"> — set to NONE if the corpus has no coherent frontier sub-literature.
- Other axes: <as relevant>

## Mandatory rule for every writer and reviewer
**Read the actual papers, not the source-page summaries.** For every source slug a writer or reviewer engages with, they must open `raw_markdown/papers/<slug>.md` and read the relevant sections. `wiki/sources/<slug>.md` is allowed only as a navigation aid.

## Stages for this round
- Stage A: Curator (1 subagent) — produces 1 brief per scope page in `page-briefs/`
- Stage B: Cluster writers (one per cluster) — drafts to `rewritten-wiki/<type>/<slug>.md`
- Stage C: Cluster reviewers (one per ~2 clusters) — `reviews/cluster-<X>.md`
- Stage D: Revisers (one per cluster with any REVISE) — final to `round-output/<type>/<slug>.md`. PASS pages copied unchanged.

## Hand-off to round N+1 (if any)
<what the next round should address: deepening, new page types, cross-link repair>
```

Show the user a 5–10 line summary of the plan and let them edit `plan.md` before continuing. (Show: page count by type, cluster count, frontier axis decision, any obvious gaps.)

---

## Phase 4 — Round-N Execution

### Stage A — Curator (1 subagent, foreground)

Spawn one curator subagent using `prompts/curator.md`. Inputs:
- `plan.md`
- Full list of scope pages (paths)
- Full list of source pages (`wiki/sources/`) + raw papers (`raw_markdown/papers/`)
- The rubric: `.claude/skills/wiki-build/rubric.md`
- The page-brief template: `.claude/skills/wiki-build/prompts/page-brief-template.md`

Output: one brief per scope page at `round-N/page-briefs/<slug>.md`, plus an `_index.md` master file listing cluster assignments. Each brief contains:

- `page_type`
- `cluster`
- `working_definition` (one paragraph)
- `why_it_matters` (one paragraph)
- `wikipedia_outline` (section list, one-line scope each)
- `key_sources_ranked` (≤10 slugs, each with a one-line rationale + the explicit path `raw_markdown/papers/<slug>.md`)
- `cross_link_targets` (other wiki pages to wikilink)
- `length_target` (words)
- `writing_constraints` (encyclopedic lead; subject-matter backbone; three knowledge levels as callouts not sections; frontier-axis section if applicable; etc.)
- `spot_check_anchors` (3 specific claims per page that the reviewer will verify against the actual paper text)

After the curator finishes, `ls round-N/page-briefs/` to confirm one file per scope page exists. If any are missing, re-spawn for just those.

### Stage B — Cluster Writers (parallel, one per cluster)

For each cluster in the plan, spawn one writer subagent using `prompts/cluster-writer.md`. Each writer is responsible for **all pages in its cluster** (typically 2–3). Inputs per writer:
- The cluster's page briefs (full content)
- The `key_sources_ranked` raw markdown paths for each page
- The rubric
- For UPDATE pages (rounds ≥2): the previous round's `round-output/<type>/<slug>.md`

Output: one full page per brief at `round-N/rewritten-wiki/<type>/<slug>.md`. Frontmatter preserved/updated.

Spawn ALL cluster writers in a single tool-call message. After they all finish, `ls round-N/rewritten-wiki/` recursively to confirm every page exists.

### Stage C — Cluster Reviewers (parallel)

Group clusters into review batches (typically 2 clusters per reviewer, so ~5 pages per reviewer). Spawn one reviewer per batch using `prompts/cluster-reviewer.md`. Each reviewer applies three lenses:

1. **Synthesis quality** — Does it read like a Wikipedia article or like a list? Is the structural backbone the subject matter (not paper-by-paper)?
2. **Fidelity** — Are paper-specific claims accurate? Reviewer spot-checks each page's `spot_check_anchors` against `raw_markdown/papers/<slug>.md` (not source pages).
3. **Coverage and cross-links** — Are all `key_sources_ranked` actually engaged in the text? Do internal wikilinks resolve to pages that exist (or will exist by end of round)?

Output: `round-N/reviews/cluster-<label>.md` with per-page verdict (`PASS` or `REVISE`) and, for REVISE, a concrete fix list (≤8 bullet items per page).

### Stage D — Revisers (parallel, one per cluster with REVISE pages)

For each cluster that has at least one REVISE page, spawn one reviser subagent using `prompts/reviser.md`. The reviser:
- Reads its cluster's review file
- Reads each REVISE page's current draft + brief + raw papers
- Applies the fix list
- Writes the final round-N output to `round-N/round-output/<type>/<slug>.md`
- Copies PASS pages from `rewritten-wiki/<type>/<slug>.md` to `round-output/<type>/<slug>.md` unchanged

After all revisers finish, every scope page must exist at `round-N/round-output/<type>/<slug>.md`. Verify with `ls`.

### End-of-round lint preview

Build a tmp-overlay of round-output on wiki/, then run the link and frontmatter checks:

```python
# Cross-platform overlay: copy wiki/ → temp dir, overlay round-output, lint
import shutil, subprocess, sys, tempfile
from pathlib import Path

WS = "agent_tasks/<workspace-slug>"
R  = "<ROUND>"  # e.g. "round-1"

tmp    = Path(tempfile.mkdtemp())
wiki_tmp = tmp / "wiki"
shutil.copytree("wiki", wiki_tmp)

# Overlay round-output on top of wiki
ro = Path(WS) / R / "round-output"
for src in ro.rglob("*.md"):
    dst = wiki_tmp / src.relative_to(ro)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

report = Path(WS) / R / "lint-report.md"
with open(report, "w") as f:
    subprocess.run([sys.executable, "scripts/check_links.py",
                    str(wiki_tmp), "raw_markdown"], stdout=f)
with open(report, "a") as f:
    subprocess.run([sys.executable, "scripts/validate_frontmatter.py",
                    str(wiki_tmp)], stdout=f)

shutil.rmtree(tmp, ignore_errors=True)
print(f"Lint report written to {report}")
```

If `lint-report.md` shows issues, spawn a targeted reviser to fix them before declaring the round done.

---

## Phase 5 — Decide on Another Round

After round-N completes, the orchestrator reads `round-N/reviews/` and counts:
- Pages that still need substantive work (any reviewer note like "still thin", "missing X", "shallow on Y")
- New page types deferred (e.g., methods/measures planned for R2)
- Cross-link gaps

Decision logic:
- If round-count < requested rounds AND non-trivial issues remain → start round N+1 (back to Phase 3)
- Otherwise → Phase 6

---

## Phase 6 — Finalise (Copy + Lint + Log)

1. Copy the last round's output to `agent_tasks/<workspace-slug>/final/round-output/`.
2. Copy `final/round-output/*` into `wiki/`, replacing the matching files. **Show the user a diff summary** (page count by type) before this step — `git diff --stat wiki/` so they see the scope of changes.
3. Run the full lint suite:
   ```bash
   python -m py_compile scripts/*.py
   python scripts/check_links.py wiki raw_markdown
   python scripts/check_orphans.py wiki
   python scripts/validate_frontmatter.py wiki
   python scripts/export_metadata.py --output exports/raw-markdown-metadata.json
   ```
4. Fix deterministic issues (frontmatter, indexes). For substantive issues, spawn one targeted reviser.
5. Update `_index.md` files where new pages were added.
6. Append to `wiki/log.md`:
   ```
   ## [YYYY-MM-DD] wiki-build | <N_rounds> rounds, <N_pages> pages
   - Workspace: agent_tasks/<workspace-slug>/
   - New papers: <N>
   - Source pages added: <list>
   - Synthesis pages created: <list>
   - Synthesis pages updated: <list>
   - Unresolved (capped after revise): <list or none>
   - Lint: <pass/issue summary>
   ```
7. Update `wiki/_index.md` "Current Status" block.

---

## Reporting Back to the User

After Phase 6, write a short summary:

```
Wiki build complete (N rounds).
- New papers ingested: N
- Source pages added: N
- Synthesis pages: <new>/<updated>/<kept>
- Unresolved: <list or none>
- Workspace: agent_tasks/<workspace-slug>/
- Lint: <pass/issues>
```

Do not paste page content. Point the user at files.

---

## When to Run This Skill

- After dropping new PDFs into `raw_pdfs/` ("ingest these papers")
- When the user wants a deep rebuild ("re-synthesize the wiki", "rebuild the concept layer", "upgrade wiki coverage")
- For an explicit n-round pass ("/wiki-build 3")

For one-off "save this insight" requests, use `wiki-synthesis`. For lint-only passes, use `wiki-update-db`. For questions, use `wiki-query`.

---

## Reference Files (Inside This Skill)

| File | Used by |
|---|---|
| `rubric.md` | All writers and reviewers — defines the Wikipedia-style quality bar |
| `prompts/source-writer.md` | Phase 2 source-page writer |
| `prompts/source-reviewer.md` | Phase 2 source-page reviewer |
| `prompts/round-planner.md` | Phase 3 round planner |
| `prompts/curator.md` | Phase 4 Stage A — per-page brief writer |
| `prompts/page-brief-template.md` | The schema the curator must fill in for every page |
| `prompts/cluster-writer.md` | Phase 4 Stage B — cluster writer |
| `prompts/cluster-reviewer.md` | Phase 4 Stage C — cluster reviewer |
| `prompts/reviser.md` | Phase 2 Stage D and Phase 4 Stage D revisers |

Open each prompt file when invoking the corresponding role. Pass the **filled-in** prompt as the subagent's `prompt` argument — never a pointer to the template.

---

## Provenance

This protocol is modeled on a working multi-round Wikipedia-style rewrite that was successfully applied to a literature wiki on the theory of the firm. The original used: per-page briefs by a curator, cluster assignment with 2–3 pages per writer, three-lens cluster review, and an explicit "read raw markdown, not source pages" rule. We keep that structure and generalize the domain-specific details (cluster themes, frontier extension axis, section templates) so the planner / curator can adapt to any research literature.
