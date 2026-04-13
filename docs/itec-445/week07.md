---
title: "Week 7 — Query Execution Plans & Advanced Optimization"
description: Learn to read EXPLAIN output, interpret query execution plans in MySQL and PostgreSQL, diagnose anti-patterns, rewrite slow queries, and tune memory buffers for sustained performance.
---

# Week 7 — Query Execution Plans & Advanced Optimization

<div class="week-meta" markdown>
**Course Objectives:** CO4, CO1 &nbsp;|&nbsp; **Focus:** Query Optimization &nbsp;|&nbsp; **Difficulty:** ⭐⭐⭐⭐☆
</div>

---

## Learning Objectives

By the end of this week, you will be able to:

- [ ] Interpret every column of tabular `EXPLAIN` output and identify the access type hierarchy
- [ ] Use `EXPLAIN FORMAT=JSON` and `EXPLAIN ANALYZE` to obtain actual row counts and timing
- [ ] Read PostgreSQL `EXPLAIN ANALYZE` output including cost estimates and buffer statistics
- [ ] Identify the join algorithm (nested loop, hash join, merge join) from execution plan output
- [ ] Apply optimizer hints (`USE INDEX`, `FORCE INDEX`, `STRAIGHT_JOIN`) to guide the optimizer
- [ ] Enable and configure the slow query log and use `pt-query-digest` to prioritize optimizations
- [ ] Recognize and rewrite the eight most damaging SQL anti-patterns
- [ ] Adjust `innodb_buffer_pool_size`, `join_buffer_size`, and `sort_buffer_size` based on workload

---

## 1. EXPLAIN: Reading MySQL Execution Plans

`EXPLAIN` (or `DESCRIBE`) prepends MySQL's chosen execution plan to a query without actually running it. It is the single most important diagnostic tool for query optimization.

### 1.1 The EXPLAIN Columns

```sql
-- Basic EXPLAIN
EXPLAIN
SELECT s.first_name, s.last_name, c.title, e.grade
FROM students  s
JOIN enrollments e ON s.student_id = e.student_id
JOIN courses   c   ON e.course_id  = c.course_id
WHERE s.dept_id = 5
  AND e.semester = '2024FA'
ORDER BY s.last_name;
```

Sample output:

```
+----+-------------+-------+--------+---------------------+-------------------+---------+----------------------+------+-------------------------------+
| id | select_type | table | type   | possible_keys       | key               | key_len | ref                  | rows | Extra                         |
+----+-------------+-------+--------+---------------------+-------------------+---------+----------------------+------+-------------------------------+
|  1 | SIMPLE      | s     | ref    | PRIMARY,idx_dept    | idx_dept          | 4       | const                |  120 | Using index condition; Using filesort |
|  1 | SIMPLE      | e     | ref    | idx_enr_stu_sem     | idx_enr_stu_sem   | 8       | university.s.student_id,const | 3 | Using index                 |
|  1 | SIMPLE      | c     | eq_ref | PRIMARY             | PRIMARY           | 4       | university.e.course_id|   1 | NULL                          |
+----+-------------+-------+--------+---------------------+-------------------+---------+----------------------+------+-------------------------------+
```

| Column | Meaning |
|--------|---------|
| `id` | Query block number; subqueries get higher IDs; same ID = same SELECT |
| `select_type` | `SIMPLE`, `PRIMARY`, `SUBQUERY`, `DERIVED`, `UNION`, `UNION RESULT` |
| `table` | Table name or alias; `<derived2>` = materialized subquery |
| `type` | **Access type** — the most critical column (see below) |
| `possible_keys` | Indexes MySQL considered; NULL = no candidate |
| `key` | Index MySQL actually chose; NULL = no index used |
| `key_len` | Bytes of index used; reveals how many columns of composite index used |
| `ref` | Column or constant matched against the key |
| `rows` | Estimated rows examined (cumulative for joins) |
| `filtered` | Estimated percentage of rows surviving WHERE (show with EXPLAIN EXTENDED or MySQL 5.7+) |
| `Extra` | Additional information — often more revealing than `type` |

### 1.2 The Access Type Hierarchy

