---
title: "Lab 08: E-Supply Chain Mapping & Disruption Analysis"
course: ITEC-442
topic: E-Supply Chain Management
week: 8
difficulty: ⭐⭐
estimated_time: 75 minutes
---

# Lab 08: E-Supply Chain Mapping & Disruption Analysis

| Field | Details |
|---|---|
| **Course** | ITEC-442 — Electronic Commerce |
| **Week** | 8 |
| **Difficulty** | ⭐⭐ Intermediate |
| **Estimated Time** | 75 minutes |
| **Topic** | E-Supply Chain Management |
| **Prerequisites** | Python 3.10+, `pip install pandas matplotlib networkx` |
| **Deliverables** | `supply_chain_map.md`, `disruption_analysis.py`, supply chain diagram |

---

## Overview

Supply chain failures make headlines — COVID-19 chip shortages, Suez Canal blockage, port congestion — but the root causes are visible in how supply chains are designed. In this lab you will map a real company's e-commerce supply chain, model it as a network graph, identify single points of failure, calculate disruption costs, and propose resilience improvements.

---

## Part A — Select & Map a Real Supply Chain (25 pts)

Choose a **real company** that sells physical products online. Good choices: a consumer electronics brand (Apple, Samsung), an apparel retailer (Nike, Patagonia), or a food company (Chewy, HelloFresh).

Research and map their supply chain in `supply_chain_map.md`:

```markdown
# [Company] E-Commerce Supply Chain Map

## Overview
- Company:
- Product category:
- Annual e-commerce revenue:
- Countries of operation:

## Supply Chain Tiers

### Tier 3 — Raw Materials
| Supplier | Country | Material | % of supply | Alternative available? |
|----------|---------|----------|------------|----------------------|
| | | | | |

### Tier 2 — Component Manufacturing
| Manufacturer | Country | Component | Sole source? |
|-------------|---------|-----------|-------------|
| | | | |

### Tier 1 — Final Assembly / Production
| Facility | Country | Capacity | Lead time |
|----------|---------|----------|-----------|
| | | | |

### Distribution & Logistics
| Layer | Provider | Mode | Avg transit time | Cost % of COGS |
|-------|---------|------|-----------------|----------------|
| Port/Air freight | | Ocean/Air | | |
| Fulfillment center | | — | | |
| Last mile | | Ground/Express | | |

### Retail / Customer Delivery
| Channel | Split % | Avg delivery time |
|---------|---------|------------------|
| Own website | | |
| Marketplace (Amazon) | | |
| Retail stores | | |

## Key Numbers
- Inventory turnover ratio:
- Days of inventory on hand:
- % of products fulfilled in-house vs 3PL:
```

---

## Part B — Network Graph Visualization (20 pts)

Model the supply chain as a directed graph using NetworkX:

```python
# disruption_analysis.py
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# Build supply chain graph
# Nodes = supply chain entities, Edges = material/product flow
G = nx.DiGraph()

# Add nodes with attributes
nodes = {
    # Raw materials
    "Copper Mine (Chile)":       {"tier": 3, "country": "CL", "risk": "medium"},
    "Lithium Mine (Australia)":  {"tier": 3, "country": "AU", "risk": "low"},
    "Rare Earth (China)":        {"tier": 3, "country": "CN", "risk": "high"},

    # Component manufacturers
    "TSMC (Taiwan)":             {"tier": 2, "country": "TW", "risk": "critical"},
    "Samsung Display (Korea)":   {"tier": 2, "country": "KR", "risk": "medium"},
    "Foxconn Assembly (China)":  {"tier": 1, "country": "CN", "risk": "high"},

    # Logistics
    "Port of Shanghai":          {"tier": 0, "country": "CN", "risk": "high"},
    "Port of Long Beach":        {"tier": 0, "country": "US", "risk": "medium"},

    # Fulfillment
    "Apple Fulfillment (CA)":    {"tier": -1, "country": "US", "risk": "low"},
    "FedEx Last Mile":           {"tier": -1, "country": "US", "risk": "low"},

    # Customer
    "End Customer":              {"tier": -2, "country": "US", "risk": "none"},
}

for node, attrs in nodes.items():
    G.add_node(node, **attrs)

# Add edges (flow relationships)
edges = [
    ("Copper Mine (Chile)",      "Foxconn Assembly (China)",  {"flow": "copper"}),
    ("Lithium Mine (Australia)", "Foxconn Assembly (China)",  {"flow": "lithium"}),
    ("Rare Earth (China)",       "TSMC (Taiwan)",             {"flow": "rare earths"}),
    ("TSMC (Taiwan)",            "Foxconn Assembly (China)",  {"flow": "chips", "critical": True}),
    ("Samsung Display (Korea)",  "Foxconn Assembly (China)",  {"flow": "displays"}),
    ("Foxconn Assembly (China)", "Port of Shanghai",          {"flow": "finished goods"}),
    ("Port of Shanghai",         "Port of Long Beach",        {"flow": "containers", "transit_days": 16}),
    ("Port of Long Beach",       "Apple Fulfillment (CA)",    {"flow": "inventory"}),
    ("Apple Fulfillment (CA)",   "FedEx Last Mile",           {"flow": "orders"}),
    ("FedEx Last Mile",          "End Customer",              {"flow": "delivery"}),
]

for src, dst, attrs in edges:
    G.add_edge(src, dst, **attrs)

# Color by risk level
risk_colors = {"critical": "#c62828", "high": "#f57c00",
               "medium": "#fbc02d", "low": "#388e3c", "none": "#1565c0"}
node_colors = [risk_colors[G.nodes[n]["risk"]] for n in G.nodes()]

plt.figure(figsize=(16, 10))
pos = nx.spring_layout(G, seed=42, k=2)
nx.draw_networkx(G, pos, node_color=node_colors, node_size=2000,
                 font_size=7, arrows=True, arrowsize=20,
                 edge_color="#555", width=1.5, with_labels=True)

legend = [mpatches.Patch(color=c, label=r) for r, c in risk_colors.items()]
plt.legend(handles=legend, loc="upper left", title="Risk Level")
plt.title("E-Commerce Supply Chain Network — Risk Heat Map", fontsize=14)
plt.axis("off")
plt.tight_layout()
plt.savefig("supply_chain_map.png", dpi=150)
print("Supply chain map saved: supply_chain_map.png")
```

Run and save the visualization.

---

## Part C — Single Points of Failure Analysis (25 pts)

Add this analysis to `disruption_analysis.py`:

```python
# ── Single Points of Failure ─────────────────────────────────────
print("\n=== Single Points of Failure Analysis ===\n")

# Find nodes whose removal disconnects the graph
critical_nodes = []
for node in G.nodes():
    G_test = G.copy()
    G_test.remove_node(node)
    if not nx.is_weakly_connected(G_test):
        critical_nodes.append(node)

print("Critical nodes (removal disconnects supply chain):")
for node in critical_nodes:
    risk = G.nodes[node]["risk"]
    print(f"  ⚠ {node} [risk: {risk}]")

# Betweenness centrality — nodes most "in between" others
centrality = nx.betweenness_centrality(G)
print("\nTop 5 nodes by betweenness centrality (flow bottlenecks):")
for node, score in sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:5]:
    print(f"  {score:.3f} — {node}")

# ── Disruption Cost Model ─────────────────────────────────────────
print("\n=== Disruption Cost Calculator ===\n")

scenarios = [
    {
        "name": "TSMC Production Stop (Taiwan conflict)",
        "duration_days": 90,
        "affected_revenue_pct": 0.85,
        "daily_revenue": 137_000_000,  # Apple ~$50B/quarter / 90 days
        "mitigation_cost": 2_000_000_000,
        "probability_annual": 0.05
    },
    {
        "name": "Port of Long Beach Strike (30 days)",
        "duration_days": 30,
        "affected_revenue_pct": 0.40,
        "daily_revenue": 137_000_000,
        "mitigation_cost": 50_000_000,
        "probability_annual": 0.15
    },
    {
        "name": "Foxconn Factory Shutdown (COVID-style)",
        "duration_days": 45,
        "affected_revenue_pct": 0.60,
        "daily_revenue": 137_000_000,
        "mitigation_cost": 500_000_000,
        "probability_annual": 0.10
    }
]

for s in scenarios:
    direct_loss = s["duration_days"] * s["daily_revenue"] * s["affected_revenue_pct"]
    expected_annual_loss = direct_loss * s["probability_annual"]
    roi = (expected_annual_loss - s["mitigation_cost"]) / s["mitigation_cost"] * 100

    print(f"Scenario: {s['name']}")
    print(f"  Direct loss:              ${direct_loss/1e9:.2f}B")
    print(f"  Probability (annual):     {s['probability_annual']*100:.0f}%")
    print(f"  Expected annual loss:     ${expected_annual_loss/1e6:.0f}M")
    print(f"  Mitigation cost:          ${s['mitigation_cost']/1e6:.0f}M")
    print(f"  Mitigation ROI:           {roi:.0f}%")
    print(f"  Decision: {'INVEST in mitigation ✓' if roi > 0 else 'Accept risk ✗'}\n")
```

