# Adaptation Guide: Using narrative-wiki for a Different Research Domain

The narrative-wiki system is a general-purpose AI-native literature wiki framework. Narrative economics is its first use case — but the architecture is fully portable to any research domain with a coherent body of literature.

This guide walks you through adapting the system for your own PDF collection and research area.

---

## What You're Adapting

### Domain-specific parts (need replacement)

These files and directories contain content specific to narrative economics. Replace them with content from your domain:

| Path | What to change |
|------|----------------|
| `CLAUDE.md` | Project purpose and topic description |
| `wiki/concepts/` | Concept pages for your domain |
| `wiki/mechanisms/` | Mechanism pages for your domain |
| `wiki/debates/` | Debate pages for your domain |
| `wiki/synthesis/overview.md` | Initial synthesis for your domain |
| `.claude/skills/*/SKILL.md` | Update topic examples in trigger descriptions |

### Domain-agnostic parts (reuse as-is)

These components are structural and carry no domain assumptions. Keep them unchanged:

- All Python scripts in `scripts/`
- Directory structure (`raw_pdfs/`, `raw_markdown/`, `wiki/`)
- Templates in `wiki/templates/`
- Schema files in `wiki/schema/` — structural, not topic-specific
- The `_index.md` router pattern
- The four skill `SKILL.md` files (except trigger descriptions)
- The three-layer pipeline architecture

---

## Step-by-Step Adaptation

### Step 1: Fork or copy the repository

Clone or copy the narrative-wiki repository. Then remove the existing domain content while keeping the scaffolding:

```bash
# Remove domain content (keep directory structure and _index.md stubs)
rm -f wiki/concepts/*.md wiki/mechanisms/*.md wiki/debates/*.md
rm -f wiki/synthesis/*.md wiki/sources/*.md
rm -f raw_markdown/papers/* raw_markdown/metadata/* raw_pdfs/*
```

