---
title: "RDBMS Architecture and the Security Model"
chapter: 2
week: 2
course: SCIA-340
---

# Chapter 2: RDBMS Architecture and the Security Model

## Introduction

To defend a database system effectively, you must understand how it works internally. Security vulnerabilities don't arise from nowhere — they emerge from specific architectural decisions, component interactions, and operational characteristics. This chapter examines the internal architecture of a Relational Database Management System (RDBMS) through a security lens, tracing how data flows from a client application through authentication, parsing, execution, and storage — and where attackers can intercept or manipulate that flow at each stage.

## RDBMS Component Architecture

A modern RDBMS is not a monolithic program but a layered collection of subsystems, each of which has distinct security implications.

### The Database Engine

The database engine coordinates all activity within the RDBMS instance. It receives connection requests, authenticates users, manages concurrent access through locking and transaction management, and enforces access controls. From a security perspective, the database engine is the central trust boundary: everything that happens inside the engine after authentication is governed by the privilege model, while everything outside — network packets, filesystem access, OS process interactions — represents potential attack paths into the engine.

### The Storage Engine

The storage engine manages how data is physically written to and read from disk. In MySQL, the pluggable storage engine architecture allows different engines per table — InnoDB for transactional tables, MyISAM for legacy read-heavy tables, MEMORY for temporary in-memory tables. Each storage engine has different security characteristics. InnoDB supports transactions and row-level locking, making it more suitable for environments requiring strong integrity guarantees. The MEMORY engine stores all data in RAM, which means data is lost on crash, but also that sensitive data may persist in memory longer than expected. SQL Server uses its own integrated storage engine with buffer pool management. Oracle uses its Automatic Storage Management (ASM) for high-availability disk management, but ASM volumes containing database files can be a target if OS-level access is obtained.

The **tablespace** is the logical storage container used by Oracle and PostgreSQL to organize data files. Access to tablespace files on the filesystem bypasses all database access controls — an attacker with OS-level read access to tablespace files can use offline tools to extract data directly, which is why filesystem permissions on database data directories are a critical hardening step.

### The Query Processor

The query processor is the component that transforms SQL text submitted by a client into an execution plan that retrieves or modifies data. It consists of several sub-components:

1. **Parser**: Validates SQL syntax and tokenizes the query into an internal representation
2. **Optimizer**: Analyzes possible execution plans and selects the most efficient one based on statistics
3. **Executor**: Carries out the chosen execution plan, interacting with the storage engine and buffer pool

> **Security Critical Point**: SQL injection attacks exploit the parser. When user-supplied input is concatenated into a SQL string, the parser cannot distinguish between legitimate query structure and attacker-supplied SQL. The parser simply processes whatever SQL text it receives. This architectural reality is why parameterized queries are the only reliable defense — they ensure user input is never processed by the parser as SQL syntax.

### The Transaction Manager

The transaction manager enforces ACID properties — Atomicity, Consistency, Isolation, and Durability — and manages concurrency through locking or multi-version concurrency control (MVCC). From a security perspective, transactions are important because they provide atomicity for audit trail entries (an audit log record is committed if and only if the transaction it records is committed) and because transaction isolation levels affect what data is visible to concurrent sessions.

## Database Objects and Security Implications

Database objects are the logical structures that organize and expose data. Each type of object has distinct security considerations.

### Tables

Tables are the fundamental storage objects. The primary security concern is that granting access to a table typically exposes all rows and columns. In environments with sensitive data, raw table access is rarely appropriate for anything other than DBA accounts. Application accounts should typically access data through views or stored procedures rather than directly against base tables.

### Views

Views are stored queries that present a subset of data from underlying tables. They are one of the most powerful and underused access control mechanisms in SQL. A view can restrict column access by selecting only non-sensitive columns, restrict row access by including a WHERE clause, and abstract the underlying schema so that table structures can change without breaking application queries. Views created with `WITH CHECK OPTION` ensure that data modifications through the view continue to satisfy the view's WHERE clause.

```sql
-- A view that exposes only non-sensitive employee columns
-- and only for active employees
CREATE VIEW hr_public.employee_directory AS
SELECT employee_id, first_name, last_name, department, office_phone
FROM hr.employees
WHERE employment_status = 'ACTIVE'
WITH CHECK OPTION;

-- Grant access only to the view, not the underlying table
GRANT SELECT ON hr_public.employee_directory TO app_readonly;
```

### Stored Procedures and Functions

