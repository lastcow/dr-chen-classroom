---
title: "Week 10 — Database Security: Encryption, Auditing & Compliance"
description: Implement encryption at rest and in transit for MySQL, design audit trail systems, and understand GDPR, HIPAA, and PCI DSS compliance requirements as they apply to database architecture.
---

# Week 10 — Database Security: Encryption, Auditing & Compliance

<div class="week-meta" markdown>
**Course Objectives:** CO7 &nbsp;|&nbsp; **Focus:** Encryption, Auditing & Compliance &nbsp;|&nbsp; **Difficulty:** ⭐⭐⭐☆☆
</div>

---

## Learning Objectives

By the end of this week, you will be able to:

- [ ] Configure InnoDB tablespace encryption and explain the key management architecture
- [ ] Set up TLS for MySQL connections and verify cipher suite selection
- [ ] Implement column-level encryption using `AES_ENCRYPT`/`AES_DECRYPT` and explain key rotation
- [ ] Install the MySQL Audit Log plugin and configure filtered JSON audit output
- [ ] Build custom DDL and DML audit triggers for sensitive tables
- [ ] Map GDPR's right to erasure, data minimization, and retention requirements to database design decisions
- [ ] Describe HIPAA and PCI DSS database-specific controls and how they are implemented technically
- [ ] Evaluate MySQL Enterprise vs. community alternatives for encryption and auditing features

---

## 1. Encryption at Rest

### 1.1 InnoDB Tablespace Encryption

Encryption at rest protects data files on disk from unauthorized physical access — stolen drives, unauthorized filesystem access, or cloud storage exposure. InnoDB tablespace encryption encrypts at the **page level** within the storage engine.

```sql
-- Check if encryption is supported and keyring is loaded
SHOW VARIABLES LIKE 'have_ssl';
SELECT PLUGIN_NAME, PLUGIN_STATUS
FROM information_schema.PLUGINS
WHERE PLUGIN_NAME LIKE 'keyring%';

-- For community edition: install keyring_file plugin
-- In my.cnf (must be set before server starts):
-- [mysqld]
-- early-plugin-load = keyring_file.so
-- keyring_file_data = /var/lib/mysql-keyring/keyring

-- Verify keyring is loaded
SELECT * FROM performance_schema.keyring_keys;

-- Encrypt a table at creation time
CREATE TABLE grades_encrypted (
    grade_id    INT           NOT NULL AUTO_INCREMENT,
    student_id  INT           NOT NULL,
    course_id   INT           NOT NULL,
    points      DECIMAL(5,2),
    max_points  DECIMAL(5,2),
    graded_on   DATE,
    PRIMARY KEY (grade_id)
) ENCRYPTION = 'Y';

-- Encrypt an existing table (online operation)
ALTER TABLE grades ENCRYPTION = 'Y';

-- Verify encryption status
SELECT TABLE_SCHEMA, TABLE_NAME, CREATE_OPTIONS
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'university'
  AND CREATE_OPTIONS LIKE '%ENCRYPTION%';
```

### 1.2 Per-Table vs. General Tablespace Encryption

=== "Per-Table (file-per-table)"

    Each table has its own `.ibd` file. Encryption applies to individual tables:

    ```sql
    -- Enable file-per-table (default in MySQL 8)
    SHOW VARIABLES LIKE 'innodb_file_per_table';
    -- innodb_file_per_table: ON

    -- Encrypt specific sensitive tables
    ALTER TABLE students  ENCRYPTION = 'Y';
    ALTER TABLE grades    ENCRYPTION = 'Y';
    -- Leave courses, departments unencrypted (no PII)

    -- Disable encryption on a table (if needed for performance testing)
    ALTER TABLE courses ENCRYPTION = 'N';
    ```

=== "General Tablespace"

    Multiple tables share one encrypted tablespace file:

    ```sql
    -- Create an encrypted general tablespace
    CREATE TABLESPACE ts_pii
        ADD DATAFILE 'ts_pii.ibd'
        ENCRYPTION = 'Y';

    -- Place tables in the encrypted tablespace
    CREATE TABLE student_pii (
        student_id   INT NOT NULL,
        ssn          VARBINARY(64),    -- encrypted at column level too
        date_of_birth DATE,
        PRIMARY KEY (student_id)
    ) TABLESPACE = ts_pii;

    ALTER TABLE students TABLESPACE = ts_pii;
    ```

