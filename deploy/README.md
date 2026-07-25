# 🚀 Deploying literature-wiki

The app is two processes:

| Service | What | Default port | Command |
|---|---|---|---|
| ⚙️ **API** | FastAPI / uvicorn agentic-search chat backend (`rag/`) | 8000 | `uvicorn rag.server:app --host 0.0.0.0 --port <port>` |
| 🌐 **Web** | Next.js frontend (`web/`) | 3000 | `pnpm build` then `pnpm start` |

The backend answers ONLY by agentic filesystem navigation — there is **no index to
build**. It just needs one **OpenAI-compatible** generation endpoint
(`RAG_OPENAI_BASE_URL`), defaulting to local **Ollama**'s `/v1`; point it at any
hosted model to swap it in. All config lives in `.env` (copy from `../.env.example`).

How the browser finds the API: the frontend derives the API base from
`window.location` host + `NEXT_PUBLIC_BACKEND_PORT` at runtime (no baked IP), so a
single build works from localhost, LAN, or a VPN address. To force a fixed origin
(e.g. behind a reverse proxy), set `NEXT_PUBLIC_API_URL`.

Three ways to run it, from most to least portable:

---

## 1. 🐳 Docker Compose (recommended, portable)

From the repo root:

```bash
cp .env.example .env          # edit as needed
docker compose up --build     # api :8000, web :3000  (no index build needed)
```

GPU / Ollama is **external** — it is not containerised. Run Ollama on the host and
set `RAG_OPENAI_BASE_URL=http://host.docker.internal:11434/v1` in `.env`, or point
`RAG_OPENAI_BASE_URL` (+ `RAG_OPENAI_API_KEY` / `RAG_GEN_MODEL`) at any hosted endpoint.
See `../docker-compose.yml` for the service definitions.

---

## 2. 🛠️ Makefile / serve.sh (development)

```bash
make install        # python deps + pnpm deps
make search-index   # build the frontend search index (Search/Browse; no RAG index)
make serve          # api (background) + web (foreground)
# or run them separately:
make api            # uvicorn on 0.0.0.0:$RAG_PORT
make web-dev        # next dev on :3000
```

There is **no RAG index to build** — the chat backend is agentic-only. The only
build artefact is the frontend search index (`make search-index`, for the Search and
Browse surfaces). The serve step starts the API, waits for `/health`, then runs the
frontend.

---

## 3. 🍎 launchd (macOS, always-on)

Two `LaunchAgent` templates auto-start at login and restart on crash, bound to
`0.0.0.0` (LAN/VPN reachable). They are **templates** with `__PLACEHOLDER__`
tokens — fill them, then install into `~/Library/LaunchAgents/`.

Placeholders:

| Token | Meaning | Example |
|---|---|---|
| `__REPO_ROOT__` | Absolute path to this repo | `/Users/you/literature-wiki` |
| `__PYTHON__` | Python interpreter (with deps installed) | `/Users/you/miniconda3/envs/sci/bin/python` |
| `__NODE__` | Node interpreter | `/Users/you/.nvm/versions/node/v22.22.0/bin/node` |
| `__PATH__` | `PATH` for the agent (include python/node bin dirs) | `/Users/you/.../bin:/usr/local/bin:/usr/bin:/bin` |
| `__API_PORT__` | API port | `31491` |
| `__WEB_PORT__` | Web port | `31490` |
| `__LOG_DIR__` | Log directory (created below) | `/Users/you/Library/Logs/litwiki` |

Fill the templates with a sed one-liner (adjust the values), writing the
installed copies straight into `~/Library/LaunchAgents/`:

```bash
REPO_ROOT="$(pwd)"
PYTHON="$(command -v python)"
NODE="$(command -v node)"
BIN_PATH="$(dirname "$PYTHON"):$(dirname "$NODE"):/usr/local/bin:/usr/bin:/bin"
API_PORT=31491; WEB_PORT=31490
LOG_DIR="$HOME/Library/Logs/litwiki"; mkdir -p "$LOG_DIR"

for svc in api web; do
  sed -e "s|__REPO_ROOT__|$REPO_ROOT|g" \
      -e "s|__PYTHON__|$PYTHON|g" \
      -e "s|__NODE__|$NODE|g" \
      -e "s|__PATH__|$BIN_PATH|g" \
      -e "s|__API_PORT__|$API_PORT|g" \
      -e "s|__WEB_PORT__|$WEB_PORT|g" \
      -e "s|__LOG_DIR__|$LOG_DIR|g" \
      "deploy/litwiki-$svc.plist.template" \
      > "$HOME/Library/LaunchAgents/litwiki-$svc.plist"
done
```

Build the frontend before loading the web agent (`next start` serves the built
`.next/`, not live source):

```bash
cd web && NODE_OPTIONS="" pnpm build && cd ..
launchctl load -w ~/Library/LaunchAgents/litwiki-api.plist
launchctl load -w ~/Library/LaunchAgents/litwiki-web.plist
```

Manage:

```bash
launchctl list | grep litwiki                          # status
launchctl kickstart -k gui/$(id -u)/litwiki.web        # restart web (after rebuild)
launchctl kickstart -k gui/$(id -u)/litwiki.api        # restart api
launchctl unload ~/Library/LaunchAgents/litwiki-{api,web}.plist   # stop / disable
```

Logs: `$LOG_DIR/{api,web}.{out,err}.log`. Rebuild the UI (`pnpm build`) and
`kickstart` the web agent whenever frontend code or `NEXT_PUBLIC_*` env changes.

---

## 🐧 Alternative: systemd (Linux always-on)

On Linux, run the two processes as user services instead of launchd. Create
`~/.config/systemd/user/litwiki-api.service`:

```ini
[Unit]
Description=literature-wiki API
After=network.target

[Service]
WorkingDirectory=/abs/path/to/literature-wiki
Environment=RAG_HOST=0.0.0.0 RAG_PORT=8000 RAG_OPENAI_BASE_URL=http://localhost:11434/v1
ExecStart=/abs/path/to/python -m uvicorn rag.server:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
```

Then `systemctl --user enable --now litwiki-api` (and an analogous
`litwiki-web.service` running `pnpm start -H 0.0.0.0 -p 3000` from `web/`). Use
`loginctl enable-linger $USER` so the services survive logout.
