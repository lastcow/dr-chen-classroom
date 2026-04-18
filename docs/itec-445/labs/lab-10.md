---
title: "Lab 10: Encryption, Auditing & Compliance"
course: ITEC-445
topic: Database Security — Encryption, Auditing & Compliance
week: 10
difficulty: ⭐⭐⭐
estimated_time: 85 minutes
---

# Lab 10: Encryption, Auditing & Compliance

| Field | Details |
|---|---|
| **Course** | ITEC-445 — Advanced Database Management |
| **Week** | 10 |
| **Difficulty** | ⭐⭐⭐ Advanced |
| **Estimated Time** | 85 minutes |
| **Topic** | Database Security — Encryption, Auditing & Compliance |
| **Prerequisites** | Lab 01 schema + Lab 09 roles on Neon branch `lab-10` |
| **Deliverables** | Encrypted columns, audit trigger system, compliance checklist, `verify_lab10()` PASS |

---

## Overview

Encryption and auditing are the technical implementation of data-protection regulations. HIPAA requires audit logs. PCI DSS requires encryption of cardholder data. GDPR requires the ability to delete (erase) a person's data. In this lab you will implement column-level encryption using `pgcrypto`, build a comprehensive audit trail system, and document your compliance posture.

---

!!! warning "Branch Requirement"
    Create branch **`lab-10`** with Lab 01 schema + Lab 09 roles.

---

## Part A — pgcrypto Column Encryption (35 pts)

Neon supports the `pgcrypto` extension for symmetric encryption.

```sql
SET search_path = fsu;

CREATE EXTENSION IF NOT EXISTS pgcrypto;
```

### A1. Add sensitive columns to students table

The Frostburg University database needs to store SSN (for financial aid) and medical notes (for accommodations). These must be encrypted at rest.

```sql
ALTER TABLE students
    ADD COLUMN IF NOT EXISTS ssn_encrypted   BYTEA,
    ADD COLUMN IF NOT EXISTS medical_notes   BYTEA,
    ADD COLUMN IF NOT EXISTS ssn_search_hash TEXT;  -- for lookup without decryption
```

### A2. Encryption functions

```sql
-- Store encryption key as a session-level setting (in production: use vault)
-- For this lab, we use a hardcoded demo key
-- NEVER hardcode keys in production SQL

CREATE OR REPLACE FUNCTION encrypt_ssn(p_ssn TEXT, p_key TEXT DEFAULT 'lab10-demo-key-32chars-padded!!!')
RETURNS BYTEA LANGUAGE sql AS $$
    SELECT pgp_sym_encrypt(p_ssn, p_key)
$$;

CREATE OR REPLACE FUNCTION decrypt_ssn(p_encrypted BYTEA, p_key TEXT DEFAULT 'lab10-demo-key-32chars-padded!!!')
RETURNS TEXT LANGUAGE sql AS $$
    SELECT pgp_sym_decrypt(p_encrypted, p_key)
$$;

-- Deterministic hash for searching (HMAC — allows lookup without decrypting)
CREATE OR REPLACE FUNCTION hash_ssn(p_ssn TEXT, p_key TEXT DEFAULT 'lab10-demo-key-32chars-padded!!!')
RETURNS TEXT LANGUAGE sql AS $$
    SELECT encode(hmac(p_ssn, p_key, 'sha256'), 'hex')
$$;
```

### A3. Store encrypted SSNs for existing students

```sql
-- Update students 1-5 with synthetic SSN data
UPDATE students SET
    ssn_encrypted   = encrypt_ssn('123-45-' || LPAD(student_id::TEXT, 4, '0')),
    ssn_search_hash = hash_ssn('123-45-' || LPAD(student_id::TEXT, 4, '0'))
WHERE student_id <= 5;

-- Verify encryption: should look like binary garbage
SELECT student_id, ssn_encrypted, ssn_search_hash FROM students WHERE student_id <= 3;

-- Decrypt to verify correctness
SELECT student_id,
       decrypt_ssn(ssn_encrypted) AS ssn_decrypted,
       ssn_search_hash
FROM students WHERE student_id <= 3;

-- Lookup by SSN hash (doesn't require decryption — fast and safe)
SELECT student_id, first_name, last_name
FROM students
WHERE ssn_search_hash = hash_ssn('123-45-0001');
```

