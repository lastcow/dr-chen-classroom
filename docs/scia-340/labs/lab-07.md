---
title: "Lab 07: Column-Level Encryption with pgcrypto"
course: SCIA-340
topic: Database Encryption — Data at Rest
week: "6"
difficulty: ⭐⭐⭐
estimated_time: 75 min
---

# Lab 07: Column-Level Encryption with pgcrypto

!!! info "Neon Connection"
    Connect to your Neon Postgres instance for all work in this lab:
    ```bash
    psql $DATABASE_URL
    ```
    Branch naming convention: `lab-07-<your-username>` (e.g., `lab-07-jsmith`)

!!! warning "Branch Requirement"
    Work on branch **lab-07**. All SQL runs on your Neon Postgres instance.
    Create the branch in the Neon console before starting, then update `$DATABASE_URL` to point to it.

---

## Overview

Encryption protects sensitive data when storage media is compromised — a stolen disk, a database backup in an S3 bucket, or a cloud provider employee with physical access all become non-threats if the data at rest is encrypted and the key is stored separately.

PostgreSQL's **pgcrypto** extension provides symmetric and asymmetric cryptographic functions directly in SQL. Students use `pgp_sym_encrypt` / `pgp_sym_decrypt` to encrypt Protected Health Information (PHI) at the column level, demonstrate that the ciphertext is opaque without the key, implement hash-based search tokens to make encrypted data queryable, and document real-world key management trade-offs.

By the end of this lab you will:

- Install and verify the `pgcrypto` extension
- Encrypt PII columns using OpenPGP symmetric encryption
- Prove that stored data is unreadable without the key
- Decrypt with the correct key and observe the failure mode for a wrong key
- Implement a SHA-256 search token to enable lookups on encrypted fields
- Catalogue key management risks and mitigations

---

## Part 1 — Setup pgcrypto

### Step 1.1 — Install the pgcrypto extension

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Confirm installation
SELECT extname, extversion
FROM pg_extension
WHERE extname = 'pgcrypto';
```

**Expected:** One row showing `pgcrypto` and its version (e.g., `1.3`).

📸 **Screenshot checkpoint** — pgcrypto installed and version confirmed.

---

## Part 2 — Column-Level Encryption

### Step 2.1 — Create the encrypted patients table

```sql
CREATE SCHEMA IF NOT EXISTS secure_data;

CREATE TABLE secure_data.patients (
  id                  SERIAL PRIMARY KEY,

  -- Unencrypted: safe to expose, used for joins and display
  patient_ref         TEXT NOT NULL UNIQUE,
  admission_date      DATE NOT NULL,

  -- CONFIDENTIAL: encrypted PHI — stored as opaque binary
  full_name_encrypted BYTEA NOT NULL,
  ssn_encrypted       BYTEA NOT NULL,
  diagnosis_encrypted BYTEA NOT NULL,

  -- Metadata
  created_at          TIMESTAMPTZ DEFAULT NOW()
);
```

### Step 2.2 — Insert encrypted patient records

```sql
-- NOTE: In production, the encryption key MUST come from an external KMS
-- (AWS KMS, HashiCorp Vault, Azure Key Vault). NEVER hardcode keys in SQL.
DO $$
DECLARE
  enc_key TEXT := 'SCIA340_Lab07_EncKey_Change_In_Prod!';
BEGIN
  INSERT INTO secure_data.patients
    (patient_ref, admission_date,
     full_name_encrypted, ssn_encrypted, diagnosis_encrypted)
  VALUES
    ('PAT-001', '2026-01-15',
      pgp_sym_encrypt('John Smith',       enc_key),
      pgp_sym_encrypt('123-45-6789',     enc_key),
      pgp_sym_encrypt('Hypertension',    enc_key)),

    ('PAT-002', '2026-02-20',
      pgp_sym_encrypt('Jane Doe',         enc_key),
      pgp_sym_encrypt('987-65-4321',     enc_key),
      pgp_sym_encrypt('Type 2 Diabetes', enc_key)),

    ('PAT-003', '2026-03-10',
      pgp_sym_encrypt('Robert Johnson',   enc_key),
      pgp_sym_encrypt('555-12-3456',     enc_key),
      pgp_sym_encrypt('Anxiety Disorder', enc_key));
