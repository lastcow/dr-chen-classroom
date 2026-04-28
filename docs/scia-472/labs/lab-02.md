---
title: "Lab 02: Passive Reconnaissance & OSINT"
course: SCIA-472
topic: Reconnaissance & OSINT
week: 2
difficulty: ⭐⭐
estimated_time: 60-75 minutes
tags:
  - osint
  - reconnaissance
  - whois
  - dns
  - passive-recon
  - google-dorking
  - certificate-transparency
---

# Lab 02: Passive Reconnaissance & OSINT

| Field | Details |
|---|---|
| **Course** | SCIA-472 — Hacking Exposed & Incident Response |
| **Topic** | Reconnaissance & OSINT |
| **Week** | 2 |
| **Difficulty** | ⭐⭐ Intermediate |
| **Estimated Time** | 60–75 minutes |
| **Tools** | Docker, Ubuntu 22.04, dnsutils, whois, curl, Python 3.11 |
| **Prerequisites** | Lab 01 complete; Docker installed and running |

---

!!! warning "Ethical Use"
    All attacks and scanning must ONLY target containers you create in this lab. Never scan or attack systems you do not own or have explicit written permission to test.

!!! warning "Reconnaissance Scope"
    Only use these techniques on domains you own or have explicit permission to test. Using `whois`, `dig`, and Google is legal on any public domain — but active scanning (`nmap`) against systems you don't own is **NOT**. This lab performs passive OSINT on `frostburg.edu` — our own institution's **public** DNS records.

---

## Overview

Professional reconnaissance collects maximum information about targets without triggering alarms. Passive recon uses publicly available sources — WHOIS, DNS records, certificate transparency logs, and Google dorking. Students gather intelligence on Frostburg State University's public infrastructure (ethical — it's our own institution) and a simulated internal target.

By the end of this lab you will be able to:

- Extract registrar and ownership data from WHOIS records
- Enumerate DNS A, MX, NS, and TXT records for intelligence value
- Identify email security posture via SPF and DMARC records
- Attempt and interpret zone transfer responses
- Enumerate subdomains using brute-force and certificate transparency
- Build a structured OSINT intelligence report

---

## Part 1 — WHOIS Domain Intelligence

WHOIS exposes registrar, organization, contact, and nameserver information. Attackers use this to identify the organization's ISP, hosting provider, and key infrastructure.

### Step 1.1 — Start the OSINT Container

```bash
docker run --rm -it ubuntu:22.04 bash
apt-get update -qq && apt-get install -y -qq dnsutils whois curl 2>/dev/null
echo 'OSINT tools ready'
```

> **Note:** All subsequent commands in Parts 1–3 run **inside this container**. Keep the session open.

---

### Step 1.2 — WHOIS Lookup on frostburg.edu

```bash
whois frostburg.edu 2>/dev/null | grep -E 'Registrar:|Registered|Expir|Name Server|Organization|State' | head -15
```

**Expected output:** Registrar info, name servers, registration and expiration dates.

📸 **Screenshot checkpoint:** Capture WHOIS output showing organization and nameservers — label this **02a**.

---

### Step 1.3 — WHOIS on a Commercial Domain

```bash
whois github.com 2>/dev/null | grep -E 'Registrar:|Organization:|Name Server:|Creation|Expir' | head -10
```

📸 **Screenshot checkpoint:** Capture GitHub WHOIS output for comparison — append to **02a**.

---

## Part 2 — DNS Intelligence

DNS records are a goldmine of infrastructure intelligence. Each record type reveals different attack surface.

### Step 2.1 — A Records (IP Addresses)

```bash
dig frostburg.edu A +short
dig google.com A +short
```

**Expected output:** IP addresses for each domain.

---

### Step 2.2 — Mail Server Records

```bash
dig frostburg.edu MX +short
dig google.com MX +short
```

**Expected output:** Mail server hostnames. Attackers use MX records to identify email providers and build phishing infrastructure that mimics the same platform.

---

### Step 2.3 — Name Servers

```bash
dig frostburg.edu NS +short
```

