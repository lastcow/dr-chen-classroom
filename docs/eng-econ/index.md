---
title: Engineering Economics — Spring 2026
description: 15-lecture engineering economics course with web-based Reveal.js decks, reading materials, and discussion segments.
---

# Engineering Economics — Spring 2026

<div class="course-hero" markdown>

> **Instructor:** Dr. Zhijiang Chen  
> **Term:** Spring 2026 · 110 min sessions  
> **Format:** Reveal.js web decks · in-class discussions · weekly problem sets

</div>

---

## Course Overview

Engineering Economics is the discipline that lets engineers and software professionals make *defensible* money decisions — the kind that survive an auditor, a board review, or a CFO who has never written a line of code. Across fifteen lectures we move from the fundamentals of how money changes value over time, through the analytical toolkit (cash-flow analysis, NPV/IRR, break-even, sensitivity, decision trees), into the software-specific extensions (LOC and Function Points, COCOMO II, quality and maintenance economics, Build/Buy/Reuse, VBSE), and finally into the two AI-era topics that are reshaping cost estimation in 2026: productivity disruption and token-cost engineering.

The course is deliberately *quantitative*. Every lecture contains worked numerical examples, every problem set requires students to compute and justify a number, and every discussion segment grounds the math in a real-world decision a practising engineer might face this semester.

---

## Learning Outcomes

By the end of the course, students will be able to:

- Convert between present, future, and uniform-series cash flows at any compounding frequency.
- Choose among NPV, IRR, payback, and PI as a function of decision context, capital constraints, and stakeholder audience.
- Quantify break-even points and run single- and multi-variable sensitivity analyses on engineering proposals.
- Decompose project risk using decision trees, expected value, and Monte Carlo simulation.
- Estimate software size using LOC, IFPUG Function Points, and Use-Case Points; estimate effort and schedule with COCOMO II.
- Reason about quality, maintenance, and technical-debt cost over the lifecycle of a software system.
- Defend a Build vs. Buy vs. Reuse vs. SaaS recommendation in stakeholder-value terms.
- Model the unit economics of an AI feature: token cost, agent-call multipliers, cache hit rates, and project ROI.

---

## Lecture Schedule

| # | Date | Topic | Materials |
|---|------|-------|-----------|
| 1 | Wed 2026-06-03 | Course intro · Build vs Buy primer | — |
| 2 | Thu 2026-06-04 | Software Cost Concepts & Lifecycle Cost | — |
| 3 | **Fri 2026-06-05** | **Time Value of Money** | **[Lecture page](lecture-03.md) · [Deck](decks/lecture-03/index.html)** |
| 4 | Sat 2026-06-06 | Cash Flow Analysis & Equivalence | — |
| 5 | Sun 2026-06-07 | Investment Decisions & Alternative Selection | — |
| 6 | Mon 2026-06-08 | Break-even & Sensitivity Analysis | — |
| 7 | Tue 2026-06-09 | Risk & Decision under Uncertainty | — |
| 8 | Wed 2026-06-10 | Cost Estimation I — Size Metrics & Function Points | — |
| 9 | Thu 2026-06-11 | Cost Estimation II — COCOMO II | — |
| 10 | Fri 2026-06-12 | Quality & Maintenance Economics | — |
| 11 | Sat 2026-06-13 | Build / Buy / Reuse & VBSE | — |
| 12 | Sun 2026-06-14 | AI I — Estimation & Productivity Disruption | — |
| 13 | Mon 2026-06-15 | AI II — Token Economics & Project ROI | — |

---

## How to Use the Web Decks

Each lecture deck is a single-file Reveal.js 5 build that renders in any modern browser — no slide software required.

- **Open** the deck link to enter presentation mode.
- Press **S** to open speaker view (pacing notes, board-work prompts, sanity-check tricks).
- Press **F** to enter full-screen.
- Press **Esc** to see the slide overview grid.
- Press **B** to black out the screen during a discussion segment.

Decks include LaTeX rendered with MathJax, inline SVG cash-flow diagrams, and an in-class **discussion** segment per lecture with solo / pair / plenary timing.

---

## Reading & Reference

The course leans on three standard references and does not require a single textbook:

- **Park, C.S.** *Contemporary Engineering Economics* (6e). Pearson. — Chapters 2–9 cover the TVM, equivalence, NPV/IRR, and risk material.
- **Boehm, B. et al.** *Software Cost Estimation with COCOMO II*. Prentice Hall. — Required for Lectures 8–9.
- **Boehm, B. & Sullivan, K.** *Value-Based Software Engineering*. Springer. — Required for Lecture 11.

Selected papers (Brooks, *No Silver Bullet*; Boehm 1981; Cusumano 2024; OpenAI/Anthropic pricing papers, 2025) are linked from individual lecture pages.