=== "Best Types (seek)"

    | Type | Description | When You See It |
    |------|-------------|----------------|
    | `system` | Single-row system table | Internal; cannot engineer |
    | `const` | Primary key or unique index equality | `WHERE pk = 5` |
    | `eq_ref` | One row per driving-table row; unique index | JOIN on PK/UNIQUE |
    | `ref` | Non-unique index equality | `WHERE dept_id = 3` |

    ```sql
    -- const example
    EXPLAIN SELECT * FROM students WHERE student_id = 1001;
    -- type: const  (lookup returns at most one row)

    -- eq_ref example
    EXPLAIN SELECT s.*, d.dept_name
    FROM students s JOIN departments d ON s.dept_id = d.dept_id;
    -- s: type=ALL (or ref), d: type=eq_ref on PRIMARY
    ```

=== "Acceptable Types (scan partial)"

    | Type | Description | When You See It |
    |------|-------------|----------------|
    | `ref_or_null` | Like `ref` but also matches NULL | `WHERE col = ? OR col IS NULL` |
    | `index_merge` | Multiple indexes merged | `WHERE a=1 OR b=2` with separate indexes |
    | `range` | Indexed range | `BETWEEN`, `<`, `>`, `IN()`, `LIKE 'x%'` |
    | `index` | Full index scan | All leaves read; covers query |

    ```sql
    -- range example
    EXPLAIN SELECT student_id, gpa FROM students
    WHERE gpa BETWEEN 3.0 AND 3.5;
    -- type: range   key: idx_gpa

    -- index_merge example (usually a design smell)
    EXPLAIN SELECT student_id FROM students
    WHERE dept_id = 3 OR is_active = 0;
    -- type: index_merge   Extra: Using union(idx_dept,idx_active)
    ```

=== "Bad Type (avoid)"

    | Type | Description | Problem |
    |------|-------------|---------|
    | `ALL` | Full table scan | Reads every row; catastrophic at scale |

    ```sql
    -- ALL is acceptable ONLY on tiny tables or when intentional
    EXPLAIN SELECT * FROM students WHERE gpa > 1.0;
    -- If 99% of students qualify, ALL may be correct
    -- But on a 2-million row table: disaster
    ```

### 1.3 Decoding the Extra Column

The `Extra` column carries critical diagnostic information:

| Extra Value | Meaning | Action |
|-------------|---------|--------|
| `Using index` | Covering index — no table lookup | ✅ Optimal |
| `Using where` | WHERE applied after index fetch | Usually fine |
| `Using index condition` | Index Condition Pushdown (ICP) active | ✅ Good |
| `Using filesort` | Extra sort pass needed | Add/adjust index to match ORDER BY |
| `Using temporary` | Temp table for GROUP BY/DISTINCT | Often indicates missing index or poor join |
| `Using join buffer` | Nested loop using buffer (no index on join key) | Add index on join column |
| `Impossible WHERE` | Condition can never be true | Check your WHERE clause logic |
| `Select tables optimized away` | Aggregate on indexed column resolved at plan time | ✅ |

---

## 2. EXPLAIN FORMAT=JSON and EXPLAIN ANALYZE

### 2.1 EXPLAIN FORMAT=JSON

The JSON format reveals details hidden in tabular form: actual cost estimates, index dive counts, subquery materialization decisions:

```sql
EXPLAIN FORMAT=JSON
SELECT s.last_name, COUNT(e.course_id) AS courses
FROM students s
LEFT JOIN enrollments e ON s.student_id = e.student_id
WHERE s.dept_id = 3
GROUP BY s.student_id, s.last_name\G
```

Key JSON fields to examine:

```json
{
  "query_block": {
    "cost_info": { "query_cost": "145.20" },
    "grouping_operation": {
      "using_filesort": false,
      "using_temporary_table": true,
      "nested_loop": [
        {
          "table": {
            "table_name": "s",
            "access_type": "ref",
            "index": "idx_dept",
            "rows_examined_per_scan": 120,
            "rows_produced_per_join": 120,
            "cost_info": { "read_cost": "12.00", "eval_cost": "12.00" }
          }
        }
      ]
    }
  }
}
```

### 2.2 EXPLAIN ANALYZE (MySQL 8.0.18+)

