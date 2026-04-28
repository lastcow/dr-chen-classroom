---
title: "Lab 07: B2B E-Commerce System Design"
course: ITEC-442
topic: B2B E-Commerce & Company-Centric Models
week: 7
difficulty: ⭐⭐⭐
estimated_time: 85 minutes
---

# Lab 07: B2B E-Commerce System Design

| Field | Details |
|---|---|
| **Course** | ITEC-442 — Electronic Commerce |
| **Week** | 7 |
| **Difficulty** | ⭐⭐⭐ Advanced |
| **Estimated Time** | 85 minutes |
| **Topic** | B2B E-Commerce & Company-Centric Models |
| **Prerequisites** | Python 3.10+, `pip install pandas` |
| **Deliverables** | `b2b_design.md`, `rfq_system.py`, `pricing_engine.py` |

---

## Overview

B2B e-commerce ($7.9T globally) dwarfs B2C ($4.9T) yet receives far less attention in courses. B2B transactions are more complex — multi-step approval workflows, negotiated pricing, EDI integration, and long sales cycles. In this lab you will design a B2B portal for a wholesale distributor, model the RFQ (Request for Quotation) workflow, build a tiered pricing engine, and compare EDI vs API integration.

---

## Part A — B2B vs B2C Comparison (10 pts)

Fill in `b2b_design.md` with a detailed comparison:

| Dimension | B2C | B2B |
|-----------|-----|-----|
| Buyer identity | Anonymous consumer | Known business entity |
| Decision maker | Individual | Buying committee (avg 6.8 people) |
| Purchase frequency | One-time to occasional | Recurring, contract-based |
| Order size | Small ($50–$200 avg) | Large ($5,000–$500,000+) |
| Pricing | Fixed, public | Negotiated, tiered, contract |
| Payment terms | Immediate (card) | Net 30/60/90, purchase orders |
| Sales cycle | Minutes to hours | Weeks to months |
| Relationship | Transactional | Long-term partnership |
| Catalog size | Curated (thousands) | Exhaustive (millions of SKUs) |
| Integration needs | None typically | ERP, procurement, EDI |

Then write 2 paragraphs explaining why B2B e-commerce has been slower to digitize than B2C, and what is driving the acceleration now.

---

## Part B — B2B Portal Design (25 pts)

Design a B2B e-commerce portal for **Frostburg Industrial Supply** — a wholesale distributor of safety equipment (hard hats, gloves, protective eyewear) serving construction companies, factories, and municipalities.

Document in `b2b_design.md`:

**1. User Types & Roles**
| Role | Permissions | Typical Actions |
|------|-------------|----------------|
| Purchasing Manager | Full order rights, view contracts | Browse catalog, place orders, approve RFQs |
| Requester | Can add to cart, cannot checkout | Submit purchase requests for manager approval |
| Finance | View invoices only | Download invoices, track payment status |
| Admin | Full access | Manage users, set approval limits |

**2. Catalog Design**
- How should the catalog handle 50,000+ SKUs?
- What filters are essential for safety equipment buyers?
- How should pricing be displayed (list price vs contract price)?
- What product information is critical for B2B safety equipment purchases?

**3. Account & Contract Structure**
- How do customer accounts differ from B2C accounts?
- How should contract pricing be stored and applied?
- What is the approval workflow for a new account?

**4. Order Management Features**
List and describe 8 features that a B2B order management system needs that a B2C system does not:
1. Purchase order number field
2. ...

---

## Part C — RFQ Workflow System (30 pts)

Model the Request for Quotation process in Python:

