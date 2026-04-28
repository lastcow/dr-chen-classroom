---
title: "Lab 13: Capstone — Build a Mini E-Commerce System"
course: ITEC-442
topic: E-Commerce System Design & Implementation
week: 15
difficulty: ⭐⭐⭐⭐
estimated_time: 150 minutes
---

# Lab 13: Capstone — Build a Mini E-Commerce System

| Field | Details |
|---|---|
| **Course** | ITEC-442 — Electronic Commerce |
| **Week** | 15 |
| **Difficulty** | ⭐⭐⭐⭐ Expert |
| **Estimated Time** | 150 minutes |
| **Topic** | E-Commerce System Design & Implementation |
| **Prerequisites** | All Labs 01–12, Python 3.10+, `pip install flask stripe sqlite3`, free Stripe account |
| **Deliverables** | Working e-commerce app, `system_design.md`, automated test suite, screenshot of live checkout |

---

## Overview

The capstone integrates every topic from ITEC-442 into a working mini e-commerce system — product catalog, shopping cart, Stripe checkout, basic analytics, and security hardening. This is not a toy: you will implement JWT authentication, a real database schema, Stripe Payment Intents, webhook confirmation, and Core Web Vitals-aware frontend. By the end you will have a deployable e-commerce application that demonstrates mastery of the full course.

---

## System Requirements

Build **FrostBuy** — a minimal e-commerce store for Frostburg-branded merchandise.

### Minimum Feature Set

| Feature | Week Topic | Implementation |
|---------|-----------|---------------|
| Product catalog (5+ products) | Wk 1–2 | SQLite + REST API |
| Shopping cart (session-based) | Wk 6 | Server-side sessions |
| Stripe checkout | Wk 9 | Payment Intents API |
| Order confirmation + webhook | Wk 9 | Stripe webhook |
| Security headers | Wk 10 | Flask-Talisman or manual |
| Basic analytics event tracking | Wk 5 | Custom event log |
| Trust signals on product pages | Wk 10 | Template design |
| Mobile-responsive UI | Wk 6, 14 | CSS only |

---

## Part A — Database Schema (15 pts)

```python
# database.py
import sqlite3
from datetime import datetime

DB_FILE = "frostbuy.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    description TEXT,
    price_cents INTEGER NOT NULL CHECK(price_cents > 0),
    category    TEXT,
    image_url   TEXT,
    stock       INTEGER DEFAULT 100,
    active      BOOLEAN DEFAULT 1,
    created_at  TEXT    DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS orders (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    stripe_payment_id  TEXT    UNIQUE,
    customer_email     TEXT,
    total_cents        INTEGER NOT NULL,
    status             TEXT    DEFAULT 'pending',
    created_at         TEXT    DEFAULT (datetime('now')),
    fulfilled_at       TEXT
);

CREATE TABLE IF NOT EXISTS order_items (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id   INTEGER NOT NULL REFERENCES orders(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    qty        INTEGER NOT NULL,
    price_cents INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS analytics_events (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    event      TEXT NOT NULL,
    product_id INTEGER,
    session_id TEXT,
    value_cents INTEGER,
    created_at TEXT DEFAULT (datetime('now'))
);
"""

SEED = """
INSERT OR IGNORE INTO products (name, description, price_cents, category, image_url) VALUES
    ('FSU Bobcat Mug',      'Ceramic 15oz mug with FSU logo',          1499, 'drinkware',  '/static/mug.jpg'),
    ('FSU Hoodie',          'Pullover hoodie — FSU Navy Blue',          3999, 'apparel',    '/static/hoodie.jpg'),
    ('FSU Laptop Sticker',  'Vinyl die-cut sticker, weatherproof',       499, 'accessories','/static/sticker.jpg'),
    ('FSU Baseball Cap',    'Adjustable cap, embroidered logo',         2499, 'apparel',    '/static/cap.jpg'),
    ('FSU Water Bottle',    'Insulated 24oz stainless steel bottle',    2999, 'drinkware',  '/static/bottle.jpg'),
    ('FSU Pennant',         'Felt pennant, 12x30 inches',               1299, 'decor',      '/static/pennant.jpg');
"""

def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.executescript(SCHEMA + SEED)
    conn.commit()
    conn.close()
    print("Database initialized.")

if __name__ == "__main__":
    init_db()
```

