---
title: "Lab 03: E-Commerce Economic Impact Report"
course: ITEC-442
topic: Economic Impacts of E-Commerce
week: 3
difficulty: ⭐⭐
estimated_time: 80 minutes
---

# Lab 03: E-Commerce Economic Impact Report

| Field | Details |
|---|---|
| **Course** | ITEC-442 — Electronic Commerce |
| **Week** | 3 |
| **Difficulty** | ⭐⭐ Intermediate |
| **Estimated Time** | 80 minutes |
| **Topic** | Economic Impacts of E-Commerce |
| **Prerequisites** | Python 3.10+, `pip install pandas matplotlib` |
| **Deliverables** | `impact_report.md`, `ecommerce_analysis.py` output, charts |

---

## Overview

E-commerce has reshaped labor markets, retail geography, tax policy, and global trade in ways that are still unfolding. In this lab you will collect real economic data, analyze it with Python, build visualizations, and write a structured economic impact report — practicing the quantitative analysis skills that underpin business strategy decisions.

---

## Part A — Data Collection (20 pts)

Collect data from **publicly available sources** (U.S. Census Bureau, Bureau of Labor Statistics, OECD, Statista, eMarketer). Create a file `ecommerce_data.csv` with at least 10 years of annual data:

```csv
year,us_ecommerce_sales_bn,total_retail_sales_bn,ecommerce_share_pct,retail_jobs_thousands,warehouse_jobs_thousands,online_sellers_millions
2014,305.7,4692,6.5,15890,745,2.1
2015,341.7,4763,7.2,15932,812,2.4
2016,390.0,4858,8.0,15899,890,2.8
2017,449.9,5016,9.0,15775,985,3.2
2018,517.4,5282,9.8,15700,1102,3.8
2019,601.7,5467,11.0,15650,1230,4.5
2020,791.7,5621,14.0,15200,1520,5.9
2021,960.4,6589,14.6,15450,1680,6.8
2022,1033.0,7112,14.5,15600,1710,7.2
2023,1118.7,7543,14.8,15720,1780,7.8
```

