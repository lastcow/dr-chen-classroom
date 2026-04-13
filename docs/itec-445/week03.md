---
title: "Week 3 — Stored Procedures & Control Flow Programming"
description: Move database logic server-side with MySQL and PostgreSQL stored procedures — mastering parameters, control flow, cursors, error handling, transactions, and real-world batch workflows.
---

# Week 3 — Stored Procedures & Control Flow Programming

<div class="week-meta" markdown>
**Course Objectives:** CO2 &nbsp;|&nbsp; **Focus:** Procedural SQL Programming &nbsp;|&nbsp; **Difficulty:** ⭐⭐⭐☆☆
</div>

---

## Learning Objectives

By the end of this week, you will be able to:

- [ ] Articulate the performance, security, and maintainability benefits of stored procedures over ad-hoc SQL
- [ ] Write MySQL stored procedures using DELIMITER, CREATE PROCEDURE, and IN/OUT/INOUT parameters
- [ ] Write equivalent PostgreSQL procedures using PL/pgSQL block structure
- [ ] Implement control flow with IF/ELSEIF/ELSE, CASE, LOOP, WHILE, and REPEAT
- [ ] Build cursor-driven row-by-row processing with proper NOT FOUND exit handling
- [ ] Declare and use condition handlers for SQLEXCEPTION, SQLWARNING, and custom error codes
- [ ] Embed transactions (START TRANSACTION, COMMIT, ROLLBACK, SAVEPOINT) within procedures
- [ ] Distinguish DEFINER vs INVOKER security and explain when each is appropriate
- [ ] Design and implement a complete real-world stored procedure with logging and error recovery

---

## 1. Why Stored Procedures?

A **stored procedure** is a named, compiled program stored within the database server that encapsulates one or more SQL statements plus procedural logic.

### 1.1 Benefits Over Ad-Hoc SQL

| Benefit | Explanation |
|---------|-------------|
| **Compiled execution plan** | The first execution parses, optimizes, and caches the plan. Subsequent calls reuse the cached plan — no parse overhead. |
| **Reduced network traffic** | Client sends one `CALL proc(args)` instead of dozens of SQL statements over the network. |
| **Centralized business logic** | Logic lives in one place — not scattered across Java, Python, PHP, and shell scripts. |
| **Security boundary** | Grant `EXECUTE` on a procedure without exposing underlying tables. Users can call the procedure but cannot `SELECT * FROM salary_data` directly. |
| **Atomicity wrapper** | Wrap multi-step operations in a transaction inside the procedure so callers don't need to manage transaction state. |
| **Consistency** | All applications use the same validated logic; one code change propagates everywhere. |

!!! warning "Stored Procedures Are Not Always the Answer"
    Procedures shift logic into the database, making it harder to version-control, test, and deploy in modern CI/CD pipelines. Use them for data-intensive batch work and security boundaries, not for all business logic.

### 1.2 When NOT to Use Stored Procedures

- Complex presentation or formatting logic (belongs in the application)
- Business rules that change frequently (harder to deploy DB changes)
- Logic requiring external API calls (procedures are sandboxed)
- Teams unfamiliar with PL/SQL — maintenance burden is real

---

## 2. MySQL Stored Procedure Syntax

### 2.1 Basic Structure and DELIMITER

MySQL uses the semicolon `;` as both the statement terminator and the procedure-end marker, causing a conflict. You must redefine the delimiter before `CREATE PROCEDURE`.

```sql
DELIMITER $$

CREATE PROCEDURE procedure_name (
    IN  param1 datatype,
    OUT param2 datatype,
    INOUT param3 datatype
)
BEGIN
    -- procedure body
    SQL statements;
END$$

DELIMITER ;
```

### 2.2 IN, OUT, and INOUT Parameters

