---
title: "Lab 07: Query Execution Plans & Advanced Optimization"
course: ITEC-445
topic: Query Execution Plans & Advanced Optimization
week: 7
difficulty: ⭐⭐⭐⭐
estimated_time: 90 minutes
---

# Lab 07: Query Execution Plans & Advanced Optimization

| Field | Details |
|---|---|
| **Course** | ITEC-445 — Advanced Database Management |
| **Week** | 7 |
| **Difficulty** | ⭐⭐⭐⭐ Expert |
| **Estimated Time** | 90 minutes |
| **Topic** | Query Execution Plans & Advanced Optimization |
| **Prerequisites** | Lab 06 branch (500+ students, indexes in place) — use branch `lab-07` from `lab-06` |
| **Deliverables** | Rewritten queries, EXPLAIN ANALYZE comparisons, `verify_lab07()` PASS |

---

## Overview

Reading execution plans is the difference between guessing at performance problems and diagnosing them precisely. In this lab you will use `EXPLAIN ANALYZE` to decode PostgreSQL's query planner output, identify the eight most damaging SQL anti-patterns in the Frostburg database, and rewrite them for maximum performance. You will also use `pg_stat_statements` to find real slow queries.

---

!!! warning "Branch Requirement"
    Create branch **`lab-07`** from `lab-06` — you need the 500+ row dataset and indexes from Lab 06.

---

## Part A — Reading EXPLAIN ANALYZE Output (20 pts)

```sql
SET search_path = fsu;

-- Enable pg_stat_statements if available
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
```

Run this complex query and study every line of the plan:

```sql
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT
    d.dept_name,
    COUNT(DISTINCT s.student_id)   AS student_count,
    ROUND(AVG(s.gpa)::NUMERIC, 2)  AS avg_gpa,
    COUNT(e.enrollment_id)          AS total_enrollments,
    SUM(c.credits)                  AS total_credits
FROM departments d
LEFT JOIN students    s ON s.dept_id    = d.dept_id
LEFT JOIN enrollments e ON e.student_id = s.student_id AND e.semester = '2024FA'
LEFT JOIN courses     c ON c.course_id  = e.course_id
GROUP BY d.dept_id, d.dept_name
ORDER BY student_count DESC;
```

**In `lab07_analysis.md`, explain each of these fields from the plan output:**

| Field | What it means |
|-------|---------------|
| `Seq Scan` vs `Index Scan` vs `Bitmap Heap Scan` | |
| `cost=X..Y` | |
| `rows=N` (estimated) vs `actual rows=N` | |
| `loops=N` | |
| `Buffers: shared hit=N read=N` | |
| `Hash Join` vs `Nested Loop` vs `Merge Join` | |
| `Planning time` vs `Execution time` | |

---

## Part B — Identify & Fix SQL Anti-Patterns (50 pts)

Each anti-pattern below is a slow version of a query. For each:
1. Run `EXPLAIN ANALYZE` on the slow version
2. Rewrite it as the fast version
3. Run `EXPLAIN ANALYZE` on the fast version
4. Record the speedup

**B1 — Function in WHERE (defeats index):**
```sql
-- SLOW: index on email is unusable
EXPLAIN ANALYZE
SELECT * FROM students WHERE UPPER(email) = 'STUDENT1@FSU.EDU';

-- FAST: use functional index (from Lab 06) or match case
EXPLAIN ANALYZE
SELECT * FROM students WHERE email = 'student1@fsu.edu';
```

**B2 — Implicit type cast (defeats index):**
```sql
-- SLOW: enroll_year is INT but we compare to TEXT
EXPLAIN ANALYZE
SELECT * FROM students WHERE enroll_year = '2024';

-- FAST: use correct type
EXPLAIN ANALYZE
SELECT * FROM students WHERE enroll_year = 2024;
```

**B3 — SELECT * (over-fetches columns):**
```sql
-- SLOW: fetches all columns including large text fields
EXPLAIN ANALYZE
SELECT * FROM students
JOIN enrollments ON students.student_id = enrollments.student_id
WHERE enrollments.semester = '2024FA';

-- FAST: fetch only needed columns (covering index can satisfy this)
EXPLAIN ANALYZE
SELECT s.student_id, s.first_name, s.last_name, e.course_id, e.grade
FROM students s
JOIN enrollments e ON s.student_id = e.student_id
WHERE e.semester = '2024FA';
```

