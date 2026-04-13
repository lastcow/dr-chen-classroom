---
title: "Week 5 — Data Import & Export: Formats, Tools & ETL"
description: Master every method for moving data into and out of MySQL — from LOAD DATA INFILE and mysqldump to JSON_TABLE, Python ETL pipelines, and large-dataset bulk loading strategies.
---

# Week 5 — Data Import & Export: Formats, Tools & ETL

<div class="week-meta" markdown>
**Course Objectives:** CO3 &nbsp;|&nbsp; **Focus:** Data Movement, ETL Pipelines & Bulk Loading &nbsp;|&nbsp; **Difficulty:** ⭐⭐☆☆☆
</div>

---

## Learning Objectives

By the end of this week, you will be able to:

- [ ] Use LOAD DATA INFILE and SELECT INTO OUTFILE for high-performance flat-file import/export
- [ ] Apply mysqldump and mysqlpump for logical backups with the correct flags for common scenarios
- [ ] Use MySQL Shell utilities (util.importTable, util.exportTable, util.loadDump) for large-scale data operations
- [ ] Parse and import JSON data using JSON_TABLE() and handle nested structures
- [ ] Handle common CSV/Excel encoding and formatting pitfalls during import
- [ ] Build a Python ETL pipeline using mysql-connector-python, pandas, and SQLAlchemy
- [ ] Validate data during import: constraint checking, duplicate detection, and referential integrity
- [ ] Apply large-dataset strategies: chunked loading, index disabling, and ANALYZE TABLE
- [ ] Distinguish ETL vs ELT patterns and know when to use staging tables
- [ ] Write import scripts that are idempotent and safe to re-run

---

## 1. LOAD DATA INFILE

`LOAD DATA INFILE` is MySQL's fastest native CSV import method — typically **20–100× faster** than equivalent `INSERT` statements because it bypasses the SQL parser per row and streams directly to the storage engine.

### 1.1 Basic Syntax

```sql
LOAD DATA INFILE '/var/lib/mysql-files/students.csv'
INTO TABLE students
FIELDS TERMINATED BY ','
       ENCLOSED BY '"'
       ESCAPED BY '\\'
LINES  TERMINATED BY '\n'
IGNORE 1 LINES                          -- skip header row
(first_name, last_name, email, gpa, dept_id, enroll_year);
```

### 1.2 LOCAL Keyword (Client-Side Files)

```sql
-- LOCAL reads the file from the CLIENT machine (not server filesystem)
-- Requires: mysql --local-infile=1  and  local_infile=ON in my.cnf
LOAD DATA LOCAL INFILE '/home/john/exports/new_students.csv'
INTO TABLE students
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES  TERMINATED BY '\r\n'            -- Windows line endings
IGNORE 1 LINES
(first_name, last_name, @raw_email, @raw_gpa, dept_id, enroll_year)
SET email = LOWER(TRIM(@raw_email)),   -- transform on load
    gpa   = IF(@raw_gpa = '', NULL, CAST(@raw_gpa AS DECIMAL(3,2)));
```

!!! warning "Security: local_infile"
    `LOAD DATA LOCAL INFILE` has historically been a security vector (a malicious server could request any file from the client). Always disable it in production unless explicitly needed, and never enable it globally on multi-tenant servers.

### 1.3 Column Transformations and User Variables

```sql
-- Import enrollment history from legacy system with date conversion
LOAD DATA INFILE '/var/lib/mysql-files/enrollments_legacy.csv'
INTO TABLE enrollments
FIELDS TERMINATED BY '|'
LINES  TERMINATED BY '\n'
IGNORE 1 LINES
(student_id, course_id, @raw_semester, @raw_grade, instructor_id)
SET semester = CASE
                   WHEN @raw_semester LIKE 'FA%' THEN CONCAT('F', SUBSTR(@raw_semester, 3))
                   WHEN @raw_semester LIKE 'SP%' THEN CONCAT('S', SUBSTR(@raw_semester, 3))
                   ELSE @raw_semester
               END,
    grade    = NULLIF(TRIM(@raw_grade), '');
```

### 1.4 LOAD DATA vs INSERT Performance

