---
title: "Lab 09: Database Auditing — Triggers, Logs & Compliance"
course: SCIA-340
topic: Database Auditing, Monitoring and Compliance
week: "8"
difficulty: ⭐⭐⭐
estimated_time: 75 min
---

# Lab 09: Database Auditing — Triggers, Logs & Compliance

!!! info "Neon Connection"
    Connect to your Neon Postgres instance for all work in this lab:
    ```bash
    psql $DATABASE_URL
    ```
    Branch naming convention: `lab-09-<your-username>` (e.g., `lab-09-jsmith`)

!!! warning "Branch Requirement"
    Work on branch **lab-09**. All SQL runs on your Neon Postgres instance.
    Create the branch in the Neon console before starting, then update `$DATABASE_URL` to point to it.

!!! note "Prerequisites"
    This lab builds on objects created in **Lab 07** (`secure_data.patients`) and **Lab 08** (`hr.employees`).
    Ensure those schemas and tables exist on your branch, or re-run the setup DDL from those labs before proceeding.

---

## Overview

**"You can't defend what you can't see."**

A database audit trail answers four critical questions for compliance and incident response:

| Question | Answered by |
|---|---|
| Who? | `db_user`, `app_user` columns |
| What? | `operation`, `old_data`, `new_data` |
| When? | `event_time` |
| Which record? | `record_id`, `table_name` |

Students implement an enterprise-grade, trigger-based audit system that captures full before/after snapshots as JSONB, protects the audit log from tampering, and builds compliance queries for anomaly detection.

By the end of this lab you will:

- Create a dedicated `audit` schema with an immutable event log
- Write a reusable PL/pgSQL trigger function that captures INSERT/UPDATE/DELETE with JSONB snapshots
- Attach the trigger to multiple sensitive tables
- Generate and inspect a complete audit trail including changed-column tracking
- Verify that the audit log is tamper-resistant for non-superusers
- Run compliance queries to detect anomalous salary changes

---

## Part 1 — Audit Infrastructure

### Step 1.1 — Create the audit schema and event log table

```sql
CREATE SCHEMA IF NOT EXISTS audit;

CREATE TABLE audit.event_log (
  id           BIGSERIAL    PRIMARY KEY,
  event_time   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  schema_name  TEXT         NOT NULL,
  table_name   TEXT         NOT NULL,
  operation    TEXT         NOT NULL
                            CHECK (operation IN ('INSERT','UPDATE','DELETE','SELECT')),
  db_user      TEXT         NOT NULL DEFAULT current_user,
  app_user     TEXT,                          -- set by application layer via SET LOCAL
  client_addr  INET,                          -- captured from pg_stat_activity if needed
  -- Change data
  record_id    BIGINT,
  old_data     JSONB,                         -- full row before change (UPDATE/DELETE)
  new_data     JSONB,                         -- full row after change  (INSERT/UPDATE)
  changed_cols TEXT[]                         -- column names that actually changed (UPDATE only)
);

-- IMMUTABILITY: revoke all access, then grant only INSERT and SELECT
REVOKE ALL ON audit.event_log FROM PUBLIC;

GRANT INSERT ON audit.event_log TO PUBLIC;   -- triggers can always write audit records
GRANT SELECT ON audit.event_log TO PUBLIC;   -- anyone can review the audit trail

-- No UPDATE or DELETE granted to anyone (superusers bypass this, see Part 3)
```

!!! note "Why BIGSERIAL?"
    Audit logs can grow very large on active production databases. `BIGSERIAL` (8-byte integer) supports up to 9.2 × 10¹⁸ rows before overflow. Regular `SERIAL` (4-byte) would overflow at ~2.1 billion rows.

### Step 1.2 — Create the universal audit trigger function

