---
title: "Lab 09: Payment Integration with Stripe"
course: ITEC-442
topic: Payment Systems & Financial Technology
week: 9
difficulty: ⭐⭐⭐
estimated_time: 90 minutes
---

# Lab 09: Payment Integration with Stripe

| Field | Details |
|---|---|
| **Course** | ITEC-442 — Electronic Commerce |
| **Week** | 9 |
| **Difficulty** | ⭐⭐⭐ Advanced |
| **Estimated Time** | 90 minutes |
| **Topic** | Payment Systems & Financial Technology |
| **Prerequisites** | Python 3.10+, `pip install stripe flask`, free Stripe account |
| **Deliverables** | `checkout_server.py`, `webhook_handler.py`, `pci_assessment.md`, test payment screenshots |

---

## Overview

Payment integration is where e-commerce theory meets production code. Stripe's Payment Intents API handles the full lifecycle of a payment — authorization, 3D Secure (SCA), fraud scoring, and webhook confirmation — all without touching raw card data. In this lab you will build a working test checkout, handle payment webhooks, complete a PCI DSS self-assessment, and analyze alternative payment methods.

!!! warning "Test Mode Only"
    This lab uses **Stripe Test Mode** exclusively. No real money is ever charged. Use only the test card numbers provided. Never enter real card data.

---

## Part A — Stripe Account Setup (10 pts)

