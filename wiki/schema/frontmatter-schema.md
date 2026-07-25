---
title: Frontmatter Schema
type: schema
---

# Frontmatter Schema

All canonical wiki pages use YAML frontmatter. Required fields differ by page type.

## Source Pages (`wiki/sources/`)

```yaml
---
title: "Full paper title"
authors: ["Last, First", "Last, First"]
year: 2024
slug: author-author-year-short-title
tags: [concept-tag, method-tag]
raw_markdown: "[[raw_markdown/papers/slug.md]]"
status: draft | canonical
---
```

Required: `title`, `authors`, `year`, `slug`, `raw_markdown`, `status`
Optional: `tags`, `journal`, `doi`, `abstract`

## Concept, Mechanism, Method, Measure Pages

```yaml
---
title: "Concept Name"
type: concept | mechanism | method | measure
tags: [related-tag]
papers: [slug1, slug2]
status: stub | active
---
```

Required: `title`, `type`, `status`
Optional: `tags`, `papers`

## Debate Pages (`wiki/debates/`)

```yaml
---
title: "Debate Title"
type: debate
papers: [slug1, slug2]
status: stub | active | resolved
---
```

Required: `title`, `type`, `status`
Optional: `papers`

## Synthesis Pages (`wiki/synthesis/`)

```yaml
---
title: "Synthesis Title"
type: synthesis
papers: [slug1, slug2]
created: YYYY-MM-DD
---
```

Required: `title`, `type`, `created`
Optional: `papers`

## Status Values

- `stub` — page exists but has minimal content; anchor links are valid but body is thin
- `active` — substantive Wikipedia-style content with cross-links present
- `canonical` — used on source pages — fully built and linked
- `resolved` — used on debate pages — the question has been answered to the wiki's satisfaction