```sql
DELIMITER $$

CREATE PROCEDURE get_student_info (
    IN  p_student_id INT,
    OUT p_full_name  VARCHAR(101),
    OUT p_gpa        DECIMAL(3,2),
    OUT p_dept_name  VARCHAR(100)
)
BEGIN
    SELECT CONCAT(s.first_name, ' ', s.last_name),
           s.gpa,
           d.dept_name
    INTO   p_full_name, p_gpa, p_dept_name
    FROM   students    s
    INNER JOIN departments d ON d.dept_id = s.dept_id
    WHERE  s.student_id = p_student_id;
END$$

DELIMITER ;

-- Calling the procedure
CALL get_student_info(1042, @name, @gpa, @dept);
SELECT @name AS student, @gpa AS gpa, @dept AS department;
```

```sql
-- INOUT example: normalize a GPA value (cap at 4.0)
DELIMITER $$

CREATE PROCEDURE normalize_gpa (INOUT p_gpa DECIMAL(3,2))
BEGIN
    IF p_gpa > 4.0 THEN SET p_gpa = 4.0; END IF;
    IF p_gpa < 0.0 THEN SET p_gpa = 0.0; END IF;
END$$

DELIMITER ;

SET @my_gpa = 4.3;
CALL normalize_gpa(@my_gpa);
SELECT @my_gpa;   -- Returns 4.00
```

---

## 3. PostgreSQL PL/pgSQL Procedure Syntax

=== "MySQL"
    ```sql
    DELIMITER $$
    CREATE PROCEDURE enroll_student (
        IN p_student_id INT,
        IN p_course_id  INT,
        IN p_semester   CHAR(6)
    )
    BEGIN
        INSERT INTO enrollments (student_id, course_id, semester)
        VALUES (p_student_id, p_course_id, p_semester);
    END$$
    DELIMITER ;
    ```

=== "PostgreSQL"
    ```sql
    CREATE OR REPLACE PROCEDURE enroll_student (
        p_student_id INT,
        p_course_id  INT,
        p_semester   CHAR(6)
    )
    LANGUAGE plpgsql
    AS $$
    BEGIN
        INSERT INTO enrollments (student_id, course_id, semester)
        VALUES (p_student_id, p_course_id, p_semester);
        COMMIT;   -- explicit COMMIT required in PL/pgSQL procedures
    END;
    $$;

    -- Calling in PostgreSQL
    CALL enroll_student(1042, 7, 'F2025');
    ```

!!! info "PostgreSQL Functions vs Procedures"
    In PostgreSQL, `CREATE FUNCTION` and `CREATE PROCEDURE` are different. **Functions** return a value and run inside the caller's transaction. **Procedures** (added in PG 11) can issue COMMIT/ROLLBACK and are called with `CALL`.

---

## 4. Control Flow

### 4.1 IF / ELSEIF / ELSE

```sql
DELIMITER $$

CREATE PROCEDURE assign_honor_status (IN p_student_id INT)
BEGIN
    DECLARE v_gpa DECIMAL(3,2);

    SELECT gpa INTO v_gpa FROM students WHERE student_id = p_student_id;

    IF v_gpa >= 3.9 THEN
        UPDATE students SET honor_status = 'Summa Cum Laude'  WHERE student_id = p_student_id;
    ELSEIF v_gpa >= 3.7 THEN
        UPDATE students SET honor_status = 'Magna Cum Laude'  WHERE student_id = p_student_id;
    ELSEIF v_gpa >= 3.5 THEN
        UPDATE students SET honor_status = 'Cum Laude'        WHERE student_id = p_student_id;
    ELSE
        UPDATE students SET honor_status = NULL               WHERE student_id = p_student_id;
    END IF;
END$$

DELIMITER ;
```

### 4.2 CASE Statement

