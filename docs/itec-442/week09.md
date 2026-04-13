---
title: "Week 9 — Payment Systems & Financial Technology"
description: "Payment ecosystem, card transaction flows, PCI DSS compliance, Stripe API integration, digital wallets, BNPL, cryptocurrency, fraud detection, and international payments for ITEC 442."
---

# Week 9 — Payment Systems & Financial Technology

> **Course Objectives:** CO1 (Evaluate e-commerce business models), CO9 (Analyze payment systems and financial technology for e-commerce)

---

## Learning Objectives

- [x] Map the payment ecosystem: issuers, acquirers, processors, and card networks
- [x] Trace a credit card transaction through authorization, clearing, and settlement
- [x] Identify all 12 PCI DSS requirements and appropriate SAQ types
- [x] Implement Stripe Payment Intents with webhooks and SCA compliance using Python or Node.js
- [x] Explain tokenization and biometric authentication in Apple Pay / Google Pay
- [x] Evaluate cryptocurrency payment options including volatility and regulatory risks
- [x] Analyze BNPL economics for merchants, consumers, and providers
- [x] Compare rule-based and ML-based fraud detection systems
- [x] Manage the chargeback process and implement prevention strategies
- [x] Design an international payment strategy considering local payment methods
- [x] Explain open banking, PSD2, and ACH/bank transfer mechanics

---

## 1. The Payment Ecosystem

### 1.1 The Five Parties in a Card Transaction

Every card payment involves five key participants:

```
CARDHOLDER                MERCHANT
    │                         │
    │  (presents card)        │ (submits transaction)
    ▼                         ▼
ISSUING BANK ←──────── ACQUIRING BANK
(Chase, Citi,           (Stripe, Square,
 Bank of America)        PayPal, WorldPay)
    ▲                         ▲
    └─────────────────────────┘
          CARD NETWORK
     (Visa, Mastercard, Amex, Discover)
```

| Party | Role | Examples | Revenue Source |
|-------|------|---------|----------------|
| **Cardholder** | Consumer making purchase | Anyone with a credit/debit card | N/A |
| **Merchant** | Seller accepting payment | Amazon, Target, any e-commerce store | Net revenue after fees |
| **Issuing Bank** | Bank that issued the card to cardholder | Chase, Citi, Capital One, Bank of America | Interchange fees, interest |
| **Acquiring Bank** | Bank that processes payments for merchant | Stripe, JPMorgan Merchant Services, WorldPay | Merchant discount rate (MDR) |
| **Card Network** | Operates the payment rails; sets rules | Visa, Mastercard, Amex, Discover | Assessment fees |

!!! info "Who Owns Amex?"
    American Express is unusual — it is both the issuing bank AND the card network for most Amex cards. This "closed-loop" system means Amex captures more of the economics but also means higher merchant fees (2.5–3.5% vs. Visa/MC at 1.5–2.5%).

### 1.2 Fee Structure

**Interchange fees** are paid by the acquiring bank to the issuing bank on each transaction. These are set by the card networks and are not negotiable.

**Interchange rates (US examples, 2024):**

| Card Type | Transaction Type | Interchange Rate |
|-----------|-----------------|-----------------|
| Visa Consumer Credit | Card-not-present (e-commerce) | 1.80% + $0.10 |
| Visa Debit (regulated) | Any | 0.05% + $0.21 (Durbin Amendment cap) |
| Mastercard Consumer Rewards | Card-not-present | 2.00% + $0.10 |
| Amex Opt-Blue | E-commerce | 2.30% + $0.10 |

**Total merchant discount rate (MDR):**

$$\text{MDR} = \text{Interchange} + \text{Network Assessment} + \text{Acquirer Markup}$$

For Stripe (2024): 2.9% + $0.30 per domestic card transaction. Of this, approximately 1.8% goes to the issuing bank, 0.13% to Visa/MC, and the remainder to Stripe.

---

## 2. Credit Card Transaction Flow

### 2.1 Authorization

Authorization is the real-time process (typically 1–2 seconds) of verifying the card and approving the transaction.

```
Step 1: Customer clicks "Pay" → Browser sends encrypted card data to payment processor

Step 2: Processor (Stripe) tokenizes card → sends authorization request to Card Network

Step 3: Card Network routes to Issuing Bank
        (Visa routes to Chase; Mastercard routes to Citi)

Step 4: Issuing Bank checks:
        ✓ Card is valid and not expired
        ✓ Account is in good standing (not closed/frozen)
        ✓ Sufficient credit available
        ✓ Fraud risk score (Falcon, Simility, or proprietary model)
        ✓ 3D Secure / Cardholder Authentication (if triggered)

Step 5: Issuing Bank responds:
        → Approved: Authorization code (e.g., 0B2934)
        → Declined: Reason code (01 = Refer to issuer, 05 = Do not honor, 
                                  14 = Invalid card number, 51 = Insufficient funds)

Step 6: Authorization result returned to merchant
        → Merchant receives approved/declined in ~1-2 seconds
        → Card is "authorized" but NOT yet charged (hold placed on funds)
```