END;
$$;
```

### Step 2.3 — Verify data is unreadable at rest

```sql
-- Raw BYTEA storage — should look like binary garbage, NOT readable SSNs
SELECT
  patient_ref,
  admission_date,
  length(ssn_encrypted)           AS ssn_enc_bytes,
  length(diagnosis_encrypted)     AS diag_enc_bytes,
  encode(ssn_encrypted, 'hex')    AS ssn_hex_sample
FROM secure_data.patients;
```

**Expected:** `ssn_enc_bytes` will be in the range of 60–80 bytes. The hex string is opaque — no `123-45-6789` visible anywhere.

📸 **Screenshot checkpoint** — encrypted columns showing opaque binary data.

### Step 2.4 — Decrypt with the correct key

```sql
SELECT
  patient_ref,
  admission_date,
  pgp_sym_decrypt(full_name_encrypted, 'SCIA340_Lab07_EncKey_Change_In_Prod!') AS full_name,
  pgp_sym_decrypt(ssn_encrypted,       'SCIA340_Lab07_EncKey_Change_In_Prod!') AS ssn,
  pgp_sym_decrypt(diagnosis_encrypted, 'SCIA340_Lab07_EncKey_Change_In_Prod!') AS diagnosis
FROM secure_data.patients;
```

**Expected:** All three patients with plaintext PII visible.

📸 **Screenshot checkpoint** — decrypted PHI returned correctly.

### Step 2.5 — Attempt decryption with the wrong key

```sql
SELECT pgp_sym_decrypt(ssn_encrypted, 'wrongkey')
FROM secure_data.patients
LIMIT 1;
```

**Expected:**
```
ERROR:  Wrong key or corrupt data
```

📸 **Screenshot checkpoint** — wrong-key error confirming data is inaccessible without the correct key.

---

## Part 3 — Hash-Based Search Tokens

Encrypted columns cannot be searched directly — `WHERE ssn_encrypted = '123-45-6789'` will never match because the ciphertext changes with each encryption call. The solution is to store a **deterministic hash of the plaintext** as a separate search token.

### Step 3.1 — Add a search token column and populate it

```sql
-- Add the search token column
ALTER TABLE secure_data.patients
  ADD COLUMN ssn_search_token TEXT;

-- Populate: decrypt plaintext, then hash it
-- In production, hash BEFORE encrypting so the key is never needed just for indexing
UPDATE secure_data.patients
SET ssn_search_token = encode(
  digest(
    pgp_sym_decrypt(ssn_encrypted, 'SCIA340_Lab07_EncKey_Change_In_Prod!'),
    'sha256'
  ),
  'hex'
);

-- Create an index on the token for efficient lookups
CREATE INDEX idx_patients_ssn_token ON secure_data.patients (ssn_search_token);
```

### Step 3.2 — Demonstrate hash-based lookup

```sql
-- Lookup patient by SSN without ever touching the encrypted column
SELECT patient_ref, admission_date
FROM secure_data.patients
WHERE ssn_search_token = encode(digest('123-45-6789', 'sha256'), 'hex');
```

**Expected:** One row — `PAT-001, 2026-01-15`.

📸 **Screenshot checkpoint** — hash lookup returns the correct patient without decrypting all rows.

!!! note "Correct Production Pattern"
    In a real system: **hash the plaintext SSN before sending it to the database**, store only the hash and the ciphertext. The application layer knows the plaintext; the database never sees it unencrypted.
    The pattern shown above (decrypt-then-hash in SQL) is for illustration only — it exposes the plaintext inside the database engine.

---

## Part 4 — Key Management Discussion

### Step 4.1 — Document key management risks

```sql
CREATE TABLE secure_data.key_management_notes (
  note_id    SERIAL PRIMARY KEY,
  risk       TEXT NOT NULL,
  severity   TEXT NOT NULL,
  mitigation TEXT NOT NULL
);

INSERT INTO secure_data.key_management_notes (risk, severity, mitigation) VALUES
  ('Key hardcoded in SQL',
   'CRITICAL',
   'Use KMS (AWS KMS, HashiCorp Vault, Azure Key Vault)'),

  ('Key stored in same DB as data',
   'HIGH',
   'Store key in a separate secret manager, never co-located with data'),

  ('Single encryption key for all records',
   'HIGH',
   'Use per-tenant or per-record keys to limit blast radius'),

  ('No key rotation process',
   'MEDIUM',
   'Implement quarterly key rotation with re-encryption pipeline'),

  ('Key in application config file',
   'HIGH',
   'Use environment variables injected at runtime + secrets manager');

