---
title: Page Rules
type: schema
---

# Page Rules

## Obsidian Wikilink Format

- Use `[[Page Name]]` or `[[slug]]` for internal links to other wiki pages.
- Use `[[Page Name#Heading]]` to link to a specific section.
- Use `![[file.pdf]]` or `![[Note Name]]` for embeds when appropriate.
- Do not use relative markdown links (`[text](../path.md)`) for wiki-to-wiki navigation.

## Link Targets

- Link to the page slug, not the full path: `[[author-and-author-year-short-title]]`.
- When linking from a source page to raw markdown, use: `[[raw_markdown/papers/<slug>]]`.
- When citing a paper from a synthesis page, use: `[[<slug>]]` (resolves to the source page).

## Cross-Linking Rules

- Every source page must link to at least one synthesis page (concept / mechanism / method / measure / debate / synthesis).
- Every synthesis page must end with a `## See also` section listing related synthesis pages plus 5–10 major source pages.
- Every wikilink must resolve to an existing page or a page scheduled to be created in the current `/wiki-build` round.
- Orphan pages (no inbound links) are flagged by `scripts/check_orphans.py`.

## Knowledge Separation (Inline, Not as Architecture)

Synthesis pages distinguish three claim levels — but **never** as separate top-level sections. They appear inline:

| Level | What it is | How to mark inline |
|---|---|---|
| **Paper claim** | What one paper asserts | Inline `[[slug]]` next to the claim |
| **Cross-paper pattern** | Pattern across ≥2 papers | Italicised generalisation + multi-citation in parentheses |
| **Current assessment** | Wiki's current best judgment with date | Short `> **Current assessment (YYYY-MM):** ...` callout |

A section titled "Paper Claims" or "Cross-Paper Patterns" is an automatic REVISE trigger. See `.claude/skills/wiki-build/rubric.md` for the full quality bar.

## Provenance Chain

The expected chain for any claim in a synthesis page:

`synthesis page → raw_markdown/papers/<slug>.md → raw_pdfs/<original>.pdf`

Note: the chain skips the source page. Writers and reviewers base substantive claims on the raw markdown, not on the source page (which is a derived summary that can flatten or mislead).

## Markdown Conventions

- Use ATX headings (`#`, `##`, `###`).
- Use fenced code blocks with language tags.
- Use LaTeX in `$...$` (inline) or `$$...$$` (block) for math.
- Prefer bullet lists only for genuine enumerations (e.g., five firm configurations, three boundary conditions). Do not use bullets as the dominant prose mode in a synthesis page.
- Keep YAML frontmatter at the top of every canonical page.
