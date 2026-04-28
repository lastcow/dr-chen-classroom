---
title: "Lab 10: E-Commerce Security Audit"
course: ITEC-442
topic: E-Commerce Security & Trust
week: 10
difficulty: ⭐⭐⭐
estimated_time: 85 minutes
---

# Lab 10: E-Commerce Security Audit

| Field | Details |
|---|---|
| **Course** | ITEC-442 — Electronic Commerce |
| **Week** | 10 |
| **Difficulty** | ⭐⭐⭐ Advanced |
| **Estimated Time** | 85 minutes |
| **Topic** | E-Commerce Security & Trust |
| **Prerequisites** | Python 3.10+, `pip install requests` |
| **Deliverables** | `security_audit.md`, `trust_checker.py`, `privacy_audit.md` |

---

## Overview

Every e-commerce site is a high-value target. A security audit systematically evaluates an online store against industry standards — identifying vulnerabilities before attackers do, measuring trust signals that affect conversion, and verifying privacy compliance. In this lab you will audit a real e-commerce site using the OWASP checklist, build an automated trust signal checker, and assess cookie/privacy compliance.

!!! danger "Legal & Ethical Scope"
    Only audit sites you have permission to test, or use **passive analysis only** (inspecting publicly available headers, cookies, and page content without sending attack payloads). All techniques in this lab are passive observation — no penetration testing.

---

## Part A — Choose Your Audit Target (5 pts)

Select a **real, publicly accessible e-commerce site** (different from your Lab 06 UX audit target). Medium-sized retailers work best — large enterprises are extremely hardened.

Document in `security_audit.md`:
- Site URL
- Company size estimate (small/medium/large)
- Products sold
- Your rationale

---

## Part B — OWASP Top 10 Checklist (30 pts)

Evaluate the site against the **OWASP Top 10 for E-Commerce** using passive analysis. For each item, document what you observed — not what you attacked.

```markdown
## OWASP Top 10 Security Assessment

**Site:** [URL]
**Assessment Type:** Passive observation only
**Date:** [date]

| OWASP # | Category | Check Performed | Finding | Severity |
|---------|---------|----------------|---------|---------|
| A01 | Broken Access Control | Can you access /admin, /dashboard without login? | | |
| A02 | Cryptographic Failures | Is the site HTTPS? What TLS version? Mixed content? | | |
| A03 | Injection | Are search/filter params reflected in URL? | | |
| A04 | Insecure Design | Is there guest checkout? Rate limiting visible? | | |
| A05 | Security Misconfiguration | Server headers exposed? Directory listing? | | |
| A06 | Vulnerable Components | What JS libraries load? (check browser console) | | |
| A07 | Auth & Session Failures | Cookie attributes? Session token in URL? | | |
| A08 | Software & Data Integrity | Are CDN resources subresource-integrity verified? | | |
| A09 | Logging & Monitoring | Does the site have a security.txt? | | |
| A10 | SSRF | (Skip — requires active testing) | N/A | N/A |
```

**How to check each item (passive only):**

```bash
# Check TLS version and certificate
curl -vI https://yoursite.com 2>&1 | grep -E "TLS|SSL|subject|issuer"

# Check security headers
curl -sI https://yoursite.com | grep -iE "strict-transport|content-security|x-frame|x-content-type|referrer-policy"

# Check for security.txt
curl -s https://yoursite.com/.well-known/security.txt

# Check cookies (in browser DevTools → Application → Cookies)
# Look for: Secure flag, HttpOnly flag, SameSite attribute, expiry
```

For each finding, rate severity: **Critical / High / Medium / Low / Informational**.

---

## Part C — Automated Trust Signal Checker (30 pts)

Build `trust_checker.py` — a script that automatically evaluates trust signals for any e-commerce URL:

