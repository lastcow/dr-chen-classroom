---
title: "Week 12 — Incident Response: Preparation & Detection"
description: Master NIST SP 800-61 incident response framework Phases 1 & 2 — building IR capability and detecting security incidents.
---

# Week 12 — Incident Response: Preparation & Detection

<div class="week-meta" markdown>
**Course Objectives:** CO5 &nbsp;|&nbsp; **Focus:** IR Phase I & II &nbsp;|&nbsp; **Difficulty:** ⭐⭐⭐☆☆
</div>

---

## Learning Objectives

- [ ] Describe the NIST SP 800-61 four-phase incident response lifecycle
- [ ] Design an Incident Response Plan (IRP) for an organization
- [ ] Identify indicators of compromise using SIEM, IDS/IPS, and endpoint telemetry
- [ ] Classify incidents by type and severity
- [ ] Perform initial triage to determine scope and impact of an incident

---

## 1. NIST SP 800-61 Incident Response Lifecycle

The authoritative federal standard for incident handling defines four phases:

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│   PHASE 1          PHASE 2          PHASE 3          PHASE 4│
│   Preparation  →  Detection &   →  Containment,  → Post-   │
│                   Analysis         Eradication &   Incident │
│        ↑                           Recovery        Activity │
│        └──────────────────────────────────────────────┘     │
│                   (Lessons Learned feed back to Preparation) │
└──────────────────────────────────────────────────────────────┘
```

**Week 12 focus:** Phase 1 (Preparation) + Phase 2 (Detection & Analysis)  
**Week 13 focus:** Phase 3 (Containment, Eradication, Recovery) + Phase 4 (Post-Incident)

---

## 2. Phase 1 — Preparation

Preparation is the most important phase. Organizations that invest in preparation suffer significantly less damage during actual incidents.

### 2.1 Incident Response Plan (IRP)

A comprehensive IRP includes:

```
SECTION 1: PURPOSE & SCOPE
  → What types of incidents does this cover?
  → Which systems and business units are in scope?

SECTION 2: INCIDENT RESPONSE TEAM
  → IR Team composition (CIRT/CSIRT/SOC)
  → Roles and responsibilities
  → Contact information (primary + backup)
  → Escalation matrix

SECTION 3: INCIDENT CLASSIFICATION
  → Severity levels (P1-P4 or Critical/High/Medium/Low)
  → Incident categories (malware, data breach, DoS, insider threat, etc.)
  → Classification criteria

SECTION 4: INCIDENT HANDLING PROCEDURES
  → Detection and reporting procedures
  → Triage process
  → Evidence collection guidelines
  → Communication templates
  → Third-party notification requirements (legal, regulatory)

SECTION 5: COMMUNICATION PLAN
  → Internal stakeholder notification
  → External communication (customers, press, law enforcement)
  → Legal and regulatory notifications (GDPR 72-hour rule, SEC 4-day rule)

SECTION 6: RECOVERY PROCEDURES
  → System restoration procedures
  → Backup restoration process
  → Business continuity integration
```

### 2.2 IR Team Roles

| Role | Responsibilities |
|------|-----------------|
| **IR Manager / IC** | Coordinate overall response, brief leadership, make decisions |
| **SOC Analyst** | Triage alerts, initial analysis, escalation |
| **Forensic Analyst** | Evidence collection, artifact analysis, chain of custody |
| **Threat Intelligence** | Attribute attack, identify TTPs, threat context |
| **Legal/Compliance** | Regulatory notifications, legal holds, law enforcement liaison |
| **PR/Communications** | External messaging, customer notification |
| **IT Operations** | System isolation, restoration, patching |
| **CISO** | Executive briefings, risk decisions, resource allocation |

### 2.3 IR Tools Preparation

!!! info "Jump Bag / IR Kit"
    IR teams maintain a pre-built toolkit ready for immediate deployment:

    ```
    COLLECTION TOOLS:
    - Write blockers (Tableau, Logicube)
    - Forensic imaging software (FTK Imager, dd)
    - Memory acquisition (WinPmem, DumpIt, LiME for Linux)
    - Network capture (Wireshark, tcpdump)
    
    ANALYSIS TOOLS:
    - Volatility (memory forensics)
    - Autopsy / Sleuth Kit (disk forensics)
    - SIEM access (Splunk, ELK, Sentinel)
    - EDR console access
    
    DOCUMENTATION:
    - Chain of custody forms
    - Evidence tags / tamper seals
    - IR case tracking system
    - Encrypted USB for evidence transport
    ```

### 2.4 Tabletop Exercises

Simulate incident scenarios to test IRP without real impact:

```
TABLETOP EXERCISE FORMATS:
  Discussion-based: Talk through response to a scenario
  Functional: Actually activate response procedures (not full)
  Full-scale: Complete simulation with technical and comms