**B4 — Correlated subquery instead of JOIN:**
```sql
-- SLOW: correlated subquery executes once per row
EXPLAIN ANALYZE
SELECT student_id, first_name,
       (SELECT dept_name FROM departments WHERE dept_id = s.dept_id) AS dept
FROM students s
WHERE enroll_year >= 2022;

-- FAST: single JOIN
EXPLAIN ANALYZE
SELECT s.student_id, s.first_name, d.dept_name
FROM students s
JOIN departments d ON s.dept_id = d.dept_id
WHERE s.enroll_year >= 2022;
```

**B5 — DISTINCT instead of proper GROUP BY:**
```sql
-- SLOW: DISTINCT forces a sort of the entire result set
EXPLAIN ANALYZE
SELECT DISTINCT dept_id FROM students WHERE gpa >= 3.0;

-- FAST: GROUP BY with aggregation is more explicit and often faster
EXPLAIN ANALYZE
SELECT dept_id, COUNT(*) AS high_gpa_count FROM students WHERE gpa >= 3.0 GROUP BY dept_id;
```

---

## Part C — `pg_stat_statements` Analysis (20 pts)

`pg_stat_statements` tracks query statistics across all executions. Query it to find your most expensive queries:

```sql
-- Top 10 queries by total execution time
SELECT
    LEFT(query, 80)     AS query_preview,
    calls,
    ROUND(total_exec_time::NUMERIC, 2) AS total_ms,
    ROUND(mean_exec_time::NUMERIC, 2)  AS avg_ms,
    ROUND(stddev_exec_time::NUMERIC,2) AS stddev_ms,
    rows
FROM pg_stat_statements
WHERE query NOT LIKE '%pg_stat%'
ORDER BY total_exec_time DESC
LIMIT 10;
```

!!! info "Neon and pg_stat_statements"
    Neon supports `pg_stat_statements`. If it shows no rows, run a few queries first, then re-query. You may need to `RESET pg_stat_statements` and re-run your Lab B queries to populate it.

**In `lab07_analysis.md`:**
1. Which query had the highest `mean_exec_time`? Does that match your EXPLAIN analysis?
2. Which query was called the most times (`calls`)? Why might that matter even if avg_ms is low?
3. What does a high `stddev_exec_time` indicate?

---

## Part D — Query Rewrite Challenge (10 pts)

Rewrite this "report query" to run as fast as possible on the seeded data. You may add indexes if needed.

```sql
-- ORIGINAL (slow) — find all students enrolled in more courses than the average
SELECT s.student_id, s.first_name, s.last_name,
       COUNT(e.enrollment_id) AS course_count
FROM students s
JOIN enrollments e ON s.student_id = e.student_id
GROUP BY s.student_id, s.first_name, s.last_name
HAVING COUNT(e.enrollment_id) > (
    SELECT AVG(cnt) FROM (
        SELECT COUNT(*) AS cnt FROM enrollments GROUP BY student_id
    ) sub
)
ORDER BY course_count DESC;
```

**Your task:**
1. Run EXPLAIN ANALYZE on the original — record the plan
2. Rewrite using a CTE or window function to avoid the nested subquery
3. Run EXPLAIN ANALYZE on your rewrite — show improvement
4. Comment your rewrite explaining why it's faster

---

## Verification