Keep everything else: all scripts, templates, schema files, `_index.md` files (which you'll update in Step 6), and the full skill set.

### Step 2: Rewrite CLAUDE.md

Update the `## Purpose` section to describe your research domain. For example:

```markdown
## Purpose
Maintain this repository as a persistent literature wiki for
[your domain], covering [key topics, e.g. mechanism design, auction theory,
market microstructure].
```

Keep the rest of the `CLAUDE.md` structure intact — the layers definition, navigation contract, operations list, maintenance sequence, and naming rules are all load-bearing and should not be modified.

### Step 3: Update the root README.md

Change the project description and any domain-specific examples at the top of `README.md`. The architecture section, folder structure diagram, and pipeline explanation can stay as-is — they describe the system, not the domain.

### Step 4: Seed concept and mechanism pages

Identify the 5–8 core concepts in your domain and create stub pages for each:

```bash
# Create stubs for your domain's concepts
touch wiki/concepts/your-concept.md
touch wiki/concepts/another-concept.md
```

Use the Wikipedia-style templates in `wiki/templates/` as base structures. Set `status: stub` in the YAML frontmatter. Do the same for any mechanism, method, measure, or debate pages you want to pre-seed.

**Note: seeding is optional.** Unlike the old per-paper ingest workflow, `/wiki-build` plans its own page set from the actual corpus — the planner subagent inspects `raw_pdfs/` and `raw_markdown/papers/` and decides which pages to write. You may skip Step 4 entirely and let the first build pass propose the taxonomy.

### Step 5: Update skill trigger descriptions

Each skill has a `description:` field in its SKILL.md frontmatter. This description tells Claude Code when to invoke the skill. Update the example questions to match your domain:

**`wiki-query`**: Update example questions to use your domain's concepts. Example: replace "what mechanisms explain norm updating?" with "what mechanisms explain bidder behaviour in first-price auctions?"

**`wiki-build`**: The description is domain-agnostic and usually does not need editing. The planner subagent adapts to whatever literature is in the corpus.

The skill logic itself does not need to change — only the description text that governs when it fires.

### Step 6: Update `_index.md` files

Update `wiki/_index.md` and each subdirectory `_index.md` to list your domain's seed pages. Remove narrative-economics-specific entries. These router documents are how both humans and agents navigate the wiki, so keeping them current matters.

A minimal `wiki/concepts/_index.md` might look like:

```markdown
# Concepts Index

## Seeded Concepts
- [[your-concept]] — brief description
- [[another-concept]] — brief description

## Stubs (not yet populated)
- [[third-concept]]
```

### Step 7: Run pilot build

Drop 5–10 representative papers from your domain into `raw_pdfs/`, then run:

```
/wiki-build
```

(Default 2 rounds. For a small pilot, `/wiki-build 1` is fine.)

After the build completes, verify:

- The `/wiki-query` skill can answer cross-paper questions using only wiki content.
- Synthesis pages (concept / mechanism / debate) are Wikipedia-style — encyclopedic lead, subject-matter backbone, integrated multi-citation. Read 2–3 pages to confirm.
- All lint checks pass (`/wiki-update-db` runs them as Phase 6).
- `wiki/log.md` has the build entry.

If the synthesis pages still read like paper listings, check the curator's briefs at `agent_tasks/wikipedia-rewrite_*/round-1/page-briefs/` — their `wikipedia_outline` should name sub-topics, not paper titles. Fix any generic briefs and re-run.

### Step 8: Scale up

Follow the protocols in `docs/scale-up-guide.md`: 2 rounds default, 1 round for small corpora, 3 for larger ones. Lint runs automatically each build.

---

## Domain Taxonomy Design

When seeding concept/mechanism/debate pages for a new domain, organize your thinking into five categories:

**Concepts** — The recurring ideas that papers in this domain invoke.
Ask: *What terms appear in most abstracts in this domain?*

**Mechanisms** — The causal pathways that explain the phenomena.
Ask: *Why does X happen? What are the micro-foundations?*

**Methods** — The research designs used.
Ask: *How do papers in this domain establish causality?*

**Measures** — How key constructs are operationalized.
Ask: *What instruments, indices, or experimental tasks does this domain use?*

**Debates** — Where papers disagree.
Ask: *What empirical or theoretical tensions exist between research groups?*

Start with 5–8 seed pages per category. Let new pages emerge organically as ingests surface concepts that do not yet have a landing page. Resist the temptation to pre-populate everything — the wiki grows better when driven by actual paper content.

---

## What Not to Change

The following elements are load-bearing. The skills and scripts depend on them — modifying them will break the pipeline:

- **The three-layer model** (`raw_pdfs` → `raw_markdown` → `wiki`). Do not collapse layers or add intermediate ones.
- **The `_index.md` router pattern**. Every directory must have an `_index.md`; agents navigate by reading these first.
- **The knowledge separation rule**: distinguish *paper claim*, *cross-paper pattern*, and *current assessment* within wiki pages. Do not collapse them into a single summary.
- **The slug naming convention**: lowercase kebab-case, `author-and-author-year-short-title` for source pages.
- **The frontmatter schema structure**: you may add fields, but do not remove required fields (`title`, `status`, `aliases`, `tags`).
- **The lint script interfaces**: `check_links.py`, `check_orphans.py`, `validate_frontmatter.py`, and `export_metadata.py` expect the standard directory layout.

---

## Minimal Viable Adaptation

For a quick start with a new domain, the minimum viable steps are:

1. Copy the repository
2. Update the `## Purpose` section in `CLAUDE.md` (5 minutes)
3. Drop your PDFs into `raw_pdfs/`
4. Run `/wiki-build` — the planner and curator subagents will inspect the corpus and propose the page set

A minimal adaptation can be functional in under an hour. You do not need any pre-seeded taxonomy — the planner / curator subagents in `/wiki-build` are domain-agnostic and adapt to whatever literature is in your corpus. Cluster themes emerge from the actual papers; the optional frontier-extension axis is only added when the corpus has such a sub-literature.

---

## Example Adaptations

The narrative-wiki pattern is well-suited for any domain with a coherent theoretical vocabulary and a mix of empirical and theoretical papers:

- **Behavioral economics** — concepts: loss aversion, present bias; mechanisms: reference-dependence, salience
- **Industrial organization** — concepts: market power, entry deterrence; mechanisms: switching costs, foreclosure
- **Political economy** — concepts: redistribution, populism; mechanisms: electoral accountability, lobbying
- **Sociology** — concepts: social capital, institutional trust; mechanisms: norm enforcement, status signaling
- **History of economic thought** — concepts: invisible hand, comparative advantage; mechanisms: price signals, comparative statics

The pattern works best when your collection has:
- A coherent theoretical vocabulary with recurring concepts worth tracking
- A mix of empirical and theoretical papers
- Cross-paper debates worth recording
- 20 or more papers to justify the overhead of maintaining a structured wiki

It is less well-suited for: purely empirical, domain-specific literatures with few cross-cutting concepts, or collections where each paper is entirely self-contained with no shared theoretical framework.

---

*For questions about the system architecture, see `docs/architecture.md`. For the full pipeline walkthrough, see `docs/pipeline.md`. For the skill reference, see `docs/skills-reference.md`.*
