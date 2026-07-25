---
title: Query Workflow
type: schema
---

# Query Workflow

## Canonical Read Order

For any literature question, read in this order. Stop when the question is answered with evidence from at least one synthesis page.

1. `CLAUDE.md` — project rules and constraints
2. `/_index.md` — repository map
3. `wiki/_index.md` — wiki navigation
4. Relevant `wiki/synthesis/`, `wiki/concepts/`, `wiki/debates/`, `wiki/mechanisms/`, `wiki/methods/`, `wiki/measures/` pages — **primary answer layer for cross-paper questions**, since these are now Wikipedia-style synthesis pages
5. Relevant `wiki/sources/` pages — only when the synthesis layer is thin or paper-specific detail is needed
6. `raw_markdown/papers/<slug>.md` — for exact numbers, model setup, specific quotes
7. `raw_pdfs/` — last resort

## Stop Signals

- A single synthesis page with a multi-citation lead paragraph usually answers a "what is X?" question.
- A debate page answers a "what is the debate about X?" question without drilling further.
- A `> **Current assessment (YYYY-MM):** ...` callout often gives the wiki's current stance directly.

Only drill to source pages when:
- The question asks for paper-specific detail
- The synthesis page is `status: stub`
- A claim's quantitative support needs verification
- Two synthesis pages disagree and a tie-breaker is needed

## Citation Expectations

- Cite synthesis pages by topic ("the wiki's concept page on X"), and individual papers as `[[slug]]` or "Author et al. (Year)" in prose.
- Preserve the wiki's distinction between paper claim / cross-paper pattern / current assessment. Do not flatten "the wiki's assessment is X" into "paper Y shows X".
- Never cite `raw_markdown/papers/<slug>.md` in a user-facing answer — it's an internal file. Cite the source page or the paper itself.

## Answer Quality

A good query answer:
- Draws on the synthesis layer first.
- For cross-paper questions, cites ≥3 sources in integrated prose.
- Distinguishes paper claims from cross-paper patterns from current assessment.
- Acknowledges gaps where the wiki is thin (`status: stub`, single-paper evidence, an Open-Questions bullet that addresses the user's question).

## Saving Strong Answers Back

Save the answer back to the wiki when it:
- Synthesises ≥2 papers in a non-obvious way that no existing synthesis page captures.
- Resolves or sharpens a debate.
- Would be costly to reconstruct in a future session.

If the answer warrants one new page, invoke `/wiki-synthesis`. If it surfaces multiple gaps that warrant a deeper rebuild, invoke `/wiki-build`. Then append a log entry:

```
## [YYYY-MM-DD] synthesis | <title>
```

## Reading the Raw Paper

If a synthesis page's claim is borderline and the answer hinges on getting the detail right, open `raw_markdown/papers/<slug>.md` (NOT the source page) and verify. Source pages are derived summaries; raw markdown is authoritative.
