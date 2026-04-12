---
title: "Database Auditing — Monitoring, Logging, and Compliance"
week: 8
chapter: 8
course: SCIA-340
---

# Chapter 8: Database Auditing — Monitoring, Logging, and Compliance

## Introduction

Organizations invest heavily in access control and encryption, but these preventive controls alone are insufficient. Attackers adapt, insiders abuse privileges, and misconfigured systems create unexpected pathways. **Database auditing** provides the detective layer: the ability to see who accessed what data, when, from where, and what they did with it. This chapter covers the principles of database auditing, native audit capabilities across major database platforms, audit log protection, centralized audit management, and the regulatory requirements that drive audit mandates across industries.

---

## 8.1 Why Database Auditing Is Critical

Consider these scenarios that auditing directly addresses:

**Detecting attacks in progress.** SQL injection attacks, credential stuffing, and lateral movement from compromised application servers all generate characteristic patterns in database activity logs — abnormal query rates, access to tables the application never normally touches, or unusual data volumes being exported. A well-monitored database can trigger alerts within seconds of attack initiation.

**Forensic investigation.** After a breach, audit logs are the primary source of truth for answering: What data was accessed? Which account was used? How long did the attacker have access? Forensic investigations without audit logs are largely guesswork.

**Regulatory compliance.** PCI DSS, HIPAA, SOX, and GDPR all impose explicit requirements for tracking access to sensitive data. Audit logs are often required to be retained for one to seven years.

**Insider threat detection.** The greatest threats to data often come from within. A privileged database user downloading bulk records outside business hours, an employee accessing records of colleagues or executives, or a DBA browsing sensitive tables without a business justification — all of these require audit logging to detect and investigate.

### 8.1.1 Logging vs. Auditing

These terms are often used interchangeably but represent different activities:

| Logging | Auditing |
|---|---|
| Captures raw events (who connected, what query ran) | Analyzes log data against defined policies and standards |
| Technical output from the database engine | Compliance and security-oriented review process |
| Ongoing, automated | Periodic or triggered review |
| Stored in log files | Produces audit reports and findings |

Logging is a prerequisite for auditing. You cannot audit events you did not log.

---

## 8.2 What Should Be Audited?

Comprehensive database auditing covers multiple event categories. Not every organization audits everything — the volume of audit data must be balanced against storage costs and the ability to review it — but certain event categories are broadly considered mandatory:

**Privileged operations:**
- DDL statements (CREATE, ALTER, DROP TABLE/INDEX/PROCEDURE)
- DCL statements (GRANT, REVOKE)
- Database configuration changes
- User account creation and modification

**Authentication events:**
- Successful logins (especially privileged accounts)
- Failed login attempts (pattern of failures may indicate brute-force)
- Session creation and termination

**Sensitive data access:**
- SELECT statements on tables containing PII, PHI, or financial data
- Especially large result sets (potential bulk exfiltration)

**Data modification:**
- INSERT, UPDATE, DELETE on critical tables
- TRUNCATE operations

**Schema changes:**
- Object creation/modification/deletion
- Stored procedure and function changes

**Backup and export operations:**
- Database backup initiation
- Data export utilities (bcp, pg_dump)

> **Key Principle:** Audit policies should be driven by data classification. Audit access to tables containing sensitive data more aggressively than access to lookup tables or application metadata.

---

## 8.3 Native Database Audit Features

### 8.3.1 Oracle Unified Auditing (12c+)

Oracle Database 12c introduced **Unified Auditing**, consolidating multiple earlier audit mechanisms (standard auditing, fine-grained auditing, SYS auditing) into a single framework. Audit records are written to a single location, the unified audit trail, queried via the `UNIFIED_AUDIT_TRAIL` view.

Oracle Unified Auditing operates through **audit policies** — named objects that specify what to audit. Policies can audit:
- Specific SQL statement types
- Object actions (e.g., SELECT on a specific table)
- System privileges
- Conditions (e.g., only audit SELECTs that return more than 1000 rows)

