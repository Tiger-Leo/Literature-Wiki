# Page-Brief Template

The curator fills in one of these for each scope page in the round plan. Writers consume the filled-in briefs in Stage B; reviewers consume them in Stage C for fidelity spot-checks.

Save each brief at `round-N/page-briefs/<slug>.md`.

---

```markdown
# Brief — `<slug>`

## page_type
concept | debate | mechanism | measure | method | synthesis

## cluster
<cluster number from the round plan>

## working_definition
One paragraph (3–5 sentences) defining the topic in the wiki's voice. This is NOT the page's lead paragraph; it is the curator's working definition that anchors the brief.

## why_it_matters
One paragraph on why this topic deserves a standalone page in this literature: where it sits in the conceptual lineage, what cross-paper pattern it pulls together, whether it carries any frontier-extension significance. Roughly 3–5 sentences.

## wikipedia_outline
A bulleted list of section headings the writer should use, with a one-line scope note for each AND a **per-section source allocation** — which `key_sources_ranked` slugs feed each section. The outline names **sub-topics**, not papers. **Provide ≥7 sections** (target 7–10) including the lead and a closing "Cross-links / See also" section, unless the corpus is genuinely too thin to support that many distinct facets (if so, say so explicitly here and in the status summary). Where a formal model is central, name a "Formal model" section explicitly. Aim each body section to draw on **≥4 distinct papers** where the corpus allows — the allocation below is how you guarantee that.

Each body section's scope note should also flag, where relevant, an **empirical signature or testable prediction** the writer should surface, so the page isn't merely descriptive.

Example shape (not prescriptive; bespoke to the topic). Format: `**Heading** — scope. Sources: [[slug-a]], [[slug-b]], [[slug-c]], [[slug-d]].`
- **Lead** — encyclopedic paragraph: what X is, why it matters, the three rival framings. *(no citations in lead)*
- **Definition and scope** — what X is and is not; standard operationalization. Sources: [[slug-a]], [[slug-b]].
- **<Sub-question or sub-topic 1>** — one-line scope (+ empirical signature if any). Sources: [[slug-a]], [[slug-c]], [[slug-d]], [[slug-e]].
- **<Sub-question or sub-topic 2>** — one-line scope. Sources: [[slug-b]], [[slug-f]], [[slug-g]], [[slug-h]].
- **Empirical synthesis** — cross-paper pattern. Sources: [[slug-c]], [[slug-d]], [[slug-i]], [[slug-j]].
- **Tensions and refinements** — one-line scope. Sources: [[slug-e]], [[slug-f]].
- **Frontier / extension axis** *(only if plan declares this page in scope for the axis)* — the plan's declared frontier-axis treatment (whatever axis the plan named — e.g. AI-era, replication wave, policy translation). Sources: [[frontier-slug-1]], [[frontier-slug-2]].
- **Open questions** — one-line scope.
- **Cross-links** — wikilinks to related pages.

## key_sources_ranked
A ranked list of ≤10 paper slugs the writer should base the page on, each with a one-line rationale and the explicit raw-markdown path. The writer MUST open `raw_markdown/papers/<slug>.md` for each; `wiki/sources/<slug>.md` is allowed only as a navigation aid.

- [[<slug-1>]] (raw_markdown/papers/<slug-1>.md) — <one-line rationale: what role this paper plays in this page>
- [[<slug-2>]] (raw_markdown/papers/<slug-2>.md) — <rationale>
- ... up to 10.

## cross_link_targets
A list of other wiki pages this page should wikilink to, grouped by type. **Target 12–15** targets for a typical page (fewer only if the wiki is genuinely small and that many related pages do not exist / aren't scheduled this round). Use `[[slug]]` (the writer will format them in a "Cross-links" / "See also" section at the end of the page).

- Concepts: [[concepts/<other-concept-1>]], [[concepts/<other-concept-2>]], ...
- Mechanisms: [[mechanisms/<related-mechanism>]], ...
- Debates: [[debates/<related-debate>]], ...
- Synthesis: [[synthesis/<related-synthesis>]], ...
- Major sources: [[<slug>]] (5–10, not exhaustive)

## callout_target
**Number of knowledge-level callouts the writer must include: 2–4** (cross-paper-pattern callouts and `> **Current assessment (YYYY-MM):** ...` blocks). Name where they should land, e.g., "one current-assessment callout closing the Empirical synthesis section; one cross-paper-pattern callout in §3." Use the low end (or note "1 minimum") only for a purely definitional topic with little to assess.

## length_target
<number> words. **Default band 1700–2200 for concept/mechanism/debate; up to 2800 for major synthesis.** Set a tighter/lower band only when the corpus genuinely cannot support that much (note the reason). Each body section should reach ≥150 words of integrated prose drawing on ≥4 papers where the corpus allows. Trim, do not pad — but do not ship a skeletal page either; merge thin sections rather than leaving one- or two-sentence stubs.

## writing_constraints
Bullet list. Always include:

- **READ THE ACTUAL PAPER for each `[[slug]]` listed under `key_sources_ranked` — open `raw_markdown/papers/<slug>.md` and read the relevant sections before drafting anything that cites it. Do NOT lean on `wiki/sources/<slug>.md`.**
- Encyclopedic lead paragraph (no bullets, no callouts, no single-paper-only citations).
- Structural backbone is the subject matter — the sub-questions, the formal model, the evolution of thinking — NOT a per-paper enumeration.
- When multiple papers say the same thing, fold them into a single synthetic sentence with multi-citation.
- Three knowledge levels distinguishable (Paper claim / Cross-paper pattern / Current assessment) but NOT as separate top-level sections. Use inline citation, italics, and short callout blocks.
- Keep wikilinks `[[slug]]` exactly as the existing format.
- <Page-specific constraint>: <e.g., "Include the formal GHM model with the renegotiation stage labelled.">
- <Page-specific constraint>: <e.g., "Frontier-axis section required: address the plan's declared frontier axis via [[<key-frontier-paper>]].">  (Or omit if not in scope.)

## spot_check_anchors
Exactly 3 specific claims on the page that the reviewer will verify against `raw_markdown/papers/<slug>.md`. Each anchor names a specific paper and a specific claim that, if absent from the actual paper text, triggers an automatic REVISE.

- [[<slug-A>]] — Verify <specific claim>, e.g., "the headline finding that asset specificity is the most robust predictor of integration across 25 years of empirical evidence."
- [[<slug-B>]] — Verify <specific claim>.
- [[<slug-C>]] — Verify <specific claim>.
```

---

## Notes for the Curator

- The brief is the contract between the planner's high-level cluster plan and the writer's actual page. The richer the brief, the better the page.
- Be opinionated about the section structure. Writers will follow your outline; if you give them a flat "Introduction / Body / Conclusion" outline, you'll get a flat page back.
- **Specify density, not just structure.** A good brief pins down the word band, ≥7 sections, the per-section source allocation (≥4 papers per major section where possible), the 2–4 callout target, and 12–15 cross-link targets. These are the levers that turn a structurally-correct page into a *detailed* one. Degrade them honestly for a thin corpus rather than padding — and flag the corpus limit in the status summary.
- The `spot_check_anchors` are the reviewer's teeth. Pick claims that are actually checkable from a 10-minute read of the raw paper, not generalities like "Verify the contribution of this paper".
- Do not invent a "frontier extension" section if the corpus doesn't support one. The round plan decides whether such an axis exists at all.
