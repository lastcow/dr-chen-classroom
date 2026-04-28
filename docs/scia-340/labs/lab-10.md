---
title: "Lab 10: Secure Database Design — Schema, Data Classification & Least Exposure"
course: SCIA-340
topic: Secure Database Design and Development
week: "10"
difficulty: ⭐⭐
estimated_time: 60 min
---

# Lab 10: Secure Database Design — Schema, Data Classification & Least Exposure

!!! info "Neon Connection"
    Connect to your Neon Postgres instance for all work in this lab:
    ```bash
    psql $DATABASE_URL
    ```
    Branch naming convention: `lab-10-<your-username>` (e.g., `lab-10-jsmith`)

!!! warning "Branch Requirement"
    Work on branch **lab-10**. All SQL runs on your Neon Postgres instance.
    Create the branch in the Neon console before starting, then update `$DATABASE_URL` to point to it.

---

## Overview

Security cannot be retrofitted onto a poorly designed schema without significant cost and risk. **Secure database design** means making security decisions — data classification, schema separation, access control, input validation, and encryption planning — as part of the initial schema design, not as an afterthought.

This lab operationalizes four principles:

| Principle | Implementation |
|---|---|
| **Data classification** | Lookup table + column comments in `pg_description` |
| **Schema separation** | Dedicated `design` schema isolated from other schemas |
| **Input validation at the DB layer** | `CHECK` constraints independent of application code |
| **Least exposure** | Column comments flag sensitive columns for encryption/RLS review |

By the end of this lab you will:

- Build a formal data classification framework as a queryable table
- Annotate every column of a sensitive table with its classification level
- Query PostgreSQL's system catalog to produce a classification report
- Add `CHECK` constraints that enforce format rules and block raw sensitive data
- Run a security design audit query that identifies RESTRICTED columns not yet encrypted
- Design an `orders` table with referential integrity and inactive-customer protection

---

## Part 1 — Data Classification Framework

### Step 1.1 — Create the classification schema and lookup table

```sql
CREATE SCHEMA IF NOT EXISTS design;

-- Master reference: defines the four classification tiers
CREATE TABLE design.data_classifications (
  level            TEXT     PRIMARY KEY,
  description      TEXT     NOT NULL,
  examples         TEXT     NOT NULL,
  retention_years  INT      NOT NULL,
  encrypt_required BOOLEAN  NOT NULL DEFAULT FALSE
);

INSERT INTO design.data_classifications
  (level, description, examples, retention_years, encrypt_required)
VALUES
  ('PUBLIC',
   'Freely shareable, no restrictions',
   'Product names, public documentation, press releases',
   7, FALSE),

  ('INTERNAL',
   'Internal use only, not for public release',
   'Employee names, org charts, internal procedures',
   7, FALSE),

  ('CONFIDENTIAL',
   'Limited internal access, business sensitive',
   'Salaries, customer email addresses, contract terms',
   7, TRUE),

  ('RESTRICTED',
   'Highest protection level — regulatory or legal obligation',
   'SSN, credit card numbers (PAN), PHI, passwords',
   7, TRUE);

-- Display ordered from least to most sensitive
SELECT *
FROM design.data_classifications
ORDER BY
  CASE level
    WHEN 'PUBLIC'       THEN 1
    WHEN 'INTERNAL'     THEN 2
    WHEN 'CONFIDENTIAL' THEN 3
    WHEN 'RESTRICTED'   THEN 4
  END;
```

📸 **Screenshot checkpoint** — four-tier classification framework with encryption requirements.

---

## Part 2 — Classified Table Design

### Step 2.1 — Design the customer table with inline classification comments

