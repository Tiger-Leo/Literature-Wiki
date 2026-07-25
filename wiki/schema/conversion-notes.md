---
title: Conversion Notes
type: schema
created: 2026-04-06
---

# Conversion Notes: PDF → Markdown Quality Audit

Recorded failure modes from quality checks on converted papers. Update this file whenever a new failure mode is observed.

---

## Audit 1: Pilot Paper Quality Check (2026-04-06)

**Papers checked**: 3 pilot papers (Eliaz & Spiegler 2020, Barron & Fries 2023, Roos & Reccius 2024) + spot checks on Hagmann et al. 2024, Panizza et al. 2023, Leib et al. 2024.

**Converter**: markitdown (via `scripts/convert_pdf_to_markdown.py`).

### What passed

- **Title and authors**: Preserved in all 3 pilot papers.
- **Abstract**: Present and readable in all 3. Multi-column journals (R&R) had line-break artefacts but text was complete.
- **Section headings**: Preserved in all papers checked (Introduction, Model, Results, References all present).
- **References section**: Present and parseable in all 3 pilot papers (E&S: line 3795; B&F: line 4996; R&R: end of file). References are formatted as plain text (not structured metadata), which is sufficient for manual lookup but not machine-parseable.
- **Greek letters and unicode math symbols**: UTF-8 characters (α, µ, σ, δ, ∈, ∑, ∏) preserved correctly in all math-heavy papers.
- **Body text**: Clean prose for single-column PDFs (E&S working paper, B&F working paper). Readable throughout.

### Failure modes observed

#### FM-1: PDF header/footer artefacts (Severity: Low)

**Observed in**: `eliaz-and-spiegler-2020-a-model-of-competing-narratives.md` (first ~40 lines).

**Description**: ArXiv submission metadata (date stamp "2018 Nov 10" and arXiv ID) appears at the top of the file as single characters on separate lines, e.g.:
```
8
1
0
2

v
o
N
0
1
```
This is caused by PDF renderers extracting the vertical/rotated arXiv watermark text as individual characters. The paper content begins correctly after line ~42.

**Impact**: Cosmetic. The actual paper content is unaffected. The garbage characters cause no downstream parsing issues because the source page extraction process begins with the abstract and introduction.

**Fix**: Trim lines before the title. No fix needed for existing pilot papers since source pages were written directly from the converted content, not the raw file header.

**Likely affected**: Any paper sourced from arXiv preprint PDFs.

#### FM-2: Math formulas as plain unicode text (Severity: Medium)

**Observed in**: `eliaz-and-spiegler-2020-a-model-of-competing-narratives.md` (throughout).

**Description**: LaTeX display equations are converted to a mix of unicode symbols and plain text without LaTeX fencing (`$$...$$` or `$...$`). Example — the Bayesian Network factorization formula appears as:
```
pR(xN ) =

p(xi |

xR(i))

N
i
Y
∈
```
The formula is identifiable but cannot be rendered as math in Obsidian without MathJax/KaTeX fencing. Superscripts and subscripts are sometimes lost or flattened.

**Impact**: Moderate for theory papers. The formulas are recognisable to a reader who knows the notation, but Obsidian will not render them as proper equations. Source page extraction compensates by re-typesetting key formulas in LaTeX when creating wiki source pages.

**Fix applied**: Source pages (`wiki/sources/`) manually re-typeset the key equations in LaTeX. Raw markdown files are kept as-is (immutable by convention).

**Likely affected**: All theory papers with display math (Eliaz-Spiegler, Schwartzstein-Sunderam, model-heavy empirical papers).

#### FM-3: Multi-column layout line splitting (Severity: Medium)

**Observed in**: `roos-and-reccius-2024-narratives-in-economics.md` (abstract and throughout body).

**Description**: Two-column journal PDFs (Roos-Reccius is published in *Journal of Economic Surveys*) have paragraphs split across lines at column boundaries, e.g.:
```
There is growing awareness within the economics pro-

fession of the important role narratives play in the
economy. Even though empirical approaches that try

to quantify economic narratives are getting increas-

ingly popular, there is no theory or even a universally
accepted definition...
```
Hyphenation artefacts (`pro-fession`, `increas-ingly`) also appear.

**Impact**: Text is fully readable but fragmented. LLM extraction is unaffected because the meaning is preserved. Not suitable for automated sentence-level parsing.

**Fix**: None needed for wiki source page creation — prose fragments are identifiable and LLM reading handles them well.

**Likely affected**: All journal-formatted PDFs (JES, AER, QJE, etc.). Working papers and NBER papers (single-column) are typically clean.

#### FM-4: Statistical tables as plain text (Severity: Medium)

