---
title: "Security Practices, Risk Management, and Compliance"
week: 14
chapter: 14
course: SCIA-120
---

# Chapter 14: Security Practices, Risk Management, and Compliance

## Introduction

Security technology alone cannot protect an organization. Firewalls can be misconfigured. Antivirus can miss novel malware. Encryption protects data at rest but not the application that decrypts it. The gap between having security tools and actually being secure is bridged by *security practices* — the organizational processes, methodologies, governance frameworks, and human behaviors that turn technology into real protection.

This chapter examines the operational side of information security: how organizations identify what they need to protect and from whom, how they assess and manage risk in a structured way, how they prepare for and respond to inevitable security incidents, how they maintain operations through disruptions, and how they meet the legal and regulatory obligations that increasingly govern information security. Together, these practices constitute information security management — the discipline that transforms technical security into organizational security.

---

## 14.1 Information Security Risk Management

Risk management is the systematic process of identifying, assessing, and treating risks to organizational assets. It is not about eliminating all risk — that is impossible. It is about making informed decisions about which risks to accept, which to mitigate, and how much to invest in doing so.

**NIST SP 800-30** (*Guide for Conducting Risk Assessments*) is the foundational U.S. government framework for information security risk assessment. It defines risk as a function of the likelihood that a threat source will exploit a vulnerability, and the resulting adverse impact on the organization.

The risk management lifecycle consists of several iterative phases:

1. **Prepare for the Assessment**: Establish context — what systems are in scope? What are the organization's mission and risk tolerance?
2. **Conduct the Assessment**: Identify threat sources and events, vulnerabilities, likelihood, and impact.
3. **Communicate Results**: Document findings and present risk levels to decision-makers.
4. **Maintain the Assessment**: Update the risk picture as threats, vulnerabilities, and assets change.

### 14.1.1 Asset Identification and Valuation

You cannot protect what you do not know you have. Asset inventory is the starting point of risk management. An *information asset* is anything of value to the organization that processes, stores, or transmits information: servers, databases, applications, endpoint devices, network infrastructure, cloud resources, intellectual property, and customer data.

Assets are characterized by their *value* — both quantitative (replacement cost, revenue generated, regulatory penalty exposure) and qualitative (reputational value, operational criticality). A customer PII database may have a moderate hardware replacement cost but an enormous regulatory and reputational cost if breached. Asset valuation informs risk prioritization: higher-value assets warrant stronger protections.

### 14.1.2 Threat Identification and Threat Intelligence

A *threat* is a potential cause of an unwanted incident that could result in harm to the organization. Threats are characterized by their *source* (who or what is behind them) and *event* (what they might do).

Threat sources include:
- **Adversarial**: Nation-state actors, cybercriminal organizations, hacktivists, insider threats (malicious employees), script kiddies
- **Accidental**: Employees making configuration errors, developers introducing vulnerabilities inadvertently
- **Structural**: Hardware failures, software bugs, infrastructure degradation
- **Environmental**: Natural disasters, power outages, physical damage

*Threat intelligence* is information about known and emerging threats — adversary tactics, active campaigns, indicators of compromise (IOCs: IP addresses, domains, file hashes associated with malicious activity). Threat intelligence can be consumed from commercial providers (CrowdStrike, Mandiant), government sources (CISA advisories, FBI flash alerts), industry sharing groups (ISACs — Information Sharing and Analysis Centers), and open-source feeds (MISP, OpenCTI). Intelligence is operationalized into security controls: blocking known-malicious IPs, updating detection signatures, patching actively exploited vulnerabilities.

### 14.1.3 Risk Treatment Options

After identifying and assessing risks, organizations choose how to treat them:

- **Mitigate (Reduce)**: Implement controls to reduce the likelihood or impact of the risk. Patching vulnerabilities, adding MFA, encrypting data, and deploying firewalls are all mitigation measures.
- **Transfer**: Shift the financial consequences of the risk to a third party, typically through cyber insurance. Transfer does not eliminate the operational impact of a breach — it addresses the financial liability.
- **Accept**: Consciously decide to tolerate a risk because the cost of mitigation exceeds the expected loss, or because the residual risk after mitigation is within acceptable bounds. Risk acceptance should be documented and made by appropriate decision-makers.
- **Avoid**: Eliminate the activity that creates the risk. If a feature stores sensitive data and cannot be made secure, removing the feature avoids the risk.

> **Key Concept — Residual Risk**: The risk that remains after controls have been applied. No control eliminates risk entirely; residual risk is what the organization accepts after mitigation. Risk management documentation should clearly articulate residual risk levels.