=== "Undo and Redo Log Encryption"

    ```ini
    # my.cnf: encrypt transaction logs too
    [mysqld]
    innodb_redo_log_encrypt  = ON   # encrypt redo log (MySQL 8.0.16+)
    innodb_undo_log_encrypt  = ON   # encrypt undo log (MySQL 8.0.16+)
    binlog_encryption        = ON   # encrypt binary log (MySQL 8.0.14+)
    ```

    !!! warning "Redo Log Encryption and Crash Recovery"
        Enabling redo log encryption means MySQL **cannot recover from a crash** if the keyring is unavailable. Ensure keyring files are included in your backup strategy and are available at startup. In production, use a centralized key management service, not `keyring_file`.

### 1.3 Key Management Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      MySQL Server                            │
│                                                              │
│  ┌──────────────────┐        ┌───────────────────────────┐  │
│  │  InnoDB Storage  │        │    Keyring Plugin          │  │
│  │  Engine          │◄──────►│                           │  │
│  │                  │ master │  keyring_file  (community)│  │
│  │  Encrypted .ibd  │  key   │  keyring_okv   (Enterprise)│ │
│  │  files on disk   │        │  keyring_hashicorp         │  │
│  └──────────────────┘        └───────────────┬───────────┘  │
└────────────────────────────────────────────── │ ─────────────┘
                                                │ master key fetch
                                    ┌───────────▼──────────┐
                                    │  External Key Store   │
                                    │  - Local file         │
                                    │  - Oracle Key Vault   │
                                    │  - HashiCorp Vault    │
                                    │  - AWS KMS            │
                                    └──────────────────────┘
```

```sql
-- Rotate the master encryption key (re-encrypts table encryption keys, NOT data)
ALTER INSTANCE ROTATE INNODB MASTER KEY;

-- This is safe and fast — table data is not re-encrypted;
-- only the table encryption key (TEK) wrapping is updated
```

!!! info "Two-Tier Key Architecture"
    InnoDB uses **two-tier encryption**: a **Table Encryption Key (TEK)** encrypts the actual tablespace pages. The TEK itself is encrypted with the **Master Encryption Key (MEK)** stored in the keyring. Rotating the master key only re-wraps the TEKs — the data pages are not touched, making rotation fast even for terabyte-scale tables.

---

## 2. Encryption in Transit (TLS)

### 2.1 TLS Configuration Deep Dive

```bash
# Generate a CA and server certificates (production: use a real PKI)
openssl genrsa 2048 > ca-key.pem
openssl req -new -x509 -nodes -days 3650 -key ca-key.pem -out ca.pem \
    -subj "/CN=Frostburg DB CA/O=Frostburg State University"

openssl req -newkey rsa:2048 -nodes -keyout server-key.pem -out server-req.pem \
    -subj "/CN=db01.frostburg.edu/O=Frostburg State University"
openssl x509 -req -in server-req.pem -CA ca.pem -CAkey ca-key.pem \
    -CAcreateserial -out server-cert.pem -days 730

# Set permissions (MySQL user must read, no other users)
chmod 600 server-key.pem ca-key.pem
chown mysql:mysql server-cert.pem server-key.pem ca.pem
```

```ini
# my.cnf: TLS configuration
[mysqld]
ssl_ca   = /etc/mysql/ssl/ca.pem
ssl_cert = /etc/mysql/ssl/server-cert.pem
ssl_key  = /etc/mysql/ssl/server-key.pem

# Minimum TLS version (TLS 1.2 or 1.3 only)
tls_version = TLSv1.2,TLSv1.3

# Preferred cipher suites (PCI DSS compliant)
ssl_cipher = ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256

# Require TLS for all connections (MySQL 8.0.26+)
require_secure_transport = ON
```

```sql
-- Verify TLS status on a live connection
SHOW STATUS LIKE 'Ssl_%';
-- Ssl_cipher:     ECDHE-RSA-AES256-GCM-SHA384
-- Ssl_version:    TLSv1.3
-- Ssl_verify_mode: 5 (CA + hostname verified)

-- Check if the current connection is TLS-encrypted
SELECT CONNECTION_ID(),
       VARIABLE_VALUE AS tls_version
FROM performance_schema.session_status
WHERE VARIABLE_NAME = 'Ssl_version';
```

### 2.2 TLS Cipher Suite Selection

| Cipher Suite | TLS Version | Notes |
|-------------|-------------|-------|
| `TLS_AES_256_GCM_SHA384` | TLS 1.3 | ✅ Recommended — AEAD, forward secrecy |
| `TLS_CHACHA20_POLY1305_SHA256` | TLS 1.3 | ✅ Good for CPU-constrained environments |
| `ECDHE-RSA-AES256-GCM-SHA384` | TLS 1.2 | ✅ Strong — PFS, AEAD |
| `ECDHE-RSA-AES128-GCM-SHA256` | TLS 1.2 | ✅ Acceptable |
| `DHE-RSA-AES256-SHA256` | TLS 1.2 | ⚠️ No AEAD; acceptable |
| `RC4-SHA` | TLS 1.0/1.1 | ❌ Broken — never use |
| `DES-CBC3-SHA` | TLS 1.0/1.1 | ❌ Broken — never use |

---

## 3. Application-Level Column Encryption

### 3.1 AES_ENCRYPT / AES_DECRYPT

MySQL provides built-in encryption functions for column-level encryption:

```sql
-- Configuration: use AES-256-CBC (set block_encryption_mode)
SET GLOBAL block_encryption_mode = 'aes-256-cbc';

