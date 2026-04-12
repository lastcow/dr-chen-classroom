---
title: "Chapter 10: Security Models and Security Policies"
chapter: 10
week: 10
course: SCIA-120
description: "A comprehensive study of formal security models, access control paradigms, Zero Trust architecture, security policy development, and major security frameworks including NIST CSF and ISO 27001."
---

# Chapter 10: Security Models and Security Policies

## Introduction

Building a secure system requires more than technical controls — it requires a coherent theoretical foundation that defines *what* security means for a given system, *who* is allowed to do *what* to *which* resources, and *how* organizational commitments to security are expressed and enforced. This is the domain of security models and security policies.

**Security models** are formal, often mathematical descriptions of security properties that a system must satisfy. They provide the conceptual framework that underlies access control implementations: the rules that determine who can read, write, execute, or otherwise interact with system objects. **Security policies** are the organizational expression of security requirements: written documents that define rules of behavior, acceptable use, and operational procedures. **Security frameworks** provide structured guidance for building comprehensive information security programs.

These three elements — models, policies, and frameworks — together form the governance layer of information security, translating abstract security requirements into enforceable rules and reproducible practices.

---

## 10.1 Formal Security Models

### The Bell-LaPadula Model

The **Bell-LaPadula (BLP) model**, developed by David Bell and Leonard LaPadula for the U.S. Department of Defense in the 1970s, is a formal mathematical model focused on **confidentiality**. It is designed for environments where information must be strictly controlled based on classification levels (e.g., Unclassified, Confidential, Secret, Top Secret) — a *multilevel security* system.

BLP defines two core security properties:

1. **The Simple Security Property ("no read up")**: A subject (user/process) at a given security level may not read objects at a higher security level. A user with Secret clearance cannot read Top Secret documents.

2. **The \*-Property (Star Property, "no write down")**: A subject at a given security level may not write to objects at a lower security level. A user with Top Secret clearance cannot write to (and potentially leak classified information into) an Unclassified document.

The intuition behind "no write down" is critical: even if a high-clearance user's intent is benign, allowing writes down creates a channel through which classified information could leak (intentionally or through indirect effects) to lower classification levels.

BLP also includes the **Discretionary Security Property**, which defers to an access control matrix for additional restrictions beyond the mandatory classification-based rules.

> 📌 **Key Concept**: Bell-LaPadula *only* addresses confidentiality. It explicitly permits a high-privilege subject to corrupt lower-integrity data — the "no write down" rule, counterintuitively, means a high-clearance user *can* write down (and potentially corrupt) lower-classified documents. This gap led directly to the development of integrity-focused models.

### The Biba Integrity Model

The **Biba model**, developed by Kenneth Biba in 1977, is the logical complement to Bell-LaPadula, focusing on **integrity** rather than confidentiality. It uses a similar structure of subjects with integrity levels and objects with integrity levels, but with inverted rules:

1. **Simple Integrity Property ("no read down")**: A subject may not read objects with a lower integrity level. A high-integrity process should not read data from an untrusted (low-integrity) source, as it could corrupt the high-integrity process's operations or conclusions.

2. **Integrity \*-Property ("no write up")**: A subject may not write to objects with a higher integrity level. An untrusted process cannot corrupt high-integrity data.

The intuition: integrity is contaminated by reading low-integrity data (garbage in, garbage out) and should be protected from writes by untrusted subjects.

Biba and BLP together illustrate a fundamental tension: applying both models simultaneously in a strict system would be extremely restrictive. In practice, real systems use approximations and trust management rather than strict formal models.

### The Clark-Wilson Integrity Model

The **Clark-Wilson model**, proposed by David Clark and David Wilson in 1987, takes a different approach to integrity, grounded in commercial business practices rather than military classification systems. It recognizes that integrity in a business context means something specific: data should only be modified through authorized, auditable procedures that maintain internal consistency.

The model introduces several key concepts:

- **Constrained Data Items (CDIs)**: Data items whose integrity must be maintained (e.g., account balances, medical records).
- **Unconstrained Data Items (UDIs)**: Input data that has not yet been validated (user input, external data).
- **Integrity Verification Procedures (IVPs)**: Programs that confirm CDIs are in a valid state (e.g., that debits and credits balance).
- **Transformation Procedures (TPs)**: The only programs allowed to modify CDIs; they must maintain the validity of CDIs.