1. Create a free account at [https://stripe.com](https://stripe.com) (no credit card required for test mode)
2. Go to **Developers → API keys**
3. Copy your **Publishable key** (`pk_test_...`) and **Secret key** (`sk_test_...`)
4. Set them as environment variables:

```bash
export STRIPE_SECRET_KEY="sk_test_YOUR_KEY_HERE"
export STRIPE_PUBLISHABLE_KEY="pk_test_YOUR_KEY_HERE"
```

Install the Stripe library:
```bash
pip install stripe flask
```

Screenshot the Stripe dashboard showing your test mode API keys (blur/redact the actual key values).

---

## Part B — Payment Intent Checkout Server (35 pts)

Build a minimal Flask server that implements the **Stripe Payment Intents** flow:

```python
# checkout_server.py
import os
import stripe
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)
stripe.api_key = os.environ["STRIPE_SECRET_KEY"]
PUBLISHABLE_KEY = os.environ["STRIPE_PUBLISHABLE_KEY"]

# ── Product catalog ───────────────────────────────────────────────
PRODUCTS = {
    "prod_001": {"name": "Safety Hard Hat",     "price": 1800, "currency": "usd"},  # $18.00
    "prod_002": {"name": "Cut-5 Safety Gloves", "price":  900, "currency": "usd"},  # $9.00
    "prod_003": {"name": "Safety Glasses",      "price":  450, "currency": "usd"},  # $4.50
}

CHECKOUT_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>FSU Safety Supply — Checkout</title>
    <script src="https://js.stripe.com/v3/"></script>
    <style>
        body { font-family: sans-serif; max-width: 500px; margin: 40px auto; padding: 20px; }
        .product { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 8px; }
        #payment-form { margin-top: 20px; }
        #card-element { border: 1px solid #ddd; padding: 12px; border-radius: 4px; }
        #submit-btn { background: #0f3460; color: white; padding: 12px 24px;
                      border: none; border-radius: 4px; cursor: pointer; margin-top: 15px; width: 100%; }
        #result { margin-top: 15px; padding: 10px; border-radius: 4px; }
        .success { background: #e8f5e9; color: #2e7d32; }
        .error   { background: #ffebee; color: #c62828; }
    </style>
</head>
<body>
    <h2>FSU Safety Supply — Test Checkout</h2>

    <div class="product">
        <strong>{{ product.name }}</strong><br>
        Price: ${{ "%.2f" | format(product.price / 100) }}
    </div>

    <form id="payment-form">
        <div id="card-element"></div>
        <button id="submit-btn" type="submit">Pay ${{ "%.2f" | format(product.price / 100) }}</button>
        <div id="result"></div>
    </form>

    <p style="color:#888;font-size:12px;margin-top:20px;">
        Test card: 4242 4242 4242 4242 | Any future date | Any CVC
    </p>

    <script>
        const stripe = Stripe("{{ publishable_key }}");
        const elements = stripe.elements();
        const card = elements.create("card");
        card.mount("#card-element");

        document.getElementById("payment-form").addEventListener("submit", async (e) => {
            e.preventDefault();
            document.getElementById("submit-btn").disabled = true;
            document.getElementById("submit-btn").textContent = "Processing...";

            // Create PaymentIntent on server
            const resp = await fetch("/create-payment-intent", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({product_id: "{{ product_id }}"})
            });
            const { clientSecret, error: serverError } = await resp.json();
            if (serverError) {
                showResult(serverError, "error");
                return;
            }

            // Confirm payment on client
            const { paymentIntent, error } = await stripe.confirmCardPayment(clientSecret, {
                payment_method: { card: card }
            });

            if (error) {
                showResult(error.message, "error");
                document.getElementById("submit-btn").disabled = false;
                document.getElementById("submit-btn").textContent = "Pay ${{ '%.2f' | format(product.price / 100) }}";
            } else if (paymentIntent.status === "succeeded") {
                showResult("✓ Payment succeeded! ID: " + paymentIntent.id, "success");
            }
        });

        function showResult(msg, type) {
            const el = document.getElementById("result");
            el.textContent = msg;
            el.className = type;
        }
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    product_id = "prod_001"
    return render_template_string(CHECKOUT_HTML,
                                  product=PRODUCTS[product_id],
                                  product_id=product_id,
                                  publishable_key=PUBLISHABLE_KEY)

@app.route("/create-payment-intent", methods=["POST"])
def create_payment_intent():
    data = request.get_json()
    product_id = data.get("product_id", "prod_001")
    product = PRODUCTS.get(product_id)

    if not product:
        return jsonify({"error": "Product not found"}), 404

    try:
        intent = stripe.PaymentIntent.create(
            amount=product["price"],
            currency=product["currency"],
            metadata={
                "product_id": product_id,
                "product_name": product["name"],
                "integration": "lab09-itec442"
            },
            automatic_payment_methods={"enabled": True}
        )
        return jsonify({"clientSecret": intent.client_secret})
    except stripe.error.StripeError as e:
        return jsonify({"error": str(e)}), 400

@app.route("/payment-success")
def payment_success():
    payment_intent_id = request.args.get("payment_intent", "")
    if payment_intent_id:
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        return jsonify({
            "status": intent.status,
            "amount": intent.amount / 100,
            "currency": intent.currency.upper()
        })
    return jsonify({"error": "No payment ID provided"}), 400

if __name__ == "__main__":
    print("Starting checkout server on http://localhost:5000")
    print("Test card: 4242 4242 4242 4242 | Any future date | Any CVC")
    app.run(debug=True, port=5000)
```

Run:
```bash
python checkout_server.py
```

Open http://localhost:5000. Complete a test payment using these **Stripe test cards**:

| Card Number | Scenario |
|------------|---------|
| `4242 4242 4242 4242` | Successful payment |
| `4000 0000 0000 9995` | Payment declined (insufficient funds) |
| `4000 0025 0000 3155` | Requires 3D Secure authentication |
| `4000 0000 0000 0002` | Card declined (generic) |

**Screenshot each result** in the Stripe Dashboard → Payments.

---

## Part C — Webhook Handler (25 pts)

Webhooks confirm payments server-side — critical for fulfillment. Build `webhook_handler.py`:

```python
# webhook_handler.py
import os
import stripe
from flask import Flask, request, jsonify

app = Flask(__name__)
stripe.api_key = os.environ["STRIPE_SECRET_KEY"]
WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

# Simulated order database
orders = {}

@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get("Stripe-Signature")

    # Verify webhook signature (prevents fake events)
    try:
        if WEBHOOK_SECRET:
            event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
        else:
            event = stripe.Event.construct_from(
                __import__("json").loads(payload), stripe.api_key
            )
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        print(f"Webhook error: {e}")
        return jsonify({"error": "Invalid payload"}), 400

    # Handle events
    event_type = event["type"]
    data = event["data"]["object"]

    print(f"\n[WEBHOOK] Received: {event_type}")

    if event_type == "payment_intent.succeeded":
        handle_payment_succeeded(data)
    elif event_type == "payment_intent.payment_failed":
        handle_payment_failed(data)
    elif event_type == "charge.dispute.created":
        handle_dispute(data)
    else:
        print(f"  Unhandled event type: {event_type}")

    return jsonify({"received": True}), 200


def handle_payment_succeeded(payment_intent):
    pi_id = payment_intent["id"]
    amount = payment_intent["amount"] / 100
    currency = payment_intent["currency"].upper()
    product = payment_intent.get("metadata", {}).get("product_name", "Unknown")

    print(f"  ✓ Payment succeeded: {pi_id}")
    print(f"    Amount: ${amount:.2f} {currency}")
    print(f"    Product: {product}")

    # Create order record
    orders[pi_id] = {
        "status": "paid",
        "amount": amount,
        "product": product,
        "fulfillment": "queued"
    }
    print(f"    Order created → fulfillment queued")


def handle_payment_failed(payment_intent):
    pi_id = payment_intent["id"]
    error = payment_intent.get("last_payment_error", {})
    print(f"  ✗ Payment failed: {pi_id}")
    print(f"    Code: {error.get('code')}")
    print(f"    Message: {error.get('message')}")
    # In production: send failure email, retry logic, etc.


def handle_dispute(charge):
    print(f"  ⚠ DISPUTE CREATED on charge: {charge['id']}")
    print(f"    Amount: ${charge['amount']/100:.2f}")
    print(f"    Reason: {charge.get('dispute', {}).get('reason', 'unknown')}")
    # In production: alert fraud team, freeze account, gather evidence


@app.route("/orders")
def list_orders():
    return jsonify(orders)


if __name__ == "__main__":
    print("Webhook handler on http://localhost:5001/webhook")
    app.run(debug=True, port=5001)
```

Test using the **Stripe CLI** (optional — install from stripe.com/docs/stripe-cli):
```bash
stripe listen --forward-to localhost:5001/webhook
stripe trigger payment_intent.succeeded
stripe trigger payment_intent.payment_failed
```

Or test manually by making a purchase in Part B while the webhook server is running.

---

## Part D — PCI DSS Self-Assessment (20 pts)

Create `pci_assessment.md`. Complete a **SAQ A** self-assessment (for merchants using Stripe Elements who never handle raw card data):

```markdown
# PCI DSS SAQ A Self-Assessment — Lab 09

**Merchant type:** E-commerce, card-not-present
**SAQ type:** SAQ A (all cardholder data functions outsourced to Stripe)
**Assessment date:** [date]

## Why SAQ A Applies
SAQ A applies when:
- [x] Merchant accepts card payments online only (no face-to-face)
- [x] All cardholder data functions are outsourced to Stripe
- [x] Merchant does not electronically store, process, or transmit any cardholder data
- [x] Stripe's iFrame/Elements is used (card data goes directly to Stripe, not through our server)

## SAQ A Requirements Checklist

| Req | Requirement | Compliant | Notes |
|-----|-------------|:---------:|-------|
| 2.2 | No default vendor passwords | ☐ Yes / No | |
| 6.2 | Protection of public-facing systems | ☐ Yes / No | |
| 6.3 | Security vulnerabilities addressed | ☐ Yes / No | |
| 8.2 | Unique user IDs for all access | ☐ Yes / No | |
| 8.3 | Secure individual authentication | ☐ Yes / No | |
| 9.5 | Physical security of media | ☐ Yes / No | |
| 12.1 | Security policy established | ☐ Yes / No | |
| 12.8 | Third-party service provider compliance | ☐ Yes / No | (Stripe) |
| 12.9 | Incident response plan | ☐ Yes / No | |

## Our Implementation

**How we avoid handling card data:**
[Explain how Stripe Elements keeps card data out of our server]

**How we verify Stripe's PCI compliance:**
[Stripe publishes their PCI AOC at stripe.com/guides/pci-compliance]

**Gaps identified:**
[Any requirements not yet met?]

**Remediation plan:**
[Steps to address gaps]
```

---

## Part E — Alternative Payments Analysis (10 pts)

Write 400 words in `pci_assessment.md` comparing:
1. **Digital wallets** (Apple Pay, Google Pay) — how they use tokenization, conversion rate impact (+10–30% on mobile)
2. **Buy Now Pay Later** (Affirm, Klarna) — merchant economics (2–8% fee), AOV lift (+30–50%), default risk
3. **Cryptocurrency** (BitPay, Coinbase Commerce) — volatility risk, demographics, settlement

For a **mid-size U.S. outdoor gear retailer** ($15M annual revenue, 65% mobile traffic), recommend which 2 alternative payment methods to add next and why.

---

## Submission Checklist

- [ ] Stripe dashboard screenshot (test mode, API keys blurred)
- [ ] `checkout_server.py` — runs on localhost:5000
- [ ] Screenshots of all 4 test card scenarios in Stripe Dashboard
- [ ] `webhook_handler.py` — runs on localhost:5001
- [ ] `pci_assessment.md` — SAQ A checklist + alternative payments analysis

---

## Grading

| Component | Points |
|-----------|--------|
| Part A — Stripe setup + dashboard screenshot | 10 |
| Part B — Working checkout (all 4 test card scenarios) | 35 |
| Part C — Webhook handler (payment_succeeded handler working) | 25 |
| Part D — PCI DSS SAQ A assessment (complete checklist + gaps) | 20 |
| Part E — Alternative payments analysis + recommendation | 10 |
| **Total** | **100** |