### 14.1.4 Security Metrics and KPIs

Effective risk management requires measurement. Common security metrics and Key Performance Indicators (KPIs) include:

| Metric | Description |
|---|---|
| Mean Time to Detect (MTTD) | Average time from incident occurrence to detection |
| Mean Time to Respond (MTTR) | Average time from detection to containment/resolution |
| Patch latency | Average time from vulnerability disclosure to patch deployment |
| Vulnerability scan coverage | Percentage of assets included in regular vulnerability scanning |
| Phishing simulation click rate | Percentage of employees who click simulated phishing emails |
| MFA adoption rate | Percentage of accounts with MFA enabled |
| Security training completion rate | Percentage of staff completing required security training |

Metrics should be tied to business outcomes and reported to executive leadership to support informed security investment decisions.

---

## 14.2 Vulnerability Assessment and Penetration Testing

Understanding the weaknesses in your own systems before attackers find them is a cornerstone of proactive security. Two complementary approaches serve this purpose:

### 14.2.1 Vulnerability Assessment

A *vulnerability assessment* is a systematic examination of systems to identify known vulnerabilities — unpatched software, misconfigured services, default credentials, missing security controls. It is primarily a discovery exercise: here is what is wrong, here is the severity, here is how to fix it. Vulnerability assessments are typically performed using automated scanning tools: Nessus, Qualys, OpenVAS, Rapid7 InsightVM. They should be run regularly (weekly or monthly for critical systems) and after significant infrastructure changes.

Vulnerability scanners work by comparing discovered service versions, configurations, and responses against databases of known vulnerabilities (CVEs). They produce reports ranked by severity (Critical, High, Medium, Low, Informational) using standardized scoring (CVSS — Common Vulnerability Scoring System).

### 14.2.2 Penetration Testing

A *penetration test* (pentest) goes beyond vulnerability scanning: it involves skilled security professionals attempting to exploit identified vulnerabilities to demonstrate real-world attack impact. A pentest answers the question: "If an attacker exploited these vulnerabilities, how far could they get, and what could they access?"

The penetration testing lifecycle follows a structured methodology:

**1. Planning and Reconnaissance**: Agree on scope, rules of engagement, and objectives. Conduct passive reconnaissance (gathering publicly available information about the target: DNS records, employee information on LinkedIn, GitHub repositories, job postings) and active reconnaissance (port scanning, service enumeration, web application crawling).

**2. Scanning and Enumeration**: Use tools (Nmap, Masscan, Nikto, Burp Suite, OWASP ZAP) to identify open ports, services, operating system versions, web application frameworks, and potential vulnerabilities. Enumerate users, shares, and Active Directory objects in network environments.

**3. Exploitation**: Attempt to exploit identified vulnerabilities to gain unauthorized access. Metasploit, custom exploit code, or manual techniques may be used, depending on scope and vulnerability type. This phase validates whether vulnerabilities are actually exploitable in the target environment.

**4. Post-Exploitation**: After gaining an initial foothold, demonstrate impact: privilege escalation, lateral movement (pivoting from one compromised system to others), data exfiltration (copying sample data to prove access), credential harvesting, and persistence mechanisms.

**5. Reporting**: Document all findings, including evidence of successful exploitation, the attack chain (step-by-step description of how access was achieved), business impact, and remediation recommendations prioritized by severity.

**Types of Penetration Tests**:
- **Black box**: No prior knowledge of the target — simulates an external attacker.
- **Grey box**: Partial knowledge (e.g., an authenticated user account) — simulates a malicious insider or a compromised user.
- **White box**: Full access to documentation, source code, architecture diagrams — most thorough, most efficient, used for deep application security assessments.

---

## 14.3 Business Continuity and Disaster Recovery

Security is not only about preventing breaches — it is also about ensuring that business operations can continue through disruptions, whether from cyberattacks, natural disasters, hardware failures, or human error.

**Business Continuity Planning (BCP)** addresses how the organization maintains critical business functions during and after a disruptive event. It is broader than IT recovery: it includes people (who does what if key staff are unavailable), processes (how are critical functions performed manually if systems are down), and facilities (where do staff work if offices are inaccessible).

**Disaster Recovery (DR)** focuses specifically on restoring IT systems and data after a catastrophic failure. Key metrics:

- **Recovery Time Objective (RTO)**: The maximum acceptable downtime — how long the organization can function without a specific system. A payment processing system might have an RTO of minutes; an HR system might have an RTO of days.