Stored procedures are precompiled, named collections of SQL statements stored in the database. From a security perspective, they offer several important benefits: they can be called by application accounts that have no direct table access (the procedure runs with the definer's privileges), they can implement complex business logic with input validation, and they centralize data access logic making it easier to audit.

However, stored procedures are not inherently safe from SQL injection. Dynamic SQL executed inside a stored procedure using `EXEC()` or `sp_executesql` (SQL Server), `EXECUTE IMMEDIATE` (Oracle), or `PREPARE`/`EXECUTE` (MySQL/PostgreSQL) is just as vulnerable as dynamic SQL in application code if parameters are concatenated rather than properly bound.

### Triggers

Triggers are procedures that execute automatically in response to data modification events (INSERT, UPDATE, DELETE). Security-relevant uses of triggers include maintaining audit tables that record changes to sensitive data, enforcing business rules that CHECK constraints cannot express, and implementing row-level security logic. However, triggers also create security risks: a trigger that executes with elevated privileges can be a vector for privilege escalation if an attacker can manipulate the data that causes the trigger to fire.

### Schemas

A schema is a named namespace that contains database objects. The schema model is foundational to multi-tenant security and least privilege design. In SQL Server and PostgreSQL, different application components can be isolated into separate schemas with separate privilege sets:

```sql
-- PostgreSQL: Separate schemas for different application modules
CREATE SCHEMA billing;
CREATE SCHEMA inventory;
CREATE SCHEMA hr;

-- The billing application role can only access billing schema objects
GRANT USAGE ON SCHEMA billing TO billing_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA billing TO billing_app;
-- billing_app cannot access hr or inventory schemas
```

## Database Instances vs. Schemas vs. Users

These three concepts are frequently confused, and the confusion creates security misconfiguration risks.

A **database instance** is a running RDBMS process with its own memory structures, background processes, and configuration. In Oracle, an instance serves one database (though Oracle RAC allows multiple instances to share one database). In SQL Server, an "instance" is an installation of SQL Server that can host multiple databases. Isolating sensitive workloads to separate instances provides strong security boundaries because instance-level administrative accounts (SYS in Oracle, SA in SQL Server) cannot access other instances.

A **schema** (in Oracle terminology, a **schema** is synonymous with a **user**) is a collection of objects owned by a user or organized under a namespace. In PostgreSQL and SQL Server, schemas are namespaces within a database that can be owned and accessed by multiple users.

A **user** (or **login**) is a database principal that can authenticate and be granted privileges. The key security consideration is ensuring that users are granted privileges appropriate to their role and that service accounts used by applications are distinct from human accounts — so that activity can be attributed and accounts can be independently managed.

## Platform-Specific Security Architectures

### Oracle Database

Oracle's security architecture is one of the most comprehensive among commercial RDBMS products. The **SYS** user owns the data dictionary and core database infrastructure. SYS has absolute authority within the database — no database access control can override SYS. Protecting the SYS password is therefore paramount. The **SYSTEM** user is a less privileged administrative account but still carries broad permissions; its password must also be changed from the default immediately upon installation.

Oracle provides two enterprise security features of particular note. **Oracle Label Security (OLS)** implements Mandatory Access Control by attaching sensitivity labels to rows and comparing them against session labels to determine row visibility. This enables Bell-LaPadula-style access control directly within the database engine. **Oracle Virtual Private Database (VPD)**, also called Fine-Grained Access Control (FGAC), automatically appends WHERE clause predicates to queries based on application context, enabling transparent row-level security without modifying application SQL.

### Microsoft SQL Server

SQL Server's security model distinguishes between **logins** (server-level principals used for authentication) and **users** (database-level principals used for authorization). A login authenticates to the SQL Server instance; a user maps that login to a specific database and its permission set. SQL Server supports both **Windows Authentication** (integrated with Active Directory Kerberos/NTLM) and **SQL Authentication** (username/password stored in SQL Server's own security catalog). Windows Authentication is strongly preferred because passwords are managed by Active Directory policy and Kerberos provides stronger authentication guarantees than SQL Server's native password handling.

**Contained databases** are a SQL Server feature where users authenticate directly to the database without a server-level login. This is useful for portability and some multi-tenant scenarios, but it also means the database carries its own authentication state that is separate from server-level management, which can complicate security administration.

### MySQL/MariaDB

MySQL uses a distinctive **user@host** authentication model. A MySQL account is identified by both a username and the hostname or IP address from which the connection originates. The account `app_user@'10.0.1.%'` is entirely separate from `app_user@'10.0.2.%'` and can have different passwords and privileges. This allows fine-grained control over which hosts can connect using particular credentials. The grant tables in the `mysql` system database store all user accounts and privilege assignments.

