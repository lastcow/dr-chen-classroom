---
title: "Week 15 — Real-World Case Studies & Capstone Review"
description: Analyze landmark breaches through the lens of course concepts, synthesize all course objectives, and prepare for the final comprehensive assessment.
---

# Week 15 — Real-World Case Studies & Capstone Review

<div class="week-meta" markdown>
**Course Objectives:** CO1–CO8 &nbsp;|&nbsp; **Focus:** Synthesis & Application &nbsp;|&nbsp; **Difficulty:** ⭐⭐⭐⭐⭐
</div>

---

## Learning Objectives

- [ ] Analyze real-world breach case studies using course frameworks (Kill Chain, ATT&CK, NIST IR)
- [ ] Synthesize offensive and defensive knowledge across all 14 weeks
- [ ] Map attacker TTPs from case studies to defensive countermeasures
- [ ] Identify systemic security failures and propose comprehensive remediation
- [ ] Demonstrate readiness for professional certifications (CEH, OSCP, GCIH, GCFE)

---

## 1. Case Study Framework

For each case study, apply the same analytical framework:

```
ANALYSIS TEMPLATE:
  1. Organization & Context      → Who, what industry, when
  2. Initial Access Vector       → How did attackers get in?
  3. Kill Chain Mapping          → Walk through the 7 stages
  4. ATT&CK TTPs                 → Specific techniques used
  5. Detection Failures          → Why wasn't it caught sooner?
  6. Defender Response           → What IR actions were taken?
  7. Business Impact             → Financial, reputational, operational
  8. Lessons Learned             → What controls would have prevented/detected this?
```

---

## 2. Case Study 1 — SolarWinds SUNBURST (2020)

### Overview

The most sophisticated supply chain attack in history. Nation-state threat actor (APT29 / Cozy Bear) compromised SolarWinds' build pipeline, inserting SUNBURST backdoor into Orion software updates. 18,000+ organizations downloaded the trojanized update; ~100 received active follow-on operations, including US government agencies.

### Kill Chain Analysis

| Stage | SolarWinds Action |
|-------|------------------|
| **Reconnaissance** | Extensive pre-attack research on SolarWinds' build/update process. Attackers had access for months before inserting backdoor. |
| **Weaponization** | Modified SolarWinds Orion DLL (`SolarWinds.Orion.Core.BusinessLayer.dll`). Added SUNBURST backdoor code. |
| **Delivery** | SolarWinds' legitimate software update mechanism (HTTPS). Cryptographically signed by SolarWinds certificate — completely trusted. |
| **Exploitation** | Trojanized DLL loaded by Orion. No CVE needed — attackers rode legitimate software. |
| **Installation** | SUNBURST sleeps 12–14 days before activation (sandbox/AV evasion). Blends with legitimate Orion traffic. |
| **C2** | Beaconing to `avsvmcloud[.]com` via DNS — traffic appeared as legitimate Orion telemetry. |
| **Objectives** | Credential theft, lateral movement to cloud environments (Azure AD), data exfiltration. TEARDROP/RAINDROP loaders deployed for high-value targets. |

### ATT&CK TTPs

```
T1195.002  Supply Chain Compromise: Software Supply Chain
T1078      Valid Accounts (used legitimate SolarWinds certificate)
T1568.002  Dynamic Resolution: Domain Generation Algorithm
T1027      Obfuscated Files or Information (SUNBURST evasion techniques)
T1550.001  Use Alternate Authentication Material: Application Access Token
T1040      Network Sniffing (on-premise credential harvesting)
```

### Why It Worked — Detection Failures

