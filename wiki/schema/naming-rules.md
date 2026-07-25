---
title: Naming Rules
type: schema
---

# Naming Rules

## Canonical Slug Format

- Lowercase kebab-case only: `author-author-year-short-title`
- No special characters, accents, or spaces
- Example: `eliaz-and-spiegler-2020-a-model-of-competing-narratives`

## Directory Assignment

| Page type | Directory |
|---|---|
| Paper-specific | `wiki/sources/` |
| Concept | `wiki/concepts/` |
| Mechanism | `wiki/mechanisms/` |
| Method | `wiki/methods/` |
| Measure | `wiki/measures/` |
| Debate | `wiki/debates/` |
| Synthesis / comparison | `wiki/synthesis/` |

## Reserved Filenames

- `_index.md` — directory router, one per directory
- `log.md` — append-only wiki event log (`wiki/log.md`)
- `overview.md` — high-level synthesis entry point (`wiki/synthesis/overview.md`)

## Raw Markdown Alignment

- Each source page slug must match its `raw_markdown/papers/<slug>.md` file exactly
- Slugs should be stable — do not rename after a source page is linked from concept/mechanism pages

## Synthesis Slug Convention

- Query output pages use the prefix `query-`: e.g. `query-what-is-a-narrative.md`
- Thematic synthesis pages use a descriptive slug without prefix: e.g. `plausibility-as-binding-constraint.md`
- Never use author names in synthesis or debate slugs — they are cross-paper constructs

## Title Punctuation in Slugs

- Strip parentheses, colons, commas, periods, apostrophes, and quotation marks from titles
- Replace spaces with hyphens
- Preserve hyphens that are intrinsic to a compound word (e.g. `dis-honesty` in the paper title becomes `dis-honesty` in the slug)
- Use the full short-title portion of the slug to distinguish papers with the same author and year

## Preventing Duplicates

- Before creating a new concept, mechanism, method, or measure page, check the relevant `_index.md` for an existing page
- If a concept could belong to two directories, choose the one that is its primary role
- Prefer extending an existing page over creating a near-duplicate
- For concepts that could be named multiple ways (e.g. "norm pluralism" vs "normative pluralism"), always use the shortest canonical form that is unambiguous
