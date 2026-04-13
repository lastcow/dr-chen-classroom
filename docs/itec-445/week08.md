---
title: "Week 8 — Database Views: Design, Security & Reporting"
description: Master the creation and management of views in MySQL and PostgreSQL, including updatable views, security views for PII protection, materialized views, and performance implications.
---

# Week 8 — Database Views: Design, Security & Reporting

<div class="week-meta" markdown>
**Course Objectives:** CO5 &nbsp;|&nbsp; **Focus:** Views &nbsp;|&nbsp; **Difficulty:** ⭐⭐☆☆☆
</div>

---

## Learning Objectives

By the end of this week, you will be able to:

- [ ] Define a view and articulate its benefits for security, abstraction, and query simplification
- [ ] Write `CREATE VIEW`, `CREATE OR REPLACE VIEW`, `ALTER VIEW`, and `DROP VIEW` in both MySQL and PostgreSQL
- [ ] Determine whether a MySQL view is updatable and apply `WITH CHECK OPTION` correctly
- [ ] Design security views that hide PII columns and restrict rows visible to specific users
- [ ] Build reporting views that pre-aggregate data and simplify joins for BI tools
- [ ] Create and refresh PostgreSQL materialized views using `REFRESH MATERIALIZED VIEW CONCURRENTLY`
- [ ] Explain the performance difference between MySQL's MERGE and TEMPTABLE view algorithms
- [ ] Inspect view metadata via `information_schema.VIEWS` and `SHOW CREATE VIEW`

---

## 1. View Fundamentals

### 1.1 What Is a View?

A **view** is a named, stored SQL query that behaves like a virtual table. When you query a view, the database engine substitutes the view's defining query and executes the combined result. No data is physically duplicated (for standard views — see Section 5 for materialized views).

```sql
-- Create a simple view
CREATE VIEW student_summary AS
SELECT
    student_id,
    CONCAT(first_name, ' ', last_name) AS full_name,
    dept_id,
    gpa,
    enrolled_on
FROM students
WHERE is_active = 1;

-- Query the view exactly like a table
SELECT full_name, gpa FROM student_summary WHERE dept_id = 5;
```

### 1.2 Benefits of Views

| Benefit | Description | Example |
|---------|-------------|---------|
| **Security** | Expose only approved columns/rows to users | Hide salary, SSN, PII |
| **Abstraction** | Decouple applications from table structure | Schema refactors don't break app queries |
| **Query simplification** | Complex joins become a simple SELECT | BI tools connect to view, not raw tables |
| **Consistency** | Business logic defined once, reused everywhere | GPA calculation formula centralized |
| **Row-level access** | WHERE clause in view restricts visible data | Students see only their own enrollments |

### 1.3 What Views Cannot Do

!!! warning "View Limitations"
    Standard (non-materialized) MySQL views:

    - **Cannot be indexed** — no index creation on a view
    - **Do not cache results** — every query re-executes the underlying SQL
    - **Cannot reference themselves** (no recursive views in MySQL without CTEs)
    - **Non-updatable views** cannot be used in `INSERT`, `UPDATE`, or `DELETE`
    - **Cannot use `ORDER BY` at the top level** without `LIMIT` (MySQL ignores it)
    - **TEMPTABLE algorithm views** are never updatable

---

## 2. Creating and Managing Views

### 2.1 CREATE VIEW Syntax

=== "MySQL"

    ```sql
    -- Basic creation
    CREATE VIEW dept_enrollment_counts AS
    SELECT
        d.dept_id,
        d.dept_name,
        COUNT(DISTINCT s.student_id) AS student_count,
        COUNT(DISTINCT e.course_id)  AS course_count
    FROM departments d
    LEFT JOIN students    s ON d.dept_id  = s.dept_id
    LEFT JOIN enrollments e ON s.student_id = e.student_id
                            AND e.semester = '2024FA'
    GROUP BY d.dept_id, d.dept_name;

    -- OR REPLACE: atomically replaces existing view definition
    CREATE OR REPLACE VIEW dept_enrollment_counts AS
    SELECT d.dept_id, d.dept_name,
           COUNT(DISTINCT s.student_id) AS student_count,
           COUNT(DISTINCT e.course_id)  AS course_count,
           ROUND(AVG(s.gpa), 2)         AS avg_dept_gpa   -- added column
    FROM departments d
    LEFT JOIN students    s ON d.dept_id  = s.dept_id
    LEFT JOIN enrollments e ON s.student_id = e.student_id
                            AND e.semester = '2024FA'
    GROUP BY d.dept_id, d.dept_name;

    -- ALTER VIEW: MySQL allows changing the definition
    ALTER VIEW student_summary AS
    SELECT student_id, CONCAT(first_name,' ',last_name) AS full_name,
           dept_id, gpa, enrolled_on, last_login
    FROM students WHERE is_active = 1;

    -- Drop view
    DROP VIEW IF EXISTS dept_enrollment_counts;
    ```

