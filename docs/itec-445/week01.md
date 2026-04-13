---
title: "Week 1 — Advanced SQL: Joins, Subqueries & Set Operations"
description: Master every JOIN type, subquery form, and set operation in SQL — with performance analysis, real schema examples, and common query patterns used in production databases.
---

# Week 1 — Advanced SQL: Joins, Subqueries & Set Operations

<div class="week-meta" markdown>
**Course Objectives:** CO1 &nbsp;|&nbsp; **Focus:** Advanced Query Writing &nbsp;|&nbsp; **Difficulty:** ⭐⭐☆☆☆
</div>

---

## Learning Objectives

By the end of this week, you will be able to:

- [ ] Write syntactically correct INNER, LEFT, RIGHT, FULL OUTER, CROSS, and SELF JOINs against a multi-table schema
- [ ] Explain the performance characteristics of each JOIN type and choose the appropriate one for a given scenario
- [ ] Distinguish between scalar, row, table, and correlated subqueries and apply each correctly
- [ ] Evaluate the trade-offs between EXISTS, IN, and JOIN for filtering and decide which to use
- [ ] Construct nested subqueries and identify opportunities to refactor them for readability and performance
- [ ] Apply UNION, UNION ALL, INTERSECT, and EXCEPT/MINUS and explain their duplicate-handling rules
- [ ] Perform multi-table UPDATE and DELETE operations using JOIN syntax
- [ ] Implement practical query patterns: duplicate detection, gap analysis, and top-N per group

---

## Reference Schema

All examples throughout this week use the **Frostburg University** database. Familiarize yourself with this schema — it appears in every week of the course.

```sql
-- Core university schema used throughout ITEC 445
CREATE TABLE departments (
    dept_id   INT          PRIMARY KEY AUTO_INCREMENT,
    dept_name VARCHAR(100) NOT NULL,
    building  VARCHAR(50),
    budget    DECIMAL(12,2)
);

CREATE TABLE instructors (
    instructor_id INT          PRIMARY KEY AUTO_INCREMENT,
    first_name    VARCHAR(50)  NOT NULL,
    last_name     VARCHAR(50)  NOT NULL,
    email         VARCHAR(100) UNIQUE,
    dept_id       INT,
    hire_date     DATE,
    salary        DECIMAL(10,2),
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
);

CREATE TABLE courses (
    course_id   INT          PRIMARY KEY AUTO_INCREMENT,
    course_code VARCHAR(10)  NOT NULL UNIQUE,  -- e.g. 'ITEC445'
    title       VARCHAR(150) NOT NULL,
    credits     TINYINT      NOT NULL DEFAULT 3,
    dept_id     INT,
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
);

CREATE TABLE students (
    student_id INT          PRIMARY KEY AUTO_INCREMENT,
    first_name VARCHAR(50)  NOT NULL,
    last_name  VARCHAR(50)  NOT NULL,
    email      VARCHAR(100) UNIQUE,
    gpa        DECIMAL(3,2),
    dept_id    INT,                            -- major department
    enroll_year YEAR,
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
);

CREATE TABLE enrollments (
    enrollment_id INT     PRIMARY KEY AUTO_INCREMENT,
    student_id    INT     NOT NULL,
    course_id     INT     NOT NULL,
    instructor_id INT,
    semester      CHAR(6) NOT NULL,            -- e.g. 'F2025'
    grade         CHAR(2),                     -- A, A-, B+, …, F, W, NULL=in-progress
    UNIQUE KEY uq_enroll (student_id, course_id, semester),
    FOREIGN KEY (student_id)    REFERENCES students(student_id),
    FOREIGN KEY (course_id)     REFERENCES courses(course_id),
    FOREIGN KEY (instructor_id) REFERENCES instructors(instructor_id)
);
```

!!! info "Schema Convention"
    A `NULL` grade means the student is still enrolled and the semester is not yet over. A grade of `'W'` means official withdrawal. We rely on these distinctions in many examples below.

---

## 1. JOIN Types — Syntax, Semantics, and Performance

A JOIN combines rows from two or more tables based on a related column. The choice of JOIN type determines which rows survive into the result set.

### 1.1 INNER JOIN

An INNER JOIN returns only rows where the join condition matches in **both** tables. It is the SQL default when you write just `JOIN`.