`EXPLAIN ANALYZE` **actually executes the query** and returns both estimated and actual statistics:

```sql
EXPLAIN ANALYZE
SELECT s.last_name, AVG(g.points) AS avg_pts
FROM students s
JOIN grades g ON s.student_id = g.student_id
WHERE s.dept_id = 5
GROUP BY s.student_id, s.last_name\G
```

Sample output:

```
-> Group aggregate: avg(g.points)  (actual time=0.089..18.432 rows=98 loops=1)
    -> Nested loop inner join  (actual time=0.078..17.105 rows=490 loops=1)
        -> Index lookup on s using idx_dept (dept_id=5)
           (cost=12.30 rows=98) (actual time=0.045..0.812 rows=98 loops=1)
        -> Index lookup on g using idx_grades_stu (student_id=s.student_id)
           (cost=0.98 rows=5) (actual time=0.016..0.165 rows=5 loops=98)
```

!!! info "Interpreting actual vs. estimated rows"
    If `rows=1000` (estimated) vs `actual rows=50000`, the optimizer had **bad statistics** — run `ANALYZE TABLE` and re-check. A large mismatch is the #1 cause of bad plan choices.

!!! warning "EXPLAIN ANALYZE Executes the Query"
    Unlike `EXPLAIN`, `EXPLAIN ANALYZE` runs the full query (including writes in DML statements with MySQL 8.0.19+). Never run `EXPLAIN ANALYZE` on a large `DELETE` or `UPDATE` in production without wrapping it in a transaction you immediately roll back.

---

## 3. PostgreSQL EXPLAIN ANALYZE

PostgreSQL's planner outputs rich cost and timing data. The format differs significantly from MySQL.

### 3.1 Reading PostgreSQL Plans

```sql
-- PostgreSQL
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT s.last_name, c.title, e.grade
FROM students  s
JOIN enrollments e ON s.student_id = e.student_id
JOIN courses   c   ON e.course_id  = c.course_id
WHERE s.dept_id = 5
  AND e.semester = '2024FA';
```

Sample output:

```
Hash Join  (cost=215.40..890.12 rows=320 width=80)
           (actual time=3.421..18.234 rows=287 loops=1)
  Hash Cond: (e.course_id = c.course_id)
  Buffers: shared hit=142 read=23
  ->  Hash Join  (cost=108.20..760.34 rows=320 width=60)
                 (actual time=1.823..14.105 rows=287 loops=1)
        Hash Cond: (e.student_id = s.student_id)
        Buffers: shared hit=98 read=18
        ->  Bitmap Heap Scan on enrollments e
              (cost=4.52..630.10 rows=1280 width=30)
              (actual time=0.134..8.342 rows=1156 loops=1)
              Recheck Cond: (semester = '2024FA')
              ->  Bitmap Index Scan on idx_enr_semester
                    (cost=0.00..4.20 rows=1280 width=0)
                    (actual time=0.089..0.089 rows=1156 loops=1)
```

| Field | Explanation |
|-------|-------------|
| `cost=X..Y` | Startup cost (first row) .. total cost in arbitrary units |
| `actual time=X..Y` | Milliseconds to first row .. milliseconds total |
| `rows=N` | Estimated (plan) or actual (analyze) row count |
| `loops=N` | How many times this node was executed |
| `shared hit=N` | Pages served from shared buffer pool (RAM) |
| `shared read=N` | Pages read from disk (I/O) |

### 3.2 Join Algorithms in PostgreSQL

=== "Nested Loop Join"

    **Best for:** Small inner table or index exists on inner join key.

    ```
    Nested Loop  (cost=0.42..850.12 rows=50 width=60)
      ->  Index Scan on students s using idx_dept (dept_id=5)
      ->  Index Scan on enrollments e using idx_enr_stu (student_id=s.student_id)
    ```

    Each row from the outer table triggers an inner index lookup. O(n × log m) complexity.

