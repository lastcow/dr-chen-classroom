---
title: "Lab 12: Compliance Controls — PCI-DSS & HIPAA on Neon"
course: SCIA-340
topic: Compliance, Regulations, and Database Security Standards
week: 13
difficulty: "⭐⭐⭐ Advanced"
estimated_time: 90 min
---

# Lab 12: Compliance Controls — PCI-DSS & HIPAA on Neon

**Course:** SCIA-340 · Secure Databases · Frostburg State University
**Week:** 13 &nbsp;|&nbsp; **Difficulty:** ⭐⭐⭐ Advanced &nbsp;|&nbsp; **Time:** 90 min

---

## Overview

Compliance frameworks translate legal and contractual obligations into specific technical controls. In this lab you implement two of the most consequential frameworks in US industry:

- **PCI-DSS** (Payment Card Industry Data Security Standard) — protects cardholder data (CHD)
- **HIPAA** (Health Insurance Portability and Accountability Act) — protects Protected Health Information (PHI)

You will implement **6 distinct technical controls**, document them in a compliance matrix, and produce a verification query that would satisfy an auditor's technical review. This lab builds directly on `audit.capture_change()` from Lab 09 and `pgcrypto` from Lab 07 — both must be in place on your branch.

---

!!! info "Neon Connection"
    Connect to your **lab-12** branch endpoint:

    ```bash
    psql "$NEON_LAB12_CONNECTION_STRING"
    ```

    **Prerequisites on this branch:**

    - `pgcrypto` extension installed (`CREATE EXTENSION IF NOT EXISTS pgcrypto;`)
    - `audit` schema with `audit.event_log` table and `audit.capture_change()` trigger function (from Lab 09)

    If these are not present, create them before continuing. The Lab 09 audit schema setup SQL is reproduced in the appendix of this lab.

!!! warning "Work on branch `lab-12`"
    All work must be performed on the **`lab-12`** branch. Create it in the Neon console before running any SQL. Dr. Chen will connect to this exact branch to run the verification script.

---

## Part 1 — PCI-DSS Technical Controls

PCI-DSS v4.0 applies to any organization that stores, processes, or transmits cardholder data. The four requirements implemented here are among the most technically specific in the standard.

---

### Step 1.1 — PCI-DSS Requirement 3.4: Never Store Full PAN in Plaintext

A Primary Account Number (PAN) — the 16-digit card number — must never be stored in cleartext. The approved approaches are one-way hashing, truncation, index tokens, or strong cryptography. We use `pgcrypto` symmetric encryption combined with truncation:

```sql
CREATE SCHEMA IF NOT EXISTS pci;

-- Ensure pgcrypto is available
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE pci.card_transactions (
  txn_id           SERIAL PRIMARY KEY,
  merchant_ref     TEXT NOT NULL,
  -- PCI-DSS Req 3.4: PAN encrypted at rest, only last 4 digits plaintext
  pan_encrypted    BYTEA NOT NULL,       -- full PAN, AES-encrypted
  pan_last4        CHAR(4) NOT NULL,     -- last 4 digits: explicitly permitted by PCI-DSS
  pan_hash         TEXT  NOT NULL UNIQUE,-- SHA-256 hash for duplicate detection (no reversal)
  card_brand       TEXT  NOT NULL,
  expiry_encrypted BYTEA NOT NULL,       -- expiry also encrypted
  amount           NUMERIC(10,2) NOT NULL,
  txn_time         TIMESTAMPTZ DEFAULT NOW()
);

-- Insert test transactions with encrypted PAN
INSERT INTO pci.card_transactions
  (merchant_ref, pan_encrypted, pan_last4, pan_hash,
   card_brand, expiry_encrypted, amount)
VALUES
  (
    'MERCH-001',
    pgp_sym_encrypt('4111111111111111', 'PCI_ENC_KEY_2026'),
    '1111',
    encode(digest('4111111111111111', 'sha256'), 'hex'),
    'Visa',
    pgp_sym_encrypt('12/2028', 'PCI_ENC_KEY_2026'),
    149.99
  ),
  (
    'MERCH-002',
    pgp_sym_encrypt('5500000000000004', 'PCI_ENC_KEY_2026'),
    '0004',
    encode(digest('5500000000000004', 'sha256'), 'hex'),
    'Mastercard',
    pgp_sym_encrypt('06/2027', 'PCI_ENC_KEY_2026'),
    299.00
  );

-- Verify: only last4 is visible without the encryption key
SELECT txn_id, merchant_ref, pan_last4, card_brand, amount
FROM pci.card_transactions;
```

