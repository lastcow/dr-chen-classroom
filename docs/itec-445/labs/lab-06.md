---
title: "Lab 06: Index Design & Query Performance"
course: ITEC-445
topic: Index Design & Query Performance
week: 6
difficulty: ⭐⭐⭐
estimated_time: 85 minutes
---

# Lab 06: Index Design & Query Performance

| Field | Details |
|---|---|
| **Course** | ITEC-445 — Advanced Database Management |
| **Week** | 6 |
| **Difficulty** | ⭐⭐⭐ Advanced |
| **Estimated Time** | 85 minutes |
| **Topic** | Index Design & Query Performance |
| **Prerequisites** | Lab 01 schema on Neon branch `lab-06`, 500+ rows of data (seed script below) |
| **Deliverables** | Indexes created, `EXPLAIN` outputs captured, `verify_lab06()` PASS |

---

## Overview

Indexes are the single most impactful performance lever available to a database developer — a well-designed index can reduce query cost from a full sequential scan (O(n)) to a B-tree lookup (O(log n)). In this lab you will bulk-seed the Frostburg database with realistic data, diagnose slow queries using `EXPLAIN ANALYZE`, design indexes to fix them, and document the before/after performance difference.

---

!!! warning "Branch Requirement"
    Create branch **`lab-06`** with Lab 01 schema. Then run the bulk seed script below to get enough data for meaningful index analysis.

---

## Part A — Bulk Data Seed (run once)

```sql
SET search_path = fsu;

-- Generate 500 students using generate_series
INSERT INTO students (first_name, last_name, email, gpa, dept_id, enroll_year)
SELECT
    'Student' || g,
    'Last' || g,
    'student' || g || '@fsu.edu',
    ROUND((RANDOM() * 3.5 + 0.5)::NUMERIC, 2),
    (g % 5) + 1,   -- dept_id 1-5 cycling
    2018 + (g % 7)
FROM generate_series(1, 500) g
ON CONFLICT (email) DO NOTHING;

-- Generate enrollments: ~3 enrollments per student across 10 courses
INSERT INTO enrollments (student_id, course_id, semester, grade)
SELECT
    s.student_id,
    (g % 10) + 1,
    CASE (g % 4) WHEN 0 THEN '2024FA' WHEN 1 THEN '2024SP'
                 WHEN 2 THEN '2023FA' ELSE '2023SP' END,
    (ARRAY['A','A-','B+','B','B-','C+','C','C-','D','F'])[floor(RANDOM()*10)+1]
FROM students s
CROSS JOIN generate_series(1, 4) g
WHERE s.student_id > 12  -- skip original seed students
ON CONFLICT (student_id, course_id, semester) DO NOTHING;

SELECT 'Students: ' || COUNT(*) FROM students;
SELECT 'Enrollments: ' || COUNT(*) FROM enrollments;
```

You should have ~500 students and ~1500 enrollments.

---

## Part B — Baseline: Queries Without Indexes (20 pts)

First, drop any non-primary-key indexes to get a clean baseline:

```sql
-- Check existing indexes
SELECT indexname, indexdef FROM pg_indexes
WHERE schemaname = 'fsu' AND tablename IN ('students','enrollments','courses')
AND indexname NOT LIKE '%pkey%';
```

Run each query with `EXPLAIN ANALYZE` and record the results in `lab06_analysis.md`:

**B1.** Find all students in the Computer Science department:
```sql
EXPLAIN ANALYZE
SELECT student_id, first_name, last_name, gpa
FROM fsu.students
WHERE dept_id = 1
ORDER BY last_name;
```

**B2.** Find all enrollments for a specific student:
```sql
EXPLAIN ANALYZE
SELECT e.enrollment_id, c.course_code, e.semester, e.grade
FROM fsu.enrollments e
JOIN fsu.courses c ON e.course_id = c.course_id
WHERE e.student_id = 5;
```

**B3.** Find students by GPA range:
```sql
EXPLAIN ANALYZE
SELECT student_id, first_name, gpa
FROM fsu.students
WHERE gpa BETWEEN 3.5 AND 4.0
ORDER BY gpa DESC;
```