```sql
-- Create an audit policy for sensitive table access
CREATE AUDIT POLICY sensitive_data_access
  ACTIONS SELECT ON hr.employees,
           SELECT ON hr.salary,
           INSERT ON hr.salary,
           UPDATE ON hr.salary,
           DELETE ON hr.salary;

-- Enable the policy for all users
AUDIT POLICY sensitive_data_access;

-- Enable only for specific users
AUDIT POLICY sensitive_data_access BY hr_admin, payroll_user;

-- View recent audit records
SELECT dbusername, action_name, object_name, unified_timestamp, sql_text
FROM unified_audit_trail
WHERE object_name = 'SALARY'
ORDER BY unified_timestamp DESC;
```

**Oracle Fine-Grained Auditing (FGA)** takes this further, enabling auditing at the row and column level — audit only when a query accesses specific columns or returns rows matching specific conditions.

```sql
-- Audit SELECT on employees table only when SSN column is accessed
DBMS_FGA.ADD_POLICY(
  object_schema   => 'HR',
  object_name     => 'EMPLOYEES',
  policy_name     => 'SSN_AUDIT',
  audit_column    => 'SSN',
  enable          => TRUE,
  statement_types => 'SELECT'
);
```

FGA is exceptionally useful for HIPAA and GDPR compliance, where regulations require tracking access to specific fields (e.g., date of birth, diagnosis codes, SSNs).

### 8.3.2 SQL Server Audit

SQL Server provides a two-level audit architecture:

- **Server-level audits:** Track events at the SQL Server instance level (logins, server configuration changes, privilege grants)
- **Database-level audits:** Track events within a specific database (table access, DML operations, schema changes)

**Audit Action Groups** are predefined sets of events. Common groups include:
- `SUCCESSFUL_LOGIN_GROUP`
- `FAILED_LOGIN_GROUP`
- `DATABASE_OBJECT_ACCESS_GROUP`
- `SCHEMA_OBJECT_ACCESS_GROUP`
- `DATABASE_CHANGE_GROUP`

```sql
-- Create a server audit writing to a file
CREATE SERVER AUDIT SensitiveDB_Audit
TO FILE (FILEPATH = 'C:\AuditLogs\', MAXSIZE = 100 MB)
WITH (ON_FAILURE = CONTINUE);

-- Create a database audit specification
CREATE DATABASE AUDIT SPECIFICATION HRData_Audit
FOR SERVER AUDIT SensitiveDB_Audit
ADD (SELECT, INSERT, UPDATE, DELETE ON hr.employees BY public),
ADD (SCHEMA_OBJECT_ACCESS_GROUP),
ADD (DATABASE_CHANGE_GROUP)
WITH (STATE = ON);

ALTER SERVER AUDIT SensitiveDB_Audit WITH (STATE = ON);
```

SQL Server **Extended Events** (XEvents) provide a lighter-weight, highly customizable event capture framework often preferred over SQL Trace/Profiler for performance-sensitive environments.

### 8.3.3 MySQL Audit Log Plugin

MySQL Community Edition does not include built-in auditing. **MySQL Enterprise Edition** includes the Audit Log Plugin. MariaDB includes an Audit Plugin. Both require explicit configuration.

```ini
# my.cnf — enable audit log
[mysqld]
plugin-load-add=audit_log.so
audit_log_format=JSON
audit_log_policy=ALL
audit_log_file=/var/log/mysql/mysql-audit.json
```

Filtering can exclude high-volume, low-risk queries (e.g., health check queries from monitoring systems) to keep log volume manageable:

```sql
-- MySQL Enterprise Audit filter (exclude monitoring user)
SELECT audit_log_filter_set_filter('exclude_monitor',
  '{ "filter": { "users": [{"user":"monitor", "host":"%"}],
     "log": false } }');
```

### 8.3.4 PostgreSQL — pgaudit Extension

