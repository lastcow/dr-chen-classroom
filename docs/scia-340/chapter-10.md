---
title: "Secure Database Design and Development"
week: 10
chapter: 10
course: SCIA-340
---

# Chapter 10: Secure Database Design and Development

## Introduction

The most expensive place to fix a security problem is in production, under pressure, after a breach. The least expensive place is at the design stage, before a single line of code is written. Yet database security is routinely treated as a post-development concern — a set of controls to "add" once the system is built. This approach results in schema designs that concentrate sensitive data unnecessarily, application code that bypasses the database's access control model, and architectural patterns that make security retrofits costly and disruptive.

Secure database design integrates security decisions into every phase: data classification before schema design, normalization choices that reduce exposure, constraint-based integrity enforcement, view and stored procedure architectures that limit direct table access, and development practices that prevent SQL injection and privilege escalation at the source. This chapter presents these principles as a cohesive methodology for building databases that are secure by design rather than secure by addition.

---

## 10.1 Security by Design — Core Principles

Four foundational principles guide secure database design:

**Minimize the attack surface.** Store only data you need. Expose only what applications require. Create only the accounts and permissions that are necessary. Every additional table, column, account, and permission is potential attack surface.

**Defense in depth.** No single control is sufficient. Layer access control, encryption, auditing, and application-level validation so that the failure of any one control does not result in a catastrophic breach.

**Fail securely.** When components fail — constraint violations, stored procedure errors, unexpected inputs — they should fail in a way that denies access rather than granting it. An error in an authorization check should default to denial, not permission.

**Principle of least privilege.** Every component — application accounts, stored procedures, users — should have only the minimum permissions necessary to perform its function.

---

## 10.2 Data Classification Before Schema Design

Before writing a single `CREATE TABLE` statement, you must understand what data the system will hold and how sensitive it is. Data classification is the process of categorizing data by its sensitivity and the regulatory frameworks that govern it.

### 10.2.1 Data Classification Categories

| Classification | Examples | Governing Regulations |
|---|---|---|
| **PII (Personally Identifiable Information)** | Name, address, phone, SSN, email, IP address | GDPR, CCPA, various state laws |
| **PHI (Protected Health Information)** | Diagnosis, medication, treatment, insurance | HIPAA |
| **PCI Data** | Credit card numbers (PAN), CVV, cardholder name | PCI DSS |
| **Financial Data** | Account balances, transaction history, salary | SOX, GLBA |
| **Confidential Internal** | Trade secrets, M&A plans, personnel records | Internal policy |
| **Public** | Published marketing content, product catalogs | No restrictions |

### 10.2.2 Data Flow Mapping

Before designing the schema, map every data element the system will process:
1. Where does it enter the system?
2. Where is it stored?
3. Who/what accesses it?
4. Where does it leave the system?
5. How long is it retained?

This mapping reveals whether sensitive data flows through systems that don't need it, gets logged unnecessarily, or is retained longer than required. GDPR's data minimization principle (Article 5(1)(c)) requires that data be "adequate, relevant, and limited to what is necessary in relation to the purposes for which they are processed."

> **Key Principle — Data Minimization:** The most secure data is data you don't have. If the system doesn't need to store raw credit card numbers, use tokenization. If it doesn't need the full SSN, store only the last four digits. Avoid collecting sensitive data "in case it's useful later."

---

## 10.3 Schema Design for Security

### 10.3.1 Normalization and Security

Database normalization — reducing data redundancy by decomposing tables — has direct security benefits:

- **Reduced exposure surface:** If SSNs are stored in one table rather than embedded in five, access control and auditing can be focused on that one table.
- **Audit clarity:** A change to normalized data requires modifying one record in one table. Denormalized data may require changes across multiple tables, increasing the audit surface and the opportunity for inconsistency.
- **Encryption focus:** A normalized sensitive column can be encrypted; denormalized copies of the same data scattered throughout the schema make consistent encryption difficult.

The trade-off is that data warehouses and analytical systems often intentionally denormalize for query performance. In these environments, compensating controls (column-level access control, strict audit logging, data masking for non-production copies) become especially important.

### 10.3.2 Separating Sensitive Data into Dedicated Schemas

Isolating sensitive data into dedicated database schemas allows granular access control. Applications that don't need access to sensitive data simply have no grants on the sensitive schema.