-- Storing encrypted PII
-- IMPORTANT: use a fixed initialization vector OR store IV alongside ciphertext
-- For production, generate a random IV per row and store it

ALTER TABLE students
    ADD COLUMN ssn_encrypted VARBINARY(256),  -- larger than CHAR to hold ciphertext
    ADD COLUMN ssn_iv        VARBINARY(16);   -- store IV with ciphertext

-- Insert with encryption (app should generate the key from a secure KMS, NOT hardcoded)
SET @encryption_key = SHA2('my-secret-key-from-vault', 256);

UPDATE students SET
    ssn_encrypted = AES_ENCRYPT('123-45-6789', @encryption_key),
    ssn = NULL       -- remove plaintext after encryption
WHERE student_id = 1001;

-- Decrypt for authorized queries
SELECT
    student_id,
    AES_DECRYPT(ssn_encrypted, @encryption_key) AS ssn_plaintext
FROM students
WHERE student_id = 1001;
```

!!! danger "Hardcoded Encryption Keys"
    **Never hardcode encryption keys in SQL scripts or application code.** The key in `AES_ENCRYPT('data', 'hardcoded_key')` appears in the MySQL general log, slow query log, and binary log in plaintext. Keys must come from: environment variables, secrets managers (HashiCorp Vault, AWS Secrets Manager), or encrypted configuration files with restricted permissions.

### 3.2 Encrypt in Database vs. Encrypt in Application

| Aspect | Encrypt in DB (`AES_ENCRYPT`) | Encrypt in Application |
|--------|-------------------------------|------------------------|
| **Key exposure** | Key transmitted with every query | Key never leaves app tier |
| **Query flexibility** | Can WHERE/JOIN on encrypted value (if key known) | Encrypted values opaque to DB |
| **Log exposure** | Key may appear in query logs | Key invisible to DB |
| **Search capability** | Only exact match (must decrypt all rows) | Deterministic encryption allows equality search |
| **Performance** | DB CPU for encryption | App CPU for encryption |
| **Recommendation** | Last resort; use app-level instead | **Preferred approach** |

### 3.3 Key Rotation Strategy

```sql
-- Column-level key rotation (app-managed):
-- 1. Add a new column with the new key version
ALTER TABLE students ADD COLUMN ssn_encrypted_v2 VARBINARY(256);

-- 2. Re-encrypt all rows in batches (avoid locking)
SET @old_key = SHA2('old-key-from-vault', 256);
SET @new_key = SHA2('new-key-from-vault', 256);

UPDATE students
SET ssn_encrypted_v2 = AES_ENCRYPT(
        AES_DECRYPT(ssn_encrypted, @old_key),
        @new_key
    )
WHERE student_id BETWEEN 1 AND 1000;   -- batch to avoid long-running transaction

-- 3. Verify batch, then continue...
-- 4. After all rows: swap column names and drop old column
-- 5. Rotate key in secrets manager; invalidate old key
```

---

## 4. MySQL Audit Log Plugin

### 4.1 Installing and Configuring the Audit Log

=== "MySQL Enterprise"

    ```sql
    -- Enterprise Audit Log plugin (pre-bundled)
    INSTALL PLUGIN audit_log SONAME 'audit_log.so';

    -- Or via my.cnf (recommended for persistence):
    -- [mysqld]
    -- plugin-load-add = audit_log.so
    -- audit_log_format = JSON
    -- audit_log_file   = /var/log/mysql/audit.log
    -- audit_log_policy = ALL     (ALL | LOGINS | QUERIES | NONE)
    ```

=== "Community Alternative: MariaDB Audit Plugin"

    ```bash
    # On MySQL Community, use McAfee MySQL Audit Plugin or install MariaDB Audit Plugin
    # For a pure-community solution, build custom audit triggers (Section 4.3)
    
    # Percona Audit Log Plugin (free, bundled with Percona Server)
    # [mysqld]
    # audit_log_handler = FILE
    # audit_log_format  = JSON
    # audit_log_file    = /var/log/mysql/audit.json
    # audit_log_policy  = ALL
    ```

### 4.2 JSON Audit Log Format and Filtering

```sql
-- Configure audit log
SET GLOBAL audit_log_format           = 'JSON';
SET GLOBAL audit_log_policy           = 'ALL';
SET GLOBAL audit_log_rotate_on_size   = 100 * 1024 * 1024;  -- rotate at 100 MB
SET GLOBAL audit_log_flush            = ON;

