---
title: "Week 2 — Window Functions, CTEs & Analytical Queries"
description: Unlock SQL's most powerful analytical tools — Common Table Expressions, recursive queries, window functions, and the frame clause — to write readable, high-performance analytical queries.
---

# Week 2 — Window Functions, CTEs & Analytical Queries

<div class="week-meta" markdown>
**Course Objectives:** CO1 &nbsp;|&nbsp; **Focus:** Analytical SQL &nbsp;|&nbsp; **Difficulty:** ⭐⭐⭐☆☆
</div>

---

## Learning Objectives

By the end of this week, you will be able to:

- [ ] Write Common Table Expressions (CTEs) and explain how they differ from derived tables and views
- [ ] Construct recursive CTEs to traverse hierarchical and graph-structured data
- [ ] Use OVER(), PARTITION BY, and ORDER BY to define window function scope
- [ ] Apply ROW_NUMBER(), RANK(), DENSE_RANK(), and NTILE() for ranking tasks
- [ ] Compute running totals, moving averages, and cumulative sums using aggregate window functions
- [ ] Use LAG(), LEAD(), FIRST_VALUE(), and LAST_VALUE() for row-to-row comparisons
- [ ] Write frame clauses (ROWS BETWEEN / RANGE BETWEEN) with UNBOUNDED, CURRENT ROW, and numeric offsets
- [ ] Implement PIVOT logic using conditional aggregation with CASE WHEN
- [ ] Analyze and compare the performance of window functions versus self-join equivalents
- [ ] Apply window functions to real analytics patterns: YoY growth, cohort analysis, and percentile ranking

---

## Reference Schema

This week continues using the Frostburg University schema from Week 1. We add a `grade_points` helper view:

```sql
-- Helper: convert letter grades to grade points
CREATE OR REPLACE VIEW grade_points AS
SELECT enrollment_id,
       student_id,
       course_id,
       semester,
       grade,
       CASE grade
           WHEN 'A'  THEN 4.0  WHEN 'A-' THEN 3.7
           WHEN 'B+' THEN 3.3  WHEN 'B'  THEN 3.0
           WHEN 'B-' THEN 2.7  WHEN 'C+' THEN 2.3
           WHEN 'C'  THEN 2.0  WHEN 'C-' THEN 1.7
           WHEN 'D+' THEN 1.3  WHEN 'D'  THEN 1.0
           WHEN 'F'  THEN 0.0  ELSE NULL
       END AS points
FROM   enrollments;
```

---

## 1. Common Table Expressions (CTEs)

A **Common Table Expression** is a named temporary result set defined at the top of a query with the `WITH` keyword. It exists only for the duration of the statement.

### 1.1 Basic CTE Syntax

```sql
-- Basic CTE: students with above-average GPA per department
WITH dept_averages AS (
    SELECT dept_id, AVG(gpa) AS avg_gpa
    FROM   students
    WHERE  gpa IS NOT NULL
    GROUP BY dept_id
)
SELECT  s.first_name,
        s.last_name,
        s.gpa,
        da.avg_gpa,
        d.dept_name
FROM    students       s
INNER JOIN dept_averages da ON da.dept_id = s.dept_id
INNER JOIN departments   d  ON d.dept_id  = s.dept_id
WHERE   s.gpa > da.avg_gpa
ORDER BY d.dept_name, s.gpa DESC;
```

### 1.2 Chained CTEs

Multiple CTEs can be chained — each subsequent CTE can reference all previous ones.

```sql
-- Step 1: compute per-student semester GPA
-- Step 2: compute per-student GPA trend (current vs previous)
WITH semester_gpa AS (
    SELECT  student_id,
            semester,
            AVG(points) AS sem_gpa
    FROM    grade_points
    WHERE   points IS NOT NULL
    GROUP BY student_id, semester
),
gpa_trend AS (
    SELECT  student_id,
            semester,
            sem_gpa,
            LAG(sem_gpa) OVER (
                PARTITION BY student_id
                ORDER BY semester
            ) AS prev_sem_gpa
    FROM    semester_gpa
)
SELECT  s.first_name,
        s.last_name,
        gt.semester,
        ROUND(gt.sem_gpa, 2)      AS current_gpa,
        ROUND(gt.prev_sem_gpa, 2) AS previous_gpa,
        ROUND(gt.sem_gpa - gt.prev_sem_gpa, 2) AS change
FROM    gpa_trend gt
INNER JOIN students s ON s.student_id = gt.student_id
WHERE   gt.prev_sem_gpa IS NOT NULL
ORDER BY ABS(gt.sem_gpa - gt.prev_sem_gpa) DESC
LIMIT   20;
```