```sql
-- Create a dedicated schema for PII data
CREATE SCHEMA pii_data;

-- Move sensitive tables into the PII schema
CREATE TABLE pii_data.patient_identifiers (
    patient_id      INT           PRIMARY KEY,
    ssn             VARCHAR(11)   NOT NULL,  -- Consider encrypting this
    date_of_birth   DATE          NOT NULL,
    full_name       VARCHAR(100)  NOT NULL
);

-- Separate schema for clinical data
CREATE SCHEMA clinical;

CREATE TABLE clinical.diagnoses (
    diagnosis_id    INT PRIMARY KEY,
    patient_id      INT REFERENCES pii_data.patient_identifiers(patient_id),
    icd10_code      VARCHAR(10) NOT NULL,
    diagnosis_date  DATE NOT NULL
);

-- Application account for the scheduling module has NO access to pii_data schema
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA clinical TO scheduling_app;
-- Does NOT grant access to pii_data
```

This architecture means a SQL injection vulnerability in the scheduling module cannot access patient SSNs — the database engine enforces the boundary.

### 10.3.3 Secure Data Types

Data type selection is a security decision, not just a performance one:

**Financial data:** Always use `NUMERIC(precision, scale)` or `DECIMAL`, never `FLOAT` or `DOUBLE`. Floating-point types are subject to rounding errors that create inconsistencies exploitable in financial fraud. A balance of `$100.00` stored as `FLOAT` may be represented as `99.99999999999...` internally.

**Date and time:** Use `DATE`, `TIMESTAMP`, or `TIMESTAMPTZ` — not `VARCHAR`. Storing dates as strings allows inconsistent formats, breaks ordering, and makes date-range queries unreliable. A `VARCHAR` date column might contain `"2024-01-15"`, `"Jan 15 2024"`, `"01/15/24"` — making queries and access control by time range unreliable.

**Identifiers:** Use integer sequences or UUIDs for primary keys — not user-supplied values. Predictable numeric IDs (1, 2, 3...) can enable enumeration attacks in web applications. UUIDs (`uuid_generate_v4()` in PostgreSQL) are unpredictable and non-enumerable.

**Text with length constraints:** Use `VARCHAR(n)` with appropriate length limits rather than `TEXT` for user-supplied input fields. This prevents large-payload attacks and provides a coarse input validation layer.

---

## 10.4 Constraints as Security Controls

Database constraints enforce data integrity and can function as security controls by preventing the insertion of invalid or malicious data states.

```sql
-- NOT NULL prevents null values that might bypass business logic checks
CREATE TABLE accounts (
    account_id      INT           NOT NULL PRIMARY KEY,
    account_type    VARCHAR(20)   NOT NULL,
    balance         NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    owner_id        INT           NOT NULL REFERENCES users(user_id),
    -- CHECK constraint enforces valid values
    CONSTRAINT valid_account_type CHECK (account_type IN ('checking','savings','money_market')),
    CONSTRAINT non_negative_balance CHECK (balance >= 0.00)
);

-- UNIQUE constraint prevents duplicate sensitive identifiers
CREATE TABLE employees (
    employee_id     INT           PRIMARY KEY,
    ssn             VARCHAR(11)   NOT NULL UNIQUE,  -- SSN must be unique
    email           VARCHAR(255)  NOT NULL UNIQUE,
    hire_date       DATE          NOT NULL,
    -- Ensure hire date is not in the future (application-level bypass prevention)
    CONSTRAINT valid_hire_date CHECK (hire_date <= CURRENT_DATE)
);
```

The `CHECK` constraint on `account_type` prevents an application bug or injection attack from inserting an unexpected account type that might bypass downstream business logic. The `non_negative_balance` constraint prevents balance from going negative through a race condition or injection attack, regardless of what the application-level code does.

**Foreign key constraints** enforce referential integrity and prevent orphaned records that might confuse access control logic:
```sql
CONSTRAINT valid_owner FOREIGN KEY (owner_id) REFERENCES users(user_id) ON DELETE RESTRICT
```

`ON DELETE RESTRICT` prevents deleting a user who still has accounts — avoiding scenarios where an account becomes un-owned and falls into an undefined access state.

---

## 10.5 Stored Procedures as Security Boundaries

One of the most effective database security architecture patterns is to prohibit application code from directly querying tables and require all data access to go through stored procedures. This provides several security properties:

**SQL injection prevention:** If applications only call stored procedures with parameters, and stored procedures never build dynamic SQL from user input, the entire SQL injection attack surface is eliminated at the architectural level.

**Least privilege enforcement:** Grant the application account `EXECUTE` permission on stored procedures, not `SELECT/INSERT/UPDATE/DELETE` on tables. The application cannot do anything the stored procedures don't explicitly allow.

**Centralized input validation:** Stored procedures can validate inputs before acting on them, providing a server-side validation layer independent of the application.

