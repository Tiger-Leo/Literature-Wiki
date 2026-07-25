# 🚀 Deployment

How to run and share the wiki app. There are two fundamentally different
ambitions, and you should pick before choosing a path:

- **Browse + search only (no AI)** — static, the most portable thing the repo
  produces. No Ollama, no API key, no Python backend. See the minimal path
  below and [search-and-browse.md](search-and-browse.md).
- **Full app with Chat** — adds the optional FastAPI RAG backend
  ([rag-backend.md](rag-backend.md)) and one OpenAI-compatible generation endpoint.

The app is at most **two processes**:

| Service | What | Default port | Command |
|---|---|---|---|
| ⚙️ **API** | FastAPI / uvicorn RAG backend (`rag/`) | 8000 | `uvicorn rag.server:app --host 0.0.0.0 --port <port>` |
| 🌐 **Web** | Next.js frontend (`web/`) | 3000 | `pnpm build` then `pnpm start` |

The full deployment recipes (docker-compose, launchd templates with placeholder
tokens, systemd) live in **`deploy/README.md`**; this doc is the orientation map
and the canonical-config reference. See also [web-frontend.md](web-frontend.md).

> 🤖 **The backend is agentic-search only.** Retrieval navigates the wiki
> filesystem at query time, so there is **no embedding-index build step** — no
> `python -m rag.build_index`, no `make index`, no vector store to populate. The
> only thing the Chat backend needs is **one OpenAI-compatible generation
> endpoint** (`RAG_OPENAI_BASE_URL`, defaulting to local Ollama) and a wiki root.
> Everything below reflects that.

---

## ⭐ One-shot: `scripts/build_and_serve.py` (recommended)

The fastest, most reliable path is the deterministic build+serve script. Given a
built `wiki/`, it is fully automated end-to-end — no hand-orchestration:

```bash
python scripts/build_and_serve.py        # build + serve (prod) on :3000 + :8000
# or:  make build-serve
```

It runs six **fail-fast** stages and traps SIGINT/SIGTERM to reap child
processes cleanly:

1. **preflight** — verify `python` + `pnpm`; resolve config from flags/`.env`; print it.
2. **install** — `pip install -r rag/requirements.txt` + `pnpm install` (skip: `--skip-install`).
3. **export** — `export_wiki.py` → `web/public/wiki-index.json`; asserts the JSON is non-empty.
4. **build** — `rm -rf web/.next` then `pnpm build` (always a fresh build dir — see the caveat below).
5. **backend** — boot the agentic uvicorn server, poll `/health` until ready (~60s; on timeout it dumps the last log lines and exits nonzero).
6. **frontend** — `pnpm start` (or `pnpm dev`), foreground.

In `--verify-only` / `--no-serve` modes it prints a `STATUS {...}` JSON line
(urls, backend pid, search-index page count, warnings) and exits.

### Flags

| Flag | Effect |
|---|---|
| `--wiki-dir PATH` | Wiki source dir relative to repo root. Default `./wiki` or `$WIKI_DIR`. |
| `--mode dev\|start` | Frontend mode. Default `start` (prod build); `dev` runs `pnpm dev`. |
| `--port` | Frontend port. Default `3000`. |
| `--api-port` | Backend port. Default `8000`. |
| `--skip-install` | Skip pip + pnpm install. |
| `--skip-build` | Skip the frontend production build. |
| `--verify-only` | Run stages 1-5 + a `/health` check, then shut down cleanly and exit 0/nonzero. CI smoke test. |
| `--no-serve` | Build everything and boot the backend, but don't keep serving (print status, exit 0). |
| `--ci` | `pnpm install --frozen-lockfile`. |

```bash
python scripts/build_and_serve.py --mode dev
python scripts/build_and_serve.py --verify-only          # CI / smoke check
python scripts/build_and_serve.py --skip-install --skip-build   # fast re-serve
make build-serve ARGS="--port 4000 --api-port 8100"
```

The manual Makefile path below remains available when you want fine-grained
control (separate terminals, custom process supervision).

---

## ⚙️ Canonical config: `.env`

The repo-root `.env.example` is the **single source of truth** for configuration,
matched 1:1 against `rag/config.py` (`RAG_*`) and the frontend (`NEXT_PUBLIC_*`).
Copy it and edit:

```bash
cp .env.example .env          # .env is git-ignored
```

The `Makefile` and `scripts/serve.sh` auto-load `.env`; docker-compose reads it
via `env_file`. Every var is optional — defaults live in `rag/config.py`. **Set
only what you need to override.** Most important per-deployment:

| Var | Set it when… |
|---|---|
| `WIKI_DIR` | Your wiki lives somewhere other than `./wiki` (frontend Browse + the exporter). |
| `RAG_WIKI_ROOT` | The RAG backend points at a wiki repo elsewhere. |
| `RAG_OPENAI_BASE_URL` / `RAG_OPENAI_API_KEY` / `RAG_GEN_MODEL` | The one generation endpoint — local Ollama `/v1` by default, or a hosted model (see [rag-backend.md](rag-backend.md)). |
| `RAG_CORS_ORIGINS` | Exposing the API beyond localhost — **restrict from `*`**. |
| `RAG_HOST` / `RAG_PORT` | Binding the API (use `0.0.0.0` for LAN/VPN). |
| `NEXT_PUBLIC_BACKEND_PORT` | The API port differs from `8000` (browser derives the API base from this + the page host). |
| `NEXT_PUBLIC_API_URL` | Forcing a fixed API origin (reverse proxy / docker cross-host). |
| `NEXT_PUBLIC_SITE_*` | Branding (title/description/greeting/placeholder). |

