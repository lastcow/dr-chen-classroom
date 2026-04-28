---
title: "Lab 05: Digital Analytics with GA4"
course: ITEC-442
topic: Market Research & Digital Analytics
week: 5
difficulty: ⭐⭐
estimated_time: 80 minutes
---

# Lab 05: Digital Analytics with GA4

| Field | Details |
|---|---|
| **Course** | ITEC-442 — Electronic Commerce |
| **Week** | 5 |
| **Difficulty** | ⭐⭐ Intermediate |
| **Estimated Time** | 80 minutes |
| **Topic** | Market Research & Digital Analytics |
| **Prerequisites** | Google Account, Python 3.10+, `pip install pandas matplotlib` |
| **Deliverables** | GA4 report screenshots, `funnel_analysis.py` output, `analytics_report.md` |

---

## Overview

Data is the lifeblood of e-commerce decision-making. Every pricing change, campaign launch, and UX redesign should be evaluated against metrics. In this lab you will explore the Google Analytics 4 Demo Account, analyze a simulated purchase funnel, compute key e-commerce KPIs, and write a data-driven recommendations report — the same workflow used by analytics teams at e-commerce companies.

---

## Part A — GA4 Demo Account Setup (10 pts)

**Step 1:** Access the GA4 Demo Account
1. Go to [https://analytics.google.com/analytics/web/demoAccount](https://analytics.google.com/analytics/web/demoAccount)
2. Click **"Access Demo Account"** — this is Google's real analytics data for the Google Merchandise Store
3. Make sure you select the **"GA4 - Google Merchandise Store"** property (not the UA property)

**Step 2:** Navigate and orient yourself. Take screenshots of:
- The **Home** overview panel
- The **Reports → Life cycle → Acquisition** section
- The **Reports → Life cycle → Monetization → Purchase journey** section

**Step 3:** Answer in `analytics_report.md`:
1. What is the current **30-day revenue**?
2. What is the **top traffic source** by sessions?
3. What is the **overall purchase conversion rate**?

---

## Part B — Purchase Funnel Analysis (30 pts)

Navigate to **Reports → Life cycle → Monetization → Purchase journey**.

This funnel shows:
```
Session Start → Product View → Add to Cart → Begin Checkout → Purchase
```

**B1.** Record the abandonment rate at each stage:

| Stage | Users | Drop-off to Next Stage | Abandonment Rate |
|-------|-------|----------------------|-----------------|
| Session Start | | — | — |
| Product View | | | % |
| Add to Cart | | | % |
| Begin Checkout | | | % |
| Purchase | | | % |

**B2.** Where is the biggest drop-off? What are 3 possible reasons for that specific drop?

**B3.** Navigate to **Explore → Funnel exploration**. Create a custom funnel with these events:
- `session_start`
- `view_item`
- `add_to_cart`
- `begin_checkout`
- `purchase`

Set the breakdown dimension to **Device category** (mobile/desktop/tablet). Screenshot the result.

**B4.** Compare mobile vs desktop conversion rates. Which device converts better? What UX differences explain this gap?

---

## Part C — Python Funnel Simulation (25 pts)

Simulate funnel analysis with Python using data modeled on typical e-commerce benchmarks:

```python
# funnel_analysis.py
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# Simulated monthly funnel data (3 months)
data = {
    "month": ["Jan", "Feb", "Mar"],
    "sessions":      [125000, 138000, 142000],
    "product_views": [ 68000,  75000,  79000],
    "add_to_cart":   [ 18500,  21000,  23500],
    "checkout_start":[  8200,   9100,  10200],
    "purchases":     [  2460,   2730,   3060],
    "revenue":       [185400, 205600, 230400]
}

df = pd.DataFrame(data)

# ── Conversion rates ─────────────────────────────────────────────
df["view_rate"]     = df["product_views"]   / df["sessions"]      * 100
df["atc_rate"]      = df["add_to_cart"]     / df["product_views"] * 100
df["checkout_rate"] = df["checkout_start"]  / df["add_to_cart"]   * 100
df["purchase_rate"] = df["purchases"]       / df["checkout_start"]* 100
df["overall_cvr"]   = df["purchases"]       / df["sessions"]      * 100
df["aov"]           = df["revenue"]         / df["purchases"]

print("=== E-Commerce Funnel Analysis ===\n")
print(df[["month","sessions","purchases","overall_cvr","aov"]].to_string(index=False))
print(f"\nAverage CVR: {df['overall_cvr'].mean():.2f}%")
print(f"Average AOV: ${df['aov'].mean():.2f}")
print(f"Revenue MoM growth: {((df['revenue'].iloc[-1]/df['revenue'].iloc[0])-1)*100:.1f}%")

# ── Funnel visualization ─────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Chart 1: Funnel chart (March data)
stages = ["Sessions", "Product Views", "Add to Cart", "Checkout", "Purchase"]
values = [df["sessions"].iloc[-1], df["product_views"].iloc[-1],
          df["add_to_cart"].iloc[-1], df["checkout_start"].iloc[-1],
          df["purchases"].iloc[-1]]
colors = ["#1a237e","#283593","#3949ab","#5c6bc0","#7986cb"]

ax1 = axes[0]
for i, (stage, val, color) in enumerate(zip(stages, values, colors)):
    width = val / values[0]
    ax1.barh(i, width, color=color, height=0.6)
    ax1.text(width + 0.01, i, f"{stage}: {val:,}", va="center", fontsize=9)

ax1.set_xlim(0, 1.4)
ax1.set_yticks([])
ax1.set_xlabel("Proportion of Sessions")
ax1.set_title("March Purchase Funnel")
ax1.invert_yaxis()

# Chart 2: CVR trend over 3 months
ax2 = axes[1]
ax2.plot(df["month"], df["overall_cvr"], marker="o", linewidth=2, color="#0f3460", label="Overall CVR")
ax2.plot(df["month"], df["atc_rate"], marker="s", linewidth=2, color="#c8a951", label="Add-to-Cart Rate")
ax2.set_title("Conversion Rate Trends")
ax2.set_ylabel("Rate (%)")
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("funnel_analysis.png", dpi=150)
print("\nFunnel chart saved: funnel_analysis.png")

# ── Revenue impact calculator ────────────────────────────────────
print("\n=== Revenue Impact Calculator ===")
baseline_cvr = df["overall_cvr"].iloc[-1]
baseline_rev = df["revenue"].iloc[-1]
sessions     = df["sessions"].iloc[-1]
aov          = df["aov"].iloc[-1]

for improvement in [0.1, 0.2, 0.5]:
    new_cvr = baseline_cvr * (1 + improvement)
    new_purchases = sessions * new_cvr / 100
    new_revenue = new_purchases * aov
    uplift = new_revenue - baseline_rev
    print(f"  CVR +{improvement*100:.0f}%: ${uplift:,.0f} additional monthly revenue")
```

Run and include output + chart in submission.

---

## Part D — KPI Dashboard Design (25 pts)

Design a **one-page KPI dashboard** for a hypothetical e-commerce director's weekly review. Write `analytics_report.md` with:

**1. KPI Selection** — justify choosing exactly these 8 metrics (explain what each measures and why it matters):

| KPI | Formula | Target | Source |
|-----|---------|--------|--------|
| Overall Conversion Rate | Purchases / Sessions | ≥ 2.5% | GA4 |
| Average Order Value | Revenue / Purchases | ≥ $75 | GA4 |
| Cart Abandonment Rate | 1 - (Purchases/Add-to-Cart) | ≤ 65% | GA4 |
| Customer Acquisition Cost | Ad Spend / New Customers | ≤ $25 | Ads + GA4 |
| Return Customer Rate | Returning / Total buyers | ≥ 30% | GA4 |
| Revenue per Session | Revenue / Sessions | ≥ $1.80 | GA4 |
| Mobile Conversion Rate | Mobile purchases / sessions | ≥ 1.8% | GA4 |
| Email Revenue % | Email revenue / Total | ≥ 15% | GA4 + ESP |

**2. Alert Thresholds** — for each KPI, define a "yellow flag" and "red flag" threshold that would trigger investigation

**3. Week-over-Week Narrative** — using your Part B GA4 data and Part C simulation data, write a 300-word executive summary as if presenting to the director:
- What's working
- What needs attention
- Recommended actions for next week

**4. Instrumentation Gaps** — what data does your dashboard NOT have that would make it more valuable? List 3 missing signals and how you'd collect them.

---

## Part E — Market Research Tool (10 pts)

Use **Google Trends** (trends.google.com) to research seasonality for one product category.

1. Search for two competing products/brands in the same category
2. Set the time range to 5 years, geography to United States
3. Export the data as CSV
4. Load it in Python and plot both trends on the same chart

In `analytics_report.md`, answer:
- What seasonal pattern do you observe?
- When should an e-commerce store in this category ramp up ad spend?
- What is the year-over-year trend (growing, stable, declining)?

---

## Submission Checklist

- [ ] GA4 demo account screenshots (Home, Acquisition, Purchase Journey)
- [ ] `funnel_analysis.py` — runs, outputs analysis + chart
- [ ] `funnel_analysis.png` — 2-panel chart
- [ ] `analytics_report.md` — Parts A, D, E complete
- [ ] Google Trends chart (Python-generated)

---

## Grading

| Component | Points |
|-----------|--------|
| Part A — GA4 setup + 3 questions answered with real data | 10 |
| Part B — Funnel analysis (table complete, mobile vs desktop) | 30 |
| Part C — Python analysis (runs, correct calculations, chart) | 25 |
| Part D — KPI dashboard (8 KPIs justified, alerts, narrative) | 25 |
| Part E — Google Trends analysis with Python chart | 10 |
| **Total** | **100** |
