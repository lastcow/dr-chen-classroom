---
title: "Lab 01: Neon Setup & Database Security Baseline"
course: SCIA-340
topic: Introduction to Database Security
week: 1
difficulty: ⭐
estimated_time: 60 minutes
---

# Lab 01: Neon Setup & Database Security Baseline

| Field | Details |
|---|---|
| **Course** | SCIA-340 — Database Security |
| **Week** | 1 |
| **Difficulty** | ⭐ Introductory |
| **Estimated Time** | 60 minutes |
| **Topic** | Introduction to Database Security |
| **Prerequisites** | `psql` installed locally, web browser |
| **Deliverables** | Screenshots at each checkpoint + verification script output |

---

## Overview

Get your Neon PostgreSQL account connected, understand what information the database exposes through system catalogs, and establish a secure baseline by creating your working schema. By the end of this lab you will have a running Neon project, have queried the most security-relevant system views, and created an isolated schema that will carry forward into later labs.

---

!!! warning "Branch Requirement"
    All SQL must be executed on your Neon branch. **Name your branch `lab-01` before starting.**
    Working on the wrong branch means your verification results will not be found when Dr. Chen runs the assessment script.

!!! info "Neon Setup — How to Connect"
    1. Log in to [https://neon.tech](https://neon.tech) and open your project.
    2. Copy the connection string from **Dashboard → Connection Details**. It looks like:
       ```
       postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/scia340?sslmode=require
       ```
    3. Export it and connect:
       ```bash
       export DATABASE_URL="postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/scia340?sslmode=require"
       psql $DATABASE_URL
       ```
    4. Once connected, switch to the correct database:
       ```
       \c scia340
       ```
    5. Confirm your prompt shows `scia340=>` before running any lab SQL.

---

## Part 1 — Neon Account and Connection

### Step 1.1 — Create Neon Account and Project

1. Go to [https://neon.tech](https://neon.tech) and create a **free account**.
2. Create a new project named **`scia340-yourname`** (substitute your actual name).
3. Inside the project, create a database named **`scia340`**.
4. Create a branch named **`lab-01`** — use this branch for all work in this lab.
5. Navigate to **Connection Details** and copy your connection string:

```
postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/scia340?sslmode=require
```

!!! tip "Keep Your Connection String Safe"
    Treat your connection string like a password. It contains your credentials. Never commit it to a public repository. Use environment variables (`DATABASE_URL`) as shown above.

---

### Step 1.2 — Connect with psql and Verify Identity

Once connected via `psql $DATABASE_URL`, run the following identity check:

```sql
-- Connect and verify
SELECT current_database(), current_user, version();
```

**Expected output:**

| current_database | current_user | version |
|---|---|---|
| scia340 | your-username | PostgreSQL 16.x ... |

📸 **Screenshot checkpoint:** Capture your terminal showing the successful `psql` connection prompt and the output of the SELECT above.

---

### Step 1.3 — Verify SSL (Neon Enforces It by Default)

Neon requires SSL/TLS on every connection. Confirm it is active for your session:

```sql
SHOW ssl;
```

```sql
SELECT ssl, bits, cipher
FROM pg_stat_ssl
WHERE pid = pg_backend_pid();
```

**Expected output:**

| ssl | bits | cipher |
|---|---|---|
| on | 256 | TLS_AES_256_GCM_SHA384 (TLSv1.3) |

📸 **Screenshot checkpoint:** Capture both query results confirming `ssl = on` and `bits = 256`.

---

## Part 2 — Exploring System Catalogs

System catalogs are internal PostgreSQL tables that describe the database itself — its roles, tables, functions, and configuration. They are readable by authenticated users and are a primary reconnaissance target.

### Step 2.1 — What Roles Exist in Your Database?

```sql
SELECT rolname, rolsuper, rolcanlogin, rolconnlimit
FROM pg_roles
ORDER BY rolname;
```

Observe which roles are superusers (`rolsuper = t`) and which can log in directly (`rolcanlogin = t`). This is exactly what an attacker queries after gaining any foothold.

📸 **Screenshot checkpoint:** Capture the full `pg_roles` output.

---

### Step 2.2 — What Can an Attacker Learn from `information_schema`?

```sql
SELECT table_schema, table_name, table_type
FROM information_schema.tables
WHERE table_schema NOT IN ('pg_catalog','information_schema')
ORDER BY table_schema, table_name;
```

!!! warning "Security Note"
    `information_schema` is **world-readable by default** — any authenticated user can query it. Attackers use it to enumerate every table and view in the database before crafting targeted queries or injection payloads. This reconnaissance step requires zero special privileges.

---

### Step 2.3 — Server Configuration Exposure

```sql
SELECT name, setting, short_desc
FROM pg_settings
WHERE name IN (
  'ssl',
  'password_encryption',
  'log_connections',
  'log_disconnections',
  'log_statement',
  'max_connections'
);
```

Note the values for `log_statement` and `password_encryption` — these directly impact your security posture and will be discussed in the reflection questions.

📸 **Screenshot checkpoint:** Capture the output showing all six security-relevant settings.

---

## Part 3 — Create Working Schema

A schema provides a namespace that isolates your objects from other users. Creating a dedicated schema (rather than using `public`) is a security baseline practice.

### Step 3.1 — Create Isolated Schema

```sql
CREATE SCHEMA IF NOT EXISTS lab01;

COMMENT ON SCHEMA lab01 IS
  'SCIA-340 Lab 01 — Baseline schema. Owner: student.';
```

Verify the schema exists:

```sql
SELECT nspname, pg_get_userbyid(nspowner) AS owner
FROM pg_namespace
WHERE nspname = 'lab01';
```

---

### Step 3.2 — Create a Sample Sensitive Table

```sql
CREATE TABLE lab01.sensitive_records (
  id            SERIAL PRIMARY KEY,
  record_type   TEXT NOT NULL CHECK (record_type IN ('PII','FINANCIAL','MEDICAL','PUBLIC')),
  description   TEXT NOT NULL,
  created_by    TEXT DEFAULT current_user,
  created_at    TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO lab01.sensitive_records (record_type, description) VALUES
  ('PII',       'Customer name and address'),
  ('FINANCIAL', 'Credit card transaction record'),
  ('MEDICAL',   'Patient diagnosis code'),
  ('PUBLIC',    'Product catalog item');

SELECT * FROM lab01.sensitive_records;
```

**Expected output:** Four rows, one per `record_type`, with `created_by` set to your Neon username and `created_at` timestamped to now.

📸 **Screenshot checkpoint:** Capture the `SELECT *` output showing all four rows populated correctly.

---

### Step 3.3 — Check Your Table Is Not Publicly Accessible

```sql
-- List privileges on table
SELECT grantee, privilege_type, is_grantable
FROM information_schema.role_table_grants
WHERE table_schema = 'lab01'
  AND table_name = 'sensitive_records'
ORDER BY grantee;
```

**Expected:** Only your own role (and possibly `neon_superuser`) appears. No `PUBLIC` grant should be present — this means other users cannot query your table.

📸 **Screenshot checkpoint:** Capture the privilege list confirming no public grant exists.

---

## Cleanup / Reset

If you need to restart the lab from scratch, run this block to drop everything created in this lab:

```sql
-- Full reset for Lab 01
DROP SCHEMA IF EXISTS lab01 CASCADE;
```

To re-run from Step 3.1, simply execute the schema creation and table setup blocks again.

---

## Assessment

### Verification Script

Dr. Chen will run the following script directly against your Neon connection string after you submit. All four values must match for full credit.

```sql
-- VERIFY LAB 01
SELECT
  (SELECT COUNT(*) FROM pg_namespace
   WHERE nspname = 'lab01')::INT                                        AS schema_created,

  (SELECT COUNT(*) FROM information_schema.tables
   WHERE table_schema = 'lab01'
     AND table_name   = 'sensitive_records')::INT                       AS table_created,

  (SELECT COUNT(*) FROM lab01.sensitive_records)::INT                   AS rows_inserted,

  (SELECT COUNT(DISTINCT record_type)
   FROM lab01.sensitive_records)::INT                                   AS distinct_types;
```

**Expected results:**

| schema_created | table_created | rows_inserted | distinct_types |
|---|---|---|---|
| 1 | 1 | 4 | 4 |

!!! warning "Verification Requirement"
    The verification script checks for **at least** 4 rows and 4 distinct types. If you completed the additional requirement below (which adds 2 more rows), `rows_inserted` will be 6 — that is fine and will still pass.

---

### Additional Requirement

**Column addition and grouped reporting** *(20 pts)*

Complete the following steps beyond the core lab:

1. Add a column `data_owner TEXT NOT NULL DEFAULT current_user` to `lab01.sensitive_records`:

    ```sql
    ALTER TABLE lab01.sensitive_records
      ADD COLUMN data_owner TEXT NOT NULL DEFAULT current_user;
    ```

2. Insert **two more records** where `data_owner` is explicitly set to `'security_team'`:

    ```sql
    INSERT INTO lab01.sensitive_records (record_type, description, data_owner) VALUES
      ('PII',       'Employee HR file',        'security_team'),
      ('FINANCIAL', 'Quarterly audit summary', 'security_team');
    ```

3. Write a query that counts records grouped by both `record_type` **and** `data_owner`, ordered meaningfully:

    ```sql
    SELECT record_type, data_owner, COUNT(*) AS record_count
    FROM lab01.sensitive_records
    GROUP BY record_type, data_owner
    ORDER BY record_type, data_owner;
    ```

**Submit:** The query text and a screenshot of its output. The result must show `security_team` as a distinct `data_owner` with a count of 2 across two record types.

---

### Reflection Questions

Answer each question in **3–5 sentences** in your lab report.

1. **Log Statement Risk** — `pg_settings` exposed that `log_statement` is set to `'none'`. What risk does this create for a database under attack or audit? What should it be set to in a security-conscious production database, and why is the choice of value (`ddl`, `mod`, or `all`) a trade-off rather than a simple answer?

2. **Information Schema Reconnaissance** — `information_schema.tables` is readable by any authenticated user by default. If an attacker gains a low-privilege database account, what can they immediately learn without accessing any application data? Name **two specific things** they can discover and explain how each piece of information advances an attack.

3. **SSL vs No SSL** — Neon enforces SSL/TLS on all connections. If a developer overrode this with `sslmode=disable`, what could an attacker on the same network segment observe? Why is unencrypted database traffic especially dangerous compared to, say, an unencrypted web page request?

---

!!! tip "Grading Rubric"
    | Component | Points |
    |---|---|
    | Lab steps completed with screenshots at all checkpoints | 50 |
    | Verification script — all 4 values correct | 30 |
    | Additional requirement — column added, rows inserted, grouped query submitted | 20 |
    | **Total** | **100** |
