---
purpose: Entry point for Claude Code agents bootstrapping a new literature wiki
audience: LLM agents and researchers setting up a wiki for the first time
---

# Literature Wiki — Agent Setup Guide

This is a **ready-to-use template** for building an AI-native literature wiki from scratch — one where every page is a **Wikipedia-style synthesis** centered on one topic (concept, debate, mechanism, measure, method, or theme), integrating evidence across the whole paper collection. Not paper-by-paper summaries; not annotated bibliographies.

When you clone this repo, the full scaffold (directories, scripts, skills, templates, schema) is already in place.

Your setup steps:
1. Customize this `CLAUDE.md` and `_index.md` for your research domain.
2. Drop PDFs into `raw_pdfs/`.
3. Run `/wiki-build` — a multi-round, multi-agent orchestrator that plans the page set from your corpus, writes pages in parallel by cluster, reviews them in parallel, revises until they hit the quality bar, and lints.
4. *(Optional)* Stand up the **Search / Browse / Chat web UI** (and the RAG chat backend) — see **Phase 4** below.

**If you are an AI agent setting this repo up, read in this order:** this `CLAUDE.md` first → `_index.md` → then, for each pipeline you intend to activate, read the docs named in that pipeline's Phase (the **Documentation Map** below says which doc gates which step). Do **Phase 1 → 2 → 3** for the core wiki; do **Phase 4** only if the user wants the web UI / chat. Don't run a pipeline before reading its gating docs.

---

## What You Are Setting Up

An **AI-native literature wiki** — a structured, cross-referenced knowledge base built from a collection of academic PDFs. The deliverable is a set of focused Wikipedia-style pages, each centered on one topic, integrating evidence from across the collection in an encyclopedic narrative voice.

Core pipeline: `raw_pdfs/ → raw_markdown/ → wiki/`

Four operations:

| Operation | Skill | When |
|---|---|---|
| **build** | `/wiki-build` | Multi-round multi-agent build/rebuild of the wiki from the paper collection. Replaces single-paper ingest. |
| **query** | `/wiki-query` | Answer a literature question from the wiki layer. |
| **synthesis** | `/wiki-synthesis` | Save a one-off insight as a single wiki page (concept, debate, mechanism, or synthesis). |
| **update-db** | `/wiki-update-db` | Lint, validate, and maintain the wiki. |
| **serve** | `/wiki-serve` | Build the search index and serve the Search/Browse/Chat web UI. (Optional layer — see below.) |

Build/serve commands for the optional web layers:

- `python scripts/export_wiki.py` (or `make search-index`) — build the frontend search index from `wiki/`.
- `make serve` — run the API (background) + web frontend together; or `make api` + `make web-dev` separately.

---

## Documentation Map

Read these files in the order listed when setting up a new wiki:

| Priority | File | When to read |
|---|---|---|
| 1 | [README.md](README.md) | Always — system overview |
| 2 | [docs/quick-start.md](docs/quick-start.md) | New setup — prerequisites and first build |
| 3 | [docs/architecture.md](docs/architecture.md) | Before making structural decisions |
| 4 | [docs/wiki-structure.md](docs/wiki-structure.md) | Before creating wiki pages |
| 5 | [docs/pipeline.md](docs/pipeline.md) | Before running `/wiki-build` |
| 6 | [docs/skills-reference.md](docs/skills-reference.md) | Before using any of the four skills |
| 7 | [docs/scripts-reference.md](docs/scripts-reference.md) | Before running lint or conversion scripts |
| 8 | [docs/obsidian-integration.md](docs/obsidian-integration.md) | If using Obsidian as a viewer |
| 9 | [docs/scale-up-guide.md](docs/scale-up-guide.md) | When scaling beyond ~10 papers |
| 10 | [docs/adaptation-guide.md](docs/adaptation-guide.md) | When adapting for a different research domain |
| 11 | [docs/llm-wiki.md](docs/llm-wiki.md) | The original inspiration (Karpathy's llm-wiki) and design philosophy |
| 12 | [docs/search-and-browse.md](docs/search-and-browse.md) | When standing up the zero-backend Search + Browse web UI |
| 13 | [docs/web-frontend.md](docs/web-frontend.md) | Before configuring/building the Next.js frontend (`web/`) |
| 14 | [docs/rag-backend.md](docs/rag-backend.md) | When enabling the optional RAG chat backend (`rag/`) |
| 15 | [docs/deployment.md](docs/deployment.md) | When serving or deploying the web UI + API (Makefile, docker, launchd) |
| 16 | [.claude/skills/wiki-build/rubric.md](.claude/skills/wiki-build/rubric.md) | The Wikipedia-style quality bar — read this before any writing |

---

## Optional layers: Search/Browse UI and RAG Chat

Beyond the three-layer wiki pipeline (`raw_pdfs/ → raw_markdown/ → wiki/`), the template now ships two **additive** layers. They consume the wiki you already built; **the core `/wiki-build` pipeline and all its invariants are unchanged**, and you never need either layer to build, query, or maintain the wiki.

**(a) Search + Browse frontend (`web/`, Next.js 16).** A zero-backend Next.js app with three surfaces — Search, Browse, and Chat. Search and Browse need **no AI and no backend**:

- 🔎 **Search** (`/search`) — client-side MiniSearch over `web/public/wiki-index.json` (built by `python scripts/export_wiki.py` / `make search-index`).
- 📖 **Browse** (`/wiki`, `/wiki/[slug]`) — a **two-pane layout**: a left category sidebar (collapsible groups by layer, page counts, active highlight, search box; a slide-in drawer behind a hamburger on mobile), a center reading column (overview cards at `/wiki`; a single page rendered from the `wiki/` filesystem at `/wiki/[slug]`, with `[[wikilinks]]`, callouts, and KaTeX), and a right "On this page" TOC on desktop.
- 💬 **Chat** (`/`) — the assistant-ui surface for the RAG backend; its thread-history sidebar is persistent on desktop and a slide-in drawer (hamburger) on mobile.

Branding flows from build-time `NEXT_PUBLIC_*` env vars. See [docs/search-and-browse.md](docs/search-and-browse.md) and [docs/web-frontend.md](docs/web-frontend.md).

**(b) Agentic search backend (`rag/`).** An optional FastAPI backend powering the Chat surface. It talks to one OpenAI-compatible generation endpoint (`RAG_OPENAI_BASE_URL`), defaulting to local Ollama's `/v1` for a zero-config local run; point `RAG_OPENAI_BASE_URL` + `RAG_OPENAI_API_KEY` + `RAG_GEN_MODEL` at any hosted model to swap it in. Retrieval is **agentic, not embedding-based**: the model navigates the wiki (`wiki/` curated pages + `raw_markdown/` raw paper text) with sandboxed filesystem tools (list/glob/grep/read, scoped to `RAG_WIKI_ROOT`), then streams a cited answer as NDJSON with thread persistence. **There is no index to build** — no vector store, no BM25, no embeddings. Point it at any wiki with `RAG_WIKI_ROOT`. Chat degrades gracefully — if the backend is absent, Search and Browse still work. See [docs/rag-backend.md](docs/rag-backend.md) and, for serving/deploying both, [docs/deployment.md](docs/deployment.md).

> ⚠️ **Deployment caveat:** always restart the web server after a rebuild. A running `next start` caches its build manifest in memory; overwriting `.next/` without restarting causes hashed CSS/JS to 404 and every page to render unstyled. Full fix in [docs/deployment.md](docs/deployment.md).

---

## Phase 1 — Customize for Your Domain

> The scaffold is already in place. Your only Phase 1 task is to fill in the blanks for your domain.

### 1.1 Verify scripts work

```bash
python -m py_compile scripts/*.py
```

Install markitdown if not present:

```bash
pip install markitdown
```

### 1.2 Customize this CLAUDE.md

Replace this file with your project's operational rules. Minimum required sections:

```markdown
# [Your Wiki Name] — Rules

## Purpose
[Describe your research domain and key topics in 2–3 sentences.]

## Layers
- `raw_pdfs/`: immutable source PDFs. Never edit.
- `raw_markdown/`: machine-readable conversions. Default converter: markitdown.
- `wiki/`: canonical knowledge layer — Wikipedia-style synthesis pages. LLM-maintained via `/wiki-build`.

## Navigation Contract
- Read `CLAUDE.md` first.
- Then read `/_index.md`.
- Then read `_index.md` in any relevant subdirectory.

## Main Operations
- `/wiki-build`: multi-round multi-agent build/rebuild of the wiki.
- `/wiki-query`: answer from the wiki first.
- `/wiki-synthesis`: save a one-off insight as a single wiki page.
- `/wiki-update-db`: lint and maintain.
- `/wiki-serve`: build the search index and serve the web UI (optional).

## Maintenance Sequence
- `python -m py_compile scripts/*.py`
- `python scripts/check_links.py wiki raw_markdown`
- `python scripts/check_orphans.py wiki`
- `python scripts/validate_frontmatter.py wiki`
- `python scripts/export_metadata.py --output exports/raw-markdown-metadata.json`
```

### 1.3 Update _index.md

Replace `[Your Wiki Name]` with your project name. Update "Current Status" after each build.

---

## Phase 2 — Drop Papers and Build

> No seeding required. `/wiki-build` plans the page set from the actual corpus.

### 2.1 Name and place PDFs

Rename PDFs to: `Author and Author - YYYY - Paper Title.pdf`, place in `raw_pdfs/`.

### 2.2 Run /wiki-build

```
/wiki-build         # default 2 rounds
/wiki-build 3       # 3 rounds for harder corpora
/wiki-build 1       # quick pass, one-round only
```

The orchestrator will:

1. **Scan** `raw_pdfs/` vs. existing `wiki/sources/` to find new papers.
2. **Convert** new PDFs to `raw_markdown/papers/<slug>.md`.
3. **Build source pages** (one parallel writer per new paper + light review).
4. **Plan the page set** — a single planner subagent inspects the corpus and produces a round plan: which concept / debate / mechanism / measure / method / synthesis pages to create or update, clustered for parallel writing, with an emergent theme label per cluster. Domain-agnostic; cluster themes emerge from the actual papers.
5. **Curate page briefs** — one curator subagent writes a structured brief per page with a Wikipedia-style outline, ≤10 ranked source slugs, three reviewer spot-check anchors, and explicit writing constraints (`.claude/skills/wiki-build/prompts/page-brief-template.md`).
6. **Write in parallel** — one cluster writer per cluster (typically 2–3 pages each), drafting Wikipedia-style synthesis pages to `agent_tasks/<workspace>/round-N/rewritten-wiki/`.
7. **Review in parallel** — one cluster reviewer per ~2 clusters, applying three lenses: synthesis quality / fidelity (spot-checks against raw papers, NOT source pages) / coverage and cross-links. Verdicts: PASS or REVISE.
8. **Revise** — one reviser per cluster with REVISE pages. Output goes to `round-N/round-output/`.
9. **Decide on another round** — if reviews still flag substantive issues and round-count < requested, repeat.
10. **Finalise** — copy last round's `round-output/` into `wiki/`, run full lint, update `_index.md` and `wiki/log.md`.

All subagent work lives under `agent_tasks/wikipedia-rewrite_<DATE><HHMM>/`. Every subagent writes to disk and returns ≤200-word status summaries — no large content flows through the orchestrator's context.

### 2.3 Read the quality bar before writing anything

`.claude/skills/wiki-build/rubric.md` is the single source of truth. The non-negotiables:

- **Encyclopedic lead paragraph** — no bullets, no single-paper-only citation.
- **Subject-matter backbone** — section headings name sub-topics, not papers. NO "Paper Claims" section.
- **Integrated citations** — multi-cite where claims converge; name papers in flow only when their distinct contribution matters.
- **Three knowledge levels visible but not dominant** — paper claims via inline `[[slug]]`, cross-paper patterns via italicised generalisations, current assessment via short callout blocks. None of these becomes a top-level section.
- **READ THE RAW PAPER**, NOT the source page. Substantive claims trace to `raw_markdown/papers/<slug>.md`. Source pages are navigation aids only.
- **Pages are detailed by default.** `/wiki-build` now encodes a density/depth standard in the rubric and prompts (word band, 7–10 subject-matter sections, multi-paper sections, a few knowledge-level callouts, generous cross-linking). Writers and reviewers hold pages to it; the standard degrades gracefully for a genuinely thin corpus rather than forcing padding.

---

## Phase 3 — Validate

### 3.1 Validate query quality

After the build, test `/wiki-query` with three questions:
1. A concept definition question: "What is [concept X]?"
2. A cross-paper comparison: "How do papers in this collection treat [concept Y]?"
3. A debate question: "What is the debate about [topic Z]?"

A passing result: the answer is grounded in synthesis pages (concept / mechanism / debate), not per-paper summaries; cites multiple sources in integrated prose; distinguishes paper claims from cross-paper patterns from current assessment.

### 3.2 Scale up

Follow `docs/scale-up-guide.md` for batch sizes, multi-round rhythms, and stub-upgrade protocols.

---

## Phase 4 — Stand up the Search / Browse / Chat web UI (optional)

> Additive layers that **consume** the wiki built in Phases 1–3. Skip entirely if you only need the wiki + `/wiki-query`. The fastest path is the `/wiki-serve` skill, which performs the steps below; do it manually when you need control.

**4.0 Read the gating docs first** (in this order):
1. [docs/search-and-browse.md](docs/search-and-browse.md) — the zero-backend Search + Browse layer and the `wiki-index.json` data contract.
2. [docs/web-frontend.md](docs/web-frontend.md) — the Next.js app (`web/`): three surfaces, `NEXT_PUBLIC_*` branding env, build/run.
3. [docs/rag-backend.md](docs/rag-backend.md) — **only if** you want the Chat surface: the agentic chat backend (one OpenAI-compatible endpoint) (`rag/`).
4. [docs/deployment.md](docs/deployment.md) — serving/deploying both (Makefile, docker, launchd) **and the rebuild→restart caveat**.

**4.1 Browse + Search only (no AI, no backend):**
```bash
make install                 # pip deps + (cd web && pnpm install)
python scripts/export_wiki.py --wiki-dir wiki   # → web/public/wiki-index.json  (or: make search-index)
make web-build               # WIKI_DIR points at ./wiki by default
make web-start               # serves http://localhost:3000  (Search + Browse + filesystem page viewer)
```
On Windows (PowerShell):
```powershell
pip install -r rag\requirements.txt
cd web; pnpm install; cd ..
python scripts/export_wiki.py --wiki-dir wiki
cd web; NODE_OPTIONS="" pnpm build; pnpm start
```
Rebuild the search index (`make search-index` / `python scripts/export_wiki.py`) whenever `wiki/` changes.

**4.2 Add the agentic Chat surface (needs a generation provider):**
```bash
# set the endpoint in .env (see .env.example): RAG_OPENAI_BASE_URL (default local Ollama http://localhost:11434/v1, or a hosted endpoint)
python scripts/build_and_serve.py   # deterministic one-shot: export search index + build web + serve API :8000 + web :3000
```
There is **no index-build step** — the agentic backend retrieves by navigating `wiki/` + `raw_markdown/` live at query time (no vector store, no embeddings). `build_and_serve.py` is idempotent and fail-fast; use `--no-serve` / `--verify-only` for CI. (`make serve` still works for running the API + frontend separately.)

> ⚠️ **After every `pnpm build`/`make web-build`, restart the running web server** (`next start` / the launchd service / `docker compose restart web`). Skipping this leaves a stale in-memory build manifest while `.next/` is overwritten → hashed CSS/JS 404 → every page renders unstyled. A clean rebuild is `rm -rf web/.next && make web-build` (Windows: `Remove-Item -Recurse -Force web\.next; cd web; pnpm build`) then restart. See [docs/deployment.md](docs/deployment.md).

**4.3 Verify** (real-run): open `/search` (type a known term), `/wiki` (browse by layer), a `/wiki/<slug>` page (math/callouts/wikilinks render), and — if enabled — `/` Chat (a query streams a cited answer). Check the page is **styled** (if not, you skipped the restart in 4.2's caveat).

---

## Automation Boundary

| Role | Responsibilities |
|---|---|
| **LLM (orchestrator)** | Plan, spawn subagents, collect status, decide on revise/round continuation |
| **LLM (subagents)** | Curate briefs, write pages, review pages, revise pages — file handoff only |
| **Scripts** | Frontmatter validation, link checking, orphan detection, index export — NO academic judgment |
| **Researcher** | Research direction, paper selection, edit the round plan if the planner's clustering is off, trust calibration of the final pages |

Scripts **never** make academic decisions. LLMs **never** do what scripts can do reliably. The orchestrator **never** writes wiki content itself.

---

## Key Invariants

1. Every `raw_pdf` has a corresponding `raw_markdown/papers/<slug>.md`.
2. Every `wiki/sources/<slug>.md` links back to its raw markdown.
3. Every synthesis page is **encyclopedic** — subject-matter backbone, integrated citations, no per-paper sections, no "Paper Claims" listing.
4. Every wiki page has complete YAML frontmatter conforming to `wiki/schema/frontmatter-schema.md`.
5. No orphan pages — every page is reachable from at least one `_index.md` or cross-linked from a sibling.
6. `wiki/log.md` is append-only.
7. Writers and reviewers always read `raw_markdown/papers/<slug>.md`, never base substantive claims on `wiki/sources/<slug>.md`.

---

## Adapting for Your Domain

See `docs/adaptation-guide.md`. The architecture — three layers, five operations/skills (`/wiki-build`, `/wiki-query`, `/wiki-synthesis`, `/wiki-update-db`, `/wiki-serve`), the maintenance scripts (including `scripts/export_wiki.py`), the multi-round build, and the optional Search/Browse/Chat + RAG layers — is fully domain-agnostic. The planner / curator inside `/wiki-build` adapts to your literature — cluster themes are emergent, not pre-set; the frontier-extension axis is optional and only included when the corpus has such a sub-literature. The web UI adapts via `NEXT_PUBLIC_*` branding and `RAG_*` provider settings (no code changes needed).