Clark-Wilson enforces integrity through *separation of duty* (no single person can complete a sensitive transaction alone), *auditing* (all modifications are logged), and *well-formed transactions* (data can only be modified through authorized TPs). This maps naturally to database transactions, accounting systems, and ERP applications.

### The Brewer-Nash (Chinese Wall) Model

The **Brewer-Nash model**, proposed by David Brewer and Michael Nash in 1989, addresses **conflicts of interest** in commercial consulting and financial contexts. The classic scenario: a consulting firm works for multiple competing clients in the same industry, such as competing investment banks. Consultants who have accessed information about one bank should not be able to access information about competing banks.

The model introduces **conflict of interest classes**: groups of companies whose information should be kept separate. A subject who has accessed data within a conflict class may not subsequently access data from any other company in the same conflict class — essentially building a dynamically growing "Chinese wall" around the subject based on their access history.

This model is unique in that access decisions are not purely static; they depend on the subject's history of accesses. It is directly relevant to compliance requirements in financial services (FINRA rules, MiFID II) governing information barriers between trading and investment banking divisions.

---

## 10.2 Access Control Models

### Discretionary Access Control (DAC)

In **Discretionary Access Control (DAC)**, the owner of a resource controls access to it. The owner can grant or revoke permissions to other subjects at their own discretion — hence "discretionary." The canonical example is the Unix file permission system: the file owner controls read/write/execute permissions for themselves, their group, and others.

DAC is flexible and intuitive, but it has a fundamental weakness: once a subject has been granted access, they may be able to pass that access to others (through copying files, changing permissions, or other mechanisms). This creates the **Trojan horse problem**: malware running as a user with read access to a file can exfiltrate that file. DAC provides no protection against compromised subjects acting within their authorized permissions.

### Mandatory Access Control (MAC)

In **Mandatory Access Control (MAC)**, access control is determined by system policy rather than resource owners' discretion. The system assigns security labels (classifications) to both subjects (clearance levels) and objects (sensitivity levels), and access decisions are enforced by the operating system based on these labels, not by user preferences.

MAC systems implement the Bell-LaPadula model (or variants of it) in practice. Users cannot override MAC policies — they cannot share files across classification levels even if they want to. **SELinux (Security-Enhanced Linux)** and **AppArmor** are MAC implementations used in Linux systems; they enforce mandatory access controls even on root processes, limiting the damage a compromised privileged process can do.

MAC is much more restrictive than DAC and is primarily used in high-security environments: government and military systems, secure operating system kernels, and some enterprise security products.

### Role-Based Access Control (RBAC)

**Role-Based Access Control (RBAC)** is the most widely used access control model in enterprise environments. Rather than assigning permissions directly to individual users, RBAC assigns permissions to **roles** (job functions — database administrator, help desk agent, payroll clerk, read-only auditor), and users are assigned to roles.

This abstraction provides several important security benefits:

- **Least privilege**: Users can be assigned to roles that provide only the permissions needed for their job function.
- **Separation of duties**: Sensitive functions can be distributed across multiple roles that no single user holds simultaneously (e.g., the role that creates a vendor cannot also be the role that approves payment to that vendor).
- **Simplified administration**: Onboarding a new employee in a role requires only assigning them to appropriate roles, not configuring dozens of individual permissions. Offboarding removes them from all roles.

RBAC is formalized in the NIST RBAC model (ANSI/INCITS 359-2004), which defines core RBAC, hierarchical RBAC (roles can inherit permissions from other roles), and constrained RBAC (with separation of duty constraints).

### Attribute-Based Access Control (ABAC)

**Attribute-Based Access Control (ABAC)** is a more expressive and flexible model in which access decisions are made based on a set of attributes associated with the subject (user), the object (resource), the action, and the environment. A policy engine evaluates these attributes against policies expressed as rules:

*Example rule*: A subject with attributes `{department: "HR", clearance: "confidential", role: "manager"}` may access an object with attributes `{type: "personnel_record", classification: "confidential"}` when the action is `{read}` and the environment is `{time: "business_hours", location: "on-premises"}`.

ABAC is significantly more powerful than RBAC — it can express fine-grained, context-sensitive policies that RBAC cannot easily represent — but it is more complex to manage and reason about. ABAC is implemented through policy languages like **XACML (eXtensible Access Control Markup Language)** and is increasingly used in cloud platforms (AWS IAM policies are essentially ABAC) and zero trust architectures.

---

## 10.3 Zero Trust Architecture

### The Principle

**Zero Trust Architecture (ZTA)** represents a fundamental shift in security philosophy from the traditional "castle and moat" model (everything inside the network perimeter is trusted; everything outside is untrusted) to the principle: **"never trust, always verify."**

The traditional perimeter model assumed that once a device was inside the corporate network firewall, it was essentially trusted. Modern threats have shattered this assumption: sophisticated attackers routinely breach perimeters through phishing, supply chain compromises, and stolen credentials; remote work has dissolved the perimeter entirely; cloud adoption means critical resources no longer reside "inside" the network.

Zero Trust asserts that:
1. **No implicit trust**: No user, device, or network location is inherently trusted, regardless of whether they are "inside" the network.
2. **Verify explicitly**: All access must be authenticated and authorized using all available signals: user identity, device health, location, time, behavior analytics.
3. **Least privilege access**: Provide the minimum access necessary for the task, for the minimum necessary duration.
4. **Assume breach**: Design and operate as if the attacker is already inside. Minimize blast radius through microsegmentation and monitor continuously for anomalous behavior.

### Zero Trust Implementation

The **NIST Special Publication 800-207** (Zero Trust Architecture) provides the authoritative framework. Key components include:

- **Strong Identity Verification**: MFA, certificate-based device authentication, identity governance.
- **Device Health Verification**: Continuous compliance checking (OS patch level, EDR presence, disk encryption) before granting access.
- **Microsegmentation**: Network is divided into small segments, each requiring explicit authorization to cross. This contains lateral movement.
- **Continuous Monitoring and Validation**: Access is continuously re-evaluated. Anomalous behavior triggers step-up authentication or session termination.
- **Data-centric Security**: Protect the data itself (classification, encryption) rather than relying on network boundaries.

Zero Trust is not a product — it is an architecture and set of principles. It is implemented progressively through a combination of identity solutions (IAM), endpoint management (MDM/EDR), network microsegmentation, and data protection controls.

---

## 10.4 Defense in Depth

**Defense in depth** is a security principle derived from military strategy: rather than relying on any single security control, implement multiple independent layers of security such that the failure or bypass of any one layer does not result in a total breach.

Layers of defense in a well-designed system include:
- Physical security (controlled access to data centers, secure hardware)
- Network perimeter security (firewalls, IPS)
- Network segmentation (VLANs, microsegmentation)
- Host security (hardened OS, EDR, host firewall, patch management)
- Application security (secure coding, WAF, SAST/DAST)
- Data security (encryption at rest and in transit, DLP)
- Identity and access management (MFA, least privilege, PAM)
- Monitoring and detection (SIEM, SOC)
- Incident response capability

Defense in depth does not mean redundant controls — it means diverse controls at different layers that address different threat scenarios. A firewall and a WAF are both "security controls," but they address different threats and should both be present.

---

## 10.5 Security Policies

### What Is a Security Policy?

A **security policy** is a formal document that expresses an organization's security requirements, rules, and expected behaviors. Policies provide the bridge between abstract security objectives and concrete operational practices. They communicate management's commitment to security, establish standards that technical controls implement, and provide the baseline for compliance and enforcement.

A policy document has three essential attributes:
1. **Clarity**: It must be unambiguous — readers should not be able to interpret it in different ways.
2. **Enforceability**: It must be possible to verify whether the policy is being followed.
3. **Completeness**: It must address all scenarios relevant to its scope.

Policies operate in a hierarchy: a high-level **security policy** sets overall direction; **standards** define specific, mandatory requirements that implement the policy; **guidelines** provide advisory recommendations; **procedures** describe step-by-step processes for carrying out activities.

