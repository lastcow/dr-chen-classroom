---
title: "Week 9 — Database Security: Authentication & Authorization"
description: Implement MySQL and PostgreSQL user account management, authentication plugins, role-based access control, privilege hierarchies, SSL/TLS connections, and SQL injection defenses at the database layer.
---

# Week 9 — Database Security: Authentication & Authorization

<div class="week-meta" markdown>
**Course Objectives:** CO7 &nbsp;|&nbsp; **Focus:** Authentication & Authorization &nbsp;|&nbsp; **Difficulty:** ⭐⭐⭐☆☆
</div>

---

## Learning Objectives

By the end of this week, you will be able to:

- [ ] Create MySQL user accounts with precise host specifications and authentication plugins
- [ ] Configure the `validate_password` plugin and account lockout policies
- [ ] Grant and revoke privileges at global, database, table, column, and routine levels
- [ ] Design and implement a role-based access control (RBAC) model for a multi-tier application
- [ ] Apply the principle of least privilege to define distinct privilege matrices for app, DBA, and reporting roles
- [ ] Audit current grants using `information_schema` privilege tables and `SHOW GRANTS`
- [ ] Configure MySQL SSL/TLS requirements and verify encrypted connections
- [ ] Explain PostgreSQL's `pg_hba.conf` authentication model and row-level security policies
- [ ] Defend against SQL injection at the database layer using parameterized queries and stored procedures

---

## 1. MySQL User Account Model

### 1.1 User Account Anatomy

In MySQL, a user account is identified by a **user@host pair**, not just a username. Two accounts with the same username but different hosts are completely separate accounts with separate privileges:

```sql
'jchen'@'localhost'       -- can only connect from the server itself
'jchen'@'10.0.1.%'        -- can connect from 10.0.1.0/24 subnet
'jchen'@'%'               -- can connect from any host
'jchen'@'10.0.1.50'       -- can connect from exactly this IP
'jchen'@'webserver01.frostburg.edu'  -- exact hostname (DNS resolved at login)
```

!!! danger "The '%' Wildcard Risk"
    Creating `'app_user'@'%'` allows connections from **any IP address on the internet** if your MySQL port (3306) is exposed. Always use specific host restrictions. For application servers, use the exact IP or subnet, not `%`. Reserve `%` only for temporary administrative accounts in firewalled environments.

### 1.2 CREATE USER Syntax

```sql
-- Basic account creation
CREATE USER 'student_app'@'10.0.1.0/255.255.255.0'
    IDENTIFIED BY 'S3cur3P@ssw0rd!'
    PASSWORD EXPIRE INTERVAL 90 DAY
    FAILED_LOGIN_ATTEMPTS 5
    PASSWORD_LOCK_TIME 1;   -- lock for 1 day after 5 failures

-- Account with specific authentication plugin
CREATE USER 'reporting'@'10.0.2.50'
    IDENTIFIED WITH caching_sha2_password BY 'R3portPass#2024'
    REQUIRE SSL;            -- SSL/TLS connection mandatory

-- Account that never expires (service account)
CREATE USER 'etl_service'@'localhost'
    IDENTIFIED WITH mysql_native_password BY 'ETLserv!ce#99'
    PASSWORD EXPIRE NEVER
    ACCOUNT UNLOCK;

-- Modify existing user
ALTER USER 'student_app'@'10.0.1.0/255.255.255.0'
    PASSWORD EXPIRE NOW;        -- force password change at next login

ALTER USER 'reporting'@'10.0.2.50'
    ACCOUNT LOCK;               -- disable without deleting

-- Rename/move a user
RENAME USER 'old_name'@'localhost' TO 'new_name'@'localhost';

-- Remove user
DROP USER IF EXISTS 'temp_user'@'%';
```

### 1.3 Authentication Plugins