> **PCI-DSS principle:** Anyone who queries this table without the decryption key sees only `****1111` — fully compliant with Requirement 3.4.

📸 **Screenshot checkpoint — Step 1.1:** Capture the SELECT result showing `pan_last4` visible and no raw PANs exposed.

---

### Step 1.2 — PCI-DSS Requirement 7: Restrict Access by Business Need to Know

Only personnel whose job function requires access to cardholder data should have it. Implement role separation with a view that hides encrypted columns from reporting users:

```sql
-- Only the payment processor role can reach encrypted PANs
CREATE ROLE pci_processor NOLOGIN;
CREATE ROLE pci_reporting NOLOGIN;

GRANT USAGE ON SCHEMA pci TO pci_processor, pci_reporting;

-- Processor role: full access including encrypted columns
GRANT SELECT, INSERT ON pci.card_transactions TO pci_processor;

-- Reporting role: view only — no access to encrypted columns
CREATE OR REPLACE VIEW pci.v_transaction_report AS
SELECT
  txn_id,
  merchant_ref,
  pan_last4,
  card_brand,
  amount,
  txn_time
FROM pci.card_transactions;

GRANT SELECT ON pci.v_transaction_report TO pci_reporting;

-- Verify access matrix
SELECT
  has_table_privilege('pci_processor', 'pci.card_transactions',     'SELECT') AS processor_can_see_encrypted,
  has_table_privilege('pci_reporting', 'pci.card_transactions',     'SELECT') AS reporting_blocked_from_full,
  has_table_privilege('pci_reporting', 'pci.v_transaction_report',  'SELECT') AS reporting_can_see_summary;
```

**Expected:**

| processor_can_see_encrypted | reporting_blocked_from_full | reporting_can_see_summary |
|-|-|-|
| `true` | `false` | `true` |

📸 **Screenshot checkpoint — Step 1.2:** Capture the three-column access matrix result.

---

### Step 1.3 — PCI-DSS Requirement 8: Unique IDs and No Shared Accounts

PCI-DSS Requirement 8 prohibits generic or shared login accounts. Every individual accessing cardholder data must have a unique identifier:

```sql
-- Audit for generic shared account names — any match is a PCI violation
SELECT
  rolname,
  rolcanlogin,
  CASE
    WHEN rolname IN ('shared','generic','app','web','default','admin','test')
    THEN 'VIOLATION: Generic shared account name'
    ELSE 'OK'
  END AS account_name_check
FROM pg_roles
WHERE rolcanlogin = TRUE
  AND rolname NOT LIKE 'pg_%'
ORDER BY rolname;
```

> **If any row shows VIOLATION:** Rename or drop the role before proceeding. PCI Requirement 8.2.1 explicitly prohibits shared credentials.

📸 **Screenshot checkpoint — Step 1.3:** Capture the full role audit list showing all login roles and their `account_name_check` status.

---

### Step 1.4 — PCI-DSS Requirement 10: Audit All Access to Cardholder Data

Every INSERT, UPDATE, and DELETE on the card transactions table must be recorded in an immutable audit log. This requires the `audit.capture_change()` function from Lab 09:

```sql
-- Attach audit trigger to card_transactions
CREATE TRIGGER pci_audit_transactions
  AFTER INSERT OR UPDATE OR DELETE ON pci.card_transactions
  FOR EACH ROW EXECUTE FUNCTION audit.capture_change();

-- Generate an auditable event
UPDATE pci.card_transactions
SET amount = 175.00
WHERE txn_id = 1;

-- Inspect the audit trail
SELECT
  event_time,
  operation,
  db_user,
  record_id,
  old_data->>'amount' AS old_amount,
  new_data->>'amount' AS new_amount
FROM audit.event_log
WHERE table_name = 'card_transactions'
ORDER BY id;
```

> **PCI-DSS Requirement 10.3:** Log entries must include the user, the type of event, the date and time, and the data changed. The `audit.event_log` structure from Lab 09 satisfies all four.

📸 **Screenshot checkpoint — Step 1.4:** Capture the audit log rows showing the UPDATE event with `old_amount = 149.99` and `new_amount = 175.00`.

---

## Part 2 — HIPAA Technical Controls

HIPAA's Security Rule (45 CFR Part 164) specifies Administrative, Physical, and Technical Safeguards. The Technical Safeguards at §164.312 are directly implementable in a database.

---

### Step 2.1 — HIPAA §164.312(a)(1): Unique User Identification

Every workforce member who accesses PHI must use a unique login. Shared credentials are prohibited under HIPAA. Create individual roles for each healthcare persona:

