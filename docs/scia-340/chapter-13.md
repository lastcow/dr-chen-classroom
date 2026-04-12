---
title: "Chapter 13: Compliance, Regulations, and Database Security Standards"
week: 13
chapter: 13
course: SCIA-340
---

# Chapter 13: Compliance, Regulations, and Database Security Standards

## Introduction

Database security does not exist in a regulatory vacuum. The data organizations store — credit card numbers, health records, personal identifying information, financial transactions, student grades — is subject to a growing web of legal and industry-mandated requirements. These regulations were not created to make database administrators' lives difficult; they emerged from a history of breaches, misuse, and exploitation that caused tangible harm to individuals. Understanding the regulatory landscape is not merely a compliance checkbox exercise — it directly shapes how you design schemas, configure access controls, implement encryption, retain logs, and respond to incidents.

This chapter surveys the major regulations and standards that govern database security in the United States and internationally, with emphasis on their specific technical requirements for database systems. It then covers the professional standards and benchmarks — CIS, DISA STIGs, NIST, ISO — that provide technical implementation guidance. Finally, it addresses how to build a database security compliance program that produces real security outcomes, not just audit documentation.

---

## 13.1 PCI DSS v4.0 and Database Security

The **Payment Card Industry Data Security Standard (PCI DSS)** is a contractual security standard maintained by the PCI Security Standards Council, established by Visa, Mastercard, American Express, Discover, and JCB. Any organization that stores, processes, or transmits cardholder data must comply. Non-compliance can result in fines, increased transaction fees, and ultimately termination of the ability to process card payments.

PCI DSS v4.0 (released March 2022, mandatory by March 2025) contains 12 requirements organized into six goals. Several requirements have direct database security implications:

### Requirement 3: Protect Stored Account Data

This requirement governs what cardholder data may be stored at all and how it must be protected if stored. Key technical controls for database systems include:

- **Encryption:** Primary Account Numbers (PANs — the 16-digit card number) must be rendered unreadable anywhere they are stored. Acceptable methods include strong one-way hashing, truncation, index tokens with secure pads, or strong cryptography with associated key management processes.
- **Masking:** When displaying PANs, only the first six and last four digits may be shown (e.g., `423456XXXXXX4321`). Database views and application layers must enforce masking.
- **Tokenization:** Replacing the PAN with a surrogate value (token) that has no exploitable relationship to the original. The token is stored in application databases; the actual PAN is stored only in a secure token vault, ideally operated by a third-party PCI-compliant tokenization provider.
- **Data retention:** A formal data retention policy must define how long cardholder data is retained, with automated deletion of data exceeding retention limits.

### Requirements 7 and 8: Access Control and Authentication

- Access to system components must be restricted to individuals whose job requires it (least privilege).
- Database accounts must have individual IDs — no shared accounts.
- Passwords (or equivalent authentication factors) must meet minimum complexity and rotation requirements.
- Multi-factor authentication is required for all non-console administrative access (expanded in v4.0 to include all access to the cardholder data environment).

### Requirement 10: Audit Logging

All access to cardholder data must be logged. Log entries must include: user ID, event type, date/time, success/failure, origination, and identity or name of affected data component. Logs must be protected from modification and retained for at least 12 months (with 3 months immediately available).

### Requirement 11: Vulnerability Testing

- Penetration testing must be conducted at least annually and after significant changes. Database servers are explicitly in scope.
- Vulnerability scanning must be performed quarterly.
- SQL injection and other web application attacks must be included in penetration testing scope.

---

## 13.2 HIPAA Database Requirements

The **Health Insurance Portability and Accountability Act (HIPAA)** applies to **covered entities** (healthcare providers, health plans, healthcare clearinghouses) and their **business associates** (vendors who handle Protected Health Information on behalf of covered entities — including cloud database providers used by healthcare organizations). The **HIPAA Security Rule** (45 CFR Part 164) establishes standards for protecting electronic Protected Health Information (ePHI).

The Security Rule does not prescribe specific technologies but requires implementation of safeguards across three categories. The **technical safeguards** most relevant to database security are:

- **Access Controls:** Assign unique user identification; implement emergency access procedures; implement automatic logoff; implement encryption and decryption of ePHI.
- **Audit Controls:** Implement hardware, software, and/or procedural mechanisms that record and examine activity in systems containing ePHI. For databases, this means query logging, access logging, and schema change tracking.
- **Integrity Controls:** Implement policies and procedures to protect ePHI from improper alteration or destruction. Database integrity constraints, checksums, and backup verification serve this function.
- **Transmission Security:** Implement technical security measures to guard against unauthorized access to ePHI transmitted over electronic communications networks. All database connections carrying ePHI must use TLS.

