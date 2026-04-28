---
title: "Lab 13: Capstone — Harden & Audit a Complete Database"
course: SCIA-340
topic: All Topics — Integration
week: 15
difficulty: "⭐⭐⭐⭐ Expert"
estimated_time: 120 min
---

# Lab 13: Capstone — Harden & Audit a Complete Database

**Course:** SCIA-340 · Secure Databases · Frostburg State University
**Week:** 15 &nbsp;|&nbsp; **Difficulty:** ⭐⭐⭐⭐ Expert &nbsp;|&nbsp; **Time:** 120 min

---

## Overview

This capstone lab integrates every skill from SCIA-340. You will:

1. Load an **intentionally insecure** database schema
2. Systematically **identify** all security vulnerabilities
3. **Harden** the schema using techniques from Labs 1–12
4. Pass a **10-check automated verification function** that Dr. Chen runs directly on your branch
5. Write a complete **Database Security Assessment Report** as a SQL query

Topics covered: authentication, encryption, access control, row-level security, data integrity, auditing, compliance, and cloud security.

---

!!! info "Neon Connection"
    Connect to your **lab-13-capstone** branch endpoint:

    ```bash
    psql "$NEON_LAB13_CONNECTION_STRING"
    ```

    **Prerequisites on this branch:**

    - `pgcrypto` extension (`CREATE EXTENSION IF NOT EXISTS pgcrypto;`)
    - `audit` schema with `audit.event_log` and `audit.capture_change()` (Lab 09)
    - `compliance_matrix` table from Lab 12 (or recreate it here)

!!! warning "Work on branch `lab-13-capstone`"
    **This is your final graded branch.** Create it in the Neon console before running any SQL.
    The `verify_capstone()` function is your final exam.
    **Do not drop or alter `verify_capstone()` after creating it** — Dr. Chen runs it remotely.

---

## Part 1 — The Insecure Baseline

Before hardening a database, a security engineer documents every vulnerability. In this part you load a schema with ten deliberate security flaws and catalog them in a findings table.

### Step 1.1 — Load the Insecure Starter Schema

!!! danger "This schema is intentionally insecure — do not use patterns from this block anywhere else"

```sql
-- Run this ENTIRE block to create the insecure baseline
CREATE SCHEMA IF NOT EXISTS insecure;

-- Table 1: No RLS, no encryption, no classification, no constraints
CREATE TABLE insecure.customers (
  id          SERIAL PRIMARY KEY,
  name        TEXT,          -- CONFIDENTIAL: nullable, no length limit
  email       TEXT,          -- CONFIDENTIAL: no format validation
  ssn         TEXT,          -- RESTRICTED: PII stored in plaintext!
  credit_card TEXT,          -- RESTRICTED: PCI violation — raw PAN!
  salary      NUMERIC,       -- CONFIDENTIAL: no protection
  password    TEXT           -- CRITICAL: passwords in cleartext!
);

-- Table 2: No audit trail, no referential integrity, no amount validation
CREATE TABLE insecure.transactions (
  id          SERIAL PRIMARY KEY,
  customer_id INT,           -- No FK constraint — orphan rows allowed
  amount      NUMERIC,       -- No CHECK — negative amounts allowed
  card_number TEXT           -- PCI violation: raw PAN in transactions
);

-- DANGER: grant everything to all users
GRANT ALL ON insecure.customers    TO PUBLIC;
GRANT ALL ON insecure.transactions TO PUBLIC;

-- Insert sample data exhibiting every vulnerability
INSERT INTO insecure.customers
  (name, email, ssn, credit_card, salary, password)
VALUES
  ('Alice Chen', 'alice@corp.com', '123-45-6789', '4111111111111111', 95000, 'alice123'),
  ('Bob Smith',  'bob@corp.com',   '234-56-7890', '5500000000000004', 72000, 'password');

INSERT INTO insecure.transactions
  (customer_id, amount, card_number)
VALUES
  (1,  149.99, '4111111111111111'),
  (2, -50.00,  '5500000000000004');  -- negative amount: no constraint stops this
```

---

### Step 1.2 — Document All Security Findings