```python
# trust_checker.py
import requests
import ssl
import socket
import re
from urllib.parse import urlparse
from datetime import datetime

def audit_site(url: str) -> dict:
    """Perform passive security and trust audit of an e-commerce URL."""
    results = {}
    hostname = urlparse(url).netloc

    print(f"\n{'='*60}")
    print(f"Security & Trust Audit: {url}")
    print(f"{'='*60}\n")

    # ── 1. HTTPS & TLS ────────────────────────────────────────────
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=hostname) as s:
            s.connect((hostname, 443))
            cert = s.getpeercert()
            tls_version = s.version()

        # Certificate expiry
        expiry_str = cert.get("notAfter", "")
        expiry = datetime.strptime(expiry_str, "%b %d %H:%M:%S %Y %Z") if expiry_str else None
        days_remaining = (expiry - datetime.now()).days if expiry else None

        results["tls_version"]     = tls_version
        results["cert_valid"]      = True
        results["cert_days_left"]  = days_remaining
        results["cert_issuer"]     = dict(cert.get("issuer", [])[-1]).get("organizationName", "Unknown")

        status = "✓" if (days_remaining or 0) > 30 else "⚠"
        print(f"{status} TLS: {tls_version} | Cert valid {days_remaining}d | Issuer: {results['cert_issuer']}")
    except Exception as e:
        results["tls_error"] = str(e)
        print(f"✗ TLS Error: {e}")

    # ── 2. Security Headers ───────────────────────────────────────
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0 (Security Audit)"})
        headers = resp.headers

        security_headers = {
            "Strict-Transport-Security": "HSTS",
            "Content-Security-Policy":   "CSP",
            "X-Frame-Options":           "Clickjacking Protection",
            "X-Content-Type-Options":    "MIME Sniffing Protection",
            "Referrer-Policy":           "Referrer Policy",
            "Permissions-Policy":        "Permissions Policy"
        }

        print("\nSecurity Headers:")
        results["headers"] = {}
        for header, name in security_headers.items():
            present = header in headers
            results["headers"][header] = present
            icon = "✓" if present else "✗"
            val = headers.get(header, "MISSING")[:60] if present else "MISSING"
            print(f"  {icon} {name}: {val}")

        # Server info leak
        server = headers.get("Server", "")
        powered = headers.get("X-Powered-By", "")
        if server or powered:
            print(f"  ⚠ Server info exposed: Server={server} X-Powered-By={powered}")
        else:
            print(f"  ✓ No server version exposed")

        results["status_code"] = resp.status_code
        results["content"] = resp.text[:5000]  # for further analysis

    except Exception as e:
        results["request_error"] = str(e)
        print(f"✗ Request error: {e}")
        return results

    # ── 3. Trust Signals ──────────────────────────────────────────
    content = results.get("content", "")
    print("\nTrust Signals (page content analysis):")

    trust_checks = {
        "SSL badge/lock icon": bool(re.search(r'ssl|secure|lock', content, re.I)),
        "Reviews/ratings":     bool(re.search(r'review|rating|star|\d+\s+reviews', content, re.I)),
        "Money-back guarantee":bool(re.search(r'money.back|guarantee|return policy', content, re.I)),
        "Phone number":        bool(re.search(r'\d{3}[-.\s]\d{3}[-.\s]\d{4}', content)),
        "Physical address":    bool(re.search(r'\d+\s+\w+\s+(st|ave|blvd|rd|dr|lane)', content, re.I)),
        "Live chat widget":    bool(re.search(r'chat|intercom|zendesk|freshchat', content, re.I)),
        "Social proof":        bool(re.search(r'customers?|users?|sold|trusted', content, re.I)),
        "Payment badges":      bool(re.search(r'visa|mastercard|paypal|amex|stripe', content, re.I)),
        "BBB/Trust badge":     bool(re.search(r'bbb|trustpilot|norton|mcafee secure', content, re.I)),
    }

    results["trust_signals"] = trust_checks
    trust_score = sum(trust_checks.values())
    for signal, present in trust_checks.items():
        icon = "✓" if present else "✗"
        print(f"  {icon} {signal}")

    print(f"\nTrust Score: {trust_score}/{len(trust_checks)} signals present")

    # ── 4. Cookie Analysis ────────────────────────────────────────
    print("\nCookie Analysis:")
    cookies = resp.cookies
    for cookie in cookies:
        secure   = "✓" if cookie.secure else "✗"
        httponly = "✓" if cookie.has_nonstandard_attr("HttpOnly") or "httponly" in str(cookie._rest).lower() else "?"
        print(f"  {cookie.name}: Secure={secure} HttpOnly={httponly} Domain={cookie.domain}")
    if not cookies:
        print("  (No cookies set on initial request — check after login)")

    # ── Summary score ─────────────────────────────────────────────
    header_score = sum(results.get("headers", {}).values())
    total_score  = trust_score + header_score
    max_score    = len(trust_checks) + len(security_headers)

    print(f"\n{'='*40}")
    print(f"OVERALL SCORE: {total_score}/{max_score}")
    print(f"  Security headers: {header_score}/6")
    print(f"  Trust signals:    {trust_score}/9")

    if total_score >= 12:   print("Rating: GOOD ✓")
    elif total_score >= 8:  print("Rating: FAIR ⚠")
    else:                   print("Rating: POOR ✗")

    return results


if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else "https://example-store.com"
    audit_site(url)
```