```sql
SET search_path = fsu;

CREATE OR REPLACE FUNCTION verify_lab07()
RETURNS TABLE(check_id TEXT, description TEXT, result TEXT, points INT) AS $$
BEGIN
    RETURN QUERY SELECT '01', 'pg_stat_statements extension installed',
        CASE WHEN EXISTS(SELECT 1 FROM pg_extension WHERE extname='pg_stat_statements')
             THEN 'PASS' ELSE 'INFO' END, 5;

    RETURN QUERY SELECT '02', 'Students table still has 500+ rows',
        CASE WHEN (SELECT COUNT(*) FROM students) >= 500 THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '03', 'All Lab 06 indexes still present',
        CASE WHEN (SELECT COUNT(*) FROM pg_indexes WHERE schemaname='fsu'
                   AND indexname NOT LIKE '%pkey%') >= 4
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '04', 'Department query returns 5 rows',
        CASE WHEN (
            SELECT COUNT(*) FROM (
                SELECT d.dept_name, COUNT(s.student_id)
                FROM departments d LEFT JOIN students s ON s.dept_id=d.dept_id
                GROUP BY d.dept_id
            ) x
        ) = 5 THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '05', 'Email index used for lowercase lookup',
        CASE WHEN EXISTS(SELECT 1 FROM students WHERE LOWER(email) = 'student1@fsu.edu')
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '06', 'JOIN rewrite returns same count as correlated subquery',
        CASE WHEN (
            SELECT COUNT(*) FROM students s JOIN departments d ON s.dept_id=d.dept_id
            WHERE s.enroll_year >= 2022
        ) = (
            SELECT COUNT(*) FROM students s
            WHERE EXISTS(SELECT 1 FROM departments WHERE dept_id=s.dept_id)
            AND s.enroll_year >= 2022
        ) THEN 'PASS' ELSE 'FAIL' END, 15;

    RETURN QUERY SELECT '07', 'Rewritten avg-enrollment query returns results',
        CASE WHEN (
            WITH avg_enr AS (
                SELECT AVG(cnt) AS avg_cnt FROM (
                    SELECT COUNT(*) AS cnt FROM enrollments GROUP BY student_id
                ) x
            )
            SELECT COUNT(*) FROM (
                SELECT student_id, COUNT(*) AS course_count FROM enrollments
                GROUP BY student_id
                HAVING COUNT(*) > (SELECT avg_cnt FROM avg_enr)
            ) y
        ) > 0 THEN 'PASS' ELSE 'FAIL' END, 15;

    RETURN QUERY SELECT '08', 'Enrollments still intact after query rewrites',
        CASE WHEN (SELECT COUNT(*) FROM enrollments) >= 1000 THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '09', 'grade_points view accessible',
        CASE WHEN EXISTS(SELECT 1 FROM grade_points LIMIT 1) THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '10', 'Anti-pattern B4: JOIN faster than correlated subquery',
        CASE WHEN (SELECT COUNT(*) FROM students s JOIN departments d ON s.dept_id=d.dept_id
                   WHERE s.enroll_year >= 2022) > 0
             THEN 'PASS' ELSE 'FAIL' END, 5;
END;
$$ LANGUAGE plpgsql;

SELECT check_id, description, result,
       CASE WHEN result IN ('PASS','INFO') THEN points ELSE 0 END AS earned
FROM verify_lab07()
ORDER BY check_id;
```

---

## Additional Requirement (20 pts)

Write `lab07_optimization_report.md` — a mini consulting report for the Frostburg DB team:

1. **Executive Summary** (2–3 sentences): overall query health of the `fsu` schema
2. **Top 5 Anti-Patterns Found**: table with anti-pattern name, query, impact, fix applied
3. **Before/After Comparison Table**: all 5 queries with EXPLAIN times
4. **Index Recommendations**: any additional indexes you'd add beyond Lab 06
5. **One Query You Could NOT Optimize Further**: explain why (data volume, no better plan, optimizer already chose best path)

---

## Submission Checklist

- [ ] `lab07_analysis.md` — EXPLAIN field explanations + pg_stat_statements analysis
- [ ] `lab07_queries.sql` — all slow + fast versions of B1–B5, rewrite challenge
- [ ] `lab07_optimization_report.md` — additional requirement
- [ ] `verify_lab07()` screenshot — all PASS/INFO

---

## Grading

| Component | Points |
|-----------|--------|
| Part A — EXPLAIN field explanations (7 fields) | 20 |
| Part B — 5 anti-patterns fixed with EXPLAIN before/after | 50 |
| Part C — pg_stat_statements analysis (3 questions answered) | 20 |
| Part D — Query rewrite challenge (CTE/window rewrite) | 10 |
| Additional requirement — optimization report | 20 |
| **Total** | **120** |