PostgreSQL's built-in logging captures connections and disconnections but does not provide SQL-statement-level auditing suitable for compliance. The **pgaudit** extension provides this capability.

```bash
# Install pgaudit (example: Debian/Ubuntu)
sudo apt install postgresql-14-pgaudit
```

```ini
# postgresql.conf
shared_preload_libraries = 'pgaudit'
pgaudit.log = 'write, ddl, role, connection'
pgaudit.log_catalog = off
pgaudit.log_relation = on
pgaudit.log_statement_once = off
```

The `pgaudit.log` parameter accepts these categories:
- `read` — SELECT, COPY from
- `write` — INSERT, UPDATE, DELETE, TRUNCATE, COPY to
- `function` — function calls
- `role` — GRANT, REVOKE, CREATE/ALTER/DROP ROLE
- `ddl` — CREATE, ALTER, DROP (not covered by role)
- `misc` — DISCARD, FETCH, CHECKPOINT
- `all` — all of the above

Object-level auditing lets you audit specific relations:
```sql
-- Audit all access to a specific table
SET pgaudit.log = 'all';
-- Object audit via audit role
GRANT SELECT ON hr.employees TO pgaudit_monitor;
```

---

## 8.4 Protecting Audit Logs

Audit logs are only valuable if their integrity can be trusted. A sophisticated attacker who gains privileged database access will attempt to tamper with or delete audit logs to conceal their activities. Log protection requires several layered controls:

**Separation of duties.** The DBA who administers the database should not have write access to the audit log storage. Audit log management should be the responsibility of a separate security or compliance team.

**Write to separate storage.** Audit logs should be written to a different server or storage system than the database itself. SQL Server can write audit logs to Windows Event Log forwarded to a SIEM, or to a file share on a separate server.

**WORM (Write Once Read Many) storage.** Some compliance frameworks require that audit logs be stored on tamper-proof WORM media — once written, they cannot be modified or deleted. AWS S3 Object Lock, Azure Immutable Blob Storage, and dedicated WORM appliances provide this capability.

**Log signing.** Some audit frameworks support cryptographic signing of audit log records, allowing detection of tampering even if the logs remain accessible.

**Retention policies.** Audit logs must be retained long enough to support investigations and compliance audits:
- PCI DSS: 12 months (3 months immediately available, 9 months archived)
- HIPAA: 6 years
- SOX: 7 years for financial records

> **⚠️ Warning:** A DBA who can disable auditing has the ability to "turn off the lights" before committing unauthorized actions. Ensure that changes to audit configuration themselves are audited and that any audit policy changes trigger immediate alerts to the security team.

---

## 8.5 Centralized Audit Log Management and SIEM Integration

Individual database audit logs are useful, but maximum value comes from centralizing logs across all databases into a **Security Information and Event Management (SIEM)** platform. A SIEM correlates events across multiple systems, enabling detection of patterns that span databases, application servers, and network devices.

**Common SIEM platforms:**
- **Splunk** — market-leading log aggregation and analysis
- **IBM QRadar** — enterprise SIEM with strong database integration
- **Microsoft Sentinel** — cloud-native SIEM in Azure
- **Elastic Security (ELK Stack)** — open-source alternative

Integration patterns:
1. **Agent-based forwarding:** A log shipper agent (Splunk Universal Forwarder, Filebeat) runs on the database server and forwards logs in real time.
2. **Syslog forwarding:** Database audit logs are sent via syslog to a central collector.
3. **API polling:** SIEM queries a database audit API at intervals.

Once in the SIEM, database audit data can be used to build **correlation rules** such as:
- "Alert if any user SELECTs more than 10,000 rows from the patients table within 5 minutes"
- "Alert if a login succeeds after 10 failed attempts within 60 seconds"
- "Alert if schema changes occur outside the approved change window (evenings or weekends)"

---

## 8.6 Database Activity Monitoring (DAM) Tools

