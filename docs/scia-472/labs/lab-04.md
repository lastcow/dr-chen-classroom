---
title: "Lab 04: Vulnerability Assessment & CVSS Scoring"
course: SCIA-472
topic: Vulnerability Assessment
week: 4
difficulty: ⭐⭐
estimated_time: 60-75 minutes
tags:
  - vulnerability-assessment
  - cvss
  - nikto
  - nmap-nse
  - dvwa
  - risk-scoring
  - docker
---

# Lab 04: Vulnerability Assessment & CVSS Scoring

| Field | Details |
|---|---|
| **Course** | SCIA-472 — Hacking Exposed & Incident Response |
| **Topic** | Vulnerability Assessment |
| **Week** | 4 |
| **Difficulty** | ⭐⭐ Intermediate |
| **Estimated Time** | 60–75 minutes |
| **Tools** | Docker, Ubuntu 22.04, Nikto, `instrumentisto/nmap`, Python 3.11 |
| **Target** | `vulnerables/web-dvwa` (isolated Docker network `vulnlab`) |
| **Prerequisites** | Labs 01–03 complete; Docker installed and running |

---

!!! warning "Ethical Use"
    All attacks and scanning must ONLY target containers you create in this lab. Never scan or attack systems you do not own or have explicit written permission to test.

---

## Overview

After scanning, pentesters assess which vulnerabilities can actually be exploited. This lab combines Nmap vulnerability scripts, Nikto web scanning, and CVSS v3.1 scoring to prioritize findings by risk. Students learn to distinguish **scanning** from **testing** and build a structured vulnerability report.

By the end of this lab you will be able to:

- Run Nikto web scanner and interpret its output
- Apply Nmap NSE vulnerability scripts against web targets
- Calculate and interpret CVSS v3.1 base scores
- Decode a CVSS vector string component by component
- Distinguish vulnerability scanning from penetration testing
- Produce a risk-prioritized vulnerability assessment report

---

## Part 1 — Lab Setup

### Step 1.1 — Create Lab Network and Start Target

```bash
docker network create vulnlab
docker run -d \
  --name vuln-target \
  --network vulnlab \
  vulnerables/web-dvwa
sleep 5
docker inspect vuln-target | grep '"IPAddress"' | tail -1
```

**Note the target IP address** — you will need it for Nmap scans in Part 3.

📸 **Screenshot checkpoint:** Capture the `docker inspect` output showing the target IP address — label this **04a**.

---

## Part 2 — Nikto Web Vulnerability Scanner

Nikto is an open-source web server scanner that tests for over 6700 potentially dangerous files and programs, outdated server software, and server configuration issues.

### Step 2.1 — Run Nikto Against DVWA

```bash
docker run --rm --network vulnlab ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq nikto 2>/dev/null
nikto -host http://vuln-target -maxtime 60 2>&1 | grep -v '^$' | head -40"
```

**Expected output:** Outdated Apache version detected, missing security headers (`X-Frame-Options`, `X-Content-Type-Options`), potential vulnerabilities, OSVDB references.

📸 **Screenshot checkpoint:** Capture the Nikto scan results (first 40 lines of findings) — label this **04b**.

---

### Step 2.2 — Nikto with Specific Checks

```bash
docker run --rm --network vulnlab ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq nikto 2>/dev/null
nikto -host http://vuln-target -Tuning 9 2>&1 | grep -E 'OSVDB|CVE|\+' | head -20"
```

**Expected output:** OSVDB references and vulnerability IDs extracted from the scan.

📸 **Screenshot checkpoint:** Capture the filtered Nikto vulnerability findings — append to **04b**.

---

## Part 3 — Nmap Vulnerability Scripts

NSE vulnerability scripts go beyond enumeration — they actively check for specific known vulnerabilities.

### Step 3.1 — HTTP Vulnerabilities with NSE

```bash
docker run --rm --network vulnlab instrumentisto/nmap \
  nmap --script=http-shellshock,http-phpself-xss,http-internal-ip-disclosure \
  10.10.0.0/24 -p 80
```

> Use the actual target IP from Step 1.1 if the /24 sweep is slow.

**Expected output:** Script results for each vulnerability check — vulnerable / not vulnerable status.

📸 **Screenshot checkpoint:** Capture the NSE vulnerability script output — label this **04c**.

---

### Step 3.2 — Check for Common Web Vulnerabilities

```bash
docker run --rm --network vulnlab instrumentisto/nmap \
  nmap --script="http-vuln*" -p 80 vuln-target 2>/dev/null | head -30
```

