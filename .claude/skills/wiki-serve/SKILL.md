---
name: wiki-serve
description: Use this skill when the user wants to serve or run the wiki web UI — phrases like "serve the wiki", "serve the wiki web UI", "start the frontend", "run the search/chat app", "launch the web UI", "build the search index", "run export_wiki", "start the chat", "make serve", "build and serve". Runs the deterministic one-shot build+serve script.
---

# Wiki Serve

Serves the optional web layer (Search · Browse · Chat) over a built `wiki/`. This
layer is **additive** — it never touches the `/wiki-build` pipeline or its
invariants. Search and Browse need no AI and no backend; only Chat requires the
**agentic-search backend** (`rag/`). There is **NO embedding-index build step** —
retrieval is filesystem/agentic, so nothing needs to be pre-embedded.

## Do this: run the one-shot script

Given that `wiki/` pages already exist, serving is **fully automated end-to-end**.
Do not hand-orchestrate the install/export/build/boot steps — run the
deterministic script:

```bash
python scripts/build_and_serve.py            # build + serve (prod) on :3000 + :8000
# or:  make build-serve
```

The script runs six fail-fast stages and cleans up child processes on Ctrl-C:

1. **preflight** — verify `python`/`pnpm`; resolve config from flags/`.env`; print it.
2. **install** — `pip install -r rag/requirements.txt` + `pnpm install` (skippable).
3. **export** — `export_wiki.py` → `web/public/wiki-index.json` (asserts non-empty).
4. **build** — `rm -rf web/.next` then `pnpm build` (honors the rebuild→restart caveat).
5. **backend** — boot the agentic uvicorn server, poll `/health` until ready (~60s).
6. **frontend** — `pnpm start` (or `pnpm dev`), foreground.

When the script reaches the serve stage it prints a `STATUS {...}` JSON line with
the URLs, the backend PID, and the search-index page count. Report those:

- 🌐 **Web UI** — http://localhost:3000 (Search · Browse · Chat)
- 🔌 **API** — http://localhost:8000 (agentic backend; `/health`, streaming `/api/chat`)

### Common flag recipes

```bash
python scripts/build_and_serve.py --mode dev          # dev server instead of prod
python scripts/build_and_serve.py --verify-only       # build + health-check, then exit 0/nonzero
python scripts/build_and_serve.py --no-serve          # build + boot backend, don't keep serving
python scripts/build_and_serve.py --skip-install --skip-build   # fast re-serve
python scripts/build_and_serve.py --port 4000 --api-port 8100   # custom ports
python scripts/build_and_serve.py --wiki-dir examples/demo-wiki/wiki
make build-serve ARGS="--mode dev"
```

| Flag | Effect |
|---|---|
| `--wiki-dir PATH` | Wiki source dir (relative to repo root). Default `./wiki` or `$WIKI_DIR`. |
| `--mode dev\|start` | Frontend mode. Default `start` (prod build). |
| `--port` / `--api-port` | Frontend / backend ports. Default `3000` / `8000`. |
| `--skip-install` | Skip pip + pnpm install. |
| `--skip-build` | Skip the frontend production build. |
| `--verify-only` | Stages 1-5 + a `/health` check, then shut down cleanly. CI smoke test. |
| `--no-serve` | Build everything and boot the backend, but don't keep serving. |
| `--ci` | `pnpm install --frozen-lockfile`. |

## Generation endpoint for Chat

The agentic backend needs a **generation** endpoint only (no embeddings). It talks
to one OpenAI-compatible endpoint, configured in `.env` (copy `.env.example` → `.env`)
via `RAG_OPENAI_BASE_URL` / `RAG_OPENAI_API_KEY` / `RAG_GEN_MODEL`. Default is local
Ollama's `/v1` (`http://localhost:11434/v1`); point it at any hosted model (OpenAI,
DeepSeek, vLLM, OpenRouter, …) to go remote. Point at a wiki elsewhere with
`RAG_WIKI_ROOT`. Details: `rag/PROVIDERS.md`.

## 🛟 Graceful degradation

Search and Browse run **fully offline** — they need neither the API nor any AI
provider. If the backend is down, only the Chat surface stops working; Search and
Browse still serve from `web/public/wiki-index.json` and the `wiki/` markdown.

## Manual fallback

If you need fine-grained control (e.g. running the two processes in separate
terminals), the underlying steps are:

```bash
make install                              # python + web deps
python scripts/export_wiki.py             # → web/public/wiki-index.json (or: make search-index)
make web-build                            # production build (fresh .next)
make api                                  # agentic uvicorn backend (background) on :8000
make web-start                            # serve production build on :3000
# or: bash scripts/serve.sh / make serve  # api (background) + web (foreground)
```

> ⚠️ **After any `pnpm build` / `make web-build`, restart the running web server.**
> A live `next start` caches the old build manifest in memory; overwriting `.next/`
> without restarting makes hashed CSS/JS 404 and every page render unstyled. The
> one-shot script avoids this by always starting a fresh server.

## Keeping in sync

After a `/wiki-build` (or any wiki edit), re-run the script (or `make search-index`)
to refresh the search index. No index rebuild is needed for Chat — the agentic
backend reads the wiki filesystem live.

## Reference

See `docs/search-and-browse.md`, `docs/web-frontend.md`, `docs/rag-backend.md`,
and `docs/deployment.md`. Full env var list: `.env.example`. Build targets: `make help`.