=== "caching_sha2_password (Default, MySQL 8)"

    The default plugin since MySQL 8.0. Uses SHA-256 hashing with salting and caches authentication data for performance.

    ```sql
    CREATE USER 'newuser'@'%'
        IDENTIFIED WITH caching_sha2_password BY 'StrongPass1!';

    -- Check current default plugin
    SHOW VARIABLES LIKE 'default_authentication_plugin';
    -- default_authentication_plugin: caching_sha2_password

    -- Verify user's plugin
    SELECT user, host, plugin FROM mysql.user WHERE user = 'newuser';
    ```

    !!! warning "Client Compatibility"
        `caching_sha2_password` requires an updated client library (MySQL Connector 8.0+, libmysqlclient 8.0+). Older applications (PHP 5.x, Python MySQLdb 1.x) may fail to connect. In that case, fall back to `mysql_native_password` for that specific account.

=== "mysql_native_password"

    Legacy plugin using SHA-1. Still widely supported but less secure. Being deprecated.

    ```sql
    -- Create user with legacy plugin (for older client compatibility)
    CREATE USER 'legacy_app'@'192.168.1.10'
        IDENTIFIED WITH mysql_native_password BY 'AppP@ss2024';

    -- Convert existing user to caching_sha2_password
    ALTER USER 'legacy_app'@'192.168.1.10'
        IDENTIFIED WITH caching_sha2_password BY 'NewStrongP@ss!';
    ```

=== "LDAP and PAM Plugins"

    Enterprise authentication via corporate directory:

    ```sql
    -- MySQL Enterprise LDAP plugin
    CREATE USER 'ad_user'@'%'
        IDENTIFIED WITH authentication_ldap_simple
        BY 'cn=ad_user,ou=DBUsers,dc=frostburg,dc=edu';

    -- PAM authentication (Linux/Unix integration)
    CREATE USER 'pam_user'@'localhost'
        IDENTIFIED WITH auth_pam;
    -- Authentication deferred to PAM stack (/etc/pam.d/mysqld)
    ```

---

## 2. Password Policies and Account Security

### 2.1 The validate_password Plugin

```sql
-- Install (if not already loaded)
INSTALL PLUGIN validate_password SONAME 'validate_password.so';

-- Or for MySQL 8.0.4+ (component-based):
INSTALL COMPONENT 'file://component_validate_password';

-- Configure policy
SET GLOBAL validate_password.policy = 'STRONG';
-- STRONG requires: length + uppercase + lowercase + digits + special chars + no dictionary words

SET GLOBAL validate_password.length          = 12;
SET GLOBAL validate_password.mixed_case_count = 2;
SET GLOBAL validate_password.number_count    = 2;
SET GLOBAL validate_password.special_char_count = 1;

-- Test a prospective password
SELECT VALIDATE_PASSWORD_STRENGTH('weak');      -- returns 0–100
SELECT VALIDATE_PASSWORD_STRENGTH('MyC0mplex!Pass#23');  -- should return 100
```

| Policy Level | Requirements |
|-------------|-------------|
| `LOW` | Length only (≥ `validate_password.length`) |
| `MEDIUM` | Length + digits + uppercase + lowercase + special chars |
| `STRONG` | MEDIUM + no dictionary word substrings |

### 2.2 Account Lockout and Expiration

```sql
-- Force password expiration after 90 days (global default)
SET GLOBAL default_password_lifetime = 90;

-- Per-account expiration
ALTER USER 'instructor_portal'@'%'
    PASSWORD EXPIRE INTERVAL 60 DAY;

-- Never expire (service accounts)
ALTER USER 'etl_service'@'localhost'
    PASSWORD EXPIRE NEVER;

-- Lock account after N failed attempts, unlock after M days
ALTER USER 'web_app'@'10.0.1.%'
    FAILED_LOGIN_ATTEMPTS 3
    PASSWORD_LOCK_TIME 2;    -- 2 days; UNBOUNDED = indefinite until admin unlocks

-- Manual unlock
ALTER USER 'web_app'@'10.0.1.%' ACCOUNT UNLOCK;

-- Check locked accounts
SELECT user, host, account_locked, password_expired,
       password_lifetime, password_last_changed
FROM mysql.user
WHERE account_locked = 'Y' OR password_expired = 'Y';
```

