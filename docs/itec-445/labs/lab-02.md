---
title: "Lab 02: Window Functions, CTEs & Analytical Queries"
course: ITEC-445
topic: Window Functions, CTEs & Analytical Queries
week: 2
difficulty: ⭐⭐⭐
estimated_time: 80 minutes
---

# Lab 02: Window Functions, CTEs & Analytical Queries

| Field | Details |
|---|---|
| **Course** | ITEC-445 — Advanced Database Management |
| **Week** | 2 |
| **Difficulty** | ⭐⭐⭐ Advanced |
| **Estimated Time** | 80 minutes |
| **Topic** | Window Functions, CTEs & Analytical Queries |
| **Prerequisites** | Lab 01 complete, `fsu` schema populated on Neon |
| **Deliverables** | Queries on branch `lab-02`, `grade_points` view, `verify_lab02()` PASS |

---

## Overview

Window functions and CTEs unlock analytical patterns impossible with plain GROUP BY — ranking within groups, running totals, period-over-period comparisons, and recursive hierarchy traversal. This lab builds the analytical reporting layer for the Frostburg University database.

---

!!! warning "Branch Requirement"
    Create branch **`lab-02`** from `lab-01` (or re-run the Lab 01 setup SQL on a fresh branch). All work goes on `lab-02`.

---

## Part A — Setup: grade_points View & Semester Data

```sql
SET search_path = fsu;

-- grade_points helper view
CREATE OR REPLACE VIEW grade_points AS
SELECT e.enrollment_id, e.student_id, e.course_id, e.semester, e.grade,
       CASE e.grade
           WHEN 'A'  THEN 4.0  WHEN 'A-' THEN 3.7
           WHEN 'B+' THEN 3.3  WHEN 'B'  THEN 3.0
           WHEN 'B-' THEN 2.7  WHEN 'C+' THEN 2.3
           WHEN 'C'  THEN 2.0  WHEN 'C-' THEN 1.7
           WHEN 'D+' THEN 1.3  WHEN 'D'  THEN 1.0
           WHEN 'F'  THEN 0.0  ELSE NULL
       END AS points
FROM enrollments e;

-- Add a second semester for time-series analysis
INSERT INTO enrollments (student_id, course_id, semester, grade) VALUES
    (1, 3, '2024SP', 'A'),   (1, 4, '2024SP', 'B+'),
    (2, 3, '2024SP', 'B-'),  (2, 4, '2024SP', 'C'),
    (3, 9, '2024SP', 'A'),   (5, 3, '2024SP', 'A-'),
    (5, 9, '2024SP', 'B+'),  (8, 9, '2024SP', 'A'),
    (9, 3, '2024SP', 'C+'),  (12,4, '2024SP', 'B+');

-- Dept hierarchy table for recursive CTE
CREATE TABLE IF NOT EXISTS dept_hierarchy (
    node_id   INT PRIMARY KEY,
    node_name VARCHAR(100),
    parent_id INT REFERENCES dept_hierarchy(node_id)
);
INSERT INTO dept_hierarchy VALUES
    (1, 'Frostburg State University', NULL),
    (2, 'College of Liberal Arts', 1),
    (3, 'College of Science', 1),
    (4, 'Computer Science', 3),
    (5, 'Mathematics', 3),
    (6, 'Physics', 3),
    (7, 'English', 2),
    (8, 'History', 2);
```

---

## Part B — Ranking Window Functions (25 pts)

**B1.** Rank all students by GPA within each department using `RANK()`. Show `dept_name`, `full_name`, `gpa`, `rank_in_dept`. Students with NULL GPA should appear last (`NULLS LAST`).

**B2.** Using `DENSE_RANK()`, rank all courses by total number of 2024FA enrollments. Show `course_code`, `title`, `enrollment_count`, `dense_rank`.

**B3.** Using `NTILE(4)`, divide all students (with non-NULL GPA) into 4 quartiles. Show `full_name`, `gpa`, `quartile`. Label quartile 4 as the top performers.