### Minimum Necessary Standard

HIPAA requires that access to ePHI be limited to the minimum necessary for the intended purpose. For database design, this means role-based access control with fine granularity — a billing clerk should have access only to financial fields, not to clinical diagnosis codes. Views and row-level security can enforce this at the database layer.

### De-Identification Standards

Data that has been properly de-identified is no longer ePHI and is not subject to HIPAA's restrictions. HIPAA provides two approved methods:

- **Safe Harbor:** Remove all 18 specified identifiers (name, geographic data smaller than state, dates, phone numbers, SSN, etc.) and verify that no remaining information could reasonably identify the individual.
- **Expert Determination:** A statistician or equivalent expert certifies that the risk of identification is very small. This allows retaining more data utility than Safe Harbor.

De-identified data in a database context requires careful schema design — even "anonymous" records can be re-identified through quasi-identifier combinations (e.g., ZIP code + birth date + gender).

---

## 13.3 GDPR and Database Design Implications

The **General Data Protection Regulation (EU) 2016/679** applies to any organization processing personal data of individuals in the European Union, regardless of where the organization is located. Its implications for database architecture and security are profound.

### Lawful Basis for Processing

Data may only be stored in a database if there is a lawful basis — consent, contract performance, legal obligation, vital interests, public task, or legitimate interests. This requirement drives database design: systems should record the legal basis for each category of personal data stored, and data collected under a specific purpose should not be used for incompatible purposes.

### Data Minimization

Article 5(1)(c) requires that personal data be "adequate, relevant and limited to what is necessary." For database designers, this means avoiding the temptation to collect extra fields "in case they're useful later." Schema reviews should question whether every personal data field has a documented, necessary purpose.

### Right to Erasure (Right to Be Forgotten)

Article 17 grants individuals the right to request deletion of their personal data under certain conditions. This creates a significant technical challenge for databases:

- **Replication and backups:** A `DELETE` from the primary database does not erase data from replicas, read replicas, point-in-time recovery snapshots, or archived backups. Organizations must have documented processes for propagating deletions to all copies, or justify retention of backup copies under a legitimate retention basis.
- **Immutable audit logs:** Audit logs may contain personal data. If a user requests erasure, log records naming that user may need to be addressed, though security and legal requirements often provide legitimate grounds for log retention.
- **Pseudonymization as an alternative:** Rather than deleting records (which may break referential integrity), some organizations replace personal identifiers with pseudonymous tokens. If the mapping table is deleted, the pseudonymized record cannot be re-linked — functionally equivalent to erasure.

### Subject Access Requests (SAR)

Article 15 grants individuals the right to obtain a copy of all personal data held about them. For database administrators, this means having the ability to query across all tables and systems for records linked to a specific individual. Organizations without a comprehensive data inventory struggle to fulfill SARs completely. Building a **data catalog** that maps personal data fields across the database estate is a GDPR-driven architectural requirement.

### Pseudonymization vs. Anonymization

GDPR explicitly encourages pseudonymization as a risk-reduction measure, though pseudonymized data is still considered personal data (because re-identification is possible with the key). Truly anonymized data falls outside GDPR's scope — but achieving true anonymization is technically more difficult than most organizations assume.

---

## 13.4 SOX, FERPA, and GLBA

**Sarbanes-Oxley (SOX)** applies to publicly traded U.S. companies. Section 404 requires management to assess and certify the effectiveness of internal controls over financial reporting. For databases containing financial data:

- **Separation of duties:** The same person should not both enter transactions and approve them. Database access controls should enforce this — a developer should not have write access to production financial tables.
- **Change management:** All changes to database schemas or stored procedures affecting financial calculations must go through a documented, approved change process.
- **COBIT** (Control Objectives for Information and Related Technologies) is widely used as the IT governance framework for SOX compliance, with specific controls for database access management.

**FERPA (Family Educational Rights and Privacy Act)** governs student education records at institutions receiving federal funding. Frostburg State University's student information system database is subject to FERPA. Key implications: student record databases must restrict access to school officials with legitimate educational interest; audit logs of who accessed which student records are required; disclosure of records to third parties requires consent.

