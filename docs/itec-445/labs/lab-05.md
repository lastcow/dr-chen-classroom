---
title: "Lab 05: Data Import, Export & ETL with Neon"
course: ITEC-445
topic: Data Import & Export — Formats, Tools & ETL
week: 5
difficulty: ⭐⭐
estimated_time: 75 minutes
---

# Lab 05: Data Import, Export & ETL with Neon

| Field | Details |
|---|---|
| **Course** | ITEC-445 — Advanced Database Management |
| **Week** | 5 |
| **Difficulty** | ⭐⭐ Intermediate |
| **Estimated Time** | 75 minutes |
| **Topic** | Data Import & Export — ETL Pipelines |
| **Prerequisites** | Lab 01 schema on Neon branch `lab-05`, Python 3.10+, `pip install psycopg2-binary pandas` |
| **Deliverables** | CSV/JSON files imported, Python ETL script, `verify_lab05()` PASS |

---

## Overview

Real databases are never populated by hand — data flows in from upstream systems as CSV exports, JSON APIs, and legacy database dumps. In this lab you will use PostgreSQL's native `COPY` command, `psql \copy` (client-side), JSON ingestion with `json_populate_recordset`, and a Python ETL pipeline with validation and error handling.

---

!!! warning "Branch Requirement"
    Create branch **`lab-05`** with Lab 01 schema populated.

---

## Part A — Generate & Import CSV with COPY (25 pts)

### A1. Create import staging tables

```sql
SET search_path = fsu;

CREATE TABLE IF NOT EXISTS staging_students (
    raw_id        TEXT,
    first_name    TEXT,
    last_name     TEXT,
    email         TEXT,
    gpa           TEXT,     -- raw text for validation
    dept_code     TEXT,     -- dept name instead of ID
    enroll_year   TEXT,
    import_status TEXT DEFAULT 'PENDING',
    import_error  TEXT
);
```

### A2. Create the CSV file locally

Save as `new_students.csv`:
```csv
raw_id,first_name,last_name,email,gpa,dept_code,enroll_year
101,Alex,Morgan,amorgan@student.fsu.edu,3.45,Computer Science,2024
102,Bailey,Nguyen,bnguyen@student.fsu.edu,2.88,Mathematics,2024
103,Cameron,Park,cpark@student.fsu.edu,4.00,Computer Science,2023
104,Dana,Reed,dreed@student.fsu.edu,,Biology,2024
105,Eli,Santos,esantos@student.fsu.edu,5.50,Computer Science,2024
106,Fiona,Taylor,ftaylor@student.fsu.edu,3.12,Physics,2024
107,George,Ueda,gueda@student.fsu.edu,2.95,FAKE_DEPT,2024
108,Hana,Vega,hvega@student.fsu.edu,1.80,English,2025
```

!!! info "Notes on the data"
    - Row 104: missing GPA (empty string) — should be treated as NULL
    - Row 105: GPA = 5.50 — invalid, out of range
    - Row 107: department `FAKE_DEPT` doesn't exist — must be caught
    - Row 108: enroll_year 2025 — future year, should be rejected

### A3. Import with `\copy` (client-side — works with Neon)

```bash
psql "$DATABASE_URL" -c "\copy fsu.staging_students(raw_id,first_name,last_name,email,gpa,dept_code,enroll_year) FROM 'new_students.csv' CSV HEADER"
```

Verify:
```sql
SELECT COUNT(*) FROM fsu.staging_students;  -- should be 8
SELECT * FROM fsu.staging_students;
```

---

## Part B — ETL Validation & Load Procedure (30 pts)

Write a PL/pgSQL procedure `process_staging_students()` that validates and loads the staging data into `students`:

```sql
CREATE OR REPLACE PROCEDURE process_staging_students()
LANGUAGE plpgsql AS $$
DECLARE
    v_rec       RECORD;
    v_dept_id   INT;
    v_gpa       NUMERIC(3,2);
    v_year      INT;
    v_loaded    INT := 0;
    v_rejected  INT := 0;
BEGIN
    FOR v_rec IN SELECT * FROM staging_students WHERE import_status = 'PENDING'
    LOOP
        BEGIN
            -- Validate and resolve department
            SELECT dept_id INTO v_dept_id
            FROM departments WHERE dept_name = v_rec.dept_code;

            IF NOT FOUND THEN
                UPDATE staging_students
                SET import_status = 'REJECTED',
                    import_error  = 'Unknown department: ' || v_rec.dept_code
                WHERE raw_id = v_rec.raw_id;
                v_rejected := v_rejected + 1;
                CONTINUE;
            END IF;

            -- Validate GPA
            IF v_rec.gpa = '' OR v_rec.gpa IS NULL THEN
                v_gpa := NULL;
            ELSE
                BEGIN
                    v_gpa := v_rec.gpa::NUMERIC(3,2);
                EXCEPTION WHEN OTHERS THEN
                    UPDATE staging_students SET import_status='REJECTED',
                        import_error='Invalid GPA: ' || v_rec.gpa WHERE raw_id=v_rec.raw_id;
                    v_rejected := v_rejected + 1; CONTINUE;
                END;
                IF v_gpa < 0 OR v_gpa > 4.0 THEN
                    UPDATE staging_students SET import_status='REJECTED',
                        import_error='GPA out of range: ' || v_gpa WHERE raw_id=v_rec.raw_id;
                    v_rejected := v_rejected + 1; CONTINUE;
                END IF;
            END IF;

            -- Validate enrollment year
            v_year := v_rec.enroll_year::INT;
            IF v_year > EXTRACT(YEAR FROM NOW())::INT THEN
                UPDATE staging_students SET import_status='REJECTED',
                    import_error='Future enrollment year: ' || v_year WHERE raw_id=v_rec.raw_id;
                v_rejected := v_rejected + 1; CONTINUE;
            END IF;

            -- Insert into students
            INSERT INTO students (first_name, last_name, email, gpa, dept_id, enroll_year)
            VALUES (v_rec.first_name, v_rec.last_name, LOWER(v_rec.email),
                    v_gpa, v_dept_id, v_year);

            UPDATE staging_students SET import_status='LOADED' WHERE raw_id=v_rec.raw_id;
            v_loaded := v_loaded + 1;

        EXCEPTION WHEN unique_violation THEN
            UPDATE staging_students SET import_status='REJECTED',
                import_error='Duplicate email' WHERE raw_id=v_rec.raw_id;
            v_rejected := v_rejected + 1;
        WHEN OTHERS THEN
            UPDATE staging_students SET import_status='ERROR',
                import_error=SQLERRM WHERE raw_id=v_rec.raw_id;
            v_rejected := v_rejected + 1;
        END;
    END LOOP;

    RAISE NOTICE 'ETL complete: % loaded, % rejected', v_loaded, v_rejected;
END;
$$;

CALL process_staging_students();

-- Review results
SELECT raw_id, first_name, last_name, import_status, import_error
FROM staging_students ORDER BY raw_id;
```

**Expected:** 5 LOADED, 3 REJECTED (dept, GPA, year)

---

## Part C — JSON Import (20 pts)

Neon supports PostgreSQL's native JSON functions. Import course registration data from a JSON structure:

```sql
-- Insert JSON data as a PostgreSQL literal
CREATE TEMP TABLE json_import AS
SELECT * FROM json_populate_recordset(
    NULL::fsu.courses,
    '[
        {"course_code": "ITEC480", "title": "Cloud Database Engineering", "credits": 3, "dept_id": 1},
        {"course_code": "MATH450", "title": "Numerical Methods", "credits": 3, "dept_id": 2},
        {"course_code": "ITEC490", "title": "Database Capstone", "credits": 3, "dept_id": 1}
    ]'::json
);

-- Insert into real table (skipping course_id which is SERIAL)
INSERT INTO fsu.courses (course_code, title, credits, dept_id)
SELECT course_code, title, credits, dept_id FROM json_import
ON CONFLICT (course_code) DO NOTHING;

SELECT * FROM fsu.courses WHERE course_code IN ('ITEC480','MATH450','ITEC490');
```

**Your task:** Write a Python script `import_json.py` that:
1. Reads a local JSON file `courses.json` containing 5 additional courses
2. Connects to Neon using `psycopg2`
3. Validates each course (dept_id must exist, credits must be 1–6, no duplicate course_code)
4. Inserts valid courses, logs rejections to a local `import_log.txt`
5. Reports summary: X inserted, Y rejected

---

## Part D — Export with COPY TO (15 pts)

**D1.** Export all students with their department name to a CSV file:
```sql
COPY (
    SELECT s.student_id, s.first_name, s.last_name, s.email,
           s.gpa, d.dept_name, s.enroll_year
    FROM fsu.students s
    LEFT JOIN fsu.departments d ON s.dept_id = d.dept_id
    ORDER BY s.student_id
) TO STDOUT CSV HEADER;
```