| Method | 1M Rows Time (typical) | Indexing Impact | Transaction Log |
|--------|----------------------|-----------------|-----------------|
| `INSERT` (one per row) | 15–30 min | Maintained per row | Full |
| `INSERT … VALUES (batch)` | 2–5 min | Maintained per batch | Full |
| `LOAD DATA INFILE` | 20–60 sec | Maintained during load | Minimal |
| `LOAD DATA` + index disable | 5–15 sec | Re-built after load | Minimal |

### 1.5 Error Handling with LOAD DATA

```sql
-- IGNORE skips error rows (logs to warning list)
LOAD DATA INFILE '/var/lib/mysql-files/students.csv'
IGNORE                                  -- skip duplicate-key and data-conversion errors
INTO TABLE students
FIELDS TERMINATED BY ','
IGNORE 1 LINES
(first_name, last_name, email, gpa, dept_id, enroll_year);

-- Check what was skipped:
SHOW WARNINGS;

-- REPLACE overwrites existing rows with same unique key
LOAD DATA INFILE '/var/lib/mysql-files/students_update.csv'
REPLACE
INTO TABLE students
FIELDS TERMINATED BY ','
IGNORE 1 LINES
(student_id, first_name, last_name, email, gpa, dept_id, enroll_year);
```

---

## 2. SELECT INTO OUTFILE

Export query results directly to the server filesystem in CSV or other delimited formats.

```sql
-- Export current semester enrollments to CSV
SELECT  s.student_id,
        s.first_name,
        s.last_name,
        c.course_code,
        e.semester,
        COALESCE(e.grade, 'IN PROGRESS') AS grade
FROM    students   s
INNER JOIN enrollments e ON e.student_id = s.student_id
INNER JOIN courses     c ON c.course_id  = e.course_id
WHERE   e.semester = 'F2025'
INTO OUTFILE '/var/lib/mysql-files/f2025_enrollments.csv'
FIELDS TERMINATED BY ','
       ENCLOSED BY '"'
       ESCAPED BY '\\'
LINES  TERMINATED BY '\n';
```

!!! info "File Location Restriction"
    `INTO OUTFILE` writes to the **server's** filesystem. The path must be accessible by the `mysql` OS user and must not already exist (MySQL will not overwrite). On managed cloud MySQL (RDS, Cloud SQL), direct file system access is not available — use `SELECT … INTO OUTFILE` with MySQL Shell or export via application code.

```sql
-- Export with custom delimiter for Excel compatibility (tab-separated)
SELECT  student_id, first_name, last_name, gpa
FROM    students
WHERE   gpa >= 3.5
INTO OUTFILE '/var/lib/mysql-files/honor_roll.tsv'
FIELDS TERMINATED BY '\t'
LINES  TERMINATED BY '\r\n';
```

---

## 3. mysqldump — Logical Backup and Export

`mysqldump` produces a SQL text file containing `CREATE TABLE` statements and `INSERT` statements (or `LOAD DATA` statements with `--tab`), suitable for portability and schema migration.

### 3.1 Common Use Cases and Flags

=== "Full Database Backup"
    ```bash
    mysqldump \
        --user=backup_user \
        --password \
        --host=localhost \
        --single-transaction \       # InnoDB consistent snapshot (no table locks)
        --routines \                  # include stored procedures and functions
        --triggers \                  # include triggers
        --events \                    # include scheduled events
        --set-gtid-purged=OFF \       # safe for non-replication restores
        university_db \
        > /backups/university_db_$(date +%Y%m%d).sql
    ```

=== "Schema Only (No Data)"
    ```bash
    mysqldump \
        --user=admin --password \
        --no-data \                   # DDL only, no INSERT statements
        --routines \
        --triggers \
        university_db \
        > /backups/schema_only.sql
    ```

=== "Data Only (No Schema)"
    ```bash
    mysqldump \
        --user=admin --password \
        --no-create-info \            # skip CREATE TABLE
        --skip-triggers \
        university_db enrollments grades \
        > /backups/data_only.sql
    ```

=== "Selective WHERE Clause"
    ```bash
    # Export only Fall 2025 enrollment records
    mysqldump \
        --user=admin --password \
        --no-create-info \
        --where="semester='F2025'" \
        university_db enrollments \
        > /backups/f2025_enrollments.sql
    ```