### Types of Security Policies

**Acceptable Use Policy (AUP)**: Defines what constitutes acceptable and unacceptable use of organizational IT resources (computers, email, internet, cloud services). Every employee should acknowledge the AUP as part of onboarding. Key elements: authorized purposes, prohibited content/activities, monitoring notice, consequences for violations.

**Data Classification Policy**: Establishes a scheme for categorizing organizational data based on sensitivity (e.g., Public, Internal, Confidential, Restricted) and defines the handling requirements for each category — storage, transmission, access controls, retention, and disposal.

**Password Policy**: Defines requirements for password creation (length, complexity), management (not reusing passwords, not sharing), and storage. Modern guidance (NIST SP 800-63B) has moved away from frequent mandatory rotations (which lead to weak passwords with predictable patterns) toward longer passphrases, breach checking, and requiring MFA.

**BYOD (Bring Your Own Device) Policy**: Addresses the security implications of employees using personal devices for work. Defines what access personal devices may have (often limited to email and collaboration tools, not core business systems), required security controls on personal devices (MDM enrollment, passcode, encryption), and what data the organization may manage or wipe from the device.

**Incident Response Policy**: Defines the organization's approach to detecting, containing, eradicating, and recovering from security incidents. Specifies roles and responsibilities, escalation procedures, communication protocols (internal and external — regulatory notifications, customer notifications), and documentation requirements.

**Remote Access Policy**: Defines requirements for employees accessing corporate resources from outside the office — VPN requirements, device security standards, prohibited activities on remote access connections.