=== "Hash Join"

    **Best for:** Larger tables, no useful index on join key.

    ```
    Hash Join  (cost=215.40..890.12 rows=320 width=80)
      Hash Cond: (e.student_id = s.student_id)
      ->  Seq Scan on enrollments e
      ->  Hash
            ->  Seq Scan on students s
                  Filter: (dept_id = 5)
    ```

    Build a hash table from the smaller relation, probe it with each row of the larger. Memory-bound: if hash table overflows, PostgreSQL spills to disk (batched hash join).

=== "Merge Join"

    **Best for:** Both inputs are sorted (index scans) on the join key.

    ```
    Merge Join  (cost=0.85..420.30 rows=287 width=80)
      Merge Cond: (s.student_id = e.student_id)
      ->  Index Scan on students s using PRIMARY
      ->  Index Scan on enrollments e using idx_enr_student
    ```

    Simultaneously advances through both sorted streams. O(n + m) after sorting — extremely efficient when indexes provide pre-sorted data.

---

## 4. Optimizer Hints and Switches

### 4.1 MySQL Optimizer Hints

When the optimizer makes a wrong choice, you can guide it with hints. Use sparingly — hints lock in a plan that may become wrong as data changes.

```sql
-- USE INDEX: restrict candidate indexes
SELECT * FROM students USE INDEX (idx_dept_gpa)
WHERE dept_id = 3 AND gpa > 3.5;

-- FORCE INDEX: use this index even if optimizer thinks table scan is cheaper
SELECT * FROM enrollments FORCE INDEX (idx_enr_stu_sem)
WHERE student_id = 1001 AND semester = '2024FA';

-- IGNORE INDEX: exclude a specific index
SELECT * FROM students IGNORE INDEX (idx_lastname)
WHERE last_name = 'Chen';

-- STRAIGHT_JOIN: force table join order exactly as written
SELECT STRAIGHT_JOIN s.*, e.*
FROM students s
JOIN enrollments e ON s.student_id = e.student_id
WHERE s.dept_id = 3;

-- NO_MERGE hint (MySQL 8): prevent derived table from being merged
SELECT /*+ NO_MERGE(dept_avg) */ s.first_name, dept_avg.avg_gpa
FROM students s
JOIN (SELECT dept_id, AVG(gpa) AS avg_gpa
      FROM students GROUP BY dept_id) dept_avg
  ON s.dept_id = dept_avg.dept_id;
```

!!! tip "Optimizer Hint Syntax (MySQL 8)"
    MySQL 8 introduced `/*+ hint_name(table) */` inside the SELECT keyword for more precise control:
    ```sql
    SELECT /*+ BKA(e) NO_BNL(s) */ s.last_name, e.grade
    FROM students s JOIN enrollments e ...
    ```

### 4.2 MySQL Optimizer Switches

`optimizer_switch` is a session/global variable containing comma-separated feature flags:

```sql
-- See all optimizer switches
SHOW VARIABLES LIKE 'optimizer_switch'\G

-- Common switches to tune
SET SESSION optimizer_switch =
    'block_nested_loop=off,'    -- disable BNL; prefer hash join (MySQL 8)
    'batched_key_access=on,'    -- enable BKA for index-based joins
    'mrr=on,'                   -- Multi-Range Read: random → sequential I/O
    'mrr_cost_based=on';        -- Let optimizer decide when to use MRR

-- Disable hash join for a session (MySQL 8 default: on)
SET SESSION optimizer_switch = 'hash_join=off';
```

| Switch | Effect |
|--------|--------|
| `block_nested_loop` | Buffer-based NL join for tables without join index |
| `hash_join` | Hash join algorithm (MySQL 8+); usually superior to BNL |
| `batched_key_access` | Read joined rows in batches for better cache efficiency |
| `mrr` | Convert random secondary index lookups to sorted primary key reads |
| `use_index_extensions` | Use PK columns appended to secondary index implicitly |
| `condition_fanout_filter` | Better row estimate for multi-predicate WHERE |

---

## 5. Slow Query Log and pt-query-digest

### 5.1 Enabling the Slow Query Log

```sql
-- Enable and configure (MySQL)
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL slow_query_log_file = '/var/log/mysql/slow.log';
SET GLOBAL long_query_time = 1.0;           -- seconds; 0 logs EVERYTHING
SET GLOBAL log_queries_not_using_indexes = 'ON';
SET GLOBAL log_slow_verbosity = 'query_plan,innodb';  -- Percona/MariaDB

-- Verify
SHOW VARIABLES LIKE 'slow%';
SHOW VARIABLES LIKE 'long_query_time';
```