=== "Compressed Output"
    ```bash
    mysqldump \
        --user=admin --password \
        --single-transaction \
        university_db \
        | gzip > /backups/university_db_$(date +%Y%m%d).sql.gz

    # Restore from compressed backup:
    gunzip -c /backups/university_db_20251201.sql.gz | mysql -u admin -p university_db
    ```

### 3.2 Critical mysqldump Flags Reference

| Flag | Effect | When to Use |
|------|--------|-------------|
| `--single-transaction` | Takes consistent InnoDB snapshot without locking | Always for InnoDB tables |
| `--lock-tables` | Locks all tables during dump (MyISAM) | MyISAM tables only |
| `--routines` | Includes stored procedures and functions | Always for full backup |
| `--triggers` | Includes trigger definitions | Always for full backup |
| `--events` | Includes scheduled events | If using Event Scheduler |
| `--no-data` | DDL only | Schema migration, dev setup |
| `--no-create-info` | Data only | Data refresh on existing schema |
| `--where` | Filter rows | Partial export |
| `--ignore-table` | Skip specific tables | Exclude log/temp tables |
| `--set-gtid-purged=OFF` | Omit GTID info from dump | Non-replication restores |
| `--column-statistics=0` | Disable column statistics (MySQL 8 client vs 5.7 server) | Cross-version dumps |

!!! danger "--single-transaction Does Not Lock"
    `--single-transaction` is safe for InnoDB but does NOT lock tables, so concurrent DDL (ALTER TABLE, DROP TABLE) during the dump can corrupt the backup. Always freeze DDL operations during critical backups.

---

## 4. mysqlpump — Parallel Logical Dump

`mysqlpump` is MySQL's multi-threaded successor to `mysqldump` for faster logical dumps.

```bash
mysqlpump \
    --user=admin --password \
    --default-parallelism=4 \         # 4 parallel dump threads
    --defer-table-indexes \           # dump data first, add indexes after (faster restore)
    --exclude-tables=proc_debug_log,enrollment_audit \
    --include-databases=university_db \
    --compress-output=LZ4 \
    --output-file=/backups/university_db_pump.sql.lz4

# Restore:
mysqlpump --uncompress /backups/university_db_pump.sql.lz4 | mysql -u admin -p
```

| Feature | mysqldump | mysqlpump |
|---------|-----------|-----------|
| Multi-threaded | ❌ Single thread | ✅ Configurable |
| Progress reporting | ❌ | ✅ `--watch-progress` |
| Deferred index build | ❌ | ✅ `--defer-table-indexes` |
| Built-in compression | ❌ (pipe to gzip) | ✅ LZ4, ZLIB |
| Available since | All versions | MySQL 5.7.8 |

---

## 5. MySQL Shell Utilities

MySQL Shell (`mysqlsh`) provides advanced import/export utilities that outperform both mysqldump and mysqlpump for large datasets.

### 5.1 util.importTable()

```javascript
// MySQL Shell JS mode: import large CSV directly with parallel loading
util.importTable('/data/students_10M.csv', {
    schema: 'university_db',
    table: 'students',
    dialect: 'csv-unix',             // field/line terminators preset
    columns: ['first_name', 'last_name', 'email', 'gpa', 'dept_id', 'enroll_year'],
    skipRows: 1,                     // skip header
    threads: 8,                      // parallel loading threads
    bytesPerChunk: '128M',           // chunk size per thread
    showProgress: true
})
```

### 5.2 util.dumpInstance() and util.loadDump()

```javascript
// Dump entire instance with parallel export
util.dumpInstance('/backups/full_dump_20251201', {
    threads: 4,
    compression: 'zstd',
    ocimds: false
})

// Load the dump into target server
util.loadDump('/backups/full_dump_20251201', {
    threads: 8,
    progressFile: '/tmp/load_progress.json',
    ignoreVersion: true,
    resetProgress: false             // resume if interrupted
})
```

!!! success "MySQL Shell for Large Migrations"
    For databases over 10 GB, MySQL Shell's `dumpInstance`/`loadDump` is the recommended approach. It parallelizes both reading and writing, uses chunked file format for resumability, and is significantly faster than mysqldump.