**Database Activity Monitoring (DAM)** tools provide real-time visibility into database activity, anomaly detection, and alerting. Unlike native database audit features that require configuring each database individually, DAM tools can monitor multiple database platforms from a single console.

**Imperva (formerly SecureSphere)** monitors database traffic by sniffing network packets or using database agents. It builds behavioral baselines — learning the "normal" query patterns for each application and user — and alerts on deviations.

**IBM Guardium** is an enterprise DAM platform that captures and analyzes all database activity in real time. It supports policy-based blocking, vulnerability assessment, compliance reporting, and integration with SIEMs.

**McAfee Database Activity Monitoring (now Trellix)** offers similar capabilities with strong integration into the broader McAfee/Trellix security ecosystem.

Key DAM capabilities:
- Real-time SQL statement capture and analysis
- Baseline profiling and anomaly detection
- Privileged user monitoring
- Compliance report generation (PCI, HIPAA, SOX)
- Integration with ticketing systems for alert management

---

## 8.7 Compliance-Driven Audit Requirements

Major regulatory frameworks impose specific database audit requirements:

### PCI DSS — Requirement 10

The Payment Card Industry Data Security Standard requires logging all access to cardholder data environments:
- Log all access to system components (logins, activities, exceptions)
- Audit logs must be available for immediate analysis for at least 3 months
- Retain audit logs for at least 12 months
- Protect logs from modification (WORM, access control)
- Review logs daily

### HIPAA — Audit Controls (§164.312(b))

The Health Insurance Portability and Accountability Act requires covered entities to implement audit controls — hardware, software, and procedural mechanisms to record and examine activity in systems containing protected health information (PHI). HIPAA does not prescribe exactly what to log, but common interpretations include:
- User login/logout events
- Access to PHI records
- Failed access attempts
- Privileged user activities

### SOX — Sarbanes-Oxley

SOX requires audit trails for financial reporting systems. Databases that store financial data used in public company reporting must have:
- Change management trails showing who modified financial data and when
- Access logs for systems that could impact financial reporting integrity
- 7-year retention for financial records

### GDPR — Article 5 and Article 30

The General Data Protection Regulation requires that personal data be processed lawfully and that processing be documented. Article 30 requires a record of processing activities. For databases:
- Log access to records containing EU residents' personal data
- Support the right to erasure — demonstrate compliance with deletion requests
- Support data subject access requests — show what data is held about an individual

---

## 8.8 Audit Report Design and Review Cadence

Audit logs that are never reviewed provide no security value. Establishing a regular review cadence is as important as the technical implementation:

| Review Type | Frequency | Focus |
|---|---|---|
| Automated alert response | Real-time | Policy violations, anomalies, attack signatures |
| Privileged user review | Daily | DBA and admin activity |
| Failed login analysis | Daily | Brute-force patterns |
| Sensitive data access | Weekly | Large queries, after-hours access |
| Schema change review | Per-change event | Change management compliance |
| Compliance audit report | Monthly / Quarterly | Regulatory requirement documentation |
| Penetration test correlation | After each test | Confirming audit capture of known activity |

Audit reports should be pre-built in the SIEM or DAM platform to reduce the burden of manual report generation. Automated reports delivered to the security team and compliance officers ensure regular review happens consistently.

---

## Key Terms