### 1.3 CTEs vs Derived Tables vs Views

| Feature | CTE | Derived Table | Temporary View |
|---------|-----|---------------|----------------|
| Reusability within query | ✅ Can reference multiple times | ❌ Must repeat | ✅ Yes |
| Readability | ✅ Named, top-level | ❌ Inline, nested | ✅ Named |
| Persistence | Statement-scoped | Statement-scoped | Session/global |
| Recursive support | ✅ Yes | ❌ No | ❌ No |
| Optimization | Optimizer may inline | Always materialized/inlined | Depends on engine |

!!! info "MySQL CTE Materialization"
    In MySQL 8.0, the optimizer may choose to materialize a CTE into a temp table or inline it. Use `NO_MERGE` / `MERGE` optimizer hints to control this behavior. PostgreSQL always materializes CTEs unless `NOT MATERIALIZED` is specified (PostgreSQL 12+).

---

## 2. Recursive CTEs

A **recursive CTE** references itself, allowing traversal of hierarchical or graph-structured data. It has two parts: the **anchor member** (base case) and the **recursive member** (self-reference).

### 2.1 Organizational Hierarchy

```sql
-- Add a manager column to instructors for hierarchy demo
ALTER TABLE instructors ADD COLUMN manager_id INT NULL,
    ADD FOREIGN KEY (manager_id) REFERENCES instructors(instructor_id);

-- Traverse the reporting hierarchy from a given root
WITH RECURSIVE org_chart AS (
    -- Anchor: start from the top-level (no manager)
    SELECT instructor_id,
           first_name,
           last_name,
           manager_id,
           0 AS depth,
           CONCAT(first_name, ' ', last_name) AS path
    FROM   instructors
    WHERE  manager_id IS NULL

    UNION ALL

    -- Recursive: join subordinates to their manager
    SELECT  i.instructor_id,
            i.first_name,
            i.last_name,
            i.manager_id,
            oc.depth + 1,
            CONCAT(oc.path, ' → ', i.first_name, ' ', i.last_name)
    FROM    instructors i
    INNER JOIN org_chart oc ON oc.instructor_id = i.manager_id
)
SELECT  REPEAT('  ', depth) AS indent,
        CONCAT(first_name, ' ', last_name) AS name,
        depth,
        path
FROM    org_chart
ORDER BY path;
```

### 2.2 Sequence Generation

Recursive CTEs can generate number sequences or date ranges without a numbers table.

```sql
-- Generate a sequence of dates for the current semester (useful for gap analysis)
WITH RECURSIVE date_series AS (
    SELECT DATE('2025-08-25') AS dt   -- semester start
    UNION ALL
    SELECT DATE_ADD(dt, INTERVAL 1 DAY)
    FROM   date_series
    WHERE  dt < DATE('2025-12-15')    -- semester end
)
SELECT dt, DAYNAME(dt) AS day_name
FROM   date_series
WHERE  DAYOFWEEK(dt) NOT IN (1, 7);  -- exclude weekends
```

!!! warning "Infinite Recursion Prevention"
    MySQL enforces `@@cte_max_recursion_depth` (default: 1000). PostgreSQL uses `CYCLE` detection syntax. Always ensure your recursive member has a termination condition in the `WHERE` clause.

### 2.3 Bill of Materials (Parts Explosion)

```sql
-- Suppose courses have prerequisites stored recursively
CREATE TABLE prerequisites (
    course_id    INT NOT NULL,
    prereq_id    INT NOT NULL,
    PRIMARY KEY (course_id, prereq_id),
    FOREIGN KEY (course_id) REFERENCES courses(course_id),
    FOREIGN KEY (prereq_id) REFERENCES courses(course_id)
);

-- All prerequisites (direct and transitive) for a given course
WITH RECURSIVE prereq_tree AS (
    SELECT course_id, prereq_id, 1 AS level
    FROM   prerequisites
    WHERE  course_id = (SELECT course_id FROM courses WHERE course_code = 'ITEC445')

    UNION ALL

    SELECT p.course_id, p.prereq_id, pt.level + 1
    FROM   prerequisites p
    INNER JOIN prereq_tree pt ON pt.prereq_id = p.course_id
)
SELECT  pt.level,
        c_req.course_code AS requires,
        c_pre.course_code AS prerequisite
FROM    prereq_tree  pt
INNER JOIN courses   c_req ON c_req.course_id = pt.course_id
INNER JOIN courses   c_pre ON c_pre.course_id = pt.prereq_id
ORDER BY pt.level, c_req.course_code;
```

