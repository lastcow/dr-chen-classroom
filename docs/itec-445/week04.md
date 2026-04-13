---
title: "Week 4 — User-Defined Functions & Triggers"
description: Extend SQL's vocabulary with custom scalar, table-valued, and aggregate functions, then automate database behavior with BEFORE/AFTER triggers for auditing, validation, and cascade operations.
---

# Week 4 — User-Defined Functions & Triggers

<div class="week-meta" markdown>
**Course Objectives:** CO2 &nbsp;|&nbsp; **Focus:** UDFs, Triggers & Database Automation &nbsp;|&nbsp; **Difficulty:** ⭐⭐⭐☆☆
</div>

---

## Learning Objectives

By the end of this week, you will be able to:

- [ ] Distinguish scalar UDFs, table-valued functions, and user-defined aggregate functions and choose the appropriate type
- [ ] Write MySQL scalar functions with correct DETERMINISTIC and data access clauses
- [ ] Write PostgreSQL functions using PL/pgSQL with RETURNS TABLE and SETOF patterns
- [ ] Identify and use the appropriate built-in function category for string, numeric, date/time, JSON, and conditional tasks
- [ ] Explain trigger timing (BEFORE/AFTER), events (INSERT/UPDATE/DELETE), and granularity (FOR EACH ROW)
- [ ] Access OLD and NEW row data inside MySQL and PostgreSQL triggers
- [ ] Implement audit logging, data validation, timestamp maintenance, and denormalization triggers
- [ ] Identify trigger pitfalls: recursive triggers, performance impact, and hidden logic
- [ ] Implement INSTEAD OF triggers in PostgreSQL for updatable view patterns
- [ ] Compare triggers, stored procedures, and application-layer code for enforcing business rules

---

## 1. User-Defined Functions (UDFs)

### 1.1 Types of UDFs

| Type | Returns | Can Use in SELECT | MySQL Support | PostgreSQL Support |
|------|---------|-------------------|---------------|--------------------|
| **Scalar UDF** | Single value | ✅ Anywhere a value fits | ✅ Native | ✅ Native |
| **Table-Valued Function** | Row set (table) | ✅ In FROM clause | ⚠️ Via stored procedure workaround | ✅ RETURNS TABLE / SETOF |
| **User-Defined Aggregate** | Single value from many rows | ✅ Like SUM/AVG | ❌ Not natively | ✅ CREATE AGGREGATE |
| **Window UDA** | Value per row | ✅ With OVER() | ❌ | ✅ |

!!! note "MySQL Table-Valued Functions"
    MySQL does not natively support table-valued functions (TVFs). Workarounds include temporary tables populated by stored procedures, or JSON-returning functions combined with `JSON_TABLE()`. PostgreSQL's `RETURNS TABLE` is far more flexible.

### 1.2 MySQL Scalar UDF Syntax

```sql
DELIMITER $$

CREATE FUNCTION calculate_gpa (p_student_id INT)
RETURNS DECIMAL(3,2)
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE v_gpa DECIMAL(3,2);

    SELECT ROUND(AVG(points), 2)
    INTO   v_gpa
    FROM   grade_points
    WHERE  student_id = p_student_id
      AND  points IS NOT NULL;

    RETURN COALESCE(v_gpa, 0.00);
END$$

DELIMITER ;

-- Using the function in a query
SELECT student_id,
       first_name,
       last_name,
       calculate_gpa(student_id) AS computed_gpa
FROM   students
ORDER BY computed_gpa DESC;
```

### 1.3 Determinism and Data Access Clauses

These clauses are **required** in MySQL when binary logging is enabled (`log_bin = ON`):

| Clause | Meaning | When to Use |
|--------|---------|-------------|
| `DETERMINISTIC` | Same inputs always produce same output | Pure computation functions |
| `NOT DETERMINISTIC` | Output may vary for same inputs | Functions using RAND(), NOW(), etc. |
| `NO SQL` | Contains no SQL statements | String/math helpers with no DB access |
| `READS SQL DATA` | Contains SELECT but no DML | Read-only lookup functions |
| `MODIFIES SQL DATA` | Contains INSERT/UPDATE/DELETE | Functions that change data |
| `CONTAINS SQL` | Contains SQL but neither reads nor modifies | Rare; SET statements, etc. |