---

## 6. Importing JSON Data

### 6.1 JSON_TABLE() — Shredding JSON into Rows

```sql
-- Inline JSON array → relational rows
SELECT jt.*
FROM JSON_TABLE(
    '[
        {"student_id": 1001, "name": "Alice Chen",  "gpa": 3.9, "dept": "ITEC"},
        {"student_id": 1002, "name": "Bob Martinez", "gpa": 3.5, "dept": "MATH"},
        {"student_id": 1003, "name": "Carol Liu",   "gpa": null, "dept": "ITEC"}
    ]',
    '$[*]' COLUMNS (
        student_id INT         PATH '$.student_id',
        full_name  VARCHAR(100) PATH '$.name',
        gpa        DECIMAL(3,2) PATH '$.gpa'    DEFAULT '0.00' ON EMPTY,
        dept_code  VARCHAR(10)  PATH '$.dept'
    )
) AS jt;
```

### 6.2 Loading JSON from a File via Staging Table

```sql
-- Step 1: Load raw JSON text into a staging table
CREATE TABLE json_staging (
    id       INT PRIMARY KEY AUTO_INCREMENT,
    raw_json LONGTEXT,
    loaded_at DATETIME DEFAULT NOW()
);

-- (Load the file content via LOAD DATA or application)

-- Step 2: Shred JSON into target table using JSON_TABLE
INSERT INTO students (first_name, last_name, email, gpa, dept_id)
SELECT  jt.first_name,
        jt.last_name,
        jt.email,
        jt.gpa,
        d.dept_id
FROM    json_staging js
CROSS JOIN JSON_TABLE(
    js.raw_json,
    '$[*]' COLUMNS (
        first_name VARCHAR(50)  PATH '$.first_name',
        last_name  VARCHAR(50)  PATH '$.last_name',
        email      VARCHAR(100) PATH '$.email',
        gpa        DECIMAL(3,2) PATH '$.gpa',
        dept_code  VARCHAR(10)  PATH '$.department'
    )
) AS jt
INNER JOIN departments d ON d.dept_name LIKE CONCAT('%', jt.dept_code, '%')
ON DUPLICATE KEY UPDATE gpa = VALUES(gpa);
```

### 6.3 Nested JSON Structures

```sql
-- Flatten nested enrollments array within student JSON
-- Input: {"student_id": 1001, "enrollments": [{"course": "ITEC445", "sem": "F2025"}, ...]}
SELECT  jt.student_id,
        enr.course_code,
        enr.semester
FROM    json_staging js
CROSS JOIN JSON_TABLE(
    js.raw_json,
    '$[*]' COLUMNS (
        student_id  INT  PATH '$.student_id',
        NESTED PATH '$.enrollments[*]' COLUMNS (
            course_code VARCHAR(10) PATH '$.course',
            semester    CHAR(6)     PATH '$.sem'
        )
    )
) AS jt
CROSS JOIN LATERAL (SELECT jt.course_code AS course_code, jt.semester AS semester) AS enr
WHERE jt.student_id IS NOT NULL;
```

---

## 7. Importing XML Data

=== "MySQL LOAD XML"
    ```sql
    -- XML file format expected by LOAD XML:
    -- <resultset><row><field name="col">val</field></row></resultset>
    LOAD XML INFILE '/var/lib/mysql-files/students.xml'
    INTO TABLE students
    ROWS IDENTIFIED BY '<row>';
    ```

=== "SQL Server XML PATH"
    ```sql
    -- SQL Server: shred XML into rows with OPENXML or nodes()
    DECLARE @xml XML = (SELECT * FROM OPENROWSET(BULK '/data/students.xml', SINGLE_BLOB) AS x);

    SELECT
        rec.value('first_name[1]', 'VARCHAR(50)') AS first_name,
        rec.value('last_name[1]',  'VARCHAR(50)') AS last_name,
        rec.value('gpa[1]',        'DECIMAL(3,2)') AS gpa
    FROM @xml.nodes('/students/student') AS t(rec);
    ```

---

## 8. CSV/Excel Import Patterns

### 8.1 Encoding Issues

