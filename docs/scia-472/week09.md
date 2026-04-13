---
title: "Week 9 — Social Engineering & Phishing"
description: Understand psychological manipulation techniques, phishing infrastructure, vishing, and organizational defenses against human-layer attacks.
---

# Week 9 — Social Engineering & Phishing

<div class="week-meta" markdown>
**Course Objectives:** CO1, CO3 &nbsp;|&nbsp; **Focus:** Human Attack Surface &nbsp;|&nbsp; **Difficulty:** ⭐⭐☆☆☆
</div>

---

## Learning Objectives

- [ ] Explain the psychological principles exploited by social engineers
- [ ] Design and analyze spearphishing campaigns using realistic pretexts
- [ ] Describe vishing, smishing, and physical social engineering techniques
- [ ] Set up phishing infrastructure using GoPhish
- [ ] Design an employee security awareness program to reduce social engineering risk

---

## 1. The Human Factor

!!! quote "Kevin Mitnick"
    *"The human side of computer security is easily exploited and constantly overlooked. Companies spend millions of dollars on firewalls, encryption, and secure access devices, and it's money wasted because none of these measures address the weakest link in the security chain: the people who use, administer, operate, and account for computer systems."*

Social engineering exploits **human psychology** rather than technical vulnerabilities. It is the primary initial access vector in over 80% of breaches.

---

## 2. Psychological Principles

Social engineers leverage well-documented cognitive biases:

| Principle | Description | Example |
|-----------|-------------|---------|
| **Authority** | Comply with figures of perceived authority | "This is the IT security team — we need your password to investigate an incident" |
| **Urgency/Scarcity** | Time pressure reduces critical thinking | "Your account will be locked in 30 minutes — click now" |
| **Social Proof** | "Everyone else is doing it" | "The rest of your team has already updated their credentials" |
| **Liking** | More likely to comply with people we like | Research target's interests → build rapport |
| **Reciprocity** | Return favors | Send gift card → ask for access |
| **Commitment** | Consistent with prior commitments | Small yes → bigger yes |
| **Fear** | Threat of negative consequence | "Your account has been compromised — act now" |

---

## 3. Phishing Taxonomy

### 3.1 Email Phishing Types

```
PHISHING (mass)
  → Generic email to thousands of targets
  → "Your PayPal account is limited — verify now"
  → Low targeting, moderate success rate (~3%)

SPEARPHISHING (targeted)
  → Customized to specific individual or organization
  → Uses personal details from OSINT (name, role, manager, projects)
  → Higher cost, 5-40% success rate

WHALING
  → Targets executives (CEO, CFO, CISO)
  → High-value: C-suite credentials or wire transfer authorization
  → BEC (Business Email Compromise) = $26B+ in losses since 2016

VISHING (voice)
  → Phone calls impersonating IT support, IRS, bank
  → Harder to detect than email phishing

SMISHING (SMS)
  → Text message phishing
  → "Your package is delayed — confirm address [link]"

QUISHING (QR code)
  → Malicious QR codes in physical environments
  → Bypasses email URL scanning
```

### 3.2 Spearphishing Construction

A high-quality spearphishing email requires thorough OSINT (Week 2):

```
OSINT → Pretext → Email Crafting → Infrastructure → Delivery

1. OSINT Collection:
   - Target name, title, direct reports from LinkedIn
   - Current projects from job postings / press releases
   - Email format from theHarvester
   - Manager's name from org chart

2. Pretext Selection:
   - IT-themed: "Security update required — MFA reset"
   - HR-themed: "2026 benefits enrollment closes Friday"
   - Executive-themed: "Urgent wire transfer request from CEO"
   - Vendor-themed: "Invoice #INV-2847 requires your approval"

3. Malicious Payload Options:
   - Link to credential harvesting page
   - Office document with macro dropper
   - PDF with embedded link
   - ISO/LNK file (bypasses Protected View)
   - QR code to phishing page

4. Infrastructure:
   - Domain: company-helpdesk.com, frostburg-it.net (typosquat)
   - Valid TLS certificate (free via Let's Encrypt)
   - Phishing kit mirroring target's login page
   - Redirector for operational security
```

---

## 4. GoPhish — Phishing Campaign Framework

GoPhish is an open-source phishing simulation framework used for authorized red team exercises and employee awareness testing:

```bash
# Install and start GoPhish
wget https://github.com/gophish/gophish/releases/download/v0.12.1/gophish-v0.12.1-linux-64bit.zip
unzip gophish-*.zip && chmod +x gophish && ./gophish

# Access admin interface: https://localhost:3333
# Default creds: admin / gophish (change immediately)
```

### GoPhish Workflow

```
1. SENDING PROFILES
   Configure SMTP relay (SendGrid, SES, or your own MTA)
   Set From name, email, host, port, auth

2. LANDING PAGES
   Clone target's login page (Site Importer feature)
   Enable credential capture
   Set redirect URL (after capture → real site or thank-you page)

3. EMAIL TEMPLATES
   Write HTML email with personalization variables:
   {{.FirstName}}, {{.LastName}}, {{.Email}}, {{.Position}}
   Embed tracking pixel + phishing link

4. USER GROUPS
   Import targets via CSV: First,Last,Email,Position

5. CAMPAIGNS
   Combine: template + landing page + SMTP + group
   Schedule send time
   Track: opens, clicks, submitted creds, email reported

6. RESULTS DASHBOARD
   Real-time statistics
   Export data for reporting
   Calculate click rate, submission rate, report rate
```

