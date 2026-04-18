---
title: "Lab 08: Quality Metrics & Statistical Quality Control"
course: SCIA-425
topic: Statistical Quality Control and Metrics
week: 10
difficulty: ⭐⭐
estimated_time: 80 minutes
---

# Lab 08: Quality Metrics & Statistical Quality Control

| Field | Details |
|---|---|
| **Course** | SCIA-425 — Software Assurance and Quality |
| **Week** | 10 |
| **Difficulty** | ⭐⭐ Intermediate |
| **Estimated Time** | 80 minutes |
| **Topic** | Statistical Quality Control and Metrics |
| **Prerequisites** | Python 3.10+, `pip install radon matplotlib pandas scipy` |
| **Deliverables** | `metrics_report.py` output, `control_chart.png`, `metrics_analysis.md` |

---

## Overview

You can't improve what you can't measure. Software quality metrics give teams objective evidence about code health, defect trends, and process stability. In this lab you will compute industry-standard code metrics on a real open-source project, build a statistical process control (SPC) chart for defect density, and analyze what the data tells you about the project's quality trajectory.

---

## Setup

```bash
# Clone a real project for analysis (a small, well-known Python project)
git clone https://github.com/pallets/click.git target_project
pip install radon matplotlib pandas scipy
```

---

## Part A — Code Complexity Metrics (30 pts)

Use **Radon** to compute Cyclomatic Complexity and Halstead metrics:

```bash
# Cyclomatic Complexity — per function
radon cc target_project/src -s -a

# Maintainability Index
radon mi target_project/src -s

# Halstead metrics
radon hal target_project/src

# Save all to files
radon cc target_project/src -s -j > cc_metrics.json
radon mi target_project/src -s -j > mi_metrics.json
```

Write `metrics_report.py` to analyze and display the results:

```python
import json
import statistics

# ── Cyclomatic Complexity ──────────────────────────────────────────
with open("cc_metrics.json") as f:
    cc_data = json.load(f)

all_functions = []
for filepath, blocks in cc_data.items():
    for block in blocks:
        all_functions.append({
            "file": filepath,
            "name": block["name"],
            "complexity": block["complexity"],
            "rank": block["rank"]
        })

complexities = [f["complexity"] for f in all_functions]
print("=== Cyclomatic Complexity ===")
print(f"Total functions analyzed: {len(all_functions)}")
print(f"Average complexity: {statistics.mean(complexities):.2f}")
print(f"Median complexity: {statistics.median(complexities):.2f}")
print(f"Max complexity: {max(complexities)} (threshold: 10 = HIGH RISK)")
print(f"Standard deviation: {statistics.stdev(complexities):.2f}")

# Risk distribution
rank_counts = {}
for f in all_functions:
    rank_counts[f["rank"]] = rank_counts.get(f["rank"], 0) + 1
print("\nRisk Distribution:")
for rank in sorted(rank_counts):
    label = {"A":"Low","B":"Low","C":"Medium","D":"High","E":"Very High","F":"Extreme"}.get(rank,"?")
    print(f"  Rank {rank} ({label}): {rank_counts[rank]} functions")

# Top 10 most complex
print("\nTop 10 Most Complex Functions:")
for f in sorted(all_functions, key=lambda x: x["complexity"], reverse=True)[:10]:
    print(f"  CC={f['complexity']:3d} [{f['rank']}]  {f['name']}  ({f['file']})")

# ── Maintainability Index ──────────────────────────────────────────
with open("mi_metrics.json") as f:
    mi_data = json.load(f)

mi_scores = [v["mi"] for v in mi_data.values() if isinstance(v, dict) and "mi" in v]
print(f"\n=== Maintainability Index ===")
print(f"Average MI: {statistics.mean(mi_scores):.1f} (threshold: <65 = unmaintainable)")
low_mi = [k for k, v in mi_data.items() if isinstance(v, dict) and v.get("mi", 100) < 65]
print(f"Files below MI threshold: {len(low_mi)}")
for f in low_mi:
    print(f"  {f}: MI={mi_data[f]['mi']:.1f}")
```

Run and screenshot:
```bash
python metrics_report.py
```

**Answer in `metrics_analysis.md`:**
1. Is the project's average complexity acceptable? (threshold: ≤5 is good, ≤10 is tolerable, >10 needs refactoring)
2. Which functions are HIGH or EXTREME risk? Should they be refactored?
3. What is the maintainability outlook?

---

## Part B — Defect Density Simulation & Control Charts (40 pts)

Real defect density data requires a bug tracker, so we simulate a project's 12-sprint defect history using a dataset:

