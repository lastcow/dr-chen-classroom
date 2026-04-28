---
title: "Lab 01: Ethical Hacking Framework — Kill Chain, ATT&CK & Methodology"
course: SCIA-472
topic: Ethical Hacking Foundations
week: 1
difficulty: ⭐
estimated_time: 45-60 minutes
tags:
  - kill-chain
  - mitre-attack
  - methodology
  - frameworks
  - penetration-testing
  - ethics
---

# Lab 01: Ethical Hacking Framework — Kill Chain, ATT&CK & Methodology

| Field | Details |
|---|---|
| **Course** | SCIA-472 — Hacking Exposed & Incident Response |
| **Topic** | Ethical Hacking Foundations |
| **Week** | 1 |
| **Difficulty** | ⭐ Beginner |
| **Estimated Time** | 45–60 minutes |
| **Tools** | Docker, Python 3.11 |
| **Prerequisites** | Docker installed and running |

---

!!! warning "Ethical Use"
    All attacks and scanning must ONLY target containers you create in this lab. Never scan or attack systems you do not own or have explicit written permission to test.

---

## Overview

Before touching a single tool, professional penetration testers understand frameworks that organize their work. This lab maps the Lockheed Martin Cyber Kill Chain and MITRE ATT&CK framework using Python, then builds a structured engagement checklist — the mental model every pentester uses.

By the end of this lab you will be able to:

- Recite all 7 phases of the Cyber Kill Chain and explain each
- Navigate MITRE ATT&CK Enterprise tactics and techniques
- Apply both frameworks to a real-world breach (Target 2013)
- Build a professional penetration testing engagement checklist
- Identify the legal boundaries that separate ethical hacking from criminal activity

---

## Part 1 — The Cyber Kill Chain in Python

The Lockheed Martin Cyber Kill Chain (2011) describes the stages an attacker must complete to achieve their objective. Defenders break the chain as early as possible — disrupting any phase stops the attack.

### Step 1.1 — Visualize the Kill Chain

```bash
docker run --rm python:3.11-slim python3 -c "
kill_chain = [
    ('1. Reconnaissance',    'Gather info about target: OSINT, scanning, enumeration'),
    ('2. Weaponization',     'Create exploit payload: malware, phishing doc, exploit code'),
    ('3. Delivery',          'Transmit payload: email, USB, watering hole, social engineering'),
    ('4. Exploitation',      'Trigger vulnerability: click link, open attachment, RCE'),
    ('5. Installation',      'Install backdoor/RAT: persistence via cron, registry, service'),
    ('6. C2 (Command & Control)', 'Establish channel: beacon to attacker-controlled server'),
    ('7. Actions on Objectives',  'Achieve goal: data exfil, ransomware, lateral movement'),
]
print('=== LOCKHEED MARTIN CYBER KILL CHAIN ===')
for phase, desc in kill_chain:
    print(f'{phase}')
    print(f'   {desc}')
    print()"
```

**Expected output:** Prints all 7 phases with descriptions.

📸 **Screenshot checkpoint:** Capture the full kill chain output showing all 7 phases — label this **01a**.

---

### Step 1.2 — Map a Real Incident to the Kill Chain (Target 2013 Breach)

```bash
docker run --rm python:3.11-slim python3 -c "
incident = {
    'Incident': 'Target Corporation Breach (2013) - 40 million credit cards stolen',
    'Kill Chain Mapping': {
        'Reconnaissance': 'Attackers identified Target used Fazio HVAC as a vendor',
        'Weaponization':  'Created spearphishing email and credential-stealing malware',
        'Delivery':       'Sent phishing email to Fazio HVAC employee',
        'Exploitation':   'Fazio employee clicked link, credentials stolen',
        'Installation':   'Used Fazio credentials to access Targets vendor portal',
        'C2':             'Malware beaconed to attacker C2 servers',
        'Actions':        'Lateral movement to POS systems, exfiltrated 40M card records',
    },
    'Defender Breakpoints': [
        'Recon: Monitor for domain enumeration and social graph analysis',
        'Delivery: Email security gateway to block phishing',
        'Exploitation: MFA on vendor portals',
        'Installation: EDR to detect new persistence mechanisms',
        'C2: Egress filtering and DNS monitoring',
        'Actions: Segment POS network from vendor network (biggest failure)',
    ]
}
print(f\"=== {incident['Incident']} ===\")
print()
print('--- Kill Chain Mapping ---')
for phase, action in incident['Kill Chain Mapping'].items():
    print(f'{phase}: {action}')
print()
print('--- Defender Breakpoints (where attack could have been stopped) ---')
for bp in incident['Defender Breakpoints']:
    print(f'  • {bp}')
"
```

