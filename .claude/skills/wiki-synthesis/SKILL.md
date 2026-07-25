---
name: wiki-synthesis
description: Use this skill when the user wants to save a single discussion, insight, or comparison as one wiki page — phrases like "save this to the wiki", "write a synthesis page about X", "create a debate page on Y", "file this comparison", "add this insight to the wiki". For a full collection rebuild use `/wiki-build`. This skill is the one-page-at-a-time path.
---

# Wiki Synthesis — One-Page Save

The single-page complement to `/wiki-build`. Use this when a conversation has produced an insight worth one wiki page (a concept, debate, mechanism, or thematic synthesis) and you want to save it without running the full multi-round build.

If you have new papers to ingest or a wide rebuild to perform, stop and use `/wiki-build` instead. This skill is for surgical, one-page additions.

## When to Create Each Page Type

| Page type | Trigger |
|---|---|
| Synthesis | A cross-cutting theme draws on ≥2 papers, the insight is non-obvious, and no existing concept/debate/mechanism page is the right home |
| Debate | ≥2 papers stake out competing positions on a precise question, the disagreement is genuine, and the tension matters for future queries |
| Concept | A theoretical or empirical construct recurs across ≥2 papers and currently lacks its own page |
| Mechanism | A causal channel recurs across ≥2 papers and currently lacks its own page |

If the insight applies to only one paper, update that paper's source page — do not create a synthesis page.

## Quality Bar

The page must meet the same Wikipedia-style bar as pages produced by `/wiki-build`. Read `.claude/skills/wiki-build/rubric.md` before writing. The non-negotiables:

- **Encyclopedic lead paragraph** — no bullets, no single-paper-only citation. Defines the topic, says why it matters.
- **Subject-matter backbone** — section headings name sub-topics, not papers. NO "Paper Claims" section.
- **Integrated citations** — multi-cite where claims converge; name papers in sentence flow only where their individual contribution matters.
- **Three knowledge levels visible but not dominant** — paper claims via inline `[[slug]]`, cross-paper patterns via italicised generalisations, current assessment via a short callout block.
- **Read the raw paper, not the source page.** Every substantive claim traces to `raw_markdown/papers/<slug>.md`, not to `wiki/sources/<slug>.md`.

## Workflow

1. **Pick the right template** from `wiki/templates/` — concept, mechanism, debate, or synthesis.
2. **List the papers** you will cite. For each, open `raw_markdown/papers/<slug>.md` and read the relevant section. Do not lean on source pages.
3. **Choose a slug** — lowercase kebab-case, descriptive. E.g., `social-norms-vs-injunctive-norms`, `forward-induction-in-signaling-games`.
4. **Draft the page** into `wiki/<type>/<slug>.md` using the template's outline. Adapt the outline — the template is a starting point, not a fixed structure.
5. **Write the frontmatter**:
   ```yaml
   ---
   title: "<Topic>"
   type: <synthesis | debate | concept | mechanism>
   status: active
   papers: [<every slug cited in the body>]
   created: <YYYY-MM-DD>   # synthesis pages only
   tags: [...]
   ---
   ```
6. **Self-check against the rubric's automatic REVISE triggers** (`.claude/skills/wiki-build/rubric.md`). Most common failure: a section organised paper-by-paper. Restructure around sub-topics.
7. **Link back** — add a `## See also` section pointing to the related concept / mechanism / debate / synthesis pages and to the major source pages.
8. **Cross-link from related pages.** The page must be discoverable from at least one existing page. Add a wikilink to it from the closest concept / mechanism / debate page's `## See also` section. Otherwise it's an orphan and the lint will flag it.
9. **Update `wiki/<type>/_index.md`** with an entry for the new page.
10. **Append to `wiki/log.md`**:
    ```
    ## [YYYY-MM-DD] synthesis | <title>
    - Page: [[<type>/<slug>]]
    - Papers: <list>
    - Trigger: <what prompted this — query session / discussion / new evidence>
    ```

## Established vs. Open Patterns

In the page's current-assessment callout, label whether the synthesis represents:

- An **established cross-paper finding** — directly supported by ≥2 papers with specific claims.
- An **open cross-paper pattern** — a structural implication of combining papers from different threads, not yet directly tested.

This labeling prevents future queries from treating speculative connections as settled evidence.

## After Creating

Run a quick local lint:

```bash
python scripts/check_links.py wiki raw_markdown
python scripts/validate_frontmatter.py wiki
```

Fix any issues before declaring the page done.
