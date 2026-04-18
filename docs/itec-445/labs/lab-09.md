---
title: "Lab 09: Database Security — Authentication & RBAC"
course: ITEC-445
topic: Database Security — Authentication & Authorization
week: 9
difficulty: ⭐⭐⭐
estimated_time: 85 minutes
---

# Lab 09: Database Security — Authentication & RBAC

| Field | Details |
|---|---|
| **Course** | ITEC-445 — Advanced Database Management |
| **Week** | 9 |
| **Difficulty** | ⭐⭐⭐ Advanced |
| **Estimated Time** | 85 minutes |
| **Topic** | Database Security — Authentication & Authorization |
| **Prerequisites** | Lab 01 schema + Lab 08 views on Neon branch `lab-09` |
| **Deliverables** | RBAC roles created, privileges granted, RLS policies, `verify_lab09()` PASS |

---

## Overview

Database security is implemented at the server layer — not just the application layer. In this lab you will design and implement a complete Role-Based Access Control model for the Frostburg University database using PostgreSQL roles, privilege hierarchies, and Row-Level Security policies. When correctly configured, even a compromised application cannot access data it isn't authorized to see.

---

!!! warning "Branch Requirement"
    Create branch **`lab-09`** with Lab 01 schema + Lab 08 views. You need the views from Lab 08 for the privilege grants to be meaningful.

!!! info "Neon Role Limitations"
    On Neon's free tier, you cannot create new login roles with passwords (the database user is managed by Neon). For this lab, **use roles without LOGIN** to demonstrate privilege design. The role hierarchy and `GRANT` statements work the same way — only the connection step is simulated.

---

## Part A — Role Hierarchy Design (20 pts)

Design a 4-tier RBAC model for the Frostburg University database. Document in `lab09_rbac_design.md` before writing any SQL:

```
                    ┌─────────────────┐
                    │   db_superuser  │  (Neon managed)
                    └────────┬────────┘
                             │ GRANT ROLE
              ┌──────────────┼──────────────┐
              │              │              │
      ┌───────▼──────┐ ┌─────▼──────┐ ┌────▼───────────┐
      │  role_dba    │ │ role_admin │ │  role_reporting │
      └───────┬──────┘ └─────┬──────┘ └────┬───────────┘
              │              │              │
         (Full DB       (Student +    (Read-only
          admin)         course mgmt)   views only)
              │
      ┌───────▼──────┐
      │  role_student │  (own records only via RLS)
      └──────────────┘
```

For each role, define in `lab09_rbac_design.md`:
- What tables/views they can SELECT, INSERT, UPDATE, DELETE
- Whether they can CREATE objects
- Which role it inherits from

---

## Part B — Create Roles & Grant Privileges (35 pts)

```sql
SET search_path = fsu;

-- Create roles (no LOGIN — Neon manages login users)
CREATE ROLE role_dba;
CREATE ROLE role_admin;
CREATE ROLE role_reporting;
CREATE ROLE role_student;

-- ── role_dba: full access to all fsu objects ──────────────────────
GRANT ALL PRIVILEGES ON SCHEMA fsu TO role_dba;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA fsu TO role_dba;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA fsu TO role_dba;
GRANT ALL PRIVILEGES ON ALL ROUTINES IN SCHEMA fsu TO role_dba;

-- ── role_admin: manage students and enrollments, read instructors ──
GRANT USAGE ON SCHEMA fsu TO role_admin;
GRANT SELECT, INSERT, UPDATE, DELETE ON fsu.students TO role_admin;
GRANT SELECT, INSERT, UPDATE, DELETE ON fsu.enrollments TO role_admin;
GRANT SELECT ON fsu.courses TO role_admin;
GRANT SELECT ON fsu.departments TO role_admin;
GRANT SELECT ON fsu.instructors TO role_admin;
GRANT USAGE ON SEQUENCE fsu.students_student_id_seq TO role_admin;
GRANT USAGE ON SEQUENCE fsu.enrollments_enrollment_id_seq TO role_admin;
-- Views
GRANT SELECT ON fsu.v_student_summary TO role_admin;
GRANT SELECT ON fsu.v_department_report TO role_admin;
GRANT SELECT ON fsu.v_student_directory TO role_admin;
-- Cannot see full instructor salary view
REVOKE SELECT ON fsu.v_instructor_full FROM role_admin;

-- ── role_reporting: read-only, views only (no raw tables) ─────────
GRANT USAGE ON SCHEMA fsu TO role_reporting;
GRANT SELECT ON fsu.v_student_summary TO role_reporting;
GRANT SELECT ON fsu.v_department_report TO role_reporting;
GRANT SELECT ON fsu.v_course_enrollment TO role_reporting;
GRANT SELECT ON fsu.v_student_directory TO role_reporting;
GRANT SELECT ON fsu.v_instructor_public TO role_reporting;
GRANT SELECT ON fsu.mv_dept_stats TO role_reporting;
-- Explicitly deny raw table access
REVOKE ALL ON fsu.students FROM role_reporting;
REVOKE ALL ON fsu.instructors FROM role_reporting;

-- ── role_student: own records only (enforced by RLS in Part C) ────
GRANT USAGE ON SCHEMA fsu TO role_student;
GRANT SELECT ON fsu.v_student_directory TO role_student;
GRANT SELECT ON fsu.v_my_enrollments TO role_student;
GRANT SELECT ON fsu.courses TO role_student;
GRANT SELECT ON fsu.departments TO role_student;
-- Students cannot see other students' raw records
REVOKE ALL ON fsu.students FROM role_student;
REVOKE ALL ON fsu.enrollments FROM role_student;
```

