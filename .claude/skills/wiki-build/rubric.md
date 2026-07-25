# Wiki Page Quality Rubric

The single source of truth for what a synthesis page in this wiki must look like. Both writers and reviewers read this file.

Synthesis pages live under `wiki/concepts/`, `wiki/debates/`, `wiki/mechanisms/`, `wiki/measures/`, `wiki/methods/`, `wiki/synthesis/`. Source pages (`wiki/sources/`) have a different rubric — they are bibliographic, not encyclopedic.

---

## What a Synthesis Page Is

A focused, encyclopedic article on **one topic**, integrating evidence from across the paper collection in a narrative voice. A reader who comes to learn about topic X should leave with a coherent picture of X from the whole literature — not 12 paper-by-paper summaries.

The right mental model is **a Wikipedia article**, not a literature-review chapter, not an annotated bibliography, not a meeting-notes dump.

---

## Pass Criteria

### 1. Encyclopedic Lead

The page opens with **one paragraph** that defines the topic, says why it matters, and previews the structure of the page. The lead has no bullet lists, no inline citations to a single paper, no callout boxes. A reader who reads only the lead should walk away with the gist.

### 2. Structural Backbone = Subject Matter, Not Papers

Section headings name **sub-questions, sub-topics, formal components, or evolutionary stages of the idea** — not papers. Sections like "Smith and Lee (2020)" or "Paper Claims" are immediate FAIL.

Acceptable backbones (illustrative, not exhaustive):
- For a concept page on a formal-theory topic: Definition → Formal model → Comparative statics → Empirical evidence → Tensions and refinements → Open questions
- For a concept page on a measurement topic: What is being measured → Standard operationalization → Validation evidence → Variants in the literature → Known biases → Open questions
- For a debate page: The question → Position A (with internal sub-structure) → Position B → Where they actually disagree → Empirical anchors → Current state of the debate
- For a mechanism page: The causal channel → Micro-foundations → Empirical signatures → Scope conditions → Failure modes / boundary cases
- For a method page: What this method does → Standard implementation → Variants → What it can and cannot answer → Common pitfalls
- For a measure page: What is being measured → Elicitation procedure → Validation evidence → Comparability across studies
- For a synthesis page: A motivated cross-cutting question → Integrated treatment organised by sub-theme → Open questions

The curator's brief provides the specific outline per page. Writers may refine the outline if a better backbone is found while reading the papers, but must not collapse into paper-by-paper structure.

### 3. Citation Integration

Citations are inline and integrated, not enumerated. A single sentence can carry multiple citations:

> Asset specificity is the most robust predictor of vertical integration across two decades of empirical work ([[lafontaine-and-slade-2007]]; [[acemoglu-aghion-and-griffith-2010]]; [[forbes-and-lederman-2009]]).

NOT:

> Lafontaine and Slade (2007) find that asset specificity predicts integration. Acemoglu, Aghion and Griffith (2010) also find this. Forbes and Lederman (2009) find this too.

When papers genuinely disagree, name them in sentence flow with the disagreement made precise — not as separate sub-sections.

### 4. Three Knowledge Levels Visible but Not Dominant

The wiki distinguishes three levels of claim. A synthesis page must keep them distinguishable without letting them turn into the structural backbone:

| Level | What it is | How to mark it |
|---|---|---|
| **Paper claim** | What a specific paper explicitly asserts | Inline citation `[[slug]]` next to the claim |
| **Cross-paper pattern** | A pattern visible across ≥2 papers | Sentence flow with multiple citations; or italic phrases like *"Across the field-experiment literature, …"* |
| **Current assessment** | The wiki's current best judgment, with date | A short callout block, OR an italicised sentence at section end |

Acceptable callout convention (use either):

```markdown
> **Current assessment (YYYY-MM):** The empirical evidence on X is now strong; the open question is Y.
```

or

```markdown
*Current wiki assessment: …*
```

**Do not** create separate top-level sections called "Paper Claims" or "Current Assessment" — those degrade pages into the listing-style format we are replacing. The levels appear inline, not as page architecture.

### 5. Coverage of Assigned Papers

Every paper in `key_sources_ranked` from the page brief must appear in the page text with a **non-trivial role**. A paper listed in the brief but absent from the page is a FAIL; a paper present only as a bare name-drop is also a FAIL.