Run:
```bash
python database.py
```

---

## Part B — Flask Application (40 pts)

```python
# app.py
import os
import json
import uuid
import sqlite3
import stripe
from flask import (Flask, render_template_string, request, jsonify,
                   session, redirect, url_for, g)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-in-prod")

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
WEBHOOK_SECRET  = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

DB_FILE = "frostbuy.db"

# ── Security headers ──────────────────────────────────────────────
@app.after_request
def add_security_headers(resp):
    resp.headers["X-Frame-Options"]        = "DENY"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"]        = "strict-origin-when-cross-origin"
    resp.headers["Permissions-Policy"]     = "geolocation=(), microphone=()"
    return resp

# ── DB helper ─────────────────────────────────────────────────────
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_FILE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop("db", None)
    if db: db.close()

def log_event(event: str, product_id=None, value_cents=None):
    db = get_db()
    db.execute(
        "INSERT INTO analytics_events (event, product_id, session_id, value_cents) VALUES (?,?,?,?)",
        (event, product_id, session.get("sid", "anonymous"), value_cents)
    )
    db.commit()

# ── Pages ─────────────────────────────────────────────────────────
CATALOG_HTML = """
<!DOCTYPE html><html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FrostBuy — FSU Merchandise</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: system-ui, sans-serif; background: #f5f5f5; }
  header { background: #0f3460; color: white; padding: 16px 24px;
           display: flex; justify-content: space-between; align-items: center; }
  header h1 { font-size: 1.4rem; }
  .cart-badge { background: #c8a951; color: #0f3460; border-radius: 50%;
                padding: 2px 8px; font-weight: bold; margin-left: 8px; }
  .products { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
              gap: 20px; padding: 24px; max-width: 1100px; margin: 0 auto; }
  .card { background: white; border-radius: 8px; overflow: hidden;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
  .card-body { padding: 16px; }
  .card h3 { font-size: 1rem; margin-bottom: 8px; }
  .price { font-size: 1.2rem; font-weight: bold; color: #0f3460; margin: 8px 0; }
  .trust { font-size: 0.75rem; color: #666; margin-top: 4px; }
  .btn { background: #0f3460; color: white; border: none; padding: 10px 16px;
         border-radius: 4px; cursor: pointer; width: 100%; margin-top: 10px;
         font-size: 0.95rem; }
  .btn:hover { background: #1a4a7a; }
  .badge { background: #e8f5e9; color: #2e7d32; font-size: 0.7rem;
           padding: 2px 6px; border-radius: 3px; }
</style>
</head>
<body>
<header>
  <h1>🐱 FrostBuy — FSU Merchandise</h1>
  <a href="/cart" style="color:white;text-decoration:none;">
    🛒 Cart <span class="cart-badge">{{ cart_count }}</span>
  </a>
</header>
<div class="products">
{% for p in products %}
<div class="card">
  <div style="background:#e0e0e0;height:150px;display:flex;align-items:center;
              justify-content:center;color:#999;font-size:2rem;">🎓</div>
  <div class="card-body">
    <h3>{{ p['name'] }}</h3>
    <p style="font-size:0.85rem;color:#555;">{{ p['description'] }}</p>
    <div class="price">${{ "%.2f" | format(p['price_cents'] / 100) }}</div>
    <div class="trust">⭐⭐⭐⭐⭐ &nbsp; Free shipping over $35 &nbsp; <span class="badge">In Stock</span></div>
    <form method="POST" action="/cart/add">
      <input type="hidden" name="product_id" value="{{ p['id'] }}">
      <button class="btn" type="submit">Add to Cart</button>
    </form>
  </div>
</div>
{% endfor %}
</div>
</body></html>
"""

CART_HTML = """
<!DOCTYPE html><html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>FrostBuy — Cart</title>
<style>
  body{font-family:system-ui,sans-serif;max-width:600px;margin:40px auto;padding:20px}
  h2{color:#0f3460;margin-bottom:20px}
  .item{display:flex;justify-content:space-between;padding:12px 0;border-bottom:1px solid #eee}
  .total{font-size:1.3rem;font-weight:bold;margin:20px 0;color:#0f3460}
  .btn{background:#0f3460;color:white;border:none;padding:12px 24px;border-radius:4px;
       cursor:pointer;font-size:1rem;width:100%}
  .empty{text-align:center;color:#888;padding:40px}
  input[type=email]{width:100%;padding:10px;border:1px solid #ddd;border-radius:4px;
                    margin:10px 0;font-size:1rem}
  #card-element{border:1px solid #ddd;padding:12px;border-radius:4px;margin:10px 0}
  #msg{padding:10px;border-radius:4px;margin-top:10px}
  .success{background:#e8f5e9;color:#2e7d32}
  .error{background:#ffebee;color:#c62828}
</style>
<script src="https://js.stripe.com/v3/"></script>
</head>
<body>
<a href="/" style="color:#0f3460">← Continue Shopping</a>
<h2>Your Cart</h2>
{% if items %}
{% for item in items %}
<div class="item">
  <span>{{ item.name }} × {{ item.qty }}</span>
  <span>${{ "%.2f" | format(item.price_cents * item.qty / 100) }}</span>
</div>
{% endfor %}
<div class="total">Total: ${{ "%.2f" | format(total / 100) }}</div>
<label>Email for order confirmation:</label>
<input type="email" id="email" placeholder="your@email.com">
<div id="card-element"></div>
<button class="btn" id="pay-btn">Pay ${{ "%.2f" | format(total / 100) }}</button>
<div id="msg"></div>
<p style="font-size:12px;color:#888;margin-top:15px">
  Test: 4242 4242 4242 4242 | Any future date | Any CVC
</p>
<script>
const stripe = Stripe("{{ publishable_key }}");
const elements = stripe.elements();
const card = elements.create("card");
card.mount("#card-element");
document.getElementById("pay-btn").addEventListener("click", async () => {
  const email = document.getElementById("email").value;
  if (!email) { showMsg("Please enter your email", "error"); return; }
  document.getElementById("pay-btn").disabled = true;
  document.getElementById("pay-btn").textContent = "Processing...";
  const r = await fetch("/create-payment-intent", {
    method:"POST", headers:{"Content-Type":"application/json"},
    body: JSON.stringify({email})
  });
  const {clientSecret, error: se} = await r.json();
  if (se) { showMsg(se, "error"); resetBtn(); return; }
  const {paymentIntent, error} = await stripe.confirmCardPayment(clientSecret,
    {payment_method:{card, billing_details:{email}}});
  if (error) { showMsg(error.message, "error"); resetBtn(); }
  else if (paymentIntent.status === "succeeded") {
    showMsg("✓ Order placed! Check your email for confirmation.", "success");
    document.getElementById("pay-btn").textContent = "Order Complete";
  }
});
function showMsg(msg, cls) {
  const el = document.getElementById("msg");
  el.textContent = msg; el.className = cls;
}
function resetBtn() {
  const b = document.getElementById("pay-btn");
  b.disabled = false; b.textContent = "Pay ${{ '%.2f' | format(total / 100) }}";
}
</script>
{% else %}
<div class="empty">Your cart is empty. <a href="/">Start shopping →</a></div>
{% endif %}
</body></html>
"""

@app.route("/")
def catalog():
    if "sid" not in session:
        session["sid"] = str(uuid.uuid4())
    db = get_db()
    products = db.execute("SELECT * FROM products WHERE active=1 ORDER BY category, name").fetchall()
    cart_count = sum(session.get("cart", {}).values())
    log_event("page_view")
    return render_template_string(CATALOG_HTML, products=products, cart_count=cart_count)

@app.route("/cart/add", methods=["POST"])
def add_to_cart():
    product_id = request.form.get("product_id")
    cart = session.get("cart", {})
    cart[product_id] = cart.get(product_id, 0) + 1
    session["cart"] = cart
    log_event("add_to_cart", product_id=int(product_id))
    return redirect(url_for("catalog"))

@app.route("/cart")
def view_cart():
    cart = session.get("cart", {})
    db = get_db()
    items = []
    total = 0
    for pid, qty in cart.items():
        product = db.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
        if product:
            items.append({"name": product["name"], "qty": qty,
                          "price_cents": product["price_cents"]})
            total += product["price_cents"] * qty
    log_event("view_cart", value_cents=total)
    return render_template_string(CART_HTML, items=items, total=total,
                                  publishable_key=PUBLISHABLE_KEY)

@app.route("/create-payment-intent", methods=["POST"])
def create_pi():
    data = request.get_json()
    cart = session.get("cart", {})
    db = get_db()
    total = 0
    for pid, qty in cart.items():
        p = db.execute("SELECT price_cents FROM products WHERE id=?", (pid,)).fetchone()
        if p: total += p["price_cents"] * qty
    if total <= 0:
        return jsonify({"error": "Empty cart"}), 400
    intent = stripe.PaymentIntent.create(
        amount=total, currency="usd",
        receipt_email=data.get("email"),
        metadata={"session_id": session.get("sid"), "source": "frostbuy-lab13"}
    )
    # Pre-create order record
    db.execute("INSERT INTO orders (stripe_payment_id, customer_email, total_cents) VALUES (?,?,?)",
               (intent.id, data.get("email"), total))
    db.commit()
    log_event("checkout_start", value_cents=total)
    return jsonify({"clientSecret": intent.client_secret})

@app.route("/webhook", methods=["POST"])
def webhook():
    payload   = request.get_data(as_text=True)
    sig       = request.headers.get("Stripe-Signature", "")
    try:
        event = stripe.Webhook.construct_event(payload, sig, WEBHOOK_SECRET) \
                if WEBHOOK_SECRET else \
                stripe.Event.construct_from(json.loads(payload), stripe.api_key)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    if event["type"] == "payment_intent.succeeded":
        pi = event["data"]["object"]
        db = get_db()
        db.execute("UPDATE orders SET status='paid', fulfilled_at=? WHERE stripe_payment_id=?",
                   (datetime.now().isoformat(), pi["id"]))
        db.commit()
        print(f"[WEBHOOK] Order fulfilled: {pi['id']} — ${pi['amount']/100:.2f}")
    return jsonify({"received": True}), 200

@app.route("/admin/analytics")
def analytics():
    db = get_db()
    events = db.execute("""
        SELECT event, COUNT(*) AS count, SUM(value_cents)/100.0 AS revenue
        FROM analytics_events GROUP BY event ORDER BY count DESC
    """).fetchall()
    orders = db.execute("SELECT COUNT(*), SUM(total_cents)/100.0 FROM orders WHERE status='paid'").fetchone()
    result = {
        "total_orders": orders[0],
        "total_revenue": f"${orders[1] or 0:.2f}",
        "events": [dict(e) for e in events]
    }
    return jsonify(result)

if __name__ == "__main__":
    from database import init_db
    init_db()
    print("FrostBuy running at http://localhost:5000")
    print("Admin analytics: http://localhost:5000/admin/analytics")
    app.run(debug=True, port=5000)
```

