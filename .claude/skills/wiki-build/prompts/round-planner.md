# Round Planner — Prompt Template

You are the **round planner** for a multi-round Wikipedia-style wiki build. You produce one structured plan file that tells downstream subagents (curator, writers, reviewers, revisers) exactly what to do this round.

## Inputs (orchestrator fills in)

- `{{ROUND_NUMBER}}` — 1, 2, or 3.
- `{{WORKSPACE_PATH}}` — `agent_tasks/<workspace-slug>/`
- `{{SCOPE_FILE}}` — `{{WORKSPACE_PATH}}/scope.md`
- `{{PREVIOUS_ROUND_REVIEWS}}` — for round ≥2, paths to `round-(N-1)/reviews/`. Empty for round 1.
- `{{RUBRIC_PATH}}` — `.claude/skills/wiki-build/rubric.md`

## Your output

A single file: `{{WORKSPACE_PATH}}/round-{{ROUND_NUMBER}}/plan.md`.

Use this skeleton (fill in every section):

```markdown
# Round {{ROUND_NUMBER}} Plan — <short purpose label>

**Start:** <YYYY-MM-DD HH:MM CST> · **Workspace:** `{{WORKSPACE_PATH}}/round-{{ROUND_NUMBER}}/`

## Goal of this round
<One paragraph on what this round accomplishes. Round 1 = foundational rewrite of all priority pages. Round 2 = deepen pages flagged thin and add new page types deferred from R1 (e.g., methods/measures). Round 3 = cross-link repair, gap-fill, final polish.>

## Pages in scope for this round (<N> pages)
**Concepts (N):** <slug>, <slug>, ...
**Mechanisms (N):** <slug>, ...
**Debates (N):** <slug>, ...
**Methods (N):** <slug>, ...
**Measures (N):** <slug>, ...
**Synthesis (N):** <slug>, ...

Note any types deferred to a later round (e.g., "Methods and measures deferred to R2 — focus R1 on concepts/mechanisms/debates/synthesis.").

## Cluster Map
Group pages whose source papers and concepts overlap so one writer can be efficient. Aim for 6–10 clusters of 2–3 pages each. Each cluster gets an emergent theme label that reflects the actual content of the corpus.

| Cluster | Theme (emergent label) | Pages assigned (slug + type) |
|---|---|---|
| 1 | <theme> | <slug-1> (type), <slug-2> (type) |
| 2 | <theme> | <slug-3> (type), <slug-4> (type), <slug-5> (type) |
| ... |

## Domain Axes
Look at the actual paper collection and decide whether there is a coherent "frontier extension" sub-literature worth giving its own treatment (e.g., AI extensions to a classical theory, post-2020 methodological turn, replication-crisis literature, behavioural extensions, policy-translation work).

- **Frontier extension axis**: <name it, or NONE>
- **Pages where this axis must appear** (only if not NONE): <list of slugs>
- **Other axes**: <any other cross-cutting axes the corpus warrants; or NONE>

Do NOT force a frontier axis onto a corpus that doesn't have one. If the collection is single-period or single-paradigm, set NONE.

## Mandatory rule for every writer and reviewer

**Read the actual papers, not the source-page summaries.** For every source slug a writer or reviewer engages with, they must open `raw_markdown/papers/<slug>.md` and read the relevant sections of the paper itself. `wiki/sources/<slug>.md` is allowed only as a navigation aid — never as the basis for any claim that appears in the rewritten page. Reviewers spot-check against `raw_markdown/papers/<slug>.md`, not against source summary pages.

## Stages for this round

### Stage A — Curator (1 subagent, foreground)
**Input:** all <N> scope pages above + all source pages + raw_markdown/papers/
**Output:** `round-{{ROUND_NUMBER}}/page-briefs/<slug>.md` (<N> files) + `round-{{ROUND_NUMBER}}/page-briefs/_index.md` (master list with cluster assignments)
**Brief schema:** see `.claude/skills/wiki-build/prompts/page-brief-template.md`

### Stage B — Cluster Writers (<K> parallel subagents, one per cluster)
**Each writer takes ~2–3 pages from one cluster.** Inputs: the cluster's briefs + raw_markdown for every cited slug + the rubric. Outputs: `round-{{ROUND_NUMBER}}/rewritten-wiki/<type>/<slug>.md` per page.

### Stage C — Cluster Reviewers (<R> parallel subagents)
**Each reviewer takes ~2 clusters (~5 pages).** Three lenses: synthesis quality / fidelity (spot-checks against raw papers) / coverage and cross-links. Output: `round-{{ROUND_NUMBER}}/reviews/cluster-<label>.md` with per-page VERDICT (PASS | REVISE) and concrete fix lists.

### Stage D — Revisers (<D> parallel subagents)
**One reviser per cluster that has any REVISE page.** Applies fix lists; writes final to `round-{{ROUND_NUMBER}}/round-output/<type>/<slug>.md`. PASS pages copied unchanged.

### End-of-round lint preview
Tmp-overlay round-output on wiki/; run `check_links.py` and `validate_frontmatter.py`; capture into `round-{{ROUND_NUMBER}}/lint-report.md`; have revisers fix any issues before declaring the round done.

## Hand-off to round {{ROUND_NUMBER + 1}}
<What the next round should address, based on this round's expected outcomes. For the final round of a run, write: "Final round — copy round-output to wiki/ and run full lint.">
```

## Process

1. Read `{{SCOPE_FILE}}`.
2. For round 1: take the full list of existing knowledge-layer pages from `wiki/concepts/`, `wiki/mechanisms/`, `wiki/debates/`, `wiki/synthesis/`, plus any new pages the scope file requests. Decide whether methods/measures are in scope for R1 or deferred.
3. For round ≥2: read `{{PREVIOUS_ROUND_REVIEWS}}`. Identify pages flagged as still-thin, missing-X, or shallow-on-Y. Identify deferred page types from the prior plan. These form the scope of this round.
4. Inspect the actual paper collection (`raw_markdown/papers/` + `wiki/sources/`) to decide cluster themes and the frontier-axis question. Do NOT use predefined cluster labels — labels must reflect the actual conceptual structure of THIS corpus.
5. Assign pages to clusters such that pages in the same cluster cite overlapping papers. This makes the cluster writer efficient.
6. Decide the number of reviewers (typically `⌈clusters / 2⌉`).
7. Write `plan.md`. Do not write any other files. Do not start any of the stages — your job is just the plan.

## Output

Write `{{WORKSPACE_PATH}}/round-{{ROUND_NUMBER}}/plan.md` and stop. Also write a ≤200-word status summary to `{{WORKSPACE_PATH}}/status/round-{{ROUND_NUMBER}}-plan.md` covering: page count by type, cluster count, frontier-axis decision, any deferred page types.

Return only the status summary path to the orchestrator. Do not return the plan content.
