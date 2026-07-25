# Literature Wiki — Web Frontend

A domain-agnostic Next.js (App Router) frontend for an AI-native literature wiki.
It exposes **three surfaces**, all branded from a single config and reusable for
any research domain:

| Surface | Route | Needs backend? | Data source |
|---|---|---|---|
| **Chat** | `/` | Yes | FastAPI RAG backend (`/api/chat`, NDJSON stream) |
| **Search** | `/search` | No | `public/wiki-index.json` (client-side MiniSearch) |
| **Browse** | `/wiki`, `/wiki/[slug]` | No | `WIKI_DIR` markdown files (server filesystem) |

Search and Browse work fully offline; only Chat requires the RAG backend. A
persistent top nav (`src/components/nav.tsx`) switches between the three
surfaces with client-side navigation, keeping the assistant-ui runtime mounted.

## Data flow

- **Chat** (`/`) streams **NDJSON** from `POST /api/chat`; thread persistence and
  export use the REST endpoints documented in [`INTEGRATION.md`](INTEGRATION.md).
  Layout (`src/app/page.tsx`) is a thread-history sidebar (`ThreadList`) + main
  chat column. On desktop the sidebar is a persistent column; below `md` it
  collapses behind a **hamburger** into a **slide-in drawer** (with scrim);
  selecting a thread or starting a new chat closes it (`ThreadList`'s
  `onNavigate`).
- **Search** reads `public/wiki-index.json`, an index built by
  `python scripts/export_wiki.py` (run from the repo root). MiniSearch indexes
  `title`, `text`, `headings`, and `tags` with fuzzy + prefix matching; results
  link to `/wiki/{slug}`. If the file is missing the page tells you to run the
  exporter.
- **Browse / View** read the wiki markdown directly from the filesystem via
  `src/lib/wiki-fs.ts` (server-only). The directory is `WIKI_DIR` (default
  `../wiki`, relative to `web/`). The whole `/wiki` segment uses a persistent
  **two-pane shell** (`wiki/layout.tsx`): a left category sidebar
  (`wiki-sidebar.tsx` — collapsible groups by layer with counts, active-page
  highlight, a search box that routes to `/search`, and a mobile slide-in
  drawer), and the right pane content. `/wiki` (`wiki/page.tsx`) is a
  section-card overview; `/wiki/[slug]` is a server component that renders the
  page (frontmatter stripped) through the shared client renderer
  (`src/components/wiki-markdown.tsx` — `[[wikilinks]]`, Obsidian callouts, GFM,
  KaTeX math) and adds a right-hand **"On this page" TOC** (`wiki-toc.tsx`,
  desktop only). `generateStaticParams()` prerenders every page. If a slug is not
  found on disk **and** an API base is configured (`NEXT_PUBLIC_API_URL` /
  `NEXT_PUBLIC_BACKEND_PORT`), it falls back to a cached `GET /api/page/{slug}`.

## Configure

Copy `.env.example` to `.env.local` and set branding + paths:

- `NEXT_PUBLIC_SITE_TITLE` / `_DESCRIPTION` / `_GREETING` / `_PLACEHOLDER`
- `NEXT_PUBLIC_API_URL` / `NEXT_PUBLIC_BACKEND_PORT` (chat backend)
- `WIKI_DIR` (wiki markdown location for Browse/View)

All user-facing strings flow from `src/lib/site-config.ts`.

> **Build-time env caveat:** `NEXT_PUBLIC_*` vars (site title/description/greeting/placeholder) are baked into the bundle at `pnpm build` time, so they must be set *before* building — setting them only at `pnpm start` runtime has no effect.

## Run

```bash
# 1. (optional) build the search index from the wiki, run from repo root:
python scripts/export_wiki.py            # → web/public/wiki-index.json

# 2. frontend dev server:
cd web && pnpm install
WIKI_DIR=../wiki pnpm dev                # http://localhost:3000
#   Demo wiki:  WIKI_DIR=../examples/demo-wiki/wiki pnpm dev

# 3. (optional, for Chat) the RAG backend, from repo root:
uvicorn rag.server:app --port 8000
```

### Build

```bash
# NODE_OPTIONS="" avoids a known worker crash under proxied node preloads.
WIKI_DIR=../examples/demo-wiki/wiki NODE_OPTIONS="" pnpm build
pnpm start                                # serve the production build
```

> **Restart after every rebuild.** A running `pnpm start` server holds the old
> `.next` build; after a fresh `pnpm build` you **must** restart it. A stale
> server against the new build manifest serves 404s for the hashed CSS chunks,
> which shows up as **unstyled pages**. Stop the server, rebuild, then start again.

## Stack

Next.js 16 · React 19 · assistant-ui 0.14 · react-markdown + remark/rehype
(GFM, math/KaTeX, custom `[[wikilink]]` + callout plugins) · MiniSearch ·
Tailwind v4. See [`AGENTS.md`](AGENTS.md) and [`NOTES-frontend.md`](NOTES-frontend.md)
for version-specific quirks.