📸 **Screenshot checkpoint:** Capture the http-vuln wildcard script results — append to **04c**.

---

## Part 4 — CVSS v3.1 Scoring

The Common Vulnerability Scoring System (CVSS) v3.1 provides a standardized method for rating the severity of security vulnerabilities. Scores range from 0.0 to 10.0.

| Score Range | Severity |
|---|---|
| 0.0 | None |
| 0.1 – 3.9 | Low |
| 4.0 – 6.9 | Medium |
| 7.0 – 8.9 | High |
| 9.0 – 10.0 | Critical |

### Step 4.1 — CVSS Scoring Calculator

```bash
docker run --rm python:3.11-slim python3 -c "
# CVSS v3.1 Base Score calculation
def cvss_severity(score):
    if score == 0: return 'None'
    elif score < 4.0: return 'Low'
    elif score < 7.0: return 'Medium'
    elif score < 9.0: return 'High'
    else: return 'Critical'

vulnerabilities = [
    {
        'name': 'SQL Injection (DVWA Login)',
        'cve': 'CWE-89',
        'vector': 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H',
        'score': 9.8,
        'description': 'Network-exploitable SQLi, no privileges needed, all 3 CIA pillars',
    },
    {
        'name': 'Outdated Apache 2.4.25',
        'cve': 'CVE-2017-7679',
        'vector': 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H',
        'score': 9.8,
        'description': 'Remote buffer overflow in mod_mime - no auth required',
    },
    {
        'name': 'Missing X-Frame-Options Header',
        'cve': 'CWE-693',
        'vector': 'CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N',
        'score': 6.1,
        'description': 'Clickjacking possible - requires user interaction',
    },
    {
        'name': 'Default Credentials (admin/password)',
        'cve': 'CWE-521',
        'vector': 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H',
        'score': 9.8,
        'description': 'Network-accessible with default credentials = full compromise',
    },
]

vulnerabilities.sort(key=lambda x: -x['score'])
print('=== VULNERABILITY ASSESSMENT REPORT ===')
print(f'{\"Risk\":<10} {\"Score\":<7} {\"Finding\":<35} {\"CVE/CWE\"}')
print('-' * 75)
for v in vulnerabilities:
    sev = cvss_severity(v['score'])
    print(f'{sev:<10} {v[\"score\"]:<7} {v[\"name\"]:<35} {v[\"cve\"]}')
    print(f'{\"\":<17} {v[\"description\"]}')
    print()
print(f'Total findings: {len(vulnerabilities)}')
print(f'Critical: {sum(1 for v in vulnerabilities if v[\"score\"] >= 9.0)}')
print(f'High:     {sum(1 for v in vulnerabilities if 7.0 <= v[\"score\"] < 9.0)}')
print(f'Medium:   {sum(1 for v in vulnerabilities if 4.0 <= v[\"score\"] < 7.0)}')
"
```

📸 **Screenshot checkpoint:** Capture the prioritized vulnerability report sorted by CVSS score — label this **04d**.

---

### Step 4.2 — CVSS Vector Component Breakdown

```bash
docker run --rm python:3.11-slim python3 -c "
vector = 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H'
components = {
    'AV': {'N': 'Network (remotely exploitable)',  'A': 'Adjacent', 'L': 'Local', 'P': 'Physical'},
    'AC': {'L': 'Low (easy to exploit)',           'H': 'High (hard to exploit)'},
    'PR': {'N': 'None (no account needed)',        'L': 'Low privileges', 'H': 'High privileges'},
    'UI': {'N': 'None (no user action needed)',    'R': 'Required (user must click)'},
    'S':  {'U': 'Unchanged (limited to component)', 'C': 'Changed (affects other systems)'},
    'C':  {'N': 'None', 'L': 'Low impact', 'H': 'High impact on Confidentiality'},
    'I':  {'N': 'None', 'L': 'Low impact', 'H': 'High impact on Integrity'},
    'A':  {'N': 'None', 'L': 'Low impact', 'H': 'High impact on Availability'},
}
metrics = dict(x.split(':') for x in vector.split('/')[1:])
print('=== CVSS v3.1 VECTOR BREAKDOWN ===')
print(f'Vector: {vector}')
print()
for metric, value in metrics.items():
    desc = components.get(metric, {}).get(value, 'Unknown')
    print(f'  {metric}:{value} = {desc}')
print()
print('Score: 9.8 (Critical) - Network, Low Complexity, No Auth, Full CIA impact')
"
```

📸 **Screenshot checkpoint:** Capture the CVSS vector breakdown with all 8 metric explanations — label this **04e**.

---