- **Recovery Point Objective (RPO)**: The maximum acceptable data loss — how old can the most recently recovered backup be? An RPO of 4 hours means the organization accepts losing up to 4 hours of transactions. RPO drives backup frequency.

### 14.3.1 Backup Strategies: The 3-2-1 Rule

The *3-2-1 backup rule* is the foundational principle of data protection:
- **3**: Maintain at least three copies of data
- **2**: Store copies on at least two different types of media (e.g., local disk and cloud storage)
- **1**: Keep at least one copy offsite (geographically separate from the primary site)

Modern ransomware attacks specifically target backup systems to prevent recovery. Defenses include maintaining *offline* or *immutable* backups (cloud object storage with Object Lock, air-gapped tape backups) that ransomware cannot reach or encrypt. Backups must be tested regularly — an untested backup is not a backup.

DR strategies range in cost and recovery speed:
- **Cold site**: Backup facility with infrastructure but no running systems; recovery takes days.
- **Warm site**: Standby environment with systems partially configured; recovery takes hours.
- **Hot site / Active-Active**: Fully operational duplicate environment, continuously synchronized; recovery takes minutes or seconds via failover.

---

## 14.4 Incident Response

Despite best efforts, security incidents will occur. The ability to detect incidents quickly and respond effectively limits their impact — every minute of undetected intrusion is time for the attacker to steal more data, spread further, or cause more damage.

**NIST SP 800-61** (*Computer Security Incident Handling Guide*) defines the incident response lifecycle as six phases:

### 14.4.1 Preparation

Preparation occurs before any incident. It includes establishing and training an incident response team (IRT), creating and rehearsing incident response plans (playbooks for specific scenarios like ransomware, data breach, insider threat, DDoS), deploying detection and logging infrastructure (SIEM, EDR, network monitoring), and establishing communication protocols (who to notify, how to communicate securely during an incident).

### 14.4.2 Detection and Analysis

The detection phase involves identifying indicators of compromise (IOCs) or unusual activity that suggests an incident has occurred. Sources include SIEM alerts, EDR detections, user reports, threat intelligence feeds, and external notifications (e.g., from CISA, a partner organization, or a security researcher).

Analysis involves determining: What happened? When did it start? What systems are affected? Is it a true positive or false positive? What is the severity? Initial triage must be rapid — a ransomware deployment in progress requires immediate action; a single failed login attempt requires logging, not crisis response.

### 14.4.3 Containment

Containment limits the spread and impact of the incident. Short-term containment may involve isolating affected systems (removing network access), blocking malicious IPs or domains, disabling compromised accounts, and preserving evidence. Long-term containment involves implementing temporary fixes to allow business continuity while full eradication is prepared.

> **Warning — Evidence Preservation**: Containment actions must be balanced against evidence preservation. Shutting down a compromised system immediately may eliminate volatile evidence (memory, running processes, open network connections) needed for forensic analysis. IR teams should ideally capture memory images and network state before taking systems offline.

### 14.4.4 Eradication

Eradication removes the cause of the incident: deleting malware, closing exploited vulnerabilities, removing backdoors and persistence mechanisms (scheduled tasks, startup entries, web shells), resetting compromised credentials, and hardening affected systems.

### 14.4.5 Recovery

Recovery restores affected systems to normal operation. This involves restoring from known-clean backups, reimaging compromised systems (often preferable to trying to "clean" them in place), applying patches, and gradually restoring services while monitoring for signs of re-compromise.

### 14.4.6 Post-Incident Activity: Lessons Learned

After recovery, the IR team conducts a thorough review: What happened? How was it detected? Was the response effective? What could have been done faster or better? What controls would have prevented or limited the incident? Lessons learned should result in concrete improvements to security controls, detection capabilities, and IR procedures.

---

## 14.5 Digital Forensics Basics

Digital forensics is the science of collecting, preserving, analyzing, and presenting digital evidence in a manner that maintains its integrity and legal admissibility.

**Chain of Custody**: Every piece of evidence must have a documented chain of custody — a record of who collected it, when, where, how it was stored, who accessed it, and how it was transferred. Breaks in chain of custody can render evidence inadmissible in legal proceedings.

**Forensic Imaging**: Forensic analysis is conducted on a bit-for-bit copy of the original evidence (forensic image), not on the original itself. Tools like `dd`, FTK Imager, and EnCase create forensic images and generate cryptographic hash values (MD5 or SHA-256) that verify the image is identical to the original. Analyzing the original evidence risks contaminating or altering it.