-- Review the risk register
SELECT risk, severity, mitigation
FROM secure_data.key_management_notes
ORDER BY
  CASE severity
    WHEN 'CRITICAL' THEN 1
    WHEN 'HIGH'     THEN 2
    WHEN 'MEDIUM'   THEN 3
    ELSE 4
  END;
```

📸 **Screenshot checkpoint** — key management risk register ordered by severity.

---

## Assessment

### Verification SQL

Dr. Chen will run the following query against your Neon connection string. Ensure all expected values are returned before submitting.

```sql
-- VERIFY LAB 07
SELECT
  -- pgcrypto installed
  (SELECT COUNT(*)
     FROM pg_extension
    WHERE extname = 'pgcrypto')::INT                                    AS pgcrypto_installed,

  -- 3 patient records exist
  (SELECT COUNT(*)
     FROM secure_data.patients)::INT                                    AS patient_count,

  -- ssn column is stored as bytea (encrypted)
  (SELECT data_type
     FROM information_schema.columns
    WHERE table_schema = 'secure_data'
      AND table_name   = 'patients'
      AND column_name  = 'ssn_encrypted')                               AS ssn_col_type,

  -- Decryption returns correct plaintext
  (SELECT pgp_sym_decrypt(
            ssn_encrypted,
            'SCIA340_Lab07_EncKey_Change_In_Prod!')
     FROM secure_data.patients
    WHERE patient_ref = 'PAT-001')                                      AS pat001_ssn,

  -- Hash-based lookup returns exactly 1 row
  (SELECT COUNT(*)
     FROM secure_data.patients
    WHERE ssn_search_token = encode(digest('123-45-6789', 'sha256'), 'hex'))::INT
                                                                        AS hash_lookup_works;
```

**Expected result:** `1 | 3 | bytea | 123-45-6789 | 1`

---

### Additional Requirement (20 pts)

Design and implement a **`secure_data.credit_cards`** table that demonstrates PCI-DSS-aligned storage patterns.

**Required schema:**

```sql
CREATE TABLE secure_data.credit_cards (
  id               SERIAL PRIMARY KEY,
  cardholder_name  TEXT  NOT NULL,
  pan_encrypted    BYTEA NOT NULL,   -- full 16-digit PAN, encrypted
  pan_last4        TEXT  NOT NULL,   -- last 4 digits stored plaintext (PCI-DSS allows this)
  expiry_encrypted BYTEA NOT NULL,   -- MM/YY encrypted
  card_hash        TEXT  NOT NULL UNIQUE  -- SHA-256 of full PAN for duplicate detection
);
```

**Deliverables:**

1. Insert **two card records** using `pgp_sym_encrypt`. Use a key of your choice (document it).
2. Query to verify `pan_last4` matches the last four digits of the decrypted PAN.
3. Attempt to insert a **duplicate PAN** (same card number, different cardholder name) and show that the `UNIQUE` constraint on `card_hash` rejects it.
4. A query that finds a card by PAN without full decryption (hash lookup).

Submit: full DDL, INSERT statements, and the output of all three verification queries with a brief explanation of each result.

---

### Reflection Questions

1. You stored the encryption key as a string literal in your SQL. Why is this a critical security failure in production? Name **three** better approaches for managing encryption keys in a cloud database environment, and briefly explain the protection each one provides that hardcoding does not.

2. Encrypted data is not directly searchable — `WHERE ssn_encrypted = '123-45-6789'` will never work. You solved this with a SHA-256 hash token. What is the **security trade-off** of storing a hash of sensitive data alongside its ciphertext? Specifically: what attack does the hash enable that full encryption (ciphertext only) would prevent? Under what conditions does that attack become practical?

3. **TDE** (Transparent Data Encryption) encrypts an entire database at the storage layer automatically and requires no application changes. **Column-level encryption** with pgcrypto requires explicit `encrypt/decrypt` calls in SQL or application code. Under what threat model is TDE sufficient on its own? When is column-level encryption necessary in addition to TDE? Describe a realistic scenario requiring both layers simultaneously.

---

!!! tip "Grading Rubric"
    | Component | Points |
    |---|---|
    | Lab steps (Parts 1–4 with screenshots) | 50 |
    | Verification SQL matches expected output | 30 |
    | Additional Requirement (credit_cards table) | 20 |
    | **Total** | **100** |