```sql
CREATE TABLE design.customers (
  id             SERIAL          PRIMARY KEY,          -- INTERNAL
  customer_ref   TEXT            NOT NULL UNIQUE,      -- PUBLIC (safe to expose in APIs)
  company_name   TEXT            NOT NULL,             -- INTERNAL
  contact_email  TEXT            NOT NULL,             -- CONFIDENTIAL
  contact_phone  TEXT,                                 -- CONFIDENTIAL
  ssn            TEXT,                                 -- RESTRICTED: must be encrypted
  credit_card    TEXT,                                 -- RESTRICTED: PCI-DSS scope
  credit_limit   NUMERIC(10,2),                        -- CONFIDENTIAL
  -- Metadata
  created_at     TIMESTAMPTZ     DEFAULT NOW(),
  is_active      BOOLEAN         DEFAULT TRUE
);

-- Document the classification of each sensitive column
-- These are stored in pg_description and queryable via the system catalog
COMMENT ON COLUMN design.customers.customer_ref
  IS 'CLASSIFICATION: PUBLIC';
COMMENT ON COLUMN design.customers.company_name
  IS 'CLASSIFICATION: INTERNAL';
COMMENT ON COLUMN design.customers.contact_email
  IS 'CLASSIFICATION: CONFIDENTIAL - email address';
COMMENT ON COLUMN design.customers.contact_phone
  IS 'CLASSIFICATION: CONFIDENTIAL - phone number';
COMMENT ON COLUMN design.customers.ssn
  IS 'CLASSIFICATION: RESTRICTED - PII, encryption required (use pgcrypto)';
COMMENT ON COLUMN design.customers.credit_card
  IS 'CLASSIFICATION: RESTRICTED - PCI-DSS in scope, encryption required';
COMMENT ON COLUMN design.customers.credit_limit
  IS 'CLASSIFICATION: CONFIDENTIAL - financial data';
```

### Step 2.2 — Query classification metadata from the system catalog

The column comments are stored in `pg_description` and are visible to any developer or security auditor who knows where to look.

```sql
SELECT
  c.column_name,
  c.data_type,
  c.is_nullable,
  pgd.description AS classification
FROM information_schema.columns c
JOIN pg_class     pc  ON pc.relname        = c.table_name
JOIN pg_namespace pn  ON pc.relnamespace   = pn.oid
                      AND pn.nspname        = 'design'
LEFT JOIN pg_description pgd
                      ON pgd.objoid        = pc.oid
                      AND pgd.objsubid     = c.ordinal_position
WHERE c.table_schema = 'design'
  AND c.table_name   = 'customers'
ORDER BY c.ordinal_position;
```

📸 **Screenshot checkpoint** — full column list with classification metadata pulled from `pg_description`.

---

## Part 3 — Input Validation at the Database Layer

### Step 3.1 — Add CHECK constraints for format enforcement

These constraints are enforced by the database engine itself — regardless of which application, script, or user runs the INSERT or UPDATE.

```sql
ALTER TABLE design.customers
  -- Email must match RFC 5321 simplified pattern
  ADD CONSTRAINT ck_email_format
    CHECK (contact_email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),

  -- Phone: allow digits, dashes, parentheses, dots, spaces — 7 to 20 characters
  ADD CONSTRAINT ck_phone_format
    CHECK (contact_phone IS NULL
        OR contact_phone ~ '^[0-9\-\+\(\)\.\s]{7,20}$'),

  -- Credit limit cannot be negative
  ADD CONSTRAINT ck_credit_limit_positive
    CHECK (credit_limit IS NULL OR credit_limit >= 0),

  -- Block storage of raw 9-digit SSNs (must be masked/encrypted before insert)
  ADD CONSTRAINT ck_ssn_masked
    CHECK (ssn IS NULL OR ssn !~ '[0-9]{9}');
```

### Step 3.2 — Test constraint enforcement with valid data

```sql
-- Valid insert: proper email, no phone, no SSN
INSERT INTO design.customers (customer_ref, company_name, contact_email)
VALUES ('CUST-001', 'Acme Corp', 'billing@acme.com');

-- Verify the record was inserted
SELECT customer_ref, company_name, contact_email, is_active
FROM design.customers
WHERE customer_ref = 'CUST-001';
```

**Expected:** One row returned cleanly.

📸 **Screenshot checkpoint** — valid insert succeeds.

### Step 3.3 — Test that invalid email is rejected

```sql
-- Invalid email format — should fail ck_email_format
INSERT INTO design.customers (customer_ref, company_name, contact_email)
VALUES ('CUST-002', 'Bad Corp', 'not-an-email');
```

**Expected:**
```
ERROR:  new row for relation "customers" violates check constraint "ck_email_format"
```

📸 **Screenshot checkpoint** — invalid email rejected by CHECK constraint.

### Step 3.4 — Test that raw SSN storage is blocked

