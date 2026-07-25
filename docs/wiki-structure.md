# Wiki Structure

Reference for the wiki layer — directory roles, page types, frontmatter conventions, and the Wikipedia-style page structure produced by `/wiki-build`.

---

## 1. Directory Roles

| Directory | Page type | When updated |
|---|---|---|
| `wiki/sources/` | Bibliographic record, one page per paper | Created in Phase 2 of `/wiki-build` per new paper |
| `wiki/concepts/` | Wikipedia-style concept synthesis | Built and rebuilt by `/wiki-build` rounds |
| `wiki/mechanisms/` | Wikipedia-style mechanism synthesis | Built and rebuilt by `/wiki-build` rounds |
| `wiki/methods/` | Wikipedia-style method synthesis | Built and rebuilt by `/wiki-build` rounds |
| `wiki/measures/` | Wikipedia-style measure synthesis | Built and rebuilt by `/wiki-build` rounds |
| `wiki/debates/` | Wikipedia-style debate synthesis | Built and rebuilt by `/wiki-build` rounds |
| `wiki/synthesis/` | Cross-cutting synthesis pages | Built and rebuilt by `/wiki-build` rounds; also written by `/wiki-synthesis` |
| `wiki/templates/` | Page templates | Edited rarely |
| `wiki/schema/` | Naming rules, frontmatter spec, workflow notes | Edited rarely |

The **synthesis pages** (concepts, mechanisms, debates, methods, measures, synthesis) are the **deliverable**. Source pages are bibliographic anchors.

---

## 2. Page Types

### 2.1 Source Pages (`wiki/sources/`)

**Purpose**: One page per paper. Bibliographic and factual record — research question, model/design, results, mechanisms identified, methods, links to relevant synthesis pages. **Not encyclopedic synthesis** — that's the job of the other page types.

**Frontmatter**:

```yaml
---
title: "Full paper title"
authors:
  - Last, First
  - Last, First
year: 2024
slug: author-and-author-year-short-title
raw_markdown: "[[raw_markdown/papers/<slug>]]"
status: canonical
tags: []
---
```

**Section structure** (`wiki/templates/source-template.md`):

- Title (Year) + one-sentence summary
- Research Question
- Model / Experimental Design
- Main Results — specifics, not vague summaries
- Mechanisms Identified
- Methods and Measures
- Concepts Engaged
- Connection to Debates
- Theoretical / Empirical Significance
- Notes and Caveats

### 2.2 Concept Pages (`wiki/concepts/`)

**Purpose**: One theoretical or empirical construct that the literature has built around. Encyclopedic synthesis across the whole collection.

**Frontmatter**:

```yaml
---
title: "Concept Name"
type: concept
status: active
papers: [<every slug cited in body>]
tags: [related-tag]
---
```