!!! tip "Service Account Best Practice"
    Service accounts (ETL pipelines, application backends, monitoring agents) should have `PASSWORD EXPIRE NEVER` and `FAILED_LOGIN_ATTEMPTS` set to a higher threshold (10+) to prevent accidental lockout causing an application outage. Rotate passwords through configuration management (Ansible, Vault), not expiration policies.

---

## 3. The GRANT System

### 3.1 Privilege Levels

MySQL privileges form a hierarchy from broadest to most granular:

```
GLOBAL (*.*)
  └── DATABASE (university.*)
        └── TABLE (university.students)
              └── COLUMN (university.students.gpa)
                    └── ROUTINE (PROCEDURE / FUNCTION)
```

```sql
-- Global: applies to ALL databases (use sparingly)
GRANT PROCESS, REPLICATION SLAVE ON *.* TO 'replica_user'@'10.0.3.%';

-- Database-level
GRANT SELECT, INSERT, UPDATE, DELETE ON university.* TO 'app_user'@'10.0.1.%';

-- Table-level
GRANT SELECT ON university.students TO 'reporting'@'10.0.2.%';
GRANT SELECT ON university.courses  TO 'reporting'@'10.0.2.%';

-- Column-level (most granular — use when views aren't appropriate)
GRANT SELECT (student_id, first_name, last_name, dept_id, gpa)
    ON university.students
    TO 'limited_access'@'localhost';
-- This user CANNOT select ssn or date_of_birth even with SELECT on other columns

-- Routine-level
GRANT EXECUTE ON PROCEDURE university.get_student_transcript
    TO 'app_user'@'10.0.1.%';

-- WITH GRANT OPTION: allow user to grant their privileges to others
GRANT SELECT ON university.* TO 'dept_admin'@'localhost' WITH GRANT OPTION;
```

!!! danger "WITH GRANT OPTION Danger"
    A user with `WITH GRANT OPTION` can potentially escalate privileges by granting their access to a new account they control. Only grant this to DBAs you fully trust. Auditing `WITH GRANT OPTION` holders should be part of your regular security review.

### 3.2 Common Privilege Reference

| Privilege | Scope | Usage |
|-----------|-------|-------|
| `SELECT` | Table/Column | Read data |
| `INSERT` | Table/Column | Add rows |
| `UPDATE` | Table/Column | Modify rows |
| `DELETE` | Table | Remove rows |
| `CREATE` | Database/Table | Create objects |
| `DROP` | Database/Table | Delete objects |
| `INDEX` | Table | Create/drop indexes |
| `ALTER` | Table | Modify table structure |
| `CREATE VIEW` | Database | Create views |
| `SHOW VIEW` | Database | See view definitions |
| `EXECUTE` | Routine | Call stored procedures/functions |
| `TRIGGER` | Table | Create/execute triggers |
| `LOCK TABLES` | Table | Explicit table locking |
| `PROCESS` | Global | See all running threads |
| `SUPER` | Global | Override restrictions; dangerous |
| `REPLICATION SLAVE` | Global | Read binary log for replication |

### 3.3 Revoking Access

```sql
-- Revoke specific privilege
REVOKE DELETE ON university.students FROM 'app_user'@'10.0.1.%';

-- Revoke all privileges (keeps user account, removes all grants)
REVOKE ALL PRIVILEGES, GRANT OPTION FROM 'old_contractor'@'%';

-- Verify after revoke
SHOW GRANTS FOR 'app_user'@'10.0.1.%';
-- Should no longer show DELETE on students

-- Complete removal (revoke + drop)
DROP USER 'old_contractor'@'%';

-- After manual grants table edits (rare), flush
FLUSH PRIVILEGES;
-- Note: using GRANT/REVOKE/CREATE USER automatically flushes
```

