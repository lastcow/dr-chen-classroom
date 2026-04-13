---
title: "Week 6 — Index Design & Query Performance"
description: Master B-tree internals, index types, composite index design, covering indexes, and practical strategies for diagnosing and fixing slow queries through smart indexing.
---

# Week 6 — Index Design & Query Performance

<div class="week-meta" markdown>
**Course Objectives:** CO4 &nbsp;|&nbsp; **Focus:** Index Design &nbsp;|&nbsp; **Difficulty:** ⭐⭐⭐☆☆
</div>

---

## Learning Objectives

By the end of this week, you will be able to:

- [ ] Explain B-tree structure and how MySQL traverses a B-tree index to satisfy a query
- [ ] Distinguish between PRIMARY KEY, UNIQUE, non-unique, FULLTEXT, SPATIAL, and composite indexes
- [ ] Apply the leftmost prefix rule to design composite indexes correctly
- [ ] Identify when a query uses a covering index and explain why it avoids table lookups
- [ ] Interpret the output of `SHOW INDEX FROM` and `information_schema.STATISTICS`
- [ ] Justify when *not* to create an index based on cardinality, table size, and write load
- [ ] Use `OPTIMIZE TABLE` and invisible indexes to maintain and safely test index changes
- [ ] Create functional indexes and indexes on generated columns to support JSON queries
- [ ] Diagnose and fix slow `ORDER BY`, `WHERE`, and `JOIN` queries by adding appropriate indexes

---

## 1. Index Fundamentals: The B-Tree Data Structure

An **index** is a separate on-disk data structure that MySQL maintains alongside a table. Its sole purpose is to let the storage engine locate rows matching a condition without scanning every row in the table. Understanding *why* indexes work requires a brief tour of B-tree internals.

### 1.1 B-Tree Architecture

A **balanced tree (B-tree)** organizes data in a hierarchical structure with three kinds of nodes:

```
                    ┌─────────────────────────────┐
                    │  ROOT NODE (non-leaf)         │
                    │  [40] [70]                    │
                    └──────┬─────────┬─────────────┘
                           │         │
             ┌─────────────┘         └──────────────┐
     ┌───────▼──────┐               ┌───────▼──────┐
     │ INTERNAL NODE │               │ INTERNAL NODE │
     │  [10][20][30] │               │  [50][60]     │
     └──┬──┬──┬──┬──┘               └────┬────┬────┘
        │  │  │  │                        │    │
   ┌────▼─┐│┌─▼──┐                  ┌────▼─┐ ┌▼────┐
   │LEAF  ││ │LEAF│  ...             │LEAF  │ │LEAF │
   │1,5,8 ││ │10- │                  │50-55 │ │60-68│
   │→data ││ │19  │                  │→data │ │→data│
   └──────┘│ └────┘                  └──────┘ └─────┘
```

**Key properties of InnoDB B-tree indexes:**

| Property | Detail |
|----------|--------|
| **Page size** | Default 16 KB per node (configurable via `innodb_page_size`) |
| **Leaf nodes** | Store the actual indexed column value(s) **plus** the primary key value |
| **Non-leaf nodes** | Store only separator keys and child page pointers |
| **Balance** | All leaf nodes are at the same depth — O(log n) lookups guaranteed |
| **Doubly-linked leaves** | Leaf pages are linked left-to-right enabling range scans |

### 1.2 How MySQL Traverses a B-Tree

When you run `SELECT * FROM students WHERE student_id = 1042`, MySQL:

1. Reads the **root page** of the PRIMARY KEY index into the buffer pool
2. Compares `1042` against separator keys to determine which child branch to follow
3. Descends through **internal nodes** (each read = one I/O unless cached)
4. Arrives at the **leaf node** containing the record data (InnoDB clustered index stores the full row)

For a table with 1 million rows and 16 KB pages, the tree is typically **3–4 levels deep** — meaning most lookups require only 3–4 page reads instead of scanning all ~60,000 pages of a full table.

!!! info "Clustered vs. Secondary Indexes"
    In InnoDB, the **primary key IS the clustered index** — the table data is physically stored in B-tree leaf order. Secondary indexes store `(indexed_column, primary_key_value)` in their leaves. A secondary index lookup therefore requires **two** tree traversals: one to find the primary key, then one to read the full row. This is the **table lookup** (also called a row lookup or bookmark lookup) that covering indexes eliminate.