```sql
DELIMITER $$

CREATE PROCEDURE get_letter_grade (
    IN  p_points DECIMAL(3,1),
    OUT p_letter CHAR(2)
)
BEGIN
    SET p_letter = CASE
        WHEN p_points >= 3.85 THEN 'A'
        WHEN p_points >= 3.50 THEN 'A-'
        WHEN p_points >= 3.15 THEN 'B+'
        WHEN p_points >= 2.85 THEN 'B'
        WHEN p_points >= 2.50 THEN 'B-'
        WHEN p_points >= 2.15 THEN 'C+'
        WHEN p_points >= 1.85 THEN 'C'
        WHEN p_points >= 1.50 THEN 'C-'
        WHEN p_points >= 1.15 THEN 'D+'
        WHEN p_points >= 0.85 THEN 'D'
        ELSE 'F'
    END;
END$$

DELIMITER ;
```

### 4.3 Loop Constructs

=== "WHILE"
    ```sql
    -- WHILE: pre-test loop
    DELIMITER $$
    CREATE PROCEDURE count_down (IN p_start INT)
    BEGIN
        DECLARE v_i INT DEFAULT p_start;
        WHILE v_i > 0 DO
            INSERT INTO debug_log (msg, ts) VALUES (CONCAT('Count: ', v_i), NOW());
            SET v_i = v_i - 1;
        END WHILE;
    END$$
    DELIMITER ;
    ```

=== "REPEAT"
    ```sql
    -- REPEAT: post-test loop (always executes at least once)
    DELIMITER $$
    CREATE PROCEDURE retry_operation (IN p_max_retries INT)
    BEGIN
        DECLARE v_attempts INT DEFAULT 0;
        DECLARE v_success  TINYINT DEFAULT 0;
        REPEAT
            SET v_attempts = v_attempts + 1;
            -- attempt_operation() returns 1 on success
            SET v_success = attempt_operation();
        UNTIL v_success = 1 OR v_attempts >= p_max_retries
        END REPEAT;
    END$$
    DELIMITER ;
    ```

=== "LOOP / LEAVE / ITERATE"
    ```sql
    -- LOOP with LEAVE (break) and ITERATE (continue)
    DELIMITER $$
    CREATE PROCEDURE process_batch (IN p_limit INT)
    BEGIN
        DECLARE v_i INT DEFAULT 0;
        batch_loop: LOOP
            SET v_i = v_i + 1;
            IF v_i > p_limit THEN
                LEAVE batch_loop;         -- break
            END IF;
            IF MOD(v_i, 2) = 0 THEN
                ITERATE batch_loop;       -- continue (skip even numbers)
            END IF;
            -- process odd-numbered items
            INSERT INTO processed (item_num) VALUES (v_i);
        END LOOP batch_loop;
    END$$
    DELIMITER ;
    ```

---

## 5. Cursors

A **cursor** allows row-by-row processing of a query result set inside a stored procedure — necessary when set-based operations are insufficient.

### 5.1 Complete Cursor Pattern

```sql
DELIMITER $$

CREATE PROCEDURE calculate_all_gpas ()
BEGIN
    -- 1. Declare variables to hold each row's data
    DECLARE v_student_id INT;
    DECLARE v_calculated_gpa DECIMAL(3,2);
    DECLARE v_done TINYINT DEFAULT 0;

    -- 2. Declare the cursor
    DECLARE cur_students CURSOR FOR
        SELECT DISTINCT student_id FROM enrollments WHERE grade IS NOT NULL;

    -- 3. Declare NOT FOUND handler (MUST come after cursor declaration)
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_done = 1;

    -- 4. Open cursor
    OPEN cur_students;

    -- 5. Fetch loop
    fetch_loop: LOOP
        FETCH cur_students INTO v_student_id;

        IF v_done = 1 THEN
            LEAVE fetch_loop;
        END IF;

        -- Calculate GPA for this student
        SELECT ROUND(AVG(points), 2)
        INTO   v_calculated_gpa
        FROM   grade_points
        WHERE  student_id = v_student_id
          AND  points IS NOT NULL;

        -- Update the students table
        UPDATE students
        SET    gpa = v_calculated_gpa
        WHERE  student_id = v_student_id;

    END LOOP fetch_loop;

    -- 6. Close cursor
    CLOSE cur_students;
END$$

DELIMITER ;
```