**Expected output:** Primary nameservers. Attackers test discovered nameservers for zone transfer vulnerabilities.

📸 **Screenshot checkpoint:** Capture A, MX, and NS record output together — label this **02b**.

---

### Step 2.4 — Text Records (SPF, DMARC, DKIM — Email Security)

```bash
dig frostburg.edu TXT +short
dig _dmarc.frostburg.edu TXT +short
```

**Expected output:** SPF record showing authorized mail senders. Absence of DMARC (or `p=none`) means the domain can be spoofed in phishing emails.

📸 **Screenshot checkpoint:** Capture TXT, SPF, and DMARC output — label this **02c**.

---

### Step 2.5 — Zone Transfer Attempt

Zone transfers (`AXFR`) are meant for replication between authoritative DNS servers. Misconfigured servers leak the **entire DNS zone** — every hostname in the domain.

```bash
NS=$(dig frostburg.edu NS +short | head -1)
echo "Attempting zone transfer from: $NS"
dig axfr @$NS frostburg.edu 2>&1 | head -5
```

**Expected output:** `Transfer failed` or `REFUSED` — properly configured DNS servers block zone transfers from unauthorized sources.

📸 **Screenshot checkpoint:** Capture the zone transfer refused/failed message — label this **02d**.

---

## Part 3 — Subdomain Enumeration

Subdomains reveal internal services, legacy applications, and forgotten infrastructure. Two methods: brute-force guessing and passive certificate transparency.

### Step 3.1 — Common Subdomain Guessing

```bash
for sub in www mail smtp ftp vpn remote portal login admin; do
  ip=$(dig $sub.frostburg.edu A +short 2>/dev/null)
  if [ -n "$ip" ]; then
    echo "FOUND: $sub.frostburg.edu -> $ip"
  else
    echo "NOT FOUND: $sub.frostburg.edu"
  fi
done
```

📸 **Screenshot checkpoint:** Capture all subdomain probe results (FOUND and NOT FOUND) — label this **02e**.

---

### Step 3.2 — Certificate Transparency Logs (Passive — No Scanning)

Certificate Transparency (CT) logs are public records of every SSL/TLS certificate issued. They expose subdomains **without sending a single packet to the target**.

```bash
curl -s 'https://crt.sh/?q=%.frostburg.edu&output=json' 2>/dev/null | \
  python3 -c "import sys,json; data=json.load(sys.stdin); [print(d['name_value']) for d in data[:15]]" 2>/dev/null || \
  echo 'Certificate transparency: https://crt.sh/?q=%.frostburg.edu (view in browser)'
```

**Expected output:** List of subdomains from SSL certificate history. Every certificate ever issued for `*.frostburg.edu` is publicly logged.

📸 **Screenshot checkpoint:** Capture CT log results or browser URL — append to **02e**.

---

## Part 4 — Google Dorking (Passive Intelligence)

Google indexes publicly accessible files and pages. Dork queries use advanced search operators to find sensitive content that was never meant to be public.

### Step 4.1 — Google Dork Syntax Reference

```bash
docker run --rm python:3.11-slim python3 -c "
dorks = [
    ('site:frostburg.edu filetype:pdf',     'Find public PDFs on the domain'),
    ('site:frostburg.edu inurl:login',      'Find login pages'),
    ('site:frostburg.edu inurl:admin',      'Find admin panels'),
    ('site:frostburg.edu filetype:xls',     'Find exposed spreadsheets'),
    ('\"frostburg.edu\" filetype:sql',        'Find database dumps (dangerous!)'),
    ('inurl:\"wp-login.php\" site:frostburg.edu', 'WordPress login pages'),
    ('site:pastebin.com frostburg',         'Leaked data on Pastebin'),
]
print('=== GOOGLE DORK EXAMPLES ===')
print('(Copy-paste into Google — never automated against Google)')
print()
for dork, purpose in dorks:
    print(f'Query:   {dork}')
    print(f'Purpose: {purpose}')
    print()"
```