```sql
CREATE OR REPLACE FUNCTION audit.capture_change()
RETURNS TRIGGER AS $$
DECLARE
  v_old_data JSONB;
  v_new_data JSONB;
  v_changed  TEXT[];
  v_rec_id   BIGINT;
BEGIN
  -- ----------------------------------------------------------------
  -- Capture old and new row images as JSONB
  -- ----------------------------------------------------------------
  IF TG_OP = 'DELETE' THEN
    v_old_data := row_to_json(OLD)::JSONB;
    v_new_data := NULL;
    v_rec_id   := (row_to_json(OLD) ->> 'id')::BIGINT;

  ELSIF TG_OP = 'INSERT' THEN
    v_old_data := NULL;
    v_new_data := row_to_json(NEW)::JSONB;
    v_rec_id   := (row_to_json(NEW) ->> 'id')::BIGINT;

  ELSIF TG_OP = 'UPDATE' THEN
    v_old_data := row_to_json(OLD)::JSONB;
    v_new_data := row_to_json(NEW)::JSONB;
    v_rec_id   := (row_to_json(NEW) ->> 'id')::BIGINT;

    -- Identify which columns actually changed (skip unchanged columns)
    SELECT array_agg(old_j.key)
    INTO   v_changed
    FROM   jsonb_each(v_old_data) old_j
    WHERE  old_j.value IS DISTINCT FROM (v_new_data -> old_j.key);
  END IF;

  -- ----------------------------------------------------------------
  -- Write the audit record
  -- ----------------------------------------------------------------
  INSERT INTO audit.event_log (
    schema_name,    table_name,  operation,
    db_user,        record_id,
    old_data,       new_data,    changed_cols
  ) VALUES (
    TG_TABLE_SCHEMA, TG_TABLE_NAME, TG_OP,
    current_user,    v_rec_id,
    v_old_data,      v_new_data,   v_changed
  );

  -- Return NEW for INSERT/UPDATE, OLD for DELETE (PostgreSQL requirement)
  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

!!! note "SECURITY DEFINER — Why It Matters"
    `SECURITY DEFINER` means this function runs with the **privileges of its owner** (typically a superuser or a dedicated audit owner), not the privileges of the user who triggered the DML.
    Without this, a user with no INSERT privilege on `audit.event_log` could inadvertently (or deliberately) cause the trigger to fail, silently skipping the audit record.
    The `SECURITY DEFINER` guarantee ensures the audit is always written, regardless of who makes the change.

---

## Part 2 — Attach Triggers to Sensitive Tables

### Step 2.1 — Add audit triggers to patients and employees

```sql
-- Audit all DML on the patients PHI table (from Lab 07)
CREATE TRIGGER audit_patients
  AFTER INSERT OR UPDATE OR DELETE
  ON secure_data.patients
  FOR EACH ROW
  EXECUTE FUNCTION audit.capture_change();

-- Audit all DML on the employees HR table (from Lab 08)
CREATE TRIGGER audit_employees
  AFTER INSERT OR UPDATE OR DELETE
  ON hr.employees
  FOR EACH ROW
  EXECUTE FUNCTION audit.capture_change();
```

### Step 2.2 — Generate a complete audit trail

Run the following sequence. Each statement should produce an audit record.

```sql
-- 1. INSERT: adds a test employee
INSERT INTO hr.employees (name, email, department, ssn, salary)
VALUES ('Test User', 'test@corp.com', 'IT', '999-99-9999', 65000);

-- 2. UPDATE: raises salary by $5,000
UPDATE hr.employees
SET    salary = 70000
WHERE  name   = 'Test User';

-- 3. DELETE: removes the test employee
DELETE FROM hr.employees
WHERE  name = 'Test User';

-- 4. Review the complete audit trail
SELECT
  event_time,
  table_name,
  operation,
  db_user,
  record_id,
  old_data  ->> 'salary'  AS old_salary,
  new_data  ->> 'salary'  AS new_salary,
  changed_cols