### 2.2 Clearing and Settlement

Authorization creates a hold; **clearing** and **settlement** complete the money movement.

```
CLEARING (T+0 to T+1 after merchant submits batch):
- Merchant "captures" (closes) the authorization — typically at shipping or end-of-day
- Processor compiles all transactions into a batch
- Batch submitted to Card Network
- Network calculates net positions for all banks in system

SETTLEMENT (T+1 to T+2):
- Card Network instructs fund movement via ACH
- Acquiring bank receives net funds from issuing banks (minus interchange)
- Acquiring bank deposits merchant net amount (minus MDR)
- Merchant sees funds in bank account T+1 to T+2 for most processors
  (Stripe default: T+2 rolling; some processors T+1 or same-day for premium)
```

!!! tip "Authorization vs. Capture in E-Commerce"
    Many e-commerce platforms separate authorization (at order placement) from capture (at shipment). This is correct practice: authorizing but not capturing means you don't charge the customer until you've confirmed you can fulfill. Authorizations expire after 7–30 days depending on card network rules. Stripe's `payment_intent` API models this explicitly with `capture_method: manual`.

---

## 3. PCI DSS Compliance

### 3.1 What is PCI DSS?

The **Payment Card Industry Data Security Standard (PCI DSS)** is a set of security requirements for organizations that store, process, or transmit cardholder data. Developed by the PCI Security Standards Council (founded by Visa, Mastercard, Amex, Discover, JCB in 2004).

**PCI DSS v4.0** (released March 2022) contains **12 requirements** organized into 6 goals:

### 3.2 The 12 PCI DSS Requirements

| # | Requirement | Goal |
|---|-------------|------|
| 1 | Install and maintain network security controls (firewalls) | Build and Maintain a Secure Network |
| 2 | Apply secure configurations to all system components | Build and Maintain a Secure Network |
| 3 | Protect stored account data (encryption at rest) | Protect Account Data |
| 4 | Protect cardholder data with strong cryptography during transmission | Protect Account Data |
| 5 | Protect all systems against malware (anti-virus, EDR) | Maintain a Vulnerability Management Program |
| 6 | Develop and maintain secure systems and software (patching, SDLC) | Maintain a Vulnerability Management Program |
| 7 | Restrict access to system components and cardholder data by business need | Implement Strong Access Control Measures |
| 8 | Identify users and authenticate access to system components (MFA) | Implement Strong Access Control Measures |
| 9 | Restrict physical access to cardholder data | Implement Strong Access Control Measures |
| 10 | Log and monitor all access to network resources and cardholder data | Regularly Monitor and Test Networks |
| 11 | Test security of systems and networks regularly (pen testing, ASV scans) | Regularly Monitor and Test Networks |
| 12 | Support information security with organizational policies and programs | Maintain an Information Security Policy |

### 3.3 SAQ Types for E-Commerce Merchants

The **Self-Assessment Questionnaire (SAQ)** type depends on how the merchant handles cardholder data:

| SAQ Type | Description | # of Questions | Applicable to |
|----------|-------------|----------------|---------------|
| **SAQ A** | Card data fully outsourced; no electronic storage | 22 | E-commerce using iFrame/hosted fields (Stripe Elements) |
| **SAQ A-EP** | Website redirects to payment page; website could affect security | 191 | Merchants with JavaScript on checkout page |
| **SAQ B** | Imprint machines or standalone dial-up terminals only | 41 | Retail/MOTO, not e-commerce |
| **SAQ C-VT** | Virtual terminal only | 80 | Phone orders via web browser |
| **SAQ C** | Payment application with internet connection | 160 | In-scope if app connects to internet |
| **SAQ D** | All other merchants | 329 | Custom payment forms; storing card data |

!!! success "SAQ A — The Goal for Most E-Commerce Sites"
    By using hosted payment fields (Stripe Elements, Braintree Drop-In UI, PayPal Hosted Fields), the card data never touches the merchant's server. Qualifying for SAQ A (22 questions) vs. SAQ D (329 questions) is a massive compliance reduction. This is why nearly all e-commerce developers use hosted payment SDKs.

---

## 4. Stripe API Integration

### 4.1 Payment Intents Architecture