```sql
-- Raw 9-digit SSN — should fail ck_ssn_masked
INSERT INTO design.customers (customer_ref, company_name, contact_email, ssn)
VALUES ('CUST-003', 'Risk Corp', 'cfo@risk.com', '123456789');
```

**Expected:**
```
ERROR:  new row for relation "customers" violates check constraint "ck_ssn_masked"
```

📸 **Screenshot checkpoint** — raw SSN rejected, demonstrating the database prevents accidental plaintext storage of regulated data.

---

## Part 4 — Schema Security Assessment

### Step 4.1 — Automated security design audit query

This query reads classification metadata from `pg_description` and applies security rules to flag columns that need attention before the schema goes to production.

```sql
SELECT
  c.column_name,
  c.data_type,
  pgd.description                                     AS classification,
  CASE
    WHEN pgd.description LIKE '%RESTRICTED%'
     AND c.data_type != 'bytea'
      THEN 'RISK: RESTRICTED column not encrypted (expected data_type = bytea)'

    WHEN pgd.description LIKE '%CONFIDENTIAL%'
     AND c.is_nullable = 'YES'
      THEN 'WARNING: CONFIDENTIAL column allows NULL — consider NOT NULL'

    WHEN pgd.description IS NULL
      THEN 'INFO: No classification assigned — review required'

    ELSE 'OK'
  END                                                 AS security_finding
FROM information_schema.columns c
JOIN pg_class     pc  ON pc.relname       = c.table_name
JOIN pg_namespace pn  ON pc.relnamespace  = pn.oid
                      AND pn.nspname       = 'design'
LEFT JOIN pg_description pgd
                      ON pgd.objoid       = pc.oid
                      AND pgd.objsubid    = c.ordinal_position
WHERE c.table_schema = 'design'
  AND c.table_name   = 'customers'
ORDER BY c.ordinal_position;
```

**Expected findings:**

- `ssn` and `credit_card` columns flagged as `RISK` (RESTRICTED but `data_type = text`, not `bytea`)
- `contact_phone` and `credit_limit` flagged as `WARNING` (CONFIDENTIAL and nullable)

📸 **Screenshot checkpoint** — security audit findings showing actionable RISK and WARNING items.

!!! note "From Finding to Fix"
    The RISK items confirm what you learned in Lab 07: `ssn` and `credit_card` should be stored as `BYTEA` after encryption with `pgp_sym_encrypt`. The security audit query provides the *specification* — Lab 07 provides the *implementation*.

---

## Assessment

### Verification SQL

Dr. Chen will run the following query against your Neon connection string. Ensure all expected values are returned before submitting.

```sql
-- VERIFY LAB 10
SELECT
  -- 4 classification tiers defined
  (SELECT COUNT(*)
     FROM design.data_classifications)::INT                          AS classification_levels,

  -- At least 4 columns have CLASSIFICATION: comments
  (SELECT COUNT(*)
     FROM pg_description    pd
     JOIN pg_class          pc ON pd.objoid      = pc.oid
     JOIN pg_namespace      pn ON pc.relnamespace = pn.oid
    WHERE pn.nspname        = 'design'
      AND pc.relname        = 'customers'
      AND pd.description LIKE 'CLASSIFICATION:%')::INT               AS classified_columns,

  -- Email CHECK constraint is active
  (SELECT COUNT(*)
     FROM information_schema.table_constraints
    WHERE table_schema    = 'design'
      AND constraint_name = 'ck_email_format')::INT                  AS email_constraint,

  -- SSN raw-storage blocking constraint is active
  (SELECT COUNT(*)
     FROM information_schema.table_constraints
    WHERE table_schema    = 'design'
      AND constraint_name = 'ck_ssn_masked')::INT                    AS ssn_constraint;
```

**Expected result:** `4 | ≥4 | 1 | 1`

---

### Additional Requirement (20 pts)

Design and implement a **`design.orders`** table that demonstrates referential integrity as a security control and cross-table business-rule enforcement.

**Required DDL:**