=== "PostgreSQL"

    ```sql
    -- PostgreSQL syntax is nearly identical
    CREATE VIEW active_students AS
    SELECT student_id,
           first_name || ' ' || last_name AS full_name,
           dept_id, gpa, enrolled_on
    FROM students
    WHERE is_active = TRUE;

    -- Replace (PostgreSQL 9.4+)
    CREATE OR REPLACE VIEW active_students AS
    SELECT student_id,
           first_name || ' ' || last_name AS full_name,
           dept_id, gpa, enrolled_on, email
    FROM students
    WHERE is_active = TRUE;

    -- PostgreSQL does not have ALTER VIEW for full replacement;
    -- use CREATE OR REPLACE VIEW instead

    -- Drop with CASCADE if other objects depend on this view
    DROP VIEW IF EXISTS active_students CASCADE;
    ```

### 2.2 Inspecting View Metadata

```sql
-- MySQL: show the original CREATE VIEW statement
SHOW CREATE VIEW student_summary\G

-- Via information_schema (both MySQL and PostgreSQL)
SELECT
    TABLE_NAME      AS view_name,
    VIEW_DEFINITION,
    IS_UPDATABLE,
    SECURITY_TYPE,
    DEFINER,
    CHECK_OPTION
FROM information_schema.VIEWS
WHERE TABLE_SCHEMA = 'university'
ORDER BY TABLE_NAME;

-- Find views that depend on a specific table (MySQL)
SELECT TABLE_NAME AS dependent_view
FROM information_schema.VIEW_TABLE_USAGE
WHERE VIEW_SCHEMA  = 'university'
  AND TABLE_NAME   = 'students';   -- tables referenced by views
```

