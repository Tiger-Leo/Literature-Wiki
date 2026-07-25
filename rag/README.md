# 🔎 literature-wiki agentic chat backend

An **agentic-search backend** over any literature wiki built with this template
(`wiki/` synthesis pages + `raw_markdown/papers/` source text). It answers
questions by **navigating the wiki filesystem with tools** — there is **no
embedding index, vector store, BM25, or graph index, and no index build**. It
talks to **one OpenAI-compatible generation endpoint**, defaulting to a local
Ollama (`http://localhost:11434/v1`) so it runs fully local out of the box, and
serves answers through a streaming HTTP API with persistent thread history and
export. It is domain-agnostic — point it at your wiki and go.

## 🧠 How it works

1. **Agentic loop** (`agent_qa.py` + `agent_tools.py`) — drives a generation
   model through the canonical `/wiki-query` read order using a tiny set of
   sandboxed, read-only filesystem tools:
   - `list_dir`, `glob`, `grep` (ripgrep when present, pure-Python fallback),
     `read_file` (paged) — all resolved under `RAG_WIKI_ROOT`, rejecting
     `..` / absolute / symlink escapes.
   - **Two-tier corpus awareness** — Tier-A = curated wiki pages (`concepts/`,
     `mechanisms/`, …, configurable via `RAG_TIER_A_DIRS`); Tier-B = raw paper
     text (`raw_markdown/papers/`). The model reads the synthesis page first,
     then drills into raw papers to ground specific claims.
   - **Two tool protocols** behind one loop — a ReAct text protocol (default) and
     the OpenAI native tool-calling schema (`RAG_AGENT_TOOL_BACKEND=react|native|auto`).
   - **Cited generation** — one integrated answer keeping three knowledge levels
     distinct (paper claim / cross-paper pattern / current assessment); invented
     `[[slug]]` citations are de-linked as the answer streams.

2. **API** (`server.py` + `store.py`) — FastAPI: streaming `/api/chat` (always
   agentic), thread + message CRUD, title generation, Markdown/JSON export,
   persisted in SQLite.

## 📦 Install

```bash
pip install -r rag/requirements.txt
# includes `openai` (the generation client). Optional: ripgrep (rg) speeds up
# the agentic grep tool; a pure-Python fallback is used when it is absent.
```

## 🚀 Usage

```bash
# There is NO index to build — just serve.

# 1) cited answer (CLI; status to stderr, answer to stdout)
python -m rag.query "your question"

# 2) API server
uvicorn rag.server:app --port 8000
python -m rag.server                         # honours RAG_HOST / RAG_PORT
```

## ⚙️ Configuration

All knobs live in `rag/config.py`, overridable via environment variables:

| Env var | Default | Purpose |
|---|---|---|
| `RAG_OPENAI_BASE_URL` | `http://localhost:11434/v1` | The one OpenAI-compatible endpoint (local Ollama by default). See [PROVIDERS.md](PROVIDERS.md). |
| `RAG_OPENAI_API_KEY` | `ollama` | API key for the endpoint (dummy for local Ollama; real key for hosted). |
| `RAG_GEN_MODEL` | `qwen3.6:35b-mlx` | Generation (chat) model. |
| `RAG_WIKI_ROOT` | rag/'s parent | Point the backend at a wiki living elsewhere. |
| `RAG_TIER_A_DIRS` | concepts,mechanisms,… | Comma-separated curated-layer dirs for your taxonomy. |
| `RAG_DOMAIN_DESC` | generic blurb | Your wiki's subject, injected into the agentic system prompt. |
| `RAG_AGENT_MAX_STEPS` | `12` | Max tool-call turns before forcing a final answer. |
| `RAG_AGENT_TOOL_BACKEND` | `react` | `react` \| `native` \| `auto`. |
| `RAG_CORS_ORIGINS` | `*` | Comma-separated allowed origins. `*` is for local dev — restrict before exposing. |
| `RAG_PORT` / `RAG_HOST` | `8000` / `127.0.0.1` | Used by `python -m rag.server`. |

## 🛟 Graceful degradation

`ripgrep` absent → pure-Python grep fallback. `openai` package absent → a clear
install error, raised only when generation is actually invoked. A stuck model is
nudged and, past `RAG_AGENT_MAX_STEPS`, forced to answer from the evidence
gathered. Invented `[[slug]]` citations are de-linked so no broken wikilink
ships. `threads.db` is gitignored.

## 🔁 Keeping in sync

Nothing to re-index — the backend reads the live filesystem, so a `/wiki-build`
or manual edit is reflected on the next question.