---

## 4. Role-Based Access Control (RBAC)

### 4.1 Creating and Assigning Roles

MySQL 8.0 introduced proper roles. A role is a named collection of privileges:

```sql
-- Create roles
CREATE ROLE 'university_readonly';
CREATE ROLE 'university_instructor';
CREATE ROLE 'university_registrar';
CREATE ROLE 'university_dba';

-- Grant privileges TO roles (not users)
GRANT SELECT ON university.* TO 'university_readonly';

GRANT SELECT, INSERT, UPDATE ON university.grades      TO 'university_instructor';
GRANT SELECT ON university.students    TO 'university_instructor';
GRANT SELECT ON university.courses     TO 'university_instructor';
GRANT SELECT ON university.enrollments TO 'university_instructor';

GRANT SELECT, INSERT, UPDATE, DELETE
    ON university.enrollments  TO 'university_registrar';
GRANT SELECT, INSERT, UPDATE
    ON university.students     TO 'university_registrar';
GRANT SELECT ON university.courses TO 'university_registrar';

GRANT ALL PRIVILEGES ON university.* TO 'university_dba';

-- Grant roles to users
GRANT 'university_instructor' TO 'prof_chen'@'localhost';
GRANT 'university_instructor' TO 'prof_jones'@'localhost';
GRANT 'university_registrar'  TO 'reg_staff1'@'10.0.4.%';
GRANT 'university_readonly'   TO 'reporting'@'10.0.2.%';

-- Roles can be nested (role-within-role)
GRANT 'university_readonly' TO 'university_instructor';
-- Instructors automatically inherit readonly privileges
```

### 4.2 Activating Roles

Roles must be activated before they take effect in a session:

```sql
-- Set default role(s) for a user (auto-activated at login)
SET DEFAULT ROLE 'university_instructor' TO 'prof_chen'@'localhost';

-- Or auto-activate ALL granted roles (server-wide setting)
SET GLOBAL activate_all_roles_on_login = ON;

-- In a session: manually activate a role
SET ROLE 'university_instructor';
SET ROLE ALL;    -- activate all granted roles
SET ROLE NONE;   -- deactivate all roles (drop to base user privileges)

-- Check currently active roles in this session
SELECT CURRENT_ROLE();

-- View all role assignments
SELECT FROM_USER, FROM_HOST, TO_USER, TO_HOST, WITH_ADMIN_OPTION
FROM information_schema.ROLE_EDGES
WHERE TO_USER LIKE 'prof_%';
```

### 4.3 University Privilege Matrix

| Role | students | courses | enrollments | grades | departments | mysql.user |
|------|----------|---------|-------------|--------|-------------|-----------|
| `university_readonly` | SELECT | SELECT | SELECT | SELECT | SELECT | — |
| `university_instructor` | SELECT | SELECT, UPDATE | SELECT | SELECT, INSERT, UPDATE | SELECT | — |
| `university_registrar` | SELECT, INSERT, UPDATE | SELECT | SELECT, INSERT, UPDATE, DELETE | SELECT | SELECT | — |
| `university_dba` | ALL | ALL | ALL | ALL | ALL | ALL |
| `app_backend` | SELECT, INSERT, UPDATE | SELECT | SELECT, INSERT, UPDATE, DELETE | SELECT, INSERT, UPDATE | SELECT | — |

```sql
-- Application backend user (principle of least privilege)
CREATE USER 'app_backend'@'10.0.1.0/255.255.255.0'
    IDENTIFIED WITH caching_sha2_password BY 'B@ckendP@ss!2024'
    REQUIRE SSL
    MAX_QUERIES_PER_HOUR 100000
    MAX_USER_CONNECTIONS 50;

CREATE ROLE 'app_backend_role';
GRANT SELECT, INSERT, UPDATE ON university.students    TO 'app_backend_role';
GRANT SELECT                 ON university.courses     TO 'app_backend_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON university.enrollments TO 'app_backend_role';
GRANT SELECT, INSERT, UPDATE ON university.grades      TO 'app_backend_role';
GRANT SELECT                 ON university.departments TO 'app_backend_role';

GRANT 'app_backend_role' TO 'app_backend'@'10.0.1.0/255.255.255.0';
SET DEFAULT ROLE 'app_backend_role' TO 'app_backend'@'10.0.1.0/255.255.255.0';
```