Systematically catalog every issue before touching any remediation. This is how real security assessments begin:

```sql
CREATE TABLE IF NOT EXISTS public.capstone_findings (
  finding_id   SERIAL PRIMARY KEY,
  severity     TEXT NOT NULL
                 CHECK (severity IN ('CRITICAL','HIGH','MEDIUM','LOW')),
  category     TEXT NOT NULL,
  description  TEXT NOT NULL,
  remediation  TEXT NOT NULL,
  status       TEXT DEFAULT 'OPEN'
                 CHECK (status IN ('OPEN','REMEDIATED'))
);

INSERT INTO capstone_findings (severity, category, description, remediation) VALUES
  ('CRITICAL', 'Authentication',
   'Passwords stored in plaintext — full compromise on any SELECT',
   'Hash with pgcrypto digest() or crypt(); never store cleartext credentials'),
  ('CRITICAL', 'PCI-DSS',
   'Full PAN (credit card number) stored in plaintext — immediate PCI violation',
   'Encrypt with pgp_sym_encrypt(), store only last 4 digits plaintext'),
  ('CRITICAL', 'PII Protection',
   'SSN stored in plaintext — HIPAA/state privacy law violation',
   'Encrypt with pgp_sym_encrypt() using a strong symmetric key'),
  ('HIGH', 'Access Control',
   'GRANT ALL ON both tables TO PUBLIC — any DB user can read/write all data',
   'REVOKE ALL FROM PUBLIC; grant minimum required privileges to named roles'),
  ('HIGH', 'Data Integrity',
   'No FK constraint on transactions.customer_id — orphan transaction rows possible',
   'ADD FOREIGN KEY REFERENCES secure.customers(id) ON DELETE RESTRICT'),
  ('HIGH', 'Data Integrity',
   'Negative transaction amounts allowed — fraud vector',
   'ADD CHECK (amount > 0) constraint'),
  ('MEDIUM', 'Auditing',
   'No audit trail on customers or transactions — changes undetectable',
   'Add audit.capture_change() triggers to both tables'),
  ('MEDIUM', 'Data Quality',
   'name and email columns are nullable — data integrity risk',
   'ADD NOT NULL constraints; add CHECK for email format'),
  ('MEDIUM', 'Compliance',
   'No Row Level Security — all users see all rows',
   'Enable RLS; create policies restricting access by role or user context'),
  ('LOW', 'Classification',
   'No data classification metadata on sensitive columns',
   'Add COMMENT ON COLUMN with classification label (RESTRICTED, CONFIDENTIAL)');

-- Summary by severity
SELECT
  severity,
  COUNT(*) AS finding_count
FROM capstone_findings
GROUP BY severity
ORDER BY
  CASE severity
    WHEN 'CRITICAL' THEN 1
    WHEN 'HIGH'     THEN 2
    WHEN 'MEDIUM'   THEN 3
    WHEN 'LOW'      THEN 4
  END;
```

📸 **Screenshot checkpoint — Step 1.2:** Capture the severity summary showing 3 CRITICAL, 3 HIGH, 3 MEDIUM, 1 LOW findings.

---

## Part 2 — Apply Hardening

Work through each finding systematically. Each step maps to one or more entries in `capstone_findings`.

### Step 2.1 — Revoke Dangerous Public Grants (Finding #4)

```sql
REVOKE ALL ON insecure.customers    FROM PUBLIC;
REVOKE ALL ON insecure.transactions FROM PUBLIC;
REVOKE CREATE ON SCHEMA insecure    FROM PUBLIC;

-- Verify: this query should return 0 rows
SELECT grantee, table_name, privilege_type
FROM information_schema.role_table_grants
WHERE table_schema = 'insecure'
  AND grantee = 'PUBLIC';
```

**Expected:** 0 rows returned — all PUBLIC grants are gone.

📸 **Screenshot checkpoint — Step 2.1:** Capture the empty result confirming PUBLIC grants revoked.

---

### Step 2.2 — Encrypt Sensitive Columns and Hash Passwords (Findings #1, 2, 3)

