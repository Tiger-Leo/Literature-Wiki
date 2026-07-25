# Skills Reference

This document is the reference for the Claude Code skills in the literature-wiki project. These project-local skills are stored under `.claude/skills/` and are loaded automatically when working in the project directory. Each is activated by matching trigger phrases.

---

## Overview

Four skills cover the core wiki operations, plus one (`wiki-serve`) for the optional web layer:

| Skill | Location | Operation |
|---|---|---|
| `wiki-build` | `.claude/skills/wiki-build/` | Multi-round multi-agent build/rebuild of the wiki from the paper collection |
| `wiki-query` | `.claude/skills/wiki-query/` | Answer literature questions from the wiki |
| `wiki-synthesis` | `.claude/skills/wiki-synthesis/` | Save a one-off insight as one wiki page |
| `wiki-update-db` | `.claude/skills/wiki-update-db/` | Lint, validate, maintain |
| `wiki-serve` | `.claude/skills/wiki-serve/` | Build the search index and serve the optional Search/Browse/Chat web UI |

The first four operate purely on the `raw_pdfs → raw_markdown → wiki` pipeline. `wiki-serve` drives the **additive** web layer ([search-and-browse.md](search-and-browse.md), [web-frontend.md](web-frontend.md), [rag-backend.md](rag-backend.md)) and never touches the build pipeline or its invariants.

The previous `literature-ingest` skill has been **removed**. Its functionality is absorbed into `/wiki-build`, which produces both source pages and synthesis pages in one orchestrated pipeline.

---

## 1. `wiki-build` — Multi-Agent Build

**Location**: `.claude/skills/wiki-build/`

**Purpose**: The centerpiece skill. Plans the page set from the actual corpus, writes Wikipedia-style synthesis pages in parallel via cluster writers, reviews them in parallel via three-lens cluster reviewers, revises until pages hit the quality bar, then lints. Domain-agnostic — adapts to whatever literature is in `raw_pdfs/`.

### Trigger Phrases

- `/wiki-build` (default 2 rounds)
- `/wiki-build 3` (override round count)
- "build the wiki"
- "rebuild wiki pages"
- "synthesize the collection"
- "process all PDFs"
- "make Wikipedia-style pages from the papers"
- "ingest these papers"

### Files Inside the Skill

| File | Purpose |
|---|---|
| `SKILL.md` | The orchestrator. Defines the 6-phase pipeline. |
| `rubric.md` | The Wikipedia-style quality bar. Single source of truth for writers and reviewers. |
| `prompts/round-planner.md` | Phase 3 planner subagent brief |
| `prompts/curator.md` | Stage A curator brief |
| `prompts/page-brief-template.md` | Schema for the per-page briefs the curator produces |
| `prompts/cluster-writer.md` | Stage B writer brief |
| `prompts/cluster-reviewer.md` | Stage C reviewer brief |
| `prompts/reviser.md` | Stage D reviser brief |
| `prompts/source-writer.md` | Phase 2 source-page writer brief |
| `prompts/source-reviewer.md` | Phase 2 source-page reviewer brief |

### Pipeline

```
Phase 0   Workspace setup at agent_tasks/wikipedia-rewrite_<DATE><HHMM>/
Phase 1   PDF → raw_markdown for new papers (deterministic)
Phase 2   Source pages — parallel writers, light review
Phase 3   Round planner subagent → round-N/plan.md
Phase 4   Round execution
             Stage A: Curator (1) → page-briefs/<slug>.md
             Stage B: Cluster writers (parallel) → rewritten-wiki/<type>/<slug>.md
             Stage C: Cluster reviewers (parallel) → reviews/cluster-<X>.md (PASS/REVISE)
             Stage D: Revisers (parallel) → round-output/<type>/<slug>.md
Phase 5   Decide on another round (default cap 2; user may override 1 or 3)
Phase 6   Finalise — copy final/round-output/ to wiki/, run full lint, update indices
```

### Key Rules

