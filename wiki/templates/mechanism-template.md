---
title: ""
type: mechanism
status: active
papers: []
tags: []
---

<!--
Wikipedia-style mechanism page. The structural backbone is the causal channel, not the papers.
Read .claude/skills/wiki-build/rubric.md before writing.
-->

# Mechanism Name

One encyclopedic paragraph (4–6 sentences) that names the causal channel, sketches how it works, says where it operates in the literature, and previews the page.

## The Causal Channel

A precise statement of the mechanism: from what initial condition, through what intermediate step, to what outcome. State the channel in terms general enough to apply across the contexts where the literature invokes it. Use a short bullet list ONLY if the channel has discrete sequential steps:

1. <Initial condition>
2. <Intermediate>
3. <Outcome>

Otherwise prose.

## Micro-foundations

The underlying preferences, beliefs, constraints, or technologies that generate the channel. Cite the founding paper(s) inline. Where there are competing micro-foundations for the same channel, name them.

## Formal Representation *(if applicable)*

The formal model the channel sits inside. Variables, key equation, comparative-statics result.

$$
\text{e.g., } \quad y = f(x; \theta), \qquad \frac{\partial y}{\partial x} > 0 \text{ when } \theta > \bar\theta.
$$

## Empirical Signatures

What the mechanism predicts, and what empirical evidence corroborates or fails to corroborate it. Organise by sub-finding, multi-cite where convergent.

## Scope Conditions

When the mechanism operates. When it does not. When it reverses. Be specific — name the conditions, cite where they were established.

> **Current assessment (YYYY-MM):** Strength of evidence and scope conditions in one short callout.

## Failure Modes and Alternatives

Competing mechanisms that produce the same observable, or boundary conditions where this mechanism breaks down. Where another mechanism is the dominant alternative, link to it: [[mechanisms/<other>]].

## Frontier / Extension *(only if the round plan declares this in scope)*

How the mechanism is being recast or extended (e.g., AI-mediated version, behavioural variant). Omit if no such sub-literature.

## Open Questions

3–6 bullet points.

## See also

- [[concepts/<related-concept>]]
- [[mechanisms/<related-mechanism>]]
- [[debates/<related-debate>]]
- [[measures/<related-measure>]]
- Major source pages: [[<slug-1>]], [[<slug-2>]]