---

## 3. Window Function Fundamentals

A **window function** performs a calculation across a set of rows related to the current row — the **window** — without collapsing rows the way GROUP BY does.

```sql
SELECT col, aggregate_function() OVER (
    [PARTITION BY partition_col]
    [ORDER BY sort_col [ASC|DESC]]
    [frame_clause]
) AS result
FROM table;
```

### 3.1 PARTITION BY and ORDER BY

```sql
-- Each student's rank within their department by GPA
SELECT  s.first_name,
        s.last_name,
        d.dept_name,
        s.gpa,
        RANK() OVER (
            PARTITION BY s.dept_id        -- separate window per department
            ORDER BY s.gpa DESC           -- rank by GPA descending
        ) AS dept_rank,
        RANK() OVER (
            ORDER BY s.gpa DESC           -- rank across ALL students
        ) AS overall_rank
FROM    students   s
INNER JOIN departments d ON d.dept_id = s.dept_id
WHERE   s.gpa IS NOT NULL;
```

!!! info "Window vs GROUP BY"
    GROUP BY reduces N rows to fewer rows. A window function keeps all rows and adds a new computed column. You can mix GROUP BY and window functions: aggregate first with GROUP BY, then apply window functions to the aggregated result.

### 3.2 Running Totals and Cumulative Aggregates

```sql
-- Running total of enrollments by semester (chronological)
SELECT  semester,
        COUNT(*) AS new_enrollments,
        SUM(COUNT(*)) OVER (
            ORDER BY semester
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS running_total
FROM    enrollments
GROUP BY semester
ORDER BY semester;
```

---

## 4. Ranking Functions

### 4.1 ROW_NUMBER, RANK, DENSE_RANK, NTILE

=== "ROW_NUMBER()"
    ```sql
    -- Assign a unique sequential number regardless of ties
    SELECT  student_id,
            last_name,
            gpa,
            ROW_NUMBER() OVER (ORDER BY gpa DESC) AS row_num
    FROM    students
    WHERE   gpa IS NOT NULL;
    -- GPAs: 4.0, 4.0, 3.9 → row_nums: 1, 2, 3
    ```

=== "RANK()"
    ```sql
    -- Tied rows get the same rank; next rank skips
    SELECT  student_id,
            last_name,
            gpa,
            RANK() OVER (ORDER BY gpa DESC) AS rnk
    FROM    students
    WHERE   gpa IS NOT NULL;
    -- GPAs: 4.0, 4.0, 3.9 → ranks: 1, 1, 3
    ```

=== "DENSE_RANK()"
    ```sql
    -- Tied rows share rank; next rank does NOT skip
    SELECT  student_id,
            last_name,
            gpa,
            DENSE_RANK() OVER (ORDER BY gpa DESC) AS dense_rnk
    FROM    students
    WHERE   gpa IS NOT NULL;
    -- GPAs: 4.0, 4.0, 3.9 → dense ranks: 1, 1, 2
    ```

=== "NTILE()"
    ```sql
    -- Divide students into 4 quartiles by GPA
    SELECT  student_id,
            last_name,
            gpa,
            NTILE(4) OVER (ORDER BY gpa DESC) AS quartile
    FROM    students
    WHERE   gpa IS NOT NULL;
    -- quartile 1 = top 25%, quartile 4 = bottom 25%
    ```

### 4.2 Ranking Function Comparison

| Function | Ties Handling | Gaps in Ranks | Use Case |
|----------|--------------|---------------|----------|
| `ROW_NUMBER()` | Arbitrary order among ties | No gaps | Pagination, deduplication |
| `RANK()` | Tied rows share rank | Yes (1,1,3) | Competitions, leaderboards |
| `DENSE_RANK()` | Tied rows share rank | No gaps (1,1,2) | Grade categories, levels |
| `NTILE(n)` | Distributes evenly | N/A | Quartiles, deciles, percentiles |

---

## 5. Aggregate Window Functions

### 5.1 Moving Average (N-row Window)

