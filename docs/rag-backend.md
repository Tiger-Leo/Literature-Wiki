# 🔎 Agentic Chat Backend (optional AI layer)

The `rag/` directory is an **optional** FastAPI backend that powers the Chat
surface of the [web frontend](web-frontend.md). It answers literature questions
by **agentic filesystem navigation** — there is **no embedding index, vector
store, BM25, or graph index, and no index build**. A generation model drives a
tiny set of sandboxed wiki-filesystem tools (`list_dir`/`glob`/`grep`/`read_file`)
to read the wiki the way the `/wiki-query` skill prescribes, then writes one
integrated, cited answer. It talks to **one OpenAI-compatible generation
endpoint**, defaulting to a local Ollama so it runs fully local out of the box.
The wiki is fully usable without it — Search and Browse
([search-and-browse.md](search-and-browse.md)) need no backend at all. Install
this only if you want conversational Q&A.

All knobs live in `rag/config.py`, every one env-overridable via `RAG_*`. The
canonical env reference is the repo-root `.env.example`; provider details are in
`rag/PROVIDERS.md`. This doc references env vars only — **no secrets**.

---

## 🏗️ Architecture

```
agent_qa  (tool-calling loop)  →  agent_tools  (sandboxed FS)  →  serve (FastAPI)
```

- **No retrieval index.** Nothing is embedded, chunked, or pre-indexed. Every
  answer is produced by navigating the live `wiki/` + `raw_markdown/` files at
  request time. Edits to the wiki are reflected immediately — no rebuild.
- **Sandboxed filesystem tools** (`rag/agent_tools.py`) — `list_dir`, `glob`,
  `grep` (ripgrep when available, pure-Python fallback otherwise), and
  `read_file` (paged). All paths resolve read-only under `RAG_WIKI_ROOT` and
  reject `..` / absolute / symlink escapes.
- **Agentic loop** (`rag/agent_qa.py`) — drives the generation model through the
  canonical `/wiki-query` read order (entry `_index.md` → synthesis / concepts →
  `wiki/sources/<slug>.md` → `raw_markdown/papers/<slug>.md`). The model gathers
  evidence with tools, signals readiness via a `write_answer` sentinel, then
  streams one integrated answer that keeps the wiki's three knowledge levels
  distinct (paper claim / cross-paper pattern / current assessment).
- **Two tool protocols** behind one loop: a **ReAct** text protocol (default,
  fenced ```` ```action {json}``` ```` blocks) and the OpenAI **native**
  tool-calling schema. Selected by `RAG_AGENT_TOOL_BACKEND` (`react` |
  `native` | `auto`); `react` is the robust default for every endpoint,
  Ollama's `/v1` included.
- **Citation safety** — `[[slug]]` citations whose slug is not a real corpus file
  are de-linked as they stream, so no broken wikilink ever ships.
- **Thread persistence** — chat threads + messages stored in SQLite
  (`rag/threads.db`, via `aiosqlite`); supports rename/archive/export.

---

## 🔌 Generation endpoint

Generation goes through `rag/llm.py`, which talks to **one** OpenAI-compatible
endpoint. There are no embeddings — generation only, no provider switch. Since
Ollama serves the OpenAI protocol at `/v1`, "fully local" is just this same
client pointed at Ollama. Full details: [`rag/PROVIDERS.md`](../rag/PROVIDERS.md).

Three settings, precedence first-non-empty-wins (`RAG_*` env > friendly `.env`
keys > local-Ollama defaults):

| Setting | Env var | `.env` key | Default |
|---|---|---|---|
| Base URL | `RAG_OPENAI_BASE_URL` | `base_url` | `http://localhost:11434/v1` (local Ollama) |
| API key | `RAG_OPENAI_API_KEY` | `api_key` | `ollama` (dummy; local Ollama ignores it) |
| Model | `RAG_GEN_MODEL` | `model` | `qwen3.6:35b-mlx` |

### 🦙 Local via Ollama (zero-config default)

```bash
ollama pull qwen3.6:35b-mlx              # nothing else to set — config.py already
                                         # points at http://localhost:11434/v1
```

### 🤖 Hosted (any OpenAI-compatible endpoint)

```bash
export RAG_OPENAI_BASE_URL=https://api.openai.com/v1   # or DeepSeek/vLLM/OpenRouter/…
export RAG_OPENAI_API_KEY=...                          # never commit this
export RAG_GEN_MODEL=gpt-4o-mini
```