SAMPLE SCENARIOS:
  "At 2:00 AM, your SIEM triggers 50 alerts on the Domain Controller. 
   The on-call analyst sees lateral movement. Walk through your response."
  
  "A user reports clicking a suspicious email. Finance is reporting 
   $2.3M missing from accounts payable. What do you do?"
  
  "Ransomware has encrypted your file servers. Production is down. 
   The attacker is demanding $500K in Bitcoin. Walk through response."

AFTER ACTION REVIEW:
  - What worked well?
  - What gaps did we discover?
  - What do we need to update in the IRP?
```

---

## 3. Phase 2 — Detection & Analysis

### 3.1 Detection Sources

```
AUTOMATED DETECTION:
  SIEM (Security Information & Event Management)
    → Aggregates logs from all sources
    → Correlation rules generate alerts
    → Examples: Splunk, IBM QRadar, Microsoft Sentinel, Elastic SIEM
    
  IDS/IPS (Intrusion Detection/Prevention System)
    → Network: Snort, Suricata, Zeek (Bro)
    → Host: OSSEC, Wazuh
    → Signature-based + anomaly-based detection
    
  EDR (Endpoint Detection & Response)
    → Deep endpoint telemetry
    → Behavioral detection
    → Examples: CrowdStrike Falcon, SentinelOne, Microsoft Defender for Endpoint
    
  Threat Intelligence Feeds
    → IoC matching against network/endpoint traffic
    → Commercial: Recorded Future, ThreatConnect
    → Free: AlienVault OTX, MISP, abuse.ch

MANUAL DETECTION:
  User reports ("I clicked something suspicious")
  IT reports ("Server is acting strangely")
  Help desk reports (password lockouts, unusual activity)
  Third-party notification (law enforcement, partner, customer)
```

### 3.2 Incident Classification

```
SEVERITY LEVELS:

P1 — CRITICAL (respond immediately)
  Active ransomware encrypting production systems
  Data exfiltration in progress (PII, financial data)
  Confirmed APT presence with DC-level access
  Public-facing system defacement
  Business operations completely halted

P2 — HIGH (respond within 1 hour)
  Malware confirmed on multiple systems
  Credential compromise of privileged account
  Significant data exposure risk
  Critical system unavailable

P3 — MEDIUM (respond within 4 hours)
  Malware on single non-critical system
  Policy violation with data exposure risk
  Phishing email that bypassed controls
  Anomalous activity requiring investigation

P4 — LOW (respond within 24 hours)
  Phishing attempt (blocked or reported before impact)
  Policy violation without data exposure
  Failed attack attempt
  Security scan (probe with no exploitation)
```

### 3.3 SIEM Detection — Correlation Rules

```python
# Example Splunk SPL — Detect Credential Spraying
index=windows EventCode=4625                    # Failed logon
| stats count by src_ip, dest_host, user, _time
| where count > 50                              # >50 failures
| stats dc(user) as unique_users by src_ip      # Count unique targets
| where unique_users > 10                       # >10 different accounts
| alert "Credential Spraying Detected"

# Example — Detect Lateral Movement (PsExec)
index=windows EventCode=7045                    # New service installed
ServiceName="PSEXESVC"                          # PsExec service name
| join dest_host [search EventCode=4624 LogonType=3]  # Network logon
| table _time, src_ip, dest_host, user