**B4.** Enrollment count per course per semester:
```sql
EXPLAIN ANALYZE
SELECT course_id, semester, COUNT(*) AS enrollment_count
FROM fsu.enrollments
WHERE semester = '2024FA'
GROUP BY course_id, semester
ORDER BY enrollment_count DESC;
```

Record for each: **plan type** (Seq Scan vs Index Scan), **rows estimated**, **actual time**.

---

## Part C — Add Indexes (30 pts)

Design and create indexes to fix each slow query:

**C1.** Single-column index for department lookup:
```sql
CREATE INDEX idx_students_dept_id ON fsu.students(dept_id);
EXPLAIN ANALYZE
SELECT student_id, first_name, last_name, gpa FROM fsu.students WHERE dept_id = 1 ORDER BY last_name;
```

**C2.** Covering index for enrollment lookups (avoid table heap access):
```sql
-- This index lets the query be satisfied entirely from the index
CREATE INDEX idx_enrollments_student ON fsu.enrollments(student_id)
    INCLUDE (course_id, semester, grade);

EXPLAIN ANALYZE
SELECT e.enrollment_id, e.course_id, e.semester, e.grade
FROM fsu.enrollments e
WHERE e.student_id = 5;
```

**C3.** Partial index for high-GPA students (only indexes rows we actually query):
```sql
-- Only indexes the ~10% of students with GPA >= 3.5
CREATE INDEX idx_students_high_gpa ON fsu.students(gpa DESC)
    WHERE gpa >= 3.5;

EXPLAIN ANALYZE
SELECT student_id, first_name, gpa FROM fsu.students WHERE gpa BETWEEN 3.5 AND 4.0 ORDER BY gpa DESC;
```

**C4.** Composite index for enrollment analytics:
```sql
-- Leftmost prefix: semester first (high cardinality filter)
CREATE INDEX idx_enrollments_semester_course ON fsu.enrollments(semester, course_id);

EXPLAIN ANALYZE
SELECT course_id, semester, COUNT(*) FROM fsu.enrollments WHERE semester='2024FA'
GROUP BY course_id, semester ORDER BY COUNT(*) DESC;
```

**For each index:** Record the new plan type and execution time. Compute the speedup ratio.

---

## Part D — Index Inspection (20 pts)

**D1.** Query `pg_indexes` and `pg_stat_user_indexes` to inventory all indexes:

```sql
SELECT
    i.indexname,
    i.tablename,
    i.indexdef,
    s.idx_scan       AS times_used,
    s.idx_tup_read   AS tuples_read,
    s.idx_tup_fetch  AS tuples_fetched,
    pg_size_pretty(pg_relation_size(i.indexrelid)) AS index_size
FROM pg_indexes i
JOIN pg_stat_user_indexes s ON i.indexname = s.indexname
WHERE i.schemaname = 'fsu'
ORDER BY s.idx_scan DESC;
```

**D2.** Identify bloated or unused indexes:
```sql
-- Indexes with 0 scans since last stats reset
SELECT indexname, tablename, idx_scan
FROM pg_stat_user_indexes
WHERE schemaname = 'fsu' AND idx_scan = 0;
```

**Answer in `lab06_analysis.md`:**
- Which indexes have been used (idx_scan > 0) after your `EXPLAIN ANALYZE` runs?
- How large is each index relative to the table it indexes?

**D3.** Demonstrate the leftmost prefix rule. Explain why this query **does NOT** use `idx_enrollments_semester_course`:
```sql
EXPLAIN ANALYZE
SELECT * FROM fsu.enrollments WHERE course_id = 3;  -- course_id is 2nd column in index
```

---

## Part E — Functional Index (15 pts)

**E1.** Email lookup is case-insensitive. A regular index won't help `WHERE LOWER(email) = 'x'`. Create a functional index:

```sql
CREATE INDEX idx_students_email_lower ON fsu.students(LOWER(email));

-- Now this query uses the index:
EXPLAIN ANALYZE
SELECT * FROM fsu.students WHERE LOWER(email) = 'student1@fsu.edu';
```

