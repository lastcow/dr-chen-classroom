---
title: "Lab 03: Stored Procedures & PL/pgSQL Control Flow"
course: ITEC-445
topic: Stored Procedures & Control Flow Programming
week: 3
difficulty: ⭐⭐⭐
estimated_time: 90 minutes
---

# Lab 03: Stored Procedures & PL/pgSQL Control Flow

| Field | Details |
|---|---|
| **Course** | ITEC-445 — Advanced Database Management |
| **Week** | 3 |
| **Difficulty** | ⭐⭐⭐ Advanced |
| **Estimated Time** | 90 minutes |
| **Topic** | Stored Procedures & Control Flow Programming |
| **Prerequisites** | Lab 01 complete, `fsu` schema on Neon branch `lab-03` |
| **Deliverables** | 4 stored procedures, `verify_lab03()` PASS |

---

## Overview

Stored procedures move business logic server-side — reducing network round trips, enforcing transaction atomicity, and creating a security boundary between applications and raw tables. In this lab you will write four PL/pgSQL stored procedures covering control flow, cursors, exception handling, and transaction management for the Frostburg University database.

---

!!! warning "Branch Requirement"
    Create branch **`lab-03`** (from `lab-01` base). All Lab 01 schema + data must be present.

---

## Part A — Basic Procedure: Enroll Student (20 pts)

Write a procedure `enroll_student` that safely enrolls a student in a course:

```sql
SET search_path = fsu;

CREATE OR REPLACE PROCEDURE enroll_student(
    p_student_id  INT,
    p_course_code VARCHAR,
    p_semester    VARCHAR
)
LANGUAGE plpgsql AS $$
DECLARE
    v_course_id   INT;
    v_student_exists BOOLEAN;
    v_already_enrolled BOOLEAN;
BEGIN
    -- 1. Verify student exists
    SELECT EXISTS(SELECT 1 FROM students WHERE student_id = p_student_id)
    INTO v_student_exists;

    IF NOT v_student_exists THEN
        RAISE EXCEPTION 'Student ID % does not exist', p_student_id;
    END IF;

    -- 2. Look up course by code
    SELECT course_id INTO v_course_id
    FROM courses WHERE course_code = p_course_code;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Course code % not found', p_course_code;
    END IF;

    -- 3. Check for duplicate enrollment
    SELECT EXISTS(
        SELECT 1 FROM enrollments
        WHERE student_id = p_student_id
          AND course_id  = v_course_id
          AND semester   = p_semester
    ) INTO v_already_enrolled;

    IF v_already_enrolled THEN
        RAISE NOTICE 'Student % already enrolled in % for %',
            p_student_id, p_course_code, p_semester;
        RETURN;
    END IF;

    -- 4. Insert enrollment
    INSERT INTO enrollments (student_id, course_id, semester)
    VALUES (p_student_id, v_course_id, p_semester);

    RAISE NOTICE 'Successfully enrolled student % in % for %',
        p_student_id, p_course_code, p_semester;
END;
$$;
```

**Test it:**
```sql
CALL enroll_student(3, 'ITEC445', '2025SP');  -- should succeed
CALL enroll_student(3, 'ITEC445', '2025SP');  -- should print NOTICE (already enrolled)
CALL enroll_student(999, 'ITEC445', '2025SP'); -- should RAISE EXCEPTION
CALL enroll_student(3, 'FAKE999', '2025SP');   -- should RAISE EXCEPTION
```

---

## Part B — Control Flow: Grade Assignment Procedure (25 pts)

Write `assign_grade` with full control flow:

```sql
CREATE OR REPLACE PROCEDURE assign_grade(
    p_student_id  INT,
    p_course_code VARCHAR,
    p_semester    VARCHAR,
    p_points      NUMERIC   -- raw points out of 100
)
LANGUAGE plpgsql AS $$
DECLARE
    v_course_id  INT;
    v_letter     VARCHAR(2);
    v_rows_updated INT;
BEGIN
    -- Convert numeric score to letter grade
    v_letter := CASE
        WHEN p_points >= 93 THEN 'A'
        WHEN p_points >= 90 THEN 'A-'
        WHEN p_points >= 87 THEN 'B+'
        WHEN p_points >= 83 THEN 'B'
        WHEN p_points >= 80 THEN 'B-'
        WHEN p_points >= 77 THEN 'C+'
        WHEN p_points >= 73 THEN 'C'
        WHEN p_points >= 70 THEN 'C-'
        WHEN p_points >= 67 THEN 'D+'
        WHEN p_points >= 60 THEN 'D'
        ELSE 'F'
    END;

    -- Validate score range
    IF p_points < 0 OR p_points > 100 THEN
        RAISE EXCEPTION 'Score % is out of valid range 0-100', p_points;
    END IF;

    SELECT course_id INTO v_course_id FROM courses WHERE course_code = p_course_code;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Course % not found', p_course_code;
    END IF;

    UPDATE enrollments
    SET grade = v_letter
    WHERE student_id = p_student_id
      AND course_id  = v_course_id
      AND semester   = p_semester;

    GET DIAGNOSTICS v_rows_updated = ROW_COUNT;

    IF v_rows_updated = 0 THEN
        RAISE EXCEPTION 'No enrollment found for student % in % %',
            p_student_id, p_course_code, p_semester;
    END IF;

    RAISE NOTICE 'Grade % assigned to student % for % in %',
        v_letter, p_student_id, p_course_code, p_semester;
END;
$$;
```

**Your task:** Extend `assign_grade` to also log each grade assignment into an `grade_audit_log` table you create:

```sql
CREATE TABLE IF NOT EXISTS grade_audit_log (
    log_id       SERIAL PRIMARY KEY,
    student_id   INT,
    course_code  VARCHAR(10),
    semester     VARCHAR(10),
    old_grade    VARCHAR(2),
    new_grade    VARCHAR(2),
    raw_score    NUMERIC,
    assigned_at  TIMESTAMPTZ DEFAULT NOW()
);
```

The procedure must capture the old grade before updating and write both old and new to the log.

---

## Part C — Cursor: Batch GPA Recalculation (25 pts)

Write `recalculate_all_gpas` — a procedure that uses a cursor to iterate over all students and recompute each student's GPA from their `grade_points` view:

```sql
CREATE OR REPLACE PROCEDURE recalculate_all_gpas()
LANGUAGE plpgsql AS $$
DECLARE
    v_student   RECORD;
    v_new_gpa   NUMERIC(3,2);
    v_updated   INT := 0;
    cur_students CURSOR FOR SELECT student_id FROM students ORDER BY student_id;
BEGIN
    OPEN cur_students;

    LOOP
        FETCH cur_students INTO v_student;
        EXIT WHEN NOT FOUND;

        -- Calculate GPA as average of grade points (exclude NULL grades)
        SELECT ROUND(AVG(points)::NUMERIC, 2) INTO v_new_gpa
        FROM grade_points
        WHERE student_id = v_student.student_id
          AND points IS NOT NULL;

        -- Only update if we have grade data
        IF v_new_gpa IS NOT NULL THEN
            UPDATE students SET gpa = v_new_gpa
            WHERE student_id = v_student.student_id;
            v_updated := v_updated + 1;
        END IF;
    END LOOP;

    CLOSE cur_students;

    RAISE NOTICE 'GPA recalculated for % students', v_updated;
END;
$$;
```

**Test it:**
```sql
-- Manually corrupt a GPA first
UPDATE fsu.students SET gpa = 0.00 WHERE student_id = 1;
SELECT student_id, gpa FROM fsu.students WHERE student_id = 1;

-- Recalculate
CALL recalculate_all_gpas();

-- Verify Lena Adams GPA is now correct
SELECT student_id, first_name, gpa FROM fsu.students WHERE student_id = 1;
```