Stripe's **Payment Intents API** is the modern, recommended payment flow. It handles:
- 3D Secure (SCA) challenges automatically
- Multiple payment method types (cards, bank transfers, BNPL)
- Idempotent retry safety
- Webhook-based async confirmation

**Payment flow:**

```
1. Customer adds items to cart and proceeds to checkout
2. Backend creates a PaymentIntent → returns client_secret to frontend
3. Frontend collects card details using Stripe Elements (card never touches server)
4. Frontend confirms the PaymentIntent using client_secret
5. Stripe handles authentication (3DS if required)
6. PaymentIntent status transitions to "succeeded"
7. Stripe sends webhook event to backend
8. Backend fulfills order
```

### 4.2 Backend: Create a PaymentIntent (Python)

```python
# requirements.txt: stripe>=7.0.0

import stripe
from flask import Flask, request, jsonify
import os

app = Flask(__name__)
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
endpoint_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')

@app.route('/create-payment-intent', methods=['POST'])
def create_payment_intent():
    """
    Create a PaymentIntent and return the client_secret to the frontend.
    The client_secret is used by Stripe.js to confirm the payment.
    """
    try:
        data = request.get_json()
        
        # Calculate order total server-side (NEVER trust client-provided amounts)
        order_total = calculate_order_total(data['items'])
        
        intent = stripe.PaymentIntent.create(
            amount=order_total,          # Amount in cents (e.g., 2999 = $29.99)
            currency='usd',
            # Enable multiple payment methods automatically
            automatic_payment_methods={'enabled': True},
            # Store order metadata for fulfillment
            metadata={
                'order_id': data.get('order_id'),
                'customer_email': data.get('email'),
                'customer_id': data.get('customer_id'),
            },
            # Optional: Set idempotency key to prevent duplicate charges
            # idempotency_key=f"order_{data['order_id']}"
        )
        
        return jsonify({
            'clientSecret': intent['client_secret'],
            'paymentIntentId': intent['id']
        })
        
    except stripe.error.CardError as e:
        # CardErrors are safe to display to users
        return jsonify({'error': e.user_message}), 400
    except stripe.error.StripeError as e:
        # Other Stripe errors should not be exposed to users
        app.logger.error(f'Stripe error: {e}')
        return jsonify({'error': 'Payment processing error'}), 500
    except Exception as e:
        app.logger.error(f'Server error: {e}')
        return jsonify({'error': 'Internal server error'}), 500


def calculate_order_total(items):
    """Calculate order total from item list. Always calculate server-side."""
    # In production: fetch prices from your database, never from client
    total = 0
    for item in items:
        product = fetch_product_from_db(item['product_id'])
        total += product['price_cents'] * item['quantity']
    return total
```

### 4.3 Webhook Handler (Python)

```python
@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Handle Stripe webhook events. Use webhooks to reliably fulfill orders
    because the customer may close their browser before your success page loads.
    """
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        # Verify webhook signature to ensure request is from Stripe
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature — possible spoofed request
        return 'Invalid signature', 400
    
    # Handle the event type
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        handle_successful_payment(payment_intent)
        
    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        handle_failed_payment(payment_intent)
        
    elif event['type'] == 'charge.dispute.created':
        dispute = event['data']['object']
        handle_dispute(dispute)
        
    # Return 200 to acknowledge receipt. If you return non-200, Stripe retries.
    return '', 200


def handle_successful_payment(payment_intent):
    """Fulfill the order after confirmed payment."""
    order_id = payment_intent['metadata'].get('order_id')
    customer_email = payment_intent['metadata'].get('customer_email')
    
    # 1. Mark order as paid in your database
    db.orders.update_one(
        {'_id': order_id},
        {'$set': {
            'status': 'paid',
            'payment_intent_id': payment_intent['id'],
            'paid_at': datetime.utcnow()
        }}
    )
    
    # 2. Trigger fulfillment workflow
    fulfillment_service.process_order(order_id)
    
    # 3. Send order confirmation email
    email_service.send_order_confirmation(customer_email, order_id)
    
    app.logger.info(f'Order {order_id} paid successfully')
```

### 4.4 Frontend: Collect Payment with Stripe Elements (JavaScript)

