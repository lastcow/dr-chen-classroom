---
title: "Week 13 — IR: Containment, Eradication & Recovery"
description: NIST SP 800-61 Phases 3 & 4 — isolate threats, eradicate malware, restore operations, and conduct lessons-learned reviews.
---

# Week 13 — Incident Response: Containment, Eradication & Recovery

<div class="week-meta" markdown>
**Course Objectives:** CO5 &nbsp;|&nbsp; **Focus:** IR Phase III & IV &nbsp;|&nbsp; **Difficulty:** ⭐⭐⭐☆☆
</div>

---

## Learning Objectives

- [ ] Select and apply appropriate containment strategies based on incident type
- [ ] Perform systematic eradication of malware and attacker persistence
- [ ] Execute structured recovery operations with validation
- [ ] Conduct a formal post-incident review and produce lessons-learned documentation
- [ ] Apply legal and regulatory notification requirements correctly

---

## 1. Phase 3 — Containment, Eradication & Recovery

```
CONTAINMENT → Stop the bleeding
ERADICATION → Remove the attacker / malware
RECOVERY    → Restore normal operations
```

---

## 2. Containment Strategies

### 2.1 Short-Term vs. Long-Term Containment

| Strategy | Short-Term | Long-Term |
|----------|-----------|-----------|
| **Goal** | Immediately stop damage | Maintain operations while remediating |
| **Action** | Isolate affected systems | Patch, rebuild, or create workarounds |
| **Duration** | Hours | Days to weeks |
| **Example** | Unplug compromised server from network | Deploy patched replacement server |

### 2.2 Containment by Incident Type

**Malware / Ransomware:**
```
IMMEDIATE:
  1. Isolate affected system(s) — network disconnect (not power off)
     → Preserve memory contents for forensics
     → Prevent further lateral movement
  
  2. Identify blast radius
     → Query EDR for similar process activity across all endpoints
     → Check SIEM for same C2 IP/domain across network
     → Review network logs for lateral movement from patient zero
  
  3. Block malicious indicators at perimeter
     → Firewall rules blocking C2 IPs/domains
     → Email gateway rules blocking malicious sender
     → DNS sinkholing for C2 domains

DECISION POINT — To power off or not?
  Power off: Destroys volatile memory (running processes, decryption keys)
  Keep on: Risk of continued encryption / data exfiltration
  
  Best practice: Take memory dump FIRST, then network isolate
```

**Account Compromise:**
```
IMMEDIATE:
  1. Disable compromised account(s) — NOT just reset password
     → Attacker may have secondary persistence (new account, SSH key)
     → Active sessions must be killed
  
  2. Invalidate all active sessions (tokens, Kerberos tickets)
     net user compromised_user /active:no  (disable)
     krbtgt password reset ×2             (invalidate Kerberos tickets)
     
  3. Audit all actions taken by compromised account
     → SIEM query: all events where user = compromised_account
     → Focus: file access, email sent, systems touched
     
  4. Check for persistence backdoors
     → New accounts created during compromise window
     → Forwarding rules on email account
     → Changes to group memberships
```

**Data Exfiltration:**
```
IMMEDIATE:
  1. Block exfiltration channel (specific IP, domain, port)
  2. Preserve evidence of exfiltration (don't block without logging)
  3. Notify legal — regulatory notification may be required
  4. Determine what data was exfiltrated:
     → DLP logs, proxy logs, email logs
     → Volume of data transferred (timing + bytes)
     → Destination IP/domain correlation with threat intelligence
```

---

## 3. Network Isolation Techniques

```bash
# Windows — network isolation without powering off
netsh advfirewall set allprofiles firewallpolicy blockinbound,blockoutbound
# (Block all traffic except specific management access)

# Allow only IR team access
netsh advfirewall firewall add rule name="IR Access" \
  dir=in action=allow remoteip=192.168.1.50

# EDR-based isolation (preferred — maintains telemetry)
# CrowdStrike: Host containment via console/API
# SentinelOne: Network quarantine
# Carbon Black: Isolate endpoint

# Switch-level isolation
# Configure port as isolated VLAN (VLAN 999 = quarantine)
# SPAN port for continued traffic capture during investigation
```

