---
title: "Spaced Repetition"
type: concept
tags: [memory, scheduling, review]
papers: [luhmann-1992]
status: active
---

# Spaced Repetition

**Spaced repetition** is a learning technique in which review of a piece of information is scheduled at progressively longer intervals, timed to occur just before the information would otherwise be forgotten. It operationalises the *spacing effect* — the long-observed finding that learning distributed over time produces more durable retention than the same effort massed into a single session.

## The forgetting curve

The technique is motivated by an exponential model of forgetting, in which the probability $R$ of recalling an item decays with the time $t$ since the last review and a memory-strength constant $S$:

$$R = e^{-t/S}$$

Each successful review increases $S$, flattening the curve so that the next interval can be longer. Scheduling algorithms differ chiefly in how they update $S$ from review outcomes.

## Scheduling algorithms

Modern implementations range from fixed-interval ladders to adaptive schemes that adjust intervals per item based on recall difficulty. The shared design goal is to minimise total review time for a target retention level.

> [!note]
> Spaced repetition is most often paired with [[active-recall]]: the *review* is not a re-reading but a retrieval attempt, so the scheduling and the retrieval mechanism reinforce one another.

## Relation to note systems

In note-based knowledge management, spaced repetition is sometimes layered on top of a linked note collection such as a [[zettelkasten]], converting durable notes into review items so that a personal knowledge base doubles as a study deck.

## See also

- [[active-recall]]
- [[zettelkasten]]
- [[digital-vs-paper]]