```sql
-- List every student and the courses they are currently enrolled in
SELECT  s.first_name,
        s.last_name,
        c.course_code,
        c.title,
        e.semester
FROM    students    s
INNER JOIN enrollments e ON e.student_id = s.student_id
INNER JOIN courses     c ON c.course_id  = e.course_id
WHERE   e.grade IS NULL          -- currently in progress
ORDER BY s.last_name, s.first_name;
```

!!! tip "Performance"
    INNER JOIN gives the optimizer the most freedom — it knows the result contains only matched rows, so it can choose hash joins, nested-loop joins, or merge joins freely. Always add appropriate indexes on join columns (here: `enrollments.student_id` and `enrollments.course_id`).

### 1.2 LEFT (OUTER) JOIN

Returns **all rows from the left table** plus matched rows from the right. Unmatched right-side columns are `NULL`.

```sql
-- Find ALL students, including those not enrolled in anything this semester
SELECT  s.student_id,
        s.first_name,
        s.last_name,
        COUNT(e.enrollment_id) AS courses_enrolled
FROM    students   s
LEFT JOIN enrollments e
       ON e.student_id = s.student_id
      AND e.semester   = 'F2025'        -- filter on the JOIN, not WHERE
GROUP BY s.student_id, s.first_name, s.last_name
ORDER BY courses_enrolled DESC;
```

!!! warning "LEFT JOIN + WHERE Pitfall"
    Placing the semester filter in the `WHERE` clause instead of the `ON` clause silently converts a LEFT JOIN into an INNER JOIN, because `WHERE e.semester = 'F2025'` eliminates all rows where `e.semester` is NULL (i.e., the unmatched students).

### 1.3 RIGHT (OUTER) JOIN

Returns **all rows from the right table** plus matched rows from the left. In practice, most developers rewrite as a LEFT JOIN with the tables swapped for clarity.

```sql
-- All courses offered this semester, including those with no students enrolled
SELECT  c.course_code,
        c.title,
        COUNT(e.enrollment_id) AS enrolled_count
FROM    enrollments e
RIGHT JOIN courses c ON c.course_id = e.course_id
                    AND e.semester  = 'F2025'
GROUP BY c.course_id, c.course_code, c.title
ORDER BY enrolled_count;
```

### 1.4 FULL OUTER JOIN

Returns **all rows from both tables**; unmatched sides are NULL. MySQL does not support `FULL OUTER JOIN` directly — emulate with `UNION`.

=== "PostgreSQL (native FULL OUTER JOIN)"
    ```sql
    -- Students and courses with no counterpart (data integrity audit)
    SELECT  s.student_id,
            s.last_name  AS student,
            c.course_id,
            c.course_code AS course
    FROM    students    s
    FULL OUTER JOIN enrollments e ON e.student_id = s.student_id
    FULL OUTER JOIN courses     c ON c.course_id  = e.course_id
    WHERE   s.student_id IS NULL OR c.course_id IS NULL;
    ```

=== "MySQL (UNION emulation)"
    ```sql
    -- Emulate FULL OUTER JOIN in MySQL
    SELECT s.student_id, s.last_name, e.course_id
    FROM   students s
    LEFT JOIN enrollments e ON e.student_id = s.student_id

    UNION

    SELECT s.student_id, s.last_name, e.course_id
    FROM   students s
    RIGHT JOIN enrollments e ON e.student_id = s.student_id
    WHERE  s.student_id IS NULL;
    ```

### 1.5 CROSS JOIN

Produces a **Cartesian product** — every row in the left table paired with every row in the right. Used deliberately for generating combinations; rarely accidental in modern SQL.

```sql
-- Generate all possible (student, course) combinations for schedule planning
SELECT  s.student_id,
        s.last_name,
        c.course_code
FROM    students s
CROSS JOIN courses c
WHERE   s.dept_id = c.dept_id   -- cross within the same department
ORDER BY s.last_name, c.course_code;
```

!!! danger "Cartesian Explosion"
    1,000 students × 500 courses = 500,000 rows. Always verify you have a meaningful limiting condition when using CROSS JOIN in production.

### 1.6 SELF JOIN

A table joined to itself — useful for hierarchical data, comparisons within the same table, or finding relationships between rows.

```sql
-- Find all instructors in the same department (exclude self-pairing)
SELECT  a.first_name AS instructor_a,
        b.first_name AS instructor_b,
        d.dept_name
FROM    instructors a
INNER JOIN instructors b ON a.dept_id = b.dept_id
                        AND a.instructor_id < b.instructor_id  -- avoid (A,B) and (B,A)
INNER JOIN departments d ON d.dept_id = a.dept_id
ORDER BY d.dept_name, a.last_name;
```