---

## 4. Evidence Preservation

!!! warning "Evidence First, Remediation Second"
    Rushing to remediate destroys forensic evidence. Always capture evidence before changing any system state.

### 4.1 Order of Volatility

Collect most volatile data first (it disappears first):

```
MOST VOLATILE → LEAST VOLATILE

1. CPU registers, cache        (lost on power off)
2. Running processes           (lost on power off)
3. Network connections         (lost on power off)
4. Memory (RAM)                (lost on power off)
5. Swap/pagefile               (lost on power off)
6. File system timestamps      (may change on access)
7. Disk content                (relatively stable)
8. Remote logging (SIEM)       (most stable)
9. Physical media              (stable)
```

### 4.2 Memory Acquisition

```bash
# Windows memory dump
# WinPmem (open source)
winpmem_mini_x64_rc2.exe memory.raw

# DumpIt (commercial-grade, free version)
DumpIt.exe /OUTPUT C:\forensics\memory.raw

# Belkasoft RAM Capturer (user-friendly)

# Linux memory acquisition
# LiME (Linux Memory Extractor — kernel module)
sudo insmod lime-$(uname -r).ko "path=/tmp/memory.lime format=lime"

# Verify integrity
sha256sum memory.raw > memory.raw.sha256
```

### 4.3 Chain of Custody

Every piece of evidence must be documented:

```
CHAIN OF CUSTODY FORM:
  Case Number: IR-2026-0001
  
  Evidence Item #1:
    Description: Dell Latitude 7490, SN: ABC123456
    Collected by: [Name, Role]
    Date/Time: 2026-04-14 14:32 EDT
    Location: Building A, Floor 3, Desk 42
    Condition: Powered on, network cable removed
    SHA-256 (disk image): abc123...
    
  Transfer log:
    From: Field Analyst → To: Forensic Lab
    Date/Time: 2026-04-14 15:00 EDT
    Method: Hand carry, sealed evidence bag
    Received by: [Lab Technician Name]
```

---

## 5. Eradication

After containment, remove all attacker presence:

### 5.1 Eradication Checklist

```
□ MALWARE REMOVAL
  Identified all affected systems (don't assume it's just the first one found)
  Removed malware from all affected systems
  Verified with multiple AV/EDR tools (one tool may miss)
  
□ ATTACKER PERSISTENCE REMOVAL
  Disabled/deleted backdoor accounts
  Removed scheduled tasks / services created by attacker
  Cleaned registry Run keys
  Removed web shells from web servers
  Revoked SSH keys / certificates added by attacker
  
□ VULNERABILITY PATCHING
  Patched the vulnerability that allowed initial access
  Applied additional patches to reduce attack surface
  
□ CREDENTIAL RESET
  Forced password reset for all potentially compromised accounts
  Reset service account passwords
  If DA compromised: reset krbtgt password TWICE (24h apart)
  Rotated API keys, certificates, application credentials
  
□ VERIFICATION
  Threat hunting across all endpoints for same IoCs
  Confirm C2 communication has ceased
  Review SIEM for recurrence of attack patterns
```

---

## 6. Recovery

### 6.1 System Restoration Process

```
OPTION A: Restore from known-good backup
  Verify backup predates compromise
  Restore to isolated environment first
  Verify integrity → reconnect to production
  
OPTION B: Rebuild from scratch
  Format and reinstall OS
  Apply all patches before reconnecting to network
  Restore only data (not applications) from backup
  
OPTION C: Partial cleanup (high-risk)
  Only for time-critical systems where rebuild isn't feasible
  Remove known malware components
  Monitor intensively for recurrence
  Plan full rebuild at next maintenance window
```

### 6.2 Validation Before Return to Production