**Page structure** (Wikipedia-style — see `wiki/templates/concept-template.md` for a starting outline; the curator's brief overrides):

- **Encyclopedic lead paragraph** — defines the concept, says why it matters, previews the page. No bullets. No single-paper-only citations.
- **Definition and Scope** — what the concept is and is not; standard operationalization.
- **Sub-topic / sub-question sections** — integrated prose drawing on multiple papers. Multi-cite where convergent; name papers in flow only where their distinct contribution matters.
- **Formal Model** *(if applicable)* — for formal-theory concepts.
- **Empirical Synthesis** — cross-paper pattern across the empirical literature.
- **Tensions and Refinements** — where the concept has been contested or unified.
- **Frontier / Extension** *(optional)* — only if the round plan declares this concept in scope for an extension axis (e.g., AI-era reformulation, behavioural turn).
- **Open Questions** — bullets.
- **See also** — wikilinks to related pages.

**Knowledge separation** — paper claims, cross-paper patterns, and current assessments are visible **inline** (inline citation, italicised generalisation, short callout block) — NEVER as separate top-level sections. Sections like "Paper Claims", "Cross-Paper Patterns" as architecture are an automatic REVISE trigger.

### 2.3 Mechanism Pages (`wiki/mechanisms/`)

**Purpose**: One causal channel that the literature invokes.

**Frontmatter** — same pattern as concept, `type: mechanism`.

**Page structure** (see `wiki/templates/mechanism-template.md`):

- Encyclopedic lead paragraph
- The Causal Channel — precise statement of the mechanism
- Micro-foundations — preferences, beliefs, constraints
- Formal Representation *(if applicable)*
- Empirical Signatures — what evidence corroborates the channel
- Scope Conditions — when it operates, fails, or reverses
- Failure Modes and Alternatives
- Frontier / Extension *(optional)*
- Open Questions
- See also

### 2.4 Method Pages (`wiki/methods/`)

**Purpose**: One methodological approach used across the literature.

**Frontmatter** — `type: method`.

**Page structure** (see `wiki/templates/method-template.md`):

- Encyclopedic lead
- What This Method Does
- Standard Implementation
- Variants
- What This Method Can Answer
- What This Method Cannot Answer
- Common Pitfalls
- Frontier / Extension *(optional)*
- Current assessment callout
- See also

### 2.5 Measure Pages (`wiki/measures/`)

**Purpose**: One operationalization of a construct.

**Frontmatter** — `type: measure`.

**Page structure** (see `wiki/templates/measure-template.md`):

- Encyclopedic lead
- What Is Being Measured
- Standard Elicitation
- Variants and Adaptations
- Validation Evidence
- Known Biases and Limitations
- Comparability Across Studies
- Frontier / Extension *(optional)*
- Current assessment callout
- See also

### 2.6 Debate Pages (`wiki/debates/`)

**Purpose**: A genuine disagreement on a precise question.

**Frontmatter** — `type: debate`, status `stub | active | resolved`.

**Page structure** (see `wiki/templates/debate-template.md`):

- Encyclopedic lead
- The Question — precise statement
- Position A — integrated narrative across papers holding it
- Position B — same
- Where the Disagreement Actually Sits
- Empirical Anchors
- Attempts at Unification
- Frontier / Extension *(optional)*
- Current State of the Debate
- Open Questions
- See also

### 2.7 Synthesis Pages (`wiki/synthesis/`)

**Purpose**: A cross-cutting theme that doesn't fit a single concept / mechanism / debate page.

**Frontmatter**:

```yaml
---
title: "Synthesis Title"
type: synthesis
status: active
papers: [...]
created: YYYY-MM-DD
tags: []
---
```

**Page structure** (see `wiki/templates/synthesis-template.md`):

- Encyclopedic lead framing the cross-cutting question
- Sub-theme sections — integrated narrative
- Tensions Across the Threads
- Frontier / Extension *(optional)*
- Current assessment callout — explicit about established vs. open findings
- Open Questions
- See also

---

## 3. Three Knowledge Levels

Every synthesis page distinguishes three claim levels, but **does not** put them in separate top-level sections:

| Level | What it is | How to mark inline |
|---|---|---|
| **Paper claim** | What one paper asserts | Inline `[[slug]]` next to the claim |
| **Cross-paper pattern** | Pattern across ≥2 papers | Italicised generalisation + multi-citation in parentheses |
| **Current assessment** | Wiki's current best judgment, with date | Short `> **Current assessment (YYYY-MM):** ...` callout |

This is the core invariant. Separating these levels into top-level sections produces the paper-listing format the new pipeline replaces. Keeping them visible inline is what makes pages encyclopedic and the wiki maintainable.

---

## 4. Status Values

| Value | Meaning |
|---|---|
| `stub` | Page exists with minimal content; anchor links valid but body thin |
| `active` | Substantive content; cross-links present; standard state after a `/wiki-build` pass |
| `canonical` | Used on source pages — fully linked and complete |
| `resolved` | Used on debate pages — the question has been answered to the wiki's satisfaction |

---

## 5. Router Files (`_index.md`)

Every directory has a `_index.md` that tells an agent what pages exist in that directory. The wiki agent reads `_index.md` files first, never enumerates a directory blindly.

Router files are updated as part of `/wiki-build` Phase 6 and any time `/wiki-synthesis` adds a page.

---

## 5.x Density and Depth Defaults

Synthesis pages should be **substantial and densely integrated by default**, not thin skeletons. The smart defaults (see `.claude/skills/wiki-build/rubric.md` §8 — the single source of truth):

- **1700–2200 words** per concept / mechanism / debate page; up to **2800** for major synthesis.
- **7–10 sections** counting the lead and the closing cross-links section (i.e. ~5–8 substantive body sections; do not split one idea, or peel the lead/cross-links into extra headings, to game the count); **each body section ≥150 words** of integrated prose — no one- or two-sentence sections (merge thin sections rather than leaving stubs).
- **≥4 distinct source papers** woven into each major section where the corpus allows; every cited paper plays a **non-trivial role** (a distinct claim/result/mechanism, not a bare name-drop).
- **2–4 knowledge-level callouts** (cross-paper pattern / current assessment); **12–15 cross-links**.
- **Equations / formal models** where the topic warrants; a **frontier-extension** section (the plan's declared axis — e.g. AI-era, replication wave, policy translation) only when the corpus supports it and the plan declares the axis.

These degrade gracefully: a small collection should hit the *spirit* (dense, integrated, no skeletal sections) without being force-padded. Trim, do not pad — and never ship a skeletal page either.

---

## 6. Cross-Linking

- Use Obsidian wikilinks `[[slug]]`.
- Every synthesis page ends with a `## See also` section listing related concept / mechanism / debate / synthesis pages and a small set of major source pages — **12–15 cross-links by default**, grouped by type (fewer only for a genuinely small wiki); major source pages 5–10, not exhaustive.
- Every wikilink must resolve to an existing page or a page scheduled to be created in the current `/wiki-build` round.
- Orphan pages (no inbound links) are flagged by `scripts/check_orphans.py`.

---

## 7. Logging

`wiki/log.md` is append-only.

Entry format:

```markdown
## [YYYY-MM-DD] wiki-build | <N> rounds, <N> pages
- Workspace: agent_tasks/wikipedia-rewrite_<DATE><HHMM>/
- New papers: <N>
- Source pages added: <list>
- Synthesis pages created: <list>
- Synthesis pages updated: <list>
- Unresolved (revise cap hit): <list or none>
- Lint: <pass/issue summary>
```

For `/wiki-synthesis` and lint operations:

```markdown
## [YYYY-MM-DD] synthesis | <title>
## [YYYY-MM-DD] lint | <summary>
```

---

## 8. Schema Files

`wiki/schema/` contains:

| File | Role |
|---|---|
| `frontmatter-schema.md` | Required and optional frontmatter fields by page type |
| `naming-rules.md` | Slug derivation rules |
| `page-rules.md` | Page structure rules (refers to this doc + the rubric) |
| `build-workflow.md` | The `/wiki-build` workflow contract (delegates detail to `.claude/skills/wiki-build/SKILL.md`) |
| `query-workflow.md` | The `/wiki-query` workflow contract |
| `synthesis-workflow.md` | The `/wiki-synthesis` workflow contract |
| `update-db-workflow.md` | The `/wiki-update-db` workflow contract |
| `scale-up-rules.md` | Rules for scaling the wiki |
| `conversion-notes.md` | Known PDF-to-markdown failure modes |
