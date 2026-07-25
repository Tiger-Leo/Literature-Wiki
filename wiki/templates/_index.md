# Wiki Page Templates

Templates for each wiki page type. Use them as a **starting outline**, not as a fixed structure — the curator's brief in `/wiki-build` provides the bespoke outline for each page, and that takes precedence.

## Style: Wikipedia, not paper-listing

Every non-source template is written in the Wikipedia-style synthesis voice:

- **Encyclopedic lead paragraph** — defines the topic, says why it matters, previews the page.
- **Subject-matter backbone** — section headings name sub-topics, sub-questions, or formal-model components, **not papers**.
- **Integrated citations** — multi-cite where claims converge; name papers in sentence flow only where their individual contribution matters.
- **Three knowledge levels visible but not dominant** — paper claims appear as inline citations; cross-paper patterns appear as italicised generalisations with multi-citation; current assessments appear as short callout blocks. None of these becomes a top-level section.

The full quality bar lives at `.claude/skills/wiki-build/rubric.md`.

## Templates

| File | When to use |
|---|---|
| [[concept-template]] | A concept page (`wiki/concepts/`) — one theoretical or empirical construct |
| [[mechanism-template]] | A mechanism page (`wiki/mechanisms/`) — one causal channel |
| [[debate-template]] | A debate page (`wiki/debates/`) — a genuine disagreement on a precise question |
| [[method-template]] | A method page (`wiki/methods/`) — one methodological approach |
| [[measure-template]] | A measure page (`wiki/measures/`) — one operationalization of a construct |
| [[synthesis-template]] | A synthesis page (`wiki/synthesis/`) — a cross-cutting theme |
| [[source-template]] | A source page (`wiki/sources/`) — one paper's bibliographic record (different rubric: factual, not interpretive) |

## What every non-source template includes

- YAML frontmatter (`title`, `type`, `status`, `papers`, `tags`)
- Encyclopedic lead paragraph
- Suggested section outline — **adaptable**, not prescriptive
- Optional `## Frontier / Extension` section — included only when the corpus has a coherent frontier sub-literature
- `## Open Questions`
- `## See also` with wikilinks

## Source pages are different

`source-template.md` is the only template with a paper-by-paper structure, because source pages are bibliographic records, not synthesis. Source pages anchor the synthesis pages but are not the primary deliverable.
