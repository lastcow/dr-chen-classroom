---
title: "Lab 08: Security Definer Views — Controlled Data Exposure"
course: SCIA-340
topic: Network Security / Secure Design
week: "7"
difficulty: ⭐⭐
estimated_time: 60 min
---

# Lab 08: Security Definer Views — Controlled Data Exposure

!!! info "Neon Connection"
    Connect to your Neon Postgres instance for all work in this lab:
    ```bash
    psql $DATABASE_URL
    ```
    Branch naming convention: `lab-08-<your-username>` (e.g., `lab-08-jsmith`)

!!! warning "Branch Requirement"
    Work on branch **lab-08**. All SQL runs on your Neon Postgres instance.
    Create the branch in the Neon console before starting, then update `$DATABASE_URL` to point to it.

---

## Overview

A **view** is one of the most powerful and underused access-control tools in PostgreSQL. By granting users access to carefully designed views and revoking direct table access, you expose exactly the data each role needs — no more, no less.

The **`security_barrier`** view option closes a subtle but real vulnerability: without it, a crafty attacker can craft a `WHERE` clause that causes PostgreSQL's query planner to evaluate their filter *before* the view's own filter, potentially leaking row data that should be hidden.

In this lab you implement a four-tier HR data exposure model — public directory, manager view, payroll view, and HR admin view — and confirm that direct table access is completely blocked for non-privileged roles.

By the end of this lab you will:

- Design a mixed-sensitivity table and immediately revoke direct access
- Create four views with progressively wider data exposure
- Apply `security_barrier = TRUE` to prevent optimizer-based data leaks
- Grant view access per role and verify that base-table access is denied
- Understand the limitations of view-based auditing vs trigger-based auditing

---

## Part 1 — Source Data with Mixed Sensitivity

### Step 1.1 — Create the HR schema and employee table

```sql
CREATE SCHEMA IF NOT EXISTS hr;

CREATE TABLE hr.employees (
  id                 SERIAL PRIMARY KEY,
  name               TEXT NOT NULL,
  email              TEXT NOT NULL,
  department         TEXT NOT NULL,

  -- CONFIDENTIAL fields
  ssn                TEXT NOT NULL,
  salary             NUMERIC(10,2) NOT NULL,

  -- RESTRICTED fields
  bank_account       TEXT,
  performance_rating INT CHECK (performance_rating BETWEEN 1 AND 5)
);

INSERT INTO hr.employees
  (name, email, department, ssn, salary, bank_account, performance_rating)
VALUES
  ('Alice Chen',  'alice@corp.com',  'Engineering', '123-45-6789', 95000.00,  'ACCT-001', 5),
  ('Bob Smith',   'bob@corp.com',    'Marketing',   '234-56-7890', 72000.00,  'ACCT-002', 3),
  ('Carol Davis', 'carol@corp.com',  'Finance',     '345-67-8901', 115000.00, 'ACCT-003', 4),
  ('Dave Wilson', 'dave@corp.com',   'Engineering', '456-78-9012', 88000.00,  'ACCT-004', 4);

-- Immediately remove all public/default access to the raw table
REVOKE ALL ON hr.employees FROM PUBLIC;
```

!!! note "Revoke First"
    Revoking `PUBLIC` access immediately after table creation is a best practice.
    New tables in PostgreSQL inherit a `PUBLIC` grant that allows any authenticated user to read them.
    Always revoke this before inserting sensitive data.

---

## Part 2 — Design Views by Access Level

### Step 2.1 — Tier 1: Public directory view (no PII)

```sql
CREATE OR REPLACE VIEW hr.v_directory
WITH (security_barrier = TRUE) AS
SELECT
  id,
  name,
  email,
  department
FROM hr.employees;

COMMENT ON VIEW hr.v_directory IS
  'PUBLIC: name, email, department only. No salary, SSN, or bank data.';
```

### Step 2.2 — Tier 2: Manager view (salary + performance, no SSN/bank)

```sql
CREATE OR REPLACE VIEW hr.v_manager
WITH (security_barrier = TRUE) AS
SELECT
  id,
  name,
  email,
  department,
  salary,
  performance_rating
FROM hr.employees;

COMMENT ON VIEW hr.v_manager IS
  'MANAGER: includes salary and performance rating. No SSN or bank account.';
```

### Step 2.3 — Tier 3: Payroll view (masked bank account, no SSN)

```sql
CREATE OR REPLACE VIEW hr.v_payroll
WITH (security_barrier = TRUE) AS
SELECT
  id,
  name,
  department,
  salary,
  -- PCI-DSS pattern: mask everything except last 4 characters
  '****' || RIGHT(bank_account, 4) AS bank_account_masked
FROM hr.employees;

COMMENT ON VIEW hr.v_payroll IS
  'PAYROLL: salary and masked bank account. SSN is never exposed through this view.';
```

### Step 2.4 — Tier 4: HR admin view (full access with implicit access logging)

```sql
CREATE OR REPLACE VIEW hr.v_hr_admin AS
SELECT
  *,
  current_timestamp AS accessed_at,
  current_user      AS accessed_by
FROM hr.employees;

COMMENT ON VIEW hr.v_hr_admin IS
  'HR ADMIN: Full access including SSN and bank account. Every SELECT records the accessor and timestamp.';
```

!!! note "security_barrier on v_hr_admin"
    The HR admin view intentionally omits `security_barrier` because it is a full-exposure view with no filtering predicate to protect. The barrier is most important on views that have a `WHERE` clause filtering sensitive data.

---

## Part 3 — Grant Access via Views Only

### Step 3.1 — Create roles and grant view-level access

