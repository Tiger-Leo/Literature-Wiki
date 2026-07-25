# 🌐 Web Frontend

The `web/` directory is a domain-agnostic **Next.js (App Router)** application
that exposes the wiki through three surfaces — **Search**, **Browse**, and
**Chat** — all branded from a single config and reusable for any research
domain. Search and Browse work fully offline (see
[search-and-browse.md](search-and-browse.md)); only Chat needs the agentic backend
([rag-backend.md](rag-backend.md)). For shipping it, see
[deployment.md](deployment.md).

---

## 🧰 Stack

| Layer | Choice |
|---|---|
| Framework | **Next.js 16** (App Router) — note `web/AGENTS.md`: this is a very new Next.js; read `node_modules/next/dist/docs/` before editing |
| UI runtime | **React 19** |
| Chat UI | **assistant-ui** 0.14 (`@assistant-ui/react`, `react-markdown`, `assistant-stream`) |
| Styling | **Tailwind v4** (CSS-config style; no `tailwind.config.js`) |
| Markdown | **react-markdown** + remark-gfm + remark-math + rehype-katex (KaTeX) + custom `[[wikilink]]` & callout plugins |
| Search | **MiniSearch** (client-side, over `public/wiki-index.json`) |
| Package manager | **pnpm** |

---

## 🧭 The three surfaces + nav

A persistent top nav (`src/components/nav.tsx`) links the three surfaces; the
brand label is `siteConfig.title`.

| Surface | Route | Needs backend? | Source |
|---|---|---|---|
| **Search** | `/search` | No | `public/wiki-index.json` (client MiniSearch) |
| **Browse / View** | `/wiki`, `/wiki/[slug]` | No | `WIKI_DIR` markdown (server filesystem) |
| **Chat** | `/` | Yes | FastAPI agentic backend (`POST /api/chat`, NDJSON) |

Search and Browse are covered in detail in
[search-and-browse.md](search-and-browse.md). This doc focuses on configuration,
markdown conventions, build/run, and the Chat ↔ backend contract.

### 🗂️ Browse layout (two-pane + TOC)

Browse is a **three-column layout** shared by `/wiki` and `/wiki/[slug]`, set up
in `src/app/wiki/layout.tsx`:

- **Left — category sidebar** (`src/components/wiki-sidebar.tsx`): persistent on
  desktop, with collapsible groups by layer, per-group page counts, an
  active-page highlight, and a search box. Large groups are collapsed by default.
- **Center — reading column**: the `/wiki` overview (`src/app/wiki/page.tsx`,
  rendered as section cards) or a single page (`src/app/wiki/[slug]/page.tsx`).
- **Right — "On this page" TOC** (`src/components/wiki-toc.tsx`): desktop only,
  built from the page's headings.

### 💬 Chat layout (responsive thread history)

The Chat surface (`src/app/page.tsx`) pairs the assistant-ui thread with a
thread-history list (`src/components/assistant-ui/thread-list.tsx`): persistent on
desktop, and a **slide-in drawer on mobile**. `thread-list.tsx` takes an
`onNavigate` prop so selecting a thread closes the drawer.

### 📱 Shared mobile drawer pattern

On phones, both the Browse category sidebar (`wiki-sidebar.tsx`) and the Chat
thread-history shell use the **same pattern**: a hamburger toggle reveals a
slide-in drawer over a scrim; tapping the scrim or a navigation target closes it.
This keeps navigation reachable on small screens (the chat history was previously
unreachable on phones).

---

## 🎨 Branding + env vars

All user-facing strings flow from `src/lib/site-config.ts`, fed by `NEXT_PUBLIC_*`
env vars. Copy `web/.env.example` to `web/.env.local` (or set them in the repo
root `.env`) and edit. **`NEXT_PUBLIC_*` vars are inlined at build time** — re-run
`pnpm build` after changing them.

| Var | Purpose |
|---|---|
| `NEXT_PUBLIC_SITE_TITLE` | Browser tab, top-nav brand, sidebar, chat welcome |
| `NEXT_PUBLIC_SITE_DESCRIPTION` | Page metadata description |
| `NEXT_PUBLIC_SITE_GREETING` | Chat welcome heading |
| `NEXT_PUBLIC_SITE_PLACEHOLDER` | Chat composer placeholder |
| `NEXT_PUBLIC_API_URL` | Explicit absolute backend base URL (optional override) |
| `NEXT_PUBLIC_BACKEND_PORT` | Backend port (default `8000`) used in runtime-host resolution |
| `WIKI_DIR` | Server-side path to the wiki markdown (Browse/View); default `../wiki` |