**Audit clarity:** Auditing `EXECUTE` on stored procedures produces clear, semantic audit records ("created a patient record") rather than raw SQL strings.

```sql
-- Stored procedure pattern: no direct table access for the application
CREATE OR REPLACE PROCEDURE create_patient(
    p_name          IN VARCHAR2,
    p_dob           IN DATE,
    p_ssn           IN VARCHAR2
) AUTHID CURRENT_USER AS
BEGIN
    -- Input validation
    IF LENGTH(p_ssn) != 11 OR p_ssn NOT REGEXP_LIKE p_ssn, '^[0-9]{3}-[0-9]{2}-[0-9]{4}$') THEN
        RAISE_APPLICATION_ERROR(-20001, 'Invalid SSN format');
    END IF;

    IF p_dob > SYSDATE THEN
        RAISE_APPLICATION_ERROR(-20002, 'Date of birth cannot be in the future');
    END IF;

    INSERT INTO pii_data.patient_identifiers (full_name, date_of_birth, ssn)
    VALUES (p_name, p_dob, p_ssn);

    COMMIT;
END;
/

-- Grant only EXECUTE to the application account, not INSERT on the table
GRANT EXECUTE ON create_patient TO app_account;
```

---

## 10.6 View-Based Access Architecture

Database views can expose a filtered subset of data, hiding sensitive columns or rows from accounts that shouldn't see them. This is particularly useful for creating different "views" of the same underlying data for different application roles.

```sql
-- Base table has all columns including sensitive ones
-- View exposes only what the scheduling application needs
CREATE VIEW scheduling.patient_appointments AS
SELECT
    p.patient_id,
    p.full_name,           -- Non-sensitive
    a.appointment_date,
    a.provider_id,
    a.appointment_type
FROM pii_data.patient_identifiers p
JOIN clinical.appointments a ON p.patient_id = a.patient_id;
-- SSN, DOB, diagnosis codes are NOT in this view

GRANT SELECT ON scheduling.patient_appointments TO scheduling_app;
```

Views can also implement row-level security by filtering based on the current user:

```sql
-- Each provider can only see their own patients through this view
CREATE VIEW my_patients AS
SELECT p.*
FROM patients p
JOIN provider_assignments pa ON p.patient_id = pa.patient_id
WHERE pa.provider_id = (SELECT provider_id FROM providers WHERE db_username = CURRENT_USER);
```

---

## 10.7 Trigger-Based Security Controls

Database triggers fire automatically on INSERT, UPDATE, or DELETE operations. They can implement security controls that cannot be bypassed by the application layer:

```sql
-- Audit trigger: records every change to salary data
CREATE OR REPLACE TRIGGER salary_audit_trigger
AFTER INSERT OR UPDATE OR DELETE ON hr.salaries
FOR EACH ROW
BEGIN
    INSERT INTO audit.salary_changes (
        event_time, db_user, action, employee_id,
        old_salary, new_salary
    ) VALUES (
        SYSTIMESTAMP,
        SYS_CONTEXT('USERENV', 'SESSION_USER'),
        CASE WHEN INSERTING THEN 'INSERT'
             WHEN UPDATING THEN 'UPDATE'
             ELSE 'DELETE' END,
        COALESCE(:NEW.employee_id, :OLD.employee_id),
        :OLD.salary,
        :NEW.salary
    );
END;
/
```

**Validation triggers** can enforce complex business rules that CHECK constraints cannot:

```sql
-- Prevent salary reductions greater than 10% (fraud prevention)
CREATE OR REPLACE TRIGGER validate_salary_change
BEFORE UPDATE ON hr.salaries
FOR EACH ROW
BEGIN
    IF :NEW.salary < :OLD.salary * 0.90 THEN
        RAISE_APPLICATION_ERROR(-20010,
            'Salary reductions greater than 10% require HR manager approval via workflow system');
    END IF;
END;
/
```

---

## 10.8 Secure Coding Practices for Database Developers

### 10.8.1 Parameterized Queries

The most fundamental secure coding practice is using parameterized queries (also called prepared statements) for all SQL that incorporates user input. This was covered in the SQL injection context in Chapter 9, but it bears repeating as a design principle:

```python
# Python — WRONG: string concatenation
query = "SELECT * FROM users WHERE username = '" + username + "'"

# Python — CORRECT: parameterized query
query = "SELECT * FROM users WHERE username = %s"
cursor.execute(query, (username,))
```

```java
// Java — CORRECT: PreparedStatement
PreparedStatement stmt = conn.prepareStatement(
    "SELECT * FROM accounts WHERE account_id = ?");
stmt.setInt(1, accountId);
ResultSet rs = stmt.executeQuery();
```

