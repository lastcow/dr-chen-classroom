---
title: "Week 1 — Ethical Hacking Foundations & the Cyber Kill Chain"
description: Establish the ethical, legal, and methodological framework for penetration testing and understand the attacker's kill chain model.
---

# Week 1 — Ethical Hacking Foundations & the Cyber Kill Chain

<div class="week-meta" markdown>
**Course Objectives:** CO1 &nbsp;|&nbsp; **Focus:** Foundations &nbsp;|&nbsp; **Difficulty:** ⭐☆☆☆☆
</div>

---

## Learning Objectives

By the end of this week, you will be able to:

- [ ] Define ethical hacking and distinguish it from malicious hacking
- [ ] Explain the legal boundaries governing penetration testing (CFAA, ECPA, state laws)
- [ ] Describe the five phases of the penetration testing process
- [ ] Map an attack scenario to the Lockheed Martin Cyber Kill Chain
- [ ] Identify the core components of a Rules of Engagement (RoE) document

---

## 1. What is Ethical Hacking?

Ethical hacking — also called **penetration testing** or **white-hat hacking** — is the authorized practice of probing computer systems, networks, and applications to discover security weaknesses before malicious actors do.

!!! warning "Authorization is Everything"
    The **only** difference between an ethical hacker and a criminal is **written authorization**. Never test a system without explicit, documented permission. The Computer Fraud and Abuse Act (CFAA, 18 U.S.C. § 1030) imposes federal felony charges for unauthorized computer access regardless of intent.

### Categories of Security Testing

| Type | Authorization | Scope | Purpose |
|------|--------------|-------|---------|
| **Penetration Test** | Full, written | Defined scope | Find exploitable vulns before attackers do |
| **Red Team Exercise** | Full, written | Broad (stealth) | Test detection & response capabilities |
| **Vulnerability Assessment** | Full, written | All assets | Enumerate weaknesses (no exploitation) |
| **Bug Bounty** | Program terms | Defined assets | Crowdsourced vuln discovery with rewards |
| **Security Audit** | Full, written | Compliance scope | Verify policy & control adherence |

---

## 2. Legal & Ethical Framework

### Key U.S. Laws

**Computer Fraud and Abuse Act (CFAA)**
: Prohibits unauthorized access to "protected computers" (any computer used in interstate commerce). Even *exceeding authorized access* is a federal crime. Key cases: *United States v. Morris* (1991), *United States v. Nosal* (2016).

**Electronic Communications Privacy Act (ECPA)**
: Governs interception of electronic communications. Packet captures without authorization may violate Title III (Wiretap Act).

**Stored Communications Act (SCA)**
: Restricts access to stored electronic communications — relevant for cloud and email system testing.

!!! tip "Rules of Engagement Document"
    A proper RoE must specify: **target IP ranges/domains**, **allowed attack techniques**, **off-limits systems**, **testing window (dates/times)**, **escalation contacts**, and **emergency stop criteria**.

### Professional Ethics Codes

- **EC-Council Code of Ethics** (CEH certification)
- **ISSA Code of Ethics**
- **(ISC)² Code of Professional Ethics** (CISSP/SSCP)
- **PTES** — Penetration Testing Execution Standard (ptes.org)

---

## 3. The Penetration Testing Process

A structured methodology ensures thoroughness and repeatability. The five-phase model:

```
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 1          PHASE 2          PHASE 3                      │
│  Reconnaissance → Scanning &    → Exploitation                  │
│  (passive/active)  Enumeration                                  │
│                                         ↓                       │
│  PHASE 5          PHASE 4                                       │
│  Reporting     ← Post-Exploitation ←──────────────             │
│                  & Maintaining Access                           │
└─────────────────────────────────────────────────────────────────┘
```

| Phase | Activities | Typical Tools |
|-------|-----------|---------------|
| **1. Reconnaissance** | OSINT, footprinting, DNS enumeration | theHarvester, Maltego, Shodan |
| **2. Scanning & Enumeration** | Port scanning, OS detection, service fingerprinting | Nmap, Nessus, Nikto |
| **3. Exploitation** | Exploit vulnerabilities, gain initial access | Metasploit, Burp Suite, sqlmap |
| **4. Post-Exploitation** | Privilege escalation, lateral movement, persistence | Mimikatz, BloodHound, Empire |
| **5. Reporting** | Document findings, risk ratings, remediation | Professional report |

---

## 4. The Cyber Kill Chain

Developed by Lockheed Martin in 2011, the **Cyber Kill Chain** models the stages an adversary must complete to achieve their objective. Defenders use it to identify where to disrupt attacks.

### The 7 Stages

=== "Stage 1: Reconnaissance"
    **Goal:** Gather intelligence about the target.

    - **Passive:** OSINT (public records, LinkedIn, job postings, Shodan, DNS records)
    - **Active:** Direct interaction with target systems (port scanning, web crawling)

    **Defender Action:** Monitor for reconnaissance signatures; limit public exposure of sensitive data.

=== "Stage 2: Weaponization"
    **Goal:** Create a deliverable payload.

    - Pair exploit code with a malicious payload (e.g., Office macro dropper, PDF exploit)
    - Attackers may purchase exploit kits or develop custom implants

    **Defender Action:** Threat intelligence feeds; track adversary TTPs via MITRE ATT&CK.