---

## 5. Auditing Grants with information_schema

### 5.1 Privilege Views

```sql
-- All global privileges
SELECT GRANTEE, PRIVILEGE_TYPE, IS_GRANTABLE
FROM information_schema.USER_PRIVILEGES
ORDER BY GRANTEE;

-- Database-level privileges
SELECT GRANTEE, TABLE_SCHEMA, PRIVILEGE_TYPE, IS_GRANTABLE
FROM information_schema.SCHEMA_PRIVILEGES
WHERE TABLE_SCHEMA = 'university'
ORDER BY GRANTEE, PRIVILEGE_TYPE;

-- Table-level privileges
SELECT GRANTEE, TABLE_SCHEMA, TABLE_NAME, PRIVILEGE_TYPE
FROM information_schema.TABLE_PRIVILEGES
WHERE TABLE_SCHEMA = 'university'
ORDER BY GRANTEE, TABLE_NAME;

-- Column-level privileges
SELECT GRANTEE, TABLE_NAME, COLUMN_NAME, PRIVILEGE_TYPE
FROM information_schema.COLUMN_PRIVILEGES
WHERE TABLE_SCHEMA = 'university'
ORDER BY GRANTEE, TABLE_NAME, COLUMN_NAME;
```

### 5.2 Security Audit Script

```sql
-- Find users with dangerous global privileges
SELECT user, host, Super_priv, Grant_priv, Create_user_priv, Shutdown_priv
FROM mysql.user
WHERE Super_priv = 'Y' OR Shutdown_priv = 'Y'
ORDER BY user;

-- Find accounts with no password (security critical!)
SELECT user, host, authentication_string, plugin
FROM mysql.user
WHERE authentication_string = ''
   OR authentication_string IS NULL;

-- Find accounts where password never expires
SELECT user, host, password_lifetime, password_last_changed
FROM mysql.user
WHERE password_lifetime IS NULL
  AND user NOT IN ('root', 'mysql.sys', 'mysql.infoschema');

-- Full grant summary report
SELECT
    GRANTEE,
    GROUP_CONCAT(PRIVILEGE_TYPE ORDER BY PRIVILEGE_TYPE SEPARATOR ', ') AS global_privs
FROM information_schema.USER_PRIVILEGES
GROUP BY GRANTEE
HAVING global_privs NOT IN ('USAGE')  -- USAGE = no privileges
ORDER BY GRANTEE;
```

---

## 6. Network and Connection Security

### 6.1 SSL/TLS Configuration

```bash
# Generate server certificates (production: use CA-signed certs)
mysql_ssl_rsa_setup --datadir=/var/lib/mysql

# Resulting files:
# ca.pem, ca-key.pem        — Certificate Authority
# server-cert.pem, server-key.pem  — Server certificate
# client-cert.pem, client-key.pem  — Client certificate
```

```ini
# my.cnf: configure SSL on the server
[mysqld]
ssl_ca   = /var/lib/mysql/ca.pem
ssl_cert = /var/lib/mysql/server-cert.pem
ssl_key  = /var/lib/mysql/server-key.pem
require_secure_transport = ON   # reject non-SSL connections globally
```