📸 **Screenshot checkpoint:** Capture the full incident mapping with all defender breakpoints — label this **01b**.

---

## Part 2 — MITRE ATT&CK Tactics

MITRE ATT&CK (Adversarial Tactics, Techniques, and Common Knowledge) is a living knowledge base of real-world adversary behavior. Unlike the Kill Chain, ATT&CK is non-linear — attackers move between tactics fluidly.

### Step 2.1 — ATT&CK Tactic Overview

```bash
docker run --rm python:3.11-slim python3 -c "
attack_tactics = [
    ('TA0043', 'Reconnaissance',        'Gather info before attack'),
    ('TA0042', 'Resource Development',  'Establish infrastructure'),
    ('TA0001', 'Initial Access',        'Get into the network'),
    ('TA0002', 'Execution',             'Run malicious code'),
    ('TA0003', 'Persistence',           'Maintain foothold'),
    ('TA0004', 'Privilege Escalation',  'Gain higher permissions'),
    ('TA0005', 'Defense Evasion',       'Avoid detection'),
    ('TA0006', 'Credential Access',     'Steal credentials'),
    ('TA0007', 'Discovery',             'Map the environment'),
    ('TA0008', 'Lateral Movement',      'Move through network'),
    ('TA0009', 'Collection',            'Gather target data'),
    ('TA0010', 'Exfiltration',          'Steal data out'),
    ('TA0011', 'Command and Control',   'Communicate with implants'),
    ('TA0040', 'Impact',                'Destroy, disrupt, encrypt'),
]
print('=== MITRE ATT&CK ENTERPRISE TACTICS ===')
print(f'{\"ID\":<10} {\"Tactic\":<30} {\"Description\"}')
print('-' * 70)
for tid, name, desc in attack_tactics:
    print(f'{tid:<10} {name:<30} {desc}')
print(f'\nTotal: {len(attack_tactics)} tactics, 200+ techniques, 400+ sub-techniques')
"
```

📸 **Screenshot checkpoint:** Capture the full 14-tactic ATT&CK table — label this **01c**.

---

### Step 2.2 — ATT&CK Technique Example (T1566 — Phishing)

```bash
docker run --rm python:3.11-slim python3 -c "
technique = {
    'ID': 'T1566',
    'Name': 'Phishing',
    'Tactic': 'Initial Access (TA0001)',
    'Description': 'Adversaries send phishing messages to gain access to victim systems',
    'Sub-techniques': [
        'T1566.001 - Spearphishing Attachment (malicious Office doc, PDF)',
        'T1566.002 - Spearphishing Link (URL leading to malicious site)',
        'T1566.003 - Spearphishing via Service (LinkedIn, Slack, etc.)',
    ],
    'Mitigations': [
        'M1049 - Antivirus/Antimalware',
        'M1031 - Network Intrusion Prevention',
        'M1017 - User Training',
        'M1054 - Software Configuration (disable macros)',
    ],
    'Detection': 'Email gateway logs, attachment scanning, URL reputation',
}
for k, v in technique.items():
    if isinstance(v, list):
        print(f'{k}:')
        for item in v: print(f'  - {item}')
    else:
        print(f'{k}: {v}')
"
```

📸 **Screenshot checkpoint:** Capture the full T1566 technique deep-dive — label this **01d**.

---

## Part 3 — Penetration Testing Methodology

### Step 3.1 — Build an Engagement Checklist

Professional pentesters follow a structured methodology across all engagements. This checklist is your roadmap.