!!! warning "Cursor Performance"
    Cursors execute row-by-row in the database server, which is slow for large datasets. Before reaching for a cursor, ask whether a single set-based UPDATE…JOIN or INSERT…SELECT can accomplish the same result. Cursors are appropriate when the per-row logic cannot be expressed as a set operation.

### 5.2 Nested Cursors

MySQL supports nested cursors, but each cursor needs its own `NOT FOUND` handler variable. Declare the inner cursor's handler after opening the outer cursor, or use separate procedures.

---

## 6. Error Handling

### 6.1 DECLARE HANDLER

```sql
DELIMITER $$

CREATE PROCEDURE safe_enroll (
    IN  p_student_id INT,
    IN  p_course_id  INT,
    IN  p_semester   CHAR(6),
    OUT p_result     VARCHAR(100)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_result = 'ERROR: Enrollment failed — transaction rolled back.';
    END;

    DECLARE EXIT HANDLER FOR 1062    -- MySQL error: Duplicate entry
    BEGIN
        SET p_result = 'ERROR: Student already enrolled in this course this semester.';
    END;

    START TRANSACTION;

    INSERT INTO enrollments (student_id, course_id, semester)
    VALUES (p_student_id, p_course_id, p_semester);

    COMMIT;
    SET p_result = 'SUCCESS: Enrollment recorded.';
END$$

DELIMITER ;
```

### 6.2 CONTINUE vs EXIT Handlers

| Handler Type | Behavior | Use When |
|--------------|----------|----------|
| `EXIT HANDLER` | Immediately exits the BEGIN…END block | Fatal errors that should stop execution |
| `CONTINUE HANDLER` | Sets flag and continues execution | Non-fatal errors you want to log and skip |

```sql
-- CONTINUE handler: log error and skip to next row
DECLARE CONTINUE HANDLER FOR SQLEXCEPTION
BEGIN
    GET DIAGNOSTICS CONDITION 1
        @err_code = MYSQL_ERRNO,
        @err_msg  = MESSAGE_TEXT;
    INSERT INTO error_log (proc_name, error_code, error_msg, occurred_at)
    VALUES ('my_procedure', @err_code, @err_msg, NOW());
    SET v_error_count = v_error_count + 1;
END;
```

### 6.3 RESIGNAL — Re-Raising Errors

```sql
DELIMITER $$

CREATE PROCEDURE validated_enrollment (
    IN p_student_id INT,
    IN p_course_id  INT,
    IN p_semester   CHAR(6)
)
BEGIN
    DECLARE v_credits INT;

    -- Business rule: max 18 credits per semester
    SELECT COALESCE(SUM(c.credits), 0)
    INTO   v_credits
    FROM   enrollments e
    INNER JOIN courses c ON c.course_id = e.course_id
    WHERE  e.student_id = p_student_id
      AND  e.semester   = p_semester;

    IF v_credits >= 18 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Credit limit exceeded: maximum 18 credits per semester',
                MYSQL_ERRNO  = 1644;
    END IF;

    INSERT INTO enrollments (student_id, course_id, semester)
    VALUES (p_student_id, p_course_id, p_semester);
END$$

DELIMITER ;
```

---

## 7. Transactions Inside Procedures

### 7.1 Basic Transaction Pattern