-- Filter: audit only sensitive database operations
SELECT audit_log_filter_set_filter('log_sensitive',
'{ "filter": {
    "class": [
      { "name": "connection" },
      { "name": "table_access",
        "event": [
          {"name": "read",   "log": { "field": { "name": "table.name",
                                                  "value": "students" }}},
          {"name": "insert", "log": true},
          {"name": "delete", "log": true},
          {"name": "update", "log": true}
        ]
      }
    ]
  }
}');

SELECT audit_log_filter_set_user('%', 'log_sensitive');
```

Sample JSON audit log entry:

```json
{
  "timestamp": "2024-11-15T14:30:22.847293Z",
  "id": 1,
  "class": "table_access",
  "event": "read",
  "connection_id": 284,
  "account": { "user": "app_user", "host": "10.0.1.15" },
  "login": { "user": "app_user", "os": "", "ip": "10.0.1.15", "proxy": "" },
  "table": { "db": "university", "table": "students" },
  "query": {
    "status": 0,
    "sql_command_id": 32,
    "sqltext": "SELECT student_id, first_name, last_name FROM students WHERE dept_id = 5"
  }
}
```

---

## 5. Custom Audit Tables and Triggers

When the MySQL Enterprise Audit plugin is unavailable, custom audit triggers provide a database-native alternative.

### 5.1 Audit Log Schema Design

```sql
-- Audit log table: append-only, no DELETE privilege granted
CREATE TABLE audit_log (
    audit_id       BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    event_time     DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    db_user        VARCHAR(100)    NOT NULL DEFAULT (CURRENT_USER()),
    action_type    ENUM('INSERT','UPDATE','DELETE','DDL') NOT NULL,
    table_name     VARCHAR(64)     NOT NULL,
    record_id      BIGINT,          -- PK of the affected row
    old_values     JSON,            -- before state (UPDATE/DELETE)
    new_values     JSON,            -- after state (INSERT/UPDATE)
    client_ip      VARCHAR(45)      DEFAULT NULL,
    application    VARCHAR(100)     DEFAULT NULL,
    PRIMARY KEY (audit_id),
    INDEX idx_audit_time  (event_time),
    INDEX idx_audit_table (table_name, event_time),
    INDEX idx_audit_user  (db_user, event_time)
) ENGINE = InnoDB;

-- Prevent tampering: revoke DELETE and UPDATE from all users
REVOKE DELETE, UPDATE ON university.audit_log FROM 'app_user'@'%';
REVOKE DELETE, UPDATE ON university.audit_log FROM 'university_dba'@'%';
-- Only a dedicated audit_writer role can INSERT
```

### 5.2 DML Audit Triggers for Students Table

```sql
DELIMITER //

-- Audit INSERT on students
CREATE TRIGGER trg_students_after_insert
AFTER INSERT ON students
FOR EACH ROW
BEGIN
    INSERT INTO audit_log (action_type, table_name, record_id, new_values)
    VALUES (
        'INSERT',
        'students',
        NEW.student_id,
        JSON_OBJECT(
            'student_id',  NEW.student_id,
            'first_name',  NEW.first_name,
            'last_name',   NEW.last_name,
            'email',       NEW.email,
            'dept_id',     NEW.dept_id,
            'gpa',         NEW.gpa,
            'enrolled_on', NEW.enrolled_on,
            'is_active',   NEW.is_active
        )
    );
END //

-- Audit UPDATE on students (captures before AND after state)
CREATE TRIGGER trg_students_after_update
AFTER UPDATE ON students
FOR EACH ROW
BEGIN
    -- Only log if something actually changed (avoid spurious entries)
    IF NOT (
        OLD.first_name <=> NEW.first_name AND
        OLD.last_name  <=> NEW.last_name  AND
        OLD.email      <=> NEW.email      AND
        OLD.gpa        <=> NEW.gpa        AND
        OLD.dept_id    <=> NEW.dept_id    AND
        OLD.is_active  <=> NEW.is_active
    ) THEN
        INSERT INTO audit_log (action_type, table_name, record_id, old_values, new_values)
        VALUES (
            'UPDATE',
            'students',
            NEW.student_id,
            JSON_OBJECT(
                'first_name', OLD.first_name,
                'last_name',  OLD.last_name,
                'email',      OLD.email,
                'gpa',        OLD.gpa,
                'dept_id',    OLD.dept_id,
                'is_active',  OLD.is_active
            ),
            JSON_OBJECT(
                'first_name', NEW.first_name,
                'last_name',  NEW.last_name,
                'email',      NEW.email,
                'gpa',        NEW.gpa,
                'dept_id',    NEW.dept_id,
                'is_active',  NEW.is_active
            )
        );
    END IF;
