---
title: "Lab 06: UX Audit & Conversion Rate Optimization Plan"
course: ITEC-442
topic: B2C Strategy, UX Design & Conversion Optimization
week: 6
difficulty: ⭐⭐⭐
estimated_time: 85 minutes
---

# Lab 06: UX Audit & Conversion Rate Optimization Plan

| Field | Details |
|---|---|
| **Course** | ITEC-442 — Electronic Commerce |
| **Week** | 6 |
| **Difficulty** | ⭐⭐⭐ Advanced |
| **Estimated Time** | 85 minutes |
| **Topic** | B2C Strategy, UX Design & Conversion Optimization |
| **Prerequisites** | Lab 05 complete, web browser |
| **Deliverables** | `ux_audit.md`, `cro_plan.md`, annotated screenshots |

---

## Overview

Conversion Rate Optimization (CRO) is the systematic process of increasing the percentage of visitors who complete a desired action. A good UX audit identifies friction — every unnecessary click, confusing label, and slow page that bleeds revenue. In this lab you will conduct a structured heuristic evaluation of a real e-commerce site, score it against industry UX standards, prioritize issues by impact, and produce a professional CRO plan.

---

## Part A — Choose Your Audit Target (5 pts)

Select a **real, publicly accessible e-commerce site** that sells physical products. Good candidates:
- A brand you personally use
- A local or regional retailer
- A niche marketplace (not Amazon — too polished)

Document in `ux_audit.md`:
- Site URL
- Product category
- Estimated audience (B2C, demographics)
- Your rationale for choosing this site

---

## Part B — Heuristic Evaluation (30 pts)

Use **Nielsen's 10 Usability Heuristics** adapted for e-commerce. Rate each heuristic 1–5 (1=Severe violation, 5=Excellent) on the site's **product listing page**, **product detail page**, and **checkout flow**.

For each heuristic, provide:
- Score (1–5)
- Specific example from the site (quote button text, describe layout)
- Screenshot reference (take screenshots and label them)

| # | Heuristic | Score | Finding | Screenshot |
|---|-----------|:---:|---------|-----------|
| 1 | **Visibility of system status** (loading indicators, cart updates, order confirmation) | /5 | | |
| 2 | **Match between system and real world** (language users understand, familiar icons) | /5 | | |
| 3 | **User control & freedom** (easy to undo, back buttons, edit cart) | /5 | | |
| 4 | **Consistency & standards** (buttons look like buttons, links underlined) | /5 | | |
| 5 | **Error prevention** (form validation, clear required fields) | /5 | | |
| 6 | **Recognition over recall** (persistent cart, recently viewed, saved searches) | /5 | | |
| 7 | **Flexibility & efficiency** (guest checkout, saved addresses, keyboard shortcuts) | /5 | | |
| 8 | **Aesthetic & minimalist design** (no clutter, clear hierarchy, whitespace) | /5 | | |
| 9 | **Help users recognize & recover from errors** (clear error messages, suggestions) | /5 | | |
| 10 | **Help & documentation** (FAQs, live chat, return policy prominence) | /5 | | |
| | **TOTAL** | /50 | | |

**Severity scale:**
- 45–50: Excellent — minor polish needed
- 35–44: Good — a few friction points
- 25–34: Fair — meaningful revenue leakage
- Below 25: Poor — urgent redesign needed

---

## Part C — Friction Point Inventory (25 pts)

Go through the **complete purchase flow** on your chosen site: search → category → product → cart → checkout → confirmation. For each step, list every friction point you encounter.