### A4. Wrong key test

```sql
-- Decryption with wrong key should fail
SELECT decrypt_ssn(ssn_encrypted, 'WRONG-KEY-12345678901234567890!!!')
FROM students WHERE student_id = 1;
-- Should raise: ERROR: Wrong key or corrupt data
```

---

## Part B — Comprehensive Audit Trail System (35 pts)

Build a generic audit trigger that captures all DML changes on sensitive tables.

```sql
-- Central audit log table
CREATE TABLE IF NOT EXISTS audit_log (
    log_id       BIGSERIAL    PRIMARY KEY,
    table_name   TEXT         NOT NULL,
    operation    TEXT         NOT NULL,  -- INSERT, UPDATE, DELETE
    record_id    INT,                    -- PK of affected row
    changed_by   TEXT         NOT NULL DEFAULT current_user,
    changed_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    old_data     JSONB,
    new_data     JSONB,
    session_user TEXT         DEFAULT session_user,
    client_addr  INET         DEFAULT inet_client_addr()
);

CREATE INDEX idx_audit_log_table ON audit_log(table_name, changed_at DESC);
CREATE INDEX idx_audit_log_record ON audit_log(table_name, record_id);

-- Generic audit trigger function
CREATE OR REPLACE FUNCTION trg_generic_audit()
RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER AS $$
DECLARE
    v_record_id INT;
    v_old_data  JSONB := NULL;
    v_new_data  JSONB := NULL;
BEGIN
    -- Get PK value
    IF TG_OP = 'DELETE' THEN
        v_record_id := (row_to_json(OLD) ->> 'student_id')::INT;
        v_old_data  := to_jsonb(OLD);
        -- Mask encrypted columns from audit
        IF v_old_data ? 'ssn_encrypted' THEN
            v_old_data := v_old_data - 'ssn_encrypted' - 'medical_notes'
                       || jsonb_build_object('ssn_encrypted', '[ENCRYPTED]', 'medical_notes', '[ENCRYPTED]');
        END IF;
    ELSIF TG_OP = 'INSERT' THEN
        v_record_id := (row_to_json(NEW) ->> 'student_id')::INT;
        v_new_data  := to_jsonb(NEW);
        IF v_new_data ? 'ssn_encrypted' THEN
            v_new_data := v_new_data - 'ssn_encrypted' - 'medical_notes'
                       || jsonb_build_object('ssn_encrypted', '[ENCRYPTED]', 'medical_notes', '[ENCRYPTED]');
        END IF;
    ELSE  -- UPDATE
        v_record_id := (row_to_json(NEW) ->> 'student_id')::INT;
        v_old_data  := to_jsonb(OLD);
        v_new_data  := to_jsonb(NEW);
        -- Only record changed columns
        SELECT jsonb_object_agg(key, value) INTO v_old_data
        FROM jsonb_each(to_jsonb(OLD))
        WHERE to_jsonb(OLD)->key IS DISTINCT FROM to_jsonb(NEW)->key;

        SELECT jsonb_object_agg(key, value) INTO v_new_data
        FROM jsonb_each(to_jsonb(NEW))
        WHERE to_jsonb(OLD)->key IS DISTINCT FROM to_jsonb(NEW)->key;
    END IF;

    INSERT INTO audit_log (table_name, operation, record_id, old_data, new_data)
    VALUES (TG_TABLE_NAME, TG_OP, v_record_id, v_old_data, v_new_data);

    RETURN COALESCE(NEW, OLD);
END;
$$;

-- Attach to students table
CREATE TRIGGER audit_students
AFTER INSERT OR UPDATE OR DELETE ON fsu.students
FOR EACH ROW EXECUTE FUNCTION fsu.trg_generic_audit();

-- Attach to enrollments table
CREATE TRIGGER audit_enrollments
AFTER INSERT OR UPDATE OR DELETE ON fsu.enrollments
FOR EACH ROW EXECUTE FUNCTION fsu.trg_generic_audit();
```

