---
title: "Lab 01: E-Commerce Business Model Analysis"
course: ITEC-442
topic: E-Commerce Foundations & Business Models
week: 1
difficulty: ⭐⭐
estimated_time: 75 minutes
---

# Lab 01: E-Commerce Business Model Analysis

| Field | Details |
|---|---|
| **Course** | ITEC-442 — Electronic Commerce |
| **Week** | 1 |
| **Difficulty** | ⭐⭐ Intermediate |
| **Estimated Time** | 75 minutes |
| **Topic** | E-Commerce Foundations & Business Models |
| **Prerequisites** | None — research and writing lab |
| **Deliverables** | `business_model_analysis.md`, `value_canvas.md`, `network_effects.md` |

---

## Overview

E-commerce success depends on choosing the right business model, building a compelling value proposition, and exploiting network effects before competitors do. In this lab you will classify and analyze five real companies using structured frameworks from Week 1, compute basic financial metrics, and build a value proposition canvas for a business of your choice.

---

## Part A — Company Classification (20 pts)

Research and classify each of the following companies. For each, fill out the table in `business_model_analysis.md`:

| Company | Primary Model | Secondary Models | Revenue Streams | Pure-Play / Click-and-Mortar / Brick-and-Mortar |
|---------|--------------|-----------------|-----------------|------------------------------------------------|
| Amazon | | | | |
| Etsy | | | | |
| Salesforce | | | | |
| Airbnb | | | | |
| Shopify | | | | |

**Model taxonomy** (from Week 1): B2C, B2B, B2G, C2C, C2B, B2B2C, D2C

For each company also answer:
1. What is the primary **value proposition** — is it selection, price, convenience, customization, or community?
2. Who are the **two sides** of the platform (if a marketplace)? Who is the buyer and who is the seller?
3. Name **one direct competitor** and explain what differentiates the company from it.

---

## Part B — Revenue Model Deep Dive (20 pts)

Choose **one** company from Part A. Research and document its full revenue model in `business_model_analysis.md`:

1. **Revenue streams** — list every way the company makes money (subscription, transaction fees, advertising, licensing, etc.) with approximate percentage of total revenue for each
2. **Cost structure** — what are the major cost categories? (COGS, fulfillment, R&D, marketing, G&A)
3. **Unit economics** — find or estimate:
   - Customer Acquisition Cost (CAC)
   - Average Order Value (AOV)
   - Gross Margin %
   - Customer Lifetime Value (CLV) using the formula: `CLV = (AOV × Purchase Frequency × Gross Margin) / Churn Rate`
4. **Profitability analysis** — is the company profitable? If not, what is its path to profitability?

Cite all data sources (annual report, 10-K, Statista, etc.).

---

## Part C — Value Proposition Canvas (25 pts)

Create `value_canvas.md` for a **real or hypothetical** e-commerce business of your choice (not one of the Part A companies). Use the Value Proposition Canvas framework:

```markdown
# Value Proposition Canvas — [Company Name]

## Customer Profile

### Customer Jobs
(What tasks are customers trying to accomplish? Functional, social, emotional.)
- Job 1: ...
- Job 2: ...
- Job 3: ...

### Customer Pains
(What frustrates customers before, during, or after trying to get the job done?)
- Pain 1: ...
- Pain 2: ...
- Pain 3: ...

### Customer Gains
(What outcomes do customers want? What would delight them?)
- Gain 1: ...
- Gain 2: ...
- Gain 3: ...

## Value Map

### Products & Services
(What does the company offer?)
- ...

### Pain Relievers
(How does the product/service reduce customer pains?)
- Pain Reliever 1: [addresses Pain X] ...
- Pain Reliever 2: ...

### Gain Creators
(How does the product/service create customer gains?)
- Gain Creator 1: [addresses Gain X] ...
- Gain Creator 2: ...

## Fit Assessment
(Where is there strong fit between value map and customer profile? Where are gaps?)
- Strong fit: ...
- Gaps: ...
- Recommended improvements: ...
```

---

## Part D — Network Effects Analysis (20 pts)

Create `network_effects.md`. Choose **one** platform company (from any industry) that exhibits strong network effects.

Answer the following:

1. **Type of network effects** — which type(s) apply?
   - Direct (same-side): more users → more value for same users
   - Indirect (cross-side): more users on side A → more value for side B
   - Data network effects: more usage → better product → more users
   - Social network effects: identity/status tied to platform

2. **Cold start problem** — how did the company solve it? (e.g., targeted seeding, geographic expansion, subsidy one side)

3. **Quantify the effect** — use any publicly available data to estimate the magnitude of network effects. For example: "Every 10% increase in seller count on Etsy correlates with a X% increase in buyer retention" (cite source or use a proxy metric).

4. **Defensibility** — what would it take for a competitor to break these network effects? Is multi-homing possible?

---

## Part E — Long Tail Analysis (15 pts)

The long tail theory (Chris Anderson) states that e-commerce enables profitable sales of niche products that physical retail cannot stock.

Pick **one** of these sectors and find data to support or challenge the long tail theory in that sector:
- Music streaming (Spotify)
- Book sales (Amazon Kindle)
- Video (YouTube)
- App stores (Apple App Store)

Write 3–4 paragraphs in `business_model_analysis.md` that:
- Define what the "head" and "tail" look like in this sector
- Present actual data (top 1% of titles vs rest)
- Argue whether the long tail is growing or shrinking in this sector
- Explain the business model implications

---

## Submission Checklist

- [ ] `business_model_analysis.md` — Parts A, B, E complete
- [ ] `value_canvas.md` — complete canvas with fit assessment
- [ ] `network_effects.md` — complete analysis with data citation

---

## Grading

| Component | Points |
|-----------|--------|
| Part A — Company classification (5 companies, all fields) | 20 |
| Part B — Revenue model deep dive (CLV formula applied) | 20 |
| Part C — Value proposition canvas (all sections, fit assessment) | 25 |
| Part D — Network effects analysis (type, cold start, quantified) | 20 |
| Part E — Long tail analysis (data-supported, 3+ paragraphs) | 15 |
| **Total** | **100** |
