# Scripts Reference

This document describes all Python utility scripts in the `scripts/` directory. These scripts handle only deterministic tasks — they never make academic judgments.

## Overview

Nine scripts live in `scripts/`:

1. `pipeline_utils.py` — shared helper library (imported by other scripts)
2. `normalize_filename.py` — derive canonical slug from PDF filename
3. `convert_pdf_to_markdown.py` — convert PDF to raw_markdown outputs
4. `check_links.py` — find broken Obsidian wikilinks
5. `check_orphans.py` — find wiki pages with no inbound links
6. `validate_frontmatter.py` — validate YAML frontmatter on wiki pages
7. `rebuild_index.py` — rebuild directory `_index.md` files
8. `export_metadata.py` — export metadata snapshot to JSON
9. `export_wiki.py` — export the wiki into a single search-index JSON for the optional web UI

Scripts 1–8 serve the core `raw_pdfs → raw_markdown → wiki` pipeline. Script 9 (`export_wiki.py`) feeds the **optional** Search/Browse web layer (see [search-and-browse.md](search-and-browse.md)); it never modifies the wiki.

---

## 1. pipeline_utils.py

**Role**: Shared utility library. Imported by all other scripts. Not run directly.

### Key functions

**`ascii_slugify(text)`** — Converts arbitrary text to lowercase kebab-case ASCII. Normalizes unicode, strips non-alphanumeric, collapses hyphens.

**`parse_pdf_filename(pdf_path)`** — Extracts authors, year, title from a filename. Expected format: `Author and Author - YYYY - Paper Title.pdf`. Returns dict with keys: `authors`, `year`, `title`, `stem`.

**`canonical_slug_from_filename(pdf_path)`** — Builds the canonical slug by combining slugified authors + year + slugified title. Example: `eliaz-and-spiegler-2020-a-model-of-competing-narratives`.

**`sha256_file(path)`** — Computes SHA-256 hash of a file for the metadata sidecar.

**`count_markdown_headings(text)`** — Counts lines starting with `#`.

**`count_words(text)`** — Word count using regex.

**`relative_to_repo(path)`** — Returns path relative to repo root.

**`REPO_ROOT`** — Resolved path to the repository root (parent of `scripts/`).

---

## 2. normalize_filename.py

**Purpose**: Show the canonical slug that would be generated for a PDF.

**Usage**:
```bash
python scripts/normalize_filename.py "raw_pdfs/Author and Author - 2024 - Paper Title.pdf"
# Output: raw_pdfs/Author and Author - 2024 - Paper Title.pdf    author-and-author-2024-paper-title
```

**Use when**: Before running `convert_pdf_to_markdown.py`, to preview and verify the slug.

---

## 3. convert_pdf_to_markdown.py

**Purpose**: Convert one or more PDFs to raw_markdown outputs.

**Usage**:
```bash
python scripts/convert_pdf_to_markdown.py "raw_pdfs/paper.pdf"
python scripts/convert_pdf_to_markdown.py "raw_pdfs/*.pdf"
python scripts/convert_pdf_to_markdown.py "raw_pdfs/paper.pdf" --overwrite
python scripts/convert_pdf_to_markdown.py "raw_pdfs/paper.pdf" --output-root /custom/path
```

**Outputs** (per PDF):
- `raw_markdown/papers/<slug>.md` — converted markdown
- `raw_markdown/metadata/<slug>.json` — metadata sidecar

**Metadata JSON fields**:

| Field | Description |
|---|---|
| `canonical_slug` | Derived slug for this paper |
| `source_pdf` | Relative path to source PDF |
| `source_pdf_name` | Basename of source PDF |
| `markdown_file` | Relative path to output markdown |
| `metadata_file` | Relative path to this sidecar |
| `conversion_tool` | Tool used (markitdown or pdftotext) |
| `conversion_command` | Full command invoked |
| `converted_at` | ISO 8601 timestamp |
| `source_sha256` | SHA-256 hash of source PDF |
| `source_size_bytes` | Size of source PDF in bytes |
| `markdown_size_bytes` | Size of output markdown in bytes |
| `line_count` | Line count of output markdown |
| `heading_count` | Number of headings in output markdown |
| `word_count` | Word count of output markdown |
| `title_guess` | Title inferred from filename |
| `authors_guess` | Authors inferred from filename |
| `year_guess` | Year inferred from filename |
| `conversion_notes` | Any warnings or fallback notes |
| `markitdown_stdout` | Raw stdout from markitdown |
| `markitdown_stderr` | Raw stderr from markitdown |

**Primary tool**: markitdown (installed via `pip install markitdown`)

**Fallback**: pdftotext — activated automatically if markitdown fails with a MediaBox error.

**stdout**: Tab-separated per converted paper:
```
<slug>\t<markdown_file>\t<metadata_file>
```

---