```sql
-- Students who enrolled the same semester as another student in the same course
SELECT  e1.student_id AS student1,
        e2.student_id AS student2,
        e1.course_id,
        e1.semester
FROM    enrollments e1
INNER JOIN enrollments e2
        ON e1.course_id = e2.course_id
       AND e1.semester  = e2.semester
       AND e1.student_id < e2.student_id;
```

### 1.7 JOIN Performance Summary

| JOIN Type | Result Rows | Index Use | Typical Cost | Use When |
|-----------|-------------|-----------|--------------|----------|
| INNER | Matching only | Optimal | Low–Medium | Most queries; reduces result set |
| LEFT | All left + matches | Good | Medium | "Show all X, optionally with Y" |
| RIGHT | All right + matches | Good | Medium | Same as LEFT (rewrite preferred) |
| FULL OUTER | All from both | Moderate | Medium–High | Data reconciliation, auditing |
| CROSS | n × m | No index help | Very High | Deliberate Cartesian product |
| SELF | Varies | Requires index on join col | Medium–High | Hierarchies, pair generation |

!!! note "Always Index Join Columns"
    Foreign key columns should always be indexed. Run `EXPLAIN` / `EXPLAIN ANALYZE` before deploying any multi-table query to production. Look for `Using filesort` or `Full table scan` as warning signs.

---

## 2. Subqueries

A **subquery** (or inner query) is a `SELECT` statement nested inside another SQL statement. Subqueries appear in the `SELECT`, `FROM`, `WHERE`, and `HAVING` clauses.

### 2.1 Scalar Subqueries

Returns exactly **one row, one column**. Can be used anywhere a single value is expected.

```sql
-- Show each student's GPA vs the department average
SELECT  s.first_name,
        s.last_name,
        s.gpa,
        (SELECT AVG(s2.gpa)
         FROM   students s2
         WHERE  s2.dept_id = s.dept_id) AS dept_avg_gpa,
        s.gpa - (SELECT AVG(s2.gpa)
                 FROM   students s2
                 WHERE  s2.dept_id = s.dept_id) AS gpa_delta
FROM    students s
ORDER BY gpa_delta DESC;
```

!!! warning "Scalar Subquery Cardinality"
    If the inner query returns more than one row, the database raises an error. Use `LIMIT 1` or aggregation to guarantee a single row.

### 2.2 Row Subqueries

Returns **one row with multiple columns**. Compared using row constructors.

```sql
-- Find students whose (dept, enroll_year) matches the most common combination
SELECT student_id, first_name, last_name
FROM   students
WHERE  (dept_id, enroll_year) = (
    SELECT dept_id, enroll_year
    FROM   students
    GROUP BY dept_id, enroll_year
    ORDER BY COUNT(*) DESC
    LIMIT 1
);
```

### 2.3 Table Subqueries (Derived Tables)

Returns **multiple rows and columns**; used in the `FROM` clause. MySQL requires an alias.

```sql
-- Average enrollment count per department
SELECT  d.dept_name,
        dept_stats.avg_courses
FROM    departments d
INNER JOIN (
    SELECT  s.dept_id,
            AVG(course_count) AS avg_courses
    FROM    students s
    INNER JOIN (
        SELECT  student_id, COUNT(*) AS course_count
        FROM    enrollments
        WHERE   semester = 'F2025'
        GROUP BY student_id
    ) AS ec ON ec.student_id = s.student_id
    GROUP BY s.dept_id
) AS dept_stats ON dept_stats.dept_id = d.dept_id
ORDER BY dept_stats.avg_courses DESC;
```

### 2.4 Correlated Subqueries

A correlated subquery references columns from the **outer query**. It executes once per outer row — powerful but potentially slow on large tables.

```sql
-- Students who have a GPA above their department's median
-- (correlated: references s.dept_id from outer query)
SELECT  s.student_id, s.first_name, s.last_name, s.gpa, s.dept_id
FROM    students s
WHERE   s.gpa > (
    SELECT AVG(s2.gpa)
    FROM   students s2
    WHERE  s2.dept_id = s.dept_id   -- correlated reference
);
```

!!! tip "Optimization"
    Many correlated subqueries can be rewritten as a JOIN with a derived table, allowing the optimizer to compute the aggregate once instead of once per row.