```
□ Antivirus full scan (clean result)
□ EDR showing no active threats or suspicious behavior
□ All critical patches applied (OS + applications)
□ Credentials changed (local admin, service accounts)
□ Monitoring/logging verified (SIEM ingesting events)
□ Backup verified (clean known-good backup exists)
□ Business owner sign-off
□ Security team sign-off
```

---

## 7. Phase 4 — Post-Incident Activity

### 7.1 Lessons Learned Meeting

Schedule within **two weeks** of incident closure:

```
AGENDA:
  1. Incident timeline (neutral, factual)
  2. What worked well?
  3. What gaps did we discover?
  4. Root cause analysis (not blame — 5 Whys technique)
  5. Action items with owners and due dates
  6. IRP updates required
  
PARTICIPANTS:
  IR team, SOC, IT ops, legal, management (as appropriate)
  External forensics firm (if engaged)
```

### 7.2 Incident Report

```
EXECUTIVE SUMMARY (1 page):
  Incident type, date range, business impact, key decisions made

DETAILED TIMELINE:
  Chronological log of every action with timestamps

ROOT CAUSE:
  Technical cause + organizational contributing factors

IMPACT ASSESSMENT:
  Systems affected, data potentially exposed, downtime cost

REMEDIATION:
  What was done to contain, eradicate, and recover

LESSONS LEARNED & RECOMMENDATIONS:
  Specific, actionable items with priority ratings
```

### 7.3 Regulatory Notification Requirements

| Regulation | Notification Trigger | Deadline | To Whom |
|------------|---------------------|----------|---------|
| **GDPR** | Personal data of EU residents | 72 hours | DPA (Data Protection Authority) |
| **CCPA** | CA resident PII | Expeditiously | Affected individuals |
| **HIPAA** | PHI of patients | 60 days (breach of 500+: 60 days to HHS + media) | HHS |
| **SEC Rule** | Material cybersecurity incident | 4 business days | SEC Form 8-K |
| **PCI DSS** | Cardholder data exposure | Immediately | Card brands + acquiring bank |
| **State Laws** | Varies | 30–90 days (varies by state) | State AG + individuals |

---

## Key Vocabulary

| Term | Definition |
|------|------------|
| **Containment** | Limiting spread and damage of an active incident |
| **Eradication** | Complete removal of attacker presence from environment |
| **Recovery** | Restoring systems to normal, verified-clean operations |
| **Post-Incident Review** | Structured lessons-learned process after incident closure |
| **Chain of Custody** | Documentation trail proving evidence integrity |
| **Order of Volatility** | Priority order for evidence collection based on data persistence |
| **Sinkholing** | Redirecting malicious DNS queries to a controlled server |
| **Blast Radius** | Scope of systems and data affected by an incident |

---

## Review Questions

!!! question "Self-Assessment"
    1. At 6 AM, ransomware is encrypting files on a file server. Walk through your containment actions for the first 30 minutes. What do you do in what order?
    2. Why is it important to reset the krbtgt account password **twice** when recovering from a domain admin compromise?
    3. A forensic investigator powers off a compromised laptop to "preserve evidence." What critical evidence was just destroyed?
    4. Your organization processes EU customer data. You confirm a breach occurred 74 hours ago. What are your legal obligations?
    5. Describe the 5 Whys root cause analysis technique applied to an incident where an employee clicked a phishing link.

---

## Further Reading

- 📄 [NIST SP 800-61 Rev. 2](https://csrc.nist.gov/publications/detail/sp/800-61/rev-2/final)
- 📄 SANS FOR508 — Advanced Incident Response
- 📄 [CISA Ransomware Guide](https://www.cisa.gov/stopransomware/ransomware-guide)
- 📄 [GDPR Notification Requirements](https://gdpr.eu/article-33-notification-of-a-personal-data-breach/)
- 📖 *Incident Response & Computer Forensics, 3rd Ed.* — Luttgens, Pepe, Mandia

---

*[← Week 12](week12.md) &nbsp;|&nbsp; [Course Index](index.md) &nbsp;|&nbsp; [Week 14 →](week14.md)*