---

## 5. Vishing (Voice Phishing)

Telephone-based social engineering exploiting trust in voice communication:

### Common Pretexts

```
IT HELPDESK:
"Hi, this is Marcus from IT Security. We detected unusual login activity 
 from your account from a location in [foreign country]. To secure your 
 account, I need to verify your identity and temporarily reset your 
 multi-factor authentication. Can I get your employee ID?"

HR / PAYROLL:
"Hi, this is Amanda from HR. We're updating our direct deposit records 
 for the new payroll system. I need to verify your current banking 
 information to ensure your next paycheck isn't delayed."

VENDOR / IT SUPPORT:
"This is technical support from [software your company uses]. We've 
 detected a critical security vulnerability on systems with your 
 license. I need to walk you through an emergency patch installation."
```

### Vishing Defense Red Flags

- Unsolicited contact requesting credentials or sensitive info
- Pressure tactics / artificial urgency
- Request to bypass normal procedures
- Cannot verify caller through official channels

---

## 6. Physical Social Engineering

### Tailgating / Piggybacking

Following an authorized person through a secure door without badging in:

```
Attack: Wait near secure door → employee approaches → "Thanks, hands full!" → enter
Defense: Strict one-person-per-badge policy, mantraps, security awareness training
```

### Pretexting Scenarios

| Scenario | Approach | Target |
|----------|----------|--------|
| **IT Tech** | Fake badge, laptop bag, technical jargon | Server room access |
| **Delivery Person** | UPS/FedEx uniform, package | Reception bypass |
| **Auditor/Consultant** | Business attire, clipboard | Sensitive areas |
| **Facilities/Cleaning** | Uniform, equipment cart | After-hours access |
| **New Employee** | "I forgot my badge" | Sympathetic tailgating |

### USB Drop Attack

```
Attack: Leave USB drives in parking lot / lobby labeled "Salaries Q1 2024.xlsx"
        Employee plugs in → HID attack (rubber ducky) or malware auto-run
Defense: Disable AutoRun, USB port policy enforcement, user training
Tools: USB Rubber Ducky, Bash Bunny, O.MG Cable
```

---

## 7. Security Awareness Program Design

An effective program reduces phishing susceptibility from ~30% (untrained) to <5%:

```
PROGRAM COMPONENTS:
  1. Baseline phishing simulation (establish current click rate)
  2. Interactive training modules (15-20 min, not death-by-PowerPoint)
  3. Simulated phishing campaigns (monthly, varied pretexts)
  4. Just-in-time training (auto-enroll clickers in additional training)
  5. Metrics tracking (click rate, report rate, credential submission rate)
  6. Positive reinforcement (reward reporters, not just punish clickers)
  7. Executive reporting (quarterly dashboard to leadership)

METRICS TO TRACK:
  - Phish click rate (target: <5%)
  - Credential submission rate (target: <1%)
  - Report rate (target: >30% — higher is better)
  - Time to report (faster = better security culture)
```

---

## Key Vocabulary

| Term | Definition |
|------|------------|
| **Social Engineering** | Psychological manipulation to obtain unauthorized access/info |
| **Pretexting** | Creating a fabricated scenario to manipulate targets |
| **Spearphishing** | Highly targeted phishing using personalized information |
| **Whaling** | Executive-targeted phishing |
| **BEC** | Business Email Compromise — impersonating executives for financial fraud |
| **Vishing** | Voice phishing via telephone |
| **Tailgating** | Following authorized personnel through secure entry |
| **GoPhish** | Open-source authorized phishing simulation platform |

---

## Review Questions

!!! question "Self-Assessment"
    1. Select three psychological principles and construct a detailed spearphishing email targeting an FSU IT department employee that exploits all three simultaneously.
    2. Explain why smishing and quishing have become more prevalent, and what technical defenses are less effective against them.
    3. Design a 12-month security awareness program for a 500-person organization. Include metrics, simulation frequency, and training format.
    4. A CEO receives an email appearing to come from the CFO requesting an urgent $250,000 wire transfer. Describe the technical mechanisms that made this BEC attack possible and how to detect it.
    5. Map a sophisticated spearphishing attack to the MITRE ATT&CK framework (TA0001 Initial Access and T1566 Phishing sub-techniques).

---

## Further Reading

- 📖 *The Art of Intrusion* — Kevin Mitnick
- 📖 *Social Engineering: The Science of Human Hacking* — Christopher Hadnagy
- 📄 [Verizon DBIR 2024](https://www.verizon.com/business/resources/reports/dbir/) — breach statistics
- 📄 [MITRE ATT&CK: T1566](https://attack.mitre.org/techniques/T1566/) — Phishing
- 📄 [SANS Security Awareness](https://www.sans.org/security-awareness-training/) — program design

---

*[← Week 8](week08.md) &nbsp;|&nbsp; [Course Index](index.md) &nbsp;|&nbsp; [Week 10 →](week10.md)*