## Part 5 — Vulnerability Scanning vs Penetration Testing

Understanding the **distinction** between these two activities is critical — they have different scopes, impacts, and authorization requirements.

### Step 5.1 — Side-by-Side Comparison

```bash
docker run --rm python:3.11-slim python3 -c "
comparison = {
    'Vulnerability Scanning': {
        'What it does':  'Automated tool identifies potential vulnerabilities',
        'Verification':  'Does NOT prove exploitability - many false positives',
        'Impact':        'Non-invasive - reads banners and checks configurations',
        'Output':        'List of potential issues with CVSS scores',
        'Tools':         'Nessus, OpenVAS, Nikto, nmap --script',
        'Analogy':       'Checking if doors look locked without testing the handle',
    },
    'Penetration Testing': {
        'What it does':  'Human tester actively attempts to exploit vulnerabilities',
        'Verification':  'Proves real exploitability with working proof-of-concept',
        'Impact':        'Invasive - may crash services, trigger alerts',
        'Output':        'Exploited vulnerabilities with business impact analysis',
        'Tools':         'Metasploit, Burp Suite, custom exploits',
        'Analogy':       'Picking the lock and walking inside to prove access',
    },
}
for test_type, details in comparison.items():
    print(f'=== {test_type.upper()} ===')
    for k, v in details.items():
        print(f'  {k:<15}: {v}')
    print()
"
```

📸 **Screenshot checkpoint:** Capture the full vulnerability scanning vs penetration testing comparison — label this **04f**.

---

## Cleanup

```bash
docker stop vuln-target && docker rm vuln-target
docker network rm vulnlab
docker system prune -f
```

---

## Assessment

### Screenshot Checklist

| Label | Required Screenshot | Points |
|---|---|---|
| **04a** | Target IP address from `docker inspect` | 7 |
| **04b** | Nikto scan output (findings + OSVDB references) | 7 |
| **04c** | NSE vulnerability script results (http-shellshock, http-vuln*) | 7 |
| **04d** | Prioritized CVSS vulnerability report (sorted by score) | 7 |
| **04e** | CVSS v3.1 vector breakdown (all 8 metrics explained) | 6 |
| **04f** | Vulnerability scanning vs penetration testing comparison | 6 |
| **Total** | | **40** |

---

### Analysis (20 points)

Complete a **Vulnerability Assessment Report** with all findings from this lab:

| # | Finding | Tool Discovered | CVSS Score | Severity | Vector | Remediation |
|---|---|---|---|---|---|---|
| 1 | SQL Injection | Nikto / Manual | 9.8 | Critical | `AV:N/AC:L/PR:N/UI:N` | Parameterized queries |
| 2 | Outdated Apache 2.4.25 | Nmap `-sV` | 9.8 | Critical | `AV:N/AC:L/PR:N/UI:N` | Update to current release |
| 3 | Default Credentials | Nikto | 9.8 | Critical | `AV:N/AC:L/PR:N/UI:N` | Change immediately; enforce policy |
| 4 | Missing X-Frame-Options | Nikto | 6.1 | Medium | `AV:N/AC:L/PR:N/UI:R` | Add header in Apache config |
| 5 | *(Add any additional Nikto/NSE findings from your scan)* | | | | | |

Include a **Remediation Priority** section explaining which items to fix first and why.

---

### Reflection Questions (40 points — 10 points each)

1. Nikto reported `Missing X-Content-Type-Options header` as a finding (CVSS ~5.3, Medium). Should a security team spend **equal effort** remediating this as the SQL injection (CVSS 9.8)? How do you prioritize remediation when resources are limited?

2. A vulnerability scanner found that Apache 2.4.25 has 15 CVEs. Does this mean the server is **definitely vulnerable** to all 15? What factors determine whether a listed CVE is actually exploitable in a specific environment?

3. Explain the difference between a **false positive** and a **false negative** in vulnerability scanning. Which is more dangerous from a security standpoint, and why?

4. CVSS scores the **technical** severity of a vulnerability, but organizations use "risk ratings" that incorporate business context. A Critical CVSS 9.8 vulnerability on an internet-facing production server vs. the same vulnerability on an isolated offline test machine — how should each be prioritized differently, and what additional factors beyond CVSS should influence that decision?

---

!!! tip "Grading Rubric"
    | Component | Points |
    |---|---|
    | Screenshots (04a–04f, all visible and labeled) | 40 |
    | Completed vulnerability report (all findings with CVSS, vector, and remediation) | 20 |
    | Reflection questions (4 × 10 pts, substantive answers) | 40 |
    | **Total** | **100** |
