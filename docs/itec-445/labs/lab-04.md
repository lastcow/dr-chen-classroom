---
title: "Lab 04: User-Defined Functions & Triggers"
course: ITEC-445
topic: User-Defined Functions & Triggers
week: 4
difficulty: ⭐⭐⭐
estimated_time: 85 minutes
---

# Lab 04: User-Defined Functions & Triggers

| Field | Details |
|---|---|
| **Course** | ITEC-445 — Advanced Database Management |
| **Week** | 4 |
| **Difficulty** | ⭐⭐⭐ Advanced |
| **Estimated Time** | 85 minutes |
| **Topic** | User-Defined Functions & Triggers |
| **Prerequisites** | Lab 01 schema on Neon branch `lab-04` |
| **Deliverables** | 4 UDFs, 3 triggers, `verify_lab04()` PASS |

---

## Overview

Functions extend SQL's vocabulary — reusable calculations you can call anywhere a value is expected. Triggers automate database behavior invisibly: auditing changes, enforcing business rules, and maintaining denormalized data. This lab builds the computed-value and automation layer for the Frostburg University database.

---

!!! warning "Branch Requirement"
    Create branch **`lab-04`** with Lab 01 schema populated. Run Lab 01 seed SQL + Lab 02 `grade_points` view.

---

## Part A — Scalar Functions (30 pts)

**A1.** GPA calculator: Write `calculate_gpa(p_student_id INT) RETURNS NUMERIC(3,2)` — computes a student's GPA from their `grade_points` view rows. Return `NULL` if no graded courses.

```sql
SET search_path = fsu;

CREATE OR REPLACE FUNCTION calculate_gpa(p_student_id INT)
RETURNS NUMERIC(3,2)
LANGUAGE plpgsql STABLE AS $$
DECLARE
    v_gpa NUMERIC(3,2);
BEGIN
    SELECT ROUND(AVG(points)::NUMERIC, 2) INTO v_gpa
    FROM grade_points
    WHERE student_id = p_student_id AND points IS NOT NULL;
    RETURN v_gpa;
END;
$$;

-- Test
SELECT student_id, first_name, gpa AS stored_gpa,
       calculate_gpa(student_id) AS computed_gpa
FROM fsu.students ORDER BY student_id;
```

**A2.** Letter grade converter: Write `points_to_letter(p_points NUMERIC) RETURNS VARCHAR(2)` — converts a 0–4.0 GPA point value back to the letter grade string. Handle edge cases (NULL, out-of-range).

**A3.** Enrollment status: Write `enrollment_status(p_student_id INT, p_semester VARCHAR) RETURNS TEXT` — returns `'Active'` if enrolled in ≥1 course that semester, `'Inactive'` otherwise, `'Invalid Student'` if student_id doesn't exist.

**A4.** Credit hours: Write `total_credits(p_student_id INT, p_semester VARCHAR) RETURNS INT` — returns the total credit hours a student is taking in a given semester by joining enrollments and courses.

---

## Part B — Table-Valued Function (15 pts)

Write `student_transcript(p_student_id INT)` returning a table of all enrollment records formatted as a transcript:

```sql
CREATE OR REPLACE FUNCTION student_transcript(p_student_id INT)
RETURNS TABLE(
    semester    VARCHAR,
    course_code VARCHAR,
    title       VARCHAR,
    credits     SMALLINT,
    grade       VARCHAR,
    points      NUMERIC,
    semester_gpa NUMERIC
)
LANGUAGE plpgsql STABLE AS $$
BEGIN
    RETURN QUERY
    SELECT
        e.semester,
        c.course_code,
        c.title,
        c.credits,
        e.grade,
        gp.points,
        ROUND(AVG(gp.points) OVER (PARTITION BY e.semester), 2) AS semester_gpa
    FROM enrollments e
    JOIN courses c     ON e.course_id = c.course_id
    JOIN grade_points gp ON e.enrollment_id = gp.enrollment_id
    WHERE e.student_id = p_student_id
    ORDER BY e.semester, c.course_code;
END;
$$;

-- Test: show Lena Adams's full transcript
SELECT * FROM student_transcript(1);
```

---

## Part C — Trigger: Audit Log (25 pts)

Create a trigger that logs every INSERT, UPDATE, and DELETE on the `enrollments` table into a `enrollment_audit` table.