### 10.8.2 Error Handling in Stored Procedures

Stored procedures must handle errors carefully to avoid both information disclosure and security bypass:

```sql
-- SQL Server stored procedure with proper error handling
CREATE PROCEDURE GetPatientRecord
    @PatientID INT
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        -- Verify the calling user is authorized for this patient
        IF NOT EXISTS (SELECT 1 FROM provider_assignments
                       WHERE patient_id = @PatientID
                       AND provider_username = SYSTEM_USER)
        BEGIN
            -- Generic error: do not reveal whether the record exists
            RAISERROR('Access denied.', 16, 1);
            RETURN;
        END

        SELECT patient_id, full_name, date_of_birth
        FROM patients WHERE patient_id = @PatientID;
    END TRY
    BEGIN CATCH
        -- Log the actual error internally
        INSERT INTO error_log (error_time, db_user, error_message)
        VALUES (GETDATE(), SYSTEM_USER, ERROR_MESSAGE());
        -- Return generic message to caller
        RAISERROR('An error occurred processing your request.', 16, 1);
    END CATCH
END;
```

### 10.8.3 TOCTOU (Time of Check to Time of Use) Races

A TOCTOU race condition occurs when a security check and the action it guards are not atomic. In database context:

```sql
-- VULNERABLE: Check and action are separate transactions
-- Step 1: Check balance
SELECT balance FROM accounts WHERE account_id = 101;  -- Returns 100.00

-- [Another transaction modifies balance here]

-- Step 2: Withdraw (now operates on stale data)
UPDATE accounts SET balance = balance - 150.00 WHERE account_id = 101;
-- Balance could go negative!
```

The solution is to use atomic SQL or proper transaction isolation:

```sql
-- SAFE: Atomic check-and-update
UPDATE accounts
SET balance = balance - 150.00
WHERE account_id = 101
  AND balance >= 150.00;  -- Only succeeds if balance check passes atomically

IF @@ROWCOUNT = 0
    RAISERROR('Insufficient funds', 16, 1);
```

---

## 10.9 Schema Versioning and Change Management

Every change to a production database schema is a potential security event. A new column added to a sensitive table, a permission granted to the wrong account, or a stored procedure modified to bypass a validation check can all introduce vulnerabilities. Schema change management provides:

- **Audit trail:** Every schema change is recorded with who requested it, who approved it, and when it was applied
- **Review process:** Security review before changes are applied catches insecure designs before they reach production
- **Rollback capability:** Changes that introduce problems can be undone in a controlled manner

**Flyway** and **Liquibase** are the leading schema migration tools:

```sql
-- Flyway migration: V20240315_01__Add_patient_consent_table.sql
CREATE TABLE clinical.patient_consent (
    consent_id      INT           GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    patient_id      INT           NOT NULL REFERENCES pii_data.patient_identifiers(patient_id),
    consent_type    VARCHAR(50)   NOT NULL
        CONSTRAINT valid_consent_type CHECK (consent_type IN ('treatment','research','marketing')),
    consented       BOOLEAN       NOT NULL,
    consent_date    TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    recorded_by     INT           NOT NULL REFERENCES staff.employees(employee_id)
);

-- Always include the reviewer's name and ticket number in migration file comments
-- Reviewed-by: Security Team
-- JIRA: SEC-4421
```

---

## 10.10 Avoiding Hardcoded Secrets in Database Code

Stored procedures, functions, and database jobs sometimes require credentials — to connect to external services, call APIs, or access linked databases. Hardcoding these credentials is a persistent and serious anti-pattern:

```sql
-- BAD: Hardcoded credentials in a stored procedure
CREATE PROCEDURE SyncToExternalSystem AS
BEGIN
    EXEC xp_cmdshell 'curl -u admin:password123 https://api.example.com/sync';
END;
```

This stored procedure's source code is visible to any DBA who can query the system catalog (`sys.sql_modules` in SQL Server). Solutions:
- Store credentials in the database's built-in credential store (SQL Server Agent Credentials, Oracle Wallet)
- Use integrated OS authentication (Windows Authentication for SQL Server, IAM for cloud databases) to avoid passwords entirely
- Reference credentials from a secrets manager via a secure API call, not hardcoded values
- Rotate credentials stored in database objects as part of standard key rotation procedures

---

## Key Terms