Run the full application:
```bash
export STRIPE_SECRET_KEY="sk_test_..."
export STRIPE_PUBLISHABLE_KEY="pk_test_..."
python app.py
```

Complete a full test purchase cycle and screenshot each step.

---

## Part C — Automated Test Suite (20 pts)

```python
# test_frostbuy.py
import pytest
import json
from app import app, get_db
from database import init_db

@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret"
    with app.test_client() as client:
        with app.app_context():
            init_db()
            yield client

def test_catalog_loads(client):
    r = client.get("/")
    assert r.status_code == 200
    assert b"FrostBuy" in r.data

def test_catalog_has_products(client):
    r = client.get("/")
    assert b"FSU" in r.data

def test_add_to_cart(client):
    r = client.post("/cart/add", data={"product_id": "1"}, follow_redirects=True)
    assert r.status_code == 200

def test_cart_shows_items(client):
    client.post("/cart/add", data={"product_id": "1"})
    r = client.get("/cart")
    assert r.status_code == 200
    assert b"Total" in r.data

def test_security_headers(client):
    r = client.get("/")
    assert "X-Frame-Options" in r.headers
    assert r.headers["X-Frame-Options"] == "DENY"
    assert "X-Content-Type-Options" in r.headers

def test_empty_cart_shows_message(client):
    r = client.get("/cart")
    assert b"empty" in r.data.lower() or b"shopping" in r.data.lower()

def test_analytics_endpoint(client):
    client.get("/")
    r = client.get("/admin/analytics")
    assert r.status_code == 200
    data = json.loads(r.data)
    assert "total_orders" in data
    assert "events" in data
```

