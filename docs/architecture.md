# Architecture Reference: narrative-wiki

**Version:** 2026-04
**Status:** Authoritative reference for developers and researchers adapting or extending this system.

---

## 1. Design Philosophy

### 1.1 The Wiki Core Is Not a RAG System

At its core, narrative-wiki is not a retrieval-augmented generation (RAG) system. Knowledge is pre-structured into typed pages (concepts, mechanisms, debates, synthesis) that an LLM agent navigates directly using explicit router files (`_index.md`) and wikilinks — `/wiki-build` and `/wiki-query` use no vector store or embedding index. This means:

- Query quality depends on how well the wiki is organized, not on embedding quality.
- Cross-paper patterns are explicit, written-out prose — not inferred at query time from raw text chunks.
- The wiki degrades gracefully without any external infrastructure.

A retrieval backend does exist, but only as an **optional, additive layer** that sits on top of the finished wiki for the web Chat experience (see §1.5). It does not feed the build or the agent-native query path.

### 1.2 Not a Summary Archive

Adding a paper to the wiki does not simply mean creating a summary page. The build pipeline produces **Wikipedia-style synthesis pages** — concept, mechanism, debate, method, measure, and cross-cutting synthesis pages — that integrate evidence from across the whole collection on each topic. Source pages exist as bibliographic anchors, not as the primary deliverable. The goal is encyclopedic, cumulative understanding organised by topic — not a stack of paper summaries.

### 1.3 AI-Native Design

The wiki is designed to be navigated, queried, and maintained primarily by LLM agents rather than by search engines or human browsing. This shapes several structural decisions:

- `CLAUDE.md` at the root and within each major directory provides operating instructions visible in the LLM's context window.
- `_index.md` files at every directory level serve as router documents that tell an agent what pages exist and what they cover, reducing the need for exhaustive file listing.
- Frontmatter YAML provides machine-parseable metadata (slug, title, authors, year, status, tags) on every canonical page.
- Page type conventions (sources, concepts, mechanisms, etc.) give an agent a reliable mental model of where different kinds of knowledge live.

### 1.4 Separation of Concerns: Three Layers

The repository enforces a strict three-layer separation:

| Layer | Directory | Role | Editability |
|---|---|---|---|
| Raw | `raw_pdfs/` | Immutable source of truth | Never edited |
| Parse | `raw_markdown/` | Faithful machine-readable conversion | Only corrected for extraction failures |
| Knowledge | `wiki/` | LLM-maintained structured understanding | Actively maintained |

No layer bypasses the one below it. Academic judgments are never embedded in the parse layer. Provenance is always traceable downward from any wiki page to its source PDF.

### 1.5 Optional Layers on Top of the Wiki

Two optional layers sit **on top of** the finished `wiki/` and leave the three-layer pipeline above unchanged:

- **Search/Browse/Chat frontend** (`web/`, Next.js) — Search `/search` (client-side MiniSearch over `web/public/wiki-index.json`, built by `python scripts/export_wiki.py`), Browse `/wiki` (category sidebar · reading column · on-page TOC), and a page viewer `/wiki/[slug]` that reads the wiki from the filesystem with no backend. Chat `/` talks to the agentic backend. See [search-and-browse.md](search-and-browse.md) and [web-frontend.md](web-frontend.md).
- **Agentic chat backend** (`rag/`, one OpenAI-compatible endpoint via `RAG_OPENAI_BASE_URL`, default local Ollama `/v1`) — answers ONLY by agentic filesystem navigation (no embeddings, no index build); used only by the web Chat tab. See [rag-backend.md](rag-backend.md).

Both are served via `/wiki-serve` / the `Makefile` and deployed per [deployment.md](deployment.md). They are strictly downstream consumers: `/wiki-build` and `/wiki-query` never depend on them, and the wiki remains fully usable without either.

---

## 2. Three-Layer Model

### 2.1 Layer 1: raw_pdfs/

`raw_pdfs/` holds the original source PDFs exactly as obtained. No renaming, no editing, no annotation.

- Original filenames are preserved even when they are inconsistent or verbose.
- This layer is never modified after a file is deposited.
- It functions as the canonical evidentiary anchor: any claim made in the wiki must be traceable to a file in this directory.

### 2.2 Layer 2: raw_markdown/