```python
# sprint_defects.py — simulated defect data for a 3-year-old project
import json

# Format: {sprint: {defects_found, kloc_changed, defect_density}}
# Defect density = defects per KLOC (thousand lines of code changed)
sprint_data = [
    {"sprint": 1,  "defects": 12, "kloc": 3.2, "density": 3.75},
    {"sprint": 2,  "defects": 8,  "kloc": 2.8, "density": 2.86},
    {"sprint": 3,  "defects": 15, "kloc": 4.1, "density": 3.66},
    {"sprint": 4,  "defects": 6,  "kloc": 2.1, "density": 2.86},
    {"sprint": 5,  "defects": 9,  "kloc": 3.0, "density": 3.00},
    {"sprint": 6,  "defects": 22, "kloc": 4.5, "density": 4.89},  # spike
    {"sprint": 7,  "defects": 11, "kloc": 3.3, "density": 3.33},
    {"sprint": 8,  "defects": 7,  "kloc": 2.5, "density": 2.80},
    {"sprint": 9,  "defects": 5,  "kloc": 2.2, "density": 2.27},
    {"sprint": 10, "defects": 4,  "kloc": 2.0, "density": 2.00},
    {"sprint": 11, "defects": 18, "kloc": 3.8, "density": 4.74},  # second spike
    {"sprint": 12, "defects": 6,  "kloc": 2.3, "density": 2.61},
]
```

Build a **Statistical Process Control (SPC) chart** in Python:

```python
import matplotlib.pyplot as plt
import numpy as np

densities = [d["density"] for d in sprint_data]
sprints = [d["sprint"] for d in sprint_data]

mean = np.mean(densities)
std = np.std(densities, ddof=1)

ucl = mean + 3 * std   # Upper Control Limit
lcl = max(0, mean - 3 * std)  # Lower Control Limit (floored at 0)

fig, ax = plt.subplots(figsize=(12, 6))

ax.plot(sprints, densities, 'o-', color='steelblue', linewidth=2, label='Defect Density')
ax.axhline(mean, color='green', linestyle='--', linewidth=1.5, label=f'Mean = {mean:.2f}')
ax.axhline(ucl, color='red', linestyle='--', linewidth=1.5, label=f'UCL = {ucl:.2f}')
ax.axhline(lcl, color='orange', linestyle='--', linewidth=1.5, label=f'LCL = {lcl:.2f}')

# Highlight out-of-control points
for i, (s, d) in enumerate(zip(sprints, densities)):
    if d > ucl or d < lcl:
        ax.plot(s, d, 'r*', markersize=15, label='Out of Control' if i == 0 else "")

ax.set_xlabel("Sprint Number")
ax.set_ylabel("Defect Density (defects/KLOC)")
ax.set_title("Defect Density Control Chart — SCIA-425 Lab 08")
ax.legend()
ax.grid(True, alpha=0.3)
ax.set_xticks(sprints)

plt.tight_layout()
plt.savefig("control_chart.png", dpi=150)
print(f"Control chart saved. Mean={mean:.2f}, UCL={ucl:.2f}, LCL={lcl:.2f}")
print(f"Out-of-control points: {[s for s,d in zip(sprints,densities) if d > ucl or d < lcl]}")
```

**Answer in `metrics_analysis.md`:**
1. Which sprints are out of statistical control? What might have caused the spikes?
2. Is the process "in control"? (A process is in control if all points are within UCL/LCL AND there are no runs of 8+ consecutive points on one side of the mean)
3. What quality action would you recommend based on the sprint 6 and 11 spikes?

---

## Part C — Halstead Complexity Deep Dive (15 pts)

Halstead metrics describe program complexity based on operator/operand counts:

```bash
radon hal target_project/src -j > halstead.json
```

Write a Python analysis of the Halstead data to compute and report:
- Total **Program Volume** (V = N × log₂(η)) for the project
- Average **Effort** (E = D × V)
- Estimated **Time to understand** the codebase in hours (T = E / 18)
- Estimated **Bug count** (B = V / 3000 — Halstead's formula)

Compare Halstead's bug count estimate against the actual defect history in Part B. Is Halstead's estimate reasonable?

---

## Part D — Additional Metric of Your Choice (15 pts)

Choose **one** of the following metrics, compute it manually or with a tool, and report on it:

**Option A — Code Churn:**
```bash
git -C target_project log --stat --since="6 months ago" | grep ".py" | \
  awk '{print $1, $3, $5}' | sort | head -20
```
Identify the top 5 most-churned files. High churn + high complexity = highest bug risk.

**Option B — Comment Density:**
```bash
radon raw target_project/src -j > raw_metrics.json
```
Calculate comment ratio (COMMENTS / LOC) per file. Files with very low comment density in high-complexity functions are a maintainability risk.

**Option C — Test Coverage Delta:**
Compare `pytest --cov` output for two versions of a project (if available). Compute coverage drift.

Report your chosen metric, methodology, and findings in `metrics_analysis.md`.

---

## Submission Checklist

- [ ] `metrics_report.py` — runs without error, output screenshot
- [ ] `control_chart.png` — SPC chart with UCL/LCL + highlighted OOC points
- [ ] `metrics_analysis.md` — answers to all analysis questions (Parts A–D)
- [ ] `cc_metrics.json`, `mi_metrics.json`, `halstead.json` — raw data files

---

## Grading

| Component | Points |
|-----------|--------|
| Part A — metrics_report.py (correct stats, top 10, MI analysis) | 30 |
| Part B — control_chart.png (correct UCL/LCL, OOC points highlighted, analysis) | 40 |
| Part C — Halstead analysis + bug estimate comparison | 15 |
| Part D — Additional metric (correct methodology + findings) | 15 |
| **Total** | **100** |