**Your task:** Extend `recalculate_all_gpas` to also update a `gpa_history` table:

```sql
CREATE TABLE IF NOT EXISTS gpa_history (
    history_id   SERIAL PRIMARY KEY,
    student_id   INT,
    old_gpa      NUMERIC(3,2),
    new_gpa      NUMERIC(3,2),
    changed_at   TIMESTAMPTZ DEFAULT NOW()
);
```

Only insert into `gpa_history` when the GPA actually changed.

---

## Part D — Exception Handling & Transactions: Semester Rollover (20 pts)

Write `rollover_semester` — a procedure that promotes all passing students (grade ≠ 'F') to enrolled status in the next semester, and logs failures with exception handling:

```sql
CREATE OR REPLACE PROCEDURE rollover_semester(
    p_from_semester VARCHAR,
    p_to_semester   VARCHAR
)
LANGUAGE plpgsql AS $$
DECLARE
    v_rec         RECORD;
    v_enrolled    INT := 0;
    v_skipped     INT := 0;
    v_failed      INT := 0;
BEGIN
    FOR v_rec IN
        SELECT DISTINCT student_id, course_id
        FROM enrollments
        WHERE semester = p_from_semester
          AND grade IS NOT NULL
          AND grade <> 'F'
    LOOP
        BEGIN
            INSERT INTO enrollments (student_id, course_id, semester)
            VALUES (v_rec.student_id, v_rec.course_id, p_to_semester);
            v_enrolled := v_enrolled + 1;
        EXCEPTION
            WHEN unique_violation THEN
                -- Already enrolled in new semester — skip
                v_skipped := v_skipped + 1;
            WHEN OTHERS THEN
                -- Log unexpected errors but continue
                RAISE WARNING 'Error enrolling student % in course %: %',
                    v_rec.student_id, v_rec.course_id, SQLERRM;
                v_failed := v_failed + 1;
        END;
    END LOOP;

    RAISE NOTICE 'Rollover complete: % enrolled, % skipped, % failed',
        v_enrolled, v_skipped, v_failed;
END;
$$;
```

**Test it:**
```sql
CALL rollover_semester('2024FA', '2025SP');

-- Verify new enrollments
SELECT COUNT(*) FROM fsu.enrollments WHERE semester = '2025SP';

-- Re-run to verify idempotency (skipped count should equal enrolled count)
CALL rollover_semester('2024FA', '2025SP');
```

**Answer in `lab03_analysis.md`:**
1. What happens if you call `rollover_semester` twice with the same arguments? Is it idempotent? Why?
2. Why use `BEGIN...EXCEPTION...END` inside the `FOR` loop rather than outside it?
3. What is the difference between `RAISE EXCEPTION` and `RAISE WARNING`?

---

## Verification

