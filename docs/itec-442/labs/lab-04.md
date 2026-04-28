---
title: "Lab 04: Consumer Behavior & A/B Test Design"
course: ITEC-442
topic: Consumer Behavior & Digital Psychology
week: 4
difficulty: ⭐⭐
estimated_time: 75 minutes
---

# Lab 04: Consumer Behavior & A/B Test Design

| Field | Details |
|---|---|
| **Course** | ITEC-442 — Electronic Commerce |
| **Week** | 4 |
| **Difficulty** | ⭐⭐ Intermediate |
| **Estimated Time** | 75 minutes |
| **Topic** | Consumer Behavior & Digital Psychology |
| **Prerequisites** | Python 3.10+, `pip install scipy` |
| **Deliverables** | `consumer_journey.md`, `bias_audit.md`, `ab_test_plan.md`, `clv_calculator.py` |

---

## Overview

Understanding *why* consumers buy — and why they don't — is the foundation of every conversion optimization decision. In this lab you will map a consumer decision journey, audit a real e-commerce site for cognitive biases, design a statistically valid A/B test, and build a Customer Lifetime Value calculator. These are real skills used daily by e-commerce product managers and growth teams.

---

## Part A — Consumer Decision Journey Map (20 pts)

Map the complete purchase journey for a **specific persona** buying a **specific product** from a **real e-commerce site**. Choose your own combination (e.g., a 35-year-old parent buying a car seat on Amazon, or a college student buying textbooks on Chegg).

Create `consumer_journey.md` with this structure:

```markdown
# Consumer Decision Journey Map

**Persona:** [Name, age, occupation, relevant context]
**Product:** [Specific product being purchased]
**Platform:** [E-commerce site]

---

## Stage 1: Need Recognition
- **Trigger:** What event prompted this purchase?
- **Emotional state:** (anxious, excited, pressured...)
- **Initial action:** What does the persona do first?
- **Touchpoints:** [search engine / social media / word-of-mouth / ad]

## Stage 2: Information Search
- **Search behavior:** What terms do they search? On what platforms?
- **Sources consulted:** (Google, YouTube reviews, Reddit, brand site, comparison sites)
- **Key questions they need answered:**
- **Pain points in this stage:** What frustrates them?
- **Opportunity:** How could the brand show up better here?

## Stage 3: Evaluation of Alternatives
- **Competitors considered:** (list 2–3)
- **Decision criteria ranked:** (price, reviews, shipping speed, brand trust, return policy)
- **How they compare:**
  | Criterion | Your Brand | Competitor A | Competitor B |
  |-----------|-----------|-------------|-------------|
  | Price | | | |
  | Reviews | | | |
  | Shipping | | | |
- **Cognitive biases active in this stage:**

## Stage 4: Purchase Decision
- **Final trigger:** What tips them into buying?
- **Friction points:** What could cause cart abandonment?
- **Checkout experience:** What did they encounter?
- **Payment method:** How did they pay? Why?

## Stage 5: Post-Purchase
- **Confirmation & shipping:** How was communication?
- **Unboxing & first use:** What was the experience?
- **Satisfaction / regret:** How do they feel?
- **Loyalty actions:** Do they review? Reorder? Refer?
- **Churn risk:** What could cause them to switch next time?

---

## Journey Summary
- **Biggest friction point:** [stage + specific issue]
- **Biggest delight moment:** [stage + what worked well]
- **Top recommendation for the brand:** [1 actionable improvement]
```

---

## Part B — Cognitive Bias Audit (20 pts)

Visit a real e-commerce product page (your choice). Screenshot it. Then complete `bias_audit.md` — identify **at least 6 distinct cognitive biases** being used on the page:

| # | Bias Name | Where on Page | How It's Used | Ethical? (Y/N/Borderline) |
|---|-----------|--------------|---------------|--------------------------|
| 1 | Scarcity bias | "Only 3 left in stock" badge | Creates urgency, may be manufactured | Borderline |
| 2 | Social proof | "4.7★ (12,847 reviews)" | Signals quality via crowd wisdom | Yes |
| 3 | | | | |
| ... | | | | |