FROM audit.event_log
WHERE table_name = 'employees'
ORDER BY id;
```

**Expected:** Three rows — INSERT (no `old_data`), UPDATE (`old_salary = 65000`, `new_salary = 70000`, `changed_cols = {salary}`), DELETE (no `new_data`).

📸 **Screenshot checkpoint** — complete audit trail showing all three operations with before/after JSONB values.

---

## Part 3 — Tamper-Resistance Test

### Step 3.1 — Create a non-superuser analyst role

```sql
-- Create a low-privilege analyst role for testing tamper resistance
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'user_analyst') THEN
    CREATE ROLE user_analyst LOGIN PASSWORD 'Analyst_Test#2026' NOINHERIT;
  END IF;
END;
$$;

GRANT USAGE ON SCHEMA audit TO user_analyst;
GRANT SELECT ON audit.event_log TO user_analyst;
-- Note: no UPDATE or DELETE granted
```

### Step 3.2 — Verify the audit log cannot be altered by a non-superuser

```sql
SET ROLE user_analyst;

-- Attempt 1: delete an audit record
DELETE FROM audit.event_log LIMIT 1;

RESET ROLE;
```

**Expected:**
```
ERROR:  permission denied for table event_log
```

```sql
SET ROLE user_analyst;

-- Attempt 2: update an audit record
UPDATE audit.event_log SET db_user = 'nobody' WHERE id = 1;

RESET ROLE;
```

**Expected:**
```
ERROR:  permission denied for table event_log
```

📸 **Screenshot checkpoint** — both tamper attempts rejected, confirming the audit log is append-only for non-superusers.

---

## Part 4 — Compliance Queries

### Step 4.1 — Detect suspicious salary changes (> 20%)

```sql
-- Compliance report: salary increases exceeding 20% (possible fraud indicator)
SELECT
  event_time,
  db_user,
  record_id,
  (old_data ->> 'salary')::NUMERIC                                   AS old_salary,
  (new_data ->> 'salary')::NUMERIC                                   AS new_salary,
  ROUND(
    100.0
    * ABS(  (new_data ->> 'salary')::NUMERIC
          - (old_data ->> 'salary')::NUMERIC)
    / (old_data ->> 'salary')::NUMERIC,
    1
  )                                                                  AS pct_change
FROM audit.event_log
WHERE table_name = 'employees'
  AND operation  = 'UPDATE'
  AND old_data ? 'salary'
  AND ABS(  (new_data ->> 'salary')::NUMERIC
          - (old_data ->> 'salary')::NUMERIC)
      / (old_data ->> 'salary')::NUMERIC > 0.20
ORDER BY pct_change DESC;
```

📸 **Screenshot checkpoint** — compliance query results (the test UPDATE from Step 2.2 should appear here: 65000 → 70000 = 7.7%, which is < 20%; re-run a larger change if you want to see a hit).

!!! tip "Generate a detectable change"
    To see a result in this query, insert and update with a salary jump > 20%:
    ```sql
    INSERT INTO hr.employees (name, email, department, ssn, salary)
    VALUES ('Big Raise', 'raise@corp.com', 'Finance', '111-22-3333', 50000);

    UPDATE hr.employees SET salary = 65000 WHERE name = 'Big Raise';
    -- 50000 → 65000 = 30% change — will appear in the compliance report
    ```

### Step 4.2 — Activity summary report

```sql
SELECT
  table_name,
  operation,
  COUNT(*)                           AS event_count,
  COUNT(DISTINCT db_user)            AS distinct_users,
  MIN(event_time)                    AS first_event,
  MAX(event_time)                    AS last_event