```sql
SET search_path = fsu;

CREATE OR REPLACE FUNCTION verify_lab03()
RETURNS TABLE(check_id TEXT, description TEXT, result TEXT, points INT) AS $$
BEGIN
    -- Check 1: enroll_student procedure exists
    RETURN QUERY SELECT '01', 'enroll_student procedure exists',
        CASE WHEN EXISTS(SELECT 1 FROM pg_proc WHERE proname = 'enroll_student')
             THEN 'PASS' ELSE 'FAIL' END, 10;

    -- Check 2: assign_grade procedure exists
    RETURN QUERY SELECT '02', 'assign_grade procedure exists',
        CASE WHEN EXISTS(SELECT 1 FROM pg_proc WHERE proname = 'assign_grade')
             THEN 'PASS' ELSE 'FAIL' END, 10;

    -- Check 3: grade_audit_log table exists
    RETURN QUERY SELECT '03', 'grade_audit_log table exists',
        CASE WHEN EXISTS(SELECT 1 FROM information_schema.tables
                         WHERE table_schema='fsu' AND table_name='grade_audit_log')
             THEN 'PASS' ELSE 'FAIL' END, 10;

    -- Check 4: recalculate_all_gpas procedure exists
    RETURN QUERY SELECT '04', 'recalculate_all_gpas procedure exists',
        CASE WHEN EXISTS(SELECT 1 FROM pg_proc WHERE proname = 'recalculate_all_gpas')
             THEN 'PASS' ELSE 'FAIL' END, 10;

    -- Check 5: gpa_history table exists
    RETURN QUERY SELECT '05', 'gpa_history table exists',
        CASE WHEN EXISTS(SELECT 1 FROM information_schema.tables
                         WHERE table_schema='fsu' AND table_name='gpa_history')
             THEN 'PASS' ELSE 'FAIL' END, 10;

    -- Check 6: rollover_semester procedure exists
    RETURN QUERY SELECT '06', 'rollover_semester procedure exists',
        CASE WHEN EXISTS(SELECT 1 FROM pg_proc WHERE proname = 'rollover_semester')
             THEN 'PASS' ELSE 'FAIL' END, 10;

    -- Check 7: enroll_student works (test enrollment for 2025SP)
    RETURN QUERY SELECT '07', 'enroll_student can enroll student 3 in ITEC445 2025SP',
        CASE WHEN EXISTS(
            SELECT 1 FROM enrollments e
            JOIN courses c ON e.course_id = c.course_id
            WHERE e.student_id = 3 AND c.course_code = 'ITEC445' AND e.semester = '2025SP'
        ) THEN 'PASS' ELSE 'NEEDS_CALL' END, 10;

    -- Check 8: grade_audit_log has rows (assign_grade was called)
    RETURN QUERY SELECT '08', 'grade_audit_log has at least 1 row',
        CASE WHEN (SELECT COUNT(*) FROM grade_audit_log) >= 1
             THEN 'PASS' ELSE 'NEEDS_CALL' END, 10;

    -- Check 9: Student GPAs are non-zero after recalculate
    RETURN QUERY SELECT '09', 'Student 1 GPA is non-zero after recalculate',
        CASE WHEN (SELECT gpa FROM students WHERE student_id = 1) > 0
             THEN 'PASS' ELSE 'FAIL' END, 10;

    -- Check 10: rollover created 2025SP rows
    RETURN QUERY SELECT '10', '2025SP enrollments exist after rollover',
        CASE WHEN (SELECT COUNT(*) FROM enrollments WHERE semester = '2025SP') > 0
             THEN 'PASS' ELSE 'NEEDS_CALL' END, 10;
END;
$$ LANGUAGE plpgsql;

SELECT check_id, description, result,
       CASE WHEN result = 'PASS' THEN points ELSE 0 END AS earned
FROM verify_lab03()
ORDER BY check_id;
```

---

## Additional Requirement (20 pts)

Write a procedure `dept_report(p_dept_id INT)` that:
1. Raises an exception if `p_dept_id` doesn't exist
2. Uses a cursor to iterate over all students in the department
3. For each student, prints (via `RAISE NOTICE`): `student name | GPA | courses enrolled | most recent grade`
4. At the end, prints department summary: total students, avg GPA, highest GPA student name

---

## Submission Checklist

- [ ] Neon branch `lab-03` with all 4 procedures + 2 tables created
- [ ] All 4 procedures tested with the provided test calls (screenshots)
- [ ] `lab03_analysis.md` — answers to Part D questions
- [ ] `verify_lab03()` screenshot showing all PASS

---

## Grading

| Component | Points |
|-----------|--------|
| Part A — enroll_student (correct validation + exception handling) | 20 |
| Part B — assign_grade (grade conversion + audit log) | 25 |
| Part C — recalculate_all_gpas (cursor + gpa_history) | 25 |
| Part D — rollover_semester (exception handling + idempotency analysis) | 20 |
| Additional requirement — dept_report procedure | 20 |
| verify_lab03() all PASS | required |
| **Total** | **110** |