```markdown
## Friction Point Inventory

### Product Search
- [ ] Search autocomplete: [present/absent/broken]
- [ ] Filter options: [sufficient/insufficient/confusing]
- [ ] Results relevance: [relevant/irrelevant]
- Friction found: ...

### Product Listing Page
- [ ] Images: [quality, zoom capability]
- [ ] Pricing: [clear/confusing/hidden fees]
- [ ] Social proof: [reviews visible/absent]
- Friction found: ...

### Product Detail Page
- [ ] CTA prominence: [clear/buried/confusing]
- [ ] Shipping info: [clear/vague/absent]
- [ ] Size/variant selection: [easy/confusing]
- [ ] Trust signals: [present/absent]
- Friction found: ...

### Shopping Cart
- [ ] Cart visibility: [persistent/hidden]
- [ ] Edit capability: [easy/difficult]
- [ ] Upsell/cross-sell: [helpful/aggressive/absent]
- Friction found: ...

### Checkout
- [ ] Guest checkout: [available/forced registration]
- [ ] Form fields: [minimal/excessive]
- [ ] Progress indicator: [present/absent]
- [ ] Payment options: [sufficient/limited]
- [ ] Security signals: [present/absent]
- Friction found: ...
```

Rank your top 5 friction points by estimated revenue impact (use the framework: Impact = Traffic Volume × Abandonment Rate × AOV × Potential Lift).

---

## Part D — CRO Prioritization Plan (30 pts)

Create `cro_plan.md` — a professional CRO roadmap.

**1. ICE Scoring**
For each of your top 5 friction points, score using the ICE framework:
- **Impact** (1–10): How much will fixing this improve conversion?
- **Confidence** (1–10): How confident are you this change will work?
- **Ease** (1–10): How easy is it to implement?
- **ICE Score** = (Impact + Confidence + Ease) / 3

| Issue | Impact | Confidence | Ease | ICE Score | Priority |
|-------|:------:|:----------:|:----:|:---------:|:--------:|
| No guest checkout | 9 | 8 | 6 | 7.7 | 1 |
| ... | | | | | |

**2. Test Plans**
For the **top 2 ICE-scored issues**, write a mini A/B test plan (hypothesis, variant description, success metric, sample size estimate).

**3. Quick Wins vs Strategic Changes**
Categorize all 5 fixes:
- **Quick wins** (< 1 week dev): List with expected lift %
- **Strategic changes** (1–4 weeks): List with expected lift % and tradeoffs
- **Long-term investment** (1+ month): List with rationale

**4. Revenue Impact Estimate**
Assume the site has 100,000 monthly sessions, 2.0% CVR, and $65 AOV.
Calculate the projected monthly revenue increase if you fix all 5 issues and achieve your expected lifts.

```
Baseline: 100,000 × 2.0% × $65 = $130,000/month

After fix 1 (CVR +0.3%): ...
After fix 2 (CVR +0.2%): ...
...
Total projected monthly revenue: $___
Annual uplift: $___
```

**5. Mobile-Specific Recommendations**
From Part B and your own mobile visit to the site, list 3 mobile-specific UX improvements not covered above.

---

## Part E — SEO Quick Audit (10 pts)

Use **Google PageSpeed Insights** (pagespeed.web.dev) to audit your site's product detail page.

Record the scores:
| Metric | Mobile | Desktop |
|--------|--------|---------|
| Performance | /100 | /100 |
| Accessibility | /100 | /100 |
| Best Practices | /100 | /100 |
| SEO | /100 | /100 |
| Largest Contentful Paint | s | s |
| Total Blocking Time | ms | ms |
| Cumulative Layout Shift | | |

In `cro_plan.md`, answer:
1. What is the biggest Core Web Vitals issue?
2. What revenue impact does a 1-second page load improvement have? (Use the Google formula: 1s faster = +2% conversion rate)
3. What is the single highest-priority technical fix?

---

## Submission Checklist

- [ ] `ux_audit.md` — Parts A, B, C complete with screenshot references
- [ ] `cro_plan.md` — Parts D, E complete with ICE scores and revenue projections
- [ ] Annotated screenshots (labeled with friction points found)
- [ ] PageSpeed Insights screenshot

---

## Grading

| Component | Points |
|-----------|--------|
| Part A — Target selection with rationale | 5 |
| Part B — Heuristic evaluation (all 10, specific examples) | 30 |
| Part C — Friction inventory (complete flow, top 5 ranked) | 25 |
| Part D — CRO plan (ICE scores, test plans, revenue impact) | 30 |
| Part E — SEO/performance audit with revenue calculation | 10 |
| **Total** | **100** |
