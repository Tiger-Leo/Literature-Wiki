# 🚀 Quick-Start Guide

Get a Wikipedia-style literature wiki running from scratch.

> **🪟 New Windows machine?** Jump to [Fresh Clone on Windows](#-fresh-clone-on-windows) for a PowerShell-native walkthrough.

---

## 🧰 Prerequisites

| Tool | macOS | Linux | Windows |
|------|-------|-------|---------|
| Python 3.10+ | [python.org](https://www.python.org/downloads/) or `conda` | `sudo apt install python3` or `conda` | [python.org](https://www.python.org/downloads/) or `conda` |
| `markitdown` CLI | `pip install markitdown` | `pip install markitdown` | `pip install markitdown` |
| `pdftotext` *(fallback)* | `brew install poppler` | `sudo apt install poppler-utils` | Skip unless needed (markitdown is primary) |
| Claude Code | [claude.ai/code](https://claude.ai/code) | [claude.ai/code](https://claude.ai/code) | [claude.ai/code](https://claude.ai/code) |
| Git | `brew install git` | `sudo apt install git` | [git-scm.com](https://git-scm.com/) |
| `pnpm` *(for web UI)* | `npm i -g pnpm` | `npm i -g pnpm` | `npm i -g pnpm` |

Verify:

```bash
python --version          # 3.10+
markitdown --version
git --version
```

On Windows (PowerShell):
```powershell
python --version
markitdown --version
git --version
claude --version          # if Claude Code is installed
```

---

## 📂 Directory Layout

The scaffold already exists in this template repo. If starting from scratch, the layout is:

```
your-wiki/
├── raw_pdfs/                  # drop your PDFs here
├── raw_markdown/
│   ├── papers/                # converted markdown
│   ├── metadata/              # JSON sidecars
│   └── assets/                # extracted images
├── wiki/
│   ├── sources/               # one bibliographic page per paper
│   ├── concepts/              # Wikipedia-style concept pages
│   ├── mechanisms/            # Wikipedia-style mechanism pages
│   ├── methods/               # Wikipedia-style method pages
│   ├── measures/              # Wikipedia-style measure pages
│   ├── debates/               # Wikipedia-style debate pages
│   ├── synthesis/             # cross-cutting synthesis pages
│   ├── templates/             # page templates
│   └── schema/                # naming, frontmatter, workflow rules
├── scripts/                   # deterministic validation scripts
├── exports/                   # metadata snapshots
├── agent_tasks/               # multi-agent workspaces (created by /wiki-build)
├── .claude/
│   └── skills/                # the four Claude Code skills
├── CLAUDE.md                  # agent operating instructions
└── _index.md                  # root navigation
```

---

## 🔧 Verify Scripts

```bash
python -m py_compile scripts/*.py
```

No output means all scripts compile.

---

## ⚙️ Customize CLAUDE.md

Edit `CLAUDE.md` at the project root. The minimum:

- Domain description (1–2 sentences on your research area)
- Layer responsibilities (already documented in the template — keep)
- The four operations: `/wiki-build`, `/wiki-query`, `/wiki-synthesis`, `/wiki-update-db`

The template `CLAUDE.md` shipped in this repo is a working starting point — modify the "Purpose" paragraph and you are ready.

---

## 📄 PDF Naming Convention

Before dropping a PDF into `raw_pdfs/`, name it:

```
Author and Author - YYYY - Paper Title.pdf
```

Examples:

```
Smith and Jones - 2022 - A Theory of Learning.pdf
Akerlof and Shiller - 2015 - Phishing for Phools.pdf
```

The `normalize_filename.py` script derives slugs like `smith-and-jones-2022-a-theory-of-learning` from this pattern. Other patterns work but produce imperfect slugs.

---

## 🤖 First Build — Walkthrough

### Step 1 — Drop PDFs

```bash
cp ~/Downloads/*.pdf raw_pdfs/
```

On Windows (PowerShell):
```powershell
Copy-Item "$env:USERPROFILE\Downloads\*.pdf" raw_pdfs\
```

### Step 2 — Open Claude Code

```bash
claude
```

On Windows, if `claude` is not on PATH, use the full path:
```powershell
# Typically installed at:
& "$env:LOCALAPPDATA\npm\claude.ps1"
# Or via npm global install:
npx @anthropic-ai/claude-code
```

The four project-local skills (`/wiki-build`, `/wiki-query`, `/wiki-synthesis`, `/wiki-update-db`) load automatically when Claude Code starts in this directory.

### Step 3 — Run /wiki-build

```
/wiki-build
```

(Default 2 rounds. For a quick first pass on a small corpus, try `/wiki-build 1`.)

### What happens

1. **Phase 0** — Workspace created at `agent_tasks/wikipedia-rewrite_<DATE><HHMM>/`.
2. **Phase 1** — Each new PDF is converted to `raw_markdown/papers/<slug>.md` (deterministic, no agent needed).
3. **Phase 2** — One parallel writer subagent per paper produces a source page at `wiki/sources/<slug>.md`. A light review pass follows.
4. **Phase 3** — A planner subagent inspects the corpus and writes `round-1/plan.md`: which concept / debate / mechanism / measure / method / synthesis pages to create or update, grouped into 6–10 clusters of 2–3 pages each. **The orchestrator shows you a summary of the plan before continuing.** You can edit `plan.md`.
5. **Phase 4 Stage A — Curator** — One subagent reads the plan + the raw markdown of every relevant paper, then writes a structured **brief** per scope page at `round-1/page-briefs/<slug>.md`. Each brief contains: working definition, Wikipedia-style section outline, ≤10 ranked source slugs with paths, three spot-check anchors the reviewer will verify, writing constraints.
6. **Phase 4 Stage B — Cluster writers** (parallel) — one writer per cluster (2–3 pages each), drafting Wikipedia-style synthesis pages to `round-1/rewritten-wiki/<type>/<slug>.md`.
7. **Phase 4 Stage C — Cluster reviewers** (parallel) — one reviewer per ~2 clusters. Three lenses: synthesis quality / fidelity (3 spot-checks against raw papers per page) / coverage and cross-links. Verdict PASS or REVISE.
8. **Phase 4 Stage D — Revisers** (parallel) — apply fix lists, write to `round-1/round-output/<type>/<slug>.md`. PASS pages copied unchanged.
9. **Phase 5** — If reviews still flag substantive issues and round count < requested, round 2 begins (back to Phase 3).
10. **Phase 6** — Copy `final/round-output/` into `wiki/`, run full lint, append to `wiki/log.md`.

You will see ≤200-word status summaries from each subagent. Full pages live on disk; the orchestrator's context stays small.

### Step 4 — Run Lint

`/wiki-build` runs lint as part of Phase 6. Re-run manually any time:

```
/wiki-update-db
```

Or:

```bash
python -m py_compile scripts/*.py
python scripts/check_links.py wiki raw_markdown
python scripts/check_orphans.py wiki
python scripts/validate_frontmatter.py wiki
python scripts/export_metadata.py --output exports/raw-markdown-metadata.json
```

---

## 🔍 First Query

After the build, ask:

```
What is the main concept of [topic X]?
```

```
Compare how papers in this collection treat [topic Y].
```

```
What is the debate about [topic Z]?
```

`/wiki-query` reads the synthesis layer first (encyclopedic concept / mechanism / debate pages), drills to source pages or raw markdown only when needed.

---

## ✏️ Saving a One-Off Insight

If a conversation produces an insight worth one wiki page (concept, debate, mechanism, or synthesis) but you do not want to run a full rebuild:

```
/wiki-synthesis
```

This creates one Wikipedia-style page using the same quality bar as `/wiki-build`. Use this for surgical additions; for new papers, use `/wiki-build`.

---

## 🌐 Run the Web UI (optional)

The core wiki works entirely from the filesystem and via Claude Code skills. On top of it sit two **optional, additive** layers: a Search/Browse/Chat frontend (`web/`) and a RAG backend (`rag/`). They never alter the `/wiki-build` pipeline.

### Quickest path (all platforms, recommended)

```bash
python scripts/build_and_serve.py   # deterministic one-shot: install → export → build → serve API + web
```

On Windows, this is the **recommended** method — it replaces all `make` targets in one command and handles platform differences internally. See [deployment.md](deployment.md) for flags (`--mode dev`, `--verify-only`, `--skip-build`, etc.).

### Browse + Search only (no AI, no backend)

**macOS / Linux (Makefile):**
```bash
make install                      # python + web (pnpm) deps
python scripts/export_wiki.py     # build the search index → web/public/wiki-index.json
make web-build                    # production build of web/
make web-start                    # serve Browse (/wiki) + Search (/search)
```

**Windows / all platforms (manual steps):**
```powershell
pip install -r rag\requirements.txt
cd web; pnpm install; cd ..
python scripts/export_wiki.py
cd web; NODE_OPTIONS="" pnpm build; cd ..
cd web; pnpm start; cd ..
```

### Full path with AI Chat

```bash
python scripts/build_and_serve.py   # same one-shot — handles export + build + api + web
```

Or run `/wiki-serve` inside Claude Code, which orchestrates the same steps.

No index to build — the agentic backend retrieves by navigating `wiki/` + `raw_markdown/` live. It talks to one OpenAI-compatible endpoint (`RAG_OPENAI_BASE_URL`), defaulting to local Ollama's `/v1`; swap in any hosted model via `.env`.

> ⚠️ **Restart the web server after every rebuild.** Re-run `python scripts/export_wiki.py` after each `/wiki-build`, then restart the server so it picks up the new index and pages.

For deployment (docker-compose / launchd / systemd) see [deployment.md](deployment.md); for the layers themselves see [search-and-browse.md](search-and-browse.md), [web-frontend.md](web-frontend.md), and [rag-backend.md](rag-backend.md).

---

## 📐 Batch Sizes

| Corpus size | Recommended round count |
|---|---|
| 1–6 papers | 1 round |
| 7–20 papers | 2 rounds (default) |
| 20+ papers | 2–3 rounds |

`/wiki-build` parallelises within a round (up to 8 cluster writers at a time, batched), so larger corpora are not linearly slower.

---

## 🗂️ Key Files to Know

| File | Role |
|------|------|
| `CLAUDE.md` | Agent operating instructions |
| `_index.md` | Root navigation |
| `wiki/_index.md` | Wiki navigation |
| `wiki/log.md` | Append-only history |
| `.claude/skills/wiki-build/rubric.md` | **The Wikipedia-style quality bar** — read before writing or reviewing |
| `agent_tasks/wikipedia-rewrite_*/` | Build workspaces (round plans, briefs, drafts, reviews) |
| `exports/raw-markdown-metadata.json` | Metadata snapshot |

---

## 🪟 Fresh Clone on Windows

Complete walkthrough from `git clone` to running wiki on a **new Windows PC**. All commands use PowerShell.

### 0. One-time tool installation

```powershell
# Python 3.10+ (miniconda recommended)
# Download: https://docs.conda.io/en/latest/miniconda.html
conda create -n sci python=3.10 -y
conda activate sci

# Core tools
pip install markitdown

# Claude Code
npm i -g @anthropic-ai/claude-code

# Git
winget install Git.Git

# Web UI tools (optional — only if you want the browser interface)
npm i -g pnpm
```

### 1. Clone and configure

```powershell
git clone <your-repo-url> literature-wiki
cd literature-wiki

# Create your .env from the template
Copy-Item .env.example .env

# If using conda, activate your env
conda activate sci
```

### 2. Verify the scaffold

```powershell
# All scripts should compile silently
python -m py_compile scripts/*.py

# Check the wiki scaffold is intact
python scripts/check_links.py wiki raw_markdown
python scripts/validate_frontmatter.py wiki
```

### 3. Drop your PDFs

```powershell
# Name format: Author and Author - YYYY - Paper Title.pdf
Copy-Item "$env:USERPROFILE\Downloads\*.pdf" raw_pdfs\
```

### 4. Build the wiki

Start Claude Code and run the build:

```powershell
claude
```

Then inside Claude Code:

```
/wiki-build          # default 2 rounds; /wiki-build 1 for quick first pass
```

This will:
1. Convert each PDF to `raw_markdown/papers/<slug>.md`
2. Create source pages at `wiki/sources/<slug>.md`
3. Plan and write Wikipedia-style synthesis pages across `wiki/concepts/`, `wiki/mechanisms/`, etc.
4. Review and revise in parallel
5. Run lint and finalise

### 5. (Optional) Run the web UI

```powershell
# One command — handles install, export, build, and serve
python scripts/build_and_serve.py

# Or step-by-step for the no-AI subset:
pip install -r rag\requirements.txt
cd web; pnpm install; cd ..
python scripts/export_wiki.py
cd web; NODE_OPTIONS="" pnpm build; pnpm start
```

Open `http://localhost:3000` — Search (`/search`) and Browse (`/wiki`) work with zero backend.

### 6. Rebuild the search index after wiki changes

```powershell
python scripts/export_wiki.py       # re-run after every /wiki-build
# Then restart the web server
```

### Windows-specific notes

- **`make` is not needed.** All `make` targets in the docs have equivalent `python`/`pnpm` commands listed above. `python scripts/build_and_serve.py` replaces `make serve` / `make api` / `make web-start` in one command.
- **`pdftotext` is optional.** The primary converter is `markitdown` (cross-platform). The `pdftotext` fallback is only invoked if markitdown fails with a MediaBox error — rare in practice.
- **Path separators.** All Python scripts normalise paths internally. You can use either `\` or `/` in commands.
- **`uvicorn` / FastAPI** for the Chat backend works on Windows — `build_and_serve.py` handles process management cross-platform.

---

## ❓ Troubleshooting

**markitdown produces an empty or very short file.** Run the fallback manually: `pdftotext "raw_pdfs/<file>.pdf" raw_markdown/papers/<slug>.md`. Then re-run `/wiki-build`.

**`/wiki-build` says "no new papers" but I just added one.** Check that the PDF is at `raw_pdfs/`, not in a subfolder, and that the filename pattern is `Author - YYYY - Title.pdf` so `normalize_filename.py` can parse it.

**A synthesis page reads like a list of paper summaries.** Either the writer ignored the rubric or the curator's brief was too generic. Open the brief at `agent_tasks/wikipedia-rewrite_*/round-N/page-briefs/<slug>.md` — its `wikipedia_outline` should name sub-topics, not papers. Fix the brief and re-run round N for that page only.

**A reviewer's verdict seems wrong.** Read the review at `agent_tasks/wikipedia-rewrite_*/round-N/reviews/cluster-*.md`. The reviewer's spot-check anchors are checkable — read the raw paper to verify. If the reviewer was wrong, edit the review file before round N+1 (the reviser uses it).

**Pages are orphans (`check_orphans.py` flags them).** Add a wikilink to each from a parent `_index.md` or from the closest concept/mechanism page's `## See also`.

**`validate_frontmatter.py` reports missing fields.** Add the missing field per `wiki/schema/frontmatter-schema.md`.

---

*For scaling to 50+ papers, see [scale-up-guide.md](scale-up-guide.md).*