!!! warning "Binary Log and DETERMINISTIC"
    On a MySQL server with `log_bin=ON` and `log_bin_trust_function_creators=OFF`, creating a `NOT DETERMINISTIC` function that `READS SQL DATA` requires the `SUPER` privilege. In production, set `log_bin_trust_function_creators=1` carefully or design functions to be DETERMINISTIC.

### 1.4 Practical Scalar Functions

```sql
-- String helper: extract initials from a name
DELIMITER $$
CREATE FUNCTION get_initials (p_first VARCHAR(50), p_last VARCHAR(50))
RETURNS CHAR(3)
DETERMINISTIC
NO SQL
BEGIN
    RETURN CONCAT(UPPER(LEFT(p_first, 1)), '.', UPPER(LEFT(p_last, 1)), '.');
END$$
DELIMITER ;

-- Date helper: return the current academic semester code
CREATE FUNCTION current_semester ()
RETURNS CHAR(6)
NOT DETERMINISTIC
NO SQL
BEGIN
    RETURN CONCAT(
        IF(MONTH(NOW()) BETWEEN 1 AND 5, 'S', 'F'),
        YEAR(NOW())
    );
END$$
DELIMITER ;

-- Numeric: letter grade from numeric grade points
CREATE FUNCTION points_to_letter (p_points DECIMAL(3,2))
RETURNS CHAR(2)
DETERMINISTIC
NO SQL
BEGIN
    RETURN CASE
        WHEN p_points >= 3.85 THEN 'A'   WHEN p_points >= 3.50 THEN 'A-'
        WHEN p_points >= 3.15 THEN 'B+'  WHEN p_points >= 2.85 THEN 'B'
        WHEN p_points >= 2.50 THEN 'B-'  WHEN p_points >= 2.15 THEN 'C+'
        WHEN p_points >= 1.85 THEN 'C'   WHEN p_points >= 1.50 THEN 'C-'
        WHEN p_points >= 1.15 THEN 'D+'  WHEN p_points >= 0.85 THEN 'D'
        ELSE 'F'
    END;
END$$
DELIMITER ;
```

---

## 2. PostgreSQL Functions

### 2.1 RETURNS TABLE

```sql
-- Table-valued function: return all courses a student is enrolled in
CREATE OR REPLACE FUNCTION get_student_courses (p_student_id INT)
RETURNS TABLE (
    course_code VARCHAR(10),
    title       VARCHAR(150),
    credits     SMALLINT,
    semester    CHAR(6),
    grade       CHAR(2)
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
        SELECT c.course_code, c.title, c.credits, e.semester, e.grade
        FROM   enrollments e
        INNER JOIN courses c ON c.course_id = e.course_id
        WHERE  e.student_id = p_student_id
        ORDER BY e.semester DESC, c.course_code;
END;
$$;

-- Call it like a table:
SELECT * FROM get_student_courses(1042);
```

### 2.2 SETOF for Returning Existing Row Types

```sql
-- Return full student rows matching a department
CREATE OR REPLACE FUNCTION students_in_dept (p_dept_name TEXT)
RETURNS SETOF students
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
        SELECT s.*
        FROM   students    s
        INNER JOIN departments d ON d.dept_id = s.dept_id
        WHERE  d.dept_name = p_dept_name;
END;
$$;
```

=== "MySQL UDF"
    ```sql
    -- MySQL: scalar function, can be used in SELECT/WHERE
    SELECT student_id, calculate_gpa(student_id) AS gpa
    FROM   students
    WHERE  calculate_gpa(student_id) >= 3.5;
    ```

=== "PostgreSQL UDF"
    ```sql
    -- PostgreSQL: table-valued function in FROM
    SELECT s.first_name, s.last_name, sc.course_code, sc.grade
    FROM   students s,
           LATERAL get_student_courses(s.student_id) sc
    WHERE  sc.grade = 'A'
    ORDER BY s.last_name;
    ```

---

## 3. Trigger Fundamentals

A **trigger** is a stored program that automatically executes in response to a specified data modification event on a table.

### 3.1 Trigger Anatomy

```
CREATE TRIGGER trigger_name
{BEFORE | AFTER}
{INSERT | UPDATE | DELETE}
ON table_name
FOR EACH ROW
trigger_body;
```