```python
# rfq_system.py
from datetime import datetime, timedelta
from enum import Enum

class RFQStatus(Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    QUOTED = "quoted"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"

class RFQItem:
    def __init__(self, sku: str, description: str, qty: int, unit: str, target_price: float = None):
        self.sku = sku
        self.description = description
        self.qty = qty
        self.unit = unit
        self.target_price = target_price
        self.quoted_price = None
        self.quoted_lead_days = None

class RFQ:
    def __init__(self, rfq_id: str, customer_id: str, customer_name: str):
        self.rfq_id = rfq_id
        self.customer_id = customer_id
        self.customer_name = customer_name
        self.items: list[RFQItem] = []
        self.status = RFQStatus.DRAFT
        self.created_at = datetime.now()
        self.valid_until = None
        self.notes = ""
        self.history = []

    def add_item(self, item: RFQItem):
        self.items.append(item)
        self._log(f"Item added: {item.sku} x{item.qty}")

    def submit(self):
        if not self.items:
            raise ValueError("Cannot submit RFQ with no items")
        self.status = RFQStatus.SUBMITTED
        self._log("RFQ submitted by customer")
        print(f"[RFQ {self.rfq_id}] Submitted — {len(self.items)} items")

    def start_review(self, rep_name: str):
        self.status = RFQStatus.UNDER_REVIEW
        self._log(f"Review started by {rep_name}")

    def apply_quote(self, item_sku: str, price: float, lead_days: int):
        for item in self.items:
            if item.sku == item_sku:
                item.quoted_price = price
                item.quoted_lead_days = lead_days
                self._log(f"Quoted {item_sku}: ${price:.2f}/unit, {lead_days} days lead")
                return
        raise ValueError(f"SKU {item_sku} not found in RFQ")

    def finalize_quote(self, valid_days: int = 30):
        unquoted = [i.sku for i in self.items if i.quoted_price is None]
        if unquoted:
            raise ValueError(f"Items not yet quoted: {unquoted}")
        self.status = RFQStatus.QUOTED
        self.valid_until = datetime.now() + timedelta(days=valid_days)
        self._log(f"Quote finalized, valid until {self.valid_until.date()}")

    def accept(self):
        if self.status != RFQStatus.QUOTED:
            raise ValueError("Can only accept a quoted RFQ")
        if datetime.now() > self.valid_until:
            self.status = RFQStatus.EXPIRED
            raise ValueError("Quote has expired")
        self.status = RFQStatus.ACCEPTED
        self._log("Quote accepted by customer")

    def total_quoted_value(self) -> float:
        return sum(i.qty * (i.quoted_price or 0) for i in self.items)

    def summary(self):
        print(f"\n{'='*50}")
        print(f"RFQ {self.rfq_id} | {self.customer_name} | Status: {self.status.value.upper()}")
        print(f"{'='*50}")
        print(f"{'SKU':<12} {'Description':<25} {'Qty':>6} {'Target':>10} {'Quoted':>10} {'Lead':>6}")
        print("-" * 75)
        for item in self.items:
            target = f"${item.target_price:.2f}" if item.target_price else "—"
            quoted = f"${item.quoted_price:.2f}" if item.quoted_price else "—"
            lead   = f"{item.quoted_lead_days}d" if item.quoted_lead_days else "—"
            print(f"{item.sku:<12} {item.description:<25} {item.qty:>6} {target:>10} {quoted:>10} {lead:>6}")
        if self.status == RFQStatus.QUOTED:
            print(f"\nTotal Quote Value: ${self.total_quoted_value():,.2f}")
            print(f"Valid Until: {self.valid_until.date()}")
        print()

    def _log(self, msg: str):
        self.history.append({"time": datetime.now().isoformat(), "event": msg})


# ── Demo: Full RFQ lifecycle ──────────────────────────────────────
rfq = RFQ("RFQ-2024-0891", "CUST-4421", "Frostburg Construction LLC")

rfq.add_item(RFQItem("HH-ANSI-RED",  "Red Hard Hat ANSI Z89.1",    50,  "ea", target_price=18.00))
rfq.add_item(RFQItem("GL-CUT5-LG",   "Cut-5 Gloves Large",         200, "pr", target_price=8.50))
rfq.add_item(RFQItem("EY-ANTI-FOG",  "Anti-fog Safety Glasses",    150, "ea", target_price=4.25))
rfq.add_item(RFQItem("VE-CLASS2-YEL","Class II Safety Vest Yellow", 75,  "ea", target_price=12.00))

rfq.submit()
rfq.start_review("Sarah Chen, Sales Rep")

# Apply quotes (with volume discounts)
rfq.apply_quote("HH-ANSI-RED",  16.50, 5)   # 8% below target
rfq.apply_quote("GL-CUT5-LG",   8.75,  3)   # slight above target
rfq.apply_quote("EY-ANTI-FOG",  3.95,  2)   # 7% below target
rfq.apply_quote("VE-CLASS2-YEL",11.50, 4)   # 4% below target

rfq.finalize_quote(valid_days=30)
rfq.summary()

rfq.accept()
print(f"RFQ {rfq.rfq_id} accepted! Generating purchase order...")
print(f"Final Order Value: ${rfq.total_quoted_value():,.2f}")
```

Run and add 2 more RFQ scenarios in your script (different customers, quantities, outcomes).

---

## Part D — Tiered Pricing Engine (25 pts)

B2B pricing is negotiated and tiered. Build a pricing engine in `pricing_engine.py`:

```python
# pricing_engine.py

class PricingEngine:
    def __init__(self):
        self.price_lists = {}     # {customer_tier: {sku: base_price}}
        self.volume_breaks = {}   # {sku: [(min_qty, discount_pct)]}
        self.contract_prices = {} # {customer_id: {sku: contract_price}}

    def set_list_price(self, sku: str, price: float, tier: str = "standard"):
        if tier not in self.price_lists:
            self.price_lists[tier] = {}
        self.price_lists[tier][sku] = price

    def set_volume_breaks(self, sku: str, breaks: list):
        """breaks: [(min_qty, discount_pct), ...] sorted ascending"""
        self.volume_breaks[sku] = sorted(breaks, key=lambda x: x[0])

    def set_contract_price(self, customer_id: str, sku: str, price: float):
        if customer_id not in self.contract_prices:
            self.contract_prices[customer_id] = {}
        self.contract_prices[customer_id][sku] = price

    def get_price(self, customer_id: str, sku: str, qty: int,
                  customer_tier: str = "standard") -> dict:
        # Priority: contract > volume break > tier list > standard list
        result = {"sku": sku, "qty": qty, "price_type": None, "unit_price": None, "total": None}

        # 1. Contract price (highest priority)
        if customer_id in self.contract_prices and sku in self.contract_prices[customer_id]:
            base = self.contract_prices[customer_id][sku]
            result.update({"price_type": "contract", "unit_price": base})

        # 2. Tier list price
        elif customer_tier in self.price_lists and sku in self.price_lists[customer_tier]:
            base = self.price_lists[customer_tier][sku]
            result.update({"price_type": f"tier:{customer_tier}", "unit_price": base})

        # 3. Standard list price
        elif "standard" in self.price_lists and sku in self.price_lists["standard"]:
            base = self.price_lists["standard"][sku]
            result.update({"price_type": "list", "unit_price": base})
        else:
            raise ValueError(f"No price found for SKU {sku}")

        # Apply volume discount on top
        if sku in self.volume_breaks and result["price_type"] != "contract":
            discount = 0
            for min_qty, disc_pct in self.volume_breaks[sku]:
                if qty >= min_qty:
                    discount = disc_pct
            if discount > 0:
                result["unit_price"] *= (1 - discount)
                result["price_type"] += f"+vol{int(discount*100)}%"

        result["total"] = round(result["unit_price"] * qty, 2)
        result["unit_price"] = round(result["unit_price"], 4)
        return result


# ── Setup & Demo ──────────────────────────────────────────────────
engine = PricingEngine()

# List prices (all tiers)
for sku, price in [("HH-ANSI-RED",18.00),("GL-CUT5-LG",9.00),("EY-ANTI-FOG",4.50),("VE-CLASS2-YEL",13.00)]:
    engine.set_list_price(sku, price, "standard")
    engine.set_list_price(sku, price * 0.90, "gold")      # gold: 10% off list
    engine.set_list_price(sku, price * 0.85, "platinum")  # platinum: 15% off list

# Volume breaks
engine.set_volume_breaks("HH-ANSI-RED",  [(25,0.05),(100,0.10),(500,0.15)])
engine.set_volume_breaks("GL-CUT5-LG",   [(50,0.05),(200,0.10),(1000,0.15)])

# Contract price for VIP customer
engine.set_contract_price("CUST-4421", "HH-ANSI-RED", 15.00)

print("=== Pricing Engine Demo ===\n")
scenarios = [
    ("CUST-0001", "HH-ANSI-RED", 10,  "standard"),
    ("CUST-0001", "HH-ANSI-RED", 150, "standard"),
    ("CUST-0002", "HH-ANSI-RED", 150, "gold"),
    ("CUST-4421", "HH-ANSI-RED", 150, "platinum"),  # contract overrides
    ("CUST-0003", "GL-CUT5-LG",  300, "gold"),
]
for cust, sku, qty, tier in scenarios:
    p = engine.get_price(cust, sku, qty, tier)
    print(f"  {cust} | {sku} | qty={qty:4d} | tier={tier:<8} | "
          f"${p['unit_price']:.4f}/ea | ${p['total']:,.2f} | [{p['price_type']}]")
```

---

## Part E — EDI vs API Comparison (10 pts)

Write a 400-word comparison in `b2b_design.md`:

1. **EDI (Electronic Data Interchange)**: How it works, common transaction sets (EDI 850=PO, 855=PO Acknowledgment, 856=ASN, 810=Invoice), who uses it, cost and complexity
2. **API integration**: REST/JSON, webhooks, real-time vs batch, developer experience
3. **When to choose each**: Legacy enterprise (EDI) vs modern tech company (API) vs hybrid
4. **Migration path**: How would Frostburg Industrial Supply migrate from EDI to API without breaking existing customer integrations?

---

## Submission Checklist

- [ ] `b2b_design.md` — Parts A, B, E complete
- [ ] `rfq_system.py` — runs with 3 scenarios
- [ ] `pricing_engine.py` — runs, all pricing logic demonstrated

---

## Grading

| Component | Points |
|-----------|--------|
| Part A — B2B vs B2C comparison (table + 2 paragraphs) | 10 |
| Part B — B2B portal design (4 sections, specific and detailed) | 25 |
| Part C — RFQ system (full lifecycle, 3 scenarios) | 30 |
| Part D — Pricing engine (all priority levels, volume breaks) | 25 |
| Part E — EDI vs API comparison (400 words, migration path) | 10 |
| **Total** | **100** |