```sql
CREATE ROLE role_directory NOLOGIN;
CREATE ROLE role_manager   NOLOGIN;
CREATE ROLE role_payroll   NOLOGIN;
CREATE ROLE role_hr_admin  NOLOGIN;

-- Schema access (required to resolve schema-qualified names)
GRANT USAGE ON SCHEMA hr
  TO role_directory, role_manager, role_payroll, role_hr_admin;

-- Grant access to VIEWS only — never to the base table
GRANT SELECT ON hr.v_directory TO role_directory;
GRANT SELECT ON hr.v_manager   TO role_manager;
GRANT SELECT ON hr.v_payroll   TO role_payroll;
GRANT SELECT ON hr.v_hr_admin  TO role_hr_admin;
```

### Step 3.2 — Query each view and observe which columns are returned

```sql
-- Tier 1: directory (no salary, no SSN, no bank)
TABLE hr.v_directory;

-- Tier 2: manager (salary and performance, no SSN)
SELECT name, department, salary, performance_rating
FROM hr.v_manager;

-- Tier 3: payroll (masked bank account — ****-NNNN format)
SELECT name, salary, bank_account_masked
FROM hr.v_payroll;
```

📸 **Screenshot checkpoint** — capture all three result sets side-by-side or in sequence, showing each view returning only its designated columns.

### Step 3.3 — Verify that direct table access is blocked

```sql
SET ROLE role_directory;

-- Attempt to bypass the view and query the base table directly
SELECT * FROM hr.employees;  -- must FAIL

RESET ROLE;
```

**Expected:**
```
ERROR:  permission denied for table employees
```

📸 **Screenshot checkpoint** — direct table access rejected for `role_directory`.

### Step 3.4 — Inventory all HR views and inspect their definitions

```sql
SELECT
  viewname,
  viewowner,
  pg_get_viewdef(viewname::regclass, TRUE) AS definition
FROM pg_views
WHERE schemaname = 'hr'
ORDER BY viewname;
```

📸 **Screenshot checkpoint** — all four views listed with their SQL definitions.

---

## Assessment

### Verification SQL

Dr. Chen will run the following query against your Neon connection string. Ensure all expected values are returned before submitting.

```sql
-- VERIFY LAB 08
SELECT
  -- All four views exist in the hr schema
  (SELECT COUNT(*)
     FROM pg_views
    WHERE schemaname = 'hr')::INT                                       AS hr_view_count,

  -- v_directory exposes NO sensitive columns (ssn, salary, bank_account)
  (SELECT COUNT(*)
     FROM information_schema.columns
    WHERE table_schema = 'hr'
      AND table_name   = 'v_directory'
      AND column_name  IN ('ssn', 'salary', 'bank_account'))::INT       AS sensitive_cols_in_directory,

  -- role_directory has SELECT on the directory view
  has_table_privilege('role_directory', 'hr.v_directory', 'SELECT')     AS dir_role_can_select,

  -- role_directory does NOT have SELECT on the base table
  has_table_privilege('role_directory', 'hr.employees', 'SELECT')       AS dir_role_blocked_from_base;
```

**Expected result:** `4 | 0 | true | false`

---

### Additional Requirement (20 pts)

Create a **`hr.v_salary_bands`** view that replaces exact salary figures with human-readable salary bands, allowing managers to understand compensation distribution without exposing precise numbers.

**Requirements:**

1. Create the view using a `CASE` expression:

    ```sql
    CREATE OR REPLACE VIEW hr.v_salary_bands
    WITH (security_barrier = TRUE) AS
    SELECT
      id,
      name,
      department,
      CASE
        WHEN salary < 75000                    THEN 'Band 1: < $75K'
        WHEN salary BETWEEN 75000 AND 100000   THEN 'Band 2: $75K–$100K'
        ELSE                                        'Band 3: > $100K'
      END AS salary_band
    FROM hr.employees;
    ```

2. Grant `role_manager` SELECT on this view (in addition to their existing `v_manager` access).
3. Run a query **as `role_manager`** on `v_salary_bands` and show that it returns bands, not exact salaries.
4. Run a query **as `role_manager`** on `v_manager` and show exact salaries are still returned via that view.
5. Write 2–3 sentences explaining: in what HR or regulatory contexts is salary banding preferable to exact salary exposure, even for managers?

Submit: both queries with output and the written explanation.

---

### Reflection Questions

1. **`security_barrier = TRUE`** prevents an optimizer-based data leak. Without this option, an attacker who has SELECT on the view can craft a WHERE clause on the view that causes the planner to evaluate their filter *before* the view's own WHERE clause, potentially leaking rows that should be hidden. Give a **concrete SQL example** of this attack against a hypothetical view `hr.v_active_employees` (which has `WHERE is_active = TRUE`) that lacks `security_barrier`. Explain step-by-step how the planner reordering reveals inactive employees.

2. You granted access to views and revoked it from the base table. What happens if a developer later runs `ALTER TABLE hr.employees ADD COLUMN medical_notes TEXT` and inserts sensitive data? Is that new column automatically protected by the existing views? What **organizational process** should be established to ensure new columns are reviewed for sensitivity before data is inserted?

3. The `v_hr_admin` view appends `accessed_at` and `accessed_by` columns. This is a lightweight, zero-infrastructure auditing approach. What are **three specific limitations** of this view-based audit compared to a proper trigger-based audit log (as implemented in Lab 09)? Describe a scenario where view-based logging would be clearly insufficient for a compliance audit.

---

!!! tip "Grading Rubric"
    | Component | Points |
    |---|---|
    | Lab steps (Parts 1–3 with screenshots) | 50 |
    | Verification SQL matches expected output | 30 |
    | Additional Requirement (v_salary_bands) | 20 |
    | **Total** | **100** |