| Component | Options | Meaning |
|-----------|---------|---------|
| **Timing** | BEFORE, AFTER | When does the trigger fire relative to the DML operation? |
| **Event** | INSERT, UPDATE, DELETE | Which operation triggers it? |
| **Granularity** | FOR EACH ROW | MySQL only supports row-level triggers |
| **NEW** | Available on INSERT, UPDATE | The new row values being written |
| **OLD** | Available on UPDATE, DELETE | The existing row values before modification |

!!! info "BEFORE vs AFTER"
    **BEFORE triggers** can modify `NEW` values before they are written — useful for data normalization and validation. **AFTER triggers** see the committed state and are used for auditing, cascades, and denormalization updates. You cannot modify `NEW` in an AFTER trigger.

### 3.2 Syntax Comparison

=== "MySQL"
    ```sql
    DELIMITER $$

    CREATE TRIGGER trg_students_before_update
    BEFORE UPDATE ON students
    FOR EACH ROW
    BEGIN
        -- Normalize email to lowercase before storing
        SET NEW.email = LOWER(NEW.email);

        -- Reject negative GPA
        IF NEW.gpa < 0 THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'GPA cannot be negative';
        END IF;
    END$$

    DELIMITER ;
    ```

=== "PostgreSQL"
    ```sql
    -- Step 1: create the trigger function
    CREATE OR REPLACE FUNCTION trg_students_before_update_fn()
    RETURNS TRIGGER
    LANGUAGE plpgsql
    AS $$
    BEGIN
        NEW.email = LOWER(NEW.email);
        IF NEW.gpa < 0 THEN
            RAISE EXCEPTION 'GPA cannot be negative';
        END IF;
        RETURN NEW;   -- BEFORE trigger must return NEW (or NULL to cancel)
    END;
    $$;

    -- Step 2: attach to the table
    CREATE TRIGGER trg_students_before_update
    BEFORE UPDATE ON students
    FOR EACH ROW EXECUTE FUNCTION trg_students_before_update_fn();
    ```

---

## 4. Trigger Use Cases with Complete Examples

### 4.1 Audit Logging

```sql
-- Setup audit table
CREATE TABLE enrollment_audit (
    audit_id     INT          PRIMARY KEY AUTO_INCREMENT,
    action_type  ENUM('INSERT','UPDATE','DELETE') NOT NULL,
    enrollment_id INT,
    student_id   INT,
    course_id    INT,
    old_grade    CHAR(2),
    new_grade    CHAR(2),
    changed_by   VARCHAR(100),
    changed_at   DATETIME(6)  DEFAULT NOW(6)
);

DELIMITER $$

-- Audit INSERT
CREATE TRIGGER trg_enrollment_audit_insert
AFTER INSERT ON enrollments
FOR EACH ROW
BEGIN
    INSERT INTO enrollment_audit
        (action_type, enrollment_id, student_id, course_id, new_grade, changed_by)
    VALUES
        ('INSERT', NEW.enrollment_id, NEW.student_id, NEW.course_id,
         NEW.grade, USER());
END$$

-- Audit UPDATE (only when grade changes)
CREATE TRIGGER trg_enrollment_audit_update
AFTER UPDATE ON enrollments
FOR EACH ROW
BEGIN
    IF OLD.grade != NEW.grade OR (OLD.grade IS NULL) != (NEW.grade IS NULL) THEN
        INSERT INTO enrollment_audit
            (action_type, enrollment_id, student_id, course_id,
             old_grade, new_grade, changed_by)
        VALUES
            ('UPDATE', NEW.enrollment_id, NEW.student_id, NEW.course_id,
             OLD.grade, NEW.grade, USER());
    END IF;
END$$

-- Audit DELETE
CREATE TRIGGER trg_enrollment_audit_delete
AFTER DELETE ON enrollments
FOR EACH ROW
BEGIN
    INSERT INTO enrollment_audit
        (action_type, enrollment_id, student_id, course_id, old_grade, changed_by)
    VALUES
        ('DELETE', OLD.enrollment_id, OLD.student_id, OLD.course_id,
         OLD.grade, USER());
END$$

DELIMITER ;
```

### 4.2 Data Validation (BEFORE INSERT)