**Bias reference list** (from Week 4):
- Scarcity / FOMO
- Social proof
- Anchoring (crossed-out price)
- Loss aversion ("Don't miss out")
- Authority bias (expert endorsements)
- Decoy effect (three pricing tiers)
- Default effect (pre-selected options)
- Framing effect (savings vs. cost)
- Endowment effect (free trial)
- Commitment & consistency (wishlists)

After the table, write **3 paragraphs**:
1. Which bias is most effective on this page and why?
2. Which use (if any) crosses an ethical line? Explain using the Week 4 framework.
3. What one bias are they NOT using that would most improve conversion?

---

## Part C — A/B Test Design (30 pts)

Design a statistically rigorous A/B test for a real optimization hypothesis.

**Scenario:** You are the conversion rate manager for a mid-size online clothing store. Current checkout page conversion rate is **2.3%**. You hypothesize that changing the CTA button from "Proceed to Checkout" to "Complete My Order" will improve conversion.

Complete `ab_test_plan.md`:

```markdown
# A/B Test Plan

## Test Overview
- **Hypothesis:** Changing the CTA button text from "Proceed to Checkout" to "Complete My Order"
  will increase checkout page conversion rate by at least 10% relative.
- **Primary metric:** Checkout conversion rate (orders / checkout page visitors)
- **Secondary metrics:** Average order value, time on checkout page, cart abandonment rate

## Statistical Parameters
- **Baseline conversion rate:** 2.3%
- **Minimum detectable effect (MDE):** 10% relative = 2.53% target rate
- **Statistical significance level (α):** 0.05 (95% confidence)
- **Statistical power (1-β):** 0.80 (80% power)
- **Tails:** Two-tailed test (we want to detect both improvements and regressions)

## Sample Size Calculation
[Show your calculation or use the formula below]
```

Then use Python to calculate the required sample size:

```python
# ab_sample_size.py
from scipy.stats import norm
import math

def sample_size_per_group(p1, p2, alpha=0.05, power=0.80):
    """
    p1: baseline conversion rate
    p2: target conversion rate
    Returns: required sample size per group
    """
    z_alpha = norm.ppf(1 - alpha/2)  # two-tailed
    z_beta  = norm.ppf(power)

    p_bar = (p1 + p2) / 2
    n = (z_alpha * math.sqrt(2 * p_bar * (1 - p_bar)) +
         z_beta  * math.sqrt(p1*(1-p1) + p2*(1-p2)))**2 / (p2-p1)**2

    return math.ceil(n)

p1 = 0.023  # baseline
p2 = 0.0253 # target (10% relative improvement)

n = sample_size_per_group(p1, p2)
print(f"Required sample size: {n:,} per group ({n*2:,} total)")
print(f"At 50,000 daily checkout visitors, test duration: {math.ceil(n*2/50000)} days")

# Simulate test results
import random
random.seed(42)

control = sum(random.random() < p1 for _ in range(n))
variant = sum(random.random() < p2 for _ in range(n))

print(f"\nSimulated Results:")
print(f"Control:  {control}/{n} conversions ({control/n:.3%})")
print(f"Variant:  {variant}/{n} conversions ({variant/n:.3%})")

# Chi-square test
from scipy.stats import chi2_contingency
table = [[control, n-control], [variant, n-variant]]
chi2, p_val, _, _ = chi2_contingency(table)
print(f"Chi-square: {chi2:.3f}, p-value: {p_val:.4f}")
print(f"Result: {'SIGNIFICANT ✓' if p_val < 0.05 else 'NOT significant ✗'}")
```

Continue `ab_test_plan.md` with:

```markdown
## Test Protocol
- **Traffic allocation:** 50/50 control/variant
- **Segmentation:** [Any segment exclusions? Mobile vs desktop split?]
- **Duration:** [X days — explain why]
- **Guardrail metrics:** [What would cause early termination?]

## Risks & Threats to Validity
- **Novelty effect:** ...
- **Seasonality:** ...
- **Sample ratio mismatch:** ...
- **Cookie deletion:** ...

## Decision Rules
- If p < 0.05 AND lift ≥ 10%: Ship the variant
- If p < 0.05 AND lift < 10%: ...
- If p ≥ 0.05: ...
- If guardrail metric degrades: ...

## Follow-up Tests
[What would you test next if this wins?]
```