```javascript
// HTML: <div id="payment-element"></div>
// HTML: <button id="submit-button">Pay $29.99</button>
// HTML: <div id="error-message"></div>

const stripe = Stripe('pk_test_YOUR_PUBLISHABLE_KEY');

// Step 1: Create PaymentIntent on page load
const response = await fetch('/create-payment-intent', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    items: cart.items,
    order_id: cart.orderId,
    email: customer.email
  })
});
const { clientSecret } = await response.json();

// Step 2: Mount Stripe Elements (hosted payment form)
const elements = stripe.elements({ clientSecret });
const paymentElement = elements.create('payment');  // Auto-detects best payment methods
paymentElement.mount('#payment-element');

// Step 3: Handle form submission
document.querySelector('#submit-button').addEventListener('click', async () => {
  const { error } = await stripe.confirmPayment({
    elements,
    confirmParams: {
      return_url: 'https://yourstore.com/order-confirmation',
      receipt_email: customer.email,
      shipping: {
        name: customer.name,
        address: {
          line1: customer.address.line1,
          city: customer.address.city,
          state: customer.address.state,
          postal_code: customer.address.zip,
          country: 'US'
        }
      }
    }
  });

  if (error) {
    // Error displays to customer (e.g., "Your card was declined")
    document.querySelector('#error-message').textContent = error.message;
  }
  // On success, Stripe redirects to return_url
});
```

!!! tip "Testing Stripe Integrations"
    Use Stripe test card numbers:
    - `4242 4242 4242 4242` — Always succeeds
    - `4000 0000 0000 0002` — Always declined
    - `4000 0025 0000 3155` — Requires 3D Secure authentication
    - `4000 0000 0000 9995` — Insufficient funds
    
    Always use test keys (`pk_test_...` / `sk_test_...`) in development. Never commit secret keys to version control — use environment variables or secrets management (AWS Secrets Manager, HashiCorp Vault).

---

## 5. Digital Wallets and Alternative Payment Methods

### 5.1 PayPal

PayPal with 435 million active accounts (Q4 2023) remains the most recognized digital wallet globally.

**PayPal integration options:**

| Method | Implementation | CVR Impact |
|--------|---------------|-----------|
| **PayPal Standard** | Redirect to PayPal; return to merchant | Baseline |
| **PayPal Express Checkout** | One-click from cart | +14% CVR (PayPal internal) |
| **PayPal Hosted Fields** | Card form on merchant page | PCI SAQ A eligible |
| **Pay Later / BNPL** | Installments shown at checkout | +10–15% AOV |

**PayPal fees (US merchant, 2024):**
- Online transactions: 3.49% + $0.49 (standard)
- PayPal Checkout: 3.49% + $0.49
- Venmo (PayPal subsidiary): 1.9% + $0.10

### 5.2 Apple Pay and Google Pay

**Apple Pay** and **Google Pay** use a mechanism called **tokenization** — the actual card number is never transmitted to the merchant. Instead, a **Device Account Number (DAN)** or **Network Token** is created for each device/merchant pair.

**Tokenization flow:**

```
1. Customer provisions card in Apple Wallet
   → Bank verifies card (ID+V — Identification and Verification)
   → Card network creates a unique Device Account Number (DAN)
   → DAN stored in Secure Enclave (iPhone) or trusted execution environment

2. Customer pays with Apple Pay at checkout
   → Face ID / Touch ID authenticates the user (biometric)
   → Device generates one-time dynamic security code using DAN
   → Merchant receives: DAN + dynamic code (NOT the real PAN)

3. Processor routes to card network using DAN
   → Network maps DAN to real card (PAN)
   → Authorizes with issuing bank
   → Merchant never sees real card number
```

**Why this matters for security:** Even if a merchant is breached, the stolen DANs are useless — they only work on the specific device with biometric authentication. This eliminates the card-present fraud vector entirely.

**Adoption rates (US, 2023):**
- Apple Pay: 507 million global users; 43% of iPhone owners use it regularly
- Google Pay: 150 million+ users; adoption strong in Android-dominant markets

**Implementation on web (Payment Request API):**

```javascript
// Check if Apple Pay / Google Pay is available
const paymentRequest = stripe.paymentRequest({
  country: 'US',
  currency: 'usd',
  total: {
    label: 'Your Order',
    amount: 2999,  // $29.99 in cents
  },
  requestPayerName: true,
  requestPayerEmail: true,
  requestShipping: true,
  shippingOptions: [
    {
      id: 'standard',
      label: 'Standard Shipping (5-7 days)',
      detail: 'Free over $50',
      amount: 0
    }
  ]
});

const elements = stripe.elements();
const prButton = elements.create('paymentRequestButton', { paymentRequest });

// Check if the browser/device supports this payment method
(async () => {
  const result = await paymentRequest.canMakePayment();
  if (result) {
    prButton.mount('#payment-request-button');
    // Shows Apple Pay button on Safari/iOS, Google Pay on Chrome/Android
  } else {
    document.getElementById('payment-request-button').style.display = 'none';
  }
})();
```

---

## 6. Cryptocurrency Payments

### 6.1 Bitcoin and Crypto Payments Overview

Cryptocurrency payments allow merchants to accept Bitcoin (BTC), Ethereum (ETH), stablecoins (USDC, USDT), and other digital assets.

