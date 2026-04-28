---
title: "Lab 02: Digital Marketplace Competitive Analysis"
course: ITEC-442
topic: Digital Marketplaces & Platform Economics
week: 2
difficulty: ⭐⭐
estimated_time: 75 minutes
---

# Lab 02: Digital Marketplace Competitive Analysis

| Field | Details |
|---|---|
| **Course** | ITEC-442 — Electronic Commerce |
| **Week** | 2 |
| **Difficulty** | ⭐⭐ Intermediate |
| **Estimated Time** | 75 minutes |
| **Topic** | Digital Marketplaces & Platform Economics |
| **Prerequisites** | Lab 01 complete |
| **Deliverables** | `marketplace_analysis.md`, `platform_scorecard.md`, `pricing_model.md` |

---

## Overview

Digital marketplaces are the dominant e-commerce infrastructure of the modern web. Understanding how they compete — through pricing, trust, liquidity, and ecosystem lock-in — is essential for anyone building on or competing with them. In this lab you will apply platform economics frameworks to compare three major marketplaces, build a competitive scorecard, and design a fee structure for a new marketplace entrant.

---

## Part A — Select Your Three Marketplaces (5 pts)

Choose **one marketplace from each category** below. You will compare all three throughout the lab.

| Category | Options |
|----------|---------|
| General retail | Amazon Marketplace, Walmart Marketplace, eBay |
| Vertical/niche | Etsy (handmade), StockX (sneakers), Reverb (music gear), Depop (fashion) |
| Services/gig | Fiverr, Upwork, TaskRabbit, Thumbtack |

Document your choices and rationale (1 sentence each) in `marketplace_analysis.md`.

---

## Part B — Platform Profile (30 pts)

For each of your three chosen marketplaces, research and document:

```markdown
## [Marketplace Name]

### Overview
- Founded: 
- Business model: (B2C / B2B / C2C / hybrid)
- Primary category:
- Geographic reach:

### Scale Metrics (most recent data available)
- Gross Merchandise Value (GMV): $
- Active buyers: 
- Active sellers:
- Annual revenue: $
- Take rate (revenue / GMV): %

### Monetization Structure
| Fee Type | Rate/Amount | Who Pays |
|----------|------------|----------|
| Listing fee | | |
| Transaction fee | | |
| Payment processing | | |
| Subscription/membership | | |
| Advertising (promoted listings) | | |
| Fulfillment services | | |

### Trust & Safety Mechanisms
- Seller verification:
- Buyer protection:
- Dispute resolution:
- Review system:

### Liquidity Strategy
(How does the platform ensure enough buyers AND sellers?)
- Seller acquisition:
- Buyer acquisition:
- Geographic expansion approach:
```

---

## Part C — Competitive Scorecard (30 pts)

Build a side-by-side comparison scorecard in `platform_scorecard.md`. Rate each platform 1–5 on each dimension and justify every score in 1–2 sentences.

| Dimension | Marketplace 1 | Marketplace 2 | Marketplace 3 |
|-----------|:---:|:---:|:---:|
| **Seller value** (fees, tools, reach) | /5 | /5 | /5 |
| **Buyer value** (selection, price, UX) | /5 | /5 | /5 |
| **Trust & safety** | /5 | /5 | /5 |
| **Network effects strength** | /5 | /5 | /5 |
| **Switching costs** (multi-homing difficulty) | /5 | /5 | /5 |
| **Monetization efficiency** (take rate vs value) | /5 | /5 | /5 |
| **Innovation velocity** | /5 | /5 | /5 |
| **International expansion** | /5 | /5 | /5 |
| **TOTAL** | /40 | /40 | /40 |

After the table, write a **500-word competitive summary** answering:
- Which platform has the strongest moat and why?
- Which platform is most vulnerable to disruption?
- What is one strategic move each platform should make in the next 2 years?

---

## Part D — New Marketplace Pricing Model (25 pts)

You are founding **CraftLink** — a marketplace for independent furniture makers to sell directly to consumers. Design the full pricing model in `pricing_model.md`.

Address each of these decisions:

**1. Which side to subsidize at launch?**
Most successful marketplaces subsidize one side early. Who should CraftLink acquire first — buyers or sellers? Why? (Reference the Week 2 cold-start literature.)

**2. Fee structure design**
Design the complete fee table:

| Fee | Rate | Rationale |
|-----|------|-----------|
| Seller listing fee | | |
| Transaction fee | | |
| Payment processing | | |
| Premium seller subscription | | |
| Promoted placement | | |
| Buyer protection insurance | | |

**3. Take rate calculation**
Calculate CraftLink's blended take rate as a percentage of GMV. Compare to competitors in similar categories. Is it competitive?

**4. Revenue projections**
Build a simple Year 1–3 projection:

```
Year 1:
  Target GMV: $___
  Take rate: ___%
  Projected revenue: $___
  Estimated seller count: ___
  Estimated buyer count: ___

Year 2: ...
Year 3: ...
```

**5. Chicken-and-egg strategy**
Write a 200-word plan for how CraftLink will solve the cold-start problem — how will you get the first 100 sellers AND the first 1,000 buyers?

---

## Part E — Platform Failure Case Study (10 pts)

Research a **failed** digital marketplace (e.g., Fab.com, Homejoy, Beepi, Quirky). Write 3 paragraphs in `marketplace_analysis.md`:

1. What was the business model and why did it seem promising?
2. What went wrong? (unit economics, trust failures, competition, regulatory, etc.)
3. What lesson does this failure teach about marketplace design?

---

## Submission Checklist

- [ ] `marketplace_analysis.md` — Parts A, B, E
- [ ] `platform_scorecard.md` — scored table + 500-word summary
- [ ] `pricing_model.md` — CraftLink full pricing model + projections

---

## Grading

| Component | Points |
|-----------|--------|
| Part A — Marketplace selection with rationale | 5 |
| Part B — Three platform profiles (all fields researched) | 30 |
| Part C — Competitive scorecard (scores justified + summary) | 30 |
| Part D — CraftLink pricing model (all 5 sections) | 25 |
| Part E — Failure case study (3 paragraphs, lessons clear) | 10 |
| **Total** | **100** |