```sql
-- Verify SSL is active
SHOW VARIABLES LIKE 'have_ssl';      -- YES
SHOW VARIABLES LIKE 'ssl_cipher';    -- current cipher suite

-- Create user requiring SSL
CREATE USER 'secure_user'@'%'
    IDENTIFIED BY 'P@ssword123!'
    REQUIRE SSL;

-- Require specific cipher
CREATE USER 'pci_user'@'10.0.5.%'
    IDENTIFIED BY 'PCIsecure1!'
    REQUIRE CIPHER 'ECDHE-RSA-AES256-GCM-SHA384';

-- Require client certificate (mutual TLS)
CREATE USER 'mtls_user'@'%'
    IDENTIFIED BY 'mTLSpass!'
    REQUIRE X509;   -- client must present a valid certificate

-- Verify connection encryption for the current session
SELECT * FROM performance_schema.session_status
WHERE VARIABLE_NAME IN ('Ssl_cipher', 'Ssl_version', 'Ssl_verify_mode');
```

### 6.2 Connection Limits and Bind Address

```sql
-- Limit connections per user
ALTER USER 'app_backend'@'10.0.1.%'
    MAX_CONNECTIONS_PER_HOUR 0      -- 0 = unlimited
    MAX_QUERIES_PER_HOUR     200000
    MAX_UPDATES_PER_HOUR     50000
    MAX_USER_CONNECTIONS     100;   -- max simultaneous connections

-- Global connection settings (my.cnf)
-- max_connections = 500          (total server connections)
-- max_user_connections = 100     (per-user global default)
```

```ini
# my.cnf: restrict to internal network only
[mysqld]
bind-address = 10.0.1.1    # listen only on internal interface, NOT 0.0.0.0
port         = 3306
```

!!! danger "Never Expose MySQL Directly to the Internet"
    MySQL port 3306 should **never** be reachable from the public internet. Use:
    - `bind-address` to listen on internal IPs only
    - Firewall rules (iptables, ufw, AWS Security Groups) to restrict port 3306
    - SSH tunneling or VPN for remote DBA access
    - Cloud: place RDS/Cloud SQL in a private subnet with no internet route

---

## 7. PostgreSQL Security Model

### 7.1 pg_hba.conf Authentication

PostgreSQL uses a **host-based authentication file** (`pg_hba.conf`) to control who can connect, from where, and how they authenticate — separate from the SQL privilege system:

```
# pg_hba.conf format:
# TYPE   DATABASE   USER         ADDRESS          METHOD
local    all        postgres                      peer
local    university app_user                      md5
host     university app_user     10.0.1.0/24      scram-sha-256
host     university reporting    10.0.2.0/24      scram-sha-256
hostssl  university pci_user     10.0.5.0/24      cert   clientcert=verify-full
host     all        all          0.0.0.0/0        reject
```

| Method | Description |
|--------|-------------|
| `trust` | No password — **never use in production** |
| `reject` | Always deny (use as catch-all at end) |
| `peer` | Unix socket: match OS username (local connections) |
| `md5` | MD5-hashed password (legacy; deprecated) |
| `scram-sha-256` | Current recommended password method |
| `cert` | SSL client certificate authentication |
| `ldap` | LDAP server authentication |
| `pam` | Pluggable Authentication Modules |

### 7.2 Schema Privileges and Row-Level Security

```sql
-- PostgreSQL: schema-level privilege model
GRANT USAGE ON SCHEMA university TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA university TO app_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA university TO app_user;

-- Default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA university
    GRANT SELECT ON TABLES TO reporting_role;

-- Row-Level Security (RLS) — PostgreSQL 9.5+
-- Each student can only see their own enrollment records

ALTER TABLE enrollments ENABLE ROW LEVEL SECURITY;

-- Policy: students see only their rows
CREATE POLICY student_sees_own_enrollments
    ON enrollments
    FOR SELECT
    USING (
        student_id = (
            SELECT student_id FROM students
            WHERE email = current_user
        )
    );

-- Instructors see enrollments for their courses
CREATE POLICY instructor_sees_course_enrollments
    ON enrollments
    FOR SELECT
    USING (
        course_id IN (
            SELECT course_id FROM courses
            WHERE instructor_email = current_user
        )
    );

-- Registrar bypasses all RLS (role with BYPASSRLS attribute)
ALTER ROLE registrar_role BYPASSRLS;
```