**Analysis**: Digital forensic analysis techniques include timeline analysis (reconstructing the sequence of events from filesystem timestamps, log entries, and registry keys), memory forensics (extracting running processes, network connections, and encryption keys from RAM images), file carving (recovering deleted files from unallocated disk space), and network forensics (analyzing packet captures for evidence of data exfiltration or C2 communication).

---

## 14.6 Security Audits and Assessments

Security audits systematically evaluate whether security controls are in place, properly configured, and effective. Internal audits are conducted by organizational staff; external audits by independent third parties. Types include:

- **Compliance audits**: Verify adherence to specific regulatory requirements (HIPAA, PCI-DSS).
- **Technical security assessments**: Assess the technical security posture of systems (vulnerability scans, configuration reviews, penetration tests).
- **Security program reviews**: Assess the maturity and effectiveness of the overall security program against frameworks like NIST CSF (Cybersecurity Framework) or ISO 27001.

---

## 14.7 Legal and Regulatory Landscape

Information security exists within a framework of laws and regulations that impose obligations on organizations handling certain types of data.

### 14.7.1 U.S. Federal Regulations

**HIPAA (Health Insurance Portability and Accountability Act, 1996)**: Requires covered entities (healthcare providers, insurers) and their business associates to protect the confidentiality, integrity, and availability of electronic Protected Health Information (ePHI). The Security Rule specifies administrative, physical, and technical safeguards. Violations can result in civil penalties up to $1.9 million per category per year, and criminal penalties for willful neglect.

**FERPA (Family Educational Rights and Privacy Act, 1974)**: Protects the privacy of student education records at institutions receiving federal funding. Institutions may not disclose education records without written consent, with exceptions for legitimate educational interests.

**GLBA (Gramm-Leach-Bliley Act, 1999)**: Requires financial institutions to protect the security and confidentiality of customer financial information. The Safeguards Rule (updated 2023) requires a comprehensive written information security program including risk assessments, access controls, encryption, and incident response.

### 14.7.2 Payment Industry Standard

**PCI-DSS (Payment Card Industry Data Security Standard)**: A contractual standard (not a law) established by the major card brands (Visa, Mastercard, Amex, Discover). Organizations that store, process, or transmit cardholder data must comply with 12 PCI-DSS requirements covering network security, access control, vulnerability management, monitoring, and incident response. Non-compliance can result in fines and loss of the ability to process card payments.

### 14.7.3 International Regulations

**GDPR (General Data Protection Regulation, EU, 2018)**: The world's most comprehensive data protection regulation. Key principles include purpose limitation, data minimization, accuracy, storage limitation, and data subject rights (access, rectification, erasure, portability). Organizations outside the EU are subject to GDPR if they offer services to or monitor the behavior of EU residents. Maximum penalties are €20 million or 4% of global annual turnover, whichever is higher.

**CCPA (California Consumer Privacy Act, 2018, amended by CPRA 2020)**: Gives California residents rights similar to GDPR: the right to know what personal data is collected, the right to delete it, and the right to opt out of its sale. CCPA applies to for-profit businesses meeting revenue or data volume thresholds.

### 14.7.4 Computer Crime Laws

**CFAA (Computer Fraud and Abuse Act, 1986, amended multiple times)**: The primary U.S. federal computer crime statute. Criminalizes unauthorized access to computers, damage to computers, and computer fraud. The CFAA has been criticized for its vague definition of "unauthorized access," which has been interpreted to potentially criminalize activities like violating website terms of service. Security researchers have historically faced legal uncertainty under the CFAA.

**ECPA (Electronic Communications Privacy Act, 1986)**: Governs law enforcement access to electronic communications and stored data. ECPA has been criticized as outdated in the internet age, though it has been partially updated by the Stored Communications Act and CLOUD Act.

---

## 14.8 Ethics in Cybersecurity

Security professionals routinely have access to sensitive systems, data, and information about vulnerabilities in others' systems. This access creates ethical obligations:

- **Confidentiality**: Security professionals must protect sensitive information encountered during engagements and employment.
- **Responsible disclosure**: When a security researcher discovers a vulnerability in a product or service they do not own, ethical practice requires notifying the affected organization before public disclosure, giving them a reasonable time to patch (typically 90 days, as practiced by Google Project Zero and others). Public disclosure without notice (*full disclosure*) may increase risk to users; perpetual silence without disclosure leaves users vulnerable.
- **Scope adherence**: Penetration testers and security researchers must stay within agreed scope. Accessing systems beyond scope — even if technically possible — is unauthorized access under the CFAA.
- **Non-maleficence**: Security professionals should not use knowledge of vulnerabilities to cause harm, even to adversarial organizations.