!!! info "Data Sources"
    - U.S. Census Bureau: [census.gov/retail](https://www.census.gov/retail)
    - BLS Occupational Employment: [bls.gov/oes](https://www.bls.gov/oes)
    - Update the placeholder values above with real figures from your research. Cite every source.

---

## Part B — Python Analysis (35 pts)

Create `ecommerce_analysis.py`:

```python
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

df = pd.read_csv("ecommerce_data.csv")

print("=== E-Commerce Economic Impact Analysis ===\n")

# ── 1. Growth metrics ─────────────────────────────────────────────
df["yoy_growth_pct"] = df["us_ecommerce_sales_bn"].pct_change() * 100
df["ecommerce_vs_retail_ratio"] = df["us_ecommerce_sales_bn"] / df["total_retail_sales_bn"]

print("Year-over-Year E-Commerce Growth:")
print(df[["year","us_ecommerce_sales_bn","yoy_growth_pct","ecommerce_share_pct"]].to_string(index=False))

# ── 2. CAGR calculation ───────────────────────────────────────────
years = df["year"].max() - df["year"].min()
start_sales = df.loc[df["year"]==df["year"].min(), "us_ecommerce_sales_bn"].values[0]
end_sales   = df.loc[df["year"]==df["year"].max(), "us_ecommerce_sales_bn"].values[0]
cagr = ((end_sales / start_sales) ** (1/years) - 1) * 100
print(f"\n10-Year CAGR: {cagr:.1f}%")
print(f"Total growth: ${start_sales:.1f}B → ${end_sales:.1f}B (+{(end_sales/start_sales-1)*100:.0f}%)")

# ── 3. Labor market correlation ───────────────────────────────────
corr_retail = df["us_ecommerce_sales_bn"].corr(df["retail_jobs_thousands"])
corr_warehouse = df["us_ecommerce_sales_bn"].corr(df["warehouse_jobs_thousands"])
print(f"\nCorrelation: E-commerce growth vs retail jobs:    {corr_retail:.3f}")
print(f"Correlation: E-commerce growth vs warehouse jobs: {corr_warehouse:.3f}")

# ── 4. Charts ─────────────────────────────────────────────────────
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle("U.S. E-Commerce Economic Impact Analysis", fontsize=14, fontweight="bold")

# Chart 1: E-commerce sales vs total retail
ax1 = axes[0, 0]
ax1.bar(df["year"], df["total_retail_sales_bn"], label="Total Retail", color="#c8c8c8")
ax1.bar(df["year"], df["us_ecommerce_sales_bn"], label="E-Commerce", color="#0f3460")
ax1.set_title("E-Commerce vs Total Retail Sales ($B)")
ax1.set_xlabel("Year"); ax1.set_ylabel("Sales ($B)")
ax1.legend()

# Chart 2: E-commerce market share
ax2 = axes[0, 1]
ax2.plot(df["year"], df["ecommerce_share_pct"], marker="o", color="#0f3460", linewidth=2)
ax2.fill_between(df["year"], df["ecommerce_share_pct"], alpha=0.2, color="#0f3460")
ax2.set_title("E-Commerce Share of Total Retail (%)")
ax2.set_xlabel("Year"); ax2.set_ylabel("Share (%)")
ax2.yaxis.set_major_formatter(mtick.PercentFormatter())

# Chart 3: Job displacement vs creation
ax3 = axes[1, 0]
ax3.plot(df["year"], df["retail_jobs_thousands"], marker="s", label="Retail Jobs", color="#c62828")
ax3.plot(df["year"], df["warehouse_jobs_thousands"], marker="^", label="Warehouse Jobs", color="#2e7d32")
ax3.set_title("Retail vs Warehouse Employment (Thousands)")
ax3.set_xlabel("Year"); ax3.set_ylabel("Jobs (Thousands)")
ax3.legend()

# Chart 4: Online seller growth
ax4 = axes[1, 1]
ax4.bar(df["year"], df["online_sellers_millions"], color="#c8a951")
ax4.set_title("Online Sellers (Millions)")
ax4.set_xlabel("Year"); ax4.set_ylabel("Sellers (Millions)")

plt.tight_layout()
plt.savefig("ecommerce_impact_charts.png", dpi=150)
print("\nCharts saved: ecommerce_impact_charts.png")
```

Run:
```bash
python ecommerce_analysis.py
```

---

## Part C — Economic Impact Report (35 pts)

Write `impact_report.md` — a structured 800–1000 word economic analysis:

### Required Sections

**1. Executive Summary** (100 words)
Key findings from your data analysis in plain language.

**2. E-Commerce Growth Trajectory**
- Present your CAGR and growth chart
- Identify inflection points (pandemic effect 2020, post-pandemic normalization)
- Forecast: at current CAGR, what will e-commerce share be in 2028?

**3. Labor Market Disruption**
Using your correlation data:
- Is the relationship between e-commerce growth and retail jobs negative (displacement)?
- Is the relationship between e-commerce growth and warehouse jobs positive (creation)?
- Net job effect: is e-commerce a net job creator or destroyer in U.S. retail? Support with data.

**4. Geographic Impact**
Research and address: which types of retail locations have been hardest hit by e-commerce? (malls, strip malls, main street)? Which have survived? Use "retail apocalypse" literature and counterarguments.

**5. Tax & Regulatory Impact**
- Explain the significance of the **South Dakota v. Wayfair (2018)** Supreme Court decision
- How did it change state sales tax obligations for online sellers?
- Estimate how much additional state tax revenue resulted

**6. Policy Recommendation**
Write a 150-word recommendation for ONE policy change that would improve the economic outcomes of e-commerce growth (could address: gig worker benefits, small seller tax relief, warehouse worker safety, rural broadband access, etc.)

---

## Part D — Small Business Spotlight (10 pts)

Research one **small business** (under 50 employees) that successfully transitioned to or was born in e-commerce. Write 3 paragraphs covering:
1. What they sell and their e-commerce model
2. What platforms/tools they use and why
3. What economic impact have they had locally (jobs, tax revenue, community)

Find a real story from news sources, not a hypothetical.

---

## Submission Checklist

- [ ] `ecommerce_data.csv` — 10+ years of data with sources cited
- [ ] `ecommerce_analysis.py` — runs without error
- [ ] `ecommerce_impact_charts.png` — 4-panel chart screenshot
- [ ] `impact_report.md` — all 6 sections + small business spotlight

---

## Grading

| Component | Points |
|-----------|--------|
| Part A — Data collection (real data, sources cited) | 20 |
| Part B — Python analysis (CAGR, correlations, 4 charts) | 35 |
| Part C — Impact report (all 6 sections, data-supported) | 35 |
| Part D — Small business spotlight | 10 |
| **Total** | **100** |