**B4.** Using `ROW_NUMBER()`, assign each enrollment a sequential number within each student, ordered by semester then course_id. Show `student_id`, `row_num`, `course_code`, `semester`.

---

## Part C — Aggregate Window Functions (25 pts)

**C1.** Running total: For each student ordered by enrollment_id, show each enrollment and the running count of courses taken so far: `student_id`, `course_code`, `semester`, `running_course_count`.

**C2.** Moving average: For each department (ordered by dept_id), compute a 3-row centered moving average of instructor salaries using `AVG(salary) OVER (ORDER BY dept_id ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING)`.

**C3.** Cumulative GPA: For each student in the CS department, show semester-by-semester cumulative average grade points using `AVG(points) OVER (PARTITION BY student_id ORDER BY semester ROWS UNBOUNDED PRECEDING)`.

**C4.** Percent of total: For each department, show total student count and what percentage of all students that represents. Use `SUM(COUNT(*)) OVER ()` as the window denominator.

---

## Part D — LAG / LEAD & Row Comparisons (20 pts)

**D1.** Semester-over-semester GPA change: For each student who has enrollments in both `2024SP` and `2024FA`, compute their average grade points per semester, then use `LAG()` to show the previous semester's average and the change. Columns: `student_id`, `semester`, `avg_points`, `prev_avg`, `change`.

**D2.** Next enrollment: For each enrollment row, show the next course the same student enrolled in (ordered by semester, course_id). Use `LEAD(course_id)` and join back to get the `course_code`.

---

## Part E — CTEs & Recursive Queries (20 pts)

**E1.** Non-recursive CTE: Using a CTE, find the top student (by GPA) in each department, then join to show the instructor with the highest salary in the same department. Present as a "department champion" report.

**E2.** Multi-CTE: Write a query with two CTEs — `dept_stats` (avg GPA, student count per dept) and `course_stats` (enrollment count, avg grade points per course) — then join them to departments to produce a single department health report.

**E3.** Recursive CTE: Traverse the `dept_hierarchy` table to produce a full indented org chart. Each row should show the path from root to node:

```
Frostburg State University
  College of Science
    Computer Science
    Mathematics
    Physics
  College of Liberal Arts
    English
    History
```

Use `WITH RECURSIVE` and `LPAD('', depth*2, ' ') || node_name` for indentation.

---

## Part F — PIVOT with CASE WHEN (10 pts)

**F1.** PIVOT report: Using conditional aggregation, produce a semester-by-department enrollment matrix. Rows = departments, Columns = `2024SP`, `2024FA`, `total`. Use `SUM(CASE WHEN semester = '2024SP' THEN 1 ELSE 0 END)`.

---

## Verification