Run:
```bash
pytest test_frostbuy.py -v
```

All tests must pass. Screenshot the pytest output.

---

## Part D — System Design Document (15 pts)

Write `system_design.md`:

1. **Architecture Diagram** — ASCII diagram showing browser → Flask → SQLite + Stripe
2. **Technology Stack** — justify each choice (Flask vs Django, SQLite vs PostgreSQL, etc.)
3. **Course Integration** — one sentence per lab (01–12) explaining which concept appears in this capstone
4. **Production Gap Analysis** — 5 things this capstone is missing for real production use and what you'd add
5. **Scaling Plan** — how would you scale FrostBuy to 100,000 daily orders?

---

## Part E — Bonus Features (up to +20 pts)

Implement one or more of:

| Bonus | Points | Description |
|-------|--------|-------------|
| Product search | +5 | Search bar that filters products by name/category |
| Order history page | +5 | `/orders?email=x` shows past orders |
| Inventory management | +5 | Decrement stock on purchase, show "Low stock" |
| Email confirmation | +5 | Send order confirmation email via Mailgun free tier |
| Coupon codes | +5 | `FROSTBURG10` gives 10% off |
| Admin dashboard | +10 | `/admin` page showing orders, revenue charts, top products |

---

## Submission Checklist

- [ ] `database.py` — runs, creates DB with seed data
- [ ] `app.py` — full application runs on localhost:5000
- [ ] Screenshots: catalog, product, cart, checkout, order success, Stripe dashboard
- [ ] `test_frostbuy.py` — all tests pass (screenshot)
- [ ] `system_design.md` — all 5 sections complete
- [ ] Bonus feature (optional)

---

## Grading

| Component | Points |
|-----------|--------|
| Part B — Working application (catalog, cart, Stripe checkout, webhook, analytics) | 50 |
| Part C — Test suite (all 7 tests pass) | 20 |
| Part D — System design document (all 5 sections) | 15 |
| Screenshots (full purchase cycle documented) | 15 |
| Bonus features | +up to 20 |
| **Total** | **100 (+20 bonus)** |

---

!!! success "Congratulations — ITEC-442 Complete!"
    You have built, analyzed, and deployed every major component of a modern e-commerce system: business models, marketplace economics, consumer psychology, analytics, UX, B2B systems, supply chains, payments, security, portals, and government services. These skills span product management, business strategy, and full-stack engineering — the foundation of a career in digital commerce.