END //

-- Audit DELETE on students (capture full row before deletion)
CREATE TRIGGER trg_students_before_delete
BEFORE DELETE ON students
FOR EACH ROW
BEGIN
    INSERT INTO audit_log (action_type, table_name, record_id, old_values)
    VALUES (
        'DELETE',
        'students',
        OLD.student_id,
        JSON_OBJECT(
            'student_id',  OLD.student_id,
            'first_name',  OLD.first_name,
            'last_name',   OLD.last_name,
            'email',       OLD.email,
            'ssn_hint',    CONCAT('***-**-', RIGHT(OLD.ssn, 4)),
            'gpa',         OLD.gpa,
            'dept_id',     OLD.dept_id,
            'is_active',   OLD.is_active
        )
    );
END //

DELIMITER ;
```

### 5.3 DDL Audit Trigger

MySQL does not support DDL triggers natively. For DDL auditing, use the **general query log** or a scheduled inspection of `information_schema.TABLES`:

```sql
-- Capture schema changes by comparing snapshots
CREATE TABLE schema_snapshot (
    snapshot_id   BIGINT UNSIGNED AUTO_INCREMENT,
    captured_at   DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    table_schema  VARCHAR(64),
    table_name    VARCHAR(64),
    create_time   DATETIME,
    update_time   DATETIME,
    table_rows    BIGINT,
    PRIMARY KEY (snapshot_id),
    INDEX idx_snap_schema (table_schema, table_name)
);

-- Event to detect DDL changes (runs every 5 minutes)
CREATE EVENT ev_detect_ddl_changes
ON SCHEDULE EVERY 5 MINUTE
DO
    INSERT INTO schema_snapshot (table_schema, table_name, create_time, update_time, table_rows)
    SELECT TABLE_SCHEMA, TABLE_NAME, CREATE_TIME, UPDATE_TIME, TABLE_ROWS
    FROM information_schema.TABLES
    WHERE TABLE_SCHEMA = 'university';