### 1.3 InnoDB Page Internals

```sql
-- Check your server's page size
SHOW VARIABLES LIKE 'innodb_page_size';
-- Default: 16384 (16 KB)

-- Estimate index tree height for a table
SELECT
    TABLE_NAME,
    INDEX_NAME,
    STAT_VALUE AS leaf_pages
FROM mysql.innodb_index_stats
WHERE stat_name = 'n_leaf_pages'
  AND database_name = 'university';
```

!!! tip "Changing Page Size"
    `innodb_page_size` must be set at **initialization time** and cannot be changed afterward. Use 4 KB pages for SSD workloads with many small random I/Os; stick with 16 KB (default) for general OLTP use. Larger pages (32/64 KB) help sequential scan workloads but waste space for random access patterns.

---

## 2. Index Types in MySQL 8

### 2.1 Primary Key and Unique Indexes

```sql
-- Primary key: clustered, NOT NULL, unique
CREATE TABLE students (
    student_id   INT          NOT NULL AUTO_INCREMENT,
    email        VARCHAR(100) NOT NULL,
    first_name   VARCHAR(50)  NOT NULL,
    last_name    VARCHAR(50)  NOT NULL,
    dept_id      INT,
    gpa          DECIMAL(3,2),
    enrolled_on  DATE,
    is_active    TINYINT(1)   DEFAULT 1,
    PRIMARY KEY (student_id),
    UNIQUE KEY uq_students_email (email)
);

-- Composite primary key (junction table)
CREATE TABLE enrollments (
    student_id  INT  NOT NULL,
    course_id   INT  NOT NULL,
    semester    CHAR(6) NOT NULL,   -- e.g. '2024FA'
    grade       CHAR(2),
    PRIMARY KEY (student_id, course_id, semester)
);
```

### 2.2 Non-Unique (INDEX) and Composite Indexes

```sql
-- Non-unique index for foreign key lookups
ALTER TABLE students
    ADD INDEX idx_students_dept (dept_id);

-- Composite index for common query pattern
ALTER TABLE enrollments
    ADD INDEX idx_enr_student_semester (student_id, semester);

-- Covering composite index for reporting
ALTER TABLE grades
    ADD INDEX idx_grades_cover (student_id, course_id, points, max_points);
```

### 2.3 FULLTEXT and SPATIAL Indexes

=== "FULLTEXT Index"

    FULLTEXT indexes support natural-language search and boolean-mode queries on `CHAR`, `VARCHAR`, and `TEXT` columns. They use an **inverted index** structure rather than B-tree.

    ```sql
    CREATE TABLE courses (
        course_id    INT         NOT NULL AUTO_INCREMENT,
        course_code  VARCHAR(10) NOT NULL,
        title        VARCHAR(120) NOT NULL,
        description  TEXT,
        PRIMARY KEY (course_id),
        FULLTEXT KEY ft_courses_desc (title, description)
    );

    -- Natural language search
    SELECT course_id, title,
           MATCH(title, description) AGAINST ('database optimization') AS relevance
    FROM courses
    WHERE MATCH(title, description) AGAINST ('database optimization')
    ORDER BY relevance DESC;

    -- Boolean mode
    SELECT title FROM courses
    WHERE MATCH(title, description)
          AGAINST ('+database -introductory' IN BOOLEAN MODE);
    ```

    !!! warning "FULLTEXT Minimum Word Length"
        By default, `ft_min_word_len = 4`. Words shorter than 4 characters are ignored. Adjust with `innodb_ft_min_token_size` for InnoDB tables and rebuild the index.

=== "SPATIAL Index"

    SPATIAL indexes accelerate geometry queries (R-tree structure). Columns must use a spatial data type.

    ```sql
    CREATE TABLE campus_buildings (
        building_id  INT NOT NULL AUTO_INCREMENT,
        name         VARCHAR(80) NOT NULL,
        location     POINT NOT NULL SRID 4326,   -- WGS 84
        PRIMARY KEY (building_id),
        SPATIAL INDEX sp_buildings_loc (location)
    );

    INSERT INTO campus_buildings (name, location) VALUES
    ('Lane Center', ST_GeomFromText('POINT(-78.8292 39.6563)', 4326));

    -- Find buildings within 500 meters of a point
    SELECT name
    FROM campus_buildings
    WHERE ST_Distance_Sphere(location,
          ST_GeomFromText('POINT(-78.829 39.656)', 4326)) <= 500;
    ```