---

## Part D — Resilience Recommendations (20 pts)

In `supply_chain_map.md`, write a **Supply Chain Resilience Report** with:

**1. Top 3 Vulnerabilities**
From your network analysis, list the 3 highest-risk single points of failure with:
- Why this node is critical
- What a disruption would look like
- Historical precedent (has this happened before?)

**2. Resilience Strategies**
For each vulnerability, recommend a mitigation:

| Vulnerability | Strategy | Cost Level | Implementation Time | Risk Reduction |
|--------------|----------|-----------|--------------------|-|
| Single chip supplier | Dual-source from 2 fabs | Very High | 3–5 years | High |
| ... | | | | |

**3. Supply Chain Technology Improvements**
Name 3 technologies that could reduce supply chain risk (e.g., blockchain for provenance tracking, IoT for real-time inventory, AI demand forecasting) and explain how each helps.

**4. COVID-19 Lessons**
Write 3 paragraphs on what your chosen company did (or should have done) differently as a result of COVID-19 supply chain disruptions. Use real news sources.

---

## Part E — Inventory Optimization Model (10 pts)

Build a simple EOQ (Economic Order Quantity) calculator:

```python
import math

def eoq(demand_annual: float, order_cost: float, holding_cost_pct: float, unit_cost: float) -> dict:
    """
    EOQ = sqrt(2 * D * S / H)
    D = annual demand, S = order cost, H = holding cost per unit per year
    """
    H = holding_cost_pct * unit_cost
    eoq_qty = math.sqrt(2 * demand_annual * order_cost / H)
    orders_per_year = demand_annual / eoq_qty
    cycle_time_days = 365 / orders_per_year
    annual_order_cost = orders_per_year * order_cost
    annual_holding_cost = (eoq_qty / 2) * H
    total_cost = annual_order_cost + annual_holding_cost

    return {
        "EOQ": round(eoq_qty),
        "Orders per year": round(orders_per_year, 1),
        "Cycle time (days)": round(cycle_time_days, 1),
        "Annual order cost": round(annual_order_cost, 2),
        "Annual holding cost": round(annual_holding_cost, 2),
        "Total annual cost": round(total_cost, 2)
    }

print("=== EOQ Calculator ===\n")
products = [
    ("Safety Gloves", 5000, 85, 0.25, 9.00),
    ("Hard Hats",     2000, 95, 0.20, 18.00),
    ("Safety Vests",  3500, 75, 0.30, 12.00),
]
for name, D, S, h, c in products:
    result = eoq(D, S, h, c)
    print(f"{name}:")
    for k, v in result.items():
        print(f"  {k}: {v}")
    print()
```

---

## Submission Checklist

- [ ] `supply_chain_map.md` — Parts A, D complete
- [ ] `disruption_analysis.py` — runs, all sections output
- [ ] `supply_chain_map.png` — network graph visualization

---

## Grading

| Component | Points |
|-----------|--------|
| Part A — Supply chain map (all tiers, real data) | 25 |
| Part B — Network graph (nodes, edges, risk coloring) | 20 |
| Part C — SPOF analysis + disruption cost model | 25 |
| Part D — Resilience report (vulnerabilities, strategies, COVID) | 20 |
| Part E — EOQ calculator | 10 |
| **Total** | **100** |