**Test the audit trail:**
```sql
-- Trigger some changes
UPDATE fsu.students SET gpa = 3.99 WHERE student_id = 1;
UPDATE fsu.students SET gpa = 3.85 WHERE student_id = 1;  -- revert
DELETE FROM fsu.enrollments WHERE student_id = 11 AND course_id = 1;

-- View audit trail
SELECT log_id, table_name, operation, record_id, changed_at,
       old_data, new_data
FROM fsu.audit_log
ORDER BY changed_at DESC
LIMIT 10;

-- Show only changed columns for updates
SELECT log_id, record_id, operation, old_data, new_data
FROM fsu.audit_log
WHERE operation = 'UPDATE' AND table_name = 'students';
```

---

## Part C — GDPR Right to Erasure (15 pts)

GDPR Article 17 requires the ability to delete a user's personal data. Implement a procedure that pseudonymizes a student record (can't truly delete if foreign keys exist):

```sql
CREATE OR REPLACE PROCEDURE gdpr_erasure(p_student_id INT)
LANGUAGE plpgsql AS $$
DECLARE
    v_exists BOOLEAN;
BEGIN
    SELECT EXISTS(SELECT 1 FROM students WHERE student_id = p_student_id) INTO v_exists;
    IF NOT v_exists THEN
        RAISE EXCEPTION 'Student % not found', p_student_id;
    END IF;

    -- Pseudonymize: replace PII with anonymized values
    UPDATE students SET
        first_name      = 'REDACTED',
        last_name       = 'REDACTED-' || p_student_id,
        email           = 'redacted-' || p_student_id || '@deleted.invalid',
        ssn_encrypted   = NULL,
        ssn_search_hash = NULL,
        medical_notes   = NULL,
        gpa             = NULL
    WHERE student_id = p_student_id;

    -- Log the erasure in audit_log
    INSERT INTO audit_log (table_name, operation, record_id, new_data)
    VALUES ('students', 'GDPR_ERASURE', p_student_id,
            jsonb_build_object('reason', 'GDPR Article 17 - Right to Erasure',
                               'timestamp', NOW()));

    RAISE NOTICE 'GDPR erasure completed for student %', p_student_id;
END;
$$;

-- Test
CALL gdpr_erasure(12);
SELECT student_id, first_name, last_name, email FROM students WHERE student_id = 12;
SELECT * FROM audit_log WHERE operation = 'GDPR_ERASURE';
```

---

## Part D — Compliance Checklist (15 pts)

Write `lab10_compliance.md` documenting your compliance posture:

### HIPAA Technical Safeguards (§164.312)

| Control | Requirement | Implementation | Status |
|---------|-------------|----------------|--------|
| §164.312(a)(2)(iv) | Encryption and decryption | `pgcrypto` column encryption on ssn_encrypted | ✅ |
| §164.312(b) | Audit controls | `audit_log` table with triggers on all sensitive tables | ✅ |
| §164.312(c)(1) | Integrity | Write-only audit_log (no DELETE privilege granted) | ✅ |
| §164.312(d) | Person authentication | Role-based access + RLS from Lab 09 | ✅ |
| §164.312(e)(1) | Transmission security | Neon enforces SSL for all connections | ✅ |

### GDPR Article Map

| Article | Requirement | Implementation | Status |
|---------|-------------|----------------|--------|
| Art. 17 | Right to erasure | `gdpr_erasure()` procedure | ✅ |
| Art. 25 | Data protection by design | Encrypted columns, RLS, least privilege | ✅ |
| Art. 32 | Appropriate technical measures | pgcrypto + TLS + audit trail | ✅ |
| Art. 5(1)(e) | Storage limitation | (Gap — no automated retention policy yet) | ❌ |

