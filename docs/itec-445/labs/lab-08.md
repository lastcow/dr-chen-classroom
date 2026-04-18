---
title: "Lab 08: Database Views — Design, Security & Reporting"
course: ITEC-445
topic: Database Views — Design, Security & Reporting
week: 8
difficulty: ⭐⭐
estimated_time: 75 minutes
---

# Lab 08: Database Views — Design, Security & Reporting

| Field | Details |
|---|---|
| **Course** | ITEC-445 — Advanced Database Management |
| **Week** | 8 |
| **Difficulty** | ⭐⭐ Intermediate |
| **Estimated Time** | 75 minutes |
| **Topic** | Database Views — Design, Security & Reporting |
| **Prerequisites** | Lab 01 schema + Lab 06 seed data on Neon branch `lab-08` |
| **Deliverables** | 6 views created, security tested, `verify_lab08()` PASS |

---

## Overview

Views are the interface layer between raw tables and the outside world — they hide sensitive columns, encapsulate complex joins, and enforce row-level access without changing the underlying schema. In this lab you will build a complete view layer for the Frostburg University database including PII-masking security views, reporting views, and materialized views.

---

!!! warning "Branch Requirement"
    Create branch **`lab-08`** with Lab 01 schema + Lab 06 seed data (500+ students).

---

## Part A — Reporting Views (30 pts)

**A1.** Student summary view — used by the registrar:

```sql
SET search_path = fsu;

CREATE OR REPLACE VIEW v_student_summary AS
SELECT
    s.student_id,
    s.first_name || ' ' || s.last_name          AS full_name,
    d.dept_name,
    s.gpa,
    s.enroll_year,
    COUNT(e.enrollment_id)                        AS total_courses,
    COUNT(CASE WHEN e.semester = '2024FA' THEN 1 END) AS current_enrollments,
    MAX(e.semester)                               AS latest_semester
FROM students s
LEFT JOIN departments d  ON s.dept_id    = d.dept_id
LEFT JOIN enrollments e  ON s.student_id = e.student_id
GROUP BY s.student_id, s.first_name, s.last_name, d.dept_name, s.gpa, s.enroll_year;

-- Test
SELECT * FROM v_student_summary ORDER BY gpa DESC NULLS LAST LIMIT 10;
```

**A2.** Department report view — used by department chairs:

```sql
CREATE OR REPLACE VIEW v_department_report AS
SELECT
    d.dept_id,
    d.dept_name,
    d.building,
    COUNT(DISTINCT s.student_id)                 AS student_count,
    ROUND(AVG(s.gpa)::NUMERIC, 2)                AS avg_gpa,
    COUNT(DISTINCT i.instructor_id)              AS instructor_count,
    ROUND(AVG(i.salary)::NUMERIC, 0)             AS avg_instructor_salary,
    COUNT(DISTINCT c.course_id)                  AS course_count
FROM departments d
LEFT JOIN students    s ON s.dept_id    = d.dept_id
LEFT JOIN instructors i ON i.dept_id    = d.dept_id
LEFT JOIN courses     c ON c.dept_id    = d.dept_id
GROUP BY d.dept_id, d.dept_name, d.building;

SELECT * FROM v_department_report ORDER BY student_count DESC;
```

**A3.** Course enrollment report view:

```sql
CREATE OR REPLACE VIEW v_course_enrollment AS
SELECT
    c.course_code,
    c.title,
    c.credits,
    d.dept_name,
    e.semester,
    COUNT(e.enrollment_id)                        AS enrolled,
    COUNT(CASE WHEN e.grade IS NOT NULL THEN 1 END) AS graded,
    ROUND(AVG(
        CASE e.grade
            WHEN 'A' THEN 4.0 WHEN 'A-' THEN 3.7 WHEN 'B+' THEN 3.3
            WHEN 'B' THEN 3.0 WHEN 'B-' THEN 2.7 WHEN 'C+' THEN 2.3
            WHEN 'C' THEN 2.0 WHEN 'C-' THEN 1.7 WHEN 'D+' THEN 1.3
            WHEN 'D' THEN 1.0 WHEN 'F'  THEN 0.0 ELSE NULL
        END
    )::NUMERIC, 2)                               AS avg_grade_points
FROM courses c
JOIN departments d  ON c.dept_id  = d.dept_id
JOIN enrollments e  ON c.course_id = e.course_id
GROUP BY c.course_id, c.course_code, c.title, c.credits, d.dept_name, e.semester
ORDER BY c.course_code, e.semester;

SELECT * FROM v_course_enrollment WHERE semester = '2024FA';
```

