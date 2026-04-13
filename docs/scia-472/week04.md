---
title: "Week 4 — Vulnerability Assessment"
description: Systematic vulnerability identification using scanners, CVE databases, and manual analysis to prioritize remediation.
---

# Week 4 — Vulnerability Assessment

<div class="week-meta" markdown>
**Course Objectives:** CO1, CO2 &nbsp;|&nbsp; **Focus:** Vulnerability Analysis &nbsp;|&nbsp; **Difficulty:** ⭐⭐☆☆☆
</div>

---

## Learning Objectives

- [ ] Operate Nessus and OpenVAS to perform automated vulnerability scans
- [ ] Interpret CVSS scores and prioritize findings by risk severity
- [ ] Distinguish between vulnerability scanning and penetration testing
- [ ] Search and utilize CVE, NVD, and Exploit-DB for vulnerability research
- [ ] Produce a vulnerability assessment report with risk ratings and remediation guidance

---

## 1. Vulnerability Assessment vs. Penetration Testing

These terms are frequently confused — they are distinct activities:

| Dimension | Vulnerability Assessment | Penetration Testing |
|-----------|-------------------------|---------------------|
| **Goal** | Identify and catalog weaknesses | Exploit weaknesses to measure impact |
| **Depth** | Broad — enumerate all vulnerabilities | Deep — follow attack chains |
| **Exploitation** | **Never** (passive) | Yes (authorized) |
| **Output** | List of vulnerabilities with CVSS scores | Demonstrated attack paths + business impact |
| **Frequency** | Continuous / quarterly | Annually or after major changes |
| **Duration** | Hours to days | Days to weeks |
| **Skill Level** | Can be automated | Requires expert judgment |

---

## 2. Common Vulnerability Scoring System (CVSS)

CVSS v3.1 is the industry standard for quantifying vulnerability severity. Understanding scores is essential for risk prioritization.

### CVSS v3.1 Score Ranges

| Score | Severity | Action |
|-------|----------|--------|
| 9.0 – 10.0 | **Critical** | Patch immediately / emergency response |
| 7.0 – 8.9 | **High** | Patch within 30 days |
| 4.0 – 6.9 | **Medium** | Patch within 90 days |
| 0.1 – 3.9 | **Low** | Patch in next maintenance window |
| 0.0 | **None** | Informational |

### CVSS v3.1 Base Metrics

```
ATTACK VECTOR (AV)          ATTACK COMPLEXITY (AC)
  Network (N) = worst          Low (L) = easier to exploit
  Adjacent (A)                 High (H)
  Local (L)
  Physical (P) = best       PRIVILEGES REQUIRED (PR)
                               None (N) = worse
SCOPE (S)                      Low (L)
  Unchanged (U)                High (H)
  Changed (C) = worse       
                            USER INTERACTION (UI)
CONFIDENTIALITY (C)            None (N) = worse
INTEGRITY (I)                  Required (R)
AVAILABILITY (A)
  None / Low / High
```

**Example — EternalBlue (MS17-010):** CVSS 9.8 Critical
- AV:Network, AC:Low, PR:None, UI:None, S:Unchanged, C:High, I:High, A:High

---

## 3. Nessus Vulnerability Scanner

Nessus (Tenable) is the most widely used commercial vulnerability scanner.

### Scan Policy Configuration

```
Scan Templates:
─────────────────────────────────────
Basic Network Scan         → Quick overview, safe checks only
Advanced Scan              → Full plugin set, credential-based
Credentialed Patch Audit   → Deep OS/application patch status
Web Application Tests      → HTTP-focused scanning
PCI DSS Compliance         → Payment card industry compliance
CIS Benchmark Audit        → Configuration hardening checks
```

### Credentialed vs. Uncredentialed Scans

!!! info "Credentialed Scanning = 10x More Findings"
    An uncredentialed scan sees only what's exposed over the network. A credentialed scan (with local admin or root) inspects installed software, patch levels, registry settings, and configurations — finding 3-10x more vulnerabilities.

```
Uncredentialed:   Open ports, service versions, network-level vulns
Credentialed:     + Patch status, installed apps, local users,
                    file permissions, registry settings, config files
```

### Interpreting Nessus Output

```
Plugin ID: 57608
Name: SMBv1 Protocol Detection
Severity: Medium (CVSS 5.3)
Description: The remote host supports SMBv1, which has known 
             critical vulnerabilities including MS17-010 (EternalBlue).
Solution: Disable SMBv1 on all Windows hosts.
See Also: https://support.microsoft.com/en-us/kb/2696547

Affected Hosts: 192.168.1.10, 192.168.1.15, 192.168.1.23
```

---

## 4. OpenVAS — Open Source Alternative

OpenVAS (Open Vulnerability Assessment System) is the free/open-source alternative:

```bash
# Start OpenVAS services
gvm-start

# Access web interface at https://localhost:9392

# Command-line scan with gvm-cli
gvm-cli socket --gmp-username admin --gmp-password admin \
  --xml "<get_tasks/>"

# Key concepts:
# Targets → Define hosts to scan
# Scan Config → Plugin sets (Full and Fast, Full, etc.)
# Tasks → Combine target + config into a scan job
# Reports → XML/PDF output with findings
```

---

## 5. CVE, NVD & Exploit-DB