!!! warning "UTF-8 BOM"
    Excel saves CSV files with a Byte Order Mark (BOM: `EF BB BF`). MySQL does not strip this automatically — the first field of the first row will contain invisible BOM characters, corrupting the data.

```bash
# Strip UTF-8 BOM before loading (Linux)
sed -i 's/^\xEF\xBB\xBF//' /var/lib/mysql-files/students.csv

# Or in Python:
with open('students.csv', encoding='utf-8-sig') as f:  # 'utf-8-sig' strips BOM
    content = f.read()
```

### 8.2 Date Format Normalization

```sql
-- Import with date stored as MM/DD/YYYY string
LOAD DATA INFILE '/var/lib/mysql-files/enrollments.csv'
INTO TABLE enrollments
FIELDS TERMINATED BY ','
IGNORE 1 LINES
(student_id, course_id, @raw_date, grade)
SET enrolled_date = STR_TO_DATE(@raw_date, '%m/%d/%Y');
```

### 8.3 NULL Handling in CSV

```sql
-- Map empty strings and literal "NULL" to SQL NULL
LOAD DATA INFILE '/var/lib/mysql-files/grades.csv'
INTO TABLE enrollments
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
IGNORE 1 LINES
(student_id, course_id, semester, @raw_grade)
SET grade = CASE
    WHEN TRIM(@raw_grade) = ''     THEN NULL
    WHEN UPPER(TRIM(@raw_grade)) = 'NULL' THEN NULL
    WHEN UPPER(TRIM(@raw_grade)) = 'N/A'  THEN NULL
    ELSE TRIM(@raw_grade)
END;
```

---

## 9. Python ETL Pipeline

### 9.1 mysql-connector-python

```python
import mysql.connector
import csv

def load_students_from_csv(csv_path: str, connection_config: dict) -> dict:
    """Bulk load students from CSV with duplicate handling."""
    conn = mysql.connector.connect(**connection_config)
    cursor = conn.cursor()

    insert_sql = """
        INSERT INTO students (first_name, last_name, email, gpa, dept_id, enroll_year)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            gpa        = VALUES(gpa),
            updated_at = NOW()
    """

    rows_inserted = 0
    rows_skipped  = 0
    errors        = []

    with open(csv_path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        batch  = []

        for row in reader:
            try:
                batch.append((
                    row['first_name'].strip(),
                    row['last_name'].strip(),
                    row['email'].strip().lower(),
                    float(row['gpa']) if row['gpa'].strip() else None,
                    int(row['dept_id']),
                    int(row['enroll_year'])
                ))

                if len(batch) >= 1000:           # flush every 1000 rows
                    cursor.executemany(insert_sql, batch)
                    conn.commit()
                    rows_inserted += cursor.rowcount
                    batch.clear()

            except (ValueError, KeyError) as e:
                errors.append({'row': row, 'error': str(e)})
                rows_skipped += 1

        if batch:                                # flush remainder
            cursor.executemany(insert_sql, batch)
            conn.commit()
            rows_inserted += cursor.rowcount

    cursor.close()
    conn.close()
    return {'inserted': rows_inserted, 'skipped': rows_skipped, 'errors': errors}
```

### 9.2 pandas DataFrame to SQL

```python
import pandas as pd
from sqlalchemy import create_engine

# Connection string: mysql+mysqlconnector://user:pass@host/db
engine = create_engine(
    'mysql+mysqlconnector://etl_user:secret@localhost/university_db',
    pool_pre_ping=True
)

# Read and transform
df = pd.read_csv('/data/new_enrollments.csv', encoding='utf-8-sig')

# Data cleaning
df['grade']    = df['grade'].replace({'': None, 'NULL': None, 'N/A': None})
df['semester'] = df['semester'].str.strip().str.upper()
df['email']    = df['email'].str.strip().str.lower()
df             = df.drop_duplicates(subset=['student_id', 'course_id', 'semester'])
df             = df.dropna(subset=['student_id', 'course_id', 'semester'])

# Load to staging table first
df.to_sql(
    name='enrollment_staging',
    con=engine,
    if_exists='replace',             # replace staging each run
    index=False,
    chunksize=5000,
    method='multi'                   # INSERT … VALUES (v1),(v2),…
)

print(f"Staged {len(df):,} rows to enrollment_staging")
```