**E2.** Index on enrollment year for recent-year filtering:
```sql
CREATE INDEX idx_students_enroll_year ON fsu.students(enroll_year)
    WHERE enroll_year >= 2022;

EXPLAIN ANALYZE
SELECT COUNT(*) FROM fsu.students WHERE enroll_year >= 2022;
```

---

## Verification

```sql
SET search_path = fsu;

CREATE OR REPLACE FUNCTION verify_lab06()
RETURNS TABLE(check_id TEXT, description TEXT, result TEXT, points INT) AS $$
BEGIN
    RETURN QUERY SELECT '01', 'students table has 500+ rows',
        CASE WHEN (SELECT COUNT(*) FROM students) >= 500 THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '02', 'enrollments table has 1000+ rows',
        CASE WHEN (SELECT COUNT(*) FROM enrollments) >= 1000 THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '03', 'idx_students_dept_id exists',
        CASE WHEN EXISTS(SELECT 1 FROM pg_indexes WHERE indexname='idx_students_dept_id' AND schemaname='fsu')
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '04', 'idx_enrollments_student exists',
        CASE WHEN EXISTS(SELECT 1 FROM pg_indexes WHERE indexname='idx_enrollments_student' AND schemaname='fsu')
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '05', 'idx_students_high_gpa partial index exists',
        CASE WHEN EXISTS(SELECT 1 FROM pg_indexes WHERE indexname='idx_students_high_gpa' AND schemaname='fsu')
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '06', 'idx_enrollments_semester_course exists',
        CASE WHEN EXISTS(SELECT 1 FROM pg_indexes WHERE indexname='idx_enrollments_semester_course' AND schemaname='fsu')
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '07', 'idx_students_email_lower functional index exists',
        CASE WHEN EXISTS(SELECT 1 FROM pg_indexes WHERE indexname='idx_students_email_lower' AND schemaname='fsu')
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '08', 'At least 4 non-PK indexes on fsu tables',
        CASE WHEN (SELECT COUNT(*) FROM pg_indexes WHERE schemaname='fsu'
                   AND indexname NOT LIKE '%pkey%') >= 4
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '09', 'High-GPA partial index covers correct range',
        CASE WHEN (SELECT COUNT(*) FROM students WHERE gpa >= 3.5) > 0
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '10', 'Functional index: email lookup works',
        CASE WHEN EXISTS(SELECT 1 FROM students WHERE LOWER(email) = 'student1@fsu.edu')
             THEN 'PASS' ELSE 'FAIL' END, 10;
END;
$$ LANGUAGE plpgsql;

SELECT check_id, description, result,
       CASE WHEN result = 'PASS' THEN points ELSE 0 END AS earned
FROM verify_lab06()
ORDER BY check_id;
```

---

## Additional Requirement (20 pts)

Write `lab06_index_report.md` — a structured index design document for the `fsu` schema:

| Query Pattern | Recommended Index | Type | Rationale | Est. Speedup |
|--------------|------------------|------|-----------|--------------|
| Filter by dept_id | `idx_students_dept_id` | B-tree | High cardinality filter | 10x |
| ... | | | | |

Include:
1. Table of all 6 indexes you created with justification
2. For each index: before/after `EXPLAIN ANALYZE` times (copy from your terminal)
3. One index you deliberately chose **NOT** to create and why (e.g., a low-cardinality column)
4. Estimated storage overhead: total index size vs table size

---

## Submission Checklist

- [ ] Neon branch `lab-06` with 500+ students, 1000+ enrollments
- [ ] All 6 indexes created
- [ ] `lab06_analysis.md` — before/after EXPLAIN outputs for all 4 queries
- [ ] `lab06_index_report.md` — additional requirement
- [ ] `verify_lab06()` screenshot — all PASS

---

## Grading

| Component | Points |
|-----------|--------|
| Part B — Baseline EXPLAIN outputs (4 queries, plan types recorded) | 20 |
| Part C — 4 indexes created, after-EXPLAIN showing improvement | 30 |
| Part D — Index inspection + leftmost prefix explanation | 20 |
| Part E — Functional + partial indexes (2 indexes) | 15 |
| Additional requirement — index design document | 20 |
| **Total** | **105** |