```sql
DELIMITER $$

CREATE PROCEDURE transfer_enrollment (
    IN  p_student_id   INT,
    IN  p_from_section INT,
    IN  p_to_section   INT,
    IN  p_semester     CHAR(6),
    OUT p_status       VARCHAR(100)
)
BEGIN
    DECLARE v_to_capacity INT;
    DECLARE v_to_enrolled INT;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_status = 'FAILED: Unexpected error. Transaction rolled back.';
    END;

    START TRANSACTION;

    -- Check capacity of target section
    SELECT capacity INTO v_to_capacity
    FROM   course_sections WHERE section_id = p_to_section;

    SELECT COUNT(*) INTO v_to_enrolled
    FROM   enrollments
    WHERE  course_id = p_to_section AND semester = p_semester;

    IF v_to_enrolled >= v_to_capacity THEN
        ROLLBACK;
        SET p_status = 'FAILED: Target section is full.';
    ELSE
        -- Remove from old section
        DELETE FROM enrollments
        WHERE  student_id = p_student_id
          AND  course_id  = p_from_section
          AND  semester   = p_semester;

        -- Add to new section
        INSERT INTO enrollments (student_id, course_id, semester)
        VALUES (p_student_id, p_to_section, p_semester);

        COMMIT;
        SET p_status = 'SUCCESS: Transfer complete.';
    END IF;
END$$

DELIMITER ;
```

### 7.2 SAVEPOINT for Partial Rollback

```sql
DELIMITER $$

CREATE PROCEDURE batch_grade_import (IN p_semester CHAR(6))
BEGIN
    DECLARE v_done     TINYINT DEFAULT 0;
    DECLARE v_s_id     INT;
    DECLARE v_c_id     INT;
    DECLARE v_grade    CHAR(2);
    DECLARE v_failures INT DEFAULT 0;

    DECLARE cur CURSOR FOR
        SELECT student_id, course_id, grade FROM grade_import_staging
        WHERE  semester = p_semester;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_done = 1;
    DECLARE CONTINUE HANDLER FOR SQLEXCEPTION SET v_failures = v_failures + 1;

    OPEN cur;
    gloop: LOOP
        FETCH cur INTO v_s_id, v_c_id, v_grade;
        IF v_done THEN LEAVE gloop; END IF;

        SAVEPOINT sp_row;

        UPDATE enrollments
        SET    grade = v_grade
        WHERE  student_id = v_s_id
          AND  course_id  = v_c_id
          AND  semester   = p_semester;

        IF ROW_COUNT() = 0 THEN
            ROLLBACK TO SAVEPOINT sp_row;
            INSERT INTO import_errors VALUES (p_semester, v_s_id, v_c_id, 'No matching enrollment');
        END IF;

        RELEASE SAVEPOINT sp_row;
    END LOOP gloop;
    CLOSE cur;

    SELECT CONCAT('Import complete. Failures: ', v_failures) AS result;
END$$

DELIMITER ;
```

---

## 8. Procedure Security: DEFINER vs INVOKER

```sql
-- DEFINER (default): procedure runs with the privileges of the creator
CREATE DEFINER = 'app_admin'@'localhost'
PROCEDURE secure_grade_update (IN p_student_id INT, IN p_grade CHAR(2))
SQL SECURITY DEFINER
BEGIN
    UPDATE enrollments SET grade = p_grade WHERE student_id = p_student_id;
END;

-- INVOKER: procedure runs with the privileges of the caller
CREATE PROCEDURE my_report ()
SQL SECURITY INVOKER
BEGIN
    SELECT * FROM enrollments;  -- caller must have SELECT on enrollments
END;
```

| Mode | Runs As | Use Case |
|------|---------|----------|
| `SQL SECURITY DEFINER` | Procedure owner | Allow limited users to perform privileged operations through a controlled interface |
| `SQL SECURITY INVOKER` | Calling user | Caller's own permissions determine access; useful for audit/reporting |

!!! danger "DEFINER Security Risks"
    A DEFINER procedure grants callers the procedure owner's privileges for those specific operations. If the procedure has a SQL injection vulnerability (e.g., dynamic SQL with user input), an attacker can execute arbitrary SQL as the owner. Always use parameterized queries inside procedures.

---

## 9. Debugging Stored Procedures