| Term | Definition |
|---|---|
| **Secure by Design** | Security incorporated into architecture and design rather than added as an afterthought |
| **Data Classification** | Categorizing data by sensitivity level and applicable regulatory requirements |
| **PII (Personally Identifiable Information)** | Data that can identify an individual; subject to privacy regulations |
| **PHI (Protected Health Information)** | Health data protected under HIPAA |
| **PCI Data** | Payment card data subject to PCI DSS requirements |
| **Data Minimization** | Collecting and storing only data necessary for the stated purpose |
| **Database Schema** | The structural definition of a database — tables, columns, constraints, relationships |
| **Normalization** | Organizing a database to reduce redundancy by decomposing tables |
| **CHECK Constraint** | Database constraint that enforces a boolean condition on column values |
| **Stored Procedure** | Pre-compiled, named SQL program stored in the database |
| **View** | Virtual table presenting a subset or transformation of underlying table data |
| **Trigger** | Database object that executes automatically in response to data modification events |
| **TOCTOU (Time of Check to Time of Use)** | Race condition where a check and its guarded action are not atomic |
| **Parameterized Query** | SQL query using placeholders for user-supplied values to prevent injection |
| **Flyway** | Open-source database schema version control and migration tool |
| **Liquibase** | Open-source database change management platform |
| **Referential Integrity** | Consistency guarantee that foreign key values correspond to existing primary keys |
| **AUTHID CURRENT_USER** | Oracle stored program attribute causing execution under caller's privileges |
| **Least Privilege** | Security principle of granting only the minimum permissions necessary |
| **Data Flow Mapping** | Documentation of how data moves through systems from collection to disposal |

---

## Review Questions

1. **Conceptual:** Explain the principle of "security by design" in the context of database development. What are the practical differences in outcomes between a database designed with security in mind from the start versus one where security controls are added after development is complete?

2. **Applied:** You are designing a database schema for a hospital patient management system. Identify the data elements that would be classified as PII, PHI, and internal-confidential. Design a schema with at least three tables that properly separates these categories into dedicated schemas.

3. **Scenario:** A development team creates a table with the following definition:
   ```sql
   CREATE TABLE user_accounts (
       id INT, username VARCHAR(500), password VARCHAR(500),
       balance FLOAT, account_type VARCHAR(500), created VARCHAR(500)
   );
   ```
   Identify at least five security and design problems with this definition and rewrite it with proper security controls.

4. **Applied:** Explain how stored procedures function as a security boundary. Write a PostgreSQL stored procedure `transfer_funds(from_account INT, to_account INT, amount NUMERIC)` that: (a) validates inputs, (b) checks sufficient funds atomically, (c) performs the transfer, and (d) handles errors without revealing internal details. Grant the appropriate permissions to an application account.

5. **Conceptual:** What is a TOCTOU (Time of Check to Time of Use) race condition in a database context? Provide a concrete banking example and show the SQL pattern that eliminates the vulnerability.

6. **Applied:** Design a view-based access architecture for a multi-role HR application where: (a) the `hr_manager` role can see all employee data including salary, (b) the `recruiter` role can see names and contact info but not salary or SSN, and (c) the `employee_self_service` account can see only their own record. Write the SQL for each view.

7. **Analysis:** Compare the security properties of `AUTHID DEFINER` vs. `AUTHID CURRENT_USER` for an Oracle stored procedure that accesses sensitive HR data. Under what circumstances would each be appropriate? What privilege escalation risk does DEFINER present?

8. **Applied:** A stored procedure in SQL Server currently contains:
   ```sql
   EXEC xp_cmdshell 'curl -u svcuser:P@ssw0rd https://api.internal.com/notify'
   ```
   Explain why this is a security problem. Describe two alternative approaches to accomplish the same goal without hardcoded credentials.

9. **Scenario:** A data warehouse team wants to copy the production customer database (containing PII) to a development environment so analysts can build new reports. What data-security controls should be applied to the development copy, and what tools or techniques would you use to implement them? Consider GDPR implications.

10. **Applied:** Your team is implementing schema change management using Flyway. Write the migration file naming convention, describe what a security review of a schema migration should examine, and write an example migration that creates a table for storing API keys with appropriate security controls (constraints, data types, audit columns).

---

## Further Reading

- Brocklehurst, S. *Secure by Design*. Manning Publications, 2019. (Chapters on database design)
- OWASP. *Database Security Cheat Sheet*. https://cheatsheetseries.owasp.org/cheatsheets/Database_Security_Cheat_Sheet.html
- Flyway by Redgate. *Database Migrations Done Right*. https://flywaydb.org/documentation/
- European Data Protection Board. *Guidelines on Data Minimisation Under GDPR Article 5(1)(c)*. https://edpb.europa.eu/
- Microsoft Documentation. *SQL Server Security Best Practices*. https://learn.microsoft.com/en-us/sql/relational-databases/security/sql-server-security-best-practices