```sql
DELIMITER $$

CREATE TRIGGER trg_enrollments_before_insert
BEFORE INSERT ON enrollments
FOR EACH ROW
BEGIN
    DECLARE v_existing_credits INT;
    DECLARE v_course_credits   INT;

    -- Rule 1: Semester must be a valid format (F or S + 4-digit year)
    IF NEW.semester NOT REGEXP '^[FS][0-9]{4}$' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Invalid semester format. Use F2025 or S2025.';
    END IF;

    -- Rule 2: Student cannot exceed 18 credits per semester
    SELECT COALESCE(SUM(c.credits), 0)
    INTO   v_existing_credits
    FROM   enrollments e
    INNER JOIN courses c ON c.course_id = e.course_id
    WHERE  e.student_id = NEW.student_id
      AND  e.semester   = NEW.semester;

    SELECT credits INTO v_course_credits
    FROM   courses WHERE course_id = NEW.course_id;

    IF v_existing_credits + v_course_credits > 18 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Enrollment would exceed 18-credit semester limit.';
    END IF;

    -- Rule 3: Auto-fill instructor_id if not provided
    IF NEW.instructor_id IS NULL THEN
        SELECT i.instructor_id INTO NEW.instructor_id
        FROM   instructors i
        INNER JOIN courses c ON c.dept_id = i.dept_id
        WHERE  c.course_id = NEW.course_id
        LIMIT  1;
    END IF;
END$$

DELIMITER ;
```

### 4.3 Automatic Timestamp Maintenance

```sql
-- Add tracking columns to students (if not already present)
ALTER TABLE students
    ADD COLUMN created_at  DATETIME DEFAULT NOW(),
    ADD COLUMN updated_at  DATETIME DEFAULT NOW() ON UPDATE NOW(),
    ADD COLUMN updated_by  VARCHAR(100);

DELIMITER $$

CREATE TRIGGER trg_students_set_updated
BEFORE UPDATE ON students
FOR EACH ROW
BEGIN
    SET NEW.updated_at = NOW(6);
    SET NEW.updated_by = USER();
END$$

DELIMITER ;
```

### 4.4 Denormalization Maintenance (Cached Aggregate)

```sql
-- Add a cached enrollment count column to courses
ALTER TABLE courses ADD COLUMN enrolled_count INT DEFAULT 0;

DELIMITER $$

CREATE TRIGGER trg_enroll_count_insert
AFTER INSERT ON enrollments
FOR EACH ROW
    UPDATE courses SET enrolled_count = enrolled_count + 1
    WHERE  course_id = NEW.course_id$$

CREATE TRIGGER trg_enroll_count_delete
AFTER DELETE ON enrollments
FOR EACH ROW
    UPDATE courses SET enrolled_count = enrolled_count - 1
    WHERE  course_id = OLD.course_id$$

-- Note: MySQL 8.0 allows single-statement triggers without BEGIN/END
DELIMITER ;
```

!!! success "Why Cache the Count?"
    `SELECT COUNT(*) FROM enrollments WHERE course_id = ?` requires a full index scan every time. Caching in a column makes the count O(1). The trigger keeps it consistent automatically. Trade-off: every INSERT/DELETE on enrollments adds a small UPDATE cost.

### 4.5 Archive Table Replication

```sql
CREATE TABLE enrollments_archive LIKE enrollments;
ALTER TABLE enrollments_archive
    ADD COLUMN archived_at DATETIME DEFAULT NOW(),
    ADD COLUMN archived_by VARCHAR(100);

DELIMITER $$

CREATE TRIGGER trg_enrollments_archive_delete
BEFORE DELETE ON enrollments
FOR EACH ROW
BEGIN
    INSERT INTO enrollments_archive
        (enrollment_id, student_id, course_id, instructor_id,
         semester, grade, archived_at, archived_by)
    VALUES
        (OLD.enrollment_id, OLD.student_id, OLD.course_id, OLD.instructor_id,
         OLD.semester, OLD.grade, NOW(6), USER());
END$$

DELIMITER ;
```

---

## 5. INSTEAD OF Triggers (PostgreSQL)

`INSTEAD OF` triggers fire **in place of** the DML operation — used primarily to make views updatable.