MySQL supports **authentication plugins** that extend the default authentication mechanism. `caching_sha2_password` (the default since MySQL 8.0) provides better security than the legacy `mysql_native_password` plugin. Other plugins support PAM, LDAP, and Kerberos authentication, enabling integration with enterprise identity infrastructure.

### PostgreSQL

PostgreSQL's security model is based entirely on **roles** — there is no distinction between users and groups at the role level. A role can be configured to log in (making it function as a user), to have member roles (making it function as a group), or both. PostgreSQL's **pg_hba.conf** file (Host-Based Authentication) is separate from the database itself and controls authentication method per host/database/user combination:

```
# pg_hba.conf entries control authentication method per combination
# TYPE  DATABASE  USER      ADDRESS        METHOD
host    payroll   payapp    10.0.1.0/24    scram-sha-256
host    all       dba_user  10.0.2.5/32    cert
local   all       postgres               peer
```

PostgreSQL 15+ implements **Row Level Security (RLS)** policies natively, allowing table owners to define row-visibility policies that are automatically enforced for all queries against the table, regardless of which application issues the query.

## Database Memory Architecture and Security

Understanding how databases use memory is important because sensitive data in memory can sometimes be accessed through unexpected paths.

The **buffer pool** (called the buffer cache in Oracle) is the primary memory structure where the RDBMS caches data pages read from disk. On a heavily loaded server, the buffer pool may contain virtually every recently accessed data page — meaning sensitive data exists in memory in plaintext, even if it is encrypted on disk. Transparent Data Encryption (TDE), which encrypts data files on disk, does not protect data in the buffer pool. Memory forensics tools or process memory dumps can potentially expose data that was never written to unencrypted disk.

The **process model vs. thread model** distinction matters for isolation. Oracle uses a multi-process architecture where each connection has a dedicated server process. PostgreSQL uses a similar model. SQL Server and MySQL primarily use threads. With threads, a vulnerability that allows reading another thread's memory within the same process could potentially expose data from other users' sessions.

## Transaction Management and ACID Properties

ACID compliance is a security property as much as a reliability property. Consider why each ACID property matters from a security standpoint:

- **Atomicity**: Ensures that a partial transaction cannot succeed — for example, a funds transfer cannot debit one account without crediting another. Attackers cannot leave a transaction in a half-completed state that creates exploitable inconsistency.
- **Consistency**: Ensures that transactions bring the database from one valid state to another, enforcing all defined constraints. SQL injection attacks that attempt to insert malformed data are blocked by consistency enforcement.
- **Isolation**: Ensures that concurrent transactions do not interfere with each other. Isolation level misconfigurations (such as using READ UNCOMMITTED) can expose uncommitted data from other transactions to unauthorized observers.
- **Durability**: Ensures that committed transactions survive system failures. For audit trails, durability is essential — without it, an attacker who crashes the database may be able to eliminate evidence of their actions.

## Redo/Undo Logs and Security Implications

All major RDBMS products maintain transaction logs — in Oracle these are redo logs and undo segments; in SQL Server, the transaction log; in PostgreSQL, Write-Ahead Log (WAL) files. These logs record every change to the database and are essential for crash recovery and point-in-time restore.

> **⚠ Warning**: Transaction logs contain the full history of data modifications, often including the before and after images of changed rows. An attacker with access to transaction log files can reconstruct sensitive data that may have been deleted from the database, potentially accessing data that was "deleted" but whose deletion was recorded in the log and is thus recoverable. Transaction log files must be protected with the same access controls as the database data files themselves.

## Temporary Files and Data Leakage

When the database performs large sort or hash operations, it may write data to temporary storage — sort areas, temporary tablespaces, or temp files. This data is typically not encrypted, even if TDE is enabled, because the encrypted storage layer is bypassed during temporary file creation in some RDBMS implementations. Sensitive data from a query — such as a full dump of a salary table — may be written to unprotected temp files during processing. Proper configuration of temporary file locations with appropriate OS-level permissions is an often-overlooked hardening step.

---

## Key Terms