> **Non-trivial role (definition).** A cited paper plays a non-trivial role when it contributes a **distinct claim, result, mechanism, or counter-position** that the surrounding prose actually uses — e.g., it supplies a specific finding ("asset specificity is the most robust predictor…"), a model component, a scope condition, or a named disagreement. A *single name-drop clause* — the slug appended to a sentence that would read identically without it, or one paper buried inside a multi-cite parenthetical it adds nothing to — does **not** count. The test: if you deleted the paper, would the substance of the sentence change? If no, the role is trivial.

The reverse is allowed: a writer may add papers not in `key_sources_ranked` if reading the cluster surfaces other relevant work in `raw_markdown/papers/`. The reviewer should not penalise that.

### 6. Cross-Links

Every page has a `## Cross-links` (or `## See also`) section at the end with wikilinks to:
- Closely related concept, mechanism, debate, measure, method pages
- Relevant synthesis pages
- Major source pages (5–10, not exhaustive)

**Default density: 12–15 wikilinks** for a typical page, grouped by target type (Concepts / Mechanisms / Debates / Synthesis / Sources). Fewer is acceptable for a genuinely small wiki where that many related pages do not yet exist — link every genuinely related page that exists or is scheduled this round, and do not invent links to pad. Note that inline `[[slug]]` citations in the body count toward connectivity but the dedicated cross-links section should still gather the navigable related-page set.

Wikilinks use `[[slug]]` (Obsidian-compatible). Every wikilink must resolve to an existing page or a page that will exist by the end of the current round (check against the round plan).

### 7. Frontier / Extension Axis (Optional, Domain-Specific)

If the round plan declared a frontier-axis (e.g., "AI extension", "post-2020 replication wave", "policy translation"), pages flagged in the plan must include a dedicated section addressing that axis. If the plan declared NONE, do not add one — forcing a frontier section onto a literature that has none is a FAIL.

### 8. Density and Depth (defaults)

A synthesis page should be **substantial and densely integrated by default** — the failure mode this section guards against is the thin, skeletal page that is structurally correct but underdeveloped. The following are **smart defaults for a corpus with adequate material**, not rigid quotas. They degrade gracefully: a 5-paper wiki, or a page whose topic only three papers genuinely engage, should hit the *spirit* (dense, integrated, no skeletal sections) without being force-padded to the word floor. Trim, do not pad — adding empty sentences to reach a number is itself a FAIL.