Run against your Part A target:
```bash
python trust_checker.py https://your-chosen-site.com
```

Screenshot the full output.

---

## Part D — Privacy & Cookie Compliance Audit (25 pts)

Create `privacy_audit.md`. Evaluate your chosen site's compliance with **GDPR** and **CCPA**:

**1. Cookie Consent Management**

Visit the site from a fresh browser (incognito). Document:
- Does a cookie consent banner appear before any tracking cookies are set?
- Is there a "Reject All" option?
- Is consent granular (marketing, analytics, functional)?
- Is the consent mechanism dark-pattern-free?

Rate each on a 1–5 scale with evidence.

**2. Privacy Policy Assessment**

Find and read the privacy policy. Check for these required GDPR/CCPA elements:

| Element | Required by | Present? | Location in Policy |
|---------|------------|---------|-------------------|
| Data categories collected | GDPR Art. 13, CCPA | | |
| Purpose of processing | GDPR Art. 13 | | |
| Legal basis for processing | GDPR Art. 6 | | |
| Data retention periods | GDPR Art. 13 | | |
| Third-party sharing | CCPA, GDPR | | |
| Right to access | GDPR Art. 15, CCPA | | |
| Right to deletion | GDPR Art. 17, CCPA | | |
| Right to opt-out of sale | CCPA | | |
| Contact for data requests | GDPR, CCPA | | |
| Last updated date | Best practice | | |

**3. Third-Party Trackers**

Open browser DevTools → Network tab. Filter by third-party requests. List all tracking pixels and analytics tools you observe loading on the site.

**4. Compliance Rating**

Give an overall GDPR compliance score (1–10) and CCPA compliance score (1–10) with a 200-word justification.

---

## Part E — Security Recommendations (10 pts)

Based on your audit in Parts B, C, and D, write a **Security & Trust Improvement Report** (one page) in `security_audit.md`:

1. **Top 3 Security Fixes** — prioritized by risk, with implementation guidance
2. **Top 3 Trust Signal Additions** — with estimated conversion lift for each
3. **Privacy Compliance Gap** — most urgent fix needed

---

## Submission Checklist

- [ ] `security_audit.md` — Parts A, B, E complete
- [ ] `trust_checker.py` — runs against your target site
- [ ] Screenshot of `trust_checker.py` output
- [ ] `privacy_audit.md` — full cookie + privacy policy + third-party audit

---

## Grading

| Component | Points |
|-----------|--------|
| Part A — Target selection | 5 |
| Part B — OWASP checklist (passive analysis, findings documented) | 30 |
| Part C — trust_checker.py (runs, all sections output) | 30 |
| Part D — Privacy audit (cookie consent, policy, trackers) | 25 |
| Part E — Security recommendations (3+3+1, actionable) | 10 |
| **Total** | **100** |