`num_ctx` has no analogue in the OpenAI protocol and is ignored; `num_predict`
maps to `max_tokens`; `temperature` passes through.

---

## 📦 Install + configure

```bash
pip install -r rag/requirements.txt
# includes `openai` (the generation client); ripgrep (rg) optionally speeds up the agentic grep.
```

Key wiring vars (full list in `rag/config.py` / `.env.example`):

| Env var | Default | Purpose |
|---|---|---|
| `RAG_WIKI_ROOT` | `rag/`'s parent | Point the backend at a wiki living elsewhere; `WIKI_DIR`/`RAW_DIR` derive from it. |
| `RAG_TIER_A_DIRS` | `concepts,mechanisms,…` | Comma-separated curated-layer dirs (used to classify a read file's layer/tier). |
| `RAG_DOMAIN_DESC` | generic blurb | Your wiki's subject, injected into the agentic system prompt. |
| `RAG_AGENT_MAX_STEPS` | `12` | Max tool-call turns before forcing a final answer. |
| `RAG_AGENT_TOOL_BACKEND` | `auto` (`react` for openai) | `auto` \| `native` \| `react`. |
| `RAG_HOST` / `RAG_PORT` | `127.0.0.1` / `8000` | Bind host/port for `python -m rag.server`. |

---

## 🛠️ Serve (no index build)

```bash
# There is NOTHING to build — just serve the API.
uvicorn rag.server:app --port 8000
python -m rag.server                        # honours RAG_HOST / RAG_PORT
```

`threads.db` is created on first run and is gitignored. Because the backend reads
the live filesystem, a `/wiki-build` or manual edit is picked up on the next
question — no re-index step.

---

## 🌐 API contract

FastAPI app (`rag/server.py`), shaped for assistant-ui adapters.

| Method | Path | Behaviour |
|---|---|---|
| GET | `/health` | `{ok, mode: "agentic", gen_model, gen_endpoint}` |
| POST | `/api/chat` | **Streaming NDJSON**. Body `{messages}`. Always runs the agentic path. |
| GET | `/api/page/{slug}` | Resolve wikilink → `{slug, title, markdown, found, layer}` (frontmatter stripped). |
| GET/POST | `/api/threads` | List / create threads. |
| GET/PATCH/DELETE | `/api/threads/{id}` | Fetch / rename+archive / delete (cascade messages). |
| POST | `/api/threads/{id}/title` | LLM-generate a 3–6-word title. |
| GET/POST | `/api/threads/{id}/messages` | History / append. |
| GET | `/api/threads/{id}/export?format=md\|json` | Download the conversation. |

**`/api/chat` NDJSON events** (one JSON object per line, `application/x-ndjson`):

| `type` | Fields | Meaning |
|---|---|---|
| `status` | `label` | Tool step / stage (spinner pill) |
| `sources` | `sources[]` | Files actually read (`{slug, path, layer, tier}`) |
| `delta` | `text` | Answer text chunk (accumulate) |
| `done` | — | Stream complete |
| `error` | `message?` | Soft failure (frontend shows inline ⚠️) |

CLI equivalent for debugging: `python -m rag.query "your question"` (status to
stderr, answer to stdout).

---

## 🔐 CORS / hardening

`RAG_CORS_ORIGINS` (comma-separated) controls allowed origins. The default `*`
is convenient for local dev; **restrict it before exposing the server**, e.g.
`RAG_CORS_ORIGINS=https://wiki.example.com,http://localhost:3000`. There is no
auth or rate limit on the endpoints — keep the server on a trusted network
(localhost / LAN / VPN) or front it with a reverse proxy that adds auth. The
agentic FS tools are sandboxed read-only under `RAG_WIKI_ROOT` and reject
`..` / absolute / symlink escapes.

---

## 🛟 Graceful degradation

- `ripgrep` (`rg`) absent → the grep tool falls back to a pure-Python regex scan.
- `openai` package absent → a clear install error, raised only when generation is
  actually invoked.
- A stuck model that repeats the same tool call is nudged and, past
  `RAG_AGENT_MAX_STEPS`, forced to write the answer from the evidence gathered.
- An invented `[[slug]]` citation is de-linked to plain text as it streams, so a
  broken wikilink never reaches the user.
- Backend unreachable → the frontend shows a clean inline ⚠️ message; Search and
  Browse keep working without the backend at all.