```

!!! tip "PostgreSQL DDL Audit"
    PostgreSQL supports `EVENT TRIGGERS` that fire on DDL statements:
    ```sql
    CREATE OR REPLACE FUNCTION log_ddl_event()
    RETURNS event_trigger LANGUAGE plpgsql AS $$
    BEGIN
        INSERT INTO audit_log (action_type, table_name, db_user)
        VALUES ('DDL', TG_TAG, SESSION_USER);
    END;
    $$;
    CREATE EVENT TRIGGER ddl_audit ON ddl_command_end
        EXECUTE FUNCTION log_ddl_event();
    ```

---

## 6. Compliance Frameworks

### 6.1 GDPR: Database Implications

The **General Data Protection Regulation (EU 2016/679)** imposes strict requirements on systems processing EU residents' personal data.

=== "Right to Erasure (Article 17)"

    The "right to be forgotten" requires that personal data be deleted upon request. This is technically complex in databases:

    ```sql
    -- Option 1: Hard DELETE (may break referential integrity, FK constraints)
    DELETE FROM students WHERE student_id = 1001;

    -- Option 2: Pseudonymization (preferred — preserves referential integrity)
    -- Replace identifying data with a pseudonymous token
    UPDATE students SET
        first_name    = CONCAT('User_', student_id),
        last_name     = CONCAT('Deleted_', student_id),
        email         = CONCAT('deleted_', student_id, '@noreply.invalid'),
        ssn           = NULL,
        date_of_birth = NULL,
        is_active     = 0
    WHERE student_id = 1001;

    -- Option 3: Anonymization stored procedure
    DELIMITER //
    CREATE PROCEDURE anonymize_student(IN p_student_id INT)
    BEGIN
        -- Remove from all identifying tables
        UPDATE students SET
            first_name = 'ANONYMIZED', last_name = 'ANONYMIZED',
            email = CONCAT('anon_', p_student_id, '@deleted.invalid'),
            ssn = NULL, date_of_birth = NULL
        WHERE student_id = p_student_id;

        -- Retain non-identifying academic records (required by FERPA)
        -- Only anonymize PII, not enrollment/grade history
        INSERT INTO audit_log (action_type, table_name, record_id)
        VALUES ('DELETE', 'students_anonymized', p_student_id);
    END //
    DELIMITER ;
    ```

=== "Data Minimization (Article 5)"

    Collect and retain only data necessary for the stated purpose:

    ```sql
    -- Enforce data retention with scheduled cleanup
    CREATE EVENT ev_purge_old_audit_logs
    ON SCHEDULE EVERY 1 DAY
    STARTS CURRENT_TIMESTAMP + INTERVAL 1 DAY
    DO
        DELETE FROM audit_log
        WHERE event_time < NOW() - INTERVAL 7 YEAR  -- 7-year retention for academic records
          AND action_type != 'DELETE';               -- keep deletion records longer

    -- Purge temporary/session data
    CREATE EVENT ev_purge_sessions
    ON SCHEDULE EVERY 1 HOUR
    DO
        DELETE FROM user_sessions WHERE last_activity < NOW() - INTERVAL 30 DAY;
    ```

=== "Breach Notification (Article 33)"

    GDPR requires notification within 72 hours of discovering a breach. Your audit log is the primary evidence:

    ```sql
    -- Query audit log to scope a potential breach
    SELECT
        db_user,
        COUNT(*) AS access_count,
        MIN(event_time) AS first_access,
        MAX(event_time) AS last_access,
        COUNT(DISTINCT record_id) AS distinct_students_accessed
    FROM audit_log
    WHERE table_name = 'students'
      AND action_type = 'READ'         -- or whatever your audit records SELECT as
      AND event_time BETWEEN '2024-11-01' AND '2024-11-15'
    GROUP BY db_user
    HAVING access_count > 1000          -- suspicious volume
    ORDER BY access_count DESC;
    ```

### 6.2 HIPAA Database Requirements

**HIPAA** (Health Insurance Portability and Accountability Act) applies to **Protected Health Information (PHI)**. A university health center's database must comply:

| HIPAA Technical Safeguard | Database Implementation |
|--------------------------|------------------------|
| Access Control (§164.312(a)(1)) | RBAC, least privilege, view-based access |
| Audit Controls (§164.312(b)) | Audit log plugin or triggers; log all PHI access |
| Integrity (§164.312(c)(1)) | Checksums, SSL/TLS in transit, InnoDB ACID |
| Transmission Security (§164.312(e)(1)) | TLS 1.2+, REQUIRE SSL on user accounts |
| Encryption (addressable) | AES-256 at rest (tablespace encryption), AES-256 in transit |
| Unique User Identification | No shared accounts; individual logins for all users |
| Emergency Access (§164.312(a)(2)(ii)) | Break-glass accounts with full audit logging |

```sql
-- HIPAA: every user accessing PHI must be individually identified
-- NO shared accounts like 'clinic_app'@'%' that multiple people use

-- Create individual accounts for each staff member
CREATE USER 'nurse_johnson'@'clinic-ws-01.frostburg.edu'
    IDENTIFIED WITH caching_sha2_password BY '...'
    REQUIRE SSL
    PASSWORD EXPIRE INTERVAL 90 DAY
    FAILED_LOGIN_ATTEMPTS 3
    PASSWORD_LOCK_TIME UNBOUNDED;

-- Audit all access to health records
CREATE TRIGGER trg_health_records_select
-- MySQL doesn't support SELECT triggers; use audit plugin or app-layer audit instead
```

### 6.3 PCI DSS Database Requirements

**PCI DSS** (Payment Card Industry Data Security Standard) applies to systems storing, processing, or transmitting cardholder data:

| PCI DSS Requirement | Database Implementation |
|---------------------|------------------------|
| Req 3.3: Mask PAN on display | View showing only last 4 digits of card number |
| Req 3.4: Render PAN unreadable | AES-256 encryption + key management |
| Req 3.5: Protect keys | Keys in HSM or approved key manager; never in DB |
| Req 7: Restrict access by need | RBAC; payment tables accessible only to payment role |
| Req 8: Unique IDs | No shared accounts; MFA for all non-consumer access |
| Req 10: Track access | Full audit log of all cardholder data access |
| Req 10.5: Protect logs | Append-only logs; log server isolated from DB |

```sql
-- PCI: Store only last 4 digits (truncation — allowed alternative to encryption)
ALTER TABLE payment_records
    ADD COLUMN card_last_four CHAR(4),   -- '4242'
    ADD COLUMN card_brand     VARCHAR(20); -- 'VISA', 'MC'
-- Never store full PAN in database at all; process via payment gateway tokenization

-- If full PAN must be stored (rare): encrypt with AES-256
ALTER TABLE payment_records
    ADD COLUMN pan_encrypted VARBINARY(256),
    ADD COLUMN pan_key_version TINYINT;   -- track which key version was used