**Observed in**: `barron-and-fries-2023-narrative-persuasion.md` (Table 1 and others).

**Description**: Regression tables and summary statistics tables are converted as plain text with column headers and values on separate lines but without markdown pipe-table formatting. Table 1 ("Distance from truth of narratives") appears as:
```
Table 1: Distance from the truth of narratives proposed by misaligned vs aligned advisors

Misaligned advisor = 1

(1)
− θ T

|θ A

post

post
12.72∗∗∗
(0.702)
```
Superscripts (`∗∗∗`) and column alignment are lost; the table structure is inferrable only with prior knowledge of the paper.

**Impact**: Moderate for empirical papers. Key quantitative results are present but require careful reading to interpret. Source page extraction compensates by re-structuring tables from source pages into wiki source pages.

**Fix applied**: Key quantitative results from Table 1 are re-formatted in the source page as structured data. Raw files are kept as-is.

**Likely affected**: All empirical papers with regression tables (Barron-Fries, Hagmann et al., Leib et al., Panizza et al., most lab/field experiment papers).

#### FM-5: Figure images absent (Severity: Low — expected)

**Observed in**: All papers with figures (B&F, Hagmann et al., others).

**Description**: Figure captions and in-text references are preserved (e.g., "Figure 1: An example of historical company data and a possible narrative."), but the actual image content is not extracted. Figures are not present in `raw_markdown/assets/`.

**Impact**: Low for text-based analysis. The figure captions provide enough context for source page writing. Visual content (experimental timeline diagrams, scatter plots, likelihood frontiers) is not accessible without the original PDF.

**Fix**: None — markitdown does not extract binary image content from PDFs. To access figures, open the original PDF in `raw_pdfs/`. This is expected and acceptable; wiki source pages describe figure content in prose.

#### FM-6: Duplicate files from re-conversion (Severity: Low)

**Observed in**: Multiple papers in `raw_markdown/papers/`.

**Description**: Some papers were converted more than once with slightly different filenames:
- `eliaz-and-spiegler-2020-a-model-of-competing-narratives.md` (canonical) + `eliaz-modelcompetingnarratives-2020.md`
- `panizza-et-al-2023-measuring-norm-pluralism-and-tolerance.md` + `panizza-et-al-2023-measuring-norm-pluralism-and-tolerance-1.md`
- `leib-et-al-2021-the-corruptive-force-of-ai-generated-advice.md` + `2023the-corruptive-force-of-ai-generated-advice.md`
- `benabou-et-al-2018-narratives-imperatives-and-moral-reasoning.md` + `benabou-et-al-narratives-imperatives-and-moral-persuasion.md`
- `scott-and-lyman-1968-accounts.md` + `scott-accounts-1968.md`
- `hagmann-and-loewenstein-persuasion-with-motivated-beliefs.md` (different paper — not a duplicate of Hagmann et al. 2024)
- `schneider-et-al-2024-sorting-and-wage-premiums-in-immoral-work.md` + `schneider-et-al-sorting-and-wage-premiums-in-immoral-work.md`

**Impact**: Low — non-canonical files are never linked from wiki pages (all source pages use the canonical slug). They consume disk space but do not cause link failures.

**Fix**: Leave non-canonical files in place for now (immutable `raw_markdown/` convention). Note canonical slug in `raw_markdown/_index.md` for the affected papers. Clean up during a future maintenance pass if needed.

---

## Summary: markitdown Suitability by Paper Type

| Paper type | Suitability | Notes |
|---|---|---|
| Working paper / arXiv (single-column, mostly prose) | **Good** | Title, authors, sections, references all clean. Math unicode-only. |
| Published journal PDF (2-column layout) | **Acceptable** | Column-splitting artefacts in body text; all content present. |
| Theory-heavy papers with display math | **Acceptable with workaround** | Equations present as unicode text; re-typeset in source page. |
| Empirical papers with regression tables | **Acceptable with workaround** | Tables as plain text; re-structured in source page. |
| Papers with important figures/diagrams | **Partial** | Captions only; open original PDF for visual content. |

**Overall verdict**: markitdown is adequate as a default converter for this wiki. The failure modes are predictable and all have workarounds at the source-page creation step. The raw markdown files are best treated as reference text, not as publication-quality renderings.

---

## When to Use Fallback Converters

Trigger fallback if:
- Math equations are the primary evidence needed (e.g., a proof-based paper where step-by-step formalism matters more than prose)
- Tables contain the primary quantitative results and the table structure is completely unreadable
- markitdown output is shorter than expected (possible truncation of a long PDF)

Fallback order: `pymupdf4llm` (better layout, better math) → `pdfplumber` (structured table extraction) → manual.