**GLBA (Gramm-Leach-Bliley Act)** applies to financial institutions — banks, credit unions, insurance companies, investment firms. The **Safeguards Rule** (revised 2023) requires a comprehensive information security program including: access controls to customer financial data, encryption of customer information in transit and at rest, audit log retention, and an incident response program.

---

## 13.5 Database Security Standards and Benchmarks

Beyond regulatory requirements, technical security standards provide specific, actionable database hardening guidance.

### CIS Benchmarks

The **Center for Internet Security (CIS)** publishes detailed benchmarks for major database platforms: MySQL, SQL Server, Oracle Database, and PostgreSQL. Each benchmark scores configurations as Level 1 (basic, widely applicable) or Level 2 (defense-in-depth, may impact functionality). A typical benchmark contains 100-300 individual checks covering:

- Default accounts and passwords
- Network listener configuration
- Audit logging settings
- Password policies
- File system permissions on database files
- Encryption settings

Organizations use CIS benchmarks to perform baseline assessments and measure improvement over time. Tools like CIS-CAT Pro can automate assessment scoring against the benchmark.

### DISA STIGs

**Defense Information Systems Agency (DISA) Security Technical Implementation Guides (STIGs)** are mandatory configuration standards for U.S. Department of Defense systems. Database STIGs exist for Oracle, SQL Server, and PostgreSQL. Each finding is categorized as CAT I (high — direct immediate risk), CAT II (medium), or CAT III (low). STIGs are more prescriptive than CIS benchmarks and are publicly available via the DISA STIG Viewer tool.

### NIST SP 800-53 Controls

NIST Special Publication 800-53 defines a catalog of security controls for federal information systems, organized into 20 control families. Controls most directly relevant to database security include:

- **AC (Access Control):** AC-2 (Account Management), AC-3 (Access Enforcement), AC-6 (Least Privilege)
- **AU (Audit and Accountability):** AU-2 (Event Logging), AU-3 (Content of Audit Records), AU-9 (Protection of Audit Information)
- **IA (Identification and Authentication):** IA-2 (User Identification), IA-5 (Authenticator Management)
- **SC (System and Communications Protection):** SC-8 (Transmission Confidentiality), SC-28 (Protection of Information at Rest)

### ISO 27001 Annex A

ISO 27001 is an international information security management system standard. Annex A contains 93 controls (in the 2022 version). Controls in the "Technological Controls" category most relevant to databases include:

- A.8.3 — Information access restriction
- A.8.5 — Secure authentication
- A.8.11 — Data masking
- A.8.15 — Logging
- A.8.24 — Use of cryptography

---

## 13.6 Building a Database Security Compliance Program

Compliance is achieved through a cycle of assessment, remediation, monitoring, and evidence collection — not through a one-time project.

**Gap Assessment:** Use CIS Benchmark scoring or a STIG review to establish the current state of database security configurations against the required standard. Document every finding with severity, affected system, and current vs. required configuration.

**Remediation Roadmap:** Prioritize findings by severity and business risk. CAT I / high-severity findings (e.g., missing authentication, publicly accessible instances) should be remediated within days. Tracking remediation in a risk register with target dates and owners creates accountability.

**Evidence Collection:** Auditors require evidence that controls exist and operate continuously. For databases, this means: exported audit log samples, screenshots of access control configurations, results of vulnerability scans, change management tickets for schema changes, and documented procedures for backup testing and key rotation. Automation is essential — manually collecting evidence for hundreds of database controls is not sustainable.

**Continuous Monitoring:** Compliance is not a point-in-time state. Database configurations drift as new instances are provisioned, parameters are changed for performance tuning, and staff turnover occurs. Automated configuration monitoring tools (CIS-CAT, AWS Config, Azure Policy) should alert on compliance deviations in near-real time.

---

## Key Terms