```

---

## 7. MySQL Enterprise vs. Community Feature Comparison

| Feature | MySQL Community | MySQL Enterprise | Community Alternative |
|---------|----------------|-----------------|----------------------|
| **Encryption at Rest** | keyring_file (limited) | Oracle Key Vault, KMIP | Percona keyring_vault |
| **Audit Log** | Manual triggers | Enterprise Audit Log | Percona Audit Plugin (free) |
| **Firewall** | None | MySQL Enterprise Firewall | pt-kill (Percona) |
| **Masking** | Manual views | Data Masking & De-id Plugin | Application-level |
| **Thread Pool** | None | Enterprise Thread Pool | Percona Thread Pool |
| **Support** | Community forums | Oracle Premier Support | Percona Support (paid) |
| **Monitor** | Performance Schema | MySQL Enterprise Monitor | PMM (Percona, free) |

!!! note "Percona Distribution for MySQL"
    [Percona Server for MySQL](https://www.percona.com/software/mysql-database/percona-server) is a drop-in replacement that adds many Enterprise-equivalent features (audit, thread pool, keyring integration) at no cost. It is binary-compatible with MySQL and widely used in production.

---

## 8. Database Activity Monitoring (DAM) and Backup Encryption

### 8.1 Database Activity Monitoring Approaches

=== "Agent-Based DAM"

    A lightweight agent installed on the database server captures queries at the OS/kernel level:

    ```
    ┌───────────────────────────┐
    │  MySQL Server              │
    │                           │
    │  ┌──────────────────────┐ │
    │  │  DAM Agent (OS-level)│ │  → streams to centralized DAM platform
    │  │  - Intercepts queries│ │     (Imperva, IBM Guardium, McAfee DAM)
    │  │  - Captures user/IP  │ │
    │  └──────────────────────┘ │
    └───────────────────────────┘
    ```

    **Advantages:** Catches local queries; no network blind spots; tamper-evident (agent separate from DB)  
    **Disadvantages:** Slight performance overhead; agent must be maintained

=== "Network Sniffing DAM"

    Monitors the network tap/SPAN port for database protocol traffic:

    ```bash
    # Conceptual: capture MySQL traffic on port 3306
    tcpdump -i eth0 -nn port 3306 -w /capture/mysql_traffic.pcap

    # DAM appliance decodes MySQL protocol, extracts query text, user, timing
    ```

    **Advantages:** Zero impact on database server; no agent to maintain  
    **Disadvantages:** Misses local socket connections (`localhost`); encrypted traffic (TLS) is opaque without key

=== "Native Logging"

    MySQL's own general log and audit plugin:

    ```sql
    -- General log: every single statement (high overhead — dev only)
    SET GLOBAL general_log = ON;
    SET GLOBAL general_log_file = '/var/log/mysql/general.log';

    -- Audit log: selective, structured JSON — suitable for production
    -- (See Section 4)
    ```

### 8.2 Backup Encryption

```bash
# mysqldump with SSL connection (protects data in transit during backup)
mysqldump \
    --ssl-ca=/etc/mysql/ssl/ca.pem \
    --ssl-cert=/etc/mysql/ssl/client-cert.pem \
    --ssl-key=/etc/mysql/ssl/client-key.pem \
    -h db01.frostburg.edu \
    -u backup_user -p \
    university > /backup/university_$(date +%Y%m%d).sql

# Encrypt the backup file at rest
openssl enc -aes-256-cbc -pbkdf2 -iter 100000 \
    -in /backup/university_20241115.sql \
    -out /backup/university_20241115.sql.enc \
    -pass file:/etc/backup/backup-key.txt

# Percona XtraBackup with built-in encryption (faster for large databases)
xtrabackup --backup \
    --encrypt=AES256 \
    --encrypt-key-file=/etc/xtrabackup/backup.key \
    --target-dir=/backup/xtrabackup/$(date +%Y%m%d)