- **File handoff only** — every subagent writes to disk; returns ≤200-word status to orchestrator.
- **Parallel within phase** — all writers spawned in a single tool-call message; same for reviewers; same for revisers.
- **Read raw markdown, not source pages** — every writer and reviewer bases substantive claims on `raw_markdown/papers/<slug>.md`, never on `wiki/sources/<slug>.md`.
- **Subject-matter backbone** — no "Paper Claims" section, no paper-by-paper structure. Headings name sub-topics.
- **Domain adaptive** — cluster themes and frontier-axis decisions emerge from the actual corpus, not from a fixed taxonomy.

---

## 2. `wiki-query` — Answer Literature Questions

**Location**: `.claude/skills/wiki-query/SKILL.md`

**Purpose**: Answer literature questions from the wiki — drawing from the synthesis layer first, drilling to source pages or raw markdown only when needed.

### Trigger Phrases

- "what does the literature say about X"
- "compare how papers treat Y"
- "summarise the debate on V"
- "how does X work?"
- "what is X?"
- "what mechanisms explain Z"
- "which papers use method W"

### Canonical Read Order

1. `CLAUDE.md`
2. Entry-point `_index.md` (matched to question type)
3. Relevant `wiki/synthesis/`, `wiki/concepts/`, `wiki/debates/`, `wiki/mechanisms/`, `wiki/methods/`, `wiki/measures/` pages — primary answer layer for cross-paper questions
4. Relevant `wiki/sources/` pages — only if the synthesis layer is thin or a paper-specific detail is needed
5. `raw_markdown/papers/<slug>.md` — for exact numbers, model setup, specific quotes
6. `raw_pdfs/` — last resort

Stop at the first layer that yields a complete answer.

### Good Answer Requirements

- Draws on the synthesis layer first.
- For cross-paper questions, cites ≥3 sources in integrated prose.
- Distinguishes paper claims from cross-paper patterns from current assessment.
- Acknowledges gaps (`status: stub`, single-paper evidence, Open-Questions bullets).

---

## 3. `wiki-synthesis` — One-Page Save

**Location**: `.claude/skills/wiki-synthesis/SKILL.md`

**Purpose**: Save a single one-off insight as one wiki page. The surgical complement to `/wiki-build`. Use when a conversation produces an insight worth one Wikipedia-style page and you do not need a full collection rebuild.

### Trigger Phrases

- "save this to the wiki"
- "write a synthesis page about X"
- "create a debate page on Y"
- "file this comparison"
- "add this insight to the wiki"

### Page Type Decision

| Page type | Trigger |
|---|---|
| Synthesis | Cross-cutting theme on ≥2 papers, non-obvious, no existing concept/debate page is the right home |
| Debate | ≥2 papers stake out competing positions on a precise question |
| Concept | New theoretical or empirical construct, recurs across ≥2 papers |
| Mechanism | New causal channel, recurs across ≥2 papers |

If the insight applies to only one paper, update that paper's source page — do not create a synthesis page.

### Quality Bar

Same as `/wiki-build`'s output. Read `.claude/skills/wiki-build/rubric.md` before writing. Non-negotiables: encyclopedic lead, subject-matter backbone, integrated citations, three knowledge levels visible but not dominant.

### After Creating

- Add a wikilink to the new page from at least one related page (otherwise orphan).
- Update `wiki/<type>/_index.md`.
- Append to `wiki/log.md`.
- Run `python scripts/check_links.py wiki raw_markdown` and `python scripts/validate_frontmatter.py wiki`.

---

## 4. `wiki-update-db` — Lint and Maintain

**Location**: `.claude/skills/wiki-update-db/SKILL.md`

**Purpose**: Lint, health-check, and maintain the wiki using deterministic scripts.

### Trigger Phrases

- "run the lint"
- "check the wiki"
- "fix broken links"
- "validate the wiki"
- "health check"
- "rebuild the index"
- "find orphan pages"

### Lint Sequence