=== "Stage 3: Delivery"
    **Goal:** Transmit the weapon to the target.

    - **Email** (phishing/spearphishing) — most common vector
    - **Web drive-by** (watering hole attacks)
    - **USB drop**, supply chain compromise, direct network injection

    **Defender Action:** Email filtering, web proxies, user awareness training.

=== "Stage 4: Exploitation"
    **Goal:** Trigger the payload on the victim system.

    - Software vulnerability exploitation (CVE, zero-day)
    - Macro execution, browser exploit
    - Social engineering (user clicks/opens)

    **Defender Action:** Patch management, application whitelisting, EDR solutions.

=== "Stage 5: Installation"
    **Goal:** Establish persistent foothold.

    - Install backdoor, RAT, or rootkit
    - Modify registry, scheduled tasks, startup items
    - Web shells on compromised servers

    **Defender Action:** File integrity monitoring, EDR behavioral detection.

=== "Stage 6: Command & Control (C2)"
    **Goal:** Establish communication channel with attacker.

    - HTTP/HTTPS beaconing to C2 server
    - DNS tunneling, domain fronting
    - Social media C2 (Twitter DMs, GitHub issues)

    **Defender Action:** Network traffic analysis, DNS monitoring, egress filtering.

=== "Stage 7: Actions on Objectives"
    **Goal:** Accomplish mission goals.

    - Data exfiltration, ransomware deployment
    - Destructive attacks, lateral movement to new targets
    - Espionage, sabotage

    **Defender Action:** DLP solutions, anomalous data transfer alerts, network segmentation.

---

## 5. Beyond the Kill Chain — MITRE ATT&CK

The MITRE ATT&CK framework extends the Kill Chain into a **comprehensive matrix of Tactics, Techniques, and Procedures (TTPs)**:

!!! info "ATT&CK vs. Kill Chain"
    - **Kill Chain** = high-level stages (strategic view)
    - **ATT&CK** = hundreds of specific techniques mapped to those stages (tactical view)
    - ATT&CK is the current industry standard for threat intelligence and detection engineering

**ATT&CK Matrices:**

- **Enterprise** — Windows, Linux, macOS, cloud, containers
- **Mobile** — iOS, Android
- **ICS** — Industrial Control Systems (SCADA/OT)

Access the full framework at [attack.mitre.org](https://attack.mitre.org).

---

## 6. Security Assessment Types Deep Dive

### Testing Perspectives

| Perspective | Knowledge | Use Case |
|-------------|-----------|----------|
| **Black Box** | No prior knowledge of target | Simulates external attacker |
| **Gray Box** | Partial knowledge (e.g., regular user credentials) | Simulates insider or compromised account |
| **White Box** | Full knowledge (architecture, source code) | Most thorough; internal audit |

### Physical vs. Technical vs. Social

```
┌─────────────────────────────────────────────────────┐
│                 ATTACK SURFACE                       │
│                                                      │
│   Physical         Technical        Social           │
│  ┌─────────┐     ┌──────────┐    ┌──────────┐      │
│  │ Locks   │     │ Network  │    │ Phishing │      │
│  │ Cameras │     │ Services │    │ Vishing  │      │
│  │ Badges  │     │ Software │    │ Pretexting│     │
│  └─────────┘     └──────────┘    └──────────┘      │
└─────────────────────────────────────────────────────┘
```

---

## Key Vocabulary

| Term | Definition |
|------|------------|
| **Threat Actor** | Individual or group that conducts attacks |
| **Threat Vector** | Path used to gain unauthorized access |
| **Attack Surface** | Total set of exploitable entry points |
| **Vulnerability** | Flaw that can be exploited |
| **Exploit** | Code/technique that takes advantage of a vulnerability |
| **Payload** | Code executed on the target after exploitation |
| **Indicator of Compromise (IoC)** | Forensic artifact indicating a breach |
| **TTPs** | Tactics, Techniques, and Procedures — attacker behavior patterns |

---

## Review Questions

!!! question "Self-Assessment"
    1. What is the primary legal distinction between ethical hacking and criminal hacking?
    2. Describe a scenario where a gray-box penetration test is more appropriate than a black-box test.
    3. Map the 2020 SolarWinds supply chain attack to the Cyber Kill Chain stages.
    4. Why do organizations still use the Cyber Kill Chain when MITRE ATT&CK exists?
    5. What elements must be included in a Rules of Engagement document?

---

## Further Reading

- 📖 *Hacking Exposed 7*, Chapter 1 — "The Attacker's Advantage and the Defender's Dilemma"
- 📄 [Lockheed Martin Cyber Kill Chain](https://www.lockheedmartin.com/en-us/capabilities/cyber/cyber-kill-chain.html)
- 📄 [PTES Technical Guidelines](http://www.pentest-standard.org/index.php/Main_Page)
- 📄 [NIST SP 800-115](https://csrc.nist.gov/publications/detail/sp/800-115/final) — Technical Guide to Information Security Testing
- 🎥 SANS Webcast: "Using ATT&CK for Threat Hunting"

---

*← [Course Index](index.md) &nbsp;|&nbsp; [Week 2 →](week02.md)*