### CVE — Common Vulnerabilities and Exposures

The CVE system (MITRE) assigns unique identifiers to publicly known vulnerabilities:

```
Format: CVE-[YEAR]-[NUMBER]
Example: CVE-2021-44228  (Log4Shell — Apache Log4j RCE)
         CVE-2021-34527  (PrintNightmare — Windows Print Spooler RCE)
         CVE-2017-0144   (EternalBlue — SMBv1 RCE)
```

**NVD (National Vulnerability Database)** — NIST enriches CVEs with CVSS scores, CPE mappings, and references:
```
https://nvd.nist.gov/vuln/detail/CVE-2021-44228
```

### Exploit-DB

Exploit-DB (Offensive Security) catalogs public exploits linked to CVEs:

```bash
# searchsploit — offline Exploit-DB search tool
searchsploit apache 2.4.49          # Search for Apache exploit
searchsploit -m 50383               # Mirror (download) exploit #50383
searchsploit --cve CVE-2021-41773  # Search by CVE number

# Output:
# Apache HTTP Server 2.4.49 - Path Traversal & RCE | multiple/webapps/50383.sh
# Apache HTTP Server 2.4.49 - Remote Code Execution | multiple/webapps/50512.py
```

---

## 6. Manual Vulnerability Research Methodology

Automated scanners miss logic flaws, business-layer vulnerabilities, and complex chained attacks. Supplement with manual research:

```
Step 1: Inventory Services
  → Map all open ports to service/version from Week 3 scans

Step 2: Search per Service
  → searchsploit [service] [version]
  → NVD: https://nvd.nist.gov
  → Vendor advisories
  → Google: "[service] [version] vulnerability 2024"

Step 3: Assess Exploitability
  → Is a public exploit available?
  → Is the exploit reliable / weaponized?
  → What conditions are required?
  → CVSS AV:Network, AC:Low, PR:None = top priority

Step 4: Validate
  → Safe check: banner grab, version confirm
  → Dangerous check: exploit attempt (requires authorization)

Step 5: Document
  → CVE number, CVSS score, affected hosts
  → Proof of concept notes
  → Remediation recommendation
```

---

## 7. Risk Prioritization Matrix

Not all vulnerabilities are equal — combine CVSS score with business context:

```
                    BUSINESS IMPACT
              Low          Medium         High
           ┌──────────┬────────────┬─────────────┐
    Low    │ Monitor  │   Patch    │ Patch Soon  │
  C │      │          │  90 days   │  30 days    │
  V ├──────┼──────────┼────────────┼─────────────┤
  S │Medium│   Patch  │ Patch Soon │ Urgent Patch│
  S │      │  90 days │  30 days   │   14 days   │
    ├──────┼──────────┼────────────┼─────────────┤
  H │ High │ Patch    │   Urgent   │  EMERGENCY  │
  I │      │ 30 days  │  14 days   │  immediate  │
  G │      │          │            │             │
  H └──────┴──────────┴────────────┴─────────────┘
```

---

## 8. Vulnerability Assessment Report Structure

A professional VA report follows this structure:

!!! note "Report Template"
    1. **Executive Summary** — business-language overview, risk posture, top 3 findings
    2. **Scope & Methodology** — what was tested, tools used, scan dates
    3. **Findings Summary** — chart of Critical/High/Medium/Low counts
    4. **Detailed Findings** — per vulnerability: CVE, CVSS, description, affected hosts, evidence, remediation
    5. **Remediation Roadmap** — prioritized fix schedule
    6. **Appendices** — raw scanner output, tool configurations

---

## Key Vocabulary

| Term | Definition |
|------|------------|
| **CVE** | Common Vulnerabilities and Exposures — unique vuln identifier |
| **CVSS** | Common Vulnerability Scoring System — standardized severity score |
| **NVD** | National Vulnerability Database — NIST's CVE enrichment database |
| **False Positive** | Scanner reports vuln that doesn't actually exist |
| **False Negative** | Scanner misses a real vulnerability |
| **Credentialed Scan** | Scanner authenticates to host for deeper inspection |
| **Plugin** | Scanner module that checks for a specific vulnerability |
| **Zero-Day** | Vulnerability unknown to vendor; no patch available |

---

## Review Questions

!!! question "Self-Assessment"
    1. A Nessus scan returns 47 Critical findings on a web server. How do you decide which to address first?
    2. Explain why a credentialed scan produces significantly more findings than an uncredentialed scan.
    3. You find CVE-2021-44228 (Log4Shell) on an internal application server. Calculate the business risk considering: the server processes financial transactions, is not internet-facing, but insiders can reach it.
    4. What types of vulnerabilities will automated scanners consistently miss?
    5. Describe the difference between a CVSS Base Score and a CVSS Environmental Score.

---

## Further Reading

- 📖 *Hacking Exposed 7*, Chapter 4 — "Vulnerability Assessment"
- 📄 [CVSS v3.1 Specification](https://www.first.org/cvss/specification-document)
- 📄 [NVD Scoring](https://nvd.nist.gov/vuln-metrics/cvss)
- 📄 [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- 📄 SANS: "Building a Vulnerability Management Program"

---

*[← Week 3](week03.md) &nbsp;|&nbsp; [Course Index](index.md) &nbsp;|&nbsp; [Week 5 →](week05.md)*