**For each ❌ gap:** describe what would need to be implemented to close it.

---

## Verification

```sql
SET search_path = fsu;

CREATE OR REPLACE FUNCTION verify_lab10()
RETURNS TABLE(check_id TEXT, description TEXT, result TEXT, points INT) AS $$
BEGIN
    RETURN QUERY SELECT '01', 'pgcrypto extension installed',
        CASE WHEN EXISTS(SELECT 1 FROM pg_extension WHERE extname='pgcrypto')
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '02', 'ssn_encrypted column exists on students',
        CASE WHEN EXISTS(SELECT 1 FROM information_schema.columns
                         WHERE table_schema='fsu' AND table_name='students'
                         AND column_name='ssn_encrypted')
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '03', 'At least 5 students have encrypted SSN',
        CASE WHEN (SELECT COUNT(*) FROM students WHERE ssn_encrypted IS NOT NULL) >= 5
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '04', 'decrypt_ssn function works',
        CASE WHEN decrypt_ssn(encrypt_ssn('123-45-6789')) = '123-45-6789'
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '05', 'SSN hash lookup works',
        CASE WHEN EXISTS(SELECT 1 FROM students
                         WHERE ssn_search_hash = hash_ssn('123-45-0001'))
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '06', 'audit_log table exists',
        CASE WHEN EXISTS(SELECT 1 FROM information_schema.tables
                         WHERE table_schema='fsu' AND table_name='audit_log')
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '07', 'audit_log has rows (triggers fired)',
        CASE WHEN (SELECT COUNT(*) FROM audit_log) > 0
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '08', 'audit_log captures UPDATE operation',
        CASE WHEN EXISTS(SELECT 1 FROM audit_log WHERE operation='UPDATE')
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '09', 'gdpr_erasure procedure exists',
        CASE WHEN EXISTS(SELECT 1 FROM pg_proc WHERE proname='gdpr_erasure')
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '10', 'GDPR erasure logged in audit_log',
        CASE WHEN EXISTS(SELECT 1 FROM audit_log WHERE operation='GDPR_ERASURE')
             THEN 'PASS' ELSE 'FAIL' END, 10;
END;
$$ LANGUAGE plpgsql;

SELECT check_id, description, result,
       CASE WHEN result = 'PASS' THEN points ELSE 0 END AS earned
FROM verify_lab10()
ORDER BY check_id;
```

---

## Additional Requirement (20 pts)

Implement a **data retention policy** to close the GDPR Article 5(1)(e) gap:

Write a procedure `apply_retention_policy(p_years INT DEFAULT 7)` that:
1. Pseudonymizes (via `gdpr_erasure`) all students who graduated more than `p_years` ago (enrolled before `CURRENT_YEAR - p_years`)
2. Archives their enrollment records to an `enrollments_archive` table (same schema as `enrollments`)
3. Deletes the original enrollment rows
4. Logs a `RETENTION_APPLIED` event in `audit_log` with count of affected students

---

## Submission Checklist

- [ ] Neon branch `lab-10` with pgcrypto installed, encrypted columns, audit triggers
- [ ] All test statements run (encrypt, decrypt, wrong-key error screenshots)
- [ ] `gdpr_erasure()` tested — student 12 pseudonymized
- [ ] `lab10_compliance.md` — HIPAA + GDPR compliance table with gap analysis
- [ ] `apply_retention_policy()` procedure (additional requirement)
- [ ] `verify_lab10()` screenshot — all PASS

---

## Grading

| Component | Points |
|-----------|--------|
| Part A — pgcrypto encryption (functions, stored data, hash lookup, wrong key test) | 35 |
| Part B — Audit trigger system (generic function, both tables, changed-columns-only) | 35 |
| Part C — GDPR erasure procedure (tested + audit log entry) | 15 |
| Part D — Compliance checklist (HIPAA + GDPR, gap analysis) | 15 |
| Additional requirement — retention policy procedure | 20 |
| **Total** | **120** |