---

## 3. How MySQL Uses Indexes

### 3.1 Access Types: From Best to Worst

The `type` column in `EXPLAIN` reveals how MySQL accesses the table. Understanding these is critical for optimization (covered in detail in Week 7).

| Access Type | Description | Typical Scenario |
|-------------|-------------|-----------------|
| `system` | Table has 0 or 1 row | System tables |
| `const` | At most one matching row via PRIMARY KEY or UNIQUE | `WHERE id = 5` |
| `eq_ref` | One row per row from previous table; best JOIN type | JOIN on PRIMARY KEY |
| `ref` | Multiple rows match; non-unique index lookup | `WHERE dept_id = 3` |
| `range` | Indexed range scan | `WHERE gpa BETWEEN 3.0 AND 4.0` |
| `index` | Full index scan (all leaves) | Covers query but reads whole index |
| `ALL` | Full table scan — **avoid for large tables** | No usable index |

### 3.2 Index Range Scans

MySQL can use an index to satisfy range predicates (`<`, `>`, `BETWEEN`, `IN`, `LIKE 'prefix%'`):

```sql
-- Range scan on gpa index
EXPLAIN SELECT student_id, first_name, gpa
FROM students
WHERE gpa BETWEEN 3.5 AND 4.0;
-- type: range   key: idx_students_gpa   Extra: Using index condition
```

The engine locates the first qualifying leaf page, then follows leaf-level pointers rightward until the range is exhausted — a very efficient sequential read pattern.

### 3.3 Index Skip Scans (MySQL 8.0.13+)

Before MySQL 8, a composite index `(dept_id, gpa)` could not be used for `WHERE gpa > 3.5` alone. The skip scan optimizer optimization allows MySQL to **simulate multiple range scans**, one per distinct `dept_id` value:

```sql
-- composite index (dept_id, gpa)
ALTER TABLE students ADD INDEX idx_dept_gpa (dept_id, gpa);

-- MySQL 8 may use skip scan even without dept_id in WHERE
EXPLAIN SELECT student_id, gpa
FROM students
WHERE gpa > 3.5;
-- Extra: Using index for skip scan
```

!!! note "Skip Scan Caveat"
    Skip scans are only beneficial when the **leading column has low cardinality** (few distinct values). If `dept_id` has 500 distinct values, skip scan degenerates to 500 separate range scans and the optimizer will prefer a table scan.

### 3.4 Covering Indexes

A **covering index** is one that satisfies all columns referenced by a query — `SELECT` list, `WHERE`, `ORDER BY`, `GROUP BY` — without needing to touch the actual row data:

```sql
-- Without covering index: secondary index lookup + table lookup
SELECT first_name, last_name, gpa FROM students WHERE dept_id = 3;

-- Add covering index
ALTER TABLE students
    ADD INDEX idx_dept_cover (dept_id, last_name, first_name, gpa);

-- Now EXPLAIN shows: Extra: Using index  (no table lookup!)
EXPLAIN SELECT first_name, last_name, gpa
FROM students
WHERE dept_id = 3
ORDER BY last_name;
```

!!! success "Covering Index Performance Gain"
    For a reporting query scanning 50,000 rows in a secondary index, avoiding table lookups can reduce I/O by **10×–50×** because index pages are much denser than full row data pages.

---

## 4. Composite Index Design

### 4.1 The Leftmost Prefix Rule

MySQL can use a composite index `(a, b, c)` for queries that reference **a prefix of the index columns, starting from the left**:

| Query Predicate | Can Use `(a, b, c)`? | Which Prefix |
|-----------------|---------------------|--------------|
| `WHERE a = ?` | ✅ Yes | (a) |
| `WHERE a = ? AND b = ?` | ✅ Yes | (a, b) |
| `WHERE a = ? AND b = ? AND c = ?` | ✅ Yes | (a, b, c) |
| `WHERE b = ?` | ❌ No | — |
| `WHERE b = ? AND c = ?` | ❌ No | — |
| `WHERE a = ? AND c = ?` | ⚠️ Partial | (a) only; c not used |
| `WHERE a BETWEEN ? AND ?` | ✅ Yes (range on a) | stops at a |
| `WHERE a = ? AND b BETWEEN ? AND ?` | ✅ Yes | (a) eq, (b) range |