```ini
# my.cnf persistent configuration
[mysqld]
slow_query_log          = 1
slow_query_log_file     = /var/log/mysql/slow.log
long_query_time         = 1
log_queries_not_using_indexes = 1
min_examined_row_limit  = 100   # don't log fast queries that examine few rows
```

### 5.2 Reading Raw Slow Query Log Entries

```
# Time: 2024-11-15T14:23:07.481925Z
# User@Host: app_user[app_user] @ webserver01 [10.0.1.15]
# Query_time: 4.823115  Lock_time: 0.000142  Rows_sent: 50  Rows_examined: 1847320
# Bytes_sent: 8240
SET timestamp=1731680587;
SELECT s.first_name, s.last_name, AVG(g.points)
FROM students s JOIN grades g ON s.student_id = g.student_id
WHERE YEAR(s.enrolled_on) = 2022
GROUP BY s.student_id;
```

Key metrics: `Query_time` (wall clock), `Rows_examined` vs `Rows_sent` ratio (1,847,320 : 50 = terrible!).

### 5.3 pt-query-digest Analysis

```bash
# Install Percona Toolkit
sudo apt-get install percona-toolkit

# Analyze slow log — groups similar queries by fingerprint
pt-query-digest /var/log/mysql/slow.log \
    --limit 10 \
    --since '2024-11-01 00:00:00' \
    --until '2024-11-15 23:59:59' \
    > /tmp/digest_report.txt

# Output summary for each query class:
# Rank Query ID           Response time    Calls  R/Call  V/M  Item
# ==== ================== ================ ======= ======= ==== ====
# 1    0xA1B2C3D4E5F6...  142.3300 38.2%      87   1.6359  0.62 SELECT students grades

# Send report directly to a database table for trend analysis
pt-query-digest /var/log/mysql/slow.log \
    --review h=localhost,D=query_review,t=query_review_history \
    --history h=localhost,D=query_review,t=query_history
```

!!! info "pt-query-digest Fingerprinting"
    pt-query-digest replaces literal values with `?` to group structurally identical queries:
    `WHERE student_id = 1001` and `WHERE student_id = 9999` become the same fingerprint.
    This lets you see the **total impact** of a query pattern, not just individual occurrences.

---

## 6. Common Anti-Patterns and Rewrites

### 6.1 Functions on Indexed Columns

```sql
-- ❌ ANTI-PATTERN: function prevents index use
SELECT * FROM students WHERE YEAR(enrolled_on) = 2023;
SELECT * FROM students WHERE UPPER(last_name)  = 'CHEN';
SELECT * FROM enrollments WHERE DATE(created_at) = '2024-11-01';

-- ✅ REWRITE: transform predicate to range or use functional index
SELECT * FROM students
WHERE enrolled_on >= '2023-01-01' AND enrolled_on < '2024-01-01';

SELECT * FROM students WHERE last_name = 'Chen';  -- rely on collation for case

SELECT * FROM enrollments
WHERE created_at >= '2024-11-01 00:00:00'
  AND created_at <  '2024-11-02 00:00:00';
```

### 6.2 Implicit Type Conversion

```sql
-- student_id is INT; passing string causes implicit CAST
-- ❌ ANTI-PATTERN
SELECT * FROM students WHERE student_id = '1001';
-- MySQL silently converts '1001' → 1001, but:

-- ❌ Worse: indexed VARCHAR column compared to integer
-- index on email (VARCHAR); comparing to integer loses index
SELECT * FROM students WHERE email = 12345;
-- MySQL converts ALL email values to numbers: full table scan!

-- ✅ Always match data types exactly
SELECT * FROM students WHERE email = 'jsmith@frostburg.edu';
```

!!! danger "Type Mismatch = Full Table Scan"
    When a function or implicit cast is applied to an **indexed column**, MySQL cannot use the index because the index stores original values, not transformed ones. This is among the most common causes of unexpected full table scans reported in production.

### 6.3 SELECT * and Wide Projections

