---
name: wiki-query
description: Use this skill when the user asks a literature question about any topic that may be covered in the wiki. Triggers on literature-framing phrases ("what does the literature say about X", "compare how papers treat Y", "summarise the debate on V") and on direct research questions ("how does X work?", "what is X?", "explain X", "what mechanisms explain Z", "which papers use method W"). Answers from the wiki first; drills to raw sources only if needed.
---

# Wiki Query

## Entry Point by Question Type

| Question type | Entry point |
|---|---|
| What is concept X? / How does concept X work? | `wiki/concepts/_index.md` |
| What mechanism explains Y? | `wiki/mechanisms/_index.md` |
| What is the debate about Z? | `wiki/debates/_index.md` |
| What methods are used to study W? | `wiki/methods/_index.md` |
| How is measure M operationalised? | `wiki/measures/_index.md` |
| Which papers discuss topic T? / Summarise the literature on T | `wiki/synthesis/overview.md`, then `wiki/concepts/_index.md` |
| What does paper P say? | `wiki/sources/_index.md` → source page directly |

## Canonical Read Order

Read in this order; stop at the first layer that yields a complete answer:

1. `CLAUDE.md`
2. Entry-point `_index.md` (see table above)
3. Relevant `wiki/synthesis/`, `wiki/concepts/`, `wiki/debates/`, `wiki/mechanisms/`, `wiki/methods/`, `wiki/measures/` pages — these are now Wikipedia-style synthesis pages, integrated across the collection, and are the **primary** answer layer for cross-paper questions
4. Relevant `wiki/sources/<slug>.md` pages — only when the synthesis layer is thin or a specific paper's detail is needed
5. `raw_markdown/papers/<slug>.md` — for exact numbers, model setup, specific quotes
6. `raw_pdfs/` — last resort

**Stop signal**: stop at the first layer that yields a complete answer. The synthesis layer is usually sufficient for cross-paper questions. Only drill to source pages or raw markdown if (a) the question asks for paper-specific detail, (b) the relevant synthesis page is a stub, or (c) a claim needs quantitative support.

## How the Synthesis Pages Are Structured

After `/wiki-build` has run, each concept / debate / mechanism / measure / method / synthesis page is an integrated Wikipedia-style article — not a per-paper listing. Expect:

- An **encyclopedic lead paragraph** answering "what is this?" directly.
- **Sub-topic sections** that integrate claims across papers, not paper-by-paper sections.
- **Inline multi-citation** — `(...; [[slug-a]]; [[slug-b]]; [[slug-c]])` — for convergent claims.
- **Short callout blocks** marking the wiki's current assessment (look for `> **Current assessment**:` markers).
- A **See also** section at the bottom with cross-links.

Read the lead first; usually it answers the question. Read sub-topic sections only as needed.

## Knowledge Separation

Pages distinguish three claim levels, but they don't put them in separate top-level sections:

- **Paper claim** — what a specific paper asserts; shown by inline `[[slug]]` citation next to the claim.
- **Cross-paper pattern** — pattern across ≥2 papers; shown by italicised generalisations with multi-citation.
- **Current assessment** — wiki's current judgment; shown in a short callout block.

When you cite the wiki in your answer, preserve the distinction in your prose. Do not flatten "the wiki's current assessment is X" into "paper Y shows X".

## Answer Quality

A good answer:
- Draws on the synthesis layer first, not on per-paper summaries.
- Distinguishes paper claims from cross-paper patterns from current assessment.
- For cross-paper questions, cites ≥3 sources in prose like "Author and Author (Year)" or `[[slug]]`.
- Acknowledges gaps where the wiki is thin (synthesis page is `status: stub`, single-paper evidence, or an `Open Questions` bullet that addresses the user's question).
- Uses Obsidian wikilinks `[[slug]]` if the answer is being saved back to the wiki.

## When to Save the Answer Back

Save the answer when it:
- Synthesises ≥2 papers in a non-obvious way that no existing synthesis page captures
- Resolves or sharpens a debate
- Would be costly to reconstruct in a future session

If it meets the bar, invoke `/wiki-synthesis` to create the page. If the answer revealed gaps that warrant a deeper rebuild (multiple new papers, multiple new pages), invoke `/wiki-build` instead.

## Reading the Raw Paper

If the synthesis page's claim is borderline and the answer depends on getting the detail right, open `raw_markdown/papers/<slug>.md` (NOT the source page) and verify. Source pages are derived summaries; raw markdown is the authoritative text.