```sql
CREATE TABLE design.orders (
  id              SERIAL          PRIMARY KEY,
  order_ref       TEXT            NOT NULL UNIQUE,     -- PUBLIC
  customer_id     INT             NOT NULL,             -- INTERNAL
  order_date      DATE            NOT NULL DEFAULT CURRENT_DATE,  -- INTERNAL
  amount          NUMERIC(12,2)   NOT NULL,             -- CONFIDENTIAL
  status          TEXT            NOT NULL DEFAULT 'pending',     -- INTERNAL
  notes           TEXT,                                -- INTERNAL
  created_at      TIMESTAMPTZ     DEFAULT NOW()
);

-- Classification comments
COMMENT ON COLUMN design.orders.order_ref   IS 'CLASSIFICATION: PUBLIC';
COMMENT ON COLUMN design.orders.customer_id IS 'CLASSIFICATION: INTERNAL';
COMMENT ON COLUMN design.orders.order_date  IS 'CLASSIFICATION: INTERNAL';
COMMENT ON COLUMN design.orders.amount      IS 'CLASSIFICATION: CONFIDENTIAL - order value';
COMMENT ON COLUMN design.orders.status      IS 'CLASSIFICATION: INTERNAL';
COMMENT ON COLUMN design.orders.notes       IS 'CLASSIFICATION: INTERNAL';

-- Referential integrity: orders must reference a real customer
ALTER TABLE design.orders
  ADD CONSTRAINT fk_orders_customer
    FOREIGN KEY (customer_id) REFERENCES design.customers (id)
    ON DELETE RESTRICT;

-- Business rule: order amount must be positive
ALTER TABLE design.orders
  ADD CONSTRAINT ck_order_amount_positive
    CHECK (amount > 0);
```

**Required trigger — prevent orders for inactive customers:**

```sql
-- CHECK constraints cannot reference other tables, so use a trigger
CREATE OR REPLACE FUNCTION design.check_customer_active()
RETURNS TRIGGER
LANGUAGE plpgsql AS $$
BEGIN
  IF NOT (SELECT is_active FROM design.customers WHERE id = NEW.customer_id) THEN
    RAISE EXCEPTION 'Cannot create order: customer % is inactive', NEW.customer_id;
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER trg_orders_active_customer
  BEFORE INSERT OR UPDATE ON design.orders
  FOR EACH ROW
  EXECUTE FUNCTION design.check_customer_active();
```

**Deliverables:**

1. Insert **2 orders** for `CUST-001` (which you created in Step 3.2) and show the SELECT result.
2. Attempt an INSERT with a non-existent `customer_id` (e.g., 99999) and capture the FK violation error.
3. Set `CUST-001` to inactive (`UPDATE design.customers SET is_active = FALSE WHERE customer_ref = 'CUST-001'`) and attempt a new INSERT into `design.orders` — show the trigger error.
4. Verify the `ck_order_amount_positive` constraint by attempting `amount = -50` — show the error.

Submit: complete DDL for the table, trigger function, and trigger; plus output of all four test queries.

---

### Reflection Questions

1. You added `CHECK` constraints that enforce email format, phone format, and SSN masking independently of any application. Why is database-layer validation important even when the application already validates input on the client and server? Describe a **realistic scenario** where application-only validation would fail to prevent bad data from reaching the database. (Hint: think about direct database access, ETL pipelines, and application bugs.)

2. The `ck_ssn_masked` constraint rejects strings containing 9 consecutive digits. Why is preventing raw SSN storage a **security control** rather than just a business rule? Name **two compliance frameworks** that impose specific requirements on SSN protection, and describe one concrete technical requirement each framework imposes (e.g., encryption standard, access logging, retention limit).

3. Column comments documenting data classification are useful documentation but have **zero enforcement power** — they do not prevent anyone from reading or writing classified columns. Design a complete **multi-layer protection approach** for a single `RESTRICTED` column (e.g., `ssn`) that combines: (a) classification metadata for discoverability, (b) encryption at rest using `pgcrypto`, (c) access control using RLS or views to limit who can decrypt, and (d) audit logging via triggers. For each layer, state specifically what threat it mitigates and what gap it still leaves that the next layer addresses.

---

!!! tip "Grading Rubric"
    | Component | Points |
    |---|---|
    | Lab steps (Parts 1–4 with screenshots) | 50 |
    | Verification SQL matches expected output | 30 |
    | Additional Requirement (orders table + trigger) | 20 |
    | **Total** | **100** |