```sql
-- Create a view joining students and departments
CREATE VIEW student_dept_view AS
    SELECT s.student_id, s.first_name, s.last_name,
           s.gpa, d.dept_name
    FROM   students s
    INNER JOIN departments d ON d.dept_id = s.dept_id;

-- Allow UPDATE through the view
CREATE OR REPLACE FUNCTION upd_student_dept_view_fn()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    UPDATE students
    SET    first_name = NEW.first_name,
           last_name  = NEW.last_name,
           gpa        = NEW.gpa
    WHERE  student_id = OLD.student_id;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_instead_of_update
INSTEAD OF UPDATE ON student_dept_view
FOR EACH ROW EXECUTE FUNCTION upd_student_dept_view_fn();
```

---

## 6. Trigger Pitfalls and Best Practices

### 6.1 Recursive and Cascading Triggers

```sql
-- DANGER: This trigger updates students, which could fire another trigger on students
CREATE TRIGGER trg_after_grade_change
AFTER UPDATE ON enrollments
FOR EACH ROW
BEGIN
    -- This UPDATE on students may fire trg_students_set_updated
    UPDATE students SET gpa = calculate_gpa(NEW.student_id)
    WHERE  student_id = NEW.student_id;
    -- If trg_students_set_updated also updates enrollments → infinite loop!
END;
```

!!! danger "Recursive Trigger Prevention"
    MySQL prevents direct recursive triggers (a trigger that fires itself) but not indirect recursion (A fires B, B fires A). Use `@@SESSION.disable_trigger` flags or careful design to break cycles. In PostgreSQL, `pg_trigger_depth()` returns the current nesting level.

### 6.2 Performance Impact

| Trigger Volume | Impact | Mitigation |
|---------------|--------|------------|
| 1 trigger on 100-row table | Negligible | None needed |
| 3 triggers on 10M-row bulk INSERT | Severe | Disable triggers, bulk load, re-enable |
| AFTER triggers with subqueries | Cumulative | Ensure trigger queries use indexes |
| Trigger + FK + another trigger | Multiplicative | Profile with EXPLAIN |

### 6.3 Comparing Business Rule Enforcement Strategies

| Approach | Pros | Cons | Best For |
|----------|------|------|----------|
| **Trigger** | Automatic, always fires, DB-enforced | Hidden logic, hard to debug, performance cost | Auditing, timestamps, simple cascades |
| **Stored Procedure** | Centralized, testable, explicit | Must be called by all clients | Complex multi-step operations |
| **Application Layer** | Flexible, version-controlled, testable | Must be enforced in ALL apps | Complex business rules, UX validation |
| **CHECK Constraint** | Simple, declarative, fast | Limited expressiveness | Simple value validation |
| **FK Constraint** | Declarative, auto-cascades | Rigid; may not match business logic | Referential integrity |

!!! tip "Principle of Least Surprise"
    Hidden triggers are the #1 cause of "ghost updates" — data changing for no apparent reason. Document all triggers in a triggers registry table or comment header, and add `-- TRIGGER: trg_name fires here` comments to DML-heavy procedures.

---

## 7. Complete Example: Prevent-Delete Trigger with Override

```sql
-- Soft-delete pattern: prevent hard deletes on students; use a deleted_at column instead
ALTER TABLE students ADD COLUMN deleted_at DATETIME DEFAULT NULL;

DELIMITER $$

CREATE TRIGGER trg_students_prevent_delete
BEFORE DELETE ON students
FOR EACH ROW
BEGIN
    -- Allow deletion only if student has never enrolled
    IF EXISTS (SELECT 1 FROM enrollments WHERE student_id = OLD.student_id LIMIT 1) THEN
        -- Soft-delete instead of hard delete
        UPDATE students SET deleted_at = NOW(6) WHERE student_id = OLD.student_id;
        -- Signal cancels the DELETE
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Student has enrollment history — record soft-deleted instead.';
    END IF;
    -- If no enrollments, allow the hard delete to proceed (no SIGNAL)
END$$

DELIMITER ;
```

---

## 8. Built-In Function Categories Reference

Understanding the MySQL and PostgreSQL built-in function landscape prevents you from writing UDFs that duplicate existing functionality.

### 8.1 String Functions