> `NEXT_PUBLIC_*` vars are **baked into the bundle at build time** — re-run
> `pnpm build` (or `make web-build`) after changing them.

---

## 🪶 Minimal path: just browse + search, no AI

The cheapest, most portable deployment. No backend, no models, no keys:

```bash
python scripts/export_wiki.py            # → web/public/wiki-index.json
cd web && pnpm install
WIKI_DIR=../wiki NODE_OPTIONS="" pnpm build
WIKI_DIR=../wiki pnpm start              # serves Search + Browse on :3000
```

That is it — Search (`/search`) and Browse (`/wiki`) work with zero backend. The
Chat tab will simply degrade gracefully (an inline notice) since no API is
running. Re-run `python scripts/export_wiki.py` (or `make search-index`) whenever
you edit the wiki. Details: [search-and-browse.md](search-and-browse.md).

---

## 🐳 (a) Docker Compose — recommended, portable

```bash
cp .env.example .env
docker compose up --build                       # api :8000, web :3000
```

No index-build step — the agentic backend reads the wiki filesystem at query
time.

Two services (`api`: python:3.12-slim + uvicorn; `web`: node:22-slim + pnpm
build/start). **The generation endpoint is external** — not containerised. Either
run Ollama on the host (it serves the OpenAI protocol at `/v1`) and set
`RAG_OPENAI_BASE_URL=http://host.docker.internal:11434/v1` in `.env`, or point
`RAG_OPENAI_BASE_URL`/`RAG_OPENAI_API_KEY` at a hosted model. Service definitions:
`docker-compose.yml`.

---

## 🛠️ (b) Makefile + `scripts/serve.sh` — local dev

```bash
make install        # python (rag/requirements.txt) + web (pnpm) deps
make search-index   # build the frontend search index (export_wiki)
make serve          # api in background + web in foreground, via scripts/serve.sh
# or separately:
make api            # agentic uvicorn backend on 0.0.0.0:$RAG_PORT
make web-dev        # next dev on :3000
make web-build      # production build (does NODE_OPTIONS="" for you)
```

There is no `make index` — the agentic backend needs no embedding index; just
rebuild the **search** index (`make search-index`) when `wiki/` changes.
`scripts/serve.sh` loads `.env`, rebuilds the search index, starts uvicorn,
polls `/health` until ready (or reports the API log on early exit), then runs the
frontend. `WEB_MODE=start make serve` serves the production build instead of
`pnpm dev`. `make clean` removes `web/.next`.

> For the **no-AI** subset here, you only need `make web-build` +
> `python scripts/export_wiki.py` + `WIKI_DIR` — skip `make api`.

---

## 🍎 (c) launchd — macOS, always-on

`deploy/` ships two `LaunchAgent` **templates** (`litwiki-api.plist.template`,
`litwiki-web.plist.template`) with `__PLACEHOLDER__` tokens
(`__REPO_ROOT__`, `__PYTHON__`, `__NODE__`, `__PATH__`, `__API_PORT__`,
`__WEB_PORT__`, `__LOG_DIR__`). They auto-start at login, restart on crash, and
bind `0.0.0.0` (LAN/VPN reachable). `deploy/README.md` has a `sed` one-liner that
fills the tokens and installs the agents into `~/Library/LaunchAgents/`.

Build the frontend before loading the web agent (`next start` serves the built
`.next/`, not live source), then `launchctl load -w` each plist. Rebuild
(`pnpm build`) and `launchctl kickstart -k gui/$(id -u)/litwiki.web` whenever
frontend code or `NEXT_PUBLIC_*` env changes. Full steps in `deploy/README.md`.

---

## 🐧 Linux always-on: systemd

On Linux, run the two processes as **user services** instead of launchd: a
`litwiki-api.service` running `uvicorn rag.server:app --host 0.0.0.0 --port 8000`
and a `litwiki-web.service` running `pnpm start -H 0.0.0.0 -p 3000` from `web/`,
each with `Restart=always` and a `WorkingDirectory` set to the repo. Use
`loginctl enable-linger $USER` so they survive logout. A ready-to-edit unit file
is in `deploy/README.md`.

---

## 🩺 Troubleshooting

### Every page renders unstyled ("corrupted") after a rebuild

**Symptom.** After running `pnpm build` / `make web-build`, the site loads but
every page is unstyled and the browser console shows 404s for hashed CSS/JS
chunks.

**Cause.** A long-lived `next start` server keeps the **old** build's manifest in
memory. When a new build overwrites `.next/` on disk, the in-memory manifest
still points at the previous build's hashed chunk filenames — which no longer
exist on disk — so those chunks 404 and the pages lose their styling.

**Fix — restart the web service after every build.** The running server must be
restarted so it reloads the fresh manifest:

```bash
# launchd (macOS):
launchctl kickstart -k gui/$(id -u)/litwiki.web

# systemd (Linux):
systemctl --user restart litwiki-web

# Docker Compose:
docker compose restart web
```

For a clean rebuild from scratch:

```bash
rm -rf web/.next && make web-build      # then restart the web service
```

This is also why `make serve` / `scripts/serve.sh` always start a **fresh**
server — they never reuse a stale `next start` process, so they don't hit this
class of problem during local dev.