---

## 8. SQL Injection Defense at the Database Layer

### 8.1 The SQL Injection Threat Model

SQL injection occurs when untrusted input is interpolated into a SQL string rather than passed as a bound parameter:

```python
# ❌ VULNERABLE: string interpolation — NEVER do this
student_id = request.args.get('id')
query = f"SELECT * FROM students WHERE student_id = {student_id}"
# Attacker sends: id=1 OR 1=1 -- 
# Executed: SELECT * FROM students WHERE student_id = 1 OR 1=1 --
# Returns ALL students!

# ✅ SAFE: parameterized query (Python mysql-connector)
import mysql.connector
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor(dictionary=True)
cursor.execute(
    "SELECT student_id, first_name, last_name, gpa FROM students WHERE student_id = %s",
    (student_id,)   # parameter binding — never string-formatted
)
result = cursor.fetchall()
```

### 8.2 Stored Procedure Defense Layer

Stored procedures can serve as an additional injection barrier by providing a controlled API:

```sql
DELIMITER //
CREATE PROCEDURE get_student_transcript(
    IN p_student_id   INT,
    IN p_semester     CHAR(6)
)
BEGIN
    -- Input validation
    IF p_student_id <= 0 OR p_semester NOT REGEXP '^[0-9]{4}(FA|SP|SU)$' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Invalid input parameters';
    END IF;

    SELECT
        s.student_id,
        s.first_name,
        s.last_name,
        c.course_code,
        c.title,
        e.grade
    FROM students s
    JOIN enrollments e ON s.student_id = e.student_id
    JOIN courses     c ON e.course_id  = c.course_id
    WHERE s.student_id = p_student_id
      AND e.semester   = p_semester;
END //
DELIMITER ;

-- Grant only EXECUTE on the procedure, not SELECT on tables
GRANT EXECUTE ON PROCEDURE university.get_student_transcript
    TO 'portal_app'@'10.0.1.%';
REVOKE ALL ON university.students FROM 'portal_app'@'10.0.1.%';
REVOKE ALL ON university.enrollments FROM 'portal_app'@'10.0.1.%';
```

### 8.3 Database-Layer Defense Checklist

```sql
-- 1. Application account should have ONLY necessary privileges
SHOW GRANTS FOR 'portal_app'@'10.0.1.%';

-- 2. Verify no account can run arbitrary DDL
SELECT user, host, Create_priv, Drop_priv, Alter_priv
FROM mysql.user WHERE user = 'portal_app';
-- All should be 'N'

-- 3. Enable MySQL general query log temporarily to inspect all queries
SET GLOBAL general_log = 'ON';
SET GLOBAL general_log_file = '/var/log/mysql/general.log';
-- Review for suspicious patterns, then turn off (performance impact)
SET GLOBAL general_log = 'OFF';

-- 4. Create a read-only proxy view for the application
-- If the app only reads students, use a view and only grant SELECT on the view
```

!!! success "Defense in Depth"
    Database-layer defenses are the **last line of defense** — they must work even when application code has bugs. The combination of: (1) parameterized queries in the application, (2) minimum-privilege application accounts, (3) stored procedure APIs, and (4) network restrictions provides defense-in-depth that prevents a single SQLi bug from becoming a catastrophic breach.

---

## Key Vocabulary