```sql
-- 3-semester moving average GPA per student
WITH sem_gpa AS (
    SELECT  student_id, semester,
            ROUND(AVG(points), 2) AS sem_gpa
    FROM    grade_points
    WHERE   points IS NOT NULL
    GROUP BY student_id, semester
)
SELECT  student_id,
        semester,
        sem_gpa,
        ROUND(AVG(sem_gpa) OVER (
            PARTITION BY student_id
            ORDER BY semester
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ), 2) AS moving_avg_3sem
FROM    sem_gpa
ORDER BY student_id, semester;
```

### 5.2 Running Total with Conditional Reset

```sql
-- Enrollment count per department per semester,
-- plus running total that resets each academic year
SELECT  d.dept_name,
        e.semester,
        COUNT(*) AS sem_count,
        SUM(COUNT(*)) OVER (
            PARTITION BY d.dept_id, LEFT(e.semester, 1)  -- reset per year prefix (F/S)
            ORDER BY e.semester
        ) AS year_running_total
FROM    enrollments e
INNER JOIN courses     c ON c.course_id = e.course_id
INNER JOIN departments d ON d.dept_id   = c.dept_id
GROUP BY d.dept_id, d.dept_name, e.semester
ORDER BY d.dept_name, e.semester;
```

---

## 6. Offset Functions: LAG, LEAD, FIRST_VALUE, LAST_VALUE

### 6.1 LAG and LEAD

```sql
-- Year-over-year enrollment change per course
WITH course_sem AS (
    SELECT  course_id,
            semester,
            COUNT(*) AS enrolled
    FROM    enrollments
    GROUP BY course_id, semester
)
SELECT  c.course_code,
        cs.semester,
        cs.enrolled,
        LAG(cs.enrolled)  OVER w AS prev_sem_enrolled,
        LEAD(cs.enrolled) OVER w AS next_sem_enrolled,
        cs.enrolled - LAG(cs.enrolled) OVER w AS change,
        ROUND(100.0 * (cs.enrolled - LAG(cs.enrolled) OVER w)
              / NULLIF(LAG(cs.enrolled) OVER w, 0), 1) AS pct_change
FROM    course_sem cs
INNER JOIN courses c ON c.course_id = cs.course_id
WINDOW w AS (PARTITION BY cs.course_id ORDER BY cs.semester)
ORDER BY c.course_code, cs.semester;
```

!!! tip "Named Windows"
    The `WINDOW w AS (...)` clause lets you name a window specification and reuse it across multiple functions in the same `SELECT`. Introduced in MySQL 8.0 and supported in PostgreSQL.

### 6.2 FIRST_VALUE and LAST_VALUE

```sql
-- Compare each semester's enrollment to the course's first-ever and most-recent enrollment
WITH course_sem AS (
    SELECT course_id, semester, COUNT(*) AS enrolled
    FROM   enrollments
    GROUP BY course_id, semester
)
SELECT  course_id,
        semester,
        enrolled,
        FIRST_VALUE(enrolled) OVER w AS first_sem_enrolled,
        LAST_VALUE(enrolled)  OVER (
            PARTITION BY course_id
            ORDER BY semester
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        )                         AS last_sem_enrolled
FROM    course_sem
WINDOW w AS (PARTITION BY course_id ORDER BY semester
             ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW);
```

!!! warning "LAST_VALUE Default Frame"
    `LAST_VALUE()` uses the default frame `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`, which means it returns the value of the current row, not the last row in the partition. You must explicitly specify `ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING` to get the true last value.

### 6.3 NTH_VALUE

```sql
-- The second-highest GPA in each department
SELECT DISTINCT
        d.dept_name,
        NTH_VALUE(s.gpa, 2) OVER (
            PARTITION BY s.dept_id
            ORDER BY s.gpa DESC
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        ) AS second_highest_gpa
FROM    students   s
INNER JOIN departments d ON d.dept_id = s.dept_id
WHERE   s.gpa IS NOT NULL;
```

---

## 7. Frame Clauses

The **frame clause** defines which rows within the ordered partition are included in the window calculation for each row.

### 7.1 ROWS vs RANGE

=== "ROWS BETWEEN"
    ```sql
    -- Physical row offsets — exact and predictable
    -- 3-row centered moving average
    SELECT  semester,
            enrolled,
            AVG(enrolled) OVER (
                ORDER BY semester
                ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING
            ) AS centered_3_avg
    FROM (
        SELECT semester, COUNT(*) AS enrolled
        FROM   enrollments GROUP BY semester
    ) sem_counts
    ORDER BY semester;
    ```