**Verify privilege grants:**
```sql
-- Check what role_reporting can access
SELECT grantee, table_name, privilege_type
FROM information_schema.role_table_grants
WHERE grantee = 'role_reporting' AND table_schema = 'fsu'
ORDER BY table_name, privilege_type;

-- Check what role_admin cannot access
SELECT has_table_privilege('role_admin', 'fsu.v_instructor_full', 'SELECT') AS can_see_salaries;
-- Should return FALSE
```

---

## Part C — Row-Level Security (RLS) (25 pts)

RLS restricts which *rows* a role can see, even when they have SELECT on the table.

```sql
-- Enable RLS on students table
ALTER TABLE fsu.students ENABLE ROW LEVEL SECURITY;
ALTER TABLE fsu.students FORCE ROW LEVEL SECURITY;

-- Enable RLS on enrollments table
ALTER TABLE fsu.enrollments ENABLE ROW LEVEL SECURITY;
ALTER TABLE fsu.enrollments FORCE ROW LEVEL SECURITY;

-- Policy: students can only see their own student record
-- We simulate the "current student" via a session setting
CREATE POLICY student_self_only ON fsu.students
    FOR SELECT
    TO role_student
    USING (
        student_id = current_setting('app.current_student_id', TRUE)::INT
    );

-- Policy: students can only see their own enrollments
CREATE POLICY student_own_enrollments ON fsu.enrollments
    FOR SELECT
    TO role_student
    USING (
        student_id = current_setting('app.current_student_id', TRUE)::INT
    );

-- Bypass policy: dba and admin see everything
CREATE POLICY admin_all_students ON fsu.students
    FOR ALL TO role_dba, role_admin
    USING (TRUE);

CREATE POLICY admin_all_enrollments ON fsu.enrollments
    FOR ALL TO role_dba, role_admin
    USING (TRUE);
```

**Test RLS policies:**
```sql
-- As DBA (bypass): should see all students
SET ROLE role_dba;
SELECT COUNT(*) FROM fsu.students;  -- should be 500+

-- As student (RLS active): should see only own record
SET ROLE role_student;
SET app.current_student_id = '1';
SELECT COUNT(*) FROM fsu.students;  -- should be 1

SET app.current_student_id = '5';
SELECT * FROM fsu.students;  -- should show only student_id=5

RESET ROLE;
```

**Answer in `lab09_rbac_design.md`:**
1. What does `FORCE ROW LEVEL SECURITY` do? When would you use it without `FORCE`?
2. What happens if a user has NO matching policy on an RLS-enabled table?
3. Why does `role_dba` need an explicit `USING (TRUE)` policy rather than being policy-exempt automatically?

---

## Part D — SQL Injection Defense (20 pts)

Demonstrate and defend against SQL injection at the database layer using parameterized queries via a Python script.

Create `lab09_sqli_demo.py`:

```python
import psycopg2
import os

conn = psycopg2.connect(os.environ["DATABASE_URL"])
conn.autocommit = True
cur = conn.cursor()
cur.execute("SET search_path = fsu")

print("=== SQL Injection Demo ===\n")

# ── VULNERABLE: string interpolation ───────────────────────────────
def vulnerable_search(name_input: str):
    """NEVER DO THIS — direct string interpolation."""
    query = f"SELECT student_id, first_name, last_name FROM fsu.students WHERE last_name = '{name_input}'"
    print(f"Executing: {query[:80]}")
    try:
        cur.execute(query)
        return cur.fetchall()
    except Exception as e:
        print(f"  ERROR: {e}")
        return []

# Normal input
print("Normal search for 'Adams':")
print(vulnerable_search("Adams"))

# SQL injection: UNION to extract all students
print("\nInjection: ' UNION SELECT student_id, email, last_name FROM students --")
print(vulnerable_search("' UNION SELECT student_id, email, last_name FROM students --"))

# ── SAFE: parameterized query ───────────────────────────────────────
def safe_search(name_input: str):
    """ALWAYS DO THIS — parameterized query."""
    query = "SELECT student_id, first_name, last_name FROM fsu.students WHERE last_name = %s"
    cur.execute(query, (name_input,))
    return cur.fetchall()

print("\n=== Parameterized Query (Safe) ===\n")
print("Normal search for 'Adams':")
print(safe_search("Adams"))

print("\nInjection attempt (treated as literal string):")
print(safe_search("' UNION SELECT student_id, email, last_name FROM students --"))
# Returns empty list — injection fails
```

Run:
```bash
python lab09_sqli_demo.py
```

**Capture output showing the injection succeeds on vulnerable and fails on safe version.**

---

## Verification

```sql
SET search_path = fsu;

CREATE OR REPLACE FUNCTION verify_lab09()
RETURNS TABLE(check_id TEXT, description TEXT, result TEXT, points INT) AS $$
BEGIN
    RETURN QUERY SELECT '01', 'role_dba exists',
        CASE WHEN EXISTS(SELECT 1 FROM pg_roles WHERE rolname='role_dba')
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '02', 'role_admin exists',
        CASE WHEN EXISTS(SELECT 1 FROM pg_roles WHERE rolname='role_admin')
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '03', 'role_reporting exists',
        CASE WHEN EXISTS(SELECT 1 FROM pg_roles WHERE rolname='role_reporting')
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '04', 'role_student exists',
        CASE WHEN EXISTS(SELECT 1 FROM pg_roles WHERE rolname='role_student')
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '05', 'RLS enabled on students table',
        CASE WHEN (SELECT rowsecurity FROM pg_tables
                   WHERE schemaname='fsu' AND tablename='students')
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '06', 'RLS enabled on enrollments table',
        CASE WHEN (SELECT rowsecurity FROM pg_tables
                   WHERE schemaname='fsu' AND tablename='enrollments')
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '07', 'At least 4 RLS policies exist',
        CASE WHEN (SELECT COUNT(*) FROM pg_policies WHERE schemaname='fsu') >= 4
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '08', 'role_reporting can SELECT v_student_summary',
        CASE WHEN has_table_privilege('role_reporting', 'fsu.v_student_summary', 'SELECT')
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '09', 'role_admin has SELECT on students',
        CASE WHEN has_table_privilege('role_admin', 'fsu.students', 'SELECT')
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '10', 'student_self_only policy exists',
        CASE WHEN EXISTS(SELECT 1 FROM pg_policies
                         WHERE schemaname='fsu' AND policyname='student_self_only')
             THEN 'PASS' ELSE 'FAIL' END, 10;
END;
$$ LANGUAGE plpgsql;

SELECT check_id, description, result,
       CASE WHEN result = 'PASS' THEN points ELSE 0 END AS earned
FROM verify_lab09()
ORDER BY check_id;
```

---

## Additional Requirement (20 pts)

Add a **column-level privilege** layer: the `instructors` table has a `salary` column that only `role_dba` should see. Even `role_admin` should not be able to SELECT it.

1. Revoke `SELECT` on `instructors.salary` from `role_admin`
2. Verify with `has_column_privilege()`
3. Create a view `v_instructor_no_salary` that `role_admin` CAN use (omitting salary column)
4. Write a `privilege_audit.sql` query that reports all column-level privileges in the `fsu` schema from `information_schema.column_privileges`

---

## Submission Checklist

- [ ] `lab09_rbac_design.md` — role hierarchy diagram + privilege matrix + RLS answers
- [ ] Neon branch `lab-09` with all 4 roles created + privileges + RLS policies
- [ ] `lab09_sqli_demo.py` — output screenshot showing injection succeeds/fails
- [ ] `privilege_audit.sql` — column privilege report (additional requirement)
- [ ] `verify_lab09()` screenshot — all PASS

---

## Grading

| Component | Points |
|-----------|--------|
| Part A — RBAC design document (4 roles, privilege matrix) | 20 |
| Part B — Roles created, privileges granted and verified | 35 |
| Part C — RLS policies (4 policies, tested) + analysis answers | 25 |
| Part D — SQL injection demo (vulnerable vs safe, Python script) | 20 |
| Additional requirement — column-level privileges + audit query | 20 |
| **Total** | **120** |