### 9.1 Debug Logging Table

```sql
CREATE TABLE proc_debug_log (
    log_id     INT           PRIMARY KEY AUTO_INCREMENT,
    proc_name  VARCHAR(100),
    step       VARCHAR(200),
    var_dump   TEXT,
    logged_at  DATETIME(6)   DEFAULT NOW(6)
);

-- Inside your procedure, instrument key points:
INSERT INTO proc_debug_log (proc_name, step, var_dump)
VALUES ('calculate_all_gpas', 'Before GPA update',
        CONCAT('student_id=', v_student_id, ' gpa=', v_calculated_gpa));
```

### 9.2 Session Variables for Lightweight Debugging

```sql
-- Quick debug without a table
SET @debug_step = 'Starting enrollment check';
-- ... procedure logic ...
SET @debug_step = 'After credit limit validation';
-- After CALL:
SELECT @debug_step;
```

### 9.3 Using MySQL Workbench Debugger

```
Tools → Stored Procedure Debugger
1. Open the procedure in the editor
2. Click "Debug" button (green bug icon)
3. Set breakpoints by clicking line numbers
4. Step Over (F8), Step Into (F7), Continue (F5)
5. Watch panel shows variable values in real time
```

!!! tip "Enable General Query Log for Debugging"
    ```sql
    SET GLOBAL general_log = 'ON';
    SET GLOBAL general_log_file = '/var/log/mysql/general.log';
    -- Run your CALL statement
    -- Inspect the log to see every SQL statement executed
    SET GLOBAL general_log = 'OFF';
    ```

---

## 10. Real-World Procedure: Student GPA Recalculation

```sql
DELIMITER $$

CREATE PROCEDURE recalculate_semester_gpas (
    IN  p_semester  CHAR(6),
    OUT p_updated   INT,
    OUT p_errors    INT
)
BEGIN
    DECLARE v_student_id   INT;
    DECLARE v_new_gpa      DECIMAL(3,2);
    DECLARE v_done         TINYINT DEFAULT 0;
    DECLARE v_update_count INT DEFAULT 0;
    DECLARE v_err_count    INT DEFAULT 0;

    DECLARE cur CURSOR FOR
        SELECT DISTINCT student_id FROM enrollments WHERE semester = p_semester;

    DECLARE CONTINUE HANDLER FOR NOT FOUND   SET v_done = 1;
    DECLARE CONTINUE HANDLER FOR SQLEXCEPTION SET v_err_count = v_err_count + 1;

    -- Log procedure start
    INSERT INTO proc_debug_log (proc_name, step, var_dump)
    VALUES ('recalculate_semester_gpas', 'START', CONCAT('semester=', p_semester));

    START TRANSACTION;

    OPEN cur;
    gpa_loop: LOOP
        FETCH cur INTO v_student_id;
        IF v_done THEN LEAVE gpa_loop; END IF;

        -- Compute cumulative GPA across all completed semesters
        SELECT ROUND(AVG(gp.points), 2)
        INTO   v_new_gpa
        FROM   grade_points gp
        WHERE  gp.student_id = v_student_id
          AND  gp.points     IS NOT NULL;

        UPDATE students SET gpa = v_new_gpa WHERE student_id = v_student_id;
        SET v_update_count = v_update_count + 1;
    END LOOP gpa_loop;
    CLOSE cur;

    COMMIT;

    SET p_updated = v_update_count;
    SET p_errors  = v_err_count;

    INSERT INTO proc_debug_log (proc_name, step, var_dump)
    VALUES ('recalculate_semester_gpas', 'END',
            CONCAT('updated=', v_update_count, ' errors=', v_err_count));
END$$

DELIMITER ;

-- Execute and check results
CALL recalculate_semester_gpas('F2025', @updated, @errors);
SELECT @updated AS rows_updated, @errors AS error_count;
```

---

## Key Vocabulary