### 9.3 SQLAlchemy Bulk Insert Mappings

```python
from sqlalchemy.orm import Session
from sqlalchemy import text

def bulk_insert_enrollments(records: list[dict], engine) -> int:
    """High-performance bulk insert using Core insert."""
    if not records:
        return 0

    with engine.begin() as conn:
        result = conn.execute(
            text("""
                INSERT INTO enrollments (student_id, course_id, semester, grade, instructor_id)
                VALUES (:student_id, :course_id, :semester, :grade, :instructor_id)
                ON DUPLICATE KEY UPDATE grade = VALUES(grade)
            """),
            records        # list of dicts — SQLAlchemy binds parameters
        )
        return result.rowcount

# Usage
records = [
    {'student_id': 1001, 'course_id': 7, 'semester': 'F2025',
     'grade': None, 'instructor_id': 3},
    {'student_id': 1002, 'course_id': 7, 'semester': 'F2025',
     'grade': None, 'instructor_id': 3},
]
inserted = bulk_insert_enrollments(records, engine)
print(f"Inserted/updated {inserted} rows")
```

---

## 10. Data Validation During Import

### 10.1 Staging Table Pattern

```sql
-- Always import into a staging table first, validate, then promote
CREATE TABLE enrollment_staging (
    row_id       INT          PRIMARY KEY AUTO_INCREMENT,
    student_id   INT,
    course_id    INT,
    semester     CHAR(6),
    grade        CHAR(2),
    raw_line     TEXT,                     -- original CSV line for debugging
    is_valid     TINYINT      DEFAULT 0,
    error_msg    VARCHAR(500),
    loaded_at    DATETIME     DEFAULT NOW()
);

-- Validate: check referential integrity
UPDATE enrollment_staging s
SET    is_valid  = 0,
       error_msg = 'Unknown student_id'
WHERE  NOT EXISTS (SELECT 1 FROM students WHERE student_id = s.student_id);

UPDATE enrollment_staging s
SET    is_valid  = 0,
       error_msg = CONCAT(COALESCE(error_msg, ''), ' | Unknown course_id')
WHERE  NOT EXISTS (SELECT 1 FROM courses WHERE course_id = s.course_id);

-- Validate: duplicate detection
UPDATE enrollment_staging s
SET    is_valid  = 0,
       error_msg = CONCAT(COALESCE(error_msg, ''), ' | Duplicate enrollment')
WHERE  EXISTS (
    SELECT 1 FROM enrollments e
    WHERE  e.student_id = s.student_id
      AND  e.course_id  = s.course_id
      AND  e.semester   = s.semester
);

-- Mark valid rows
UPDATE enrollment_staging
SET    is_valid = 1
WHERE  is_valid = 0 AND error_msg IS NULL;

-- Promote valid rows to production
INSERT INTO enrollments (student_id, course_id, semester, grade)
SELECT student_id, course_id, semester, grade
FROM   enrollment_staging
WHERE  is_valid = 1;

-- Report results
SELECT
    SUM(is_valid = 1) AS promoted,
    SUM(is_valid = 0) AS rejected
FROM enrollment_staging;
```

### 10.2 Constraint Checking During Import

```sql
-- Temporarily allow loading without FK checks (faster but risky)
SET FOREIGN_KEY_CHECKS = 0;
LOAD DATA INFILE '/var/lib/mysql-files/enrollments_bulk.csv'
INTO TABLE enrollments
FIELDS TERMINATED BY ','
IGNORE 1 LINES
(student_id, course_id, semester, grade);
SET FOREIGN_KEY_CHECKS = 1;

-- Then verify no orphans were introduced:
SELECT COUNT(*) AS orphaned_enrollments
FROM   enrollments e
WHERE  NOT EXISTS (SELECT 1 FROM students s WHERE s.student_id = e.student_id)
   OR  NOT EXISTS (SELECT 1 FROM courses  c WHERE c.course_id  = e.course_id);
```