```sql
-- ❌ ANTI-PATTERN: SELECT * prevents covering indexes, wastes bandwidth
SELECT * FROM students WHERE dept_id = 3;

-- ✅ Select only needed columns — enables covering index opportunities
SELECT student_id, first_name, last_name, gpa
FROM students WHERE dept_id = 3;
```

### 6.4 LIKE with Leading Wildcard

```sql
-- ❌ Cannot use B-tree index — must scan all index leaves
SELECT * FROM courses WHERE title LIKE '%database%';

-- ✅ Option 1: trailing wildcard only — uses index
SELECT * FROM courses WHERE title LIKE 'Database%';

-- ✅ Option 2: FULLTEXT index for contains-style search
SELECT * FROM courses
WHERE MATCH(title, description) AGAINST ('database' IN BOOLEAN MODE);
```

### 6.5 OR Across Columns / IN with Large Lists

```sql
-- ❌ OR across different indexed columns often degrades to table scan
SELECT * FROM students WHERE dept_id = 3 OR last_name = 'Smith';

-- ✅ UNION rewrites each branch to use its own index
SELECT * FROM students WHERE dept_id = 3
UNION ALL
SELECT * FROM students WHERE last_name = 'Smith' AND dept_id <> 3;

-- ❌ IN with thousands of values: optimizer may give up
SELECT * FROM enrollments WHERE student_id IN (1,2,3,...,50000);

-- ✅ Use a JOIN or temporary table instead
CREATE TEMPORARY TABLE target_students (student_id INT PRIMARY KEY);
INSERT INTO target_students VALUES (1),(2),(3),...;
SELECT e.* FROM enrollments e JOIN target_students t USING (student_id);
```

### 6.6 EXISTS vs. IN for Subqueries

```sql
-- ❌ IN with correlated subquery: may execute subquery once per outer row
SELECT * FROM students
WHERE student_id IN (
    SELECT student_id FROM enrollments WHERE semester = '2024FA'
);

-- ✅ EXISTS short-circuits on first match (especially with index on inner column)
SELECT * FROM students s
WHERE EXISTS (
    SELECT 1 FROM enrollments e
    WHERE e.student_id = s.student_id AND e.semester = '2024FA'
);

-- ✅ Even better: semi-join rewrite (optimizer may do this automatically in MySQL 8)
SELECT DISTINCT s.*
FROM students s
JOIN enrollments e ON s.student_id = e.student_id
WHERE e.semester = '2024FA';
```

---

## 7. Optimizer Statistics and Buffer Tuning

### 7.1 Keeping Statistics Accurate

```sql
-- InnoDB auto-recalculates when 10% of rows change (innodb_stats_auto_recalc = ON)
-- For tables with >1M rows, 10% threshold means stats can be stale for a long time

-- Increase sample pages for accuracy (global setting)
SET GLOBAL innodb_stats_persistent_sample_pages = 50;  -- default: 20

-- Manual recalculation for critical tables
ANALYZE TABLE students, courses, enrollments, grades;

-- Check the raw statistics tables
SELECT * FROM mysql.innodb_table_stats WHERE database_name = 'university';
SELECT * FROM mysql.innodb_index_stats
WHERE database_name = 'university'
  AND table_name = 'enrollments'\G
```

### 7.2 InnoDB Buffer Pool Tuning

The **buffer pool** is InnoDB's main memory cache for data and index pages. It is the single most impactful memory setting.

```sql
-- See current size and hit rate
SHOW VARIABLES LIKE 'innodb_buffer_pool_size';

SELECT
    ROUND(TP.variable_value / 1024 / 1024, 0) AS pool_mb,
    ROUND(HR.variable_value / (HR.variable_value + RD.variable_value) * 100, 2) AS hit_rate_pct
FROM performance_schema.global_status TP
JOIN performance_schema.global_status HR ON HR.variable_name = 'Innodb_buffer_pool_read_requests'
JOIN performance_schema.global_status RD ON RD.variable_name = 'Innodb_buffer_pool_reads'
WHERE TP.variable_name = 'Innodb_buffer_pool_pages_total';
```