```sql
-- University query: students in a dept, sorted by last name
-- Best index: (dept_id, last_name, first_name)
ALTER TABLE students
    ADD INDEX idx_dept_name (dept_id, last_name, first_name);

SELECT student_id, first_name, last_name
FROM students
WHERE dept_id = 7
ORDER BY last_name, first_name;
-- Uses index for both filtering AND sorting — no filesort!
```

### 4.2 Cardinality and Selectivity

**Cardinality** = number of distinct values in an indexed column.  
**Selectivity** = cardinality ÷ total rows (ranges from 0 to 1; higher = more selective = better for indexing).

```sql
-- Measure selectivity before deciding to index
SELECT
    COUNT(DISTINCT dept_id)  / COUNT(*) AS dept_selectivity,     -- ~0.003 (low)
    COUNT(DISTINCT email)    / COUNT(*) AS email_selectivity,    -- ~1.000 (high)
    COUNT(DISTINCT gpa)      / COUNT(*) AS gpa_selectivity,      -- ~0.04  (medium)
    COUNT(DISTINCT last_name)/ COUNT(*) AS name_selectivity      -- ~0.15  (medium)
FROM students;
```

!!! warning "Low Selectivity Indexes"
    An index on `is_active` (values 0 or 1) has selectivity ≈ 0.5 for an equal split. If 95% of rows are active, `WHERE is_active = 1` returns 95% of rows — the optimizer will choose a full table scan because the index provides no real filtering benefit.

### 4.3 Column Order Strategy

For composite indexes, place columns in this priority order:

1. **Equality predicates first** (highest cardinality → most selective)
2. **Range predicate column** (must be last useful column — range stops prefix use)
3. **ORDER BY columns** (if they match index order, no filesort needed)
4. **SELECT list columns** (to make it a covering index)

```sql
-- Query: enrollments for a student in a semester, ordered by course
-- Predicate: student_id = ? AND semester = ?  ORDER BY course_id
ALTER TABLE enrollments
    ADD INDEX idx_enr_stu_sem_crs (student_id, semester, course_id);
```

---

## 5. Index Statistics and Maintenance

### 5.1 SHOW INDEX and information_schema.STATISTICS

```sql
-- Full index information for a table
SHOW INDEX FROM students\G

-- Via information_schema (scriptable)
SELECT
    INDEX_NAME,
    SEQ_IN_INDEX,
    COLUMN_NAME,
    CARDINALITY,
    INDEX_TYPE,
    NON_UNIQUE,
    NULLABLE
FROM information_schema.STATISTICS
WHERE TABLE_SCHEMA = 'university'
  AND TABLE_NAME   = 'students'
ORDER BY INDEX_NAME, SEQ_IN_INDEX;
```

Key columns to understand:

| Column | Meaning |
|--------|---------|
| `CARDINALITY` | Estimated distinct values — updated by ANALYZE TABLE or auto-recalc |
| `SEQ_IN_INDEX` | Position of column in composite index (1 = leftmost) |
| `NON_UNIQUE` | 0 = unique (PK or UNIQUE KEY), 1 = non-unique |
| `INDEX_TYPE` | BTREE, FULLTEXT, or HASH (Memory engine) |
| `SUB_PART` | Prefix length if only part of column is indexed |

### 5.2 ANALYZE TABLE and Statistics Accuracy

InnoDB estimates cardinality by **sampling random leaf pages** (default 8 pages via `innodb_stats_persistent_sample_pages`). For large tables, this estimate can be wildly inaccurate, causing the optimizer to choose wrong indexes.

```sql
-- Force statistics recalculation (reads more pages for accuracy)
SET SESSION innodb_stats_transient_sample_pages = 100;
ANALYZE TABLE students, courses, enrollments;

-- Check when stats were last updated
SELECT TABLE_NAME, UPDATE_TIME, TABLE_ROWS
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'university';
```

