# 📚 Demo Wiki — Knowledge Management

A tiny, **domain-neutral** demonstration corpus so the literature-wiki template
(and its new search / browse / RAG frontend) runs **out-of-the-box** without
exposing any real research domain. The theme — *the science of note-taking and
personal knowledge management* — is generic and self-explanatory.

## 🗂 What's here

This corpus uses the **canonical wiki repo layout** — a `wiki/` knowledge layer
plus a sibling `raw_markdown/papers/` Tier-B layer — so it works for the frontend
and the RAG backend with no symlink hacks, and doubles as a layout reference.

```
examples/demo-wiki/                     # ← repo root (RAG_WIKI_ROOT points here)
├── wiki/                               # ← knowledge layer (WIKI_DIR points here)
│   ├── _index.md                       # wiki landing page (heading → wiki_title)
│   ├── concepts/
│   │   ├── spaced-repetition.md        # concept · inline math $R = e^{-t/S}$ · [!note] · wikilink
│   │   └── zettelkasten.md             # concept · links back + cites [[luhmann-1992]]
│   ├── mechanisms/
│   │   └── active-recall.md            # mechanism · [!tip] · display math $$...$$
│   ├── debates/
│   │   └── digital-vs-paper.md         # debate · multi-cite ([[a]]; [[b]])
│   └── sources/
│       └── luhmann-1992.md             # source · title/authors/year/slug/status
├── raw_markdown/
│   └── papers/
│       └── luhmann-1992.md             # Tier-B raw source text for the RAG demo
└── README.md                           # this file
```

Every page carries full, schema-valid frontmatter and exercises **all** wiki
conventions: encyclopedic lead paragraphs, subject-matter section headings,
integrated `[[wikilink]]` citations, Obsidian `> [!type]` callouts, and LaTeX
math (`$inline$` and `$$display$$`).

## ▶️ Build the frontend fixture from this corpus

```bash
python scripts/export_wiki.py \
  --wiki-dir examples/demo-wiki/wiki \
  --out web/public/wiki-index.json \
  --also exports/demo-wiki.json \
  --title "Demo Wiki — Knowledge Management"
```

## 🎯 Pointing the frontend / RAG at the demo

The frontend and the RAG backend point at **different levels** of the same tree:

- **Frontend search/browse** reads the knowledge layer, so it points at the
  `wiki/` subdir:

  ```bash
  # exporter (build the client-side search index):
  python scripts/export_wiki.py --wiki-dir examples/demo-wiki/wiki \
    --out web/public/wiki-index.json --title "Demo Wiki — Knowledge Management"
  # frontend dev/build (Browse reads *.md from here, server-side, no backend):
  cd web && WIKI_DIR=../examples/demo-wiki/wiki pnpm dev
  ```

- **Agentic Chat backend** reads the whole repo, so it points at the **repo root**
  (the dir holding `wiki/` + `raw_markdown/`) via `RAG_WIKI_ROOT`. There is **no
  index to build** — it navigates the filesystem live at query time. To serve it:

  ```bash
  RAG_WIKI_ROOT=examples/demo-wiki python scripts/build_and_serve.py
  ```

  From `RAG_WIKI_ROOT` the backend derives `WIKI_DIR=<root>/wiki` (Tier-A
  synthesis pages) and `RAW_DIR=<root>/raw_markdown/papers` (Tier-B raw text).
  Each can also be overridden independently via `RAG_WIKI_DIR`, `RAG_RAW_DIR`,
  and `RAG_SOURCES_DIR`.

The `raw_markdown/papers/` directory matches the real pipeline exactly, so the
RAG demo has both a wiki page (`wiki/sources/luhmann-1992.md`) and its raw source
(`raw_markdown/papers/luhmann-1992.md`).
