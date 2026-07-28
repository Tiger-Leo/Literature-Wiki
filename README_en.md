# 📚 Literature Wiki

[![中文](https://img.shields.io/badge/Readme-中文-red)](README.md)

A ready-to-use template for building an AI-native literature wiki from a collection of academic PDFs — using Claude Code as the orchestrator that builds and maintains it via a multi-round, multi-agent pipeline.

> **Inspired by** [karpathy/llm-wiki](https://github.com/karpathy/llm-wiki): *"Instead of just retrieving from raw documents at query time, the LLM incrementally builds and maintains a persistent wiki… The knowledge is compiled once and then kept current, not re-derived on every query."*

---

## ⚡ Quick Commands

> Frequently-used commands, placed up front for easy reference.

### One-time Setup

```powershell
# Link your PDF directory to the project. Replace <your-pdf-dir> with your actual path.
# Examples: e:\Papers, D:\literature\journals, /home/user/papers, etc.
python scripts/link_pdfs.py "<your-pdf-dir>" --mode manifest
```

### PDF Management (external PDFs — no copying or moving source files)

```powershell
# Link an external PDF directory (generates the path-mapping manifest)
python scripts/link_pdfs.py "<your-pdf-dir>" --mode manifest

# Exclude subdirectories you don't want to scan (repeatable)
python scripts/link_pdfs.py "<your-pdf-dir>" --mode manifest --exclude "<your-pdf-dir>\unwanted-folder"

# Batch convert all PDFs via MinerU cloud API (high quality)
python scripts/link_pdfs.py "<your-pdf-dir>" --mode manifest --convert

# Incremental: convert only newly-added PDFs (daily use)
python scripts/link_pdfs.py "<your-pdf-dir>" --mode manifest --convert --new-only

# Convert a single PDF
python scripts/convert_pdf_to_markdown.py "Author and Author - YYYY - Title.pdf" --converter mineru --overwrite
```

### Zotero Semantic Search

```powershell
# Incrementally update semantic search database (run after adding new papers; auto-runs when project opened after 10:00 PM Monday, with fulltext extraction)
zotero-mcp update-db --fulltext

# Check database status
zotero-mcp db-status

# Force full rebuild (use when switching embedding models or repairing the database)
zotero-mcp update-db --force-rebuild

# Incremental update with fulltext extraction (more comprehensive, slower)
zotero-mcp update-db --fulltext
```

#### Auto-Update Mechanism

> The semantic search database auto-update runs via a **Claude Code SessionStart hook**. Every time you open a Claude Code session in this project, it checks whether it's Monday after 10:00 PM and the update hasn't been done this ISO week — if so, it launches `zotero-mcp update-db --fulltext` in the background. Runs at most once per week.

**How it works:**

1. Open a Claude Code session in this project
2. `SessionStart` hook fires → runs `scripts/auto-update-db.ps1`
3. Script checks: (a) Is it Monday? (b) ≥ 22:00 Beijing time? (c) Already done this week?
4. All three true → background launch `zotero-mcp update-db --fulltext`, write `.cache/zotero-db-update-week.txt`
5. Update runs in background; session not blocked

**Prerequisites:**

| Condition | Notes |
|---|---|
| **Zotero desktop running** | Local mode (`ZOTERO_LOCAL: true`) requires Zotero desktop. Recommended: add Zotero to startup |
| **Internet access** | The embedding API (SiliconFlow `BAAI/bge-m3`) needs external network |
| **Hook configured** | `SessionStart` hook is configured in project `.claude/settings.local.json` |

**Manual run (bypasses auto mechanism):**

```powershell
zotero-mcp update-db              # incremental update
zotero-mcp update-db --fulltext   # with fulltext extraction
zotero-mcp update-db --force-rebuild  # full rebuild
```

**Troubleshooting:**

- Auto-update not triggered → check Monday + after 22:00 + first session this week; inspect `.cache/zotero-db-update-week.txt`
- Hook not executing → verify `hooks.SessionStart` config exists in `.claude/settings.local.json`
- Update failed → run `zotero-mcp update-db` manually; ensure Zotero desktop is running
- View background update log: `Get-Content .cache/zotero-db-update.log`

### Wiki Build & Maintenance

```bash
/wiki-build          # Default 2-round multi-agent build
/wiki-build 3        # 3 rounds for deeper corpora
/wiki-query          # Answer research questions from the wiki layer
/wiki-synthesis      # Save a one-off insight as a single page
/wiki-update-db      # Lint, validate, and maintain the wiki
/wiki-serve          # Build search index and serve web UI
```

### Validation Scripts

```bash
python -m py_compile scripts/*.py                         # Compile check
python scripts/check_links.py wiki raw_markdown           # Broken links
python scripts/check_orphans.py wiki                      # Orphan pages
python scripts/validate_frontmatter.py wiki               # Frontmatter validation
python scripts/export_wiki.py --wiki-dir wiki             # Export search index
```

### Check Converter Source

```bash
# Show which converter was used for each markdown file (mineru / markitdown / pdftotext)
python -c "import json,glob;[print(f'{json.load(open(f))[\"canonical_slug\"]:55s} {json.load(open(f))[\"conversion_tool\"]}') for f in sorted(glob.glob('raw_markdown/metadata/*.json'))]"
```

---

## 🧭 What Is This?

An **AI-native literature wiki** that transforms a collection of academic PDFs into a set of focused **Wikipedia-style synthesis pages** — each centered on one topic (concept, debate, mechanism, measure, method, or theme) and integrating evidence from across the whole collection.

**Not** per-paper summaries. **Not** annotated bibliographies. **Not** "Paper X says A, Paper Y says B" listings. The wiki reads like an encyclopedia of the literature, organised by topic.

The architecture is fully domain-agnostic and works for any academic research area. **Cross-platform** — macOS, Linux, and Windows (PowerShell) are all supported.

---

## ✨ New: Read Your Wiki in a Browser — Search · Browse · Chat

The template now ships an **optional web layer** on top of the build pipeline — three surfaces over the same `wiki/`:

- 🔎 **Search** (`/search`) — instant client-side full-text search (MiniSearch) over every page. No backend, no AI.
- 📖 **Browse** (`/wiki`) — a **two-pane layout**: a left category sidebar (collapsible by layer, counts, active highlight, search box; a mobile slide-in drawer), a center reading column rendering the `wiki/` markdown (wikilinks, callouts, KaTeX) straight from the filesystem, and a right "On this page" TOC on desktop. No backend, no AI.
- 💬 **Chat** (`/`) — optional agentic chat backend talking to one OpenAI-compatible endpoint (`RAG_OPENAI_BASE_URL`), defaulting to local Ollama's `/v1` (swap in any hosted model), that streams cited answers grounded in your wiki; its thread-history sidebar is persistent on desktop and a slide-in drawer on mobile.

These layers are **purely additive** — the `/wiki-build` pipeline is unchanged, and Search + Browse work fully offline even when the Chat backend is absent. See [docs/search-and-browse.md](docs/search-and-browse.md), [docs/web-frontend.md](docs/web-frontend.md), [docs/rag-backend.md](docs/rag-backend.md), and [docs/deployment.md](docs/deployment.md).

---

## 🎯 Core Idea: Not a RAG System, Not a Summary Archive

Most literature management tools fall into one of two categories:

- **PDF archives** — files stored by folder, searched when needed.
- **RAG systems** — documents chunked and embedded, retrieved at query time to generate an answer.

**literature-wiki is neither.** It is a persistent, evolving wiki where each build pass produces focused synthesis pages, written and reviewed by multiple agents in parallel, that integrate the whole collection on each topic. The wiki is the primary interface — not the PDFs, not an embedding index.

When you ask "how do different papers conceptualize concept X?" — the answer is already pre-organized as a Wikipedia-style page at `wiki/concepts/concept-x.md`, with an encyclopedic lead paragraph, sub-topic sections that integrate multiple papers, and explicit current-assessment callouts. No retrieval step needed.

---

## 🏗️ Three-Layer Architecture

```
raw_pdfs/
    └── Immutable source PDFs. Never edited. Source of truth.

raw_markdown/
    ├── papers/      ← Faithful PDF-to-markdown conversions (via markitdown)
    ├── metadata/    ← Structured sidecar data extracted at conversion time
    └── assets/      ← Images and attachments extracted from PDFs

wiki/
    ├── sources/     ← Per-paper bibliographic record (anchor, not deliverable)
    ├── concepts/    ← Wikipedia-style concept pages (deliverable)
    ├── mechanisms/  ← Wikipedia-style mechanism pages
    ├── methods/     ← Wikipedia-style method pages
    ├── measures/    ← Wikipedia-style measure pages
    ├── debates/     ← Wikipedia-style debate pages
    ├── synthesis/   ← Higher-level cross-cutting pages
    ├── templates/   ← Page templates (Wikipedia-style outlines)
    ├── schema/      ← Naming rules, frontmatter specs, build workflow
    └── log.md       ← Append-only history of all build/synthesis/lint events
```

**Layer responsibilities:**

- `raw_pdfs/` — preservation only. LLMs never write here.
- `raw_markdown/` — faithful machine-readable conversion. Authoritative for all substantive claims on synthesis pages.
- `wiki/` — structured knowledge. The **synthesis pages** are the primary interface for queries; **source pages** are bibliographic anchors only.
- `scripts/` — deterministic utilities (validation, indexing, export, normalization). No academic judgment.

---

## ⚙️ Four Core Operations

| Operation | Skill | What it does |
|---|---|---|
| **build** | `/wiki-build` | Multi-round, multi-agent build/rebuild. Plans the page set from the corpus, writes pages in parallel by cluster, reviews them in parallel, revises until they hit the quality bar, then lints. Domain-agnostic — cluster themes emerge from the actual papers. |
| **query** | `/wiki-query` | Answer research questions from the synthesis layer first; drill to source pages or raw markdown only when needed. |
| **synthesis** | `/wiki-synthesis` | Save a single one-off insight as one wiki page (concept, debate, mechanism, or synthesis) — the surgical one-page-at-a-time complement to `/wiki-build`. |
| **update-db** | `/wiki-update-db` | Lint and health-check — broken-link detection, orphan-page detection, frontmatter validation, metadata export. |

**Usage rhythm:**

- After dropping new PDFs in `raw_pdfs/` → `/wiki-build`
- Answering research questions → `/wiki-query`
- After a discussion that produced a non-obvious insight → `/wiki-synthesis`
- Monthly, and after every major build → `/wiki-update-db`

---

## 🤖 The Multi-Agent Build Pipeline

`/wiki-build` is the centerpiece. It runs as a round-based, file-handoff orchestrator:

```
Phase 0  Scan & workspace setup
Phase 1  PDF → raw_markdown for new papers
Phase 2  Source pages — parallel writers, then light review
Phase 3  Round plan — single planner subagent produces page list with clusters
Phase 4  Round execution
           Stage A: Curator (1 subagent) — page briefs with outlines & spot-checks
           Stage B: Cluster writers (parallel) — Wikipedia-style page drafts
           Stage C: Cluster reviewers (parallel) — three-lens review with verdicts
           Stage D: Revisers (parallel) — apply fix lists; PASS pages pass through
         Repeat for round 2 (deepen, add deferred page types) and round 3 (polish) as needed
Phase 5  Decide whether to start another round
Phase 6  Finalise — copy round-output to wiki/, run full lint, update indices
```

All intermediate artefacts live in `agent_tasks/wikipedia-rewrite_<DATE><HHMM>/`. Subagents communicate by writing files; the orchestrator collects ≤200-word status summaries.

The pattern is modelled on a working protocol that successfully rewrote a paper-listing wiki into a Wikipedia-style synthesis ([provenance noted in the skill SKILL.md](.claude/skills/wiki-build/SKILL.md#provenance)).

---

## 🧠 Key Design Principles

### Separation of roles

> **LLM (orchestrator)** plans, spawns subagents, collects status, decides on revise/round continuation. Never writes wiki content itself.
>
> **LLM (subagents)** curate briefs, write pages, review pages, revise pages — file handoff only, ≤200-word status returns.
>
> **Scripts** validate frontmatter, check links, detect orphans, export metadata — deterministic only, no academic judgment.
>
> **Researcher** sets research direction, picks papers, edits the round plan if the clustering is off, trust-calibrates the final pages.

### Wikipedia-style synthesis, not paper-listing

Every synthesis page meets these non-negotiables (full rubric at `.claude/skills/wiki-build/rubric.md`):

- **Encyclopedic lead paragraph** — defines the topic, says why it matters, previews the page. No bullets.
- **Subject-matter backbone** — section headings name sub-topics, sub-questions, formal-model components — **not papers**. No "Paper Claims" section.
- **Integrated citations** — multi-cite where claims converge; name papers in flow only when their distinct contribution matters.
- **Three knowledge levels visible but not dominant** — paper claims via inline `[[slug]]`, cross-paper patterns via italicised generalisations, current assessment via short callout blocks.

### Read the raw paper, not the source page

The wiki distinguishes three claim levels:

1. **Paper claim** — what a specific paper asserts. Inline `[[slug]]` citation.
2. **Cross-paper pattern** — pattern across ≥2 papers. Italicised generalisation with multi-citation.
3. **Current assessment** — the wiki's current judgment. Short callout block with a date.

These levels are visible inline but **never** become separate top-level sections — keeping them separate as architecture is what produced the paper-listing format we replaced.

Every writer and reviewer reads `raw_markdown/papers/<slug>.md`, never bases substantive claims on `wiki/sources/<slug>.md`. Source pages are derived summaries; raw markdown is authoritative.

### Domain adaptivity

The build protocol is fixed. What flexes with the research domain:

- **What pages exist** — the planner inspects the actual corpus.
- **Cluster themes** — emergent from the corpus, not pre-set.
- **Frontier / extension axis** — optional. Only included when the corpus contains a coherent frontier sub-literature (e.g., AI-era extensions, post-2020 replication wave). Not forced.

---

## 🗂️ Table of Contents

| Document | Contents |
|---|---|
| [docs/llm-wiki.md](docs/llm-wiki.md) | Original inspiration by Andrej Karpathy |
| [docs/architecture.md](docs/architecture.md) | Design principles, layer model, rationale |
| [docs/quick-start.md](docs/quick-start.md) | Setup + first build walkthrough |
| [docs/pipeline.md](docs/pipeline.md) | Complete PDF-to-wiki pipeline, step by step |
| [docs/wiki-structure.md](docs/wiki-structure.md) | Wiki directory design and page types |
| [docs/skills-reference.md](docs/skills-reference.md) | The four Claude Code skills |
| [docs/scripts-reference.md](docs/scripts-reference.md) | The seven Python utility scripts |
| [docs/obsidian-integration.md](docs/obsidian-integration.md) | Obsidian wikilinks and vault compatibility |
| [docs/scale-up-guide.md](docs/scale-up-guide.md) | Multi-round rhythms and batch sizes |
| [docs/adaptation-guide.md](docs/adaptation-guide.md) | Adapting for other research domains |
| [docs/search-and-browse.md](docs/search-and-browse.md) | Zero-backend Search + Browse web UI |
| [docs/web-frontend.md](docs/web-frontend.md) | Configuring and building the Next.js frontend (`web/`) |
| [docs/rag-backend.md](docs/rag-backend.md) | The optional agentic chat backend — one OpenAI-compatible endpoint (`rag/`) |
| [docs/deployment.md](docs/deployment.md) | Serving + deploying the web UI and API (Makefile, docker, launchd) |
| [.claude/skills/wiki-build/rubric.md](.claude/skills/wiki-build/rubric.md) | **The Wikipedia-style quality bar** |

---

## 🚀 Quick Start

If you are **new to the project**, start with:

1. [docs/quick-start.md](docs/quick-start.md) — get set up and run your first build
2. [docs/architecture.md](docs/architecture.md) — understand why it is designed this way
3. [.claude/skills/wiki-build/rubric.md](.claude/skills/wiki-build/rubric.md) — read the quality bar before writing anything

If you are **adding papers and building**, see:

- [docs/pipeline.md](docs/pipeline.md) — full build pipeline reference
- [docs/skills-reference.md](docs/skills-reference.md) — the four skills

If you are **maintaining the wiki**, see:

- [docs/scripts-reference.md](docs/scripts-reference.md) — lint and validation scripts
- [docs/scale-up-guide.md](docs/scale-up-guide.md) — maintenance rhythm

If you are **adapting this for another domain**, see:

- [docs/adaptation-guide.md](docs/adaptation-guide.md) — what to change and what to keep

---

## 🌐 Quick Start — Run the Web UI

Once you have a built `wiki/`, stand up Search + Browse with **no AI and no backend**:

```bash
make install                     # python (rag/requirements.txt) + web (pnpm) deps
python scripts/export_wiki.py    # → web/public/wiki-index.json (search index)
make web-build                   # production build of the Next.js frontend
make web-start                   # serve at http://localhost:3000  (Search + Browse only)
```

To add the 💬 **Chat** surface (optional agentic search backend), build and serve everything in one shot — **no index to build**; the backend retrieves by navigating the filesystem live:

```bash
python scripts/build_and_serve.py   # deterministic build + serve (API :8000 + web :3000)
```

Configure branding and the generation endpoint in `.env` (copy from [.env.example](.env.example); `RAG_OPENAI_BASE_URL` defaults to local Ollama's `/v1`, or point it at any hosted OpenAI-compatible endpoint). The 🛟 graceful-degradation rule: if the Chat backend is down, Search and Browse keep working.

> 📏 **Pages come out detailed by default.** `/wiki-build` now encodes a density/depth standard, so synthesis pages are richly developed unless the corpus is genuinely thin.

> ⚠️ **Always restart the web server after a rebuild.** A running `next start` caches its build manifest in memory; overwriting `.next/` without restarting makes hashed CSS/JS 404 and renders every page unstyled. Full details in [docs/deployment.md](docs/deployment.md).

---

## 🔗 Navigation Contract

When an LLM agent enters this repository, the intended reading order is:

1. `CLAUDE.md` — project rules and automation boundary
2. `/_index.md` — global repository navigation
3. Subdirectory `_index.md` files — local routing before opening many pages in a directory
4. `wiki/synthesis/` and `wiki/concepts/` — primary query targets (Wikipedia-style)
5. `wiki/sources/` — paper-specific bibliographic detail when needed
6. `raw_markdown/` — authoritative text when wiki coverage is insufficient or when reviewing
7. `raw_pdfs/` — original evidence, only when necessary

This reading order is why `_index.md` files exist at every level — they are router documents for agents.

---

*This documentation describes the literature-wiki system as a general-purpose framework. The original project description lives in the project `README.md` at the repository root.*
