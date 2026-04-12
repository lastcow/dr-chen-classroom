---
title: "Access Control in Databases — DAC, MAC, and RBAC"
chapter: 5
week: 5
course: SCIA-340
---

# Chapter 5: Access Control in Databases — DAC, MAC, and RBAC

## Introduction: The Three Questions of Access Control

Once a user has authenticated to a database, the database must answer three questions for every operation the user attempts: **Who** is the user? **What** are they trying to do? **Which** object are they trying to do it to? Access control is the system that answers these questions and either permits or denies the operation.

Database access control is more nuanced than most other IT access control contexts. The granularity can extend to individual rows and columns within tables, not just files or directories. The relationships between objects are complex — views depend on tables, stored procedures operate on data in schemas, triggers fire as part of other users' transactions. And the consequences of misconfiguration are severe: a single over-privileged database account can expose millions of records to an attacker who compromises that account.

This chapter examines the three primary access control models as implemented in real database systems, their strengths and weaknesses, and how they are combined to achieve practical, defense-in-depth database authorization.

## Discretionary Access Control (DAC) in SQL

### The GRANT and REVOKE Model

SQL's native access control mechanism is **Discretionary Access Control (DAC)**. In DAC, the owner of an object has discretion over who can access it and can grant access to others. SQL implements DAC through the `GRANT` and `REVOKE` statements defined in the SQL standard.

The object owner can grant privileges to specific users, and by default can revoke them at any time. DAC is "discretionary" because it is left to the owner's discretion — there is no mandatory policy that prevents an owner from granting access even to inappropriate parties.

### Standard SQL Privileges

SQL defines a set of object-level privileges that can be independently granted and revoked:

| Privilege | Applies To | Description |
|-----------|-----------|-------------|
| `SELECT` | Tables, Views, Sequences | Read data from the object |
| `INSERT` | Tables, Views | Insert new rows |
| `UPDATE` | Tables, Views | Modify existing rows (can be column-specific) |
| `DELETE` | Tables, Views | Remove rows |
| `REFERENCES` | Tables | Create foreign key constraints referencing this table |
| `TRIGGER` | Tables | Create triggers on the table |
| `EXECUTE` | Functions, Procedures | Call the function or procedure |
| `CREATE` | Schemas, Databases | Create new objects |
| `DROP` | Schemas, Databases | Drop existing objects |
| `ALTER` | Tables, Schemas | Modify the structure of existing objects |

```sql
-- Grant SELECT and INSERT on a specific table to an application user
GRANT SELECT, INSERT ON hr.employees TO app_user;

-- Grant UPDATE only on specific columns (not the sensitive salary column)
GRANT UPDATE (first_name, last_name, email, phone) ON hr.employees TO hr_coordinator;

-- Grant EXECUTE on a stored procedure (no direct table access needed)
GRANT EXECUTE ON PROCEDURE hr.update_employee_contact TO hr_coordinator;

-- Revoke a privilege
REVOKE INSERT ON hr.employees FROM app_user;
```

### The WITH GRANT OPTION Problem

The `WITH GRANT OPTION` clause allows a user who receives a privilege to grant that same privilege to other users. This creates a potential for privilege spread that is difficult to track and control:

```sql
-- A grants SELECT to B with grant option
GRANT SELECT ON sensitive_data TO user_b WITH GRANT OPTION;

-- B now grants SELECT to C (and can grant to anyone else)
-- A may not be aware this happened
GRANT SELECT ON sensitive_data TO user_c;
```

If A later revokes SELECT from B, what happens to C's access depends on the database product. In PostgreSQL and SQL Server, revoking B's privilege also cascades to revoke any privileges B granted (`REVOKE ... CASCADE`). But without careful tracking, administrators often don't know who has been granted what through multiple grant chains. The practical recommendation is to **avoid using `WITH GRANT OPTION`** except for role administrators, and to use roles (covered below) to manage privilege distribution rather than granting directly to individual users.

### Ownership Chains and Implicit Access

SQL Server and Oracle both implement **ownership chain** (or **ownership chain resolution**) behavior: when a stored procedure or view owned by user A accesses a table also owned by user A, users granted EXECUTE on the procedure or SELECT on the view do not need explicit table privileges. The access check is only performed at the entry point (the procedure/view), not the underlying objects if they share an owner.