`raw_markdown/` holds machine-readable conversions of the source PDFs. The default conversion tool is [markitdown](https://github.com/microsoft/markitdown), which produces structured Markdown from PDFs. Conversion is done without academic interpretation — the parse layer is faithful to the source, not editorialized.

**Subdirectory structure:**

```
raw_markdown/
  papers/          # One .md file per paper, slug-named
  metadata/        # One .json sidecar per paper with structured metadata
  assets/          # Extracted figures, tables, or other binary assets (if any)
```

**Metadata sidecar format** (`metadata/<slug>.json`):

Each paper's sidecar JSON records the following fields at minimum:

| Field | Description |
|---|---|
| `slug` | Canonical slug, matching the filename base |
| `title` | Paper title as extracted |
| `authors` | List of author names |
| `year` | Publication year |
| `word_count` | Approximate word count of converted markdown |
| `heading_count` | Number of headings extracted |
| `sha256` | SHA-256 hash of the source PDF |
| `conversion_tool` | Tool used (e.g., `markitdown`) |
| `conversion_notes` | Any extraction failures, warnings, or manual corrections |

**Editing policy:** Manual edits to `raw_markdown/papers/` are permitted only to correct obvious extraction failures (garbled equations, broken table structure, truncated references). Content-level edits or paraphrasing are not permitted.

### 2.3 Layer 3: wiki/

`wiki/` is the canonical knowledge layer. It is maintained by LLM agents following the rules in this repository. All pages use Obsidian-flavored Markdown with YAML frontmatter.

**Top-level structure:**

```
wiki/
  _index.md          # Wiki-level router document
  log.md             # Chronological record of all ingest and synthesis operations
  sources/           # One page per paper
  concepts/          # Cross-paper concept definitions
  mechanisms/        # Causal mechanism pages
  methods/           # Research design and method pages
  measures/          # Measurement and operationalization pages
  debates/           # Structured competing/contradicting claim records
  synthesis/         # Higher-level cumulative interpretations
  templates/         # Page templates for each page type
  schema/            # Naming rules, frontmatter schema, workflow documentation
```

---

## 3. Wiki Page Type Hierarchy

Each page type has a distinct role and is not interchangeable with others. The **synthesis page types** (concept, mechanism, method, measure, debate, synthesis) are written as **Wikipedia-style articles** — integrated, encyclopedic, subject-matter-organised — and are the wiki's primary deliverable. **Source pages** are bibliographic records per paper, used as navigation anchors. Confusing types degrades the wiki's navigability.

### 3.1 sources/

One page per paper. Paper-specific. Bibliographic record only. Contains:

- YAML frontmatter (slug, title, authors, year, venue, tags, status, raw_markdown)
- Research question, model/design, main results, mechanisms identified, methods, measures, concepts engaged, connection to debates
- Wikilinks out to relevant synthesis pages
- Provenance link to the corresponding `raw_markdown/papers/` file

Source pages record what a paper does. They are **not** the wiki's encyclopedic interpretation — that's the synthesis pages' job.

### 3.2 concepts/

Wikipedia-style concept pages. One concept per page. Created when a theoretical or empirical construct is substantively engaged by ≥2 papers in the corpus.

A concept page is an encyclopedic article that integrates the literature on the concept:
- Encyclopedic lead paragraph (defines + situates)
- Sub-topic / sub-question sections that integrate multiple papers per section
- Formal model where applicable
- Empirical synthesis across the field
- Tensions and refinements
- Optional frontier-extension section
- Open questions
- See also

NOT a list of "what each paper says about the concept".

### 3.3 mechanisms/

Wikipedia-style mechanism pages. One causal channel per page. Structural backbone is the channel itself (initial condition → intermediate → outcome), with micro-foundations, formal representation, empirical signatures, scope conditions, and failure modes integrated across the literature.

### 3.4 methods/

Wikipedia-style method pages. One methodological approach per page (e.g., "vignette experiment", "dictator game", "regression discontinuity"). Covers standard implementation, variants, what the method can and cannot answer, common pitfalls, and any frontier methodological developments.

### 3.5 measures/

Wikipedia-style measure pages. One operationalization per page. Covers standard elicitation, variants used in the literature, validation evidence, known biases, comparability across studies.

### 3.6 debates/

Wikipedia-style debate pages. One precise disagreement per page. Structure: the question, position A (integrated narrative), position B (integrated narrative), where the disagreement actually sits, empirical anchors, attempts at unification, current state.

### 3.7 synthesis/

Cross-cutting synthesis pages — the wiki's higher-level interpretive layer. Used for themes that pull together multiple concepts / mechanisms / debates and don't fit any one page type. Most editorially demanding; must explicitly distinguish established cross-paper findings from open cross-paper patterns.

### 3.8 templates/

Wikipedia-style page templates for each page type. The curator's per-page brief produced in `/wiki-build` takes precedence — templates are starting outlines, not fixed structures.

### 3.9 schema/

Naming conventions, frontmatter schema, workflow contracts. See `scale-up-rules.md` for batch sizes and lint cadence.

---

## 4. Knowledge Separation Rule

Every synthesis page distinguishes three claim levels — but **not** as architecture. The levels appear **inline**, never as separate top-level sections.

| Level | What it is | How to mark inline |
|---|---|---|
| **Paper claim** | What a specific paper asserts | Inline `[[slug]]` next to the claim |
| **Cross-paper pattern** | Pattern across ≥2 papers | Italicised generalisation with multi-citation in parentheses |
| **Current assessment** | Wiki's current best judgment, with date | Short `> **Current assessment (YYYY-MM):** ...` callout |

A section titled "Paper Claims" or "Cross-Paper Patterns" is an automatic REVISE trigger (see `.claude/skills/wiki-build/rubric.md`). The old version of the wiki did separate these into top-level sections and the result was paper-listing pages, not encyclopedic synthesis. The new pipeline keeps the levels visible inline so the page reads as a Wikipedia article while the provenance of every claim is still traceable.

### 4.1 Paper Claim (inline)

Example: "Asset specificity raises the optimal degree of vertical integration ([[grossman-and-hart-1986]])."

### 4.2 Cross-Paper Pattern (inline)

Example: "*Across two decades of empirical work, asset specificity is the most robust predictor of integration* ([[lafontaine-and-slade-2007]]; [[acemoglu-aghion-and-griffith-2010]]; [[forbes-and-lederman-2009]])."

### 4.3 Current Assessment (callout)

Example:

```markdown
> **Current assessment (2026-05):** The empirical evidence linking asset specificity to integration is well-established. The open question concerns whether AI-mediated coordination compresses the specificity gradient and erodes this prediction.
```

---

## 5. Navigation Architecture

### 5.1 Entry Points for Agents

An LLM agent entering this repository cold should follow this path:

1. Read `CLAUDE.md` at the root — operating rules and layer descriptions.
2. Read `_index.md` at the root — global navigation map.
3. Read `wiki/_index.md` — wiki-level router listing active pages by type.
4. Read per-directory `_index.md` before opening individual pages within that directory.

This four-step entry protocol is designed to minimize unnecessary file reads while giving the agent sufficient context to route queries correctly.

### 5.2 Router Files (_index.md)

Every major directory contains an `_index.md` that lists:

- What pages exist in the directory
- One-line descriptions of each page
- Status indicators (stub, active, needs-update)
- Notable cross-links or thematic groupings

Router files are updated by agents after every ingest or synthesis pass that adds or substantially modifies pages within the directory.

### 5.3 Provenance Chain

Every claim made in a synthesis or concept page must be traceable downward through this chain:

```
synthesis page
  -> source page (wiki/sources/<slug>.md)
    -> raw markdown page (raw_markdown/papers/<slug>.md)
      -> raw PDF (raw_pdfs/<original-filename>.pdf)
```

Wikilinks enforce the upper part of this chain. The metadata sidecar (`raw_markdown/metadata/<slug>.json`) records the SHA-256 hash that ties a parsed file to its source PDF.

Agents and developers should be able to follow any claim from a synthesis statement all the way to the passage in the original PDF that supports it.

### 5.4 Internal Linking Standards

All internal links use Obsidian wikilink syntax:

- Page links: `[[Page Name]]` or `[[slug]]`
- Section links: `[[Page Name#Section Heading]]`
- Embeds: `![[Note Name]]` or `![[image.png]]`

Standard Markdown relative links (`[text](../path/to/file.md)`) are used only when linking to files outside the wiki layer (e.g., linking to a raw_markdown file from a source page).

---

## 6. Automation Boundary

The system enforces a strict boundary between scripted operations and LLM operations.

### 6.1 What Scripts Do

Scripts handle deterministic, non-judgmental tasks only:

| Script | Task |
|---|---|
| `check_links.py` | Detect broken wikilinks and dead internal references |
| `check_orphans.py` | Detect pages unreachable from any router file |
| `validate_frontmatter.py` | Check required YAML fields are present and well-formed |
| `export_metadata.py` | Export structured metadata to `exports/raw-markdown-metadata.json` |

Scripts run after every batch of three or more papers ingested, and as part of the monthly maintenance pass.

**Maintenance sequence:**

```bash
python -m py_compile scripts/*.py
python scripts/check_links.py wiki raw_markdown
python scripts/check_orphans.py wiki
python scripts/validate_frontmatter.py wiki
python scripts/export_metadata.py --output exports/raw-markdown-metadata.json
```

### 6.2 What LLM Agents Do

LLM agents handle all tasks that require academic judgment:

- Deciding which concept, mechanism, or debate pages a paper is relevant to
- Writing cross-paper pattern claims
- Upgrading stubs to active pages
- Authoring or revising synthesis pages
- Identifying when a new concept or mechanism page is warranted
- Assessing conflicting evidence across papers

### 6.3 What Neither Does

No automated process — script or LLM — should make citation decisions, fabricate claims, or modify `raw_pdfs/`. These are inviolable constraints.

---

## 7. Slug Naming Convention

### 7.1 Format

The canonical slug format is:

```
author-and-author-year-short-title
```

- All lowercase.
- Kebab-case (hyphens only, no underscores, no spaces).
- ASCII characters only — transliterate non-ASCII author names.
- "and" separates author surnames; list only first two authors for papers with three or more authors (e.g., `kubin-and-colleagues-2021-...` or simply `kubin-et-al-2021-...`).
- Year is four digits.
- Short title captures the main noun phrase of the title — typically three to six words, enough to be uniquely identifying.

**Example:**

```
eliaz-and-spiegler-2020-a-model-of-competing-narratives
```

### 7.2 Cross-Layer Consistency

The slug must be identical across all three locations where a paper appears:

1. `raw_markdown/papers/<slug>.md`
2. `raw_markdown/metadata/<slug>.json`
3. `wiki/sources/<slug>.md`

All wikilinks to a source page must use this slug. Inconsistent slugs break provenance traceability and cause link-checking failures.

### 7.3 Slug Stability

Once a slug is assigned and the paper is fully integrated, it must not be changed. Changing a slug requires updating every wikilink, every metadata reference, and every router file that cites it — a high-cost operation with no academic benefit.

---

## 8. Build Workflow Summary

The wiki is built and rebuilt by `/wiki-build`, a multi-round, multi-agent orchestrator. The full pipeline is detailed in `docs/pipeline.md` and in `.claude/skills/wiki-build/SKILL.md`. The summary:

1. **Phase 0** — Workspace created at `agent_tasks/wikipedia-rewrite_<DATE><HHMM>/`. Scan `raw_pdfs/` for new papers.
2. **Phase 1** — Convert new PDFs to `raw_markdown/papers/<slug>.md` (deterministic).
3. **Phase 2** — One parallel writer subagent per new paper produces a source page at `wiki/sources/<slug>.md`. A light reviewer pass follows.
4. **Phase 3** — A planner subagent produces `round-N/plan.md` listing scope pages, cluster assignments (6–10 clusters of 2–3 pages each), and the optional frontier-extension axis.
5. **Phase 4** — Round execution: curator writes per-page briefs → parallel cluster writers draft Wikipedia-style pages → parallel cluster reviewers apply three lenses (synthesis quality / fidelity / coverage) → parallel revisers apply fix lists.
6. **Phase 5** — Decide whether to run another round (default cap 2; max 3).
7. **Phase 6** — Copy final round-output to `wiki/`, run full lint, append to `wiki/log.md`.

All subagents write outputs to disk and return ≤200-word status summaries. The orchestrator never writes wiki content itself.

**Round count policy:** 1 round for very small corpora (≤6 papers); 2 rounds (default) for 7–20 papers; 2–3 rounds for larger corpora. Lint runs as part of Phase 6 of every build.

---

## 9. File and Directory Map

```
narrative-wiki/
  CLAUDE.md                        # LLM operating rules (root)
  _index.md                        # Global navigation for agents
  TODO.md                          # Master build checklist
  raw_pdfs/                        # Layer 1: immutable source PDFs
  raw_markdown/
    papers/                        # Layer 2: converted markdown
    metadata/                      # Layer 2: JSON metadata sidecars
    assets/                        # Layer 2: extracted assets (if any)
  wiki/
    _index.md                      # Wiki-level router
    log.md                         # Build, synthesis, lint log
    sources/                       # Bibliographic anchor pages (one per paper)
    concepts/                      # Wikipedia-style concept pages
    mechanisms/                    # Wikipedia-style mechanism pages
    methods/                       # Wikipedia-style method pages
    measures/                      # Wikipedia-style measure pages
    debates/                       # Wikipedia-style debate pages
    synthesis/                     # Cross-cutting synthesis pages
    templates/                     # Wikipedia-style page templates
    schema/                        # Naming, frontmatter, workflow contracts
  scripts/
    check_links.py
    check_orphans.py
    validate_frontmatter.py
    export_metadata.py
    rebuild_index.py
    normalize_filename.py
    convert_pdf_to_markdown.py
    pipeline_utils.py
  exports/
    raw-markdown-metadata.json     # Exported metadata (auto-generated)
  agent_tasks/                     # Multi-agent workspaces (per /wiki-build run)
  docs/
    architecture.md                # This document
    pipeline.md, skills-reference.md, quick-start.md, ...
  .claude/
    skills/                        # Repo-local agent skills
      wiki-build/
        SKILL.md
        rubric.md                  # Wikipedia-style quality bar
        prompts/                   # Subagent prompt templates
      wiki-query/
      wiki-synthesis/
      wiki-update-db/
```

---

*This document is maintained by the repository owner. Update it when structural decisions change. Do not auto-generate this file from scripts.*