```bash
docker run --rm python:3.11-slim python3 -c "
phases = {
    'Phase 1: Pre-Engagement': [
        '[ ] Signed Statement of Work (SOW)',
        '[ ] Rules of Engagement (ROE) defined',
        '[ ] Scope documented (IP ranges, domains, out-of-scope)',
        '[ ] Emergency contacts established',
        '[ ] Legal authorization obtained',
    ],
    'Phase 2: Reconnaissance': [
        '[ ] Passive OSINT (whois, DNS, LinkedIn, Shodan)',
        '[ ] Active scanning (nmap, nikto)',
        '[ ] Service enumeration',
        '[ ] Technology fingerprinting',
    ],
    'Phase 3: Exploitation': [
        '[ ] Vulnerability verification',
        '[ ] Exploit selection and testing',
        '[ ] Payload generation',
        '[ ] Access obtained and documented',
    ],
    'Phase 4: Post-Exploitation': [
        '[ ] Privilege escalation attempted',
        '[ ] Lateral movement documented',
        '[ ] Data access verified (do NOT exfiltrate real data)',
        '[ ] Persistence mechanisms identified (do NOT install)',
    ],
    'Phase 5: Reporting': [
        '[ ] Executive summary written',
        '[ ] Technical findings documented with evidence',
        '[ ] Risk ratings assigned (Critical/High/Medium/Low)',
        '[ ] Remediation recommendations provided',
        '[ ] Remediation verification offer made',
    ],
}
for phase, tasks in phases.items():
    print(f'\n{phase}')
    for task in tasks: print(f'  {task}')
"
```

📸 **Screenshot checkpoint:** Capture the full 5-phase engagement checklist — label this **01e**.

---

### Step 3.2 — Legal and Ethical Boundaries

```bash
docker run --rm python:3.11-slim python3 -c "
legal_framework = [
    ('CFAA', 'Computer Fraud and Abuse Act (US)', 'Federal law - unauthorized access = criminal offense'),
    ('ECPA', 'Electronic Communications Privacy Act', 'Intercept communications = federal crime without consent'),
    ('GDPR', 'General Data Protection Regulation (EU)', 'Personal data exposure during testing = reportable breach'),
    ('SOX',  'Sarbanes-Oxley Act', 'Unauthorized access to financial systems = severe penalties'),
]
print('=== LEGAL FRAMEWORK FOR PENETRATION TESTING ===')
print()
for abbr, name, impact in legal_framework:
    print(f'{abbr}: {name}')
    print(f'  Impact: {impact}')
    print()
print('KEY RULE: Written authorization from system OWNER is mandatory.')
print('Verbal permission is NOT sufficient. Get it in writing.')
print('Scope creep = unauthorized access = criminal liability.')
"
```

📸 **Screenshot checkpoint:** Capture the legal framework output — label this **01f**.

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
| **01a** | Kill chain 7 phases (all visible) | 7 |
| **01b** | Target breach mapped to kill chain + defender breakpoints | 7 |
| **01c** | ATT&CK 14 tactics table | 7 |
| **01d** | T1566 Phishing technique detail (sub-techniques + mitigations) | 7 |
| **01e** | Full 5-phase engagement checklist | 6 |
| **01f** | Legal framework (CFAA, ECPA, GDPR, SOX) | 6 |
| **Total** | | **40** |

---

### Analysis (20 points)

Create a **Kill Chain vs ATT&CK comparison table** with the following columns:

| Dimension | Cyber Kill Chain | MITRE ATT&CK |
|---|---|---|
| Structure | | |
| Number of stages/tactics | | |
| Linearity | | |
| Primary use case | | |
| Defender value | | |
| Attacker perspective | | |

Complete all cells based on what you observed in this lab.

---

### Reflection Questions (40 points — 10 points each)

1. The Lockheed Martin Cyber Kill Chain has 7 phases. Defenders try to "break the chain" as early as possible. Which phase is the **best** to disrupt and why? Use the Target breach example to justify your answer.

2. The Cyber Kill Chain is linear (1→7) while MITRE ATT&CK is non-linear (attackers jump between tactics). What real-world attack behavior does the ATT&CK model better capture that the Kill Chain misses?

3. A company emails you and says *"You have our permission to test our website."* Is this sufficient authorization to begin a penetration test? What additional documents do you need and why?

4. The distinction between a penetration tester and a criminal attacker often comes down to one document. What is it and what must it contain? What happens legally if you discover an unintended vulnerability **outside** your defined scope?

---

!!! tip "Grading Rubric"
    | Component | Points |
    |---|---|
    | Screenshots (01a–01f, all visible and labeled) | 40 |
    | Kill Chain vs ATT&CK comparison table (all cells complete) | 20 |
    | Reflection questions (4 × 10 pts, substantive answers) | 40 |
    | **Total** | **100** |