Run with `psql`:
```bash
psql "$DATABASE_URL" -c "\copy (SELECT s.student_id, s.first_name, s.last_name, s.email, s.gpa, d.dept_name, s.enroll_year FROM fsu.students s LEFT JOIN fsu.departments d ON s.dept_id = d.dept_id ORDER BY s.student_id) TO 'students_export.csv' CSV HEADER"
```

**D2.** Export all current enrollments as JSON:
```bash
psql "$DATABASE_URL" -t -c "SELECT json_agg(row_to_json(t)) FROM (SELECT e.enrollment_id, s.first_name||' '||s.last_name AS student, c.course_code, e.semester, e.grade FROM fsu.enrollments e JOIN fsu.students s ON e.student_id=s.student_id JOIN fsu.courses c ON e.course_id=c.course_id) t;" > enrollments_export.json
```

Verify the JSON is valid:
```bash
python3 -c "import json; data=json.load(open('enrollments_export.json')); print(f'Valid JSON: {len(data)} records')"
```

---

## Verification

```sql
SET search_path = fsu;

CREATE OR REPLACE FUNCTION verify_lab05()
RETURNS TABLE(check_id TEXT, description TEXT, result TEXT, points INT) AS $$
BEGIN
    RETURN QUERY SELECT '01', 'staging_students table exists',
        CASE WHEN EXISTS(SELECT 1 FROM information_schema.tables
                         WHERE table_schema='fsu' AND table_name='staging_students')
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '02', 'staging_students has 8 raw rows',
        CASE WHEN (SELECT COUNT(*) FROM staging_students) = 8
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '03', '5 rows loaded from staging',
        CASE WHEN (SELECT COUNT(*) FROM staging_students WHERE import_status='LOADED') = 5
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '04', '3 rows rejected from staging',
        CASE WHEN (SELECT COUNT(*) FROM staging_students WHERE import_status='REJECTED') = 3
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '05', 'FAKE_DEPT row is rejected',
        CASE WHEN EXISTS(SELECT 1 FROM staging_students
                         WHERE dept_code='FAKE_DEPT' AND import_status='REJECTED')
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '06', 'GPA 5.50 row is rejected',
        CASE WHEN EXISTS(SELECT 1 FROM staging_students
                         WHERE gpa='5.50' AND import_status='REJECTED')
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '07', 'Future year 2025 row is rejected',
        CASE WHEN EXISTS(SELECT 1 FROM staging_students
                         WHERE enroll_year='2025' AND import_status='REJECTED')
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '08', 'NULL GPA row (Dana Reed) loaded successfully',
        CASE WHEN EXISTS(SELECT 1 FROM students WHERE last_name='Reed' AND gpa IS NULL)
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '09', 'JSON import: ITEC480 course exists',
        CASE WHEN EXISTS(SELECT 1 FROM courses WHERE course_code='ITEC480')
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '10', 'process_staging_students procedure exists',
        CASE WHEN EXISTS(SELECT 1 FROM pg_proc WHERE proname='process_staging_students')
             THEN 'PASS' ELSE 'FAIL' END, 10;
END;
$$ LANGUAGE plpgsql;

SELECT check_id, description, result,
       CASE WHEN result = 'PASS' THEN points ELSE 0 END AS earned
FROM verify_lab05()
ORDER BY check_id;
```

---

## Additional Requirement (20 pts)

Write `etl_report.sql` — a query that produces a full ETL run summary report:

```
ETL Import Summary — [timestamp]
=================================
Total rows staged:    8
  LOADED:             5
  REJECTED:           3
  PENDING:            0

Rejection Breakdown:
  Unknown department: 1
  GPA out of range:   1
  Future year:        1

Loaded Students by Department:
  Computer Science:   2 new students
  Mathematics:        1 new student
  Biology:            1 new student
  Physics:            1 new student
```

Use `FORMAT()`, string aggregation, and CTEs to produce this output in a single query.

---

## Submission Checklist

- [ ] `new_students.csv` — 8-row CSV file
- [ ] Neon branch `lab-05` with staging table, process procedure, and JSON imports
- [ ] `import_json.py` — Python ETL script
- [ ] `courses.json` — 5 additional courses for Python import
- [ ] `students_export.csv` and `enrollments_export.json`
- [ ] `etl_report.sql` — summary report query
- [ ] `verify_lab05()` screenshot — all PASS

---

## Grading

| Component | Points |
|-----------|--------|
| Part A — CSV import, staging table populated (8 rows) | 25 |
| Part B — process_staging_students (correct validation, 5 loaded, 3 rejected) | 30 |
| Part C — JSON import (SQL + Python script) | 20 |
| Part D — CSV + JSON export files | 15 |
| Additional requirement — ETL summary report | 20 |
| **Total** | **110** |