```sql
CREATE TABLE IF NOT EXISTS enrollment_audit (
    audit_id     SERIAL PRIMARY KEY,
    operation    VARCHAR(6) NOT NULL,  -- INSERT, UPDATE, DELETE
    enrollment_id INT,
    student_id   INT,
    course_id    INT,
    semester     VARCHAR(10),
    old_grade    VARCHAR(2),
    new_grade    VARCHAR(2),
    changed_by   TEXT DEFAULT current_user,
    changed_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE OR REPLACE FUNCTION trg_enrollment_audit()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO enrollment_audit
            (operation, enrollment_id, student_id, course_id, semester, new_grade)
        VALUES ('INSERT', NEW.enrollment_id, NEW.student_id, NEW.course_id, NEW.semester, NEW.grade);
        RETURN NEW;

    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO enrollment_audit
            (operation, enrollment_id, student_id, course_id, semester, old_grade, new_grade)
        VALUES ('UPDATE', NEW.enrollment_id, NEW.student_id, NEW.course_id,
                NEW.semester, OLD.grade, NEW.grade);
        RETURN NEW;

    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO enrollment_audit
            (operation, enrollment_id, student_id, course_id, semester, old_grade)
        VALUES ('DELETE', OLD.enrollment_id, OLD.student_id, OLD.course_id,
                OLD.semester, OLD.grade);
        RETURN OLD;
    END IF;
END;
$$;

CREATE TRIGGER enrollment_audit_trigger
AFTER INSERT OR UPDATE OR DELETE ON enrollments
FOR EACH ROW EXECUTE FUNCTION trg_enrollment_audit();
```

**Test it:**
```sql
-- INSERT
INSERT INTO fsu.enrollments (student_id, course_id, semester) VALUES (6, 1, '2025SP');

-- UPDATE (assign a grade)
UPDATE fsu.enrollments SET grade = 'A-'
WHERE student_id = 6 AND course_id = 1 AND semester = '2025SP';

-- DELETE
DELETE FROM fsu.enrollments WHERE student_id = 6 AND course_id = 1 AND semester = '2025SP';

-- View audit log
SELECT * FROM fsu.enrollment_audit ORDER BY changed_at;
```

Verify 3 rows appear in `enrollment_audit` (INSERT, UPDATE, DELETE).

---

## Part D — Trigger: BEFORE Validation (20 pts)

Write a `BEFORE INSERT OR UPDATE` trigger on `students` that:
1. Rejects any update that would set GPA outside the range 0.00–4.00
2. Normalizes the email to lowercase automatically
3. Prevents enrollment year from being in the future

```sql
CREATE OR REPLACE FUNCTION trg_student_validate()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    -- Normalize email
    NEW.email := LOWER(TRIM(NEW.email));

    -- Validate GPA range
    IF NEW.gpa IS NOT NULL AND (NEW.gpa < 0 OR NEW.gpa > 4.0) THEN
        RAISE EXCEPTION 'GPA % is outside valid range 0.00-4.00', NEW.gpa;
    END IF;

    -- Validate enrollment year
    IF NEW.enroll_year > EXTRACT(YEAR FROM NOW()) THEN
        RAISE EXCEPTION 'Enrollment year % cannot be in the future', NEW.enroll_year;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER student_validate_trigger
BEFORE INSERT OR UPDATE ON students
FOR EACH ROW EXECUTE FUNCTION trg_student_validate();
```

**Test it — each should behave as noted:**
```sql
-- Should FAIL (GPA > 4.0)
UPDATE fsu.students SET gpa = 4.5 WHERE student_id = 1;

-- Should FAIL (future year)
UPDATE fsu.students SET enroll_year = 2099 WHERE student_id = 1;

-- Should SUCCEED and normalize email to lowercase
UPDATE fsu.students SET email = 'LADAMS@STUDENT.FSU.EDU' WHERE student_id = 1;
SELECT email FROM fsu.students WHERE student_id = 1;  -- should be lowercase
```

---

## Part E — Trigger: Auto-Update GPA (10 pts)

Write an `AFTER INSERT OR UPDATE OR DELETE` trigger on `enrollments` that automatically calls `recalculate_all_gpas()` — or better, recalculates only the affected student's GPA — whenever a grade changes:

```sql
CREATE OR REPLACE FUNCTION trg_update_student_gpa()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
DECLARE
    v_student_id INT;
    v_new_gpa    NUMERIC(3,2);
BEGIN
    -- Determine which student was affected
    v_student_id := COALESCE(NEW.student_id, OLD.student_id);

    -- Recalculate just this student's GPA
    SELECT ROUND(AVG(points)::NUMERIC, 2) INTO v_new_gpa
    FROM fsu.grade_points
    WHERE student_id = v_student_id AND points IS NOT NULL;

    UPDATE fsu.students SET gpa = v_new_gpa WHERE student_id = v_student_id;
    RETURN COALESCE(NEW, OLD);
END;
$$;

CREATE TRIGGER update_gpa_on_grade_change
AFTER INSERT OR UPDATE OF grade OR DELETE ON enrollments
FOR EACH ROW EXECUTE FUNCTION trg_update_student_gpa();
```