```sql
CREATE SCHEMA IF NOT EXISTS hipaa;

-- Individual login roles — no shared accounts
CREATE ROLE dr_chen       LOGIN PASSWORD 'DrChen_Secure#2026'  NOINHERIT;
CREATE ROLE nurse_johnson LOGIN PASSWORD 'Nurse_Secure#2026'   NOINHERIT;
CREATE ROLE billing_staff LOGIN PASSWORD 'Billing_Secure#2026' NOINHERIT;

-- PHI table: sensitive fields encrypted, non-sensitive plaintext
CREATE TABLE hipaa.patient_records (
  id             SERIAL PRIMARY KEY,
  patient_ref    TEXT NOT NULL UNIQUE,
  -- PHI columns — must be encrypted (HIPAA + minimum necessary)
  name_enc       BYTEA NOT NULL,
  dob_enc        BYTEA NOT NULL,
  diagnosis_enc  BYTEA NOT NULL,
  -- Non-PHI columns — plaintext acceptable for operations
  visit_date     DATE  NOT NULL,
  provider_id    TEXT  NOT NULL
);

GRANT USAGE ON SCHEMA hipaa TO dr_chen, nurse_johnson, billing_staff;
```

> **Why `NOINHERIT`?** It forces explicit `SET ROLE` before accessing any granted group role's permissions — an additional safeguard against accidental privilege use.

---

### Step 2.2 — HIPAA §164.312(a)(2)(i): Minimum Necessary Access

Clinical staff receive the minimum PHI necessary for patient care. Billing staff receive only what they need for claims processing — non-PHI fields only:

```sql
-- Clinical group role: full PHI access for care delivery
CREATE ROLE hipaa_clinical NOLOGIN;
GRANT SELECT, INSERT, UPDATE ON hipaa.patient_records TO hipaa_clinical;
GRANT hipaa_clinical TO dr_chen, nurse_johnson;

-- Billing view: strips all PHI — only visit metadata for claims
CREATE OR REPLACE VIEW hipaa.v_billing_safe AS
SELECT
  id,
  patient_ref,
  visit_date,
  provider_id
FROM hipaa.patient_records;

GRANT SELECT ON hipaa.v_billing_safe TO billing_staff;

-- Verify minimum necessary enforcement
SELECT
  has_table_privilege('billing_staff', 'hipaa.patient_records', 'SELECT')
    AS billing_blocked_phi,
  has_table_privilege('billing_staff', 'hipaa.v_billing_safe', 'SELECT')
    AS billing_sees_nonphi,
  has_table_privilege('dr_chen', 'hipaa.patient_records', 'SELECT')
    AS doctor_sees_phi;
```

**Expected:**

| billing_blocked_phi | billing_sees_nonphi | doctor_sees_phi |
|-|-|-|
| `false` | `true` | `true` |

📸 **Screenshot checkpoint — Step 2.2:** Capture the three-column minimum necessary verification result.

---

### Step 2.3 — HIPAA §164.312(b): Audit Controls

HIPAA requires activity audit controls to record and examine access to PHI. Apply the same `audit.capture_change()` trigger used for PCI:

```sql
-- Audit trigger on the PHI table
CREATE TRIGGER hipaa_audit_patients
  AFTER INSERT OR UPDATE OR DELETE ON hipaa.patient_records
  FOR EACH ROW EXECUTE FUNCTION audit.capture_change();

-- Verify trigger is active
SELECT
  tgname,
  tgenabled
FROM pg_trigger
WHERE tgname = 'hipaa_audit_patients';
```

> **Expected:** One row with `tgname = 'hipaa_audit_patients'` and `tgenabled = 'O'` (origin — fires on all connections).

📸 **Screenshot checkpoint — Step 2.3:** Capture the trigger verification row.

---

## Part 3 — Compliance Matrix

A compliance matrix maps regulatory requirements to specific technical controls and evidence. It is the primary artifact a database auditor will request.

### Step 3.1 — Build and Populate the Compliance Matrix