```sql
-- Essential string functions used in university database context
SELECT
    CONCAT(first_name, ' ', last_name)         AS full_name,
    UPPER(last_name)                            AS last_upper,
    LOWER(email)                                AS email_norm,
    LENGTH(email)                               AS email_len,
    CHAR_LENGTH(first_name)                     AS fname_chars,   -- multi-byte safe
    TRIM(BOTH ' ' FROM '  Alice  ')             AS trimmed,
    SUBSTRING(email, 1, LOCATE('@', email) - 1) AS username,
    REPLACE(course_code, 'ITEC', 'CS')          AS new_code,
    LPAD(student_id, 8, '0')                    AS padded_id,
    REGEXP_REPLACE(email, '[^a-z0-9@.]', '')    AS sanitized_email
FROM students s
INNER JOIN courses c ON c.dept_id = s.dept_id
LIMIT 5;
```

### 8.2 Numeric and Aggregate Functions

```sql
SELECT
    ROUND(gpa, 1)                   AS gpa_rounded,
    TRUNCATE(gpa, 1)                AS gpa_truncated,  -- no rounding
    ABS(gpa - 3.0)                  AS distance_from_3,
    MOD(student_id, 10)             AS id_last_digit,
    POWER(gpa, 2)                   AS gpa_squared,
    GREATEST(gpa, 2.0)              AS at_least_2,
    LEAST(gpa, 4.0)                 AS capped_at_4,
    FORMAT(gpa, 2)                  AS formatted_str,  -- locale-aware, returns string
    COALESCE(gpa, 0.0)              AS gpa_or_zero
FROM students;
```

### 8.3 Date and Time Functions

```sql
SELECT
    NOW()                                               AS current_datetime,
    CURDATE()                                           AS today,
    DATE_FORMAT(hire_date, '%M %d, %Y')                 AS hire_display,
    DATEDIFF(CURDATE(), hire_date)                      AS days_employed,
    TIMESTAMPDIFF(YEAR, hire_date, CURDATE())           AS years_employed,
    DATE_ADD(CURDATE(), INTERVAL 1 SEMESTER)            AS -- not valid
    LAST_DAY(CURDATE())                                 AS end_of_month,
    DAYNAME(hire_date)                                  AS hire_weekday,
    WEEK(CURDATE(), 1)                                  AS iso_week,
    EXTRACT(YEAR FROM hire_date)                        AS hire_year
FROM instructors;
```

### 8.4 JSON Functions (MySQL 5.7+)

```sql
-- Students table with a JSON preferences column
ALTER TABLE students ADD COLUMN preferences JSON;

UPDATE students SET preferences = '{"theme":"dark","notifications":true,"lang":"en"}'
WHERE student_id = 1001;

SELECT
    student_id,
    JSON_EXTRACT(preferences, '$.theme')           AS theme,
    preferences->>'$.lang'                         AS lang,           -- shorthand
    JSON_CONTAINS(preferences, '"true"', '$.notifications') AS notif_on,
    JSON_KEYS(preferences)                         AS pref_keys,
    JSON_SET(preferences, '$.theme', 'light')      AS updated_prefs
FROM students
WHERE preferences IS NOT NULL;
```

### 8.5 Conditional Functions

```sql
SELECT
    student_id,
    gpa,
    IF(gpa >= 3.5, 'Honor Roll', 'Standard')           AS status,
    IFNULL(gpa, 0.00)                                  AS gpa_safe,
    NULLIF(grade, 'W')                                 AS non_withdrawal_grade, -- NULL if W
    CASE
        WHEN gpa >= 3.9 THEN 'Summa'
        WHEN gpa >= 3.7 THEN 'Magna'
        WHEN gpa >= 3.5 THEN 'Cum Laude'
        ELSE 'Standard'
    END                                                AS honor_status,
    COALESCE(grade, 'In Progress', 'Unknown')          AS grade_display
FROM students s
LEFT JOIN enrollments e ON e.student_id = s.student_id AND e.semester = 'F2025';
```

!!! info "NULLIF Usefulness"
    `NULLIF(x, y)` returns NULL if x = y, otherwise x. This is invaluable for preventing division-by-zero: `total / NULLIF(count, 0)` returns NULL instead of an error when count is 0.

---

## Key Vocabulary

