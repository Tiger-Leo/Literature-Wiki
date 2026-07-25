# Frontend ↔ backend integration contract

The frontend (this `web/` Next.js app, assistant-ui 0.14) talks to the Python
FastAPI backend in `../rag/server.py`. Base URL: `process.env.NEXT_PUBLIC_API_URL`
(default `http://localhost:8000`).

## Backend endpoints

| Method | Path | Body | Returns |
|---|---|---|---|
| POST | `/api/chat` | `{ messages: ThreadMessageLike[], deep?: boolean, mode?: "rag"\|"agentic", paper? }` | streaming **NDJSON** (`application/x-ndjson`, one JSON event per line) |
| GET | `/api/threads` | — | `[{ id, title, status }]` (status: `regular`\|`archived`) |
| POST | `/api/threads` | `{ localId? }` | `{ id, title, status }` |
| GET | `/api/threads/{id}` | — | `{ id, title, status }` |
| PATCH | `/api/threads/{id}` | `{ title? , status? }` | `{ ok: true }` |
| DELETE | `/api/threads/{id}` | — | `{ ok: true }` |
| POST | `/api/threads/{id}/title` | `{ messages }` | `{ title }` |
| GET | `/api/threads/{id}/messages` | — | `[{ id, parent_id, role, format, content }]` |
| POST | `/api/threads/{id}/messages` | `{ id, parent_id, format, content, role? }` | `{ ok: true }` |
| GET | `/api/threads/{id}/export?format=md\|json` | — | file download (`text/markdown` or `application/json`) |

Notes:
- `/api/chat` streams **NDJSON** (`Content-Type: application/x-ndjson`), one JSON
  object per line. Event types: `{type:"status",label}` (pipeline stage),
  `{type:"sources",sources}` (provenance), `{type:"delta",text}` (answer chunk —
  accumulate), `{type:"done"}`, `{type:"error",message?}`. The `ChatModelAdapter`
  reads `response.body`, buffers partial lines, `JSON.parse`s each, accumulates
  `delta.text`, and yields `{ content:[{type:"text",text: accumulated}], metadata:{custom:{sources}} }`.
- Archive/unarchive are done via `PATCH {status:"archived"|"regular"}` (there is no
  `/archive` sub-route).
- `content` for stored messages is whatever the history adapter's `fmt.encode` produces,
  sent as-is; the backend stores it verbatim and returns it for `fmt.decode`.
- Request body: `{ messages }` only — no mode/flag fields. The backend always runs the
  agentic filesystem-navigation path (no embeddings, no index, no mode toggle); there is
  no RAG-vs-agentic switch in the UI.
- `GET /api/page/{slug}` returns `{ slug, path, layer, title, type, status, markdown, found }`
  — the off-disk fallback for `/wiki/[slug]` when an API base is configured. The frontend
  fetches it with `cache:"force-cache"` (an uncached fetch would flip the statically
  generated route to dynamic, which Next 16 rejects).

## Runtime composition (the key pattern)

```tsx
const runtime = useRemoteThreadListRuntime({
  runtimeHook: () => useLocalRuntime(chatAdapter),
  adapter: threadListAdapter,  // includes unstable_Provider injecting the history adapter
});
// <AssistantRuntimeProvider runtime={runtime}> ... </AssistantRuntimeProvider>
```

- `chatAdapter`: `ChatModelAdapter` streaming from `POST /api/chat`.
- `threadListAdapter`: `RemoteThreadListAdapter` → `/api/threads*`, with
  `unstable_Provider` wrapping a `ThreadHistoryAdapter` (`withFormat`) →
  `/api/threads/{remoteId}/messages` for per-thread message persistence.

## Chat surface components (this contract)

This contract covers the **Chat** surface (`/`). The Search and Browse surfaces
read static/filesystem data and do not touch this backend — see
[`README.md`](README.md) and [`NOTES-frontend.md`](NOTES-frontend.md).

- `src/lib/api.ts` — `API_URL` resolution + tiny fetch helpers.
- `src/lib/chat-adapter.ts` — streaming `ChatModelAdapter` (NDJSON; posts `{ messages }`).
- `src/lib/chat-status.ts` — module-level store for the pipeline-stage status pill.
- `src/lib/thread-list-adapter.tsx` — `RemoteThreadListAdapter` + history `unstable_Provider`.
- `src/lib/runtime-provider.tsx` — `MyRuntimeProvider` composing the two.
- `src/components/assistant-ui/thread.tsx` — Gemini-styled Thread (markdown replies, pill composer, status pill).
- `src/components/assistant-ui/thread-list.tsx` — thread-history sidebar (New + items + rename/delete); optional `onNavigate` closes the mobile drawer on selection/new-chat.
- `src/components/sources-panel.tsx` — renders the `sources` provenance from chat metadata.
- `src/components/export-button.tsx` — downloads `/export?format=md`.
- `src/app/page.tsx` — Chat layout: persistent thread-list sidebar on desktop, hamburger + slide-in drawer (with scrim) below `md`, main chat column + export button.
- `src/app/layout.tsx` — wraps children in `MyRuntimeProvider` and the top `Nav`; imports styles.

## Run

```bash
# backend (sci env, from literature-wiki/):
uvicorn rag.server:app --port 8000
# frontend:
cd web && pnpm dev   # http://localhost:3000
```