!!! danger "Foreign Key Checks"
    Disabling `FOREIGN_KEY_CHECKS` during import is a performance technique but **removes referential integrity protection**. Always re-enable and audit for orphans immediately after. On InnoDB, you cannot disable FK checks at the table level — it's session-wide.

---

## 11. Large Dataset Strategies

### 11.1 Chunked Loading

```python
import pandas as pd
from sqlalchemy import create_engine, text

engine = create_engine('mysql+mysqlconnector://user:pass@host/university_db')
CHUNK_SIZE = 50_000

for i, chunk in enumerate(pd.read_csv('/data/enrollments_10M.csv',
                                       chunksize=CHUNK_SIZE,
                                       encoding='utf-8-sig')):
    chunk.to_sql('enrollment_staging', con=engine,
                 if_exists='append', index=False, method='multi')
    print(f"Chunk {i+1}: {(i+1)*CHUNK_SIZE:,} rows staged")
```

### 11.2 Disabling Indexes During Bulk Load

```sql
-- For MyISAM: disable index maintenance during load
ALTER TABLE enrollments DISABLE KEYS;

LOAD DATA INFILE '/var/lib/mysql-files/enrollments_10M.csv'
INTO TABLE enrollments
FIELDS TERMINATED BY ','
IGNORE 1 LINES
(student_id, course_id, semester, grade, instructor_id);

ALTER TABLE enrollments ENABLE KEYS;   -- rebuilds all secondary indexes at once (faster)

-- For InnoDB: similar effect with:
SET unique_checks   = 0;
SET foreign_key_checks = 0;
-- ... load ...
SET unique_checks   = 1;
SET foreign_key_checks = 1;
ANALYZE TABLE enrollments;             -- update optimizer statistics
```

### 11.3 ANALYZE TABLE and Optimizer Statistics

```sql
-- After any large import, refresh statistics so the optimizer has accurate data
ANALYZE TABLE students, enrollments, courses, instructors, departments;

-- Check table statistics:
SELECT table_name, table_rows, avg_row_length, data_length, index_length
FROM   information_schema.tables
WHERE  table_schema = 'university_db'
ORDER BY data_length DESC;
```

---

## 12. ETL vs ELT Patterns

| Pattern | Flow | Where Transform Happens | Best For |
|---------|------|------------------------|----------|
| **ETL** | Extract → Transform → Load | External (Python, Spark, etc.) | Complex transforms, data quality rules, multi-source integration |
| **ELT** | Extract → Load → Transform | Inside the database (SQL) | Powerful destination DB (BigQuery, Snowflake, MySQL), raw data archives |

### 12.1 Staging Table Architecture

```
[ Source CSV / JSON / API ]
          │
          ▼
┌─────────────────────┐
│   staging table     │  ← Raw data, no constraints, nullable
│   (no FKs, no idx)  │
└─────────────────────┘
          │ validate, transform (SQL or Python)
          ▼
┌─────────────────────┐
│  production tables  │  ← Full constraints, indexes, triggers active
│  (FKs, indexes)     │
└─────────────────────┘
```

```sql
-- A complete idempotent ETL step: upsert from staging to production
INSERT INTO students (student_id, first_name, last_name, email, gpa, dept_id, enroll_year)
SELECT  s.student_id,
        TRIM(s.first_name),
        TRIM(s.last_name),
        LOWER(TRIM(s.email)),
        CASE WHEN s.gpa BETWEEN 0.0 AND 4.0 THEN s.gpa ELSE NULL END,
        d.dept_id,
        s.enroll_year
FROM    student_staging s
INNER JOIN departments d ON d.dept_name = TRIM(s.dept_name)
WHERE   s.is_valid = 1
ON DUPLICATE KEY UPDATE
    first_name  = VALUES(first_name),
    last_name   = VALUES(last_name),
    email       = VALUES(email),
    gpa         = VALUES(gpa),
    updated_at  = NOW();
```

!!! tip "Idempotency"
    Design every ETL step to be **idempotent** — safe to run multiple times without side effects. Using `ON DUPLICATE KEY UPDATE` or `INSERT IGNORE` ensures re-running a load doesn't create duplicates. Truncate the staging table at the start of each run.

---

## Key Vocabulary