```sql
-- Equivalent rewrite — computes dept averages once
SELECT  s.student_id, s.first_name, s.last_name, s.gpa, s.dept_id
FROM    students s
INNER JOIN (
    SELECT dept_id, AVG(gpa) AS avg_gpa
    FROM   students
    GROUP BY dept_id
) avg ON avg.dept_id = s.dept_id
WHERE s.gpa > avg.avg_gpa;
```

---

## 3. EXISTS vs IN vs JOIN

Choosing among these three is one of the most consequential decisions in query writing.

=== "EXISTS"
    ```sql
    -- Students who are enrolled in at least one course this semester
    SELECT s.student_id, s.first_name, s.last_name
    FROM   students s
    WHERE  EXISTS (
        SELECT 1
        FROM   enrollments e
        WHERE  e.student_id = s.student_id
          AND  e.semester   = 'F2025'
    );
    ```
    **Best for:** Semi-join patterns; checking *existence* without needing data from the inner table.
    **Performance:** Short-circuits as soon as one matching row is found. Excellent on large inner tables with an index on the join column.

=== "IN"
    ```sql
    -- Students enrolled in at least one course this semester (IN version)
    SELECT student_id, first_name, last_name
    FROM   students
    WHERE  student_id IN (
        SELECT student_id
        FROM   enrollments
        WHERE  semester = 'F2025'
    );
    ```
    **Best for:** Small, static result sets; column IN (list of values).
    **Performance:** The entire subquery executes first; result is materialized as a list. Degrades with large inner result sets. **NULL issues:** `IN` with NULLs returns UNKNOWN (not TRUE), which can cause surprising behavior.

=== "JOIN"
    ```sql
    -- Students enrolled this semester (JOIN version)
    SELECT DISTINCT s.student_id, s.first_name, s.last_name
    FROM   students s
    INNER JOIN enrollments e ON e.student_id = s.student_id
                             AND e.semester  = 'F2025';
    ```
    **Best for:** When you need columns from the joined table too. `DISTINCT` required to avoid duplicates if a student has multiple enrollments.
    **Performance:** The optimizer has more strategies available. Modern optimizers often rewrite EXISTS/IN as JOINs internally.

### 3.1 NOT EXISTS vs NOT IN — Critical Difference

```sql
-- Correct: Students NOT enrolled this semester (NOT EXISTS)
SELECT s.student_id, s.first_name
FROM   students s
WHERE  NOT EXISTS (
    SELECT 1 FROM enrollments e
    WHERE  e.student_id = s.student_id
      AND  e.semester   = 'F2025'
);

-- DANGEROUS: If ANY enrollment has a NULL student_id, returns NO ROWS
SELECT student_id, first_name
FROM   students
WHERE  student_id NOT IN (
    SELECT student_id FROM enrollments WHERE semester = 'F2025'
    -- If student_id is NULLable, this subquery can return NULLs,
    -- making the entire NOT IN return empty
);
```

!!! danger "NOT IN with NULLs"
    Always prefer `NOT EXISTS` over `NOT IN` when the subquery column might contain NULLs. `x NOT IN (1, 2, NULL)` is UNKNOWN (not TRUE) for every value of x, because SQL cannot confirm that x is not equal to the unknown NULL value.

---

## 4. Set Operations

Set operations combine the results of two or more `SELECT` statements. Both queries must have the **same number of columns** with compatible data types.

### 4.1 UNION and UNION ALL

```sql
-- UNION: All distinct email addresses from students and instructors
SELECT email, 'student'    AS role FROM students
UNION
SELECT email, 'instructor' AS role FROM instructors
ORDER BY email;

-- UNION ALL: Include duplicates (faster — no deduplication step)
SELECT course_id FROM enrollments WHERE semester = 'F2024'
UNION ALL
SELECT course_id FROM enrollments WHERE semester = 'F2025';
```

### 4.2 INTERSECT

Returns only rows present in **both** result sets.

=== "PostgreSQL"
    ```sql
    -- Courses offered in both Fall 2024 and Fall 2025
    SELECT course_id FROM enrollments WHERE semester = 'F2024'
    INTERSECT
    SELECT course_id FROM enrollments WHERE semester = 'F2025';
    ```

=== "MySQL (emulation)"
    ```sql
    -- MySQL 8.0.31+ supports INTERSECT natively; for older versions:
    SELECT DISTINCT e1.course_id
    FROM   enrollments e1
    INNER JOIN enrollments e2 ON e2.course_id = e1.course_id
                              AND e2.semester = 'F2025'
    WHERE  e1.semester = 'F2024';
    ```