The `insecure.customers` table cannot be safely altered in place without migrating data. Create a new hardened schema:

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SCHEMA IF NOT EXISTS secure;

CREATE TABLE secure.customers (
  id                  SERIAL PRIMARY KEY,
  -- Required, validated fields
  name                TEXT NOT NULL,
  email               TEXT NOT NULL
                        CONSTRAINT ck_email
                        CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
  -- RESTRICTED: SSN encrypted at rest
  ssn_encrypted       BYTEA,
  -- RESTRICTED: full PAN encrypted; only last 4 digits stored plaintext (PCI-DSS)
  credit_card_enc     BYTEA,
  credit_card_last4   CHAR(4),
  -- CONFIDENTIAL: salary encrypted
  salary_encrypted    BYTEA,
  -- CRITICAL: passwords hashed — NEVER stored in cleartext
  password_hash       TEXT NOT NULL,
  created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- Migrate data from insecure baseline with encryption applied
INSERT INTO secure.customers
  (name, email,
   ssn_encrypted,
   credit_card_enc, credit_card_last4,
   salary_encrypted,
   password_hash)
SELECT
  name,
  email,
  pgp_sym_encrypt(ssn,          'CAP_ENC_KEY_2026'),
  pgp_sym_encrypt(credit_card,  'CAP_ENC_KEY_2026'),
  RIGHT(credit_card, 4),
  pgp_sym_encrypt(salary::TEXT, 'CAP_ENC_KEY_2026'),
  encode(digest(password, 'sha256'), 'hex')  -- SHA-256 hash (bcrypt preferred in production)
FROM insecure.customers;

-- Verify: sensitive data is encrypted, passwords are hashed
SELECT
  id,
  name,
  email,
  credit_card_last4,
  length(ssn_encrypted)  AS ssn_enc_bytes,
  length(credit_card_enc) AS cc_enc_bytes,
  LEFT(password_hash, 20) AS pw_hash_preview
FROM secure.customers;
```

📸 **Screenshot checkpoint — Step 2.2:** Capture the query result showing non-null `ssn_enc_bytes`, `cc_enc_bytes`, and a truncated hex `pw_hash_preview` — no plaintext values visible.

---

### Step 2.3 — Add Integrity Constraints (Findings #5, 6, 8)

```sql
CREATE TABLE secure.transactions (
  id          SERIAL PRIMARY KEY,
  customer_id INT           NOT NULL
                REFERENCES secure.customers(id) ON DELETE RESTRICT,
  amount      NUMERIC(10,2) NOT NULL CHECK (amount > 0),
  card_last4  CHAR(4),
  txn_time    TIMESTAMPTZ DEFAULT NOW()
);

-- Verify all constraints are in place
SELECT
  constraint_name,
  constraint_type
FROM information_schema.table_constraints
WHERE table_schema = 'secure'
  AND table_name   = 'transactions'
ORDER BY constraint_type;
```

**Expected constraint types:** CHECK, FOREIGN KEY, NOT NULL (PRIMARY KEY also present).

📸 **Screenshot checkpoint — Step 2.3:** Capture the constraints list showing at minimum `CHECK` and `FOREIGN KEY` rows.

---

### Step 2.4 — Enable Row Level Security (Finding #9)

```sql
ALTER TABLE secure.customers    ENABLE ROW LEVEL SECURITY;
ALTER TABLE secure.transactions ENABLE ROW LEVEL SECURITY;

-- Policy: users see only their own record, DBA role members see all
CREATE POLICY customer_self_service ON secure.customers
  FOR SELECT
  USING (
    name = current_user
    OR pg_has_role(current_user, 'role_dba', 'member')
  );

-- Verify RLS is enabled
SELECT
  tablename,
  rowsecurity
FROM pg_tables
WHERE schemaname = 'secure'
ORDER BY tablename;
```

📸 **Screenshot checkpoint — Step 2.4:** Capture the `pg_tables` result showing `rowsecurity = true` for both `customers` and `transactions`.

---

### Step 2.5 — Add Audit Triggers (Finding #7)

```sql
CREATE TRIGGER capstone_audit_customers
  AFTER INSERT OR UPDATE OR DELETE ON secure.customers
  FOR EACH ROW EXECUTE FUNCTION audit.capture_change();

CREATE TRIGGER capstone_audit_transactions
  AFTER INSERT OR UPDATE OR DELETE ON secure.transactions
  FOR EACH ROW EXECUTE FUNCTION audit.capture_change();

-- Generate audit events to populate the log
INSERT INTO secure.transactions (customer_id, amount, card_last4)
VALUES (1, 89.99, '1111');

UPDATE secure.customers
SET email = 'alice.chen@corp.com'
WHERE name = 'Alice Chen';

-- Verify triggers and log entries
SELECT tgname, tgenabled
FROM pg_trigger
WHERE tgname LIKE 'capstone_%';
```

📸 **Screenshot checkpoint — Step 2.5:** Capture both trigger rows showing `tgenabled = 'O'`.

---

### Step 2.6 — Update Findings to REMEDIATED

```sql
UPDATE capstone_findings
SET status = 'REMEDIATED'
WHERE finding_id IN (1, 2, 3, 4, 5, 6, 7);

-- Findings summary
SELECT
  status,
  COUNT(*) AS count
FROM capstone_findings
GROUP BY status;
```

📸 **Screenshot checkpoint — Step 2.6:** Capture the status summary showing 7 REMEDIATED and 3 OPEN (findings 8–10 are lower severity and documented but not yet remediated by the steps above).

---

## Part 3 — Automated Verification

### Step 3.1 — Create and Run the Verification Function

This function is your **final exam**. Create it, then run it, and ensure all 10 checks pass.

```sql
CREATE OR REPLACE FUNCTION public.verify_capstone()
RETURNS TABLE(
  check_id    TEXT,
  description TEXT,
  result      TEXT,
  points      INT
) AS $$
BEGIN

  -- [1] pgcrypto extension installed
  RETURN QUERY SELECT
    '1'::TEXT,
    'pgcrypto extension installed'::TEXT,
    CASE WHEN EXISTS(
      SELECT 1 FROM pg_extension WHERE extname = 'pgcrypto')
      THEN 'PASS' ELSE 'FAIL'
    END::TEXT,
    5::INT;

  -- [2] PUBLIC privileges revoked from insecure schema tables
  RETURN QUERY SELECT
    '2'::TEXT,
    'PUBLIC privileges revoked from insecure tables'::TEXT,
    CASE WHEN NOT EXISTS(
      SELECT 1 FROM information_schema.role_table_grants
      WHERE table_schema = 'insecure' AND grantee = 'PUBLIC')
      THEN 'PASS' ELSE 'FAIL'
    END::TEXT,
    10::INT;

  -- [3] SSN stored as encrypted BYTEA
  RETURN QUERY SELECT
    '3'::TEXT,
    'SSN stored as encrypted BYTEA (not plaintext TEXT)'::TEXT,
    CASE WHEN EXISTS(
      SELECT 1 FROM information_schema.columns
      WHERE table_schema = 'secure'
        AND table_name   = 'customers'
        AND column_name  = 'ssn_encrypted'
        AND data_type    = 'bytea')
      THEN 'PASS' ELSE 'FAIL'
    END::TEXT,
    10::INT;

  -- [4] Credit card encrypted (bytea) and last4 column exists
  RETURN QUERY SELECT
    '4'::TEXT,
    'Credit card encrypted, last4 plaintext only'::TEXT,
    CASE WHEN EXISTS(
      SELECT 1 FROM information_schema.columns
      WHERE table_schema = 'secure'
        AND table_name   = 'customers'
        AND column_name  = 'credit_card_enc'
        AND data_type    = 'bytea')
      AND EXISTS(
      SELECT 1 FROM information_schema.columns
      WHERE table_schema = 'secure'
        AND table_name   = 'customers'
        AND column_name  = 'credit_card_last4')
      THEN 'PASS' ELSE 'FAIL'
    END::TEXT,
    10::INT;

  -- [5] Passwords hashed — no original plaintext values present
  RETURN QUERY SELECT
    '5'::TEXT,
    'Passwords hashed (no plaintext passwords stored)'::TEXT,
    CASE WHEN NOT EXISTS(
      SELECT 1 FROM secure.customers
      WHERE password_hash IN ('alice123','password','Password1','letmein'))
      THEN 'PASS' ELSE 'FAIL'
    END::TEXT,
    10::INT;

  -- [6] Foreign key constraint on transactions.customer_id
  RETURN QUERY SELECT
    '6'::TEXT,
    'Foreign key constraint on transactions.customer_id'::TEXT,
    CASE WHEN EXISTS(
      SELECT 1 FROM information_schema.table_constraints
      WHERE table_schema     = 'secure'
        AND table_name       = 'transactions'
        AND constraint_type  = 'FOREIGN KEY')
      THEN 'PASS' ELSE 'FAIL'
    END::TEXT,
    5::INT;

  -- [7] CHECK constraint prevents negative amounts
  RETURN QUERY SELECT
    '7'::TEXT,
    'CHECK constraint prevents negative transaction amounts'::TEXT,
    CASE WHEN EXISTS(
      SELECT 1 FROM information_schema.table_constraints
      WHERE table_schema    = 'secure'
        AND table_name      = 'transactions'
        AND constraint_type = 'CHECK')
      THEN 'PASS' ELSE 'FAIL'
    END::TEXT,
    5::INT;

  -- [8] RLS enabled on secure.customers
  RETURN QUERY SELECT
    '8'::TEXT,
    'Row Level Security enabled on secure.customers'::TEXT,
    CASE WHEN EXISTS(
      SELECT 1 FROM pg_tables
      WHERE schemaname = 'secure'
        AND tablename  = 'customers'
        AND rowsecurity = TRUE)
      THEN 'PASS' ELSE 'FAIL'
    END::TEXT,
    10::INT;

  -- [9] Audit trigger exists on secure.customers
  RETURN QUERY SELECT
    '9'::TEXT,
    'Audit trigger on secure.customers'::TEXT,
    CASE WHEN EXISTS(
      SELECT 1 FROM pg_trigger
      WHERE tgname = 'capstone_audit_customers')
      THEN 'PASS' ELSE 'FAIL'
    END::TEXT,
    10::INT;

  -- [10] Audit log has entries from capstone tables
  RETURN QUERY SELECT
    '10'::TEXT,
    'Audit log contains events from capstone tables'::TEXT,
    CASE WHEN EXISTS(
      SELECT 1 FROM audit.event_log
      WHERE table_name = 'customers')
      THEN 'PASS' ELSE 'FAIL'
    END::TEXT,
    5::INT;

END;
$$ LANGUAGE plpgsql;

-- ── Run the verification ──────────────────────────────────────────────────────
SELECT
  check_id,
  description,
  result,
  points,
  CASE WHEN result = 'PASS' THEN points ELSE 0 END AS earned
FROM verify_capstone()
ORDER BY check_id::INT;

-- ── Final score ───────────────────────────────────────────────────────────────
SELECT
  SUM(points)                                                AS total_possible,
  SUM(CASE WHEN result = 'PASS' THEN points ELSE 0 END)      AS earned,
  SUM(CASE WHEN result = 'PASS' THEN 1 ELSE 0 END)::TEXT
    || '/' || COUNT(*)::TEXT                                 AS checks_passed
FROM verify_capstone();
```

**Target:** All 10 checks `PASS` = 80 points earned from automated verification.

📸 **Screenshot checkpoint — Step 3.1:** Capture the full verification result table and the score summary row. All 10 results must show `PASS` before submission.

---

## Assessment

### Automated Verification (Dr. Chen runs this directly)

```bash
# Dr. Chen connects to your branch and runs:
psql "$STUDENT_CONNECTION_STRING" -c \
  "SELECT check_id, description, result,
          CASE WHEN result='PASS' THEN points ELSE 0 END AS earned
   FROM verify_capstone()
   ORDER BY check_id::INT;"
```

**Expected:** All 10 checks `PASS`, total earned = 80 points from this component.

---

### Additional Requirement — Database Security Assessment Report (20 pts)

Write a single SQL query that produces a complete security posture report. Dr. Chen will run this query and read the output as a report. It must use `UNION ALL` and produce exactly three columns: `section`, `item`, `status_or_count`.

The query **must** include all five sections:

```sql
-- SECTION 1: Extension inventory
SELECT
  'Extensions'                           AS section,
  extname                                AS item,
  extversion                             AS status_or_count
FROM pg_extension
WHERE extname NOT IN ('plpgsql')         -- hide built-ins

UNION ALL

-- SECTION 2: Role security audit
SELECT
  'Role Security'                        AS section,
  rolname                                AS item,
  CASE
    WHEN rolsuper    THEN 'SUPERUSER — review required'
    WHEN rolcreatedb THEN 'createdb flag set'
    ELSE 'ok'
  END                                    AS status_or_count
FROM pg_roles
WHERE rolcanlogin = TRUE
  AND rolname NOT LIKE 'pg_%'

UNION ALL

-- SECTION 3: RLS status for all user tables
SELECT
  'RLS Status'                           AS section,
  schemaname || '.' || tablename         AS item,
  CASE WHEN rowsecurity THEN 'RLS ON' ELSE 'RLS OFF' END AS status_or_count
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog','information_schema')

UNION ALL

-- SECTION 4: Audit log summary by table and operation
SELECT
  'Audit Log Summary'                    AS section,
  table_name || ' — ' || operation       AS item,
  COUNT(*)::TEXT                         AS status_or_count
FROM audit.event_log
GROUP BY table_name, operation

UNION ALL

-- SECTION 5: Compliance control implementation rate
SELECT
  'Compliance Matrix'                    AS section,
  framework                              AS item,
  SUM(CASE WHEN status='IMPLEMENTED' THEN 1 ELSE 0 END)::TEXT
    || '/' || COUNT(*)::TEXT
    || ' implemented'                    AS status_or_count
FROM public.compliance_matrix
GROUP BY framework

ORDER BY section, item;
```

Submit the complete query **and** a screenshot of its full output as your final deliverable.

---

### Final Reflection Essay (30 pts)

!!! question "Final Essay — 400–500 words, answer all three questions"

    **1. Security Transformation Walkthrough**

    Walk through the transformation from the insecure baseline to the hardened schema. For each of the five security categories below, identify the specific control you applied and explain **why** it addresses the original vulnerability — not just what it does:

    - **Authentication** (plaintext passwords → ?)
    - **Encryption** (plaintext SSN/PAN → ?)
    - **Access Control** (GRANT ALL to PUBLIC → ?)
    - **Auditing** (no audit trail → ?)
    - **Data Integrity** (no FK, no CHECK → ?)

    ---

    **2. Cloud Amplification**

    Neon's cloud model changes some responsibilities compared to on-premise PostgreSQL. Identify **two specific security controls** from this course that are *more* important in a cloud database environment than in on-premise, and explain why cloud hosting amplifies their necessity. Consider factors such as shared infrastructure, network exposure, credential management, and the serverless compute model.

    ---

    **3. Course Reflection**

    Reflect on what surprised you most about database security in SCIA-340. Then answer:

    - Which **single control** from the course provides the best security-to-implementation-effort ratio — high protection value for relatively low complexity? Justify your choice.
    - Of the ten vulnerabilities in the insecure baseline (Step 1.2), which one would cause the **most organizational damage** if exploited in a real-world system, and why? Consider financial, legal, reputational, and regulatory consequences.

---

!!! tip "Grading Rubric"
    | Component | Points |
    |-----------|--------|
    | Automated verification — `verify_capstone()` (10 checks × points) | 50 |
    | Additional requirement — Security Assessment Report query correct and complete | 20 |
    | Final Reflection Essay — all three questions answered, 400–500 words | 30 |
    | **Total** | **100** |

    > **Note:** The automated verification accounts for 50 of the 100 points. Dr. Chen connects directly to your `lab-13-capstone` branch to run `verify_capstone()`. Ensure the function exists and all 10 checks pass before the submission deadline.