!!! tip "Persistent vs Transient Statistics"
    With `innodb_stats_persistent = ON` (default), statistics are stored in `mysql.innodb_table_stats` and `mysql.innodb_index_stats` and survive server restarts. With `innodb_stats_auto_recalc = ON`, InnoDB automatically triggers ANALYZE when roughly 10% of rows change — but this can cause sudden plan changes in production.

### 5.3 Index Fragmentation and OPTIMIZE TABLE

InnoDB B-tree pages fill up as rows are inserted and empty out as rows are deleted, creating **page fragmentation**. Heavy DELETE/UPDATE workloads cause wasted space and slower range scans.

```sql
-- Check fragmentation level
SELECT
    TABLE_NAME,
    DATA_LENGTH,
    INDEX_LENGTH,
    DATA_FREE,
    ROUND(DATA_FREE / (DATA_LENGTH + INDEX_LENGTH) * 100, 1) AS frag_pct
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'university'
ORDER BY frag_pct DESC;

-- Rebuild table + all indexes (locks table in MySQL 5.x, online in 8.x)
OPTIMIZE TABLE enrollments;

-- Alternative: ALTER TABLE ... ALGORITHM=INPLACE (online, non-blocking)
ALTER TABLE enrollments
    ENGINE = InnoDB,
    ALGORITHM = INPLACE,
    LOCK = NONE;
```

!!! warning "OPTIMIZE TABLE on Production"
    `OPTIMIZE TABLE` acquires a table-level lock and can take **minutes to hours** on large tables. Schedule during maintenance windows, or use `pt-online-schema-change` (Percona Toolkit) for zero-downtime rebuilds.

---

## 6. Advanced Index Features (MySQL 8)

### 6.1 Invisible Indexes

MySQL 8.0 introduced **invisible indexes** — indexes that exist and are maintained but are completely ignored by the optimizer. This lets you safely test what removing an index would do without actually dropping it:

```sql
-- Make an index invisible (optimizer ignores it)
ALTER TABLE students
    ALTER INDEX idx_students_dept INVISIBLE;

-- Verify current visibility
SELECT INDEX_NAME, IS_VISIBLE
FROM information_schema.STATISTICS
WHERE TABLE_SCHEMA = 'university'
  AND TABLE_NAME = 'students'
GROUP BY INDEX_NAME, IS_VISIBLE;

-- Force optimizer to use invisible indexes (for testing in this session only)
SET SESSION optimizer_switch = 'use_invisible_indexes=on';

-- Make visible again if needed
ALTER TABLE students
    ALTER INDEX idx_students_dept VISIBLE;

-- Safe to drop after confirming no performance regression
DROP INDEX idx_students_dept ON students;
```

!!! success "Invisible Index Workflow"
    1. Make index invisible → monitor for slow queries (hours/days)  
    2. If no regression → drop index safely  
    3. If regression → make visible instantly (no rebuild needed)  
    This is vastly safer than dropping and recreating (rebuild cost).

### 6.2 Functional (Expression) Indexes

MySQL 8.0.13+ supports indexes on **expressions**, eliminating the need for generated columns in many cases:

```sql
-- Problem: query uses YEAR() on a date column — can't use regular index
SELECT student_id FROM students
WHERE YEAR(enrolled_on) = 2023;  -- forces full table scan!

-- Solution 1: Functional index (MySQL 8.0.13+)
ALTER TABLE students
    ADD INDEX idx_enroll_year ((YEAR(enrolled_on)));

-- Now this uses the index:
EXPLAIN SELECT student_id FROM students
WHERE YEAR(enrolled_on) = 2023;

-- Solution 2: Functional index for case-insensitive search
ALTER TABLE students
    ADD INDEX idx_lastname_lower ((LOWER(last_name)));

SELECT student_id FROM students
WHERE LOWER(last_name) = 'chen';
```

!!! info "PostgreSQL Expression Indexes"
    PostgreSQL has supported expression indexes since version 7.1:
    ```sql
    -- PostgreSQL
    CREATE INDEX idx_students_lower_email
        ON students (LOWER(email));
    CREATE INDEX idx_enrolled_year
        ON students (EXTRACT(YEAR FROM enrolled_on));
    ```

### 6.3 Indexes on Generated Columns for JSON

When storing JSON documents, you need indexes on specific JSON paths. The pattern is to create a **virtual generated column** and index it:

```sql
-- Table storing student preferences as JSON
ALTER TABLE students
    ADD COLUMN pref_json JSON,
    ADD COLUMN major_code VARCHAR(10)
        AS (JSON_UNQUOTE(JSON_EXTRACT(pref_json, '$.major'))) VIRTUAL,
    ADD INDEX idx_major_code (major_code);

-- Insert with JSON
UPDATE students
SET pref_json = '{"major": "CS", "minor": "Math", "advisor_id": 42}'
WHERE student_id = 1001;

-- This now uses the index on the generated column:
SELECT student_id, first_name
FROM students
WHERE major_code = 'CS';

-- MySQL 8 shorthand with functional index on JSON path:
ALTER TABLE students
    ADD INDEX idx_json_major ((JSON_UNQUOTE(JSON_EXTRACT(pref_json, '$.major'))));
```

---

## 7. When NOT to Index & Real-World Scenarios

### 7.1 Cases Where Indexes Hurt

| Situation | Reason Not to Index |
|-----------|-------------------|
| **Low-cardinality column** (e.g., `is_active`, `gender`) | Optimizer skips index; DML overhead pointless |
| **Small table** (< ~1,000 rows) | Full table scan reads 1–2 pages — faster than index I/O |
| **Write-heavy tables** (>80% INSERT/UPDATE/DELETE) | Every write updates all indexes; can slow writes 10× |
| **Rarely queried column** | Index consumes space and write overhead for no read benefit |
| **Duplicate/redundant index** | `(a, b)` makes standalone `(a)` redundant |
| **Already covered by leftmost prefix** | `(a)` makes `(a, b)` cover queries needing only `a` |

```sql
-- Find redundant indexes using sys schema
SELECT * FROM sys.schema_redundant_indexes
WHERE table_schema = 'university';

-- Find unused indexes (zero selects since last restart)
SELECT * FROM sys.schema_unused_indexes
WHERE object_schema = 'university';
```

### 7.2 Scenario: Fixing a Slow ORDER BY

```sql
-- Slow: full table scan + filesort
SELECT student_id, last_name, first_name, gpa
FROM students
WHERE dept_id = 4
ORDER BY gpa DESC
LIMIT 10;
-- EXPLAIN: type=ALL, Extra=Using where; Using filesort

-- Fix: composite index — equality first, then range/sort column
ALTER TABLE students
    ADD INDEX idx_dept_gpa_desc (dept_id, gpa DESC);

-- Now: type=ref, Extra=Using index condition  (no filesort!)
```

### 7.3 Scenario: Fixing a Slow JOIN

```sql
-- Slow join: missing index on FK side
SELECT s.first_name, s.last_name, c.title, e.grade
FROM students s
JOIN enrollments e ON s.student_id = e.student_id
JOIN courses c     ON e.course_id  = c.course_id
WHERE s.dept_id = 5
  AND e.semester = '2024FA';

-- Check: enrollments.student_id and enrollments.course_id indexed?
SHOW INDEX FROM enrollments;

-- Add if missing:
ALTER TABLE enrollments
    ADD INDEX idx_enr_student (student_id),
    ADD INDEX idx_enr_course  (course_id),
    ADD INDEX idx_enr_stu_sem (student_id, semester);
```

### 7.4 Scenario: Covering Index for a Reporting Query

```sql
-- Report: grade distribution per department per semester
-- Runs every night — must be fast
SELECT
    d.dept_name,
    e.semester,
    AVG(g.points / g.max_points * 100) AS avg_score,
    COUNT(*)                             AS enrollment_count
FROM enrollments e
JOIN students  s ON e.student_id = s.student_id
JOIN departments d ON s.dept_id = d.dept_id
JOIN grades    g ON e.student_id = g.student_id
                 AND e.course_id  = g.course_id
WHERE e.semester = '2024FA'
GROUP BY d.dept_name, e.semester;

-- Covering index on grades eliminates all row lookups:
ALTER TABLE grades
    ADD INDEX idx_grades_rpt (student_id, course_id, points, max_points);

-- Covering index on enrollments:
ALTER TABLE enrollments
    ADD INDEX idx_enr_sem_stu_crs (semester, student_id, course_id);
```

---

## 8. Key Vocabulary