| Term | Definition |
|---|---|
| **PCI DSS** | Payment Card Industry Data Security Standard — security requirements for handling cardholder data |
| **Tokenization** | Replacing sensitive data (e.g., PAN) with a non-sensitive surrogate value |
| **PAN** | Primary Account Number — the 16-digit credit/debit card number |
| **HIPAA** | Health Insurance Portability and Accountability Act — U.S. law governing ePHI security |
| **ePHI** | Electronic Protected Health Information — individually identifiable health data |
| **Covered Entity** | Healthcare provider, plan, or clearinghouse subject to HIPAA |
| **Business Associate** | Vendor handling ePHI on behalf of a covered entity — also subject to HIPAA |
| **De-Identification** | Removing identifiers from data so individuals cannot be reasonably identified |
| **Safe Harbor** | HIPAA de-identification method requiring removal of 18 specified identifiers |
| **GDPR** | General Data Protection Regulation — EU regulation governing personal data processing |
| **Data Minimization** | GDPR principle requiring collection of only necessary personal data |
| **Right to Erasure** | GDPR right allowing individuals to request deletion of their personal data |
| **Subject Access Request (SAR)** | GDPR right allowing individuals to obtain a copy of personal data held about them |
| **Pseudonymization** | Replacing direct identifiers with pseudonyms while retaining a mapping key |
| **SOX** | Sarbanes-Oxley Act — U.S. law requiring internal controls over financial reporting |
| **FERPA** | Family Educational Rights and Privacy Act — governs student education records |
| **CIS Benchmark** | Detailed configuration hardening guide for specific technologies, published by the Center for Internet Security |
| **DISA STIG** | DoD mandatory security configuration standard, categorized by severity |
| **NIST SP 800-53** | NIST catalog of security controls for federal information systems |
| **Gap Assessment** | Comparison of current security configuration against required standard to identify deficiencies |

---

## Review Questions

1. **Conceptual:** PCI DSS Requirement 3 lists several methods for protecting stored PANs: encryption, hashing, truncation, and tokenization. Explain each method and when you would choose tokenization over encryption for a payment processing database.

2. **Applied:** A database schema for a healthcare application stores the following fields in a `patients` table: `patient_id`, `full_name`, `dob`, `ssn`, `diagnosis_code`, `prescribing_physician`, `insurance_plan_id`. Identify which fields constitute ePHI and describe the minimum-necessary access controls that should be applied to a billing role vs. a clinical role.

3. **Conceptual:** A user submits a GDPR Subject Access Request asking for all personal data your organization holds about them. Describe the technical process of fulfilling this request, including the challenges of finding personal data across multiple database tables and backup copies.

4. **Applied:** Your organization's production PostgreSQL database contains customer personal data. A customer invokes their GDPR right to erasure. The database has daily snapshots retained for 30 days and a streaming read replica. Describe your technical approach to fulfilling the erasure request across all data stores.

5. **Conceptual:** What is the difference between pseudonymization and anonymization in the GDPR context? Why does GDPR still consider pseudonymized data to be personal data?

6. **Applied:** You are performing a CIS Benchmark Level 1 assessment on a MySQL 8.0 database. You discover: (a) the anonymous user account still exists, (b) `LOAD DATA LOCAL INFILE` is enabled, (c) the `test` database is present. Describe the security risk for each finding and the remediation SQL command.

7. **Conceptual:** Explain how SOX's separation of duties requirement applies specifically to database-level access controls. Give a concrete example of a separation of duties violation in a database environment and how it would be detected during an audit.

8. **Applied:** Your organization is a financial institution subject to the GLBA Safeguards Rule. The rule requires that customer financial data be encrypted in transit and at rest. Describe the specific technical controls you would implement in your SQL Server environment to satisfy these requirements, including the commands or configuration settings.

9. **Conceptual:** Compare CIS Benchmarks and DISA STIGs as database hardening standards. What types of organizations would use each, and what is the practical difference between a Level 1/Level 2 CIS finding and a CAT I/CAT II STIG finding?

10. **Applied/Scenario:** Frostburg State University's student information system database receives a FERPA audit request. Auditors want evidence that access to student records is restricted to appropriate personnel and that access events are logged. Describe three specific pieces of evidence you would collect from the database environment to satisfy this audit request.

---

## Further Reading

- PCI Security Standards Council. (2022). *PCI DSS v4.0*. https://www.pcisecuritystandards.org/document_library/
- U.S. Department of Health & Human Services. (2024). *HIPAA Security Rule Guidance*. https://www.hhs.gov/hipaa/for-professionals/security/index.html
- European Commission. (2018). *General Data Protection Regulation (GDPR) Full Text*. https://gdpr-info.eu/
- Center for Internet Security. (2024). *CIS Benchmarks*. https://www.cisecurity.org/cis-benchmarks
- NIST. (2020). *SP 800-53 Rev. 5: Security and Privacy Controls for Information Systems and Organizations*. https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final
