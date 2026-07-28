# 📚 产业融合文献 Wiki

Global navigation entry point for agents and humans.

> **Agent**: read `CLAUDE.md` first, then this file, then the relevant subdirectory `_index.md`.

---

## Repository Structure

| Directory | Role |
|---|---|
| `raw_pdfs/` | Immutable source PDFs — never edited |
| `raw_markdown/` | Faithful PDF-to-markdown conversions |
| `wiki/` | Structured knowledge layer — primary interface |
| `scripts/` | Deterministic utility scripts |
| `exports/` | Metadata snapshots |
| `agent_tasks/` | Timestamped work plans for multi-agent sessions |
| `.claude/skills/` | Claude Code skills |
| `docs/` | Documentation for the system |
| `web/` | Next.js frontend — Search · Browse · Chat (optional, additive) |
| `rag/` | Optional agentic chat backend — one OpenAI-compatible endpoint (FastAPI) |
| `deploy/` | Deployment templates (docker, launchd) for serving the web UI + API |
| `examples/` | `demo-wiki/` — a domain-neutral sample wiki for trying the UI |

---

## Wiki Entry Points

| Goal | Start here |
|---|---|
| Ask a literature question | `wiki/_index.md` → `wiki/synthesis/overview.md` |
| Find papers on a concept | `wiki/concepts/_index.md` |
| Find papers using a method | `wiki/methods/_index.md` |
| Explore a debate | `wiki/debates/_index.md` |
| Explore a mechanism | `wiki/mechanisms/_index.md` |
| Find a specific paper | `wiki/sources/_index.md` |

---

## Current Status

- Papers ingested: 13
- Last build: —
- Last lint: —
- Last synthesis: —
- Last config: 2026-07-28 (manifest adjusted — 13 PDFs verified consistent)

*Update this section after each major wiki operation.*

---

## Four Core Operations

| Operation | Skill | When |
|---|---|---|
| `build` | `/wiki-build` | Multi-round, multi-agent build/rebuild from the paper collection. Plans → curates briefs → parallel cluster writers → parallel cluster reviewers → revisers → finalise. |
| `query` | `/wiki-query` | Answer a literature question from the synthesis layer. |
| `synthesis` | `/wiki-synthesis` | Save a one-off insight as one wiki page. |
| `update-db` | `/wiki-update-db` | Lint, validate, maintain. |
| `serve` | `/wiki-serve` | Build the search index and serve the Search/Browse/Chat web UI (optional). |

The quality bar for every synthesis page lives at `.claude/skills/wiki-build/rubric.md` — Wikipedia-style narrative, subject-matter backbone, integrated citations, no per-paper sections.

---

## Optional Web Layer

Beyond the wiki pipeline, the template ships an additive web layer that reads your built `wiki/`:

- 🔎 **Search** + 📖 **Browse** — `web/`, zero backend, no AI. Search index built by `python scripts/export_wiki.py` (`make search-index`).
- 💬 **Chat** — optional agentic search backend in `rag/` (talks to one OpenAI-compatible endpoint via `RAG_OPENAI_BASE_URL`, defaulting to local Ollama's `/v1`; swap in any hosted model). No index to build — it retrieves by navigating `wiki/` + `raw_markdown/` live. Build + serve with `python scripts/build_and_serve.py`.

Serve everything with `make serve` (web :3000, api :8000), or run `/wiki-serve`. Chat degrades gracefully — Search and Browse work even when the backend is down. See `docs/search-and-browse.md`, `docs/web-frontend.md`, `docs/rag-backend.md`, `docs/deployment.md`.