| Term | Definition |
|------|------------|
| **Stored procedure** | Named, compiled program stored in the database server |
| **DELIMITER** | MySQL command to change the statement terminator during procedure creation |
| **IN parameter** | Value passed into a procedure; cannot be modified and returned |
| **OUT parameter** | Value set by the procedure and returned to the caller |
| **INOUT parameter** | Passed in by the caller, modified, and returned |
| **DECLARE** | Statement to define local variables, cursors, and condition handlers |
| **Cursor** | Database object for row-by-row result set traversal |
| **FETCH** | Retrieve the next row from an open cursor |
| **NOT FOUND handler** | CONTINUE handler triggered when a FETCH finds no more rows |
| **SQLEXCEPTION** | Catch-all handler for any SQL error (non-completion condition) |
| **SQLWARNING** | Handler for SQL warnings (completion conditions with warnings) |
| **SIGNAL** | Raise a custom error condition from within a procedure |
| **RESIGNAL** | Re-raise the current error condition, optionally with new attributes |
| **SAVEPOINT** | Named point within a transaction allowing partial rollback |
| **SQL SECURITY DEFINER** | Procedure executes with the permissions of its creator |
| **SQL SECURITY INVOKER** | Procedure executes with the permissions of the calling user |
| **Execution plan caching** | Reuse of a query's parsed and optimized plan across calls |
| **PL/pgSQL** | PostgreSQL's procedural language for stored procedures and functions |
| **GET DIAGNOSTICS** | MySQL statement to retrieve error information from the diagnostics area |
| **ROW_COUNT()** | MySQL function returning the number of rows affected by the last DML statement |

---

!!! question "Self-Assessment"
    1. A developer argues that all business logic should live in the application layer, never in stored procedures. Write a counterargument with three specific database scenarios where stored procedures are clearly superior. Then describe one scenario where the developer's position is correct.
    2. Your cursor-based procedure processes 100,000 rows correctly but takes 8 minutes. Describe two specific rewrites (set-based SQL) that could reduce this to under 10 seconds.
    3. Explain the exact execution sequence when a `CONTINUE HANDLER FOR SQLEXCEPTION` fires inside a cursor fetch loop. What happens to the current row? What happens to subsequent rows? Where does execution resume?
    4. A procedure uses `SQL SECURITY DEFINER` and builds a dynamic SQL string using `CONCAT()` with a user-supplied parameter, then executes it with `PREPARE`/`EXECUTE`. What is the security vulnerability, and how do you fix it?
    5. Design a stored procedure `process_withdrawals(p_semester CHAR(6))` that: (a) marks all NULL-grade enrollments for students with 0 attendance as 'W', (b) recalculates those students' GPAs, (c) logs each change to an audit table, (d) uses a SAVEPOINT per student so a failure on one student doesn't rollback all others. Write the complete procedure.

---

## Further Reading

- 📖 *MySQL Stored Procedure Programming* (Guy Harrison, Steven Feuerstein) — the definitive reference
- 📄 [MySQL 8.0 Reference — Stored Routines](https://dev.mysql.com/doc/refman/8.0/en/stored-routines.html)
- 📄 [MySQL 8.0 Reference — Condition Handling](https://dev.mysql.com/doc/refman/8.0/en/condition-handling.html)
- 📄 [PostgreSQL PL/pgSQL Documentation](https://www.postgresql.org/docs/current/plpgsql.html)
- 📄 [MySQL 8.0 — SIGNAL and RESIGNAL](https://dev.mysql.com/doc/refman/8.0/en/signal.html)
- 📖 *Expert MySQL*, Chapter 9 — "Stored Routines"
- 🎥 Percona Live — "Best Practices for MySQL Stored Procedures" (freely available on YouTube)

---

*[← Week 2](week02.md) &nbsp;|&nbsp; [Course Index](index.md) &nbsp;|&nbsp; [Week 4 →](week04.md)*