**Technical flow (Bitcoin on-chain):**

```
1. Customer clicks "Pay with Bitcoin"
2. Merchant payment processor (BitPay, Coinbase Commerce, NOWPayments) 
   generates a unique Bitcoin address and invoice amount in BTC
3. Customer sends BTC from their wallet to the address
4. Transaction broadcast to Bitcoin network
5. After N confirmations (typically 1-6, each ~10 minutes), payment confirmed
6. Processor either:
   a. Converts BTC to USD immediately (protects against volatility) and
      deposits USD to merchant bank account
   b. Holds BTC in merchant crypto wallet (merchant takes price risk)
```

### 6.2 Stablecoins

**Stablecoins** are cryptocurrencies pegged to a stable asset (usually USD) to eliminate volatility.

| Stablecoin | Peg | Backing Mechanism | Market Cap (2024) |
|------------|-----|------------------|-------------------|
| **USDC** | USD | Cash + US Treasuries (audited monthly) | $43B |
| **USDT (Tether)** | USD | Mixed reserve (controversy) | $108B |
| **DAI** | USD | Crypto-collateralized (algorithmic) | $5B |
| **PYUSD (PayPal)** | USD | Cash + short-term Treasuries | $0.4B |

Stablecoins eliminate the primary objection to crypto payments: volatility. A merchant accepting USDC receives exactly $1 per USDC with no exchange risk.

!!! warning "Crypto Payment Risks and Regulatory Considerations"
    - **Volatility:** Bitcoin has experienced 50–80% price swings within a year. Accepting BTC without immediate conversion exposes merchants to speculative risk.
    - **Regulatory:** FinCEN classifies crypto exchanges as Money Services Businesses (MSBs) requiring BSA compliance. IRS treats crypto as property — each transaction is a potential taxable event.
    - **Irreversibility:** Unlike card payments, crypto transactions are final. No chargebacks — but also no recourse for fraud or errors.
    - **Customer adoption:** <1% of US online purchases made with cryptocurrency (2023). Primarily a niche/PR strategy.
    - **Tax reporting:** IRS Form 1099-DA requirements for crypto brokers took effect 2025.

### 6.3 Real-World Crypto Merchant Adoption

Notable merchants accepting crypto: Tesla (paused), Microsoft (Xbox), Overstock.com, Newegg, Shopify merchants (via third-party plugins), Whole Foods (via Spedn app).

---

## 7. Buy Now Pay Later (BNPL)

### 7.1 BNPL Economics

**Buy Now Pay Later** allows consumers to split purchases into installments, typically interest-free (if paid on time). BNPL represented **$75 billion in US e-commerce volume** in 2023 (Insider Intelligence).

**Three major BNPL models:**

=== "Klarna"
    - Founded 2005 in Stockholm; 150 million global users
    - **Products:** Pay in 4 (4 installments, 0% interest), Pay in 30 days, financing (up to 36 months)
    - **Merchant fee:** 3.29–5.99% + $0.30 per transaction (higher than standard credit card)
    - **Model:** Klarna pays merchant upfront; consumer repays Klarna
    - **Revenue:** Merchant fees (primary) + late fees ($7/missed payment) + interest on longer financing
    - **Risk:** Klarna holds credit risk for all defaults

=== "Afterpay (Block)"
    - Founded 2014 in Melbourne; 20 million US users
    - **Products:** Pay in 4 (every 2 weeks, 0% interest)
    - **Merchant fee:** 4–6% + $0.30 per transaction
    - **Late fee cap:** $8 or 25% of order value (whichever is less)
    - **No hard credit check:** Uses behavioral scoring + bank account verification
    - **Acquired by Block (Square):** $29 billion acquisition in 2022

=== "Affirm"
    - Founded 2012 by Max Levchin (PayPal co-founder); 17 million active users
    - **Products:** Pay in 4 (0% interest); monthly installments 6–36 months (0–36% APR)
    - **Merchant fee:** Varies; often 2–5.5% — lower for partners like Amazon
    - **Differentiator:** No hidden fees; all costs disclosed upfront (unlike credit cards)
    - **Amazon partnership:** Affirm is the exclusive BNPL partner for Amazon.com
    - **Revenue model:** Merchant fees + consumer interest income on APR products

### 7.2 BNPL Impact on Merchants

| Impact | Stat | Source |
|--------|------|--------|
| AOV increase | +30–50% with BNPL offer | Klarna merchant data |
| CVR increase | +20–30% | Afterpay merchant data |
| Cart abandonment reduction | -20% | Affirm |
| Return rate with BNPL | Higher (6–10pp above credit card) | Various |
| Merchant fee premium vs. credit card | +1.5–3.5% | Industry analysis |