## 4. check_links.py

**Purpose**: Find broken Obsidian wikilinks in wiki pages.

**Usage**:
```bash
python scripts/check_links.py wiki raw_markdown
```

**What it checks**: Every `[[target]]` wikilink in `wiki/` pages — resolves to a `.md` file somewhere in `wiki/` or `raw_markdown/`. Reports links that cannot be resolved.

**Output**: List of broken links with source file and line number.

**Fix protocol**: Update the wikilink in the source page (rename or correct the target name).

---

## 5. check_orphans.py

**Purpose**: Find wiki pages with no inbound wikilinks.

**Usage**:
```bash
python scripts/check_orphans.py wiki
```

**What it checks**: Every `.md` page in `wiki/` — determines whether any other page links to it via `[[pagename]]`. Reports pages that have zero inbound links.

**Exclusions**: `_index.md` files and `log.md` are excluded (they are router files, not content pages).

**Fix protocol**: Add an inbound link from the most relevant concept, mechanism, debate, or `_index.md` page.

---

## 6. validate_frontmatter.py

**Purpose**: Validate YAML frontmatter on all wiki pages.

**Usage**:
```bash
python scripts/validate_frontmatter.py wiki
```

**What it checks**:
- Required fields present per page type (see `wiki/schema/frontmatter-schema.md`)
- `status` field has a valid value
- `type` field matches directory location
- No malformed YAML

**Output**: List of pages with missing or invalid frontmatter fields.

**Fix protocol**: Add or correct the missing fields per `wiki/schema/frontmatter-schema.md`.

---

## 7. rebuild_index.py

**Purpose**: Rebuild `_index.md` router files from actual directory contents.

**Usage**:
```bash
python scripts/rebuild_index.py wiki
```

**What it does**: Scans each wiki subdirectory, reads frontmatter titles, regenerates `_index.md` with a list of pages and one-line descriptions.

**Note**: The script generates structural content only — it does not add academic descriptions. Review and enrich after rebuild.

---

## 8. export_metadata.py

**Purpose**: Export a consolidated metadata snapshot across all converted papers.

**Usage**:
```bash
python scripts/export_metadata.py --output exports/raw-markdown-metadata.json
```

**Output**: JSON array of metadata objects from all `raw_markdown/metadata/*.json` files. Useful for batch analysis, citation maps, and external tooling.

Runs silently on success (no stdout output).

---

## 9. export_wiki.py

**Purpose**: Walk the `wiki/` layer and emit a single JSON search index consumed by the optional Search/Browse web frontend (`web/`). Powers the client-side MiniSearch index on `/search` and the page list on `/wiki`. Part of the additive web layer — it reads the wiki and never modifies it.

**Usage**:
```bash
python scripts/export_wiki.py                                  # defaults
python scripts/export_wiki.py --wiki-dir wiki                  # explicit source
python scripts/export_wiki.py --out web/public/wiki-index.json # explicit output
python scripts/export_wiki.py --also exports/wiki.json         # second copy
python scripts/export_wiki.py --title "My Literature Wiki"     # index title
# Equivalent shortcut:
make search-index
```

**CLI flags**:

| Flag | Default | Description |
|---|---|---|
| `--wiki-dir` | `wiki` | Root of the wiki layer to walk |
| `--out` | `web/public/wiki-index.json` | Primary output path (read by the frontend) |
| `--also` | `exports/wiki.json` | Optional second copy of the same index |
| `--title` | derived | Wiki title stored in the index wrapper |

**Output**: A JSON wrapper carrying `generated_at`, `wiki_title`, `count`, and a `pages` array. Per-page fields: `slug`, `path`, `layer`, `title`, `type`, `status`, `tags[]`, `papers[]`, `headings[]`, `wikilinks_out[]`, `excerpt`, `text`.

**Exclusions** — these are not emitted as pages:
- `_index.md` and any `_`-prefixed file
- Top-level files directly under `wiki/` (e.g., `log.md`)
- The `templates/`, `schema/`, `inbox/`, `scratch/`, and `_raw/` directories

**Dependencies**: Pure stdlib. PyYAML is used for frontmatter when available, with a tolerant hand-rolled fallback parser.

**Caveat**: Re-run after every `/wiki-build` (or `make search-index`) to refresh the index, and restart the web server so it picks up the new file. See [deployment.md](deployment.md).

---

## Automation Boundary

Scripts are strictly for deterministic tasks:

| Task | In scope |
|---|---|
| Filename normalization | Yes |
| PDF conversion (tool invocation) | Yes |
| Link validation | Yes |
| Orphan detection | Yes |
| Frontmatter field validation | Yes |
| Index file generation | Yes |
| Metadata export | Yes |
| Academic judgment | No |
| Content synthesis | No |
| Stub upgrades (requires LLM assessment) | No |
| Cross-paper pattern detection | No |