=== "RANGE BETWEEN"
    ```sql
    -- Logical value range — includes ties with same ORDER BY value
    -- Sum of all rows with the same or earlier semester value
    SELECT  semester,
            enrolled,
            SUM(enrolled) OVER (
                ORDER BY semester
                RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            ) AS range_running_total
    FROM (
        SELECT semester, COUNT(*) AS enrolled
        FROM   enrollments GROUP BY semester
    ) sem_counts
    ORDER BY semester;
    ```

### 7.2 Frame Boundary Reference

| Boundary Keyword | Meaning |
|-----------------|---------|
| `UNBOUNDED PRECEDING` | Start of the partition |
| `n PRECEDING` | n rows/range units before current row |
| `CURRENT ROW` | The current row (ROWS) or current value (RANGE) |
| `n FOLLOWING` | n rows/range units after current row |
| `UNBOUNDED FOLLOWING` | End of the partition |

---

## 8. Practical Analytics Patterns

### 8.1 Cohort Analysis

```sql
-- Retention: students who are still enrolled in semester 4 of their program
WITH cohort AS (
    SELECT  student_id,
            MIN(semester) AS first_semester
    FROM    enrollments
    GROUP BY student_id
),
active_by_cohort AS (
    SELECT  c.first_semester,
            e.semester        AS active_semester,
            COUNT(DISTINCT e.student_id) AS active_students
    FROM    cohort   c
    INNER JOIN enrollments e ON e.student_id  = c.student_id
    GROUP BY c.first_semester, e.semester
)
SELECT  first_semester,
        active_semester,
        active_students,
        FIRST_VALUE(active_students) OVER (
            PARTITION BY first_semester ORDER BY active_semester
        ) AS cohort_size,
        ROUND(100.0 * active_students /
            FIRST_VALUE(active_students) OVER (
                PARTITION BY first_semester ORDER BY active_semester
            ), 1) AS retention_pct
FROM    active_by_cohort
ORDER BY first_semester, active_semester;
```

### 8.2 Percentile Ranking

```sql
-- Assign each student a percentile rank (0-100) within their department
SELECT  s.first_name,
        s.last_name,
        d.dept_name,
        s.gpa,
        ROUND(100 * PERCENT_RANK() OVER (
            PARTITION BY s.dept_id
            ORDER BY s.gpa
        ), 1) AS percentile,
        ROUND(100 * CUME_DIST() OVER (
            PARTITION BY s.dept_id
            ORDER BY s.gpa
        ), 1) AS cumulative_pct
FROM    students   s
INNER JOIN departments d ON d.dept_id = s.dept_id
WHERE   s.gpa IS NOT NULL
ORDER BY d.dept_name, s.gpa DESC;
```

### 8.3 PIVOT with Conditional Aggregation

```sql
-- Pivot: enrollment counts by department × semester (last 4 semesters)
SELECT  d.dept_name,
        SUM(CASE WHEN e.semester = 'S2024' THEN 1 ELSE 0 END) AS S2024,
        SUM(CASE WHEN e.semester = 'F2024' THEN 1 ELSE 0 END) AS F2024,
        SUM(CASE WHEN e.semester = 'S2025' THEN 1 ELSE 0 END) AS S2025,
        SUM(CASE WHEN e.semester = 'F2025' THEN 1 ELSE 0 END) AS F2025
FROM    enrollments e
INNER JOIN courses     c ON c.course_id = e.course_id
INNER JOIN departments d ON d.dept_id   = c.dept_id
WHERE   e.semester IN ('S2024','F2024','S2025','F2025')
GROUP BY d.dept_id, d.dept_name
ORDER BY d.dept_name;
```

!!! note "Dynamic PIVOT in MySQL"
    MySQL does not have a native PIVOT statement. For dynamic column names, you must generate the CASE WHEN SQL programmatically (via a stored procedure or application code) and execute it with `PREPARE`/`EXECUTE`.

---

## 9. Performance: Window Functions vs Self-Joins

### 9.1 The Self-Join Approach (Legacy)

```sql
-- Running total with self-join (pre-window function approach)
SELECT  a.semester,
        a.enrolled,
        SUM(b.enrolled) AS running_total
FROM (SELECT semester, COUNT(*) AS enrolled FROM enrollments GROUP BY semester) a
INNER JOIN
     (SELECT semester, COUNT(*) AS enrolled FROM enrollments GROUP BY semester) b
     ON b.semester <= a.semester
GROUP BY a.semester, a.enrolled
ORDER BY a.semester;
```