```ini
# Rule of thumb: 70–80% of available RAM on a dedicated DB server
[mysqld]
innodb_buffer_pool_size     = 12G        # for a 16 GB server
innodb_buffer_pool_instances = 8         # one per GB; reduces mutex contention
innodb_buffer_pool_chunk_size = 128M     # pool_size must be multiple of chunk × instances
```

!!! tip "Buffer Pool Hit Rate Target"
    Aim for **> 99% hit rate**. A hit rate of 95% means 1 in 20 page reads goes to disk — catastrophic for latency. If hit rate is low, increase `innodb_buffer_pool_size` before any query-level tuning.

### 7.3 Sort and Join Buffers

```sql
-- Sort buffer: allocated per sort operation per thread
SET GLOBAL sort_buffer_size = 4 * 1024 * 1024;   -- 4 MB default; 8–16 MB for heavy sorts

-- Join buffer: used when join has no index (nested loop + buffer)
SET GLOBAL join_buffer_size = 8 * 1024 * 1024;   -- 256 KB default; increase for hash joins

-- Read buffer for sequential scans
SET GLOBAL read_buffer_size = 2 * 1024 * 1024;   -- 128 KB default

-- Check memory usage summary
SELECT event_name, current_alloc, high_alloc
FROM sys.memory_global_by_current_bytes
ORDER BY current_alloc DESC
LIMIT 20;
```

!!! warning "Per-Thread Memory Multiplier"
    `sort_buffer_size` and `join_buffer_size` are allocated **per connection**, not globally. With 500 concurrent connections and 16 MB sort buffer, peak memory consumption = 500 × 16 MB = **8 GB** — potentially OOM-killing MySQL. Set these conservatively and rely on buffer pool tuning instead.

---

## 8. Practical Optimization Workflow

### 8.1 The Optimization Loop

```
1. Identify slow query (slow log, performance_schema, monitoring alert)
         ↓
2. EXPLAIN — examine type, key, rows, Extra
         ↓
3. EXPLAIN FORMAT=JSON — check cost estimates, subquery strategies
         ↓
4. EXPLAIN ANALYZE — get actual vs. estimated row counts
         ↓
5. ANALYZE TABLE — fix stale statistics if estimates are wildly off
         ↓
6. Rewrite query — eliminate anti-patterns
         ↓
7. Add/modify indexes — cover query, fix access type
         ↓
8. Verify with EXPLAIN ANALYZE — confirm improvement
         ↓
9. Monitor in production — check slow log, performance_schema
```

### 8.2 Performance Schema for Live Diagnosis

```sql
-- Top 10 slowest statements since server start
SELECT DIGEST_TEXT, COUNT_STAR, AVG_TIMER_WAIT/1e9 AS avg_sec,
       SUM_ROWS_EXAMINED, SUM_ROWS_SENT
FROM performance_schema.events_statements_summary_by_digest
ORDER BY AVG_TIMER_WAIT DESC
LIMIT 10;

-- Tables with most full table scans
SELECT OBJECT_NAME, COUNT_READ, COUNT_FETCH
FROM performance_schema.table_io_waits_summary_by_table
WHERE COUNT_FETCH > 0
ORDER BY COUNT_FETCH DESC
LIMIT 10;

-- Index usage statistics
SELECT OBJECT_NAME, INDEX_NAME, COUNT_FETCH, COUNT_INSERT, COUNT_UPDATE, COUNT_DELETE
FROM performance_schema.table_io_waits_summary_by_index_usage
WHERE OBJECT_SCHEMA = 'university'
ORDER BY COUNT_FETCH DESC;
```

---

## Key Vocabulary