This is a security feature when used intentionally — it allows application accounts to call stored procedures without needing raw table access. But it can become a security vulnerability if the ownership chain is not understood: an attacker who can create objects in a schema might be able to access tables they otherwise couldn't by exploiting implicit chain resolution.

## Column-Level and Row-Level Security

### Column-Level Privileges

Standard SQL supports granting `SELECT` and `UPDATE` on specific columns rather than entire tables. This is essential for tables that mix sensitive and non-sensitive data:

```sql
-- The hr.employees table contains both public-OK and sensitive columns:
-- public: employee_id, first_name, last_name, department, office_phone
-- sensitive: ssn, salary, performance_rating, medical_notes

-- Directory role sees only public columns
GRANT SELECT (employee_id, first_name, last_name, department, office_phone)
ON hr.employees TO employee_directory_role;

-- Payroll role sees salary but not medical data
GRANT SELECT (employee_id, first_name, last_name, salary)
ON hr.employees TO payroll_role;

-- Medical role sees medical data but not salary
GRANT SELECT (employee_id, first_name, last_name, medical_notes)
ON hr.employees TO medical_role;
```

While column-level grants are available, many DBAs find them operationally complex to manage at scale. An alternative — and often cleaner — approach is to create views that expose only the appropriate columns and grant access to the views rather than the base table.

### Row-Level Security

Row-level security (RLS) restricts which rows a user can see or modify based on their identity or session attributes. Without RLS, a `SELECT * FROM orders` query returns all orders regardless of which customer or region the querying user is responsible for. RLS allows the database to automatically filter results to only the rows the user is authorized to see — transparently, without requiring the application to construct filtering WHERE clauses.

**PostgreSQL Row Level Security** is the most explicit RLS implementation. RLS must first be enabled on a table, then one or more policies define the conditions under which rows are visible or modifiable:

```sql
-- Enable RLS on the orders table
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- Policy: users can only see orders they created
CREATE POLICY user_can_see_own_orders ON orders
    FOR SELECT
    USING (created_by = current_user);

-- Policy: managers can see all orders in their region
CREATE POLICY manager_sees_region_orders ON orders
    FOR ALL
    TO manager_role
    USING (region = current_setting('app.user_region'));

-- The table owner bypasses RLS by default; to make RLS apply to the owner too:
ALTER TABLE orders FORCE ROW LEVEL SECURITY;
```

> **Key Concept**: PostgreSQL RLS policies use `USING` clauses (which rows can be read) and `WITH CHECK` clauses (which rows can be written). By separating read and write policies, fine-grained control over both visibility and modification is achievable at the engine level, regardless of how the application constructs its queries.

**Oracle Virtual Private Database (VPD)** implements row-level security by automatically appending a WHERE clause predicate to queries against protected tables. A VPD policy function is written in PL/SQL, takes the schema and table name as parameters, and returns a WHERE clause string that is silently appended to queries:

```sql
-- Oracle VPD: Policy function that restricts visibility to user's region
CREATE OR REPLACE FUNCTION my_schema.region_policy (
    schema_name IN VARCHAR2,
    table_name  IN VARCHAR2
) RETURN VARCHAR2 IS
    v_region VARCHAR2(50);
BEGIN
    v_region := SYS_CONTEXT('USERENV', 'CLIENT_IDENTIFIER');
    IF v_region IS NULL THEN
        RETURN '1=0';  -- No region set: see nothing
    ELSE
        RETURN 'region = ''' || v_region || '''';
    END IF;
END;

-- Attach the policy to the orders table
DBMS_RLS.ADD_POLICY(
    object_schema   => 'my_schema',
    object_name     => 'orders',
    policy_name     => 'region_policy',
    function_schema => 'my_schema',
    policy_function => 'region_policy',
    statement_types => 'SELECT,UPDATE,DELETE'
);
```

**SQL Server Row-Level Security** uses inline table-valued functions as security predicates, registered as policies on tables:

```sql
-- SQL Server RLS: Security predicate function
CREATE FUNCTION Security.fn_OrderAccessPredicate(@user_name AS sysname)
    RETURNS TABLE
    WITH SCHEMABINDING
AS
    RETURN SELECT 1 AS access_granted
    FROM dbo.UserRegionMap
    WHERE UserName = @user_name
      AND Region = (SELECT Region FROM dbo.Orders WHERE Orders.CreatedBy = @user_name);

-- Create security policy using the predicate
CREATE SECURITY POLICY OrderAccessPolicy
ADD FILTER PREDICATE Security.fn_OrderAccessPredicate(USER_NAME())
ON dbo.Orders
WITH (STATE = ON);
```

