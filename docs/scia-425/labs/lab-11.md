---
title: "Lab 11: Compliance Testing & Regulatory Assurance"
course: SCIA-425
topic: Compliance Testing and Regulatory Assurance
week: 13
difficulty: ⭐⭐⭐
estimated_time: 85 minutes
---

# Lab 11: Compliance Testing & Regulatory Assurance

| Field | Details |
|---|---|
| **Course** | SCIA-425 — Software Assurance and Quality |
| **Week** | 13 |
| **Difficulty** | ⭐⭐⭐ Advanced |
| **Estimated Time** | 85 minutes |
| **Topic** | Compliance Testing and Regulatory Assurance |
| **Prerequisites** | Python 3.10+, `pip install pytest requests` |
| **Deliverables** | `asvs_checker.py`, `compliance_report.json`, `compliance_summary.md` |

---

## Overview

Regulatory compliance isn't a checkbox — it's a set of verifiable, testable requirements imposed by law or industry standards. In this lab you will automate compliance testing against **OWASP Application Security Verification Standard (ASVS) Level 1** requirements and simulate evidence collection for **HIPAA Technical Safeguards** using a test Flask application. Compliance testing bridges security engineering and audit.

---

## The System Under Test

```python
# test_target.py — A Flask app to test against (run this first)
from flask import Flask, request, jsonify, make_response
import os, hashlib, secrets, time

app = Flask(__name__)

# Simulated user store
USERS = {
    "alice": hashlib.sha256("CorrectPass123!".encode()).hexdigest(),
    "bob":   hashlib.sha256("BobSecure456#".encode()).hexdigest(),
}

# Simulated session store
SESSIONS = {}

# Rate limiting (simple in-memory)
LOGIN_ATTEMPTS = {}

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username", "")
    password = data.get("password", "")
    ip = request.remote_addr

    # Rate limiting
    now = time.time()
    attempts = [t for t in LOGIN_ATTEMPTS.get(ip, []) if now - t < 60]
    if len(attempts) >= 5:
        return jsonify({"error": "Rate limit exceeded"}), 429
    LOGIN_ATTEMPTS[ip] = attempts + [now]

    pw_hash = hashlib.sha256(password.encode()).hexdigest()
    if username in USERS and USERS[username] == pw_hash:
        token = secrets.token_hex(32)
        SESSIONS[token] = {"user": username, "created": now}
        resp = make_response(jsonify({"status": "ok"}))
        # Secure cookie attributes
        resp.set_cookie("session", token,
                       httponly=True, samesite="Strict",
                       max_age=1800)  # 30 minutes
        return resp
    return jsonify({"error": "Invalid credentials"}), 401

@app.route("/api/profile")
def profile():
    token = request.cookies.get("session", "")
    if token not in SESSIONS:
        return jsonify({"error": "Unauthorized"}), 401
    session = SESSIONS[token]
    # Check session expiry
    if time.time() - session["created"] > 1800:
        del SESSIONS[token]
        return jsonify({"error": "Session expired"}), 401
    return jsonify({"user": session["user"], "role": "standard"})

@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(port=5000, debug=False)
```

Start the target:
```bash
pip install flask
python test_target.py &
sleep 2
echo "Target running on http://localhost:5000"
```

---

## Part A — OWASP ASVS Level 1 Checker (40 pts)

ASVS Level 1 is the minimum standard for any application handling user data. Implement automated checks for the following ASVS requirements:

Create `asvs_checker.py`:

```python
import requests
import json
import time

BASE = "http://localhost:5000"
results = []

def check(control_id: str, title: str, requirement: str):
    """Decorator-style test runner."""
    def decorator(fn):
        try:
            passed, evidence = fn()
            status = "PASS" if passed else "FAIL"
        except Exception as e:
            passed, status, evidence = False, "ERROR", str(e)
        results.append({
            "control_id": control_id,
            "title": title,
            "requirement": requirement,
            "status": status,
            "evidence": evidence
        })
        icon = "✓" if passed else "✗"
        print(f"  [{icon}] {control_id} {title}: {status}")
        return fn
    return decorator

print("=== OWASP ASVS Level 1 Compliance Scan ===\n")

# ── V2: Authentication ──────────────────────────────────────────
print("V2 Authentication")

@check("V2.1.1", "Password Length",
       "Verify user-set passwords are at least 12 characters in length")
def v2_1_1():
    # Try to login with a short password — server should accept (we're not testing policy here,
    # we're testing that the server correctly rejects authentication, not password length enforcement
    # This control requires checking registration endpoint or policy documentation
    evidence = "Manual verification required — no registration endpoint in scope"
    return True, evidence  # Mark as requires manual review

@check("V2.1.6", "Password Strength Meter",
       "Verify that a password strength meter is provided")
def v2_1_6():
    evidence = "No registration endpoint — check UI implementation separately"
    return None, evidence

@check("V2.2.1", "Rate Limiting — Brute Force",
       "Verify that anti-automation controls are effective at mitigating breached credential testing, brute force, and account lockout attacks")
def v2_2_1():
    s = requests.Session()
    blocked = False
    for i in range(6):
        r = s.post(f"{BASE}/api/login",
                   json={"username": "alice", "password": "wrong_password"})
        if r.status_code == 429:
            blocked = True
            break
    evidence = f"After 6 attempts: HTTP {r.status_code} — {'rate limited' if blocked else 'NOT rate limited'}"
    return blocked, evidence

@check("V2.7.1", "Authentication Failure Response",
       "Verify that authentication failure responses do not indicate whether the username or password was incorrect")
def v2_7_1():
    r_bad_user = requests.post(f"{BASE}/api/login",
                               json={"username": "nonexistent_user_xyz", "password": "anything"})
    r_bad_pass = requests.post(f"{BASE}/api/login",
                               json={"username": "alice", "password": "wrong"})
    msg_bad_user = r_bad_user.json().get("error", "")
    msg_bad_pass = r_bad_pass.json().get("error", "")
    identical = msg_bad_user == msg_bad_pass
    evidence = f"Bad username: '{msg_bad_user}' | Bad password: '{msg_bad_pass}' | Same message: {identical}"
    return identical, evidence

# ── V3: Session Management ──────────────────────────────────────
print("\nV3 Session Management")

@check("V3.2.1", "Session Token Entropy",
       "Verify the application generates a new session token on user authentication")
def v3_2_1():
    r1 = requests.post(f"{BASE}/api/login", json={"username":"alice","password":"CorrectPass123!"})
    r2 = requests.post(f"{BASE}/api/login", json={"username":"alice","password":"CorrectPass123!"})
    t1 = r1.cookies.get("session", "")
    t2 = r2.cookies.get("session", "")
    unique = t1 != t2 and len(t1) >= 32
    evidence = f"Token 1: {t1[:16]}... | Token 2: {t2[:16]}... | Length: {len(t1)} | Unique: {unique}"
    return unique, evidence

@check("V3.4.1", "Cookie Security Attributes",
       "Verify that cookie-based session tokens have the 'Secure' attribute set")
def v3_4_1():
    # Note: Secure attribute requires HTTPS — we check HttpOnly and SameSite
    r = requests.post(f"{BASE}/api/login", json={"username":"alice","password":"CorrectPass123!"})
    cookie_header = r.headers.get("Set-Cookie", "")
    httponly = "httponly" in cookie_header.lower()
    samesite = "samesite" in cookie_header.lower()
    evidence = f"Set-Cookie header: {cookie_header[:100]} | HttpOnly: {httponly} | SameSite: {samesite}"
    return httponly and samesite, evidence

@check("V3.3.1", "Session Logout",
       "Verify that logout invalidates the session token")
def v3_3_1():
    # Log in, note token, then access profile — then check if server has expiry
    s = requests.Session()
    s.post(f"{BASE}/api/login", json={"username":"alice","password":"CorrectPass123!"})
    r = s.get(f"{BASE}/api/profile")
    auth_works = r.status_code == 200
    evidence = f"Profile access with valid session: HTTP {r.status_code} | Auth: {auth_works}"
    # Note: no /logout endpoint — report as gap
    return False, evidence + " | GAP: No /logout endpoint found"

# ── V4: Access Control ──────────────────────────────────────────
print("\nV4 Access Control")

@check("V4.1.1", "Authentication Required",
       "Verify that the application enforces access control rules on a trusted service layer")
def v4_1_1():
    r = requests.get(f"{BASE}/api/profile")
    denied = r.status_code == 401
    evidence = f"Unauthenticated access to /api/profile: HTTP {r.status_code}"
    return denied, evidence

# ── V9: Communications ──────────────────────────────────────────
print("\nV9 Communications")

@check("V9.1.1", "TLS Required",
       "Verify that TLS is used for all client connectivity and does not fall back to insecure protocols")
def v9_1_1():
    # Can't test TLS on localhost — mark as requires infrastructure review
    evidence = "Running on HTTP localhost — production deployment must enforce HTTPS/TLS 1.2+"
    return None, evidence

# ── Report ──────────────────────────────────────────────────────
print("\n=== Summary ===")
passed = sum(1 for r in results if r["status"] == "PASS")
failed = sum(1 for r in results if r["status"] == "FAIL")
errors = sum(1 for r in results if r["status"] in ("ERROR", None))
print(f"PASS: {passed} | FAIL: {failed} | MANUAL: {errors}")

with open("compliance_report.json", "w") as f:
    json.dump({
        "scan_target": BASE,
        "standard": "OWASP ASVS Level 1",
        "controls_tested": len(results),
        "results": results
    }, f, indent=2)
print("Report saved: compliance_report.json")
```

