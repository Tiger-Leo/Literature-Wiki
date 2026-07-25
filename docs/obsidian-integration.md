# Obsidian Integration

This document covers Obsidian-specific conventions used in the narrative-wiki project.

## Why Obsidian-Flavored Markdown

The wiki is designed to be opened in Obsidian as well as navigated by AI agents. Obsidian's wikilink format provides:

- Human-readable navigation in Obsidian
- Agent-navigable links (agents resolve `[[Page Name]]` by searching for matching filenames)
- Graph view for visual exploration of concept relationships
- Dataview compatibility for future query features

The wiki does NOT require Obsidian to function — Claude Code can work with it entirely via the filesystem. Obsidian is one optional viewer; the template also ships an optional Search/Browse/Chat web frontend (see [search-and-browse.md](search-and-browse.md)). Neither is required.

## Wikilink Conventions

### Basic wikilinks

```markdown
[[Page Name]]                    # link to a page
[[Page Name#Heading]]            # link to a specific heading
[[Page Name|Display Text]]       # link with custom display text
![[Page Name]]                   # embed a page
![[image.png]]                   # embed an image
![[paper.pdf]]                   # embed a PDF
```

### Cross-layer linking

The canonical provenance chain is:

```
[[synthesis/overview]] → [[sources/author-year-title]] → [[raw_markdown/papers/slug]] → raw PDF
```

Source pages MUST include: `raw_markdown: "[[raw_markdown/papers/<slug>.md]]"` in frontmatter.

### Wikilink resolution

Links use the page name without path prefix. Obsidian resolves by filename. Scripts resolve by searching `wiki/` and `raw_markdown/` recursively.

**Correct**: `[[eliaz-and-spiegler-2020-a-model-of-competing-narratives]]`
**Incorrect**: `[[wiki/sources/eliaz-and-spiegler-2020-a-model-of-competing-narratives]]`

### When to use wikilinks vs prose citations

| Context | Format |
|---|---|
| Within wiki pages (cross-links) | `[[slug]]` |
| In prose query answers | "Author et al. (Year)" |
| In frontmatter `papers:` lists | slugs (bare strings, no brackets) |

## YAML Frontmatter

All canonical wiki pages begin with YAML frontmatter:

```yaml
---
title: "Page Title"
type: source | concept | mechanism | method | measure | debate | synthesis
authors: ["Last, First"]     # source pages only
year: 2024                    # source pages only
slug: author-year-title       # source pages only
papers: [slug1, slug2]        # cross-reference pages
tags: [narrative, experiment] # optional
status: stub | active | canonical | draft | resolved
created: YYYY-MM-DD           # synthesis pages
raw_markdown: "[[...]]"       # source pages
---
```

Frontmatter is validated by `scripts/validate_frontmatter.py`.

## `_index.md` as Router

Every directory contains `_index.md`. These are not regular notes — they are router files for both humans and agents:

```markdown
# Concepts Directory

## Purpose
Cross-paper concept definitions. Each page covers one recurring concept.

## Pages
- [[concept-a]] — Brief description of concept A
- [[concept-b]] — Brief description of concept B
- [[concept-c]] — Brief description of concept C

## Navigation
- Read this file first to find the right concept page.
- If a concept page has status: stub, drill to source pages listed in its Linked Pages section.
- Return to [[wiki/_index]] to navigate other wiki sections.
```

## Obsidian Setup (optional)

To use this wiki in Obsidian:

1. Open the repository root as an Obsidian vault
2. Enable "Use [[Wikilinks]]" in Settings > Files and Links
3. Set attachment folder to `raw_markdown/assets/`
4. Consider installing the Dataview plugin for advanced queries

The vault works without any Obsidian plugins — core wikilinks and frontmatter are standard.

## Graph View Tips

In Obsidian Graph view:

- Source pages connect outward to concept/mechanism/debate pages
- Concept pages are the hubs (many inbound links)
- Synthesis pages connect many source pages (visible as dense clusters)
- Orphan pages (no connections) appear as isolated nodes — use `check_orphans.py` to find them

## Naming and Slug Rules

- All filenames: lowercase kebab-case
- Source page slug format: `author-and-author-year-short-title`
  - Multiple authors: use `and` as separator
  - "et al." shortening only in prose, never in slugs
  - Year: 4 digits
  - Short title: 3-5 meaningful words
- Reserved filename: `_index.md` (directory router, one per directory)
- Disambiguation: if two papers would share a slug, append `-a` / `-b`

**Examples**:

```
eliaz-and-spiegler-2020-a-model-of-competing-narratives.md
barron-and-fries-2023-narrative-persuasion.md
dimant-et-al-2025-strategic-behavior-with-tight-loose-and-polarized-norms.md
```

## Tag Conventions

Tags in the frontmatter `tags:` field:

| Category | Examples |
|---|---|
| Research topic | Use your domain's key concepts, e.g. `learning`, `equilibrium`, `incentive` |
| Method | `experiment`, `theory`, `survey`, `field-experiment` |
| Status | not used in `tags:` — use the `status:` field instead |

Tags are optional but enable Obsidian tag filtering and future Dataview queries.