| Dimension | Default floor / band | Graceful degradation |
|---|---|---|
| **Page length** | **1700–2200 words** (concept / mechanism / debate); up to **2800** for major synthesis pages | Thin corpus: a shorter page is fine if every section is still dense; never pad to reach the band |
| **Top-level sections** | **7–10** sections **counting the lead and the closing cross-links section** — i.e. ~5–8 *substantive body* sections | Fewer if the topic genuinely has fewer facets; never split one idea, or peel the lead/cross-links into extra headings, to game the count |
| **Per body section** | **≥150 words** of integrated prose | A section that cannot reach ~150 words of real content should be merged into a neighbour, not left skeletal |
| **Papers per major section** | **≥4 distinct source papers** woven in, where the corpus allows | Use as many as genuinely engage the section; do not cite papers that say nothing about it |
| **Knowledge-level callouts** | **2–4 per page** (cross-paper pattern / current assessment) | At least 1 where any real assessment or convergence exists; 0 only if the topic is purely definitional |
| **Cross-links** | **12–15** wikilinks | As many as exist / are scheduled; see §6 |
| **Equations / formal model** | Include where the topic warrants (formal-theory, measurement, model-driven topics) | Optional for purely empirical/narrative topics; do **not** omit on a formalizable topic merely to "keep it readable" |
| **Frontier / extension section** | Include a forward-looking / open-problems / current-frontier extension section (the plan's declared axis — e.g. AI-era, post-2020 replication wave, policy translation) **only where the corpus supports it** and the round plan declares that axis | Omit entirely when the plan declared NONE — forcing one is a FAIL (see §7) |

Additional depth expectations:

- **No skeletal sections.** A one- or two-sentence section under a top-level heading is an automatic REVISE. Either develop it to ≥150 words of integrated prose or fold it into an adjacent section.
- **Fold multi-citations.** Where ≥2 papers converge on a claim, fold them into a single multi-cite sentence (see §3) rather than spreading them across sentences. This raises density without raising word count.
- **Empirical signatures / testable predictions.** Where the topic is a mechanism or empirical regularity, state specific, checkable signatures or predictions (e.g., the conditions under which an effect appears or reverses) rather than only abstract description.

Trim, do not pad. The floors describe *how much real, integrated content a well-supported topic deserves* — not a word budget to fill.

### 9. Frontmatter

Every page has YAML frontmatter conforming to `wiki/schema/frontmatter-schema.md`:

```yaml
---
title: "Topic name"
type: concept | debate | mechanism | measure | method | synthesis
status: active        # not stub, once written
papers: [slug1, slug2, ...]
tags: [...]
---
```

The `papers:` array must list every slug cited in the page body. Reviewer checks this.

### 10. Reading the Actual Papers

This is the hardest invariant to enforce but the most important. Every substantive claim on the page must trace to text actually present in `raw_markdown/papers/<slug>.md` — not to `wiki/sources/<slug>.md`. Source pages are derived; they can be wrong; they can flatten. Writers and reviewers must spot-check claims against the raw paper, not against the wiki's own summaries.

The page brief lists `spot_check_anchors` — 3 specific claims per page that the reviewer will verify against the raw paper. Pages that fail spot-checks are an automatic REVISE regardless of how well-written they are.

---

## Automatic REVISE Triggers

A reviewer must mark `VERDICT: REVISE` if **any** of these apply:

1. The page has a section called "Paper Claims" or equivalent listing structure.
2. ≥2 consecutive paragraphs are organised paper-by-paper rather than topic-by-topic.
3. The lead paragraph contains bullet lists or single-paper citations only.
4. Any `key_sources_ranked` paper is absent from the page body.
5. Any `spot_check_anchor` claim fails verification against the raw paper.
6. The frontmatter `papers:` list does not match the slugs cited in the body.
7. A frontier-axis section is present when the plan said NONE, or absent when the plan said REQUIRED for this page.
8. Wikilinks point to pages that do not exist and are not scheduled to exist this round.
9. **The page is skeletal relative to the density defaults (§8) and the corpus could support more** — e.g., well under the word band, fewer than ~7 sections (counting lead + cross-links; not a reason to split one idea into filler sections), a body section under ~150 words / one-to-two sentences, a major section drawing on only one paper where several engage it, or zero knowledge-level callouts where genuine assessment/convergence exists. (Do NOT trigger this for a genuinely thin corpus where the material simply isn't there — name the corpus limit instead.)

---

## Automatic PASS Indicators

A reviewer who reads the page and can answer all of the following with "yes" should mark `VERDICT: PASS`:

- Does the lead paragraph make me understand the topic without reading the rest?
- Does each section heading name a sub-topic, not a paper?
- When papers are cited, do they support claims rather than become claims themselves?
- Are paper claim / cross-paper pattern / current assessment distinguishable without separate top-level sections?
- Do the cross-links go to pages that exist?
- Did all three spot-check anchors verify against the raw paper text?
- Is the page dense and substantial per §8 — roughly in the word band, ~7–10 subject-matter sections, each body section ≥150 words, major sections drawing on several papers, 2–4 knowledge-level callouts, 12–15 cross-links — *or* appropriately shorter only because the corpus is genuinely thin (no skeletal sections, no padding either way)?

---

## Style Notes

- **Tense**: present tense for claims and patterns, past for historical sequence (e.g., "Coase (1937) introduced the marginal-comparison framing…").
- **Voice**: third-person neutral. The wiki is not addressing the reader as "you" and not narrating its own process. No "this page will discuss" sentences.
- **Hedging**: precise. "There is strong evidence that X" with citation, not "many papers seem to suggest X".
- **Equations**: include the formal model where the topic warrants it. Use LaTeX in `$...$` inline or `$$...$$` block. Do not skip equations to "keep it readable" — equations clarify, prose alone often flattens.
- **No meta-prose**: do not write "In this section we discuss…" or "As we have seen above…". Just write the content.