**Test it:**
```sql
-- Check Lena Adams's current GPA
SELECT gpa FROM fsu.students WHERE student_id = 1;

-- Change a grade
UPDATE fsu.enrollments SET grade = 'F'
WHERE student_id = 1 AND semester = '2024FA' AND course_id = 1;

-- GPA should auto-update (drop significantly)
SELECT gpa FROM fsu.students WHERE student_id = 1;

-- Restore
UPDATE fsu.enrollments SET grade = 'A'
WHERE student_id = 1 AND semester = '2024FA' AND course_id = 1;
SELECT gpa FROM fsu.students WHERE student_id = 1;
```

---

## Verification

```sql
SET search_path = fsu;

CREATE OR REPLACE FUNCTION verify_lab04()
RETURNS TABLE(check_id TEXT, description TEXT, result TEXT, points INT) AS $$
BEGIN
    RETURN QUERY SELECT '01', 'calculate_gpa function exists',
        CASE WHEN EXISTS(SELECT 1 FROM pg_proc WHERE proname='calculate_gpa')
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '02', 'calculate_gpa(1) returns non-null',
        CASE WHEN calculate_gpa(1) IS NOT NULL THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '03', 'points_to_letter function exists',
        CASE WHEN EXISTS(SELECT 1 FROM pg_proc WHERE proname='points_to_letter')
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '04', 'student_transcript function returns rows for student 1',
        CASE WHEN (SELECT COUNT(*) FROM student_transcript(1)) > 0
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '05', 'enrollment_audit table exists',
        CASE WHEN EXISTS(SELECT 1 FROM information_schema.tables
                         WHERE table_schema='fsu' AND table_name='enrollment_audit')
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '06', 'enrollment_audit trigger fires on INSERT',
        CASE WHEN (SELECT COUNT(*) FROM enrollment_audit WHERE operation='INSERT') > 0
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '07', 'enrollment_audit trigger fires on UPDATE',
        CASE WHEN (SELECT COUNT(*) FROM enrollment_audit WHERE operation='UPDATE') > 0
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '08', 'student_validate_trigger exists',
        CASE WHEN EXISTS(SELECT 1 FROM pg_trigger WHERE tgname='student_validate_trigger')
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '09', 'email normalized to lowercase by trigger',
        CASE WHEN NOT EXISTS(SELECT 1 FROM students WHERE email != LOWER(email))
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '10', 'update_gpa_on_grade_change trigger exists',
        CASE WHEN EXISTS(SELECT 1 FROM pg_trigger WHERE tgname='update_gpa_on_grade_change')
             THEN 'PASS' ELSE 'FAIL' END, 10;
END;
$$ LANGUAGE plpgsql;

SELECT check_id, description, result,
       CASE WHEN result = 'PASS' THEN points ELSE 0 END AS earned
FROM verify_lab04()
ORDER BY check_id;
```

---

## Additional Requirement (20 pts)

Write a function `dean_list(p_semester VARCHAR, p_min_gpa NUMERIC DEFAULT 3.5) RETURNS TABLE` that returns all students who qualify for the dean's list for a given semester — defined as having a semester GPA of at least `p_min_gpa` and being enrolled in at least 12 credit hours that semester.

Columns: `student_id`, `full_name`, `dept_name`, `semester_gpa`, `credit_hours`.

---

## Submission Checklist

- [ ] Neon branch `lab-04` with all functions and triggers created
- [ ] All test statements run with screenshots showing expected behavior
- [ ] `verify_lab04()` screenshot — all PASS
- [ ] `lab04_bonus.sql` — `dean_list` function

---

## Grading

| Component | Points |
|-----------|--------|
| Part A — 4 scalar functions (correct logic, handles NULLs) | 30 |
| Part B — student_transcript table-valued function | 15 |
| Part C — enrollment_audit trigger (INSERT/UPDATE/DELETE) | 25 |
| Part D — BEFORE validation trigger (3 rules enforced) | 20 |
| Part E — auto-GPA update trigger | 10 |
| Additional requirement — dean_list function | 20 |
| **Total** | **120** |