### 9.2 Performance Comparison

| Approach | Complexity | Passes Over Data | Readable | Recommended |
|----------|-----------|-----------------|----------|-------------|
| Self-join | O(n²) | Multiple | Low | ❌ Avoid |
| Window function | O(n log n) | Single | High | ✅ Yes |
| Subquery per row | O(n²) | One per row | Medium | ❌ Avoid |

!!! success "Window Functions Are the Right Tool"
    On a table with 1 million rows, a self-join running total may scan hundreds of billions of row pairs. A window function with an appropriate index processes the same result in seconds. Always prefer window functions for running totals, rankings, and row-to-row comparisons.

---

## Key Vocabulary

| Term | Definition |
|------|------------|
| **CTE** | Common Table Expression — a named temporary result set scoped to one statement |
| **Recursive CTE** | CTE that references itself to traverse hierarchical data |
| **Anchor member** | The non-recursive base SELECT in a recursive CTE |
| **Recursive member** | The self-referencing SELECT that builds on the anchor |
| **Window function** | Aggregates or calculations across a window of related rows without collapsing them |
| **OVER()** | Clause that defines the window for a window function |
| **PARTITION BY** | Divides rows into independent windows (like GROUP BY but without collapsing) |
| **Frame clause** | Defines which rows within the ordered partition contribute to each calculation |
| **ROW_NUMBER()** | Assigns a unique sequential integer to each row within the window |
| **RANK()** | Assigns rank with gaps for ties (1, 1, 3) |
| **DENSE_RANK()** | Assigns rank without gaps for ties (1, 1, 2) |
| **NTILE(n)** | Divides rows into n equal-sized buckets |
| **LAG(col, n)** | Value of col from n rows before the current row |
| **LEAD(col, n)** | Value of col from n rows after the current row |
| **FIRST_VALUE()** | Value of the first row in the window frame |
| **LAST_VALUE()** | Value of the last row in the window frame (requires explicit frame) |
| **PERCENT_RANK()** | Relative rank as a fraction: (rank-1)/(rows-1) |
| **CUME_DIST()** | Cumulative distribution: fraction of rows ≤ current value |
| **Cohort analysis** | Grouping users by a common start event and tracking behavior over time |
| **PIVOT** | Transform row values into columns; implemented in MySQL via CASE WHEN |

---

!!! question "Self-Assessment"
    1. A colleague rewrites a query by replacing a CTE with a derived table, arguing "they're the same thing." In what two specific situations would this rewrite fail or produce different results?
    2. Write a recursive CTE that finds all students who took a course that has ITEC 345 somewhere in its prerequisite chain (direct or transitive). Describe the anchor member and recursive member.
    3. Explain in detail why `LAST_VALUE(gpa) OVER (ORDER BY gpa DESC)` returns the current row's GPA rather than the minimum GPA in the partition, and write the corrected version.
    4. A report requires: for each student, show their current semester GPA, their GPA from exactly one semester ago, and the 4-semester rolling average. Write this as a single query using only window functions (no self-joins). What frame specification achieves the 4-semester average?
    5. You have 10 million enrollment rows. A DBA reports that a query using `SUM(enrolled) OVER (ORDER BY semester)` is consuming 8 minutes. What indexes, if any, can help? What else might you check in the execution plan?

---

## Further Reading

- 📖 *SQL Antipatterns*, Chapter 18 — "Spaghetti Query" (window function solutions)
- 📄 [MySQL 8.0 Reference — Window Function Concepts](https://dev.mysql.com/doc/refman/8.0/en/window-functions-usage.html)
- 📄 [PostgreSQL Documentation — Window Functions](https://www.postgresql.org/docs/current/tutorial-window.html)
- 📄 [Mode Analytics — SQL Window Functions Tutorial](https://mode.com/sql-tutorial/sql-window-functions/)
- 📄 [MySQL 8.0 — WITH (Common Table Expressions)](https://dev.mysql.com/doc/refman/8.0/en/with.html)
- 📖 *High Performance MySQL 4th Ed.*, Chapter 6 — "Query Performance Optimization"
- 🎥 CMU 15-445 Lecture 13 — "Query Execution" (window aggregates)

---

*[← Week 1](week01.md) &nbsp;|&nbsp; [Course Index](index.md) &nbsp;|&nbsp; [Week 3 →](week03.md)*