| Term | Definition |
|------|------------|
| **EXPLAIN** | MySQL/PostgreSQL command that outputs the optimizer's chosen execution plan |
| **access type** | How MySQL accesses a table: `const`, `ref`, `range`, `index`, `ALL` |
| **eq_ref** | Best join access type: exactly one row per driving-table row via unique index |
| **filesort** | MySQL's internal sort pass when ORDER BY cannot be resolved by index order |
| **covering index** | Index satisfying all query columns; eliminates table lookups |
| **ICP (Index Condition Pushdown)** | Optimizer pushes WHERE evaluation into storage engine during index scan |
| **nested loop join** | Join algorithm: for each outer row, probe inner table |
| **hash join** | Build hash table from smaller relation; probe with larger; O(n+m) |
| **merge join** | Simultaneously traverse two sorted inputs; requires sorted order |
| **EXPLAIN ANALYZE** | Executes query and returns both estimated and actual plan statistics |
| **slow query log** | MySQL log of queries exceeding `long_query_time` threshold |
| **pt-query-digest** | Percona Toolkit tool for parsing and aggregating slow query logs |
| **query fingerprint** | Query with literal values replaced by `?`; used to group similar queries |
| **optimizer hint** | Directive embedded in SQL to guide optimizer choices |
| **optimizer_switch** | MySQL server variable containing feature flags controlling optimizer behavior |
| **buffer pool hit rate** | Ratio of pages served from RAM vs. disk; target > 99% |
| **innodb_buffer_pool_size** | Main InnoDB memory cache; most impactful MySQL memory setting |
| **sort_buffer_size** | Per-thread buffer for sort operations; over-provisioning causes OOM risk |
| **MRR (Multi-Range Read)** | Optimization converting random secondary index lookups into sorted PK reads |
| **index merge** | Optimizer reads two indexes and merges results; usually indicates design issue |

---

## Self-Assessment

!!! question "Self-Assessment"
    1. A query's EXPLAIN shows `type=ALL, rows=2000000, Extra=Using where` on the `enrollments` table. The query is `SELECT * FROM enrollments WHERE semester = '2024FA' AND grade = 'A'`. The `enrollments` table has a composite index `(student_id, semester)`. Explain exactly why this index is not used, then design the optimal index for this query.

    2. EXPLAIN ANALYZE reports `rows=500` (estimated) vs. `actual rows=89000` for a scan on the `grades` table. What is the most likely cause of this discrepancy? What command(s) do you run to fix it, and what server variable controls how aggressively InnoDB auto-collects statistics?

    3. A developer writes the following query that runs in 8 seconds on a 10-million-row `enrollments` table: `SELECT * FROM enrollments WHERE DATE(created_at) = '2024-11-01'`. The `created_at` column has a B-tree index. Explain why the index is not used and provide two rewrites — one that uses the existing index and one that uses a functional index.

    4. Your DBA reports that `innodb_buffer_pool_size` is set to 2 GB on a dedicated 32 GB server. The buffer pool hit rate is 87%. Describe the performance impact of this misconfiguration, calculate an appropriate new value, and explain the relationship between `innodb_buffer_pool_instances` and `innodb_buffer_pool_chunk_size` that must be satisfied.

    5. You need to optimize a reporting query that joins `students`, `departments`, `enrollments`, and `grades` and takes 45 seconds. Walk through the full optimization workflow: what tools you use at each step, what outputs you examine, what specific information tells you whether to rewrite the query, add an index, or tune memory settings.

---

## Further Reading

- 📖 *High Performance MySQL, 4th Edition* — Chapter 9: Query Performance Optimization (O'Reilly)
- 📖 *MySQL 8.0 Reference Manual* — [Section 8.8: Understanding the Query Execution Plan](https://dev.mysql.com/doc/refman/8.0/en/execution-plan-information.html)
- 📄 [EXPLAIN ANALYZE in MySQL 8.0.18](https://dev.mysql.com/blog-archive/mysql-explain-analyze/) — MySQL Server Blog
- 📄 [Percona Toolkit Documentation: pt-query-digest](https://docs.percona.com/percona-toolkit/pt-query-digest.html)
- 📄 [PostgreSQL EXPLAIN Documentation](https://www.postgresql.org/docs/current/sql-explain.html)
- 📄 [Use The Index, Luke: Explain Plan](https://use-the-index-luke.com/sql/explain-plan) — Database-agnostic EXPLAIN guide
- 📄 [MySQL Performance Schema Quick Start](https://dev.mysql.com/doc/refman/8.0/en/performance-schema-quick-start.html)
- 🎥 *Query Optimization with EXPLAIN* — Percona Live (YouTube)

---

[← Week 6](week06.md) | [Course Index](index.md) | [Week 8 →](week08.md)