!!! warning "BNPL Regulatory Environment"
    The CFPB (Consumer Financial Protection Bureau) published a report in 2022 noting BNPL borrowers are more likely to have high credit card balances and overdraft fees. In 2023, the CFPB issued interpretive guidance stating BNPL lenders must provide certain protections under the Truth in Lending Act (TILA). Regulation is evolving rapidly and merchants should monitor for compliance changes.

---

## 8. Fraud Detection Systems

### 8.1 Rule-Based Fraud Detection

Traditional fraud detection uses configurable rules to flag or block suspicious transactions:

```python
# Example rule engine pseudo-code
def evaluate_fraud_rules(transaction):
    risk_score = 0
    flags = []
    
    # Rule 1: IP geolocation mismatch
    if transaction.billing_country != transaction.ip_country:
        risk_score += 25
        flags.append('BILLING_IP_MISMATCH')
    
    # Rule 2: High-velocity — multiple cards from same IP
    recent_failed = count_failed_attempts(transaction.ip_address, minutes=30)
    if recent_failed >= 3:
        risk_score += 40
        flags.append('HIGH_VELOCITY_IP')
    
    # Rule 3: First purchase + high order value + expedited shipping
    if (is_first_purchase(transaction.email) and 
        transaction.amount > 500 and 
        transaction.shipping_method == 'overnight'):
        risk_score += 30
        flags.append('FIRST_ORDER_HIGH_VALUE_RUSH')
    
    # Rule 4: Card BIN country mismatch
    bin_country = lookup_bin_country(transaction.card_bin)
    if bin_country != transaction.billing_country:
        risk_score += 20
        flags.append('BIN_BILLING_MISMATCH')
    
    # Rule 5: Known fraud email domain pattern
    if check_fraud_email_list(transaction.email):
        risk_score += 50
        flags.append('KNOWN_FRAUD_EMAIL')
    
    # Disposition
    if risk_score >= 80:
        return 'DECLINE'
    elif risk_score >= 50:
        return 'REVIEW'
    else:
        return 'APPROVE'
```

**Rule-based limitations:**
- High false positive rate (legitimate orders blocked): avg 2–3% of orders falsely declined
- Rigid — fraudsters quickly learn and adapt rule patterns
- Cannot detect subtle behavioral patterns
- Expensive to maintain: requires fraud analyst time to tune rules

### 8.2 Machine Learning Fraud Detection

ML models learn from historical transaction data to identify fraud patterns:

| Technique | How it works | Advantage |
|-----------|-------------|-----------|
| **Supervised learning (XGBoost, Random Forest)** | Trained on labeled fraud/legitimate transactions | High accuracy when training labels are clean |
| **Neural networks (LSTM)** | Captures sequential transaction patterns over time | Detects behavioral drift |
| **Graph analysis** | Detects fraud rings by mapping entity relationships | Identifies coordinated attacks |
| **Anomaly detection (Isolation Forest, Autoencoders)** | Flags statistically unusual transactions | Works without labeled data |

**Fraud signals used as ML features:**

```
Device fingerprint (browser, OS, screen resolution, fonts)
Typing speed and keystroke patterns (behavioral biometrics)
Mouse movement patterns (human vs. bot behavior)
Session duration and page navigation sequence
Historical transaction velocity for device/email/IP
Time since account creation
Email domain age and reputation
Shipping address delivery success history
Card BIN risk profile
Darkweb credential database match (email:password exposure)
```

**Commercial fraud platforms:**
- **Stripe Radar:** ML model trained on Stripe's global transaction network ($1+ trillion/year); included with Stripe payments
- **Signifyd:** Specializes in e-commerce fraud; offers financial guarantee for approved orders
- **Kount (Equifax):** Rule + ML hybrid; strong in digital goods and gaming
- **Forter:** Real-time identity-based decisions; fast approval for good customers

### 8.3 Chargeback Process and Prevention

A **chargeback** occurs when a cardholder disputes a transaction with their issuing bank, which reverses the charge and debits the merchant.

**Chargeback process:**

```
1. Customer disputes charge with issuing bank
   ("I didn't authorize this" / "Item not as described" / "Never received")

2. Issuing bank provisionally credits customer and notifies card network

3. Card network notifies acquiring bank → notifies merchant
   Merchant has 7–30 days to respond (varies by network)

4. Merchant options:
   a. Accept: Funds permanently transferred to customer
   b. Dispute: Submit compelling evidence package

5. If disputed:
   Merchant submits: proof of delivery, customer communication, 
   signed terms of service, IP logs, device fingerprint

6. Issuing bank reviews evidence
   → Decides for merchant (funds returned) or cardholder (merchant loses)

7. If merchant loses AND disputes again: Arbitration (card network decides)
   Arbitration costs: $250–$500 regardless of outcome
```