| Term | Definition |
|------|------------|
| **B-tree** | Balanced tree data structure used by most MySQL indexes; O(log n) lookup |
| **Clustered index** | Index where leaf nodes contain actual row data; InnoDB primary key |
| **Secondary index** | Any non-clustered index; leaf nodes store (key, primary key) |
| **Table lookup** | Extra read of the clustered index to fetch columns not in secondary index |
| **Covering index** | Index containing all columns needed by a query; eliminates table lookup |
| **Composite index** | Index defined on two or more columns |
| **Leftmost prefix rule** | MySQL can use composite index `(a,b,c)` only if query references columns from the left |
| **Cardinality** | Number of distinct values in an indexed column |
| **Selectivity** | Cardinality ÷ total rows; higher = more discriminating index |
| **Index range scan** | Traverses a contiguous portion of B-tree leaves using inequality predicates |
| **Index skip scan** | MySQL 8 optimization simulating multiple range scans to bypass leftmost prefix rule |
| **FULLTEXT index** | Inverted index structure for natural-language text search |
| **Invisible index** | MySQL 8 feature: index maintained but ignored by optimizer for safe testing |
| **Functional index** | Index defined on an expression rather than a raw column value |
| **Generated column** | Column whose value is computed from an expression; can be VIRTUAL or STORED |
| **Fragmentation** | Wasted space in index pages from deletions and updates; remedied by OPTIMIZE TABLE |
| **ANALYZE TABLE** | Command that recalculates index cardinality statistics |
| **Index merge** | Optimizer reads multiple indexes and merges results; often indicates a design issue |
| **Page size** | Fixed unit of storage in InnoDB (default 16 KB); determines B-tree branching factor |
| **Filesort** | In-memory or on-disk sort operation when ORDER BY cannot be satisfied by index order |

---

## Self-Assessment

!!! question "Self-Assessment"
    1. A table has a composite index `(dept_id, semester, course_id)`. For each of the following queries, state whether the index is used, and if so, which prefix: (a) `WHERE dept_id = 3`, (b) `WHERE semester = '2024FA'`, (c) `WHERE dept_id = 3 AND course_id = 101`, (d) `WHERE dept_id = 3 AND semester = '2024FA' AND course_id = 101`.

    2. You have a table `enrollments` with 5 million rows. `EXPLAIN` shows `type=ALL` on the query `SELECT * FROM enrollments WHERE grade = 'A'`. The `grade` column has only 13 distinct values (A, A-, B+, B, …, F). Explain why adding an index on `grade` alone is unlikely to help, and propose a better indexing strategy for a common application query pattern.

    3. Describe the sequence of steps you would follow to safely test whether removing an index from a production table (500 GB, 1,000 QPS) causes query regressions. Which MySQL 8 feature makes this safe and what `information_schema` view do you check first?

    4. A developer reports that the query `SELECT student_id FROM students WHERE UPPER(last_name) = 'SMITH'` is slow despite a B-tree index on `last_name`. Explain the root cause and provide two different solutions — one using a functional index and one using a generated column.

    5. Explain the difference between a **covering index** and a **composite index**. Can a single index be both? Give a concrete SQL example using the university schema where a 4-column composite index serves as a covering index, and identify which columns serve which role (filter, sort, payload).

---

## Further Reading

- 📖 *High Performance MySQL, 4th Edition* — Chapter 8: Indexing for High Performance (O'Reilly)
- 📖 *MySQL 8.0 Reference Manual* — [Section 8.3: Optimization and Indexes](https://dev.mysql.com/doc/refman/8.0/en/optimization-indexes.html)
- 📄 [InnoDB Index Structures](https://dev.mysql.com/doc/internals/en/innodb-page-structure.html) — MySQL Internals Manual
- 📄 [Use The Index, Luke](https://use-the-index-luke.com/) — Free book-quality reference on SQL indexing (database-agnostic)
- 📄 [MySQL 8.0: Invisible Indexes](https://dev.mysql.com/blog-archive/mysql-8-0-invisible-indexes/) — MySQL Server Blog
- 📄 [Percona: Practical MySQL Indexing Guidelines](https://www.percona.com/blog/practical-mysql-indexing-guidelines/)
- 🎥 MySQL EXPLAIN Demystified — Percona Live talk (YouTube)

---

[← Week 5](week05.md) | [Course Index](index.md) | [Week 7 →](week07.md)