FROM audit.event_log
GROUP BY table_name, operation
ORDER BY table_name, operation;
```

📸 **Screenshot checkpoint** — summary showing all audited tables, operation types, and activity counts.

---

## Assessment

### Verification SQL

Dr. Chen will run the following query against your Neon connection string. Ensure all expected values are returned before submitting.

```sql
-- VERIFY LAB 09
SELECT
  -- Audit table exists in audit schema
  (SELECT COUNT(*)
     FROM pg_tables
    WHERE schemaname = 'audit'
      AND tablename  = 'event_log')::INT                              AS audit_table_exists,

  -- Trigger on hr.employees is active
  (SELECT COUNT(*)
     FROM pg_trigger
    WHERE tgname = 'audit_employees')::INT                           AS trigger_exists,

  -- At least 3 employee audit events exist (INSERT + UPDATE + DELETE)
  (SELECT COUNT(*)
     FROM audit.event_log
    WHERE table_name = 'employees')::INT                             AS employee_events,

  -- All three DML operations are represented
  (SELECT COUNT(DISTINCT operation)
     FROM audit.event_log
    WHERE table_name = 'employees')::INT                             AS distinct_operations,

  -- At least one UPDATE has changed_cols populated
  (SELECT COUNT(*)
     FROM audit.event_log
    WHERE operation    = 'UPDATE'
      AND changed_cols IS NOT NULL)::INT                             AS updates_with_changed_cols;
```

**Expected result:** `1 | 1 | ≥3 | 3 | ≥1`

---

### Additional Requirement (20 pts)

Implement **SELECT auditing** on the `hr.v_hr_admin` view from Lab 08. Standard `AFTER INSERT OR UPDATE OR DELETE` triggers do not fire on `SELECT`, so a different mechanism is required.

**Approach — rewrite the view to call a logging function:**

1. Create a logging function:

    ```sql
    CREATE OR REPLACE FUNCTION audit.log_select(
      p_schema TEXT,
      p_table  TEXT
    )
    RETURNS VOID
    LANGUAGE plpgsql
    SECURITY DEFINER AS $$
    BEGIN
      INSERT INTO audit.event_log
        (schema_name, table_name, operation, db_user)
      VALUES
        (p_schema, p_table, 'SELECT', current_user);
    END;
    $$;
    ```

2. Rewrite `hr.v_hr_admin` to call the logging function on every access:

    ```sql
    CREATE OR REPLACE VIEW hr.v_hr_admin AS
    SELECT
      e.*,
      current_timestamp              AS accessed_at,
      current_user                   AS accessed_by,
      audit.log_select('hr', 'employees')  -- side-effect: writes audit record
    FROM hr.employees e;
    ```

3. Test: query the view, then confirm a `SELECT` row appears in `audit.event_log`.
4. Write a brief explanation (3–5 sentences) of **one fundamental limitation** of SELECT auditing via function side-effects compared to INSERT/UPDATE/DELETE trigger auditing. Consider: what can go wrong with connection pooling, prepared statements, or query caching?

Submit: the function DDL, the updated view DDL, a SELECT from the view, and the audit log query showing the SELECT event — plus the written explanation.

---

### Reflection Questions

1. The audit trigger function uses `SECURITY DEFINER`, meaning it executes with the privileges of the function owner rather than the calling user. Why is this essential for audit integrity? What would happen concretely if the trigger used `SECURITY INVOKER` and the DML was executed by a role with no INSERT privilege on `audit.event_log`? Would the triggering DML succeed or fail?

2. The audit log stores full JSONB snapshots of `old_data` and `new_data` for every change. Estimate the storage cost for a `hr.employees`-style table (~500 bytes per row) with 200,000 UPDATE operations per day. At what point does the audit log become a storage or performance problem? Name **two** specific techniques production audit systems use to manage this cost while preserving compliance requirements.

3. A compromised superuser account can `DELETE FROM audit.event_log` and erase evidence of the compromise. Name **three specific technical controls** that make a database audit log more tamper-resistant, even against superuser access. For each, explain exactly what it prevents and what its limitations are. (Hint: think about log shipping, append-only storage services, and cryptographic chaining.)

---

!!! tip "Grading Rubric"
    | Component | Points |
    |---|---|
    | Lab steps (Parts 1–4 with screenshots) | 50 |
    | Verification SQL matches expected output | 30 |
    | Additional Requirement (SELECT auditing) | 20 |
    | **Total** | **100** |