# Verify encryption
file /backup/university_20241115.sql.enc
# university_20241115.sql.enc: openssl enc'd data with salted password
```

!!! success "Backup Encryption Checklist"
    - [ ] Backup files encrypted with AES-256 at rest
    - [ ] Encryption keys stored **separately** from backup files
    - [ ] Backup transfers over TLS or SSH (never FTP/HTTP)
    - [ ] Offsite backup copies also encrypted
    - [ ] Restore tested at least quarterly (encrypted backup is useless if you can't restore)
    - [ ] Key rotation procedure documented and tested

---

## Key Vocabulary

| Term | Definition |
|------|------------|
| **Encryption at rest** | Encrypting data stored on disk so physical access to storage does not expose data |
| **Tablespace encryption** | InnoDB feature encrypting entire `.ibd` data files at the page level |
| **Table Encryption Key (TEK)** | Per-table AES key that encrypts tablespace pages |
| **Master Encryption Key (MEK)** | Key that encrypts TEKs; stored in keyring plugin |
| **Keyring plugin** | MySQL module managing encryption key storage (file, vault, OKV) |
| **ALTER INSTANCE ROTATE INNODB MASTER KEY** | Command to rotate the MEK without re-encrypting data |
| **TLS (Transport Layer Security)** | Cryptographic protocol securing data in transit |
| **Cipher suite** | Combination of key exchange, authentication, encryption, and MAC algorithms |
| **require_secure_transport** | MySQL variable forcing all connections to use TLS |
| **AES_ENCRYPT / AES_DECRYPT** | MySQL functions for symmetric column-level encryption |
| **Initialization vector (IV)** | Random value ensuring identical plaintexts produce different ciphertexts |
| **Audit log** | Chronological record of database access and modification events |
| **GDPR** | EU regulation governing personal data processing; extraterritorial scope |
| **Right to erasure** | GDPR right for individuals to request deletion of their personal data |
| **Pseudonymization** | Replacing identifying fields with artificial identifiers; preferred over hard deletion |
| **HIPAA** | U.S. law governing Protected Health Information (PHI) security and privacy |
| **PCI DSS** | Payment Card Industry standard for cardholder data security |
| **DAM (Database Activity Monitoring)** | Technology capturing and analyzing database traffic for security events |
| **XtraBackup** | Percona's open-source hot backup tool for MySQL with encryption support |
| **Key rotation** | Replacing encryption keys on a schedule to limit the window of key compromise |

---

## Self-Assessment

!!! question "Self-Assessment"
    1. Your university stores student Social Security Numbers (SSNs) in the `students` table. Describe a **three-layer encryption strategy** combining InnoDB tablespace encryption, column-level `AES_ENCRYPT`, and application-level encryption. Explain which threats each layer defends against and what the tradeoffs are. Which layer is most important, and why?

    2. A GDPR erasure request arrives for a student who graduated 5 years ago. The `students.student_id` appears in `enrollments`, `grades`, and `audit_log` tables, all with foreign key constraints. Explain the technical problem with a simple `DELETE FROM students` and propose a complete pseudonymization strategy including the SQL statements, how it preserves referential integrity, and what data should be retained vs. removed.

    3. You are tasked with achieving PCI DSS compliance for a university payment system. The current database stores full credit card PANs in `payment_records.card_number VARCHAR(20)`. List **five specific PCI DSS requirements** that this violates, then design the schema changes, encryption approach, view-based masking, and RBAC structure needed to achieve compliance.

    4. Compare and contrast the three approaches to database activity monitoring (agent-based, network sniffing, native audit log). For a MySQL 8.0 Community Edition server processing HIPAA-regulated health data, which approach(es) do you recommend and why? Include a discussion of what happens to audit trails when TLS is enabled.

    5. Design a complete audit trail system for the `students` table using custom triggers. Your design must: (a) capture INSERT, UPDATE, and DELETE with before/after state, (b) prevent the audit log from being tampered with by application users, (c) support GDPR erasure requests (auditing the anonymization event itself), and (d) be performant enough to not significantly slow down normal student record updates. Discuss the tradeoffs and failure modes of trigger-based auditing vs. the MySQL Enterprise Audit Log plugin.

---

## Further Reading

- 📖 *MySQL 8.0 Reference Manual* — [Section 15.13: InnoDB Data-at-Rest Encryption](https://dev.mysql.com/doc/refman/8.0/en/innodb-data-encryption.html)
- 📖 *MySQL 8.0 Reference Manual* — [Section 6.4: Security Plugins](https://dev.mysql.com/doc/refman/8.0/en/security-plugins.html)
- 📄 [GDPR for Database Administrators](https://gdpr.eu/what-is-gdpr/) — gdpr.eu
- 📄 [PCI DSS v4.0 Quick Reference Guide](https://www.pcisecuritystandards.org/document_library/)
- 📄 [NIST SP 800-111](https://csrc.nist.gov/publications/detail/sp/800-111/final) — Guide to Storage Encryption Technologies
- 📄 [Percona: MySQL Encryption at Rest](https://www.percona.com/blog/mysql-encryption-at-rest-the-complete-guide/)
- 📄 [HashiCorp Vault MySQL Secrets Engine](https://developer.hashicorp.com/vault/docs/secrets/databases/mysql-rds) — Dynamic credential rotation
- 🎥 *Database Encryption Best Practices* — AWS re:Invent (YouTube)
- 📄 [HHS HIPAA Security Series: Technical Safeguards](https://www.hhs.gov/hipaa/for-professionals/security/guidance/index.html)

---

[← Week 9](week09.md) | [Course Index](index.md) | [Week 11 →](week11.md)