**Chargeback costs:**

| Cost Component | Amount |
|---------------|--------|
| Merchandise/service value | $X (lost) |
| Chargeback fee (processor) | $15–$100 |
| Processing/labor cost | ~$25 |
| Merchandise potentially destroyed | Cost of goods |
| **Total cost to merchant** | **2–3× original transaction value** |

**Chargeback thresholds:** Visa/Mastercard monitor merchant chargeback rates. Exceeding 1% (Visa Dispute Monitoring Program threshold) or 1.5% (excessive) results in:
- Increased scrutiny and reporting requirements
- Fines ($25–$75 per chargeback above threshold)
- Potential account termination ("merchant high risk")

---

## 9. International Payments

### 9.1 Payment Methods by Region

E-commerce merchants targeting international markets must offer **local payment methods (LPMs)** — in many markets, credit card penetration is low and local alternatives dominate.

| Market | Dominant Payment Methods | Notes |
|--------|--------------------------|-------|
| **Netherlands** | iDEAL (bank transfer) | 60% of all online payments |
| **Germany** | SEPA Direct Debit, PayPal, Klarna SOFORT | Cash-on-delivery still significant |
| **Brazil** | Pix (instant bank transfer), Boleto Bancário | Pix launched 2020; explosive growth |
| **China** | Alipay, WeChat Pay | Cards rarely used online |
| **India** | UPI (Unified Payments Interface), Paytm | UPI processes 10B+ transactions/month |
| **Poland** | BLIK, PayByLink | Strong preference for local methods |
| **Mexico** | OXXO (cash voucher), SPEI (bank transfer) | Large unbanked population |
| **Japan** | Convenience store payment, JCB | Konbini payment (in-store QR code) |

**Impact of local payment method support:**
Stripe research (2022) found that offering local payment methods can increase conversion by **20–50%** in markets where cards are secondary.

### 9.2 Currency and FX

**Dynamic currency conversion (DCC):** Offered by some payment terminals — converts the transaction to the cardholder's home currency at point of sale. Generally provides poor exchange rates; most sophisticated travelers decline.

**Multi-currency pricing strategies:**

=== "Presentment Currency"
    Show prices in the customer's local currency even if settlement is in USD.
    
    - Customer sees "€89.95" not "USD $97.83"
    - Payment processor handles FX conversion
    - Increases trust and reduces friction in European/global markets
    - Stripe Payments: Automatic currency conversion available in 135 currencies

=== "Local Pricing"
    Set distinct prices per market (not just FX-converted USD prices).
    
    - Allows for market-specific pricing strategy
    - Requires management of multiple price books
    - Avoids "round number" weirdness from FX conversion ($97.83 → €89.95)
    - Used by major software and media companies (Apple, Netflix, Spotify)

### 9.3 Open Banking and PSD2

**PSD2 (Revised Payment Services Directive)** is a European regulation (2018, revised 2023) mandating that banks open APIs to licensed third parties:

- **Account Information Service Providers (AISPs):** Read account data (balance, transactions) with customer consent — enables apps like Mint, Plaid
- **Payment Initiation Service Providers (PISPs):** Initiate payments directly from bank accounts — bypasses card networks entirely
- **Strong Customer Authentication (SCA):** Multi-factor authentication required for most electronic payments in the EU: two of three factors (knowledge, possession, inherence)

**SCA exemptions (to reduce friction for low-risk transactions):**
- Transactions < €30
- Merchant-initiated transactions (subscriptions)
- Transactions from trusted merchants (whitelisted by cardholder)
- Low-risk transactions (fraud rate below threshold)

### 9.4 ACH and Bank Transfers for B2B

**ACH (Automated Clearing House)** is the US electronic bank-to-bank transfer network operated by Nacha.

| ACH Type | Description | Timing | Use Case |
|----------|-------------|--------|---------|
| **Standard ACH** | Next-day or 2-day settlement | T+1 or T+2 | Payroll, vendor payments |
| **Same-Day ACH** | Multiple daily settlement windows | Same business day | Urgent B2B payments |
| **ACH Debit** | Pull funds from another account | T+1 | B2B subscriptions, invoices |
| **Real-Time Payments (RTP)** | Instant settlement 24/7/365 | Seconds | Emerging; RFIs and B2B |
| **FedNow** | Fed's instant payment service (2023) | Seconds | Competing with RTP |

**ACH fees:** $0.20–$1.50 per transaction (vs. 2.9% for credit cards) — dramatically lower for B2B high-value transactions. A $50,000 supplier payment via ACH costs $1.50; via credit card would cost $1,450.

---