### 4.3 EXCEPT / MINUS

Returns rows from the **first query** that do not appear in the second. Called `EXCEPT` in PostgreSQL/SQL Server; `MINUS` in Oracle.

=== "PostgreSQL"
    ```sql
    -- Courses in Fall 2024 that were NOT offered in Fall 2025
    SELECT course_id FROM enrollments WHERE semester = 'F2024'
    EXCEPT
    SELECT course_id FROM enrollments WHERE semester = 'F2025';
    ```

=== "MySQL (emulation)"
    ```sql
    -- MySQL 8.0.31+ supports EXCEPT; for older versions:
    SELECT DISTINCT e24.course_id
    FROM   enrollments e24
    WHERE  e24.semester = 'F2024'
      AND  e24.course_id NOT IN (
               SELECT course_id
               FROM   enrollments
               WHERE  semester = 'F2025'
           );
    ```

### 4.4 Set Operation Performance Comparison

| Operation | Deduplication | Relative Cost | MySQL Native Support |
|-----------|--------------|---------------|----------------------|
| UNION ALL | None | Lowest | Yes (all versions) |
| UNION | Yes (sort/hash) | Low–Medium | Yes (all versions) |
| INTERSECT | Yes | Medium | 8.0.31+ |
| EXCEPT | Yes | Medium | 8.0.31+ |

!!! tip "Prefer UNION ALL"
    When you know duplicates are impossible or acceptable, always use `UNION ALL`. The deduplication step in `UNION` requires sorting or hashing the entire combined result — a significant cost on large datasets.

---

## 5. Multi-Table UPDATE and DELETE

### 5.1 Multi-Table UPDATE with JOIN

```sql
-- Give a 5% salary raise to instructors in departments that have a budget > 500,000
UPDATE instructors i
INNER JOIN departments d ON d.dept_id = i.dept_id
SET    i.salary = i.salary * 1.05
WHERE  d.budget > 500000;
```

```sql
-- Reset grade to NULL for students who withdrew (W) from a course
-- where the instructor was subsequently terminated (not in instructors table)
UPDATE enrollments e
LEFT JOIN instructors i ON i.instructor_id = e.instructor_id
SET    e.grade = 'W'
WHERE  i.instructor_id IS NULL
  AND  e.grade IS NULL;
```

!!! warning "Always Test with SELECT First"
    Before running any multi-table UPDATE or DELETE, replace `UPDATE`/`DELETE` with a `SELECT *` using the same join conditions to preview which rows will be affected.

### 5.2 Multi-Table DELETE with JOIN

```sql
-- Delete enrollment records for students who have graduated (no longer in students table)
DELETE e
FROM   enrollments e
LEFT JOIN students s ON s.student_id = e.student_id
WHERE  s.student_id IS NULL;
```

```sql
-- Delete a student and all their enrollments atomically
-- (assumes FK with ON DELETE CASCADE is not set)
DELETE s, e
FROM   students s
INNER JOIN enrollments e ON e.student_id = s.student_id
WHERE  s.student_id = 1042;
```

!!! note "PostgreSQL DELETE with USING"
    PostgreSQL uses `USING` instead of JOIN in DELETE:
    ```sql
    DELETE FROM enrollments e
    USING  students s
    WHERE  s.student_id = e.student_id
      AND  s.student_id = 1042;
    ```

---

## 6. Real-World Query Patterns

### 6.1 Finding Duplicate Records

```sql
-- Detect students with the same name (potential duplicate entries)
SELECT   first_name, last_name, COUNT(*) AS occurrences
FROM     students
GROUP BY first_name, last_name
HAVING   COUNT(*) > 1
ORDER BY occurrences DESC;

-- Get full details of the duplicates
SELECT  s.*
FROM    students s
INNER JOIN (
    SELECT first_name, last_name
    FROM   students
    GROUP BY first_name, last_name
    HAVING COUNT(*) > 1
) dups ON dups.first_name = s.first_name
       AND dups.last_name  = s.last_name
ORDER BY s.last_name, s.first_name, s.student_id;
```

### 6.2 Detecting Gaps in Sequences

```sql
-- Find gaps in student_id sequence (e.g., after bulk deletes)
SELECT  a.student_id + 1 AS gap_start,
        MIN(b.student_id) - 1 AS gap_end
FROM    students a
INNER JOIN students b ON b.student_id > a.student_id
GROUP BY a.student_id
HAVING   gap_start < MIN(b.student_id)
ORDER BY gap_start;
```

