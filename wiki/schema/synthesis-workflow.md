---
title: Synthesis Workflow
type: schema
---

# Synthesis Workflow

The `/wiki-synthesis` skill saves a single one-off insight as one wiki page. It is the surgical complement to `/wiki-build`, which builds the whole synthesis layer at once.

For multi-page or whole-collection work, use `/wiki-build`. For lint-only passes, use `/wiki-update-db`.

## When to Create a Synthesis Page

Create a `wiki/synthesis/<slug>.md` when:
- A discussion draws on ≥2 papers and the insight is costly to reconstruct, AND
- No existing concept / mechanism / debate page is the right home, AND
- The insight is cross-cutting (spans multiple sub-topics) rather than confined to one concept

## When to Create a Debate Page

Create a `wiki/debates/<slug>.md` when:
- ≥2 papers make competing or contradictory claims on a precise question
- The tension is genuine (not resolvable by closer reading)
- The disagreement matters for future queries

## When to Create a Concept or Mechanism Page

Create a `wiki/concepts/<slug>.md` or `wiki/mechanisms/<slug>.md` when:
- The construct or causal channel recurs across ≥2 papers
- It does not yet have a page
- The insight justifies an encyclopedic treatment, not just an inline mention on a source page

## When NOT to Create a Page

Do **not** create a page when:
- Only one paper engages the topic (update that paper's source page instead)
- The insight overlaps an existing concept / mechanism / debate page (update that page)
- The conversation that produced the insight was not grounded in the raw papers (the wiki's invariant is that substantive claims trace to `raw_markdown/papers/<slug>.md`)

## Page Quality Bar

The page must meet the same Wikipedia-style bar as `/wiki-build`. Read `.claude/skills/wiki-build/rubric.md`. The non-negotiables:

- Encyclopedic lead paragraph
- Subject-matter backbone (section headings name sub-topics, not papers)
- Integrated citations (multi-cite where claims converge)
- Three knowledge levels visible inline, not as architecture
- Every substantive claim traces to `raw_markdown/papers/<slug>.md`, not to source pages

## Workflow

1. Pick the page template from `wiki/templates/` (concept / mechanism / debate / synthesis).
2. For each paper to cite, open `raw_markdown/papers/<slug>.md` and read the relevant section. Do not lean on source pages.
3. Choose a kebab-case slug.
4. Draft the page into `wiki/<type>/<slug>.md`.
5. Write frontmatter (`title`, `type`, `status`, `papers`, `tags`, `created` for synthesis pages).
6. Self-check against the rubric's automatic REVISE triggers.
7. Add a `## See also` section with wikilinks to related pages and a small set of source pages.
8. Add a wikilink to the new page from at least one existing related page (otherwise orphan).
9. Update `wiki/<type>/_index.md`.
10. Append to `wiki/log.md`:
    ```
    ## [YYYY-MM-DD] synthesis | <title>
    - Page: [[<type>/<slug>]]
    - Papers: <list of slugs>
    - Trigger: <what prompted this>
    ```
11. Run `python scripts/check_links.py wiki raw_markdown` and `python scripts/validate_frontmatter.py wiki`. Fix issues.

## Established vs. Open

In the page's current-assessment callout, label whether the synthesis represents:
- An **established cross-paper finding** — directly supported by ≥2 papers with specific claims.
- An **open cross-paper pattern** — a structural implication of combining papers from different threads, not yet directly tested.

This prevents future queries from treating speculative connections as settled.