- ✗ Build pipeline integrity not monitored — no diff on compiled binaries
- ✗ Software signing did not prevent trojanized code insertion (key wasn't stolen — pipeline was)
- ✗ Legitimate update traffic identical to normal C2 beaconing — no behavioral baseline
- ✗ Extensive dwell time: attackers in environment 8+ months before discovery (FireEye found it while investigating own breach)
- ✗ No detection when credentials were stolen for cloud pivot

### Lessons Learned

- ✅ Software supply chain integrity — verify builds against source code (reproducible builds)
- ✅ SolarWinds should not have had internet access from sensitive government networks
- ✅ Privileged access workstations (PAWs) for Orion administrators
- ✅ Zero-trust network access — even trusted software shouldn't have unlimited network reach

---

## 3. Case Study 2 — Colonial Pipeline Ransomware (2021)

### Overview

DarkSide ransomware gang encrypted Colonial Pipeline IT systems, causing a 6-day shutdown of the largest US fuel pipeline (45% of East Coast fuel supply). $4.4M ransom paid. Gas shortages across southeastern US. Attack attributed to RaaS (Ransomware-as-a-Service) affiliate.

### Breach Timeline

```
April 29, 2021:   DarkSide accesses Colonial via VPN
                  Credentials: leaked password found in dark web breach dump
                  VPN account had no MFA

May 7, 2021:      Ransomware deployed — 100 GB data exfiltrated
  06:00 AM:       Ransomware encrypts IT systems
  06:10 AM:       Colonial operators notice anomalies
  06:30 AM:       Colonial manually shuts down OT systems (proactive)
  09:00 AM:       Ransom demand received ($4.4M Bitcoin)

May 13, 2021:     Ransom paid — decryptor received
                  (too slow — Colonial restores from backup)

May 15, 2021:     Pipeline operations resume
  
June 2021:        DOJ recovers ~$2.3M from DarkSide Bitcoin wallet
```

### Root Cause Analysis — 5 Whys

```
Problem: Ransomware encrypted Colonial's IT systems

Why 1: Attackers accessed Colonial's VPN
Why 2: They had valid VPN credentials
Why 3: Credentials were in a dark web breach dump (legacy account)
Why 4: No MFA on VPN, no credential monitoring
Why 5: Security controls were not applied to legacy/inactive accounts

Root cause: Lack of MFA + poor credential hygiene + no dark web monitoring
```

### ATT&CK TTPs

```
T1078      Valid Accounts (compromised VPN credentials)
T1133      External Remote Services (VPN access)
T1486      Data Encrypted for Impact (ransomware)
T1041      Exfiltration Over C2 Channel (100 GB before encryption)
T1657      Financial Theft (extortion)
```

### Key Lessons

- ✅ **MFA is mandatory** — especially for remote access (VPN, RDP, Citrix)
- ✅ Regular dark web credential monitoring (HaveIBeenPwned Enterprise, Recorded Future)
- ✅ Disable/audit inactive accounts
- ✅ Network segmentation between IT and OT (Colonial's OT was NOT directly encrypted)
- ✅ Offline backups that ransomware can't reach

---

## 4. Case Study 3 — Equifax Data Breach (2017)

### Overview

Chinese military hackers (PLA Unit 61398) exfiltrated personal data of **147 million Americans** from Equifax over 76 days. Exploited Apache Struts vulnerability (CVE-2017-5638, CVSS 10.0) patched 2 months prior — Equifax had not applied it.

### What Made It Catastrophic

```
INITIAL VECTOR:
  CVE-2017-5638: Apache Struts Content-Type header injection → RCE
  Patch available: March 7, 2017
  Equifax breach began: May 13, 2017 (67 days after patch)
  
STAYING HIDDEN (76 days):
  SSL inspection was disabled on key network segment
  → Encrypted traffic from attacker was NOT inspected
  → Attacker exfiltrated data via HTTPS — completely blind to Equifax

SCALE OF FAILURE:
  19 distinct attacker IPs used — none blocked
  9,000 data queries executed — not detected as anomalous
  147 million SSNs, DOBs, addresses, driver's license numbers
  
DISCOVERY: Expired SSL certificate on inspection device
           → Tool that would have caught exfiltration was non-functional
```

### ATT&CK Mapping

```
T1190  Exploit Public-Facing Application (Apache Struts)
T1059  Command and Scripting Interpreter (web shell)
T1003  OS Credential Dumping
T1083  File and Directory Discovery
T1213  Data from Information Repositories
T1048  Exfiltration Over Alternative Protocol (HTTPS with disabled inspection)
```

### Systemic Failures

| Failure | Lesson |
|---------|--------|
| Unpatched 10.0 CVE for 67 days | Patch critical vulnerabilities within 48-72 hours |
| SSL inspection expired/disabled | Certificate expiry monitoring + automated alerting |
| No anomaly detection on 9,000 queries | Database activity monitoring (DAM) baseline + alerting |
| No network segmentation | Sensitive PII should not be reachable from internet-facing servers |
| 147M records in one accessible database | Data minimization, tokenization, masking |

---

## 5. Case Study 4 — Twitter Hack (2020)

### Overview

17-year-old attacker social-engineered Twitter employees into granting access to internal admin tools ("God Mode"). Compromised accounts of Obama, Biden, Gates, Musk, Apple and others. Ran Bitcoin scam generating $120K in 24 hours.

### Social Engineering Kill Chain

```
1. RECONNAISSANCE:
   Researched Twitter employees on LinkedIn + gaming/Discord communities
   Found employees who discussed work on social media

2. VISHING (Telephone):
   Called Twitter employees posing as IT department
   "We're seeing unusual access on your account — need to verify"
   Obtained VPN credentials

3. INTERNAL PIVOT:
   Used VPN credentials to access Twitter internal network
   Social-engineered employees with higher access to add attacker's
   phone number to their Slack accounts

4. GOD MODE ACCESS:
   Accessed internal Twitter admin tools
   Changed email/phone on target accounts
   Disabled 2FA on high-value accounts (Obama, Gates, Musk)

5. OBJECTIVES:
   Tweeted Bitcoin scam from compromised accounts
   Attempted to sell access to other accounts
   Downloaded full Twitter archives of elected officials
```

### Lessons Learned

- ✅ Privileged admin tools need hardware MFA (FIDO2) — not just Slack auth
- ✅ Zero trust for internal tools — VPN ≠ trusted
- ✅ Behavior analytics on privileged account changes (disable 2FA should require approval)
- ✅ Separation of duties — one employee shouldn't be able to disable all controls
- ✅ Internal threat intelligence — monitor dark web for employees offering access

---

## 6. Course Synthesis — Connecting Attack & Defense

### Mapping Course Weeks to Career Paths

| Career | Most Relevant Weeks | Certifications |
|--------|--------------------|-----------------|
| **Penetration Tester** | 1–10 | OSCP, CEH, GPEN |
| **Security Operations (SOC)** | 11–13 | GCIH, GCIA, CEH |
| **Digital Forensics / DFIR** | 11–14 | GCFE, GCFA, EnCE |
| **Security Engineering** | 1–4, 6, 8 | CISSP, SSCP |
| **Threat Intelligence** | 1, 2, 11–13 | GCTI, CTI certifications |
| **Red Team** | All (1–10 primary) | CRTO, CRTE, OSED |

---

## 7. Capstone Review — All 8 Course Objectives

!!! abstract "Quick Reference — Course Objectives"

=== "CO1 — Ethical Hacking Methodology"
    - Kill Chain: Recon → Weaponize → Deliver → Exploit → Install → C2 → Act
    - MITRE ATT&CK: Tactics, Techniques, Procedures
    - Legal: CFAA, ECPA, Rules of Engagement
    - Testing types: Black/Gray/White box; Red Team vs. Pentest

=== "CO2 — Reconnaissance & Scanning"
    - Passive: OSINT, WHOIS, Shodan, CT logs, Google dorking
    - Active: Nmap (scan types, NSE scripts), masscan
    - Enumeration: SMB (enum4linux), SNMP (snmpwalk), LDAP, RPC

=== "CO3 — Exploitation"
    - Metasploit: exploit → payload → meterpreter workflow
    - Web: SQLi (manual + sqlmap), XSS (reflected/stored/DOM), IDOR, SSRF, Burp Suite
    - Credentials: Hashcat, John, Pass-the-Hash, spraying, Responder
    - Post-exploitation: privesc paths, BloodHound, Kerberoasting, lateral movement

=== "CO4 — Wireless Security"
    - WPA2 4-way handshake → Aircrack-ng/Hashcat crack
    - PMKID attack (no client required)
    - Evil twin / rogue AP / KARMA / EAP attacks
    - Defense: WPA3, EAP-TLS, WIDS

=== "CO5 — Incident Response"
    - NIST SP 800-61: Preparation → Detection → Containment/Eradication/Recovery → Post-Incident
    - Detection: SIEM correlation rules, IDS/IPS, EDR, user reports
    - Containment: isolation strategies by incident type
    - Legal: GDPR 72h, HIPAA 60d, SEC 4-day, PCI DSS

=== "CO6 — Malware Analysis"
    - Static: file ID, strings, PE header, imports, YARA
    - Dynamic: ProcMon, Wireshark, sandboxes
    - Classification: virus, worm, trojan, ransomware, RAT, fileless
    - IoC extraction and sharing (STIX/TAXII, MISP)

=== "CO7 — Digital Forensics"
    - Chain of custody, order of volatility
    - Disk imaging: write blockers, FTK Imager, hash verification
    - NTFS: MFT, timestamps, prefetch, registry, shellbags, Recycle Bin
    - Memory: Volatility (pslist, psscan, malfind, netstat)
    - Timeline: log2timeline/Plaso, Timeline Explorer

=== "CO8 — Professional Reporting"
    - Pentest report: executive summary, technical findings, CVSS ratings, remediation
    - VA report: scope, methodology, findings table, risk matrix
    - IR report: incident timeline, root cause, impact, lessons learned
    - Chain of custody documentation, evidence logs

---

## 8. Final Exam Preparation

!!! tip "Study Strategy"

    **High-yield topics** (appear frequently on exams):
    
    1. Nmap scan types and when to use each
    2. WPA2 4-way handshake attack chain  
    3. NIST IR phases and activities in each
    4. CVSS scoring components
    5. Kerberoasting attack and prevention
    6. Order of volatility for evidence collection
    7. OWASP Top 10 (2021) — all 10 categories
    8. Key Windows Event IDs (4624, 4625, 4688, 4698, 7045)
    9. Hashcat attack modes (-m values for NTLM, WPA2, bcrypt)
    10. Kill Chain stages with attack examples and defender mitigations

---

## Review Questions — Comprehensive

!!! question "Final Exam Style Questions"
    1. **SolarWinds** had endpoint detection, network monitoring, and a mature SOC. Explain why SUNBURST evaded detection for 8+ months.
    2. **Design a security architecture** for a healthcare company processing 500K patient records. Address: network segmentation, encryption, authentication, monitoring, and incident response capability.
    3. A **red team assessment** reveals: initial access via phishing, privilege escalation via token impersonation, lateral movement via PsExec, DC-level access via Kerberoasting. Write the executive summary section of the penetration test report.
    4. **Ransomware scenario**: You are the IR lead at 2 AM. The SIEM shows ransomware notes appearing on 15 file servers. Three servers are still encrypting. Walk through your first 60 minutes of response.
    5. **Forensic scenario**: A terminated employee is accused of exfiltrating 50,000 customer records before departing. Describe your evidence collection plan, analysis methodology, and the artifacts you would examine.

---

## Professional Certification Roadmap

```
ENTRY LEVEL:
  CompTIA Security+    → General security fundamentals
  CEH (EC-Council)     → Ethical hacking methodology

INTERMEDIATE:
  GCIH (SANS)          → Incident Handling (Weeks 12-13 focus)
  GCFE (SANS)          → Windows Forensics (Week 14 focus)
  GWAPT (SANS)         → Web App Penetration Testing (Week 6)

ADVANCED:
  OSCP (OffSec)        → Practical penetration testing (Weeks 1-10)
  GCFA (SANS)          → Advanced Forensics (Week 14+)
  GCTI (SANS)          → Cyber Threat Intelligence
  CRTO (Zero-Point)    → Red Team Ops & Cobalt Strike

ELITE:
  OSED (OffSec)        → Windows exploit development
  GXPN (SANS)          → Advanced exploit research
  CRTE (Altered Security) → Active Directory red teaming
```

---

## Further Reading — Capstone

- 📄 [Mandiant M-Trends Annual Report](https://www.mandiant.com/m-trends) — latest breach statistics
- 📄 [Verizon DBIR](https://www.verizon.com/business/resources/reports/dbir/) — Data Breach Investigations Report
- 📄 [CISA Advisories](https://www.cisa.gov/news-events/cybersecurity-advisories) — current threat intelligence
- 📄 [Krebs on Security](https://krebsonsecurity.com/) — breach reporting and analysis
- 📄 [Hacking the Xbox: An Introduction to Reverse Engineering](https://bunniefoo.com/nostarch/hacking_the_xbox_free.pdf)
- 📖 *The Cuckoo's Egg* — Cliff Stoll (original hacker chase story — still relevant)

---

*[← Week 14](week14.md) &nbsp;|&nbsp; [Course Index](index.md)*

---

> **Congratulations on completing SCIA 472.** The skills you've developed — from reconnaissance to exploitation, wireless attacks to incident response, malware analysis to digital forensics — form the foundation of a professional cybersecurity career. Use them ethically, legally, and with care. The same knowledge that enables attack enables defense. Choose defense.