## Role-Based Access Control (RBAC) in Databases

### The Role Model

RBAC organizes privileges by function rather than by individual user. Roles are named collections of privileges that can be granted to users. When a user needs a new capability, you assign them an appropriate role rather than enumerating individual privileges. When job functions change, you modify the role definition and all role members are affected immediately.

```sql
-- PostgreSQL: Create roles representing job functions
CREATE ROLE readonly_analyst;
CREATE ROLE data_entry_clerk;
CREATE ROLE reporting_manager;
CREATE ROLE dba_operator;

-- Assign privileges to roles
GRANT SELECT ON ALL TABLES IN SCHEMA analytics TO readonly_analyst;
GRANT SELECT, INSERT, UPDATE ON data.transactions TO data_entry_clerk;
GRANT SELECT ON ALL TABLES IN SCHEMA analytics TO reporting_manager;
GRANT readonly_analyst TO reporting_manager;  -- Role inheritance

-- Grant roles to users
GRANT readonly_analyst TO alice;
GRANT data_entry_clerk TO bob;
GRANT reporting_manager TO carol;
```

### Role Hierarchies and Inheritance

Roles can be members of other roles, creating hierarchies where a higher-level role inherits all privileges of lower-level roles. This mirrors organizational hierarchy:

```
dba_operator
    └── reporting_manager
            └── readonly_analyst
                    └── SELECT on analytics tables
```

In this hierarchy, `dba_operator` inherits reporting_manager's privileges, which include readonly_analyst's SELECT privileges. Role inheritance must be designed carefully — if the hierarchy is too flat, roles accumulate more privileges than intended. The principle of least privilege still applies to role design.