### 6.3 Top-N per Group

```sql
-- Top 3 students by GPA in each department
SELECT  dept_name, first_name, last_name, gpa
FROM (
    SELECT  d.dept_name,
            s.first_name,
            s.last_name,
            s.gpa,
            ROW_NUMBER() OVER (
                PARTITION BY s.dept_id
                ORDER BY s.gpa DESC
            ) AS dept_rank
    FROM    students s
    INNER JOIN departments d ON d.dept_id = s.dept_id
    WHERE   s.gpa IS NOT NULL
) ranked
WHERE  dept_rank <= 3
ORDER BY dept_name, dept_rank;
```

!!! success "Row Number vs Rank"
    `ROW_NUMBER()` always produces distinct ranks (no ties). Use `RANK()` if you want tied students to share a rank. We cover window functions in depth in Week 2.

---

## Key Vocabulary

| Term | Definition |
|------|------------|
| **INNER JOIN** | Returns rows matching in both tables |
| **LEFT JOIN** | All rows from left table; NULLs for unmatched right |
| **FULL OUTER JOIN** | All rows from both tables; NULLs for unmatched sides |
| **CROSS JOIN** | Cartesian product — every left row paired with every right row |
| **SELF JOIN** | A table joined to itself using an alias |
| **Subquery** | A SELECT statement nested inside another SQL statement |
| **Scalar subquery** | Returns exactly one row and one column |
| **Correlated subquery** | References columns from the outer query; executes per outer row |
| **Derived table** | Subquery in the FROM clause; must be aliased in MySQL |
| **EXISTS** | Predicate that returns TRUE if the subquery returns at least one row |
| **Semi-join** | Logical join pattern returning left rows only if a match exists (implemented via EXISTS or IN) |
| **UNION** | Combines query results and removes duplicates |
| **UNION ALL** | Combines query results keeping all rows (no deduplication) |
| **INTERSECT** | Returns rows common to both result sets |
| **EXCEPT / MINUS** | Returns rows in first result set not in the second |
| **Cartesian product** | All combinations of rows between two tables |
| **Cardinality** | Number of rows a subquery or table expression returns |
| **Short-circuit evaluation** | EXISTS stops scanning as soon as one match is found |
| **Multi-table DELETE** | DELETE with JOIN to remove rows based on related table data |
| **Top-N per group** | Pattern returning the N best rows in each partition |

---

!!! question "Self-Assessment"
    1. A query returns duplicate rows when you replace `LEFT JOIN … WHERE col IS NULL` with `NOT IN`. Explain exactly why this happens and how to fix it.
    2. You have a query that uses a correlated subquery to find the maximum enrollment semester for each student. It works correctly but takes 45 seconds on 500,000 rows. Rewrite it using a derived table and explain why it is faster.
    3. Write a single SQL query (no procedural code) that identifies all courses that have been offered every semester in the enrollments table for the last four semesters. Which set operation or join pattern is most appropriate?
    4. Explain the output difference between `UNION` and `UNION ALL` when combining two identical SELECT statements. Give a scenario where each is the correct choice.
    5. You need to delete all enrollments for students whose GPA has dropped below 1.0, but only for courses in the Computer Science department. Write the multi-table DELETE statement and the safe SELECT preview version.

---

## Further Reading

- 📖 *Learning MySQL*, Chapter 6 — "Performing Joins and Subqueries"
- 📖 *PostgreSQL: Up and Running*, Chapter 7 — "Writing SQL Queries"
- 📄 [MySQL 8.0 Reference — JOIN Syntax](https://dev.mysql.com/doc/refman/8.0/en/join.html)
- 📄 [MySQL 8.0 Reference — Subquery Optimization](https://dev.mysql.com/doc/refman/8.0/en/subquery-optimization.html)
- 📄 [Use The Index, Luke — Nested Loops, Hash Joins, Sort-Merge Joins](https://use-the-index-luke.com/sql/join)
- 📄 [PostgreSQL EXPLAIN Documentation](https://www.postgresql.org/docs/current/sql-explain.html)
- 🎥 CMU 15-445 Lecture 11 — "Join Algorithms" (freely available on YouTube)

---

*[Course Index](index.md) &nbsp;|&nbsp; [Week 2 →](week02.md)*