!!! note "View Security Types"
    Views in MySQL have a `SECURITY_TYPE` of either `DEFINER` (view runs with the permissions of the user who created it) or `INVOKER` (view runs with the calling user's permissions). `DEFINER` is the default and is commonly used to give users access through a view to tables they cannot directly query.

---

## 3. Updatable Views

### 3.1 MySQL Updatability Requirements

A MySQL view is **updatable** (supports `INSERT`, `UPDATE`, `DELETE`) only when:

- Defined on a **single base table** (or simple equi-join)
- Contains **no** `DISTINCT`
- Contains **no** aggregate functions (`SUM`, `AVG`, etc.)
- Contains **no** `GROUP BY` or `HAVING`
- Contains **no** subqueries in the `SELECT` list
- Contains **no** set operations (`UNION`, `INTERSECT`, `EXCEPT`)
- References **no** non-updatable views
- Contains **no** literal values or expressions in the SELECT list that map to columns

```sql
-- ✅ Updatable view (simple single-table projection)
CREATE VIEW active_students AS
SELECT student_id, first_name, last_name, dept_id, gpa, email
FROM students
WHERE is_active = 1;

-- These all work on the view:
UPDATE active_students SET gpa = 3.8 WHERE student_id = 1001;
DELETE FROM active_students WHERE student_id = 1099;
INSERT INTO active_students (student_id, first_name, last_name, dept_id, gpa, email)
VALUES (5000, 'Alice', 'Nguyen', 3, 3.5, 'anguyen@frostburg.edu');

-- ❌ NOT updatable (GROUP BY present)
CREATE VIEW dept_avg_gpa AS
SELECT dept_id, AVG(gpa) AS avg_gpa
FROM students
GROUP BY dept_id;
-- UPDATE dept_avg_gpa ... → ERROR 1288: target not updatable
```

### 3.2 WITH CHECK OPTION

`WITH CHECK OPTION` ensures that rows inserted or updated through a view still satisfy the view's `WHERE` clause — preventing "invisible row" bugs:

```sql
-- Without CHECK OPTION: you can insert a row the view can't see
CREATE VIEW cs_students AS
SELECT student_id, first_name, last_name, dept_id
FROM students WHERE dept_id = (SELECT dept_id FROM departments WHERE dept_code = 'CS');

-- Inserting a student from a different department succeeds (silently disappears from view)
INSERT INTO cs_students (student_id, first_name, last_name, dept_id)
VALUES (6001, 'Bob', 'Lee', 7);  -- dept_id 7 = Mathematics — user won't see this via view!

-- ✅ WITH CHECK OPTION prevents this
CREATE OR REPLACE VIEW cs_students AS
SELECT student_id, first_name, last_name, dept_id
FROM students
WHERE dept_id = (SELECT dept_id FROM departments WHERE dept_code = 'CS')
WITH CHECK OPTION;

-- Now this raises an error:
INSERT INTO cs_students VALUES (6002, 'Carol', 'Kim', 7);
-- ERROR 1369: CHECK OPTION failed 'university.cs_students'
```

=== "LOCAL Check Option"

    `WITH LOCAL CHECK OPTION` — only checks the current view's `WHERE` clause, not the clauses of any underlying views:

    ```sql
    CREATE VIEW honors_students AS
    SELECT * FROM active_students WHERE gpa >= 3.5
    WITH LOCAL CHECK OPTION;
    -- Enforces gpa >= 3.5 but NOT is_active = 1 from the underlying view
    ```

=== "CASCADED Check Option"

    `WITH CASCADED CHECK OPTION` (default) — checks the current view AND all underlying views in the chain:

    ```sql
    CREATE VIEW honors_students AS
    SELECT * FROM active_students WHERE gpa >= 3.5
    WITH CASCADED CHECK OPTION;
    -- Enforces BOTH: gpa >= 3.5 AND is_active = 1
    ```

---

## 4. Security Views

### 4.1 Hiding Sensitive Columns (PII Masking)

Views are the standard mechanism for column-level security — grant access to the view, revoke access to the base table:

```sql
-- Base table (never grant SELECT to application users)
CREATE TABLE students (
    student_id   INT          NOT NULL AUTO_INCREMENT,
    first_name   VARCHAR(50)  NOT NULL,
    last_name    VARCHAR(50)  NOT NULL,
    email        VARCHAR(100) NOT NULL,
    ssn          CHAR(11),           -- Social Security Number — highly sensitive
    date_of_birth DATE,              -- PII
    gpa          DECIMAL(3,2),
    dept_id      INT,
    is_active    TINYINT(1)   DEFAULT 1,
    PRIMARY KEY (student_id)
);

-- ✅ Safe view: SSN and DOB never exposed
CREATE VIEW students_public AS
SELECT
    student_id,
    first_name,
    last_name,
    email,
    -- Mask SSN: show only last 4 digits
    CONCAT('***-**-', RIGHT(ssn, 4)) AS ssn_masked,
    gpa,
    dept_id,
    is_active
FROM students;

-- Grant view access to application role; never grant table access
GRANT SELECT ON university.students_public TO 'app_readonly'@'%';
REVOKE ALL ON university.students FROM 'app_readonly'@'%';
```

### 4.2 Row-Level Security via WHERE Clause

```sql
-- Each instructor can only see their own course enrollments
-- (Row-level access enforced by SESSION_USER() or application-passed variable)

CREATE VIEW my_course_enrollments AS
SELECT
    e.student_id,
    s.first_name,
    s.last_name,
    c.course_code,
    c.title,
    e.semester,
    e.grade
FROM enrollments e
JOIN students  s ON e.student_id = s.student_id
JOIN courses   c ON e.course_id  = c.course_id
JOIN instructors i ON c.instructor_id = i.instructor_id
WHERE i.email = CURRENT_USER();   -- row restricted to logged-in instructor

-- Students see only their own transcript
CREATE VIEW my_transcript AS
SELECT
    c.course_code,
    c.title,
    c.credits,
    e.semester,
    e.grade,
    g.points,
    g.max_points
FROM enrollments e
JOIN courses c ON e.course_id  = c.course_id
JOIN grades  g ON e.student_id = g.student_id AND e.course_id = g.course_id
WHERE e.student_id = (
    SELECT student_id FROM students WHERE email = CURRENT_USER()
);
```

!!! tip "Combining View Security with DEFINER"
    Set `SQL SECURITY DEFINER` on the view so it runs as the DBA account. Grant the application user `SELECT` on the view only. The underlying table remains invisible to the app user while the view controls exactly what they see.

### 4.3 Sensitive Data Masking Patterns

```sql
-- Full masking library view for compliance
CREATE VIEW students_masked AS
SELECT
    student_id,
    first_name,
    CONCAT(LEFT(last_name, 1), REPEAT('*', LENGTH(last_name)-1))   AS last_name,
    CONCAT(LEFT(email, 2), '***@', SUBSTRING_INDEX(email,'@',-1))  AS email,
    CONCAT('***-**-', RIGHT(ssn, 4))                                AS ssn,
    CONCAT(YEAR(date_of_birth), '-**-**')                           AS birth_year_only,
    gpa,
    dept_id
FROM students;
```

---

## 5. Reporting Views and Materialized Views

### 5.1 Reporting Views

Pre-built reporting views simplify BI tool configuration and ensure consistent metric definitions:

```sql
-- Department summary for enrollment reports
CREATE VIEW v_dept_summary AS
SELECT
    d.dept_id,
    d.dept_name,
    d.dept_code,
    COUNT(DISTINCT s.student_id)                            AS total_students,
    COUNT(DISTINCT CASE WHEN s.is_active = 1 THEN s.student_id END) AS active_students,
    ROUND(AVG(CASE WHEN s.is_active = 1 THEN s.gpa END), 3) AS avg_gpa,
    SUM(CASE WHEN s.gpa >= 3.5 THEN 1 ELSE 0 END)          AS honors_count,
    COUNT(DISTINCT f.instructor_id)                          AS faculty_count
FROM departments d
LEFT JOIN students    s ON d.dept_id      = s.dept_id
LEFT JOIN instructors f ON d.dept_id      = f.dept_id
GROUP BY d.dept_id, d.dept_name, d.dept_code;

-- Faculty workload view
CREATE VIEW v_faculty_workload AS
SELECT
    i.instructor_id,
    CONCAT(i.first_name,' ',i.last_name) AS instructor_name,
    d.dept_name,
    COUNT(DISTINCT c.course_id)              AS courses_assigned,
    SUM(c.credits)                           AS total_credit_hours,
    COUNT(DISTINCT e.student_id)             AS total_enrolled_students
FROM instructors i
JOIN departments  d ON i.dept_id     = d.dept_id
JOIN courses      c ON c.instructor_id = i.instructor_id
LEFT JOIN enrollments e ON e.course_id = c.course_id
                       AND e.semester = '2024FA'
GROUP BY i.instructor_id, instructor_name, d.dept_name;
```

### 5.2 Materialized Views (PostgreSQL)

A **materialized view** physically stores the query result on disk. Unlike regular views, queries against a materialized view read cached data — they are not re-executed live.

```sql
-- PostgreSQL: Create materialized view
CREATE MATERIALIZED VIEW mv_semester_gpa_summary AS
SELECT
    e.semester,
    d.dept_name,
    COUNT(DISTINCT e.student_id)                     AS enrolled_count,
    ROUND(AVG(g.points::DECIMAL / g.max_points * 4), 3) AS avg_gpa_equiv,
    COUNT(CASE WHEN e.grade = 'A' THEN 1 END)        AS a_grade_count
FROM enrollments e
JOIN students   s ON e.student_id = s.student_id
JOIN departments d ON s.dept_id   = d.dept_id
JOIN grades     g ON e.student_id = g.student_id AND e.course_id = g.course_id
GROUP BY e.semester, d.dept_name
ORDER BY e.semester DESC, d.dept_name;

-- Populate immediately (default)
-- CREATE MATERIALIZED VIEW ... WITH DATA;

-- Create empty shell (populate later)
CREATE MATERIALIZED VIEW mv_semester_gpa_summary
WITH NO DATA AS ...;

-- Refresh strategies
REFRESH MATERIALIZED VIEW mv_semester_gpa_summary;
-- Blocks all reads during refresh (exclusive lock)

REFRESH MATERIALIZED VIEW CONCURRENTLY mv_semester_gpa_summary;
-- Non-blocking: builds new data then swaps atomically
-- REQUIRES a UNIQUE index on the materialized view

-- Create required unique index for CONCURRENTLY
CREATE UNIQUE INDEX ON mv_semester_gpa_summary (semester, dept_name);

-- Automate refresh with pg_cron (PostgreSQL extension)
SELECT cron.schedule('refresh-mv-daily', '0 2 * * *',
    'REFRESH MATERIALIZED VIEW CONCURRENTLY mv_semester_gpa_summary');
```

!!! info "Materialized View vs. Regular View"

    | Feature | Regular View | Materialized View |
    |---------|--------------|------------------|
    | Data storage | None (virtual) | Physical table |
    | Query speed | As fast as base query | As fast as a table scan |
    | Data freshness | Always current | Stale until refreshed |
    | Index support | No | Yes (can index freely) |
    | DML support | Sometimes | No |
    | Availability | MySQL ✅ PostgreSQL ✅ | PostgreSQL ✅ MySQL ❌ (simulate with table+trigger) |

### 5.3 Simulating Materialized Views in MySQL

MySQL lacks native materialized views, but you can simulate them:

```sql
-- Step 1: Create summary table
CREATE TABLE mv_dept_summary (
    dept_id          INT NOT NULL,
    dept_name        VARCHAR(80),
    total_students   INT,
    avg_gpa          DECIMAL(5,3),
    last_refreshed   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (dept_id)
);

-- Step 2: Stored procedure to refresh
DELIMITER //
CREATE PROCEDURE refresh_mv_dept_summary()
BEGIN
    TRUNCATE TABLE mv_dept_summary;
    INSERT INTO mv_dept_summary (dept_id, dept_name, total_students, avg_gpa, last_refreshed)
    SELECT
        d.dept_id,
        d.dept_name,
        COUNT(DISTINCT s.student_id),
        ROUND(AVG(s.gpa), 3),
        NOW()
    FROM departments d
    LEFT JOIN students s ON d.dept_id = s.dept_id
    GROUP BY d.dept_id, d.dept_name;
END //
DELIMITER ;

-- Step 3: Schedule with MySQL Event Scheduler
SET GLOBAL event_scheduler = ON;
CREATE EVENT ev_refresh_dept_summary
ON SCHEDULE EVERY 1 HOUR
STARTS CURRENT_TIMESTAMP
DO CALL refresh_mv_dept_summary();
```

---

## 6. View Performance: MERGE vs. TEMPTABLE

### 6.1 MySQL View Algorithms

MySQL processes views using one of two internal algorithms:

=== "MERGE Algorithm"

    The view definition is **merged inline** with the outer query before execution. The optimizer sees the full combined query and can use indexes from base tables.

    ```sql
    CREATE ALGORITHM = MERGE VIEW v_active_cs_students AS
    SELECT student_id, first_name, last_name, gpa
    FROM students
    WHERE dept_id = (SELECT dept_id FROM departments WHERE dept_code = 'CS')
      AND is_active = 1;

    -- Query: SELECT * FROM v_active_cs_students WHERE gpa > 3.5
    -- Optimizer rewrites to: SELECT ... FROM students WHERE dept_id=? AND is_active=1 AND gpa>3.5
    -- Full index access to base table indexes available!
    ```

    **MERGE is used when:** the view is simple enough — no `GROUP BY`, `DISTINCT`, aggregate functions, subqueries in SELECT, or `UNION`.

=== "TEMPTABLE Algorithm"

    MySQL **materializes the view into a temporary table**, then runs the outer query against that temp table. **No base table indexes are available** after materialization.

    ```sql
    -- MySQL is forced to use TEMPTABLE for aggregate views
    CREATE ALGORITHM = TEMPTABLE VIEW v_dept_avg AS
    SELECT dept_id, AVG(gpa) AS avg_gpa, COUNT(*) AS cnt
    FROM students
    GROUP BY dept_id;

    -- Query: SELECT * FROM v_dept_avg WHERE avg_gpa > 3.2
    -- MySQL:
    --   1. Executes GROUP BY query → writes to temp table (no indexes!)
    --   2. Scans temp table WHERE avg_gpa > 3.2
    -- Full scan of temp table — can't index avg_gpa
    ```

    !!! warning "TEMPTABLE Performance Impact"
        TEMPTABLE views are materialized to **memory** (up to `tmp_table_size`, default 16 MB), then spill to disk. Avoid them in queries called many times per second. Consider replacing them with the MySQL simulated materialized view pattern from Section 5.3.

### 6.2 Checking Algorithm Assignment

```sql
-- Check which algorithm MySQL chose
SELECT TABLE_NAME, VIEW_DEFINITION, IS_UPDATABLE
FROM information_schema.VIEWS
WHERE TABLE_SCHEMA = 'university';

-- EXPLAIN shows <derived> for TEMPTABLE views:
EXPLAIN SELECT * FROM v_dept_avg WHERE avg_gpa > 3.2;
-- table: <derived2>  type: ALL  -- this is the temp table scan!

-- EXPLAIN shows base table directly for MERGE views:
EXPLAIN SELECT * FROM v_active_cs_students WHERE gpa > 3.5;
-- table: students  type: ref  key: idx_dept  -- base table index used!
```

---

## 7. Practical View Designs for the University Database

### 7.1 Student Transcript View

```sql
CREATE VIEW v_student_transcript AS
SELECT
    s.student_id,
    CONCAT(s.first_name, ' ', s.last_name)      AS student_name,
    d.dept_name,
    c.course_code,
    c.title                                      AS course_title,
    c.credits,
    e.semester,
    e.grade,
    ROUND(g.points / g.max_points * 100, 1)      AS score_pct,
    CASE e.grade
        WHEN 'A'  THEN 4.0 WHEN 'A-' THEN 3.7
        WHEN 'B+' THEN 3.3 WHEN 'B'  THEN 3.0
        WHEN 'B-' THEN 2.7 WHEN 'C+' THEN 2.3
        WHEN 'C'  THEN 2.0 WHEN 'D'  THEN 1.0
        ELSE 0.0
    END                                          AS grade_points
FROM students  s
JOIN departments  d ON s.dept_id      = d.dept_id
JOIN enrollments  e ON s.student_id   = e.student_id
JOIN courses      c ON e.course_id    = c.course_id
JOIN grades       g ON e.student_id   = g.student_id
                    AND e.course_id   = g.course_id;

-- Example usage: calculate cumulative GPA
SELECT
    student_name,
    SUM(credits * grade_points) / SUM(credits) AS cumulative_gpa
FROM v_student_transcript
WHERE student_id = 1001
GROUP BY student_name;
```

### 7.2 Application Abstraction View

Views serve as a stable **API contract** — applications query views, and schema changes are absorbed in the view definition:

```sql
-- Schema change: students table splits full_name into first + last
-- Application code queries v_student_profile — no change needed in app

CREATE OR REPLACE VIEW v_student_profile AS
SELECT
    s.student_id        AS id,
    CONCAT(s.first_name,' ',s.last_name) AS display_name,
    s.email,
    d.dept_code         AS department,
    s.gpa,
    s.enrolled_on       AS enrollment_date,
    s.is_active         AS active
FROM students s
LEFT JOIN departments d ON s.dept_id = d.dept_id;
```

---

## Key Vocabulary

| Term | Definition |
|------|------------|
| **View** | Named stored query that behaves as a virtual table |
| **Base table** | Underlying real table(s) from which a view is derived |
| **Updatable view** | View that supports INSERT, UPDATE, DELETE operations |
| **Non-updatable view** | View using GROUP BY, aggregates, DISTINCT — read-only |
| **WITH CHECK OPTION** | Constraint ensuring DML through view satisfies the view's WHERE clause |
| **LOCAL check option** | Check option applied only to the current view's WHERE clause |
| **CASCADED check option** | Check option applied to current view and all underlying view clauses |
| **MERGE algorithm** | View definition merged inline with outer query; base table indexes available |
| **TEMPTABLE algorithm** | View materialized to a temporary table before outer query runs; no base table indexes |
| **Materialized view** | View whose result is physically stored and must be explicitly refreshed |
| **REFRESH MATERIALIZED VIEW** | PostgreSQL command to update a materialized view's stored data |
| **CONCURRENTLY** | PostgreSQL refresh option that allows reads during refresh (requires unique index) |
| **DEFINER security** | View executes with the permissions of its creator |
| **INVOKER security** | View executes with the permissions of the calling user |
| **PII (Personally Identifiable Information)** | Data that can identify an individual: SSN, DOB, email |
| **Column masking** | Partially obscuring sensitive data (e.g., showing only last 4 digits of SSN) |
| **Row-level security** | Restricting visible rows based on the querying user's identity |
| **View dependency** | Another database object (view, procedure) that references a given view |
| **information_schema.VIEWS** | System catalog table containing view metadata |
| **Event Scheduler** | MySQL feature for scheduling recurring stored procedure or SQL execution |

---

## Self-Assessment

!!! question "Self-Assessment"
    1. A faculty member queries `v_faculty_workload` and the query takes 12 seconds despite the underlying tables being well-indexed. You run `EXPLAIN` and see `table: <derived2>, type: ALL`. Explain what this means, why the indexes on `instructors`, `courses`, and `enrollments` are not being used, and provide two strategies to fix the performance problem.

    2. Your security audit reveals that the application role `app_user` has `SELECT` privilege on the `students` base table. You need to implement column-level security to hide `ssn` and `date_of_birth` and row-level security to restrict each student to only seeing their own record. Write the complete SQL: create the view, configure the security type, and adjust privileges. Include `WITH CHECK OPTION` considerations.

    3. Explain the exact conditions that make a MySQL view non-updatable. You have a view `v_cs_honors` that joins `students` and `departments` and filters on `gpa > 3.5`. Is this view updatable? Write a test query to confirm updatability programmatically using `information_schema`.

    4. A teammate proposes replacing a heavily-used reporting query (runs 500 times/minute) with a regular view containing three `GROUP BY` aggregations and two `LEFT JOIN` subqueries. Explain the performance implications of this approach and propose a better architecture for MySQL and for PostgreSQL separately.

    5. Describe the difference between `WITH LOCAL CHECK OPTION` and `WITH CASCADED CHECK OPTION` in the context of a two-level view chain: `v_base` filters `is_active = 1`, and `v_honors` (built on `v_base`) filters `gpa >= 3.5 WITH LOCAL CHECK OPTION`. What happens when a user inserts a row with `is_active = 0` and `gpa = 3.8` through `v_honors`? Would the behavior change with CASCADED?

---

## Further Reading

- 📖 *MySQL 8.0 Reference Manual* — [Section 25.5: Using Views](https://dev.mysql.com/doc/refman/8.0/en/views.html)
- 📖 *PostgreSQL Documentation* — [Section 7.8: WITH Queries (CTEs)](https://www.postgresql.org/docs/current/queries-with.html) and [Materialized Views](https://www.postgresql.org/docs/current/rules-materializedviews.html)
- 📄 [MySQL View Algorithms — MERGE vs TEMPTABLE](https://dev.mysql.com/doc/refman/8.0/en/view-algorithms.html)
- 📄 [Percona Blog: MySQL Views and Performance](https://www.percona.com/blog/mysql-views-and-performance/)
- 📄 [PostgreSQL Wiki: Materialized Views](https://wiki.postgresql.org/wiki/Materialized_Views)
- 📄 [OWASP: Column-Level Security with Views](https://owasp.org/www-community/controls/Database_Security_Cheat_Sheet)
- 🎥 MySQL and Security — Oracle University Webinar (YouTube)

---

[← Week 7](week07.md) | [Course Index](index.md) | [Week 9 →](week09.md)