| Term | Definition |
|------|------------|
| **Storage Engine** | The RDBMS component that manages physical read/write of data to disk |
| **Query Processor** | The component that parses, optimizes, and executes SQL queries |
| **Buffer Pool** | In-memory cache of data pages recently read from or written to disk |
| **ACID** | Atomicity, Consistency, Isolation, Durability — the four properties of reliable transactions |
| **Transaction Manager** | The RDBMS component enforcing ACID guarantees and managing concurrent access |
| **Schema** | A named namespace that groups database objects; in Oracle, synonymous with a user account |
| **Tablespace** | A logical storage unit that maps to one or more physical data files on disk |
| **Oracle VPD** | Virtual Private Database — Oracle feature for transparent row-level security via automatic WHERE clause modification |
| **Oracle Label Security** | Oracle's implementation of Mandatory Access Control using row-level sensitivity labels |
| **Contained Database** | SQL Server feature where authentication is scoped to the database rather than the server |
| **user@host Model** | MySQL's authentication model identifying accounts by both username and originating host |
| **pg_hba.conf** | PostgreSQL Host-Based Authentication configuration file controlling per-connection auth methods |
| **Write-Ahead Log (WAL)** | PostgreSQL's transaction log that records all changes before they are applied to data files |
| **Redo Log** | Oracle's transaction log recording all changes for crash recovery purposes |
| **Trigger** | Database object that executes automatically in response to DML events |
| **Stored Procedure** | Named, precompiled set of SQL statements stored in the database |
| **MVCC** | Multi-Version Concurrency Control — method of managing concurrent access by maintaining multiple data versions |
| **Authentication Plugin** | MySQL module that extends or replaces the default username/password authentication mechanism |

---

## Review Questions

1. **Conceptual**: Explain why data in the buffer pool is potentially vulnerable even when Transparent Data Encryption (TDE) is enabled. What threat scenario does this create?

2. **Applied**: Write SQL statements to create three schemas (`app_data`, `app_log`, `app_admin`) and three corresponding roles in PostgreSQL, granting each role only the privileges appropriate to its name (the `app_data` role can read/write application tables, the `app_log` role can only insert into log tables, and the `app_admin` role has full schema control). Explain your privilege design choices.

3. **Conceptual**: Compare Oracle's process-per-connection architecture to a threaded RDBMS architecture from a memory isolation security perspective. What are the security trade-offs?

4. **Applied**: Review the default authentication entries in a fresh PostgreSQL `pg_hba.conf`. Which entries represent security risks, and how would you modify them to improve security for a production database?

5. **Conceptual**: Explain why transaction logs (redo logs, WAL files, SQL Server transaction log) must be protected with the same rigor as database data files. Give a scenario where an attacker with only transaction log access could recover sensitive data.

6. **Applied**: Research Oracle's Virtual Private Database (VPD). Write a brief technical explanation of how VPD works at the query execution level, and describe a business scenario where VPD would be the most appropriate access control mechanism.

7. **Conceptual**: A developer argues that using stored procedures for all data access is "just extra complexity." Explain the specific security benefits of the stored procedure pattern and counter the developer's argument.

8. **Applied**: Examine the MySQL `mysql.user` grant table structure. What columns represent security controls, and what values would indicate a security misconfiguration?

9. **Conceptual**: The chapter describes the parser as the architectural point where SQL injection occurs. Explain mechanically why concatenating user input into SQL allows injection to succeed, and why parameterized queries prevent this at the parser level.

10. **Conceptual**: Describe three scenarios where temporary files or sort areas could expose sensitive data. What configuration or compensating controls can mitigate this risk?

---

## Further Reading

- **Oracle Corporation. (2023). *Oracle Database Security Guide, 19c*.**  Comprehensive documentation of Oracle's security architecture, including VPD, OLS, and privilege management. Available at docs.oracle.com.

- **Microsoft. (2024). *SQL Server Security Documentation*.** Covers the SQL Server principal/securable/permission model, contained databases, and Always Encrypted. Available at docs.microsoft.com.

- **PostgreSQL Global Development Group. (2024). *PostgreSQL 16 Documentation: Chapter 21 — Database Roles and Chapter 20 — Client Authentication*.** Authoritative reference for PostgreSQL's role model and HBA authentication. Available at postgresql.org/docs.

- **Takahashi, D. (2017). "Deep Dive: RDBMS Internals and Security." In *Database Security: An Introduction*.** Covers storage engine internals, buffer management, and the security implications of RDBMS architecture choices.

- **Graefe, G. (1993). "Query Evaluation Techniques for Large Databases." *ACM Computing Surveys*, 25(2), 73–169.** While dated, this survey remains the definitive technical reference for how query processors work — essential background for understanding where injection can occur in the execution pipeline.