> **⚠ Warning**: In Oracle, roles granted to users are not available within stored procedures by default (stored procedures run with the definer's directly granted privileges, not their role privileges). This means an Oracle stored procedure that relies on a role for table access will fail. Developers must be aware of this distinction and DBAs must grant direct privileges for objects accessed within stored procedures.

### Predefined Administrative Roles

Every major RDBMS ships with built-in administrative roles that should be used sparingly:

| RDBMS | Powerful Role | Capabilities |
|-------|--------------|-------------|
| Oracle | `DBA` | Full DDL/DML on all objects, system privileges |
| Oracle | `SYSDBA` | Startup/shutdown, full instance control |
| SQL Server | `sysadmin` | Unrestricted server-level access |
| SQL Server | `db_owner` | Full control over a database |
| MySQL | `GRANT ALL PRIVILEGES` | Full privileges on specified objects |
| PostgreSQL | `pg_read_all_data` | Read all tables in all schemas |
| PostgreSQL | Superuser | Unrestricted, bypasses all access checks |

These roles should never be granted to application service accounts. Their use should be limited to dedicated DBA accounts that are managed through PAM solutions with MFA (as discussed in Chapter 4).

## Mandatory Access Control (MAC) — Oracle Label Security

While DAC gives object owners discretion over access grants, **Mandatory Access Control (MAC)** enforces a centrally defined policy that no user — including the data owner — can override. MAC is used in environments with strict data classification requirements, particularly government and intelligence agencies.

**Oracle Label Security (OLS)** is Oracle's implementation of MAC. OLS attaches sensitivity labels to rows and compares them against session labels to determine whether a user's session can read or modify a row. Labels consist of three components:

- **Level**: A hierarchical sensitivity level (e.g., UNCLASSIFIED < CONFIDENTIAL < SECRET < TOP SECRET)
- **Compartment**: A non-hierarchical category that represents a project or program (e.g., ALPHA, BRAVO, CHARLIE)
- **Group**: An organizational unit (e.g., US_ONLY, NATO)

A row labeled `SECRET:ALPHA,BRAVO:US_ONLY` is visible only to sessions whose label includes SECRET or higher level, at least one of the ALPHA or BRAVO compartments, and the US_ONLY group. A user with a `CONFIDENTIAL:ALPHA:US_ONLY` session label cannot see this row because their level (CONFIDENTIAL) is lower than the row's label (SECRET), even if all other components match.

```sql
-- OLS: Creating a policy and attaching it to a table
EXEC SA_SYSDBA.CREATE_POLICY('DEFENSE_POLICY', 'DEFENSE_LABEL');
EXEC SA_COMPONENTS.CREATE_LEVEL('DEFENSE_POLICY', 40, 'S', 'SECRET');
EXEC SA_COMPONENTS.CREATE_LEVEL('DEFENSE_POLICY', 30, 'C', 'CONFIDENTIAL');
EXEC SA_COMPONENTS.CREATE_COMPARTMENT('DEFENSE_POLICY', 1000, 'ALPHA', 'Project Alpha');
EXEC SA_SYSDBA.APPLY_TABLE_POLICY('DEFENSE_POLICY', 'MY_SCHEMA', 'SENSITIVE_DATA', 'DEFENSE_LABEL');
```

## The Principle of Least Privilege Applied

### Application Account Design

Application database accounts should follow a strict least privilege design:

- **Read-only reporting accounts**: `SELECT` only, on specific tables or views, no access to audit or system tables
- **OLTP application accounts**: `SELECT`, `INSERT`, `UPDATE` on specific tables; `DELETE` only if the application actually deletes data; `EXECUTE` on stored procedures; no DDL privileges
- **ETL/batch accounts**: Specific source schema `SELECT` + destination schema `INSERT/UPDATE`; no access to production OLTP tables
- **Never**: `DBA` role, `CREATE TABLE/DROP TABLE`, access to system schemas, `GRANT` privileges

```sql
-- PostgreSQL: Properly scoped application account
CREATE ROLE myapp LOGIN PASSWORD '...';

-- Grant schema usage (required to access objects in the schema)
GRANT USAGE ON SCHEMA app_data TO myapp;

-- Grant specific DML permissions on specific tables
GRANT SELECT, INSERT, UPDATE ON app_data.orders TO myapp;
GRANT SELECT, INSERT, UPDATE ON app_data.order_items TO myapp;
GRANT SELECT ON app_data.products TO myapp;  -- Read-only for product catalog

-- Do NOT grant DELETE (application archives, doesn't delete)
-- Do NOT grant DDL (CREATE/ALTER/DROP)
-- Do NOT grant access to other schemas
```

### Separation of Duties for DBAs

The DBA role itself should be decomposed to enforce separation of duties:

- **DBA-Operations**: Can tune queries, monitor performance, manage backup/recovery. Cannot modify data or grant privileges.
- **DBA-Security**: Can manage user accounts and privileges. Cannot modify production data or perform backup/recovery.
- **DBA-Developer**: Can create/modify schema objects in development. Cannot access production.
- **Auditor**: Can query all audit log tables. Cannot modify any data or configuration.

No single person should have all DBA capabilities simultaneously. Emergency access procedures (break-glass accounts) should exist for situations requiring elevated access, but these accounts should require approval, be logged, and trigger alerts.

### Privilege Escalation Risks

Several patterns create privilege escalation risks that security assessments commonly find:

**PUBLIC role abuse**: SQL Server, Oracle, and PostgreSQL all have a PUBLIC role/privilege that is automatically granted to every user. Privileges granted to PUBLIC are available to all database users. Never grant privileges on sensitive objects to PUBLIC. Review existing PUBLIC grants periodically.

```sql
-- Find dangerous PUBLIC grants in Oracle
SELECT table_name, privilege, grantable
FROM dba_tab_privs
WHERE grantee = 'PUBLIC'
ORDER BY table_name;
```

**Excessive EXECUTE grants on powerful packages**: In Oracle, packages like `UTL_FILE`, `UTL_HTTP`, `UTL_TCP`, and `DBMS_SCHEDULER` can be abused to read files from the OS, make outbound network connections, or execute OS commands. Granting EXECUTE on these packages to application accounts enables significant privilege escalation beyond the database.

**EXECUTE AS and impersonation**: SQL Server's `EXECUTE AS` clause and the `SETUSER` command in PostgreSQL allow executing code in the security context of another user. If impersonation permissions are misconfigured, a lower-privileged user may be able to temporarily assume a higher-privileged identity.

## Views as Access Control Mechanisms

Views provide a powerful and flexible access control tool. A view can:

1. **Restrict columns**: The view definition selects only non-sensitive columns
2. **Restrict rows**: The view's WHERE clause filters to only authorized data
3. **Abstract schema**: Changes to underlying table structure don't break application access through views
4. **Mask data**: Views can apply masking functions to partially obscure sensitive data

```sql
-- A view that masks SSN and limits row visibility to active employees
CREATE VIEW hr_safe.employee_public_info AS
SELECT
    employee_id,
    first_name,
    last_name,
    department,
    office_location,
    CONCAT('XXX-XX-', RIGHT(ssn, 4)) AS ssn_masked,  -- Show only last 4 digits
    hire_date
FROM hr.employees
WHERE employment_status = 'ACTIVE';

-- Grant access to view only — no access to underlying hr.employees table
GRANT SELECT ON hr_safe.employee_public_info TO hr_reporting_role;
```

## Schema-Level Isolation for Multi-Tenancy

In multi-tenant database architectures — where multiple customers or business units share a single database instance — schema-level isolation provides security boundaries between tenants.

Each tenant's data lives in a separate schema with a dedicated service account. PostgreSQL's `search_path` setting controls which schemas are visible by default. By setting each application session's `search_path` to only the tenant's schema, accidental cross-tenant access through unqualified table names is prevented.

```sql
-- PostgreSQL multi-tenant setup
CREATE SCHEMA tenant_acme;
CREATE SCHEMA tenant_globex;

CREATE ROLE tenant_acme_app LOGIN;
CREATE ROLE tenant_globex_app LOGIN;

-- Each role can only access its own schema
GRANT USAGE ON SCHEMA tenant_acme TO tenant_acme_app;
GRANT ALL ON ALL TABLES IN SCHEMA tenant_acme TO tenant_acme_app;
-- tenant_acme_app has NO privileges on tenant_globex schema

-- At connection time, set search_path to enforce isolation
ALTER ROLE tenant_acme_app SET search_path = tenant_acme;
```

## Database Links and Linked Servers

**Oracle Database Links** and **SQL Server Linked Servers** allow one database to issue queries against another database, potentially on a remote server. These features create significant security risks if not carefully managed.

Database links in Oracle execute queries on the remote database using the credentials configured in the link definition. If a database link is configured with DBA credentials on the remote database, any user who can access the link inherits those DBA-level privileges on the remote system — a direct cross-database privilege escalation path.

```sql
-- Oracle: Review all database links and their connection users
SELECT db_link, username, host FROM dba_db_links;

-- Ensure no database links use DBA-level remote accounts
-- Each link should use a minimally privileged remote account
```

SQL Server linked servers present similar risks. The `sp_addlinkedsrvlogin` procedure maps local logins to remote server logins. A poorly configured linked server may allow any SQL Server login to connect to the remote server as SA. Security assessors routinely check linked server configurations for this pattern.

---

## Key Terms

| Term | Definition |
|------|------------|
| **Discretionary Access Control (DAC)** | Access control model where object owners have discretion over who can access their objects |
| **Mandatory Access Control (MAC)** | Access control model where centrally defined policy governs access, overriding owner discretion |
| **Role-Based Access Control (RBAC)** | Access control model where privileges are assigned to roles and roles are assigned to users |
| **GRANT** | SQL statement that assigns a privilege to a user or role |
| **REVOKE** | SQL statement that removes a previously granted privilege |
| **WITH GRANT OPTION** | Allows a privilege recipient to grant that privilege to others — creates privilege spread risk |
| **Row-Level Security (RLS)** | Database mechanism that automatically filters query results based on the user's identity |
| **Oracle VPD** | Virtual Private Database — Oracle's RLS mechanism using automatic WHERE clause predicates |
| **Oracle Label Security (OLS)** | Oracle's MAC implementation using sensitivity labels on rows |
| **Ownership Chain** | SQL Server/Oracle behavior where object permissions are checked only at the chain entry point |
| **Least Privilege** | Security principle requiring users to have only the minimum access necessary for their function |
| **Separation of Duties** | Distributing sensitive functions across multiple roles to prevent fraud or undetected error |
| **PUBLIC Role** | A role automatically held by every database user — privileges granted to PUBLIC apply to everyone |
| **Schema Isolation** | Using separate schemas and role restrictions to create security boundaries between application modules |
| **Multi-tenancy** | Architecture where multiple customers or units share a single database with data isolation |
| **Database Link** | Oracle mechanism for one database to issue queries against another database |
| **Linked Server** | SQL Server mechanism for querying remote database servers |
| **Privilege Escalation** | Gaining access beyond what is directly authorized through exploiting misconfiguration or software flaws |
| **Column-Level Privilege** | Permission to access specific columns rather than an entire table |
| **Security Predicate** | SQL Server RLS function that returns a filter condition applied to row-level access checks |

---

## Review Questions

1. **Applied**: A table called `patient_records` in a hospital database contains the following columns: `patient_id`, `full_name`, `date_of_birth`, `ssn`, `diagnosis`, `medications`, `treating_physician`, `billing_insurance`. Design a complete column-level and view-based access control scheme for three roles: Billing Clerk, Treating Nurse, and Medical Records Auditor. Write the SQL to implement your design.

2. **Conceptual**: Explain the `WITH GRANT OPTION` problem in detail. Give an example scenario where improper use of `WITH GRANT OPTION` leads to uncontrolled privilege spread, and describe the administrative process required to track and revoke such privileges.

3. **Applied**: Implement PostgreSQL Row Level Security on an `orders` table so that: (a) sales representatives can only see orders they created (using `created_by = current_user`), (b) regional managers can see all orders in their region (using an application-context setting), (c) the DBA role bypasses RLS and sees all rows. Write all required SQL statements.

4. **Conceptual**: Compare Oracle Label Security (MAC) to PostgreSQL Row Level Security (DAC-based). What categories of threats does OLS address that PostgreSQL RLS cannot? Under what circumstances would OLS be required rather than PostgreSQL RLS?

5. **Applied**: Conduct a privilege audit query for a PostgreSQL database: write a query against `information_schema.role_table_grants` that identifies any application roles that have been granted DDL privileges (CREATE, DROP, ALTER) or that have SELECT on system catalog tables. Explain why each of these findings represents a security risk.

6. **Conceptual**: Explain how an Oracle Database Link can be used for privilege escalation. What configuration of the database link creates this risk, and what privilege design on the remote database end would eliminate it?

7. **Applied**: A security assessment of a SQL Server database reveals the following: the PUBLIC role has EXECUTE on `xp_cmdshell`, the application service account is a member of `db_owner`, and there are linked server connections configured to use SA credentials on remote servers. For each finding, explain the specific attack scenario it enables and the remediation steps required.

8. **Conceptual**: Describe the security benefits of using stored procedures as the sole data access interface (no direct table grants to application accounts). What specific threats does this pattern mitigate, and what are its limitations?

9. **Applied**: Design a multi-tenant PostgreSQL schema where three tenants (Alpha Corp, Beta Inc, Gamma LLC) share one database instance. Create schemas, roles, and grants such that each tenant's application account can only access its own schema. Write SQL demonstrating that the Alpha Corp application role cannot query Beta Inc's tables.

10. **Conceptual**: The principle of least privilege is easy to state but difficult to implement in practice. Describe three organizational or technical obstacles that prevent proper least privilege implementation in real enterprise database environments, and propose solutions for each obstacle.

---

## Further Reading

- **Ferraiolo, D. F., Sandhu, R., Gavrila, S., Kuhn, D. R., & Chandramouli, R. (2001). "Proposed NIST Standard for Role-Based Access Control." *ACM Transactions on Information and System Security*, 4(3), 224–274.** The foundational academic paper defining the RBAC reference model that underlies database role systems.

- **Oracle Corporation. (2023). *Oracle Database Label Security Administrator's Guide, 19c*.** Comprehensive reference for OLS label design, policy creation, and enforcement. Available at docs.oracle.com.

- **PostgreSQL Global Development Group. (2024). *PostgreSQL 16 Documentation: Chapter 5.8 — Row Security Policies*.** Authoritative technical reference for PostgreSQL RLS policy design and implementation. Available at postgresql.org/docs.

- **Microsoft. (2024). *Row-Level Security in SQL Server and Azure SQL*.** Covers security predicate functions, filter predicates, block predicates, and performance considerations. Available at docs.microsoft.com.

- **Bertino, E., & Sandhu, R. (2005). "Database Security — Concepts, Approaches, and Challenges." *IEEE Transactions on Dependable and Secure Computing*, 2(1), 2–19.** Comprehensive academic survey of database access control models including DAC, MAC, RBAC, and emerging models — excellent theoretical foundation for understanding the design space.