`WIKI_DIR` is **not** a `NEXT_PUBLIC_*` var — it is read server-side by
`wiki-fs.ts`, not baked into the client bundle.

**API base resolution order** (`src/lib/api.ts`): (1) `NEXT_PUBLIC_API_URL` if
set; (2) else, in the browser, `<page-host>:<NEXT_PUBLIC_BACKEND_PORT>` — this is
what makes one build portable across localhost / LAN / VPN without baking an IP;
(3) else `http://localhost:<port>` (SSR fallback).

---

## ✍️ Markdown conventions rendered

The shared renderer (`src/components/wiki-markdown.tsx`, reused by both Browse
and Chat) supports the wiki's Obsidian-flavored conventions:

- **`[[wikilinks]]`** — `[[slug]]` and `[[slug|alias]]` become client-side links
  to `/wiki/{slug}`. Path-style targets (`concepts/foo`, `raw_markdown/papers/bar`)
  are normalized to the basename slug; `.md` and `#anchor` are stripped.
- **`> [!callouts]`** — Obsidian callouts (`> [!note]`, `> [!tip]`, `> [!warning]`,
  …) render as styled, theme-aware callout blocks.
- **`$math$` / `$$math$$`** — LaTeX math via remark-math + KaTeX. LLM-emitted
  delimiter variants (`\(…\)`, `\[…\]`) are normalized to `$…$`/`$$…$$` first.
- **GFM** — tables, task lists, strikethrough, autolinks.

These render identically whether the page came from the filesystem (Browse) or
from a streamed chat answer (Chat).

---

## 🏃 Build / run

```bash
cd web && pnpm install

# dev server (Search + Browse work immediately; Chat needs the backend up)
WIKI_DIR=../wiki pnpm dev                 # http://localhost:3000
#   demo corpus:  WIKI_DIR=../examples/demo-wiki/wiki pnpm dev

# production build + serve
NODE_OPTIONS="" pnpm build                # see workaround note below
pnpm start
```

> ⚠️ **`NODE_OPTIONS="" pnpm build` workaround.** If `NODE_OPTIONS` contains a
> `-r <preload>` (e.g. a proxy preload), the Next build worker crashes with
> `ERR_WORKER_INVALID_EXEC_ARGV`. Clearing `NODE_OPTIONS` for the build avoids it.
> `pnpm dev` is unaffected. The `Makefile` `web-build` target already does this.

From the repo root you can instead use `make web-dev` / `make web-build` /
`make web-start`, or `make serve` to run the API + web together.

---

## 💬 How Chat talks to the agentic backend

The Chat surface (assistant-ui) streams from `POST /api/chat`. The backend always
answers by agentic filesystem navigation (no embeddings/RAG) — there is no `mode`
toggle and no index.

**Request:** `{ "messages": ThreadMessageLike[] }`

**Response: NDJSON** (`application/x-ndjson`), one JSON object per line:

```ts
type NdjsonEvent =
  | { type: "status";  label: string }          // tool step / stage → spinner pill
  | { type: "sources"; sources: SourceRef[] }    // files read → Sources panel
  | { type: "delta";   text: string }            // answer chunk → accumulate
  | { type: "done" }
  | { type: "error";   message?: string };       // → graceful inline ⚠️, no throw

type SourceRef = { slug: string; citekey?: string; layer?: string; tier?: string; heading_path?: string };
```

The adapter accumulates `delta` text, shows `status` labels as a spinner while no
text has arrived, and renders `sources` in a collapsible **Sources** panel whose
entries link to `/wiki/{slug}`. Thread persistence, titles, and export use the
REST endpoints in [rag-backend.md](rag-backend.md) (and `web/INTEGRATION.md`).

### 🛟 Graceful degradation when the backend is offline

The Chat surface fails soft, by design:

- The thread-list adapter's `list()` swallows backend-down errors and returns an
  empty list, so the app still loads.
- `error` events and network/abort failures become an inline `⚠️` message — no
  crash, no console overlay.
- Search and Browse are entirely independent of the backend, so the wiki stays
  fully readable and searchable even with the API down or never installed.