```sql
CREATE TABLE IF NOT EXISTS public.compliance_matrix (
  req_id       TEXT PRIMARY KEY,
  framework    TEXT NOT NULL,
  requirement  TEXT NOT NULL,
  db_control   TEXT NOT NULL,
  status       TEXT NOT NULL
                 CHECK (status IN ('IMPLEMENTED','PARTIAL','NOT_STARTED')),
  evidence_sql TEXT NOT NULL
);

INSERT INTO compliance_matrix VALUES
  (
    'PCI-3.4', 'PCI-DSS',
    'Do not store PAN in plaintext',
    'pgcrypto column encryption on pan_encrypted (BYTEA)',
    'IMPLEMENTED',
    'SELECT data_type FROM information_schema.columns WHERE column_name=''pan_encrypted'''
  ),
  (
    'PCI-7.1', 'PCI-DSS',
    'Limit access to cardholder data by business need',
    'pci_processor/pci_reporting roles + view separation',
    'IMPLEMENTED',
    'SELECT has_table_privilege(''pci_reporting'',''pci.card_transactions'',''SELECT'')'
  ),
  (
    'PCI-8.2', 'PCI-DSS',
    'Unique IDs for all users accessing CHD',
    'Individual LOGIN roles per user, no shared accounts',
    'IMPLEMENTED',
    'SELECT COUNT(*) FROM pg_roles WHERE rolcanlogin AND rolname NOT LIKE ''pg_%'''
  ),
  (
    'PCI-10.1', 'PCI-DSS',
    'Implement audit trails for all access to cardholder data',
    'audit.capture_change() trigger on pci.card_transactions',
    'IMPLEMENTED',
    'SELECT COUNT(*) FROM pg_trigger WHERE tgname=''pci_audit_transactions'''
  ),
  (
    'HIPAA-164.312a1', 'HIPAA',
    'Unique user identification',
    'Individual login roles: dr_chen, nurse_johnson, billing_staff',
    'IMPLEMENTED',
    'SELECT COUNT(*) FROM pg_roles WHERE rolname IN (''dr_chen'',''nurse_johnson'',''billing_staff'')'
  ),
  (
    'HIPAA-164.312a2', 'HIPAA',
    'Minimum necessary access to PHI',
    'billing_staff restricted to hipaa.v_billing_safe view — no base PHI table access',
    'IMPLEMENTED',
    'SELECT has_table_privilege(''billing_staff'',''hipaa.v_billing_safe'',''SELECT'')'
  )
ON CONFLICT (req_id) DO NOTHING;

-- Compliance summary by framework
SELECT
  framework,
  COUNT(*)                                                AS total,
  SUM(CASE WHEN status = 'IMPLEMENTED' THEN 1 ELSE 0 END) AS implemented,
  ROUND(
    100.0 * SUM(CASE WHEN status = 'IMPLEMENTED' THEN 1 ELSE 0 END) / COUNT(*),
    0
  )                                                       AS pct_complete
FROM compliance_matrix
GROUP BY framework
ORDER BY framework;
```

**Expected summary:**

| framework | total | implemented | pct_complete |
|-----------|-------|-------------|--------------|
| HIPAA | 2 | 2 | 100 |
| PCI-DSS | 4 | 4 | 100 |

📸 **Screenshot checkpoint — Step 3.1:** Capture the compliance summary showing 100% implementation for both frameworks.

---

## Assessment

### Verification Script

Run this block and submit the output. Dr. Chen will run the same script on your `lab-12` branch.

```sql
-- VERIFY LAB 12
SELECT
  -- PAN column is BYTEA (encrypted), not TEXT
  (SELECT data_type
   FROM information_schema.columns
   WHERE table_schema = 'pci'
     AND table_name   = 'card_transactions'
     AND column_name  = 'pan_encrypted')              AS pan_encrypted_type,

  -- PCI audit trigger exists on card_transactions
  (SELECT COUNT(*)
   FROM pg_trigger
   WHERE tgname = 'pci_audit_transactions')::INT      AS pci_trigger,

  -- billing_staff is blocked from the raw PHI table
  has_table_privilege(
    'billing_staff',
    'hipaa.patient_records',
    'SELECT')                                          AS billing_blocked,

  -- All 6 controls marked IMPLEMENTED in compliance matrix
  (SELECT COUNT(*)
   FROM public.compliance_matrix
   WHERE status = 'IMPLEMENTED')::INT                 AS controls_implemented;
```

**Expected results:**

| pan_encrypted_type | pci_trigger | billing_blocked | controls_implemented |
|---|---|---|---|
| `bytea` | `1` | `false` | `6` |

---

### Additional Requirement (20 pts)

**Add GDPR to your compliance matrix** by implementing two Privacy by Design controls under GDPR Article 25.

#### GDPR Control 1 — Article 25: Data Minimization View

Create a view that removes all non-essential PII for an analytics use case:

```sql
CREATE SCHEMA IF NOT EXISTS gdpr;

-- Data minimization: analytics view strips all direct identifiers
CREATE OR REPLACE VIEW gdpr.v_visit_analytics AS
SELECT
  id,
  visit_date,
  provider_id,
  -- No name, no patient_ref, no dob, no diagnosis
  DATE_PART('year', AGE(visit_date)) AS years_since_visit
FROM hipaa.patient_records;
```