Run:
```bash
python asvs_checker.py
```

**You must also add 3 more ASVS checks** beyond the pre-written ones. Browse https://owasp.org/www-project-application-security-verification-standard/ to choose controls you can automate.

---

## Part B — HIPAA Technical Safeguards Evidence Collection (30 pts)

HIPAA §164.312 Technical Safeguards require documented evidence. Simulate evidence collection by creating `hipaa_evidence.py`:

```python
"""
HIPAA §164.312 Technical Safeguards Evidence Collection
Each control requires: description, evidence type, and pass/fail status
"""
import json, datetime, platform

evidence_log = []

def collect(control: str, title: str, evidence_type: str, automated: bool, fn):
    result = fn()
    entry = {
        "hipaa_control": control,
        "title": title,
        "evidence_type": evidence_type,
        "automated": automated,
        "collected_at": datetime.datetime.utcnow().isoformat(),
        "result": result
    }
    evidence_log.append(entry)
    icon = "✓" if result.get("compliant") else "✗"
    print(f"[{icon}] {control}: {title}")
    return result

# §164.312(a)(1) — Access Control
collect(
    "§164.312(a)(2)(i)", "Unique User Identification",
    "Automated API Test", True,
    lambda: {
        "compliant": True,
        "evidence": "Login endpoint requires unique username credential",
        "test": "POST /api/login with username+password returns session token"
    }
)

collect(
    "§164.312(a)(2)(iii)", "Automatic Logoff",
    "Configuration Review", True,
    lambda: {
        "compliant": True,
        "evidence": "Session max_age=1800 (30 minutes) enforced in Set-Cookie header",
        "test": "Set-Cookie: session=...; Max-Age=1800"
    }
)

collect(
    "§164.312(b)", "Audit Controls",
    "Log Inspection", False,
    lambda: {
        "compliant": None,
        "evidence": "MANUAL REVIEW REQUIRED: Audit log implementation not verifiable via API",
        "test": "Review application logs for authentication event capture"
    }
)

collect(
    "§164.312(c)(1)", "Integrity Controls",
    "Transport Inspection", True,
    lambda: {
        "compliant": None,
        "evidence": "PRODUCTION ONLY: TLS integrity protection requires HTTPS deployment",
        "test": "Verify TLS 1.2+ enforced with HSTS header in production"
    }
)

collect(
    "§164.312(d)", "Person Authentication",
    "Automated API Test", True,
    lambda: {
        "compliant": True,
        "evidence": "Authentication endpoint rejects unauthenticated access with HTTP 401",
        "test": "GET /api/profile without session token → 401 Unauthorized"
    }
)

# YOUR ADDITIONAL EVIDENCE (required):
# Add 2 more HIPAA controls with evidence collection

with open("hipaa_evidence.json", "w") as f:
    json.dump(evidence_log, f, indent=2)
print(f"\nEvidence log: {len(evidence_log)} controls, saved to hipaa_evidence.json")
```

---

## Part C — Compliance Summary Report (30 pts)

Write `compliance_summary.md`:

1. **ASVS Results Table** — all controls tested, pass/fail/manual
2. **HIPAA Gap Analysis** — which controls have evidence gaps and why
3. **Compliance Posture** — overall rating: Compliant / Partially Compliant / Non-Compliant with justification
4. **Remediation Priority** — top 3 gaps to fix first, with effort estimate
5. **Evidence Retention** — how long should compliance evidence be retained per HIPAA and why?

---

## Cleanup

```bash
# Stop the test server
pkill -f "python test_target.py"
```

---

## Submission Checklist

- [ ] `asvs_checker.py` — all pre-written + 3 custom checks
- [ ] `compliance_report.json` — generated by checker
- [ ] `hipaa_evidence.py` — all 5 controls + 2 custom
- [ ] `hipaa_evidence.json` — generated evidence log
- [ ] `compliance_summary.md` — all 5 sections

---

## Grading

| Component | Points |
|-----------|--------|
| Part A — asvs_checker.py (pre-written checks work + 3 custom) | 40 |
| Part B — hipaa_evidence.py (5 pre-written + 2 custom, evidence collected) | 30 |
| Part C — compliance_summary.md (all 5 sections, correct analysis) | 30 |
| **Total** | **100** |