```bash
python -m py_compile scripts/*.py
python scripts/check_links.py wiki raw_markdown
python scripts/check_orphans.py wiki
python scripts/validate_frontmatter.py wiki
python scripts/export_metadata.py --output exports/raw-markdown-metadata.json
```

### Fix Protocol

| Issue | Fix |
|---|---|
| Broken wikilink | Update wikilink in source page |
| Orphan page | Add inbound link from concept/mechanism/debate/`_index.md` |
| Missing frontmatter field | Add per `wiki/schema/frontmatter-schema.md` |
| Missing `_index.md` | Create router file for that directory |

For substantive issues, spawn a targeted writer subagent via `/wiki-synthesis` rather than editing inline.

### Health Check Beyond Scripts

- **Stub upgrades** — grep for `status: stub`; check if ≥2 papers now cite it and the body is substantive; upgrade.
- **Stale assessments** — after a `/wiki-build` pass, check whether recently added papers contradict or extend the current-assessment callouts.
- **Missing concept pages** — grep wikilinks for targets that do not exist.

---

## 5. `wiki-serve` — Build the Search Index and Serve the Web UI

**Location**: `.claude/skills/wiki-serve/SKILL.md`

**Purpose**: Build the frontend search index and serve the **optional** web layer — Search · Browse · Chat — over an already-built `wiki/`. This layer is additive: Search and Browse need no AI and no backend; only Chat requires the RAG backend. It never touches the `/wiki-build` pipeline or its invariants.

### Trigger Phrases

- "serve the wiki" / "serve the wiki web UI"
- "start the frontend" / "launch the web UI"
- "run the search/chat app"
- "build the search index" / "run export_wiki"
- "start the RAG chat"
- "make serve"

### What It Does

1. **Install deps** — `make install` (Python `rag/requirements.txt` + web `pnpm` deps; skips frontend deps with a message if `pnpm` is missing).
2. **Build the search index** — `python scripts/export_wiki.py` (or `make search-index`) → `web/public/wiki-index.json` (+ `exports/wiki.json`). Powers Search `/search` (client-side MiniSearch) and Browse `/wiki`.
3. **Optional agentic Chat backend** — no index to build. The backend retrieves by navigating `wiki/` + `raw_markdown/` live with sandboxed filesystem tools (one OpenAI-compatible generation endpoint via `RAG_OPENAI_BASE_URL`, default local Ollama `/v1`). Only needed for the Chat tab; build + serve everything with `python scripts/build_and_serve.py`.
4. **Serve** — `make web-build` + `make web-start` (browse + search, no AI), or `make serve` / `scripts/serve.sh` to run the API backend and web together for the full Search/Browse/Chat experience.

### Key Points

- Search and Browse read `wiki/` and `web/public/wiki-index.json` directly; no backend or AI required.
- The page viewer `/wiki/[slug]` reads the wiki from the filesystem at request time.
- **Restart the web server after every wiki rebuild** so it picks up the regenerated index and pages.
- Config is read from `.env` (copy `.env.example` → `.env`); defaults live in `rag/config.py` and the frontend.

See [search-and-browse.md](search-and-browse.md), [web-frontend.md](web-frontend.md), [rag-backend.md](rag-backend.md), and [deployment.md](deployment.md) for the full web layer.

---

## Skill Design Principles

- **Narrow scope** — each skill handles exactly one operation type. `wiki-build` orchestrates many subagents but is itself one skill.
- **File handoff** — `wiki-build` uses files as the agent communication medium so the orchestrator's context stays small. Every subagent writes outputs to disk and returns a ≤200-word status.
- **Schema delegation** — skills point to `wiki/schema/` for frontmatter and naming conventions, and to `.claude/skills/wiki-build/rubric.md` for the page quality bar.
- **Script delegation** — deterministic validation lives in `scripts/`, not in skill prose.
- **Knowledge separation** — every synthesis page distinguishes paper claim / cross-paper pattern / current assessment inline. Never as separate top-level sections.
- **Read raw markdown, not source pages** — substantive claims trace to the authoritative paper text. Source pages are derived summaries and can flatten or mislead.
