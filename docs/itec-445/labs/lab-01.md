---
title: "Lab 01: Advanced SQL — Joins, Subqueries & Set Operations"
course: ITEC-445
topic: Advanced SQL — Joins, Subqueries & Set Operations
week: 1
difficulty: ⭐⭐
estimated_time: 75 minutes
---

# Lab 01: Advanced SQL — Joins, Subqueries & Set Operations

| Field | Details |
|---|---|
| **Course** | ITEC-445 — Advanced Database Management |
| **Week** | 1 |
| **Difficulty** | ⭐⭐ Intermediate |
| **Estimated Time** | 75 minutes |
| **Topic** | Advanced SQL: Joins, Subqueries & Set Operations |
| **Prerequisites** | Neon account, `psql` installed locally |
| **Deliverables** | All queries running on Neon branch `lab-01`, verification script PASS |

---

## Overview

This lab exercises every JOIN type, all subquery forms, and the full set of PostgreSQL set operations against the Frostburg University database. By the end you will be able to write production-quality analytical queries across multi-table schemas.

---

!!! warning "Branch Requirement"
    Create a Neon branch named **`lab-01`** before starting. All work must be done on this branch.

!!! info "Neon Connection"
    Log in at [https://neon.tech](https://neon.tech) → your project → **Connection Details** → copy the connection string.
    ```bash
    export DATABASE_URL="postgresql://user:***@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require"
    psql "$DATABASE_URL"
    ```

---

## Part A — Schema Setup (run once on your branch)

```sql
-- Frostburg University schema — used in every ITEC-445 lab
CREATE SCHEMA IF NOT EXISTS fsu;
SET search_path = fsu;

CREATE TABLE departments (
    dept_id   SERIAL       PRIMARY KEY,
    dept_name VARCHAR(100) NOT NULL,
    building  VARCHAR(50),
    budget    NUMERIC(12,2)
);

CREATE TABLE instructors (
    instructor_id SERIAL       PRIMARY KEY,
    first_name    VARCHAR(50)  NOT NULL,
    last_name     VARCHAR(50)  NOT NULL,
    email         VARCHAR(100) UNIQUE,
    dept_id       INT          REFERENCES departments(dept_id),
    hire_date     DATE,
    salary        NUMERIC(10,2)
);

CREATE TABLE courses (
    course_id   SERIAL      PRIMARY KEY,
    course_code VARCHAR(10) NOT NULL UNIQUE,
    title       VARCHAR(150) NOT NULL,
    credits     SMALLINT    NOT NULL DEFAULT 3,
    dept_id     INT         REFERENCES departments(dept_id)
);

CREATE TABLE students (
    student_id  SERIAL       PRIMARY KEY,
    first_name  VARCHAR(50)  NOT NULL,
    last_name   VARCHAR(50)  NOT NULL,
    email       VARCHAR(100) UNIQUE,
    gpa         NUMERIC(3,2) CHECK (gpa BETWEEN 0 AND 4),
    dept_id     INT          REFERENCES departments(dept_id),
    enroll_year SMALLINT
);

CREATE TABLE enrollments (
    enrollment_id SERIAL  PRIMARY KEY,
    student_id    INT     NOT NULL REFERENCES students(student_id),
    course_id     INT     NOT NULL REFERENCES courses(course_id),
    semester      VARCHAR(10) NOT NULL,  -- e.g. '2024FA'
    grade         VARCHAR(2),
    UNIQUE (student_id, course_id, semester)
);

-- Seed data
INSERT INTO departments (dept_name, building, budget) VALUES
    ('Computer Science', 'Cordts Hall', 850000),
    ('Mathematics',      'Compton Hall', 620000),
    ('Biology',          'Lowndes Hall', 740000),
    ('English',          'Gunter Hall',  480000),
    ('Physics',          'Compton Hall', 590000);

INSERT INTO instructors (first_name, last_name, email, dept_id, hire_date, salary) VALUES
    ('Alice',  'Wang',    'awang@frostburg.edu',   1, '2015-08-15', 95000),
    ('Bob',    'Carter',  'bcarter@frostburg.edu', 1, '2018-01-10', 88000),
    ('Carol',  'Liu',     'cliu@frostburg.edu',    2, '2012-08-20', 92000),
    ('David',  'Patel',   'dpatel@frostburg.edu',  3, '2020-08-25', 82000),
    ('Eve',    'Johnson', 'ejohnson@frostburg.edu',4, '2010-08-01', 78000),
    ('Frank',  'Kim',     'fkim@frostburg.edu',    5, '2017-01-15', 91000),
    ('Grace',  'Torres',  'gtorres@frostburg.edu', 1, '2022-08-18', 80000),
    ('Henry',  'Brown',   'hbrown@frostburg.edu',  2, '2019-08-12', 85000);

INSERT INTO courses (course_code, title, credits, dept_id) VALUES
    ('ITEC445', 'Advanced Database Management', 3, 1),
    ('ITEC320', 'Database Systems I',           3, 1),
    ('MATH301', 'Linear Algebra',               3, 2),
    ('MATH201', 'Calculus II',                  4, 2),
    ('BIOL201', 'Cell Biology',                 4, 3),
    ('ENGL210', 'Technical Writing',            3, 4),
    ('PHYS301', 'Quantum Mechanics',            3, 5),
    ('ITEC410', 'Networks & Security',          3, 1),
    ('MATH402', 'Abstract Algebra',             3, 2),
    ('BIOL350', 'Genetics',                     3, 3);

INSERT INTO students (first_name, last_name, email, gpa, dept_id, enroll_year) VALUES
    ('Lena',   'Adams',   'ladams@student.fsu.edu',  3.85, 1, 2022),
    ('Marcus', 'Bell',    'mbell@student.fsu.edu',   2.90, 1, 2021),
    ('Nina',   'Cruz',    'ncruz@student.fsu.edu',   3.60, 2, 2023),
    ('Omar',   'Davis',   'odavis@student.fsu.edu',  1.75, 3, 2020),
    ('Piper',  'Evans',   'pevans@student.fsu.edu',  3.95, 1, 2022),
    ('Quinn',  'Ford',    'qford@student.fsu.edu',   2.40, 4, 2021),
    ('Rosa',   'Garcia',  'rgarcia@student.fsu.edu', 3.10, 5, 2023),
    ('Sam',    'Harris',  'sharris@student.fsu.edu', 3.50, 2, 2022),
    ('Tara',   'Ingram',  'tingram@student.fsu.edu', 2.80, 1, 2021),
    ('Umar',   'Jackson', 'ujackson@student.fsu.edu',3.70, 3, 2022),
    ('Vera',   'Klein',   'vklein@student.fsu.edu',  NULL, 1, 2023),
    ('Will',   'Lopez',   'wlopez@student.fsu.edu',  3.20, 2, 2022);

INSERT INTO enrollments (student_id, course_id, semester, grade) VALUES
    (1, 1, '2024FA', 'A'),   (1, 2, '2024FA', 'A-'),
    (2, 1, '2024FA', 'B'),   (2, 8, '2024FA', 'C+'),
    (3, 3, '2024FA', 'A'),   (3, 4, '2024FA', 'B+'),
    (4, 5, '2024FA', 'D'),   (4, 10,'2024FA', 'F'),
    (5, 1, '2024FA', 'A'),   (5, 8, '2024FA', 'A-'),
    (6, 6, '2024FA', 'B-'),
    (7, 7, '2024FA', 'B+'),  (7, 3, '2024FA', 'A-'),
    (8, 3, '2024FA', 'A'),   (8, 4, '2024FA', 'A-'),
    (9, 1, '2024FA', 'C'),   (9, 2, '2024FA', 'B'),
    (10,5, '2024FA', 'B+'),  (10,10,'2024FA', 'A'),
    (11,1, '2024FA', NULL),  -- enrolled, not yet graded
    (12,3, '2024FA', 'B'),   (12,9, '2024FA', 'A');
```

---

## Part B — JOIN Exercises (40 pts)

Write and save each query in a file `lab01_joins.sql`. Run each against your Neon branch.

**B1.** List every student with their department name. Include students with no department (use `LEFT JOIN`).

**B2.** List every course with the instructor's full name (`first_name || ' ' || last_name`). Include courses with no instructor assigned (`LEFT JOIN instructors` on `dept_id`).

**B3.** Find all pairs of students enrolled in the **same course in the same semester** (SELF JOIN on `enrollments`). Show `student_a_id`, `student_b_id`, `course_code`. Exclude mirror pairs (A,B) and (B,A) — use `e1.student_id < e2.student_id`.

**B4.** FULL OUTER JOIN: Show all departments and all students, matched where possible. Display `dept_name`, `student first+last`, `gpa`. Rows with no match on either side should appear with NULLs.

**B5.** CROSS JOIN: Generate all possible (student, course) pairs for students in dept 1 and courses in dept 1. How many combinations are there?

---

## Part C — Subquery Exercises (35 pts)

**C1.** Scalar subquery: For each student, show their GPA and how much it differs from the overall average GPA. Column: `gpa_vs_avg`.

**C2.** Correlated subquery: List students whose GPA is higher than the average GPA of **their own department**.

**C3.** EXISTS: Find courses that have at least one enrollment with a NULL grade (students enrolled but not yet graded).

**C4.** NOT EXISTS: Find students who are enrolled in zero courses in semester `2024FA`.

**C5.** IN with subquery: List all courses taken by students in the Computer Science department (`dept_id = 1`). Use `IN` with a subquery — then rewrite it using a `JOIN` and compare.

---

## Part D — Set Operations (15 pts)

**D1.** `UNION ALL`: Combine first and last names of all instructors and all students into one result set with column `full_name` and `type` ('instructor' or 'student').

**D2.** `INTERSECT`: Find `dept_id` values that appear in **both** the `instructors` table and the `students` table (departments that have both faculty and enrolled students).

**D3.** `EXCEPT`: Find `dept_id` values in `departments` that have **no courses** assigned to them.

---

## Part E — Advanced Patterns (10 pts)

**E1.** Top-N per group: Show the **top 2 students by GPA** for each department. Use a subquery or window function (preview of Lab 02).

**E2.** Gap analysis: Find `dept_id` values from 1 to 5 that are missing from the `students` table (departments with zero students enrolled). Use `EXCEPT` or `NOT IN`.

---

## Verification

Create and run this on your `lab-01` branch:

```sql
SET search_path = fsu;

CREATE OR REPLACE FUNCTION verify_lab01()
RETURNS TABLE(check_id TEXT, description TEXT, result TEXT, points INT) AS $$
BEGIN
    -- Check 1: departments table has 5 rows
    RETURN QUERY SELECT '01', 'departments has 5 rows',
        CASE WHEN (SELECT COUNT(*) FROM departments) = 5 THEN 'PASS' ELSE 'FAIL' END, 10;

    -- Check 2: students table has 12 rows
    RETURN QUERY SELECT '02', 'students has 12 rows',
        CASE WHEN (SELECT COUNT(*) FROM students) = 12 THEN 'PASS' ELSE 'FAIL' END, 10;

    -- Check 3: enrollments table has 22 rows
    RETURN QUERY SELECT '03', 'enrollments has 22 rows',
        CASE WHEN (SELECT COUNT(*) FROM enrollments) = 22 THEN 'PASS' ELSE 'FAIL' END, 10;

    -- Check 4: student Vera Klein has NULL GPA
    RETURN QUERY SELECT '04', 'Vera Klein has NULL GPA',
        CASE WHEN EXISTS(SELECT 1 FROM students WHERE last_name='Klein' AND gpa IS NULL)
             THEN 'PASS' ELSE 'FAIL' END, 10;

    -- Check 5: ITEC445 has 5 enrollments in 2024FA
    RETURN QUERY SELECT '05', 'ITEC445 has 5 enrollments in 2024FA',
        CASE WHEN (
            SELECT COUNT(*) FROM enrollments e
            JOIN courses c ON e.course_id = c.course_id
            WHERE c.course_code = 'ITEC445' AND e.semester = '2024FA'
        ) = 5 THEN 'PASS' ELSE 'FAIL' END, 10;

    -- Check 6: student with highest GPA is Piper Evans (3.95)
    RETURN QUERY SELECT '06', 'Highest GPA student is Piper Evans',
        CASE WHEN (
            SELECT last_name FROM students ORDER BY gpa DESC NULLS LAST LIMIT 1
        ) = 'Evans' THEN 'PASS' ELSE 'FAIL' END, 10;

    -- Check 7: dept 4 (English) has no students
    RETURN QUERY SELECT '07', 'English dept has 1 student (Quinn Ford)',
        CASE WHEN (SELECT COUNT(*) FROM students WHERE dept_id = 4) = 1
             THEN 'PASS' ELSE 'FAIL' END, 10;

    -- Check 8: correlated subquery returns students above dept avg
    RETURN QUERY SELECT '08', 'Above-dept-avg students query returns rows',
        CASE WHEN (
            SELECT COUNT(*) FROM students s
            WHERE gpa > (SELECT AVG(gpa) FROM students s2 WHERE s2.dept_id = s.dept_id)
        ) > 0 THEN 'PASS' ELSE 'FAIL' END, 10;

    -- Check 9: INTERSECT of dept_ids in instructors and students returns 4 depts
    RETURN QUERY SELECT '09', 'INTERSECT of instructor/student depts returns 4+',
        CASE WHEN (
            SELECT COUNT(*) FROM (
                SELECT dept_id FROM instructors
                INTERSECT
                SELECT dept_id FROM students
            ) x
        ) >= 4 THEN 'PASS' ELSE 'FAIL' END, 10;

    -- Check 10: grade_points view can be created
    RETURN QUERY SELECT '10', 'grade_points view exists or can be created',
        CASE WHEN EXISTS(
            SELECT 1 FROM information_schema.views
            WHERE table_schema = 'fsu' AND table_name = 'grade_points'
        ) THEN 'PASS' ELSE 'NEEDS_VIEW' END, 10;
END;
$$ LANGUAGE plpgsql;

SELECT check_id, description, result,
       CASE WHEN result = 'PASS' THEN points ELSE 0 END AS earned
FROM verify_lab01()
ORDER BY check_id;
```

**All 10 checks must show PASS to receive full credit.**

---

## Additional Requirement (20 pts)

Write a single query `lab01_bonus.sql` that answers:

> **"For each department, show the department name, number of students, average GPA (rounded to 2 decimal places), and the name of the highest-paid instructor in that department — even for departments that have no students or no instructors."**

This requires at least one JOIN, one subquery, one aggregate function, and `COALESCE` or `LEFT JOIN` to handle missing data gracefully.

---

## Submission Checklist

- [ ] Neon branch `lab-01` exists with `fsu` schema populated
- [ ] `lab01_joins.sql` — B1–B5 queries
- [ ] `lab01_subqueries.sql` — C1–C5 queries
- [ ] `lab01_sets.sql` — D1–D3 queries
- [ ] `lab01_advanced.sql` — E1–E2 queries
- [ ] `lab01_bonus.sql` — additional requirement query
- [ ] `SELECT * FROM verify_lab01()` screenshot showing all PASS

---

## Grading

| Component | Points |
|-----------|--------|
| Part B — JOIN queries (5 queries, correct results) | 40 |
| Part C — Subquery queries (5 queries, correct results) | 35 |
| Part D — Set operation queries (3 queries) | 15 |
| Part E — Advanced patterns (2 queries) | 10 |
| Additional requirement — department summary query | 20 |
| verify_lab01() all PASS | required |
| **Total** | **120** |