#### GDPR Control 2 — Article 17: Right to Erasure

Create an erasure procedure that deletes PHI and issues a verifiable deletion certificate:

```sql
CREATE TABLE IF NOT EXISTS gdpr.erasure_log (
  erasure_id      SERIAL PRIMARY KEY,
  patient_ref     TEXT NOT NULL,
  erasure_time    TIMESTAMPTZ DEFAULT NOW(),
  requesting_user TEXT NOT NULL,
  confirmed       BOOLEAN DEFAULT TRUE
);

CREATE OR REPLACE PROCEDURE gdpr.erase_patient(p_patient_ref TEXT)
LANGUAGE plpgsql AS $$
BEGIN
  -- Delete the patient record (cascades to any FK-linked rows)
  DELETE FROM hipaa.patient_records
  WHERE patient_ref = p_patient_ref;

  -- Insert deletion certificate as required by GDPR Article 17
  INSERT INTO gdpr.erasure_log (patient_ref, erasure_time, requesting_user)
  VALUES (p_patient_ref, NOW(), current_user);

  RAISE NOTICE 'Patient % erased and deletion certificate issued.', p_patient_ref;
END;
$$;

-- Test the erasure procedure (insert a patient first, then erase)
INSERT INTO hipaa.patient_records
  (patient_ref, name_enc, dob_enc, diagnosis_enc, visit_date, provider_id)
VALUES
  ('PAT-TEST-001',
   pgp_sym_encrypt('Test Patient', 'HIPAA_ENC_KEY'),
   pgp_sym_encrypt('1990-01-01',   'HIPAA_ENC_KEY'),
   pgp_sym_encrypt('Test Only',    'HIPAA_ENC_KEY'),
   CURRENT_DATE,
   'PROV-001');

CALL gdpr.erase_patient('PAT-TEST-001');

-- Verify deletion certificate
SELECT * FROM gdpr.erasure_log;
```

#### Add GDPR Controls to the Compliance Matrix

```sql
INSERT INTO compliance_matrix VALUES
  (
    'GDPR-25', 'GDPR',
    'Article 25 — Data minimization: collect only what is necessary',
    'gdpr.v_visit_analytics view removes all direct identifiers for analytics',
    'IMPLEMENTED',
    'SELECT COUNT(*) FROM information_schema.views WHERE table_name=''v_visit_analytics'''
  ),
  (
    'GDPR-17', 'GDPR',
    'Article 17 — Right to erasure (right to be forgotten)',
    'gdpr.erase_patient() procedure deletes PHI and logs deletion certificate',
    'IMPLEMENTED',
    'SELECT COUNT(*) FROM gdpr.erasure_log'
  )
ON CONFLICT (req_id) DO NOTHING;

-- Final compliance summary including GDPR
SELECT framework, COUNT(*) AS total,
  SUM(CASE WHEN status='IMPLEMENTED' THEN 1 ELSE 0 END) AS implemented
FROM compliance_matrix
GROUP BY framework
ORDER BY framework;
```

Submit screenshots of: the analytics view schema, a successful `CALL gdpr.erase_patient(...)`, the erasure log row, and the updated compliance matrix summary showing all three frameworks.

---

### Reflection Questions

!!! question "Reflection (answer in your lab submission)"
    1. **PCI-DSS encryption sufficiency:** PCI-DSS requires that no full PANs be stored in plaintext. You stored them encrypted in the same database as the application. Is database-level symmetric encryption sufficient for PCI-DSS compliance? What additional controls does PCI-DSS require beyond encryption — specifically, think about who holds the encryption key, where it is stored, and how key rotation is managed.

    2. **Procedural vs. technical HIPAA controls:** HIPAA's minimum necessary principle says healthcare workers should only access the PHI required for their specific function. You implemented this with views. A nurse claims she needs to see diagnosis data to do her job, but your schema restricts it. How should this access request be handled procedurally — not just technically? What documentation would a HIPAA auditor require to approve such a change?

    3. **Compliance minimums vs. security maximums:** Compliance frameworks like PCI-DSS and HIPAA set *minimum* security standards, not maximums. A payment processor could be technically PCI-DSS compliant while still having serious security gaps not covered by the standard. Name two security controls you implemented in earlier SCIA-340 labs that are **not** required by PCI-DSS but significantly improve the overall security posture.

---

!!! tip "Grading Rubric"
    | Component | Points |
    |-----------|--------|
    | Lab steps completed (Parts 1–3, all screenshots) | 50 |
    | Verification script — all four values match expected | 30 |
    | Additional requirement (GDPR controls + matrix entries) | 20 |
    | **Total** | **100** |