| Term | Definition |
|------|------------|
| **LOAD DATA INFILE** | MySQL high-performance server-side file import statement |
| **LOCAL** | Modifier reading the file from the client machine rather than the server |
| **SELECT INTO OUTFILE** | MySQL export of query results to a server-side file |
| **mysqldump** | Single-threaded logical backup utility producing SQL text output |
| **mysqlpump** | Multi-threaded replacement for mysqldump with parallel export |
| **MySQL Shell** | Modern MySQL client with util.importTable/dumpInstance/loadDump |
| **JSON_TABLE()** | MySQL function that converts JSON data into a relational result set |
| **NESTED PATH** | JSON_TABLE clause for expanding nested JSON arrays into additional rows |
| **UTF-8 BOM** | Invisible byte sequence (EF BB BF) Excel prepends to CSV; must be stripped |
| **ETL** | Extract, Transform, Load — transform happens before loading |
| **ELT** | Extract, Load, Transform — raw data loaded first, transformed in the DB |
| **Staging table** | Temporary table for raw imported data before validation and promotion |
| **Idempotent** | Operation that produces the same result regardless of how many times it runs |
| **ANALYZE TABLE** | Rebuilds optimizer statistics after bulk data changes |
| **DISABLE KEYS** | MyISAM directive to defer secondary index maintenance during bulk load |
| **Chunked loading** | Breaking a large dataset into smaller batches to manage memory and lock time |
| **ON DUPLICATE KEY UPDATE** | MySQL upsert syntax — updates existing row if unique key conflict occurs |
| **STR_TO_DATE()** | MySQL function to parse a date string with a specified format mask |
| **FOREIGN_KEY_CHECKS** | Session variable that enables/disables FK constraint enforcement |
| **bulk_insert_mappings** | SQLAlchemy method for high-performance batch inserts using Core (not ORM) |

---

!!! question "Self-Assessment"
    1. A colleague proposes importing 5 million enrollment records using a Python loop with individual `INSERT` statements. Quantify the performance difference compared to `LOAD DATA INFILE` and describe three specific changes that would improve their approach while keeping Python as the driver.
    2. You run `LOAD DATA INFILE` with `IGNORE 1 LINES` and the import completes with no errors, but you notice the first actual data row is missing from the table. What are two possible causes and how do you diagnose each?
    3. Design a complete ETL pipeline that imports a daily JSON feed of new course registrations from an external university system. The JSON has nested enrollments per student. Include: (a) schema for the staging table, (b) JSON_TABLE query to flatten the data, (c) validation steps with specific checks, (d) promotion SQL, (e) rollback strategy if more than 5% of rows fail validation.
    4. A `mysqldump` of a 50 GB database with `--single-transaction` takes 4 hours and blocks the server. Propose an alternative strategy using MySQL Shell utilities and justify why it would be faster. What are the trade-offs?
    5. Explain the difference between ETL and ELT, and describe a scenario at a university where ELT is clearly the better choice. Include the staging table design and the in-database transformation SQL for your scenario.

---

## Further Reading

- 📄 [MySQL 8.0 Reference — LOAD DATA INFILE](https://dev.mysql.com/doc/refman/8.0/en/load-data.html)
- 📄 [MySQL 8.0 Reference — JSON_TABLE](https://dev.mysql.com/doc/refman/8.0/en/json-table-functions.html)
- 📄 [MySQL Shell — Dump & Load Utilities](https://dev.mysql.com/doc/mysql-shell/8.0/en/mysql-shell-utilities-dump-instance-schema.html)
- 📄 [mysqldump Reference Manual](https://dev.mysql.com/doc/refman/8.0/en/mysqldump.html)
- 📄 [SQLAlchemy Core — Bulk Operations](https://docs.sqlalchemy.org/en/14/core/dml.html)
- 📖 *High Performance MySQL 4th Ed.*, Chapter 8 — "Optimizing Server Settings" (bulk load section)
- 📄 [Pandas read_csv Documentation](https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html)
- 🎥 Percona Live — "Fast Data Loading in MySQL 8.0" (freely available on YouTube)

---

*[← Week 4](week04.md) &nbsp;|&nbsp; [Course Index](index.md) &nbsp;|&nbsp; [Week 6 →](week06.md)*