**Vendor/Third-Party Security Policy**: Addresses security requirements for vendors, contractors, and other third parties with access to organizational systems or data, reflecting the risk that third parties can be an entry point for attackers (as demonstrated by the Target breach in 2013, where attackers entered through an HVAC vendor's compromised credentials).

### Policy Development Lifecycle

Security policies are not written once and forgotten — they require ongoing care:

1. **Identify Need**: What risk or compliance requirement is driving this policy? What behavior is it intended to govern?
2. **Draft**: Working group involving security, legal, HR, business stakeholders. Policies that security writes in isolation without business input are often impractical or ignored.
3. **Review and Approve**: Legal review (compliance implications), HR review (enforceability), executive approval (signals organizational commitment).
4. **Communicate and Train**: Employees cannot follow a policy they don't know about. Training, awareness campaigns, and acknowledgment processes.
5. **Enforce**: Technical controls (where possible) reinforce policies. Violations must have consequences, or the policy loses credibility.
6. **Review and Update**: Annual review at minimum; triggered review when technology, business, or threat landscape changes significantly.

---

## 10.6 Security Frameworks

### NIST Cybersecurity Framework (CSF)

The **NIST Cybersecurity Framework (CSF)**, first published in 2014 and updated as CSF 2.0 in 2024, provides voluntary guidance for organizations to manage and reduce cybersecurity risk. It is organized around six core functions (CSF 2.0 added "Govern"):

| Function | Purpose |
|----------|---------|
| **Govern** | Establish cybersecurity strategy, risk appetite, governance structures, and accountability |
| **Identify** | Understand the organization's assets, risks, and vulnerabilities |
| **Protect** | Implement appropriate safeguards to ensure delivery of critical services |
| **Detect** | Identify the occurrence of a cybersecurity event |
| **Respond** | Take action regarding a detected cybersecurity incident |
| **Recover** | Maintain resilience and restore capabilities after an incident |

Each function contains **categories** and **subcategories** (specific outcomes) that can be mapped to specific technical controls. The framework is voluntary but has been widely adopted and referenced in U.S. government contracts and regulatory guidance.

The NIST CSF uses the concept of **Implementation Tiers** (1-4, from Partial to Adaptive) to characterize the maturity of an organization's risk management practices, and **Profiles** to express the current state and target state of an organization's security posture.

### ISO/IEC 27001 and 27002

**ISO/IEC 27001** is an international standard for **Information Security Management Systems (ISMS)**. Unlike NIST CSF, which is a flexible framework, ISO 27001 is a formal standard against which organizations can be certified through independent audits. Certification demonstrates to customers, partners, and regulators that the organization has a systematic, documented, and continuously improving information security management program.

ISO 27001 specifies requirements for establishing, implementing, maintaining, and continuously improving an ISMS. It requires:
- Defining the scope of the ISMS
- Conducting a systematic risk assessment
- Selecting and implementing controls
- Documenting policies and procedures
- Measuring and reviewing effectiveness
- Continuously improving

**ISO/IEC 27002** is the companion code of practice that provides implementation guidance for the 93 controls organized across four themes in the 2022 revision: Organizational Controls, People Controls, Physical Controls, and Technological Controls. Organizations select and implement controls from 27002 based on their risk assessment.

### CIS Controls

The **CIS Critical Security Controls (CIS Controls)**, maintained by the Center for Internet Security, are a prioritized set of 18 security controls derived from analysis of the most common attack patterns. They are organized into three Implementation Groups (IGs) of increasing maturity:

- **IG1 (Basic Cyber Hygiene)**: Controls 1-6, addressing inventory, patching, access control, and awareness. Suitable for all organizations.
- **IG2 (Expanded)**: IG1 plus additional controls for organizations with more resources and greater risk.
- **IG3 (Organizational)**: The full set, for organizations facing sophisticated threats.

The CIS Controls are particularly valued because they are prescriptive and prioritized — they tell you not just what to do, but in what order to do it based on risk reduction impact.

### Compliance vs. Security

An important — and frequently misunderstood — distinction: **compliance is not security**. Compliance means meeting the requirements of a specific standard, regulation, or framework at a specific point in time. Security means actually reducing risk effectively. The two often overlap but are not identical.

Organizations that treat compliance as a goal in itself (rather than as a proxy for security) frequently achieve audit pass grades while remaining practically vulnerable. Compliance frameworks are designed for broad applicability across many different organizations and contexts — they cannot perfectly match the specific risk profile of any particular organization. Effective security programs use compliance frameworks as a *floor*, not a ceiling, layering in additional controls based on their specific threat model and risk appetite.

### Security Governance

**Security governance** refers to the framework of leadership, organizational structures, accountability, and processes through which security decisions are made and enforced. Key elements include:

- **Chief Information Security Officer (CISO)**: Executive ownership of the security program, reporting to the CEO or Board.
- **Security Steering Committee**: Cross-functional body (IT, legal, HR, business units, finance) providing oversight and aligning security with business objectives.
- **Risk Management**: Formal processes for identifying, assessing, treating, and monitoring information security risk, integrated with enterprise risk management.
- **Metrics and Reporting**: Regular reporting to leadership on security posture, incidents, compliance status, and program progress.
- **Third-Party Risk Management (TPRM)**: Governance of vendor and supplier security risk through due diligence, contractual requirements, and ongoing monitoring.

Effective governance ensures that security is not purely a technical function — it is a business function with executive sponsorship, adequate resources, and clear accountability.

---

## Key Terms

- **Security Model**: A formal description of security properties and rules that a system must satisfy.
- **Bell-LaPadula Model**: A formal security model focused on confidentiality; "no read up, no write down."
- **Biba Model**: A formal security model focused on integrity; "no read down, no write up."
- **Clark-Wilson Model**: An integrity model emphasizing well-formed transactions, separation of duty, and auditing.
- **Brewer-Nash (Chinese Wall) Model**: An access control model preventing conflicts of interest by dynamically restricting access based on prior access history.
- **DAC (Discretionary Access Control)**: Access controlled by the resource owner's discretion.
- **MAC (Mandatory Access Control)**: Access controlled by system-enforced policy based on security labels.
- **RBAC (Role-Based Access Control)**: Access granted through roles assigned to users based on job function.
- **ABAC (Attribute-Based Access Control)**: Access decisions based on attributes of the subject, object, action, and environment.
- **Zero Trust Architecture**: A security philosophy and architecture based on "never trust, always verify," with no implicit network trust.
- **Microsegmentation**: Dividing the network into small zones, each requiring explicit authorization to access.
- **Defense in Depth**: Layering multiple diverse security controls so that failure of one does not constitute total breach.
- **Security Policy**: A formal document expressing an organization's security requirements, rules, and behavioral expectations.
- **AUP (Acceptable Use Policy)**: A policy defining acceptable and prohibited uses of organizational IT resources.
- **Data Classification Policy**: A policy categorizing data by sensitivity and defining handling requirements for each category.
- **BYOD (Bring Your Own Device)**: A policy and practice allowing employees to use personal devices for work.
- **ISMS (Information Security Management System)**: A systematic approach to managing information security risks, as formalized in ISO 27001.
- **NIST CSF (Cybersecurity Framework)**: A voluntary framework for managing cybersecurity risk organized around Govern/Identify/Protect/Detect/Respond/Recover.
- **ISO 27001**: International standard for information security management system requirements and certification.
- **CIS Controls**: A prioritized set of 18 security controls derived from common attack patterns.
- **Separation of Duty**: A control principle requiring that no single individual can complete a sensitive transaction alone.
- **Least Privilege**: The principle of granting subjects only the minimum permissions necessary for their function.
- **Compliance vs. Security**: Compliance is meeting framework requirements; security is actually reducing risk — the two are related but not identical.
- **CISO (Chief Information Security Officer)**: Executive responsible for an organization's information security program.

---

## Review Questions

1. Explain the Bell-LaPadula model's two core properties ("no read up" and "no write down") using concrete examples from a military classification scenario. Why is BLP unable to provide complete security on its own?

2. The Biba model appears to be the "mirror image" of Bell-LaPadula. Explain how this is true in terms of the model's rules, and explain why the intuition behind Biba's properties makes sense from an integrity perspective.

3. Compare the Clark-Wilson model's approach to integrity with Biba's approach. What real-world scenarios is Clark-Wilson better suited to, and what mechanisms does it use that Biba does not?

4. A financial services firm has a team that provides advice to multiple competing investment banks. Explain how the Brewer-Nash (Chinese Wall) model addresses the conflict of interest this creates, and describe how the access restrictions evolve over time.

5. Compare DAC, MAC, and RBAC. For each, describe a scenario where it would be the most appropriate access control model and explain why.

6. An organization is considering implementing Zero Trust Architecture to replace its traditional VPN-and-perimeter model. Describe the key principles of ZTA, the limitations of the traditional model it addresses, and three specific technical changes that would be required in the organization's infrastructure.

7. A new employee violates the organization's Acceptable Use Policy by using their work laptop for personal cryptocurrency mining. The AUP exists and the employee acknowledged it during onboarding. Walk through the considerations — from policy enforcement to disciplinary action — that should govern the organization's response.

8. Compare the NIST Cybersecurity Framework (CSF) and ISO 27001 as security frameworks. What are the key differences in their purpose, structure, and applicability? Under what circumstances might an organization pursue ISO 27001 certification rather than just using the NIST CSF?

9. An organization passes its annual PCI-DSS audit but suffers a significant cardholder data breach six months later. How is this possible? What does this illustrate about the relationship between compliance and security?

10. Describe the security governance structures that a large enterprise should have in place. What role should the CISO play, and how should security decisions be integrated with business decision-making?

---

## Further Reading

1. Bell, D.E., & LaPadula, L.J. (1976). *Secure Computer Systems: Unified Exposition and Multics Interpretation* (ESD-TR-75-306). MITRE Corporation. — The original Bell-LaPadula technical report.

2. Ross, R., et al. (2020). *Zero Trust Architecture* (NIST SP 800-207). National Institute of Standards and Technology. Available at: https://csrc.nist.gov/publications/detail/sp/800-207/final

3. NIST. (2024). *NIST Cybersecurity Framework 2.0*. National Institute of Standards and Technology. Available at: https://www.nist.gov/cyberframework

4. Whitman, M.E., & Mattord, H.J. (2021). *Management of Information Security* (6th ed.). Cengage Learning. — Comprehensive coverage of security policy, governance, and frameworks.

5. Shostack, A., & Stewart, A. (2007). *The New School of Information Security*. Addison-Wesley. — A thought-provoking examination of how to build effective security programs grounded in evidence and sound risk management.