Professional ethics frameworks include the (ISC)² Code of Ethics, EC-Council Code of Ethics, and CompTIA Code of Ethics, all emphasizing honesty, integrity, and protection of the public.

---

## Key Terms

- **Risk**: The likelihood that a threat will exploit a vulnerability, multiplied by the resulting impact.
- **Threat**: A potential cause of an unwanted security incident.
- **Vulnerability**: A weakness in a system, process, or control that can be exploited by a threat.
- **Asset**: Any resource of value to an organization that requires protection.
- **Risk Mitigation**: Implementing controls to reduce the likelihood or impact of a risk.
- **Risk Transfer**: Shifting financial consequences of risk (e.g., via cyber insurance).
- **Threat Intelligence**: Actionable information about adversary tactics, techniques, and indicators of compromise.
- **Vulnerability Assessment**: A systematic scan and review identifying known weaknesses in systems.
- **Penetration Testing**: Active, authorized exploitation of vulnerabilities to demonstrate real-world attack impact.
- **CVE (Common Vulnerabilities and Exposures)**: A standardized identifier for publicly known cybersecurity vulnerabilities.
- **CVSS (Common Vulnerability Scoring System)**: A standardized scoring system for vulnerability severity.
- **RTO (Recovery Time Objective)**: Maximum acceptable downtime for a system after a disruption.
- **RPO (Recovery Point Objective)**: Maximum acceptable data loss, expressed as time since last backup.
- **BCP (Business Continuity Planning)**: Organizational planning to maintain critical functions during disruptions.
- **Incident Response**: The structured process for detecting, containing, eradicating, and recovering from security incidents.
- **Chain of Custody**: A documented record of evidence handling to ensure integrity and legal admissibility.
- **Forensic Image**: A bit-for-bit copy of digital media used for analysis without altering the original.
- **HIPAA**: U.S. law protecting health information privacy and security.
- **GDPR**: EU regulation governing personal data protection and privacy.
- **PCI-DSS**: Industry standard for securing payment cardholder data.
- **CFAA (Computer Fraud and Abuse Act)**: Primary U.S. federal computer crime statute.
- **Responsible Disclosure**: Notifying vendors of vulnerabilities before public disclosure, allowing time for patching.
- **Residual Risk**: Risk remaining after controls have been applied.

---

## Review Questions

1. Explain the four risk treatment options (mitigate, transfer, accept, avoid) and give a concrete example of each in the context of an organization that operates a web application handling customer payment information.

2. Describe the difference between a vulnerability assessment and a penetration test. Why would an organization conduct both, rather than relying on one or the other?

3. A company experiences a ransomware attack on a Tuesday morning. Walk through how an incident response team should handle each phase of the NIST SP 800-61 incident response lifecycle, noting what actions are appropriate at each stage.

4. Explain the 3-2-1 backup rule. Why are offline or immutable backups particularly important in the context of ransomware attacks?

5. What is the difference between RTO and RPO? How do these metrics influence the design of a disaster recovery strategy?

6. A security researcher discovers a critical vulnerability in a widely used open-source library. Describe the ethical considerations involved and the steps the researcher should take under responsible disclosure principles.

7. An organization that processes health insurance claims is considering migrating to a cloud-based data processing platform. What HIPAA obligations must they fulfill, and what contractual agreement must they obtain from the cloud provider?

8. What is the CFAA, and why has it generated controversy in the security research community? What protections do researchers seek when conducting vulnerability research?

9. Describe the concept of chain of custody in digital forensics. What are the consequences if chain of custody is broken?

10. A CISO reports to the board that the organization's Mean Time to Detect (MTTD) is 45 days. What does this metric mean, why is it concerning, and what types of controls or improvements might reduce it?

---

## Further Reading

- National Institute of Standards and Technology. (2012). *Guide for Conducting Risk Assessments* (NIST SP 800-30 Rev. 1). https://csrc.nist.gov/publications/detail/sp/800-30/rev-1/final

- National Institute of Standards and Technology. (2012). *Computer Security Incident Handling Guide* (NIST SP 800-61 Rev. 2). https://csrc.nist.gov/publications/detail/sp/800-61/rev-2/final

- Sims, A., Sims, B., & Sims, C. (2022). *GDPR Compliance: A Practical Guide for Organizations*. IAPP Press.

- Harris, S., & Maymi, F. (2022). *CISSP All-in-One Exam Guide* (9th ed.). McGraw-Hill. (Chapters on Risk Management and Incident Response)

- Mandiant. (2023). *M-Trends Report: The State of Security*. https://www.mandiant.com/m-trends