---

## Part D — CLV Calculator (20 pts)

Create `clv_calculator.py` — an interactive CLV calculator for an e-commerce business:

```python
# clv_calculator.py

def calculate_clv(aov, purchase_freq, gross_margin, churn_rate, discount_rate=0.10):
    """
    Simple CLV: (AOV × Purchase Frequency × Gross Margin) / Churn Rate
    DCF CLV: accounts for time value of money
    """
    # Simple CLV
    simple_clv = (aov * purchase_freq * gross_margin) / churn_rate

    # Discounted CLV (3-year horizon)
    dcf_clv = 0
    for year in range(1, 4):
        annual_value = aov * purchase_freq * gross_margin * ((1 - churn_rate) ** (year-1))
        dcf_clv += annual_value / ((1 + discount_rate) ** year)

    return simple_clv, dcf_clv

print("=== E-Commerce CLV Calculator ===\n")

# Scenario 1: Fashion retailer
print("Scenario 1: Online Fashion Retailer")
s_clv, d_clv = calculate_clv(aov=85, purchase_freq=3.2, gross_margin=0.55, churn_rate=0.40)
print(f"  AOV: $85 | Frequency: 3.2x/yr | Margin: 55% | Churn: 40%")
print(f"  Simple CLV: ${s_clv:.2f}")
print(f"  3-Year DCF CLV: ${d_clv:.2f}")
print(f"  Max CAC (at 3:1 ratio): ${d_clv/3:.2f}\n")

# Scenario 2: Subscription box
print("Scenario 2: Monthly Subscription Box")
s_clv, d_clv = calculate_clv(aov=45, purchase_freq=12, gross_margin=0.35, churn_rate=0.08)
print(f"  AOV: $45 | Frequency: 12x/yr | Margin: 35% | Churn: 8%")
print(f"  Simple CLV: ${s_clv:.2f}")
print(f"  3-Year DCF CLV: ${d_clv:.2f}")
print(f"  Max CAC (at 3:1 ratio): ${d_clv/3:.2f}\n")

# Scenario 3: YOUR scenario (fill in)
print("Scenario 3: [Your Business]")
# TODO: Replace with your own e-commerce business scenario
your_aov = float(input("Average Order Value ($): "))
your_freq = float(input("Purchase frequency (times/year): "))
your_margin = float(input("Gross margin (0-1): "))
your_churn = float(input("Annual churn rate (0-1): "))
s_clv, d_clv = calculate_clv(your_aov, your_freq, your_margin, your_churn)
print(f"  Simple CLV: ${s_clv:.2f}")
print(f"  3-Year DCF CLV: ${d_clv:.2f}")
print(f"  Breakeven CAC: ${d_clv:.2f}")
print(f"  Max CAC (at 3:1 LTV:CAC ratio): ${d_clv/3:.2f}")
```

Run both scenarios and the interactive one. In `clv_calculator_analysis.md` (one page), explain:
1. Why is the subscription box CLV so much higher despite lower AOV?
2. What happens to CLV if churn rate drops from 40% to 30%? Calculate it.
3. What is the maximum a business should spend on CAC? What ratio did you use and why?

---

## Submission Checklist

- [ ] `consumer_journey.md` — full 5-stage map with analysis
- [ ] `bias_audit.md` — 6+ biases identified + 3 paragraphs
- [ ] `ab_test_plan.md` — complete plan with sample size calculation
- [ ] `ab_sample_size.py` — runs, outputs sample size + simulated results
- [ ] `clv_calculator.py` — runs all 3 scenarios
- [ ] `clv_calculator_analysis.md` — 3 analysis questions answered

---

## Grading

| Component | Points |
|-----------|--------|
| Part A — Consumer journey map (all 5 stages, specific and detailed) | 20 |
| Part B — Bias audit (6+ biases, ethics analysis, recommendation) | 20 |
| Part C — A/B test design (sample size calculated, protocol complete) | 30 |
| Part D — CLV calculator (runs, analysis questions answered) | 20 |
| Overall quality of analysis and writing | 10 |
| **Total** | **100** |
