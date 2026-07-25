# 🔍 Search and Browse (the no-AI layer)

The wiki ships with a **static, zero-backend** way to read and find pages. Two of
the frontend's three surfaces — **Search** (`/search`) and **Browse**
(`/wiki`, `/wiki/[slug]`) — need no chat backend, no Ollama, no API key, and no
network beyond serving the static Next.js bundle. They work straight off the
filesystem and a single prebuilt JSON index. The third surface, **Chat**, is the
optional AI layer documented in [rag-backend.md](rag-backend.md).

This is the recommended path for "just let people read and search the wiki" — it
is the most portable thing the repo produces. See also: [web-frontend.md](web-frontend.md)
for the app as a whole, [deployment.md](deployment.md) for shipping it.

---

## 🧱 The two static surfaces

| Surface | Route | Data source | Backend? |
|---|---|---|---|
| **Search** | `/search` | `web/public/wiki-index.json` (client-side MiniSearch) | No |
| **Browse / View** | `/wiki`, `/wiki/[slug]` | `WIKI_DIR` markdown on the server filesystem | No |

Both are fully decoupled from the chat backend. If the backend is down, missing, or
never installed, Search and Browse keep working.

---

## 📇 The search index: `scripts/export_wiki.py`

`scripts/export_wiki.py` walks `WIKI_DIR`, parses each page's frontmatter +
body, and emits a single JSON file the Search page loads in the browser. It is
pure stdlib (PyYAML used for frontmatter when present, with a tolerant "yamlish"
fallback for the repo's hand-rolled frontmatter format).

```bash
# from the repo root
python scripts/export_wiki.py                       # → web/public/wiki-index.json (+ exports/wiki.json)
python scripts/export_wiki.py --wiki-dir examples/demo-wiki/wiki \
    --out web/public/wiki-index.json --title "Demo Wiki"
```

CLI flags: `--wiki-dir` (default `wiki`), `--out` (default
`web/public/wiki-index.json`), `--also` (a second copy, default
`exports/wiki.json`), `--title` (overrides the wiki title; otherwise taken from
the `wiki/_index.md` H1, else `"Literature Wiki"`).

**What it excludes:** `_index.md`, `README.md`, and any page under `templates/`,
`schema/`, `inbox/`, or `_raw/`. Everything else under `WIKI_DIR/**/*.md` becomes
one record.

### JSON contract

The output wrapper:

```json
{
  "generated_at": "2026-06-01T13:13:23Z",   // ISO-8601 UTC, Z-suffixed
  "wiki_title": "Literature Wiki",
  "count": 42,
  "pages": [ /* one object per page, sorted by (layer, slug) */ ]
}
```

Each page object:

```json
{
  "slug": "spaced-repetition",          // filename stem
  "path": "concepts/spaced-repetition.md", // posix path relative to WIKI_DIR
  "layer": "concepts",                  // first path segment
  "title": "Spaced Repetition",         // frontmatter title || first H1 || humanized slug
  "type": "concept",                    // frontmatter type || singular of layer
  "status": "active",                   // frontmatter status || ""
  "tags": ["memory", "learning"],       // frontmatter array (inline or block)
  "papers": ["luhmann-1992"],           // frontmatter papers || falls back to authors || []
  "headings": ["Definition", "Formal model"],  // all ## / ### heading text
  "wikilinks_out": ["zettelkasten"],    // unique [[target]] slugs (alias/anchor/path stripped)
  "excerpt": "First ~280 chars of the body…",   // post-frontmatter, post-H1, flattened
  "text": "full flattened searchable body"      // markdown markup removed; LaTeX math kept verbatim
}
```

Notes on `text` (the field MiniSearch indexes most heavily): wikilinks are
flattened (`[[a|b]]`→`b`, `[[a]]`→`a`), callout markers and blockquote/heading
markers are stripped (heading *text* kept), emphasis/code/list/table markup is
collapsed, and **LaTeX math (`$…$`, `$$…$$`) is preserved verbatim** so the
client can render it.

---

## 🔎 The Search page (`/search`)

A client component loads `public/wiki-index.json`, builds a
[MiniSearch](https://github.com/lucaong/minisearch) index over `title`, `text`,
`headings`, and `tags` (fuzzy + prefix matching), and renders debounced live
results with highlighted snippets and layer/type filter chips. Each result links
to `/wiki/{slug}`. If the index file is missing, the page tells you to run
`scripts/export_wiki.py` rather than erroring. All of this runs in the browser —
no server round-trip per keystroke.

---

## 🗂️ The Browse page (`/wiki`) and page view (`/wiki/[slug]`)

Browse and View read the wiki markdown **directly from the server filesystem**
via `src/lib/wiki-fs.ts` (a `server-only` module), rooted at `WIKI_DIR` (default
`../wiki`, relative to `web/`; may be absolute).

Both routes sit inside a **two-pane layout** (`src/app/wiki/layout.tsx`):

- **Left category sidebar** (`src/components/wiki-sidebar.tsx`) — collapsible
  groups by layer, per-group page counts, an active-page highlight, and a search
  box; large groups collapsed by default. Persistent on desktop, a slide-in
  drawer (hamburger) on mobile.
- **Center reading column** — the overview or a single page.
- **Right "On this page" TOC** (`src/components/wiki-toc.tsx`) — desktop only,
  built from the current page's headings.

The pages that fill the reading column:

- **`/wiki`** — a server component (`src/app/wiki/page.tsx`) rendering an overview
  of every page grouped by layer as section cards, with per-layer counts.
- **`/wiki/[slug]`** — a server component that loads the page from disk, strips
  the frontmatter, and renders the body through the shared client renderer
  (`src/components/wiki-markdown.tsx`): `[[wikilinks]]`, Obsidian `> [!callouts]`,
  GFM, and KaTeX math. `generateStaticParams()` prerenders every page at build
  time, so View is fully static.

If a slug is not found on disk **and** an API base is configured
(`NEXT_PUBLIC_API_URL` / `NEXT_PUBLIC_BACKEND_PORT`), View falls back to
`GET /api/page/{slug}` on the agentic backend — but this is purely optional gravy;
with the backend off, only on-disk pages resolve, which is every page the
exporter sees.

The frontmatter-stripping and title-resolution logic in `wiki-fs.ts` mirrors
`scripts/export_wiki.py` (same excluded dirs, same first-H1/title fallback), so
Browse and Search agree on what counts as a page and what its title is.

---

## 🔄 Rebuilding after you edit the wiki

The search index is a **build-time snapshot** — it does not auto-update. After
adding or editing wiki pages (e.g. after a `/wiki-build` run), regenerate it:

```bash
python scripts/export_wiki.py        # rebuild web/public/wiki-index.json
# or, equivalently:
make search-index                     # same thing, loads .env first
```

Browse/View read markdown live, so they reflect edits on the next request (dev)
or next `pnpm build` (production prerender). Search only reflects edits after the
exporter re-runs. `scripts/serve.sh` and `scripts/build_and_serve.py` run the
exporter for you; the standalone target is `make search-index`.
