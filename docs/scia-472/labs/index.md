# SCIA-472 Hands-On Labs

**Course:** SCIA-472 · Hacking Exposed & Incident Response  
**Frostburg State University — Department of Computer Science & Information Technology**

---

## Lab Program Overview

This lab series provides **13 Docker-based hands-on exercises** that cover the complete offensive and defensive security lifecycle: reconnaissance through exploitation, incident response, malware analysis, and digital forensics — all in isolated, legal, contained environments.

!!! warning "Ethical Use Policy"
    All attacks, scans, and exploitation techniques in this lab series **must only target containers you create during each lab**. Scanning or attacking any system you do not own or have explicit written permission to test is a federal crime under the Computer Fraud and Abuse Act (CFAA). These labs are designed for educational use in isolated Docker environments only.

!!! info "What You Need"
    - A computer running **Windows 10/11**, **macOS**, or **Linux**
    - **Docker Desktop** installed — [Download here](https://www.docker.com/products/docker-desktop)
    - A terminal (PowerShell on Windows, Terminal on macOS/Linux)
    - Approximately **1–1.5 hours** per lab (Lab 13: 2 hours)

---

## Lab Schedule

| Lab | Title | Week | Topic | Difficulty | Time |
|-----|-------|------|--------|------------|------|
| [**Lab 01**](lab-01.md) | Ethical Hacking Framework — Kill Chain, ATT&CK & Methodology | 1 | Foundations | ⭐ | 45–60 min |
| [**Lab 02**](lab-02.md) | Passive Reconnaissance & OSINT | 2 | Reconnaissance | ⭐⭐ | 60–75 min |
| [**Lab 03**](lab-03.md) | Network Scanning & Enumeration with Nmap | 3 | Scanning | ⭐⭐ | 60–75 min |
| [**Lab 04**](lab-04.md) | Vulnerability Assessment & CVSS Scoring | 4 | Vuln Assessment | ⭐⭐ | 60–75 min |
| [**Lab 05**](lab-05.md) | Exploitation Fundamentals — Metasploit Framework | 5 | Exploitation | ⭐⭐⭐ | 75–90 min |
| [**Lab 06**](lab-06.md) | Web Application Attacks — SQL Injection & XSS | 6 | Web Security | ⭐⭐⭐ | 75–90 min |
| [**Lab 07**](lab-07.md) | Password Attacks & Credential Exploitation | 8 | Credential Attacks | ⭐⭐⭐ | 75–90 min |
| [**Lab 08**](lab-08.md) | Social Engineering & Phishing Analysis | 9 | Human Factor | ⭐⭐ | 60–75 min |
| [**Lab 09**](lab-09.md) | Post-Exploitation & Persistence Mechanisms | 10 | Post-Exploit | ⭐⭐⭐ | 75–90 min |
| [**Lab 10**](lab-10.md) | Malware Analysis — Static & Dynamic Techniques | 11 | Malware Analysis | ⭐⭐⭐ | 75–90 min |
| [**Lab 11**](lab-11.md) | Incident Response — Detection, Triage & SIEM | 12 | IR Phase 1–2 | ⭐⭐⭐ | 75–90 min |
| [**Lab 12**](lab-12.md) | Digital Forensics — Disk Imaging & Evidence | 14 | Forensics | ⭐⭐⭐ | 75–90 min |
| [**Lab 13**](lab-13.md) | Capstone — Full Attack Chain & IR Report | 15 | All Topics | ⭐⭐⭐⭐ | 120–150 min |

---

## Learning Progression

```
Labs 01–04           Labs 05–07          Labs 08–09          Labs 10–12         Lab 13
Foundations &    →   Active Attack   →   Human Factor &  →   Analysis &     →  Capstone
Reconnaissance       Techniques          Post-Exploit        Response           Integration
Kill Chain, OSINT,   Metasploit,         Phishing,           Malware, SIEM,     Full attack
Nmap, CVSS          SQLi, XSS,          Persistence,        Forensics, IR      chain + report
                     Password attacks    Lateral movement
```

---

## Key Docker Images Used

| Image | Used In | Purpose |
|-------|---------|---------|
| `vulnerables/web-dvwa` | Labs 03, 04, 05, 06, 13 | Deliberately vulnerable web app target |
| `instrumentisto/nmap` | Labs 03, 04, 13 | Network scanning |
| `metasploitframework/metasploit-framework` | Lab 05 | Exploitation framework |
| `ubuntu:22.04` | Labs 02–13 | Base for most tool installations |
| `python:3.11-slim` | Labs 01, 02, 04, 07–13 | Python analysis scripts |
| `httpd:alpine` | Lab 11 | HTTP server for IR lab |

---

## Assessment Structure

Each lab is worth **100 points**:

| Component | Points |
|-----------|--------|
| Screenshot submission (5–10 per lab, labeled) | 40 |
| Analysis deliverable (report, table, timeline) | 20 |
| Reflection questions (4 per lab) | 40 |

**Lab 13 (Capstone):** Screenshots+findings (30) + ATT&CK mapping (20) + SIEM alerts (20) + Essay (30) = 100

---

## Ethical Framework

Every lab begins with an ethical use reminder. Professional penetration testers operate under:

1. **Written Authorization** — signed scope agreement from system owner
2. **Defined Scope** — explicit list of permitted targets, IP ranges, and test types
3. **Rules of Engagement** — what is allowed, what is prohibited, emergency contacts
4. **Reporting Obligation** — all findings documented and reported to the client

The skills you learn in this course are identical to what real attackers use. The only difference is authorization and intent.

---

## Quick Start

```bash
# Verify Docker is ready
docker --version
docker run --rm hello-world

# Pull the main target image for Labs 03-06
docker pull vulnerables/web-dvwa
```

Start with [Lab 01 →](lab-01.md)

---

*Labs authored for SCIA-472 · Frostburg State University · Department of Computer Science & Information Technology · Spring 2026*