---

## Part B — Security Views: PII Masking (30 pts)

**B1.** Public student directory — masks email domain and omits GPA:

```sql
CREATE OR REPLACE VIEW v_student_directory AS
SELECT
    student_id,
    first_name,
    last_name,
    -- Mask email: show first 3 chars + *** + domain
    LEFT(email, 3) || '***@' ||
        SPLIT_PART(email, '@', 2)                AS masked_email,
    dept_id,
    enroll_year
FROM students;

-- Verify: email is masked
SELECT * FROM v_student_directory LIMIT 5;
```

**B2.** Instructor salary view — only shows salary to HR role, masked to others:

```sql
-- Full view (HR only)
CREATE OR REPLACE VIEW v_instructor_full AS
SELECT instructor_id, first_name, last_name, email, dept_id, hire_date, salary
FROM instructors;

-- Masked view (general use) — salary replaced with band
CREATE OR REPLACE VIEW v_instructor_public AS
SELECT
    instructor_id,
    first_name,
    last_name,
    dept_id,
    hire_date,
    CASE
        WHEN salary < 80000 THEN 'Band A (<$80k)'
        WHEN salary < 90000 THEN 'Band B ($80k-$90k)'
        WHEN salary < 100000 THEN 'Band C ($90k-$100k)'
        ELSE 'Band D ($100k+)'
    END AS salary_band
FROM instructors;

SELECT * FROM v_instructor_public;
```

**B3.** Row-level security view — students see only their own enrollments:

```sql
-- This view simulates RLS by filtering to a hypothetical "current user" student ID
-- In production: use RLS policies (see Lab 09)
CREATE OR REPLACE VIEW v_my_enrollments AS
SELECT
    e.enrollment_id,
    c.course_code,
    c.title,
    e.semester,
    e.grade
FROM enrollments e
JOIN courses c ON e.course_id = c.course_id
WHERE e.student_id = current_setting('app.current_student_id', TRUE)::INT;

-- Test:
SET app.current_student_id = '1';
SELECT * FROM v_my_enrollments;

SET app.current_student_id = '5';
SELECT * FROM v_my_enrollments;
```

---

## Part C — Updatable Views & WITH CHECK OPTION (20 pts)

**C1.** Create an updatable view for active 2024FA enrollments:

```sql
CREATE OR REPLACE VIEW v_active_enrollments AS
SELECT enrollment_id, student_id, course_id, semester, grade
FROM enrollments
WHERE semester = '2024FA'
WITH CHECK OPTION;  -- prevents INSERT/UPDATE that would leave the filter
```

Test that `WITH CHECK OPTION` works:
```sql
-- Should SUCCEED (2024FA row)
UPDATE v_active_enrollments SET grade = 'B+' WHERE enrollment_id = 1;

-- Should FAIL (WITH CHECK OPTION rejects semester change)
UPDATE v_active_enrollments SET semester = '2023SP' WHERE enrollment_id = 1;
```

**C2.** Insert through a view:
```sql
-- Should succeed and be visible through the view
INSERT INTO v_active_enrollments (student_id, course_id, semester)
VALUES (12, 5, '2024FA');

-- Verify it appeared
SELECT * FROM v_active_enrollments WHERE student_id = 12 AND course_id = 5;
```

---

## Part D — Materialized View (20 pts)

Standard views re-execute their query every time. For expensive aggregations, a **materialized view** pre-computes and stores the result:

```sql
CREATE MATERIALIZED VIEW mv_dept_stats AS
SELECT
    d.dept_id,
    d.dept_name,
    COUNT(DISTINCT s.student_id)          AS student_count,
    ROUND(AVG(s.gpa)::NUMERIC, 2)         AS avg_gpa,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY s.gpa) AS median_gpa,
    COUNT(DISTINCT e.enrollment_id)       AS total_enrollments
FROM departments d
LEFT JOIN students    s ON s.dept_id    = d.dept_id
LEFT JOIN enrollments e ON e.student_id = s.student_id
GROUP BY d.dept_id, d.dept_name
WITH DATA;

-- Create an index on the materialized view for fast lookups
CREATE UNIQUE INDEX idx_mv_dept_stats ON mv_dept_stats(dept_id);

SELECT * FROM mv_dept_stats ORDER BY student_count DESC;
```