| Term | Definition |
|------|------------|
| **Scalar UDF** | Function returning a single value; usable anywhere a value expression is valid |
| **Table-valued function** | Function returning a result set; used in the FROM clause (PostgreSQL) |
| **DETERMINISTIC** | Function attribute: same inputs always yield same output |
| **READS SQL DATA** | Function reads from tables but does not modify them |
| **MODIFIES SQL DATA** | Function performs INSERT, UPDATE, or DELETE |
| **Trigger** | Named procedure that fires automatically on INSERT, UPDATE, or DELETE |
| **BEFORE trigger** | Fires before the row change is written; can modify NEW values |
| **AFTER trigger** | Fires after the row change is committed; used for auditing and cascades |
| **NEW** | Pseudo-record representing the new row in INSERT/UPDATE triggers |
| **OLD** | Pseudo-record representing the existing row in UPDATE/DELETE triggers |
| **FOR EACH ROW** | Trigger executes once for every affected row (row-level) |
| **INSTEAD OF trigger** | Replaces the original DML operation; used for updatable views in PostgreSQL |
| **Soft delete** | Marking a record as deleted (e.g., deleted_at timestamp) instead of physically removing it |
| **Recursive trigger** | A trigger that directly or indirectly causes itself to fire again |
| **Denormalization** | Intentionally storing derived/redundant data for read performance |
| **Audit trail** | Historical record of all data changes including who made them and when |
| **SIGNAL** | MySQL statement to raise a custom error from a trigger or procedure |
| **RAISE EXCEPTION** | PostgreSQL statement to throw an error from a trigger function |
| **pg_trigger_depth()** | PostgreSQL function returning the current trigger call nesting depth |
| **User-defined aggregate** | Custom aggregation function operating across multiple rows (PostgreSQL CREATE AGGREGATE) |

---

!!! question "Self-Assessment"
    1. You need to enforce a rule that no student can enroll in a course they have already passed (grade A through D). Should this be a BEFORE INSERT trigger, a CHECK constraint, an application validation, or a stored procedure? Justify your choice with specific reasons, and then implement it as a BEFORE INSERT trigger.
    2. A colleague deletes 500,000 rows from the enrollments table and the operation takes 2 hours because of three AFTER DELETE triggers. Describe step-by-step how you would speed up this bulk delete while preserving trigger behavior for normal single-row deletes.
    3. Explain the exact difference in behavior between a BEFORE UPDATE trigger that does `SET NEW.gpa = ROUND(NEW.gpa, 2)` versus an AFTER UPDATE trigger that does `UPDATE students SET gpa = ROUND(gpa, 2) WHERE student_id = NEW.student_id`. What extra risk does the AFTER version introduce?
    4. You are designing a system where the `courses.enrolled_count` column must always match `COUNT(*) FROM enrollments WHERE course_id = ?`. Implement the full set of triggers (INSERT, UPDATE, DELETE on enrollments) needed to maintain this. What edge case involving UPDATE on enrollments could cause the count to go wrong?
    5. A PostgreSQL view joins `students`, `enrollments`, and `courses`. Write an INSTEAD OF INSERT trigger that inserts a new student if they don't exist and creates their first enrollment record — all in one `INSERT INTO the_view VALUES(...)` statement from the caller's perspective.

---

## Further Reading

- 📄 [MySQL 8.0 Reference — CREATE FUNCTION](https://dev.mysql.com/doc/refman/8.0/en/create-function.html)
- 📄 [MySQL 8.0 Reference — CREATE TRIGGER](https://dev.mysql.com/doc/refman/8.0/en/create-trigger.html)
- 📄 [PostgreSQL — PL/pgSQL Trigger Functions](https://www.postgresql.org/docs/current/plpgsql-trigger.html)
- 📄 [PostgreSQL — CREATE FUNCTION](https://www.postgresql.org/docs/current/sql-createfunction.html)
- 📖 *MySQL Stored Procedure Programming* (Harrison & Feuerstein) — Chapter 11: Triggers
- 📄 [Percona Blog — MySQL Triggers Performance](https://www.percona.com/blog/)
- 🎥 "Triggers vs. Application Logic" — PGConf 2023 (freely available on YouTube)

---

*[← Week 3](week03.md) &nbsp;|&nbsp; [Course Index](index.md) &nbsp;|&nbsp; [Week 5 →](week05.md)*