# Example — Detect DCSync
index=windows EventCode=4662                    # Object access (AD)
Properties="*1131f6aa*" OR Properties="*1131f6ad*"  # Replication OIDs
| where NOT match(user, "^(?i)(MSOL_|AAD_|health)")  # Exclude sync accounts
| alert "Potential DCSync Activity"
```

### 3.4 Initial Triage Checklist

When an alert fires, analysts follow a structured triage:

```
□ 1. Acknowledge the alert — note time, source, analyst
□ 2. Gather initial data
     What triggered the alert? (log source, rule)
     What system/user is involved?
     What time did the activity begin?
     
□ 3. Determine if it's a true positive or false positive
     Check context: Is this expected behavior?
     Cross-reference other logs for corroboration
     
□ 4. Scope the incident
     Is this isolated to one system?
     Are other systems showing similar behavior?
     Is data exfiltration occurring?
     
□ 5. Classify severity (P1–P4)

□ 6. Escalate per the IRP
     Notify IR manager if P1/P2
     Begin documentation in case tracking system
     
□ 7. Preserve evidence
     Do NOT reimage or modify affected systems yet
     Capture volatile data first (memory, network connections, processes)
```

---

## 4. Windows Event Log Analysis

Key Windows event IDs for security analysis:

| Event ID | Description | Significance |
|----------|-------------|--------------|
| **4624** | Successful logon | LogonType 3=Network, 10=RemoteInteractive |
| **4625** | Failed logon | Brute force detection |
| **4648** | Logon with explicit credentials | Lateral movement indicator |
| **4688** | New process created | Command execution tracking |
| **4698** | Scheduled task created | Persistence mechanism |
| **4720** | User account created | Backdoor account |
| **4722** | User account enabled | Dormant account activation |
| **4732** | Member added to local admin group | Privilege escalation |
| **4776** | Credential validation | NTLM auth attempts |
| **5140** | Network share accessed | SMB lateral movement |
| **7045** | New service installed | PsExec, malware persistence |

---

## Key Vocabulary

| Term | Definition |
|------|------------|
| **CSIRT** | Computer Security Incident Response Team |
| **SOC** | Security Operations Center — 24/7 monitoring |
| **SIEM** | Security Information & Event Management — log aggregation + correlation |
| **IDS/IPS** | Intrusion Detection/Prevention System |
| **EDR** | Endpoint Detection & Response — deep endpoint telemetry |
| **Triage** | Initial rapid assessment to determine severity and scope |
| **True Positive** | Alert correctly identifies a real threat |
| **False Positive** | Alert fires on benign/expected activity |

---

## Review Questions

!!! question "Self-Assessment"
    1. Describe three detection sources that would be involved in identifying a ransomware infection in its early stages.
    2. A SOC analyst receives an alert: "Credential spraying detected — 200 failed logons from IP 192.168.5.100 across 45 accounts in 10 minutes." Walk through your triage process.
    3. Your IRP says P1 incidents require notifying the CISO within 15 minutes. How do you ensure this SLA is met at 3 AM?
    4. Write a SIEM correlation rule (in plain language) to detect a Golden Ticket attack.
    5. What is the difference between a tabletop exercise and a full-scale incident simulation? When should each be used?

---

## Further Reading

- 📄 [NIST SP 800-61 Rev. 2](https://csrc.nist.gov/publications/detail/sp/800-61/rev-2/final) — Computer Security Incident Handling Guide (free)
- 📄 [SANS Incident Handler's Handbook](https://www.sans.org/white-papers/33901/)
- 📄 [PICERL Framework](https://www.crowdstrike.com/cybersecurity-101/incident-response/incident-response-steps/) — CrowdStrike's 6-phase model
- 📄 [MITRE ATT&CK: Detection](https://attack.mitre.org/resources/working-with-attack/)
- 📄 Splunk SIEM Use Cases — Threat Detection Library

---

*[← Week 11](week11.md) &nbsp;|&nbsp; [Course Index](index.md) &nbsp;|&nbsp; [Week 13 →](week13.md)*