**Refresh after data changes:**
```sql
-- Add a new student
INSERT INTO students (first_name, last_name, email, gpa, dept_id, enroll_year)
VALUES ('New', 'Student', 'new@fsu.edu', 3.9, 1, 2024);

-- Materialized view is stale — old count
SELECT student_count FROM mv_dept_stats WHERE dept_id = 1;

-- Refresh
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_dept_stats;

-- Now current
SELECT student_count FROM mv_dept_stats WHERE dept_id = 1;
```

**Answer in `lab08_analysis.md`:**
1. When should you use a materialized view vs a regular view?
2. What does `CONCURRENTLY` do — and what does it require?
3. What is the downside of materialized views in terms of data freshness?

---

## Verification

```sql
SET search_path = fsu;

CREATE OR REPLACE FUNCTION verify_lab08()
RETURNS TABLE(check_id TEXT, description TEXT, result TEXT, points INT) AS $$
BEGIN
    RETURN QUERY SELECT '01', 'v_student_summary view exists',
        CASE WHEN EXISTS(SELECT 1 FROM information_schema.views
                         WHERE table_schema='fsu' AND table_name='v_student_summary')
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '02', 'v_department_report returns 5 rows',
        CASE WHEN (SELECT COUNT(*) FROM v_department_report) = 5
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '03', 'v_course_enrollment view exists',
        CASE WHEN EXISTS(SELECT 1 FROM information_schema.views
                         WHERE table_schema='fsu' AND table_name='v_course_enrollment')
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '04', 'v_student_directory masks email',
        CASE WHEN NOT EXISTS(SELECT 1 FROM v_student_directory WHERE masked_email NOT LIKE '%***%')
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '05', 'v_instructor_public shows salary band not raw salary',
        CASE WHEN NOT EXISTS(
            SELECT 1 FROM information_schema.columns
            WHERE table_schema='fsu' AND table_name='v_instructor_public' AND column_name='salary'
        ) THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '06', 'v_my_enrollments view exists',
        CASE WHEN EXISTS(SELECT 1 FROM information_schema.views
                         WHERE table_schema='fsu' AND table_name='v_my_enrollments')
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '07', 'v_active_enrollments view exists with check option',
        CASE WHEN EXISTS(SELECT 1 FROM information_schema.views
                         WHERE table_schema='fsu' AND table_name='v_active_enrollments'
                         AND check_option = 'CASCADED')
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '08', 'mv_dept_stats materialized view exists',
        CASE WHEN EXISTS(SELECT 1 FROM pg_matviews WHERE schemaname='fsu' AND matviewname='mv_dept_stats')
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '09', 'mv_dept_stats has 5 rows (one per dept)',
        CASE WHEN (SELECT COUNT(*) FROM mv_dept_stats) = 5
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '10', 'v_student_summary returns rows',
        CASE WHEN (SELECT COUNT(*) FROM v_student_summary) > 0
             THEN 'PASS' ELSE 'FAIL' END, 10;
END;
$$ LANGUAGE plpgsql;

SELECT check_id, description, result,
       CASE WHEN result = 'PASS' THEN points ELSE 0 END AS earned
FROM verify_lab08()
ORDER BY check_id;
```

---

## Additional Requirement (20 pts)

Create `v_at_risk_students` — a view identifying students who may be academically at risk:

**Criteria for "at risk":**
- GPA < 2.0, OR
- Has a grade of 'F' in any course in the last 2 semesters, OR
- Enrolled in 0 courses in the current semester (`2024FA`)

Columns: `student_id`, `full_name`, `dept_name`, `gpa`, `risk_reason` (text explaining which criterion triggered), `last_active_semester`.

---

## Submission Checklist

- [ ] Neon branch `lab-08` with all 6 views + 1 materialized view created
- [ ] `lab08_analysis.md` — Part D answers + view design decisions
- [ ] All views tested with SELECT queries (screenshots)
- [ ] `WITH CHECK OPTION` test screenshots (succeed + fail cases)
- [ ] `v_at_risk_students` view (additional requirement)
- [ ] `verify_lab08()` screenshot — all PASS

---

## Grading

| Component | Points |
|-----------|--------|
| Part A — 3 reporting views (correct aggregations, tested) | 30 |
| Part B — 3 security views (PII masked, RLS simulated) | 30 |
| Part C — updatable view + WITH CHECK OPTION tests | 20 |
| Part D — materialized view + refresh + analysis answers | 20 |
| Additional requirement — v_at_risk_students | 20 |
| **Total** | **120** |