| Term | Definition |
|---|---|
| **Unified Audit Trail** | Oracle 12c+ centralized repository for all audit records |
| **Fine-Grained Auditing (FGA)** | Oracle feature enabling row- and column-level audit conditions |
| **Audit Policy** | Named set of events to be audited, enabled for specific users or globally |
| **pgaudit** | PostgreSQL extension providing SQL-statement-level auditing |
| **Database Activity Monitoring (DAM)** | Tools providing real-time monitoring and analysis of database activity |
| **SIEM** | Security Information and Event Management — platform for correlating security events across systems |
| **WORM Storage** | Write Once Read Many — tamper-proof storage for audit logs |
| **Separation of Duties** | Dividing responsibilities so no single individual can commit and conceal an action |
| **Audit Action Groups** | SQL Server predefined sets of auditable events |
| **Extended Events (XEvents)** | SQL Server lightweight event capture framework |
| **Behavioral Baseline** | Profile of normal activity patterns used to detect anomalies |
| **PCI DSS** | Payment Card Industry Data Security Standard |
| **HIPAA** | Health Insurance Portability and Accountability Act |
| **SOX** | Sarbanes-Oxley Act — financial reporting compliance law |
| **GDPR** | General Data Protection Regulation — EU data privacy law |
| **IBM Guardium** | Enterprise Database Activity Monitoring platform |
| **Splunk** | Market-leading log aggregation and SIEM platform |
| **Log Signing** | Cryptographically signing audit records to detect tampering |
| **DDL** | Data Definition Language — CREATE, ALTER, DROP statements |
| **DCL** | Data Control Language — GRANT and REVOKE statements |

---

## Review Questions

1. **Conceptual:** Explain the difference between database logging and database auditing. Why are both necessary for an effective security program? Can you have auditing without logging?

2. **Applied:** Write Oracle SQL to create an audit policy called `pii_access_audit` that audits SELECT, INSERT, UPDATE, and DELETE operations on the `hr.employees` and `finance.salary` tables. Then write a query to retrieve the five most recent audit records from the unified audit trail for the `salary` table.

3. **Scenario:** Your organization's HIPAA compliance officer asks you to prove that no one accessed patient records for a specific patient (ID: 98765) between January 1 and March 31. What audit infrastructure would need to be in place to answer this question, and what query would you run to retrieve that information from Oracle's unified audit trail?

4. **Conceptual:** Why is it insufficient to let the database administrator manage both the database and the audit log storage? What security principle does this violate, and what architectural controls enforce it?

5. **Applied:** Configure `pgaudit` in PostgreSQL to audit all DDL operations, all role management operations, and all write operations (INSERT, UPDATE, DELETE). Show the relevant lines in `postgresql.conf`.

6. **Analysis:** Compare SQL Server's native audit feature with a dedicated DAM tool like IBM Guardium. In what scenarios would the native audit feature be sufficient? When would a DAM tool be necessary?

7. **Scenario:** A SIEM alert fires: a service account (`app_readonly`) performed a `SELECT *` query returning 850,000 rows from the `customers` table at 2:47 AM — well outside business hours. Walk through how you would investigate this event. What additional audit data would you query, and what are the possible explanations?

8. **Compliance:** PCI DSS Requirement 10 mandates daily review of audit logs. Your organization has 15 database servers generating hundreds of thousands of audit events per day. How would you implement daily review in a practical way? What automation and tooling would you use?

9. **Applied:** A disgruntled DBA is suspected of accessing executive salary records they are not authorized to view. The DBA has `SYSDBA` privileges on an Oracle database. Explain why this is particularly challenging to detect and what Oracle audit configurations would capture `SYSDBA` activity.

10. **Conceptual:** Explain the GDPR right to erasure ("right to be forgotten") from a database audit logging perspective. If a user requests deletion of their data and you delete their records, what happens to the audit logs that show their data was accessed? How do you reconcile audit log retention requirements with erasure requests?

---

## Further Reading

- Oracle Corporation. *Oracle Database Security Guide — Auditing Database Activity*. Oracle Database Documentation Library.
- Microsoft Documentation. *SQL Server Audit (Database Engine)*. https://learn.microsoft.com/en-us/sql/relational-databases/security/auditing/sql-server-audit-database-engine
- pgaudit Project. *pgaudit: Open Source PostgreSQL Audit Logging*. https://www.pgaudit.org/
- PCI Security Standards Council. *PCI DSS v4.0 — Requirement 10: Log and Monitor All Access to System Components*. https://www.pcisecuritystandards.org/
- IBM. *IBM Guardium Data Protection — Product Overview*. https://www.ibm.com/products/ibm-guardium-data-protection