## Key Vocabulary

| Term | Definition |
|------|-----------|
| **Issuing Bank** | Bank that issues credit/debit cards to consumers |
| **Acquiring Bank** | Bank that processes card payments on behalf of merchants |
| **Card Network** | Operates payment rails and sets interchange rules (Visa, Mastercard) |
| **Interchange Fee** | Fee paid by acquiring bank to issuing bank per transaction |
| **MDR** | Merchant Discount Rate — total fee charged to merchant per transaction |
| **PCI DSS** | Payment Card Industry Data Security Standard |
| **SAQ** | Self-Assessment Questionnaire — PCI compliance self-evaluation |
| **Payment Intent** | Stripe object representing payment lifecycle from creation to completion |
| **Tokenization** | Replacing sensitive card data with a non-sensitive token |
| **3D Secure (3DS)** | Authentication protocol adding cardholder verification step |
| **SCA** | Strong Customer Authentication — EU PSD2 requirement for 2-factor auth |
| **Chargeback** | Forced payment reversal initiated by cardholder through issuing bank |
| **BNPL** | Buy Now Pay Later — deferred payment installment product |
| **ACH** | Automated Clearing House — US electronic bank transfer network |
| **PSD2** | EU regulation requiring banks to open APIs to licensed third parties |
| **Stablecoin** | Cryptocurrency pegged to stable asset (usually USD) |
| **CVV** | Card Verification Value — 3-4 digit security code on card |
| **BIN** | Bank Identification Number — first 6-8 digits identifying issuing bank |

---

## Review Questions

!!! question "Week 9 Review Questions"

    1. **Trace a $150 online purchase from card swipe to merchant bank deposit, identifying every party involved (cardholder, merchant, acquirer, network, issuer), what action each party takes, what fee each earns or pays, and how long each phase (authorization, clearing, settlement) takes. What is the net amount the merchant receives if using Stripe at 2.9% + $0.30?**

    2. **A startup e-commerce company asks you whether they should build their own payment form with direct card data collection, use Stripe Elements (iFrame hosted fields), or redirect to PayPal. Compare all three approaches on the dimensions of: PCI DSS compliance burden (which SAQ applies?), user experience, conversion rate impact, implementation complexity, and ongoing maintenance. Make a clear recommendation with justification.**

    3. **Analyze the BNPL ecosystem using Klarna, Afterpay, and Affirm as examples. From the merchant's perspective: what are the true costs and benefits? From the consumer's perspective: how does BNPL compare to credit cards in terms of cost, credit impact, and consumer protection? What regulatory risks should merchants be aware of when prominently featuring BNPL at checkout?**

    4. **Design a fraud detection strategy for an e-commerce company selling electronics ($200–$2,000 average order value) that is experiencing a 1.8% chargeback rate. Describe the signals you would use, how you would distinguish between rule-based and ML-based detection, what threshold would trigger manual review vs. auto-decline, and how you would measure and reduce your false positive rate (legitimate orders incorrectly declined). What does a chargeback rate of 1.8% actually cost the company?**

    5. **A US-based fashion retailer wants to expand to Germany, Brazil, and China. For each market, identify the dominant payment methods, explain why local payment methods matter for conversion, describe the technical integration required to support each method on their Shopify Plus store, and identify any regulatory compliance requirements specific to payments in each market.**

---

## Further Reading

- Stripe Documentation. (2024). *Payment Intents API Guide*. [stripe.com/docs/payments/payment-intents](https://stripe.com/docs/payments/payment-intents)
- PCI Security Standards Council. (2022). *PCI DSS v4.0 Requirements and Testing Procedures*. [pcisecuritystandards.org](https://www.pcisecuritystandards.org)
- Baymard Institute. (2023). *Online Payment & Form Usability Research*. [baymard.com](https://baymard.com)
- CFPB. (2022). *Buy Now, Pay Later: Market trends and consumer impacts*. [consumerfinance.gov](https://www.consumerfinance.gov)
- European Banking Authority. (2023). *Guidelines on Strong Customer Authentication (SCA)*. [eba.europa.eu](https://www.eba.europa.eu)
- Nacha. (2024). *ACH Network Rules and Operating Guidelines*. [nacha.org](https://www.nacha.org)
- Worldpay from FIS. (2024). *Global Payments Report 2024*. [worldpayglobal.com/global-payments-report](https://www.worldpayglobal.com/global-payments-report) — Comprehensive local payment method data by country
- Visa. (2024). *Visa Core Rules and Visa Product and Service Rules*. [usa.visa.com/support/merchant](https://usa.visa.com/support/merchant)

---

[← Week 8](week08.md) | [Course Index](index.md) | [Week 10 →](week10.md)