> **Note:** Copy these queries into a browser manually. Never automate Google searches — it violates their ToS and may result in IP blocks.

📸 **Screenshot checkpoint:** Capture the full dork reference list — label this **02f**.

---

## Part 5 — Simulated OSINT Report

A professional OSINT engagement ends with a compiled intelligence report. This synthesizes all gathered data into actionable findings.

### Step 5.1 — Compile Intelligence into a Report

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq dnsutils 2>/dev/null
python3 -c \"
print('=== OSINT INTELLIGENCE REPORT ===')
print('Target: frostburg.edu')
print('Classification: PUBLIC DOMAIN - Educational Institution')
print()
print('--- DNS Intelligence ---')
import subprocess
try:
    ns = subprocess.check_output(['dig','frostburg.edu','NS','+short'], text=True, timeout=5).strip()
    print(f'Nameservers: {ns[:80] if ns else \"lookup failed\"}')
except: print('Nameservers: (DNS lookup)')
try:
    mx = subprocess.check_output(['dig','frostburg.edu','MX','+short'], text=True, timeout=5).strip()
    print(f'Mail servers: {mx[:80] if mx else \"not found\"}')
except: print('Mail servers: (MX lookup)')
print()
print('--- Risk Assessment ---')
print('[HIGH]   Zone transfer: Test if REFUSED (should be)')
print('[MEDIUM] SPF/DMARC: Verify email spoofing protections')
print('[LOW]    Exposed subdomains: Document all live subdomains')
print('[INFO]   Certificate transparency: All issued certs visible')
print()
print('Recon Status: PASSIVE PHASE COMPLETE')
print('Next Phase:   Active scanning (requires written authorization)')
\""
```

📸 **Screenshot checkpoint:** Capture the full compiled OSINT intelligence report — label this **02g**.

---

## Cleanup

```bash
docker system prune -f
```

---

## Assessment

### Screenshot Checklist

| Label | Required Screenshot | Points |
|---|---|---|
| **02a** | WHOIS output — registrar, nameservers, dates (frostburg.edu + github.com) | 6 |
| **02b** | DNS records — A, MX, NS for frostburg.edu | 6 |
| **02c** | TXT / SPF / DMARC records | 6 |
| **02d** | Zone transfer REFUSED or failed message | 6 |
| **02e** | Subdomain enumeration results + CT log output | 6 |
| **02f** | Google dork reference list (all 7 queries) | 5 |
| **02g** | Compiled OSINT intelligence report | 5 |
| **Total** | | **40** |

---

### Analysis (20 points)

Write a complete **5-section OSINT Intelligence Report** for `frostburg.edu` using your collected data:

1. **Target Summary** — Organization, registrar, hosting provider
2. **DNS Infrastructure** — A, MX, NS records and their security implications
3. **Email Security Posture** — SPF and DMARC findings; phishing risk assessment
4. **Exposed Subdomains** — Live subdomains discovered; risk for each
5. **Recommendations** — Top 3 remediation priorities with justification

---

### Reflection Questions (40 points — 10 points each)

1. You found that `frostburg.edu`'s DNS zone transfer is `REFUSED`. If zone transfers **were** allowed, what information could an attacker harvest and why would that be dangerous?

2. DMARC and SPF records prevent email spoofing. If a domain has no DMARC record (or `p=none`), what can an attacker do? Why is email a primary initial access vector?

3. Certificate Transparency logs are public and passive — no scanning required. How does this help attackers discover subdomains without any active probing? What does this mean for "security through obscurity"?

4. Passive reconnaissance (WHOIS, DNS, Google) is completely legal on any domain. At what point does reconnaissance **become illegal** under the Computer Fraud and Abuse Act? Where is the legal line between passive OSINT and unauthorized access?

---

!!! tip "Grading Rubric"
    | Component | Points |
    |---|---|
    | Screenshots (02a–02g, all visible and labeled) | 40 |
    | OSINT Intelligence Report (complete 5-section report) | 20 |
    | Reflection questions (4 × 10 pts, substantive answers) | 40 |
    | **Total** | **100** |