```sql
SET search_path = fsu;

CREATE OR REPLACE FUNCTION verify_lab02()
RETURNS TABLE(check_id TEXT, description TEXT, result TEXT, points INT) AS $$
BEGIN
    -- Check 1: grade_points view exists
    RETURN QUERY SELECT '01', 'grade_points view exists',
        CASE WHEN EXISTS(SELECT 1 FROM information_schema.views
                         WHERE table_schema='fsu' AND table_name='grade_points')
             THEN 'PASS' ELSE 'FAIL' END, 10;

    -- Check 2: grade_points returns points for grade A = 4.0
    RETURN QUERY SELECT '02', 'grade A maps to 4.0 points',
        CASE WHEN EXISTS(SELECT 1 FROM grade_points WHERE grade='A' AND points=4.0)
             THEN 'PASS' ELSE 'FAIL' END, 10;

    -- Check 3: dept_hierarchy table has 8 rows
    RETURN QUERY SELECT '03', 'dept_hierarchy has 8 rows',
        CASE WHEN (SELECT COUNT(*) FROM dept_hierarchy) = 8
             THEN 'PASS' ELSE 'FAIL' END, 10;

    -- Check 4: 2024SP semester enrollments exist (10 rows added)
    RETURN QUERY SELECT '04', '2024SP enrollments exist',
        CASE WHEN (SELECT COUNT(*) FROM enrollments WHERE semester='2024SP') >= 10
             THEN 'PASS' ELSE 'FAIL' END, 10;

    -- Check 5: RANK() - top student per dept returns correct count
    RETURN QUERY SELECT '05', 'Ranking query returns one top student per dept',
        CASE WHEN (
            SELECT COUNT(*) FROM (
                SELECT dept_id, RANK() OVER (PARTITION BY dept_id ORDER BY gpa DESC NULLS LAST) AS rnk
                FROM students WHERE gpa IS NOT NULL
            ) r WHERE rnk = 1
        ) >= 4 THEN 'PASS' ELSE 'FAIL' END, 10;

    -- Check 6: Recursive CTE root node is accessible
    RETURN QUERY SELECT '06', 'Recursive CTE root node accessible',
        CASE WHEN EXISTS(SELECT 1 FROM dept_hierarchy WHERE parent_id IS NULL)
             THEN 'PASS' ELSE 'FAIL' END, 10;

    -- Check 7: grade_points NULL for NULL grade
    RETURN QUERY SELECT '07', 'NULL grade maps to NULL points',
        CASE WHEN NOT EXISTS(SELECT 1 FROM grade_points WHERE grade IS NULL AND points IS NOT NULL)
             THEN 'PASS' ELSE 'FAIL' END, 10;

    -- Check 8: Lena Adams has enrollments in both semesters
    RETURN QUERY SELECT '08', 'Student 1 enrolled in 2 semesters',
        CASE WHEN (SELECT COUNT(DISTINCT semester) FROM enrollments WHERE student_id=1) >= 2
             THEN 'PASS' ELSE 'FAIL' END, 10;

    -- Check 9: Total enrollments now >= 32
    RETURN QUERY SELECT '09', 'Total enrollments >= 32 after seed',
        CASE WHEN (SELECT COUNT(*) FROM enrollments) >= 32
             THEN 'PASS' ELSE 'FAIL' END, 10;

    -- Check 10: NTILE(4) would produce 4 quartiles
    RETURN QUERY SELECT '10', 'NTILE(4) on students produces 4 groups',
        CASE WHEN (
            SELECT COUNT(DISTINCT NTILE(4) OVER (ORDER BY gpa))
            FROM students WHERE gpa IS NOT NULL
        ) = 4 THEN 'PASS' ELSE 'FAIL' END, 10;
END;
$$ LANGUAGE plpgsql;

SELECT check_id, description, result,
       CASE WHEN result = 'PASS' THEN points ELSE 0 END AS earned
FROM verify_lab02()
ORDER BY check_id;
```

---

## Additional Requirement (20 pts)

Write `lab02_cohort.sql` — a **cohort retention analysis**:

> For each enrollment year (`enroll_year`) of students, compute how many enrolled in `2024SP` and how many enrolled in `2024FA`. Show the retention rate (FA enrollees / SP enrollees as a percentage). Use CTEs and window functions.

---

## Submission Checklist

- [ ] Neon branch `lab-02` with all setup SQL executed
- [ ] `lab02_ranking.sql` — Part B queries
- [ ] `lab02_aggregate.sql` — Part C queries
- [ ] `lab02_lag_lead.sql` — Part D queries
- [ ] `lab02_cte.sql` — Part E queries (including recursive)
- [ ] `lab02_pivot.sql` — Part F query
- [ ] `lab02_cohort.sql` — additional requirement
- [ ] `SELECT * FROM verify_lab02()` screenshot showing all PASS

---

## Grading

| Component | Points |
|-----------|--------|
| Part B — Ranking window functions (4 queries) | 25 |
| Part C — Aggregate window functions (4 queries) | 25 |
| Part D — LAG/LEAD comparisons (2 queries) | 20 |
| Part E — CTEs + recursive CTE (3 queries) | 20 |
| Part F — PIVOT with CASE WHEN | 10 |
| Additional requirement — cohort analysis | 20 |
| **Total** | **120** |