| Term | Definition |
|------|------------|
| **user@host pair** | MySQL's identity for an account: username plus allowed connection host |
| **authentication plugin** | MySQL module implementing the password verification algorithm |
| **caching_sha2_password** | Default MySQL 8 plugin; SHA-256 with performance caching |
| **mysql_native_password** | Legacy SHA-1 plugin; deprecated but still supported |
| **validate_password** | MySQL component that enforces password complexity rules |
| **FAILED_LOGIN_ATTEMPTS** | MySQL setting to lock an account after N consecutive bad passwords |
| **GRANT** | SQL command assigning a privilege to a user or role |
| **REVOKE** | SQL command removing a privilege from a user or role |
| **privilege level** | Scope at which a privilege applies: global, database, table, column, routine |
| **WITH GRANT OPTION** | Allows a user to grant their privileges to other users |
| **role** | Named collection of privileges; assigned to users |
| **RBAC** | Role-Based Access Control: assign privileges to roles, not individual users |
| **activate_all_roles_on_login** | MySQL server variable that auto-activates all granted roles at login |
| **principle of least privilege** | Users and services should have only the minimum permissions required |
| **REQUIRE SSL** | User account constraint mandating TLS-encrypted connections |
| **mutual TLS (mTLS)** | Both client and server present certificates; enforced with REQUIRE X509 |
| **pg_hba.conf** | PostgreSQL host-based authentication configuration file |
| **scram-sha-256** | Current recommended PostgreSQL password hashing method |
| **Row-Level Security (RLS)** | PostgreSQL policy system controlling which rows each user can see |
| **SQL injection** | Attack inserting malicious SQL via unsanitized user input |
| **parameterized query** | Query using placeholders (`?` or `%s`) for values, preventing injection |

---

## Self-Assessment

!!! question "Self-Assessment"
    1. A security audit finds that the application database account `web_app@'%'` has `GRANT ALL PRIVILEGES ON university.* WITH GRANT OPTION`. List five specific security problems this creates and rewrite the account definition (CREATE USER + GRANT statements) following the principle of least privilege for a web application that reads students/courses/enrollments and writes to enrollments.

    2. Your university's IT policy requires: (a) passwords expire every 60 days for human accounts, (b) service accounts never expire, (c) accounts lock for 24 hours after 5 failed logins. Write the complete SQL to implement this for three accounts: DBA `jchen@localhost`, application service `webapp@10.0.1.0/24`, and reporting user `bi_reader@10.0.2.50`.

    3. Design a complete RBAC scheme for the university database with four roles: `student_role` (read own records only), `instructor_role` (read/write grades for their courses), `registrar_role` (manage enrollments), and `dba_role` (full access). Write the CREATE ROLE, GRANT TO ROLE, and GRANT ROLE TO USER statements. Explain how role nesting could simplify the hierarchy.

    4. A developer proposes this Python code to look up a student: `cursor.execute("SELECT * FROM students WHERE email = '" + email_input + "'")`. Demonstrate a SQL injection attack payload that would dump all student SSNs, explain exactly how it works, and rewrite the code using parameterized queries with mysql-connector-python.

    5. Explain the PostgreSQL row-level security model: what are policies, how do they interact with the BYPASSRLS role attribute, and what happens when multiple policies apply to the same table and user? Write RLS policies for the `enrollments` table that allow students to see only their own rows and instructors to see all rows in courses they teach.

---

## Further Reading

- 📖 *MySQL 8.0 Reference Manual* — [Section 6: Security](https://dev.mysql.com/doc/refman/8.0/en/security.html)
- 📖 *PostgreSQL Documentation* — [Chapter 21: Database Roles](https://www.postgresql.org/docs/current/user-manag.html) and [Chapter 5.8: Row Security Policies](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- 📄 [MySQL 8.0 Role-Based Access Control](https://dev.mysql.com/blog-archive/mysql-8-0-roles/)
- 📄 [OWASP SQL Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)
- 📄 [CIS MySQL 8 Benchmark](https://www.cisecurity.org/benchmark/mysql) — Hardening guidelines
- 📄 [Percona Blog: MySQL User Account Security Best Practices](https://www.percona.com/blog/securing-mysql-user-accounts/)
- 🎥 *Securing MySQL in Production* — Percona Live (YouTube)

---

[← Week 8](week08.md) | [Course Index](index.md) | [Week 10 →](week10.md)
