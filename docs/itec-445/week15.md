---
title: "Week 15 — Advanced Project Implementation & Capstone Review"
description: "Complete capstone project: build the University Course Registration System from schema design through stored procedures, triggers, security, views, indexing, scripting, and monitoring — then synthesise all 15 weeks."
---

# Week 15 — Advanced Project Implementation & Capstone Review

**Course Objectives: CO9** | **Focus: Capstone Project, Synthesis, Career Paths** | **Difficulty: ⭐⭐⭐⭐⭐**

---

## Learning Objectives

By the end of this week, you should be able to:

- [ ] Design and implement a fully normalised 8-table schema for a real-world registration system
- [ ] Write advanced stored procedures with cursor iteration, conditional logic, and error signalling
- [ ] Implement BEFORE and AFTER triggers that enforce business rules and maintain audit trails
- [ ] Create user-defined functions for computed values used across views and procedures
- [ ] Apply a complete role-based security model with granular privilege grants
- [ ] Define views that encapsulate complex joins and serve specific application layers
- [ ] Justify every index with EXPLAIN output analysis and explain the trade-off
- [ ] Write a Python ETL script that validates and imports enrollment data from CSV
- [ ] Configure and verify Event Scheduler events for nightly and semester-end automation
- [ ] Articulate how all 15 weeks of the course connect into professional database engineering practice

---

## 1. Capstone Project Overview — University Course Registration System

This capstone delivers a production-quality database for Frostburg State University's Course Registration System. It integrates every major topic covered in ITEC 445: schema design, stored procedures, triggers, functions, security, views, indexing, scripting, and automation.

!!! info "Project Scope"
    **System:** FCRS — Frostburg Course Registration System  
    **Database:** `fcrs` (MySQL 8.0)  
    **Tables:** 9 core tables + 1 audit table  
    **Users/Roles:** 4 roles with distinct privilege sets  
    **Deliverables:** Schema DDL, procedures, triggers, functions, views, indexes, Python importer, backup script, event scheduler, health check procedure, project documentation

---

## 2. Full Normalised Schema

### 2.1 Entity-Relationship Overview

```
departments ──< courses ──< sections ──< enrollments >── students
                                              │
                                          grades ─── (1:1 per enrollment)
instructors >── sections (instructor assigned to section)
courses >── prerequisites (self-referential many-to-many)
audit_log ──── (records all sensitive changes)
```

### 2.2 CREATE TABLE Statements

```sql title="fcrs_schema.sql — complete DDL"
-- ============================================================
-- FCRS: Frostburg Course Registration System
-- MySQL 8.0+
-- ============================================================
CREATE DATABASE IF NOT EXISTS fcrs
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE fcrs;

SET FOREIGN_KEY_CHECKS = 0;

-- ============================================================
-- TABLE: departments
-- ============================================================
CREATE TABLE IF NOT EXISTS departments (
    dept_id     TINYINT UNSIGNED   NOT NULL AUTO_INCREMENT,
    dept_code   CHAR(4)            NOT NULL COMMENT 'e.g. ITEC, MATH, ENGL',
    dept_name   VARCHAR(80)        NOT NULL,
    building    VARCHAR(40)        NULL,
    chair_id    INT                NULL     COMMENT 'FK -> instructors; set after instructors loaded',
    created_at  DATETIME           NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (dept_id),
    UNIQUE KEY uq_dept_code (dept_code)
) ENGINE=InnoDB COMMENT='Academic departments';

-- ============================================================
-- TABLE: instructors
-- ============================================================
CREATE TABLE IF NOT EXISTS instructors (
    instructor_id   INT UNSIGNED       NOT NULL AUTO_INCREMENT,
    first_name      VARCHAR(50)        NOT NULL,
    last_name       VARCHAR(50)        NOT NULL,
    email           VARCHAR(120)       NOT NULL,
    dept_id         TINYINT UNSIGNED   NOT NULL,
    title           ENUM('Instructor','Asst Professor','Assoc Professor',
                         'Professor','Adjunct','Lecturer')
                                       NOT NULL DEFAULT 'Instructor',
    hired_date      DATE               NOT NULL,
    is_active       TINYINT(1)         NOT NULL DEFAULT 1,
    PRIMARY KEY (instructor_id),
    UNIQUE KEY uq_instructor_email (email),
    KEY idx_instructor_dept (dept_id),
    CONSTRAINT fk_instr_dept FOREIGN KEY (dept_id)
        REFERENCES departments(dept_id) ON UPDATE CASCADE
) ENGINE=InnoDB COMMENT='Faculty and instructors';

-- Now set chair FK (deferred to avoid circular ref)
ALTER TABLE departments
    ADD CONSTRAINT fk_dept_chair FOREIGN KEY (chair_id)
        REFERENCES instructors(instructor_id) ON DELETE SET NULL;

-- ============================================================
-- TABLE: students
-- ============================================================
CREATE TABLE IF NOT EXISTS students (
    student_id      INT UNSIGNED       NOT NULL AUTO_INCREMENT,
    fsuid           CHAR(9)            NOT NULL COMMENT 'FSU student ID e.g. B00123456',
    first_name      VARCHAR(50)        NOT NULL,
    last_name       VARCHAR(50)        NOT NULL,
    preferred_name  VARCHAR(50)        NULL,
    email           VARCHAR(120)       NOT NULL,
    dept_id         TINYINT UNSIGNED   NULL     COMMENT 'Declared major department',
    gpa             DECIMAL(4,3)       NOT NULL DEFAULT 0.000,
    credit_hours    SMALLINT UNSIGNED  NOT NULL DEFAULT 0 COMMENT 'Total completed credit hours',
    enrollment_status ENUM('active','suspended','withdrawn','graduated','applicant')
                                       NOT NULL DEFAULT 'active',
    admit_date      DATE               NOT NULL,
    grad_date       DATE               NULL,
    PRIMARY KEY (student_id),
    UNIQUE KEY uq_student_fsuid (fsuid),
    UNIQUE KEY uq_student_email (email),
    KEY idx_student_dept (dept_id),
    KEY idx_student_status (enrollment_status),
    CONSTRAINT fk_student_dept FOREIGN KEY (dept_id)
        REFERENCES departments(dept_id) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB COMMENT='Registered students';

-- ============================================================
-- TABLE: courses
-- ============================================================
CREATE TABLE IF NOT EXISTS courses (
    course_id       INT UNSIGNED       NOT NULL AUTO_INCREMENT,
    dept_id         TINYINT UNSIGNED   NOT NULL,
    course_code     VARCHAR(10)        NOT NULL COMMENT 'e.g. ITEC445',
    title           VARCHAR(120)       NOT NULL,
    description     TEXT               NULL,
    credit_hours    TINYINT UNSIGNED   NOT NULL DEFAULT 3,
    level           ENUM('100','200','300','400','500','600')
                                       NOT NULL DEFAULT '400',
    is_active       TINYINT(1)         NOT NULL DEFAULT 1,
    PRIMARY KEY (course_id),
    UNIQUE KEY uq_course_code (course_code),
    KEY idx_course_dept (dept_id),
    CONSTRAINT fk_course_dept FOREIGN KEY (dept_id)
        REFERENCES departments(dept_id) ON UPDATE CASCADE
) ENGINE=InnoDB COMMENT='Course catalogue';

-- ============================================================
-- TABLE: prerequisites (self-referential many-to-many)
-- ============================================================
CREATE TABLE IF NOT EXISTS prerequisites (
    course_id       INT UNSIGNED       NOT NULL COMMENT 'Course that has prereqs',
    prereq_id       INT UNSIGNED       NOT NULL COMMENT 'Required prerequisite course',
    min_grade       CHAR(2)            NOT NULL DEFAULT 'D' COMMENT 'Minimum passing grade',
    PRIMARY KEY (course_id, prereq_id),
    CONSTRAINT fk_prereq_course FOREIGN KEY (course_id)
        REFERENCES courses(course_id) ON DELETE CASCADE,
    CONSTRAINT fk_prereq_prereq FOREIGN KEY (prereq_id)
        REFERENCES courses(course_id) ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='Course prerequisite relationships';

-- ============================================================
-- TABLE: sections
-- ============================================================
CREATE TABLE IF NOT EXISTS sections (
    section_id      INT UNSIGNED       NOT NULL AUTO_INCREMENT,
    course_id       INT UNSIGNED       NOT NULL,
    instructor_id   INT UNSIGNED       NULL,
    section_num     TINYINT UNSIGNED   NOT NULL DEFAULT 1,
    semester        VARCHAR(10)        NOT NULL COMMENT 'e.g. Fall2025',
    schedule_days   SET('M','T','W','R','F','S')
                                       NOT NULL,
    start_time      TIME               NOT NULL,
    end_time        TIME               NOT NULL,
    room            VARCHAR(20)        NULL,
    capacity        TINYINT UNSIGNED   NOT NULL DEFAULT 30,
    enrolled_count  TINYINT UNSIGNED   NOT NULL DEFAULT 0,
    delivery_mode   ENUM('in-person','online','hybrid')
                                       NOT NULL DEFAULT 'in-person',
    status          ENUM('open','closed','cancelled','waitlist')
                                       NOT NULL DEFAULT 'open',
    PRIMARY KEY (section_id),
    UNIQUE KEY uq_section (course_id, section_num, semester),
    KEY idx_section_semester (semester),
    KEY idx_section_instructor (instructor_id),
    CONSTRAINT fk_section_course FOREIGN KEY (course_id)
        REFERENCES courses(course_id) ON UPDATE CASCADE,
    CONSTRAINT fk_section_instructor FOREIGN KEY (instructor_id)
        REFERENCES instructors(instructor_id) ON DELETE SET NULL
) ENGINE=InnoDB COMMENT='Scheduled course sections';

-- ============================================================
-- TABLE: enrollments
-- ============================================================
CREATE TABLE IF NOT EXISTS enrollments (
    enrollment_id   INT UNSIGNED       NOT NULL AUTO_INCREMENT,
    student_id      INT UNSIGNED       NOT NULL,
    section_id      INT UNSIGNED       NOT NULL,
    enrolled_at     DATETIME           NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status          ENUM('enrolled','dropped','withdrawn','waitlisted','completed')
                                       NOT NULL DEFAULT 'enrolled',
    drop_date       DATE               NULL,
    PRIMARY KEY (enrollment_id),
    UNIQUE KEY uq_enrollment (student_id, section_id),
    KEY idx_enrollment_section   (section_id),
    KEY idx_enrollment_student   (student_id),
    KEY idx_enrollment_status    (status),
    KEY idx_enrollment_semester  (section_id, status),
    CONSTRAINT fk_enroll_student FOREIGN KEY (student_id)
        REFERENCES students(student_id) ON UPDATE CASCADE,
    CONSTRAINT fk_enroll_section FOREIGN KEY (section_id)
        REFERENCES sections(section_id) ON UPDATE CASCADE
) ENGINE=InnoDB COMMENT='Student section enrollments';

-- ============================================================
-- TABLE: grades
-- ============================================================
CREATE TABLE IF NOT EXISTS grades (
    grade_id        INT UNSIGNED       NOT NULL AUTO_INCREMENT,
    enrollment_id   INT UNSIGNED       NOT NULL,
    numeric_grade   DECIMAL(5,2)       NULL     COMMENT '0.00 - 100.00',
    letter_grade    CHAR(2)            NULL,
    grade_points    DECIMAL(3,2)       NULL     COMMENT 'GPA points: 4.0 scale',
    graded_at       DATETIME           NULL,
    graded_by       INT UNSIGNED       NULL     COMMENT 'FK -> instructors',
    is_final        TINYINT(1)         NOT NULL DEFAULT 0,
    PRIMARY KEY (grade_id),
    UNIQUE KEY uq_grade_enrollment (enrollment_id),
    KEY idx_grade_instructor (graded_by),
    CONSTRAINT fk_grade_enrollment FOREIGN KEY (enrollment_id)
        REFERENCES enrollments(enrollment_id) ON DELETE CASCADE,
    CONSTRAINT fk_grade_instructor FOREIGN KEY (graded_by)
        REFERENCES instructors(instructor_id) ON DELETE SET NULL,
    CONSTRAINT chk_numeric_grade CHECK (numeric_grade BETWEEN 0.00 AND 100.00)
) ENGINE=InnoDB COMMENT='Grades for enrollments';

-- ============================================================
-- TABLE: audit_log
-- ============================================================
CREATE TABLE IF NOT EXISTS audit_log (
    log_id          BIGINT UNSIGNED    NOT NULL AUTO_INCREMENT,
    event_ts        DATETIME(6)        NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    event_type      VARCHAR(40)        NOT NULL,
    table_name      VARCHAR(64)        NOT NULL,
    record_id       INT UNSIGNED       NULL,
    user_name       VARCHAR(80)        NOT NULL DEFAULT (USER()),
    old_value       JSON               NULL,
    new_value       JSON               NULL,
    ip_address      VARCHAR(45)        NULL,
    PRIMARY KEY (log_id),
    KEY idx_audit_ts    (event_ts),
    KEY idx_audit_table (table_name, event_ts),
    KEY idx_audit_user  (user_name)
) ENGINE=InnoDB COMMENT='Immutable audit trail for sensitive changes';

SET FOREIGN_KEY_CHECKS = 1;
```

---

## 3. Advanced Stored Procedures

### 3.1 sp_enroll_student — With Prerequisites and Conflict Checking

```sql title="sp_enroll_student — full implementation"
DELIMITER $$

DROP PROCEDURE IF EXISTS sp_enroll_student$$
CREATE PROCEDURE sp_enroll_student(
    IN  p_student_id  INT UNSIGNED,
    IN  p_section_id  INT UNSIGNED,
    OUT p_status_code TINYINT,      -- 0=success, 1-n=error codes
    OUT p_message     VARCHAR(255)
)
sp_block: BEGIN
    DECLARE v_enrolled_count  TINYINT UNSIGNED DEFAULT 0;
    DECLARE v_capacity        TINYINT UNSIGNED DEFAULT 0;
    DECLARE v_course_id       INT UNSIGNED;
    DECLARE v_semester        VARCHAR(10);
    DECLARE v_student_status  VARCHAR(20);
    DECLARE v_prereq_id       INT UNSIGNED;
    DECLARE v_prereq_met      TINYINT DEFAULT 0;
    DECLARE v_conflict_count  INT DEFAULT 0;
    DECLARE v_enrollment_id   INT UNSIGNED;
    DECLARE done              INT DEFAULT FALSE;

    -- Cursor: iterate all prerequisites for this course
    DECLARE prereq_cur CURSOR FOR
        SELECT p.prereq_id
        FROM   prerequisites p
        WHERE  p.course_id = v_course_id;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_status_code = 99;
        SET p_message     = 'Unexpected database error — enrollment rolled back';
    END;

    -- ---- Step 1: Validate student is active -----------------
    SELECT enrollment_status INTO v_student_status
    FROM   students
    WHERE  student_id = p_student_id;

    IF v_student_status IS NULL THEN
        SET p_status_code = 1;
        SET p_message = 'Student not found';
        LEAVE sp_block;
    END IF;

    IF v_student_status != 'active' THEN
        SET p_status_code = 2;
        SET p_message = CONCAT('Student status is ', v_student_status,
                               '; must be active to enroll');
        LEAVE sp_block;
    END IF;

    -- ---- Step 2: Get section info ----------------------------
    SELECT s.capacity, s.enrolled_count, s.course_id, s.semester
    INTO   v_capacity, v_enrolled_count, v_course_id, v_semester
    FROM   sections s
    WHERE  s.section_id = p_section_id
      AND  s.status IN ('open', 'waitlist')
    FOR UPDATE;

    IF v_course_id IS NULL THEN
        SET p_status_code = 3;
        SET p_message = 'Section not found or not open for enrollment';
        LEAVE sp_block;
    END IF;

    -- ---- Step 3: Check capacity ------------------------------
    IF v_enrolled_count >= v_capacity THEN
        -- Add to waitlist instead
        INSERT INTO enrollments (student_id, section_id, status)
        VALUES (p_student_id, p_section_id, 'waitlisted')
        ON DUPLICATE KEY UPDATE status = 'waitlisted';

        SET p_status_code = 4;
        SET p_message = 'Section full — added to waitlist';
        LEAVE sp_block;
    END IF;

    -- ---- Step 4: Check prerequisites ------------------------
    OPEN prereq_cur;
    prereq_loop: LOOP
        FETCH prereq_cur INTO v_prereq_id;
        IF done THEN LEAVE prereq_loop; END IF;

        SET v_prereq_met = 0;
        SELECT COUNT(*) INTO v_prereq_met
        FROM   enrollments e
        JOIN   grades      g ON g.enrollment_id = e.enrollment_id
        JOIN   sections    s ON s.section_id    = e.section_id
        WHERE  e.student_id = p_student_id
          AND  s.course_id  = v_prereq_id
          AND  g.is_final   = 1
          AND  g.letter_grade NOT IN ('F','W','I');

        IF v_prereq_met = 0 THEN
            CLOSE prereq_cur;
            SET p_status_code = 5;
            SET p_message = CONCAT('Prerequisite not satisfied: course_id = ',
                                   v_prereq_id);
            LEAVE sp_block;
        END IF;
    END LOOP prereq_loop;
    CLOSE prereq_cur;

    -- ---- Step 5: Check schedule conflicts -------------------
    SELECT COUNT(*) INTO v_conflict_count
    FROM   enrollments  e2
    JOIN   sections     s2 ON s2.section_id = e2.section_id
    JOIN   sections     s1 ON s1.section_id = p_section_id
    WHERE  e2.student_id = p_student_id
      AND  e2.status     = 'enrolled'
      AND  s2.semester   = v_semester
      AND  s2.section_id != p_section_id
      AND  FIND_IN_SET(SUBSTRING_INDEX(s2.schedule_days, ',', 1),
                       s1.schedule_days) > 0
      AND  s2.start_time < s1.end_time
      AND  s2.end_time   > s1.start_time;

    IF v_conflict_count > 0 THEN
        SET p_status_code = 6;
        SET p_message = 'Schedule conflict with an existing enrollment';
        LEAVE sp_block;
    END IF;

    -- ---- Step 6: Perform enrollment -------------------------
    START TRANSACTION;

    INSERT INTO enrollments (student_id, section_id, status)
    VALUES (p_student_id, p_section_id, 'enrolled')
    ON DUPLICATE KEY UPDATE status = 'enrolled', drop_date = NULL;

    SET v_enrollment_id = LAST_INSERT_ID();

    UPDATE sections
    SET    enrolled_count = enrolled_count + 1
    WHERE  section_id = p_section_id;

    -- Create placeholder grade record
    INSERT IGNORE INTO grades (enrollment_id)
    VALUES (v_enrollment_id);

    COMMIT;

    SET p_status_code = 0;
    SET p_message = CONCAT('Successfully enrolled in section ', p_section_id);

END$$
DELIMITER ;
```

### 3.2 sp_calculate_gpa — Per Student, Per Semester

```sql title="sp_calculate_gpa"
DELIMITER $$
DROP PROCEDURE IF EXISTS sp_calculate_gpa$$
CREATE PROCEDURE sp_calculate_gpa(
    IN  p_student_id INT UNSIGNED,
    IN  p_semester   VARCHAR(10),    -- NULL for cumulative
    OUT p_gpa        DECIMAL(4,3),
    OUT p_credits    SMALLINT UNSIGNED
)
BEGIN
    SELECT
        ROUND(
            SUM(g.grade_points * c.credit_hours)
            / NULLIF(SUM(c.credit_hours), 0),
        3) AS gpa,
        SUM(c.credit_hours) AS total_credits
    INTO p_gpa, p_credits
    FROM   enrollments e
    JOIN   grades      g  ON g.enrollment_id = e.enrollment_id
    JOIN   sections    s  ON s.section_id    = e.section_id
    JOIN   courses     c  ON c.course_id     = s.course_id
    WHERE  e.student_id = p_student_id
      AND  e.status     IN ('enrolled', 'completed')
      AND  g.is_final   = 1
      AND  g.grade_points IS NOT NULL
      AND  (p_semester IS NULL OR s.semester = p_semester);

    IF p_gpa IS NULL THEN
        SET p_gpa     = 0.000;
        SET p_credits = 0;
    END IF;

    -- Update students table if cumulative
    IF p_semester IS NULL THEN
        UPDATE students
        SET    gpa          = p_gpa,
               credit_hours = p_credits
        WHERE  student_id   = p_student_id;
    END IF;
END$$
DELIMITER ;
```

### 3.3 sp_generate_transcript — Cursor-Based

```sql title="sp_generate_transcript — cursor iteration"
DELIMITER $$
DROP PROCEDURE IF EXISTS sp_generate_transcript$$
CREATE PROCEDURE sp_generate_transcript(
    IN p_student_id INT UNSIGNED
)
BEGIN
    DECLARE v_semester      VARCHAR(10);
    DECLARE v_course_code   VARCHAR(10);
    DECLARE v_title         VARCHAR(120);
    DECLARE v_credits       TINYINT UNSIGNED;
    DECLARE v_letter        CHAR(2);
    DECLARE v_points        DECIMAL(3,2);
    DECLARE v_sem_gpa       DECIMAL(4,3);
    DECLARE v_sem_credits   SMALLINT;
    DECLARE v_cum_points    DECIMAL(8,3) DEFAULT 0;
    DECLARE v_cum_credits   SMALLINT DEFAULT 0;
    DECLARE done            INT DEFAULT FALSE;

    -- Result set delivered via temp table
    DROP TEMPORARY TABLE IF EXISTS tmp_transcript;
    CREATE TEMPORARY TABLE tmp_transcript (
        semester        VARCHAR(10),
        course_code     VARCHAR(10),
        course_title    VARCHAR(120),
        credit_hours    TINYINT,
        letter_grade    CHAR(2),
        grade_points    DECIMAL(3,2),
        sem_gpa         DECIMAL(4,3),
        cum_gpa         DECIMAL(4,3)
    );

    DECLARE transcript_cur CURSOR FOR
        SELECT  s.semester, c.course_code, c.title,
                c.credit_hours, g.letter_grade, g.grade_points
        FROM    enrollments e
        JOIN    sections    s ON s.section_id    = e.section_id
        JOIN    courses     c ON c.course_id     = s.course_id
        JOIN    grades      g ON g.enrollment_id = e.enrollment_id
        WHERE   e.student_id = p_student_id
          AND   g.is_final   = 1
        ORDER BY s.semester, c.course_code;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    OPEN transcript_cur;
    trans_loop: LOOP
        FETCH transcript_cur INTO v_semester, v_course_code, v_title,
                                  v_credits, v_letter, v_points;
        IF done THEN LEAVE trans_loop; END IF;

        SET v_cum_points  = v_cum_points  + (v_points * v_credits);
        SET v_cum_credits = v_cum_credits + v_credits;

        CALL sp_calculate_gpa(p_student_id, v_semester, v_sem_gpa, v_sem_credits);

        INSERT INTO tmp_transcript VALUES (
            v_semester, v_course_code, v_title, v_credits,
            v_letter, v_points,
            v_sem_gpa,
            ROUND(v_cum_points / NULLIF(v_cum_credits, 0), 3)
        );
    END LOOP;
    CLOSE transcript_cur;

    SELECT * FROM tmp_transcript ORDER BY semester, course_code;
    DROP TEMPORARY TABLE IF EXISTS tmp_transcript;
END$$
DELIMITER ;
```

---

## 4. Trigger Implementations

### 4.1 trg_enforce_capacity — BEFORE INSERT on enrollments

```sql title="Trigger: enforce section capacity"
DELIMITER $$
DROP TRIGGER IF EXISTS trg_enforce_capacity$$
CREATE TRIGGER trg_enforce_capacity
BEFORE INSERT ON enrollments
FOR EACH ROW
BEGIN
    DECLARE v_enrolled  TINYINT UNSIGNED;
    DECLARE v_capacity  TINYINT UNSIGNED;
    DECLARE v_status    VARCHAR(10);

    SELECT enrolled_count, capacity, status
    INTO   v_enrolled, v_capacity, v_status
    FROM   sections
    WHERE  section_id = NEW.section_id;

    IF v_status = 'cancelled' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cannot enroll: section has been cancelled';
    END IF;

    IF v_enrolled >= v_capacity AND NEW.status = 'enrolled' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cannot enroll: section is at capacity';
    END IF;
END$$
DELIMITER ;
```

### 4.2 trg_audit_grade_change — AFTER UPDATE on grades

```sql title="Trigger: audit grade modifications"
DELIMITER $$
DROP TRIGGER IF EXISTS trg_audit_grade_change$$
CREATE TRIGGER trg_audit_grade_change
AFTER UPDATE ON grades
FOR EACH ROW
BEGIN
    -- Only log when numeric_grade or letter_grade actually changes
    IF (OLD.numeric_grade != NEW.numeric_grade
        OR OLD.letter_grade != NEW.letter_grade
        OR OLD.is_final     != NEW.is_final)
    THEN
        INSERT INTO audit_log (
            event_type, table_name, record_id,
            user_name, old_value, new_value
        )
        VALUES (
            'GRADE_CHANGE',
            'grades',
            NEW.grade_id,
            USER(),
            JSON_OBJECT(
                'numeric_grade', OLD.numeric_grade,
                'letter_grade',  OLD.letter_grade,
                'grade_points',  OLD.grade_points,
                'is_final',      OLD.is_final
            ),
            JSON_OBJECT(
                'numeric_grade', NEW.numeric_grade,
                'letter_grade',  NEW.letter_grade,
                'grade_points',  NEW.grade_points,
                'is_final',      NEW.is_final,
                'graded_by',     NEW.graded_by
            )
        );
    END IF;
END$$
DELIMITER ;
```

### 4.3 trg_update_enrollment_count — AFTER UPDATE on enrollments

```sql title="Trigger: sync enrolled_count on status change"
DELIMITER $$
DROP TRIGGER IF EXISTS trg_update_enrollment_count$$
CREATE TRIGGER trg_update_enrollment_count
AFTER UPDATE ON enrollments
FOR EACH ROW
BEGIN
    -- Student dropped: decrement count
    IF OLD.status = 'enrolled' AND NEW.status IN ('dropped','withdrawn') THEN
        UPDATE sections
        SET    enrolled_count = GREATEST(0, enrolled_count - 1),
               status = CASE
                            WHEN enrolled_count - 1 < capacity THEN 'open'
                            ELSE status
                        END
        WHERE  section_id = NEW.section_id;

    -- Student re-enrolled from waitlist or dropped state
    ELSEIF OLD.status != 'enrolled' AND NEW.status = 'enrolled' THEN
        UPDATE sections
        SET    enrolled_count = enrolled_count + 1,
               status = CASE
                            WHEN enrolled_count + 1 >= capacity THEN 'closed'
                            ELSE 'open'
                        END
        WHERE  section_id = NEW.section_id;
    END IF;
END$$
DELIMITER ;
```

---

## 5. User-Defined Functions

```sql title="UDF: fn_letter_grade, fn_student_gpa, fn_credit_hours_completed"
DELIMITER $$

-- ============================================================
-- fn_letter_grade: Convert numeric score to letter grade
-- ============================================================
DROP FUNCTION IF EXISTS fn_letter_grade$$
CREATE FUNCTION fn_letter_grade(p_score DECIMAL(5,2))
RETURNS CHAR(2)
DETERMINISTIC NO SQL
BEGIN
    RETURN CASE
        WHEN p_score >= 93 THEN 'A'
        WHEN p_score >= 90 THEN 'A-'
        WHEN p_score >= 87 THEN 'B+'
        WHEN p_score >= 83 THEN 'B'
        WHEN p_score >= 80 THEN 'B-'
        WHEN p_score >= 77 THEN 'C+'
        WHEN p_score >= 73 THEN 'C'
        WHEN p_score >= 70 THEN 'C-'
        WHEN p_score >= 67 THEN 'D+'
        WHEN p_score >= 60 THEN 'D'
        ELSE 'F'
    END;
END$$

-- ============================================================
-- fn_student_gpa: Calculate current cumulative GPA
-- ============================================================
DROP FUNCTION IF EXISTS fn_student_gpa$$
CREATE FUNCTION fn_student_gpa(p_student_id INT UNSIGNED)
RETURNS DECIMAL(4,3)
READS SQL DATA
BEGIN
    DECLARE v_gpa DECIMAL(4,3) DEFAULT 0.000;

    SELECT ROUND(
               SUM(g.grade_points * c.credit_hours)
               / NULLIF(SUM(c.credit_hours), 0),
           3)
    INTO   v_gpa
    FROM   enrollments e
    JOIN   grades      g ON g.enrollment_id = e.enrollment_id
    JOIN   sections    s ON s.section_id    = e.section_id
    JOIN   courses     c ON c.course_id     = s.course_id
    WHERE  e.student_id = p_student_id
      AND  g.is_final   = 1
      AND  g.grade_points IS NOT NULL;

    RETURN COALESCE(v_gpa, 0.000);
END$$

-- ============================================================
-- fn_credit_hours_completed: Credits earned in a semester
-- ============================================================
DROP FUNCTION IF EXISTS fn_credit_hours_completed$$
CREATE FUNCTION fn_credit_hours_completed(
    p_student_id INT UNSIGNED,
    p_semester   VARCHAR(10)
)
RETURNS SMALLINT UNSIGNED
READS SQL DATA
BEGIN
    DECLARE v_hours SMALLINT UNSIGNED DEFAULT 0;

    SELECT COALESCE(SUM(c.credit_hours), 0) INTO v_hours
    FROM   enrollments e
    JOIN   sections    s ON s.section_id    = e.section_id
    JOIN   courses     c ON c.course_id     = s.course_id
    JOIN   grades      g ON g.enrollment_id = e.enrollment_id
    WHERE  e.student_id = p_student_id
      AND  s.semester   = p_semester
      AND  g.is_final   = 1
      AND  g.letter_grade NOT IN ('F','W','I');

    RETURN v_hours;
END$$

DELIMITER ;
```

---

## 6. Security Implementation

### 6.1 Role-Based Access Control

```sql title="FCRS role-based security model"
-- ============================================================
-- Step 1: Create Roles
-- ============================================================
CREATE ROLE IF NOT EXISTS student_portal;
CREATE ROLE IF NOT EXISTS faculty_role;
CREATE ROLE IF NOT EXISTS registrar_role;
CREATE ROLE IF NOT EXISTS admin_role;

-- ============================================================
-- Step 2: Grant Privileges to Roles
-- ============================================================

-- Student Portal: Read own data + enroll via procedure
GRANT SELECT ON fcrs.courses         TO student_portal;
GRANT SELECT ON fcrs.sections        TO student_portal;
GRANT SELECT ON fcrs.departments     TO student_portal;
GRANT SELECT ON fcrs.prerequisites   TO student_portal;
-- Students can only see their own rows via views (not direct table access)
GRANT SELECT ON fcrs.v_student_transcript   TO student_portal;
GRANT SELECT ON fcrs.v_course_availability  TO student_portal;
GRANT EXECUTE ON PROCEDURE fcrs.sp_enroll_student TO student_portal;
GRANT EXECUTE ON FUNCTION  fcrs.fn_letter_grade   TO student_portal;

-- Faculty Role: Grade entry + view own schedule
GRANT SELECT ON fcrs.courses      TO faculty_role;
GRANT SELECT ON fcrs.sections     TO faculty_role;
GRANT SELECT ON fcrs.enrollments  TO faculty_role;
GRANT SELECT ON fcrs.students     TO faculty_role;
GRANT SELECT, UPDATE (
    numeric_grade, letter_grade, grade_points, graded_at, graded_by, is_final
)                                  ON fcrs.grades TO faculty_role;
GRANT SELECT ON fcrs.v_faculty_schedule   TO faculty_role;
GRANT EXECUTE ON PROCEDURE fcrs.sp_calculate_gpa TO faculty_role;
GRANT EXECUTE ON FUNCTION  fcrs.fn_letter_grade  TO faculty_role;

-- Registrar Role: Full data + enrollment management
GRANT SELECT, INSERT, UPDATE ON fcrs.students     TO registrar_role;
GRANT SELECT, INSERT, UPDATE ON fcrs.enrollments  TO registrar_role;
GRANT SELECT, INSERT, UPDATE ON fcrs.grades       TO registrar_role;
GRANT SELECT, INSERT, UPDATE ON fcrs.sections     TO registrar_role;
GRANT SELECT ON fcrs.audit_log                    TO registrar_role;
GRANT SELECT ON fcrs.v_student_transcript         TO registrar_role;
GRANT SELECT ON fcrs.v_department_stats           TO registrar_role;
GRANT EXECUTE ON PROCEDURE fcrs.sp_enroll_student    TO registrar_role;
GRANT EXECUTE ON PROCEDURE fcrs.sp_generate_transcript TO registrar_role;
GRANT EXECUTE ON PROCEDURE fcrs.sp_calculate_gpa     TO registrar_role;

-- Admin Role: Full schema access
GRANT ALL PRIVILEGES ON fcrs.* TO admin_role;

-- ============================================================
-- Step 3: Create Application Users and Assign Roles
-- ============================================================
CREATE USER IF NOT EXISTS 'portal_app'@'10.0.1.%'
    IDENTIFIED WITH caching_sha2_password BY 'Portal@2025!Secure'
    REQUIRE SSL
    WITH MAX_USER_CONNECTIONS 200;
GRANT student_portal TO 'portal_app'@'10.0.1.%';
SET DEFAULT ROLE student_portal FOR 'portal_app'@'10.0.1.%';

CREATE USER IF NOT EXISTS 'faculty_app'@'10.0.1.%'
    IDENTIFIED WITH caching_sha2_password BY 'Faculty@2025!Secure'
    REQUIRE SSL;
GRANT faculty_role TO 'faculty_app'@'10.0.1.%';
SET DEFAULT ROLE faculty_role FOR 'faculty_app'@'10.0.1.%';

CREATE USER IF NOT EXISTS 'registrar_app'@'10.0.0.%'
    IDENTIFIED WITH caching_sha2_password BY 'Registrar@2025!Secure'
    REQUIRE SSL;
GRANT registrar_role TO 'registrar_app'@'10.0.0.%';
SET DEFAULT ROLE registrar_role FOR 'registrar_app'@'10.0.0.%';
```

---

## 7. View Definitions

```sql title="FCRS views"
-- ============================================================
-- v_student_transcript
-- ============================================================
CREATE OR REPLACE VIEW v_student_transcript AS
SELECT
    s.student_id,
    s.fsuid,
    CONCAT(s.first_name, ' ', s.last_name)  AS student_name,
    sec.semester,
    c.course_code,
    c.title                                  AS course_title,
    c.credit_hours,
    g.numeric_grade,
    g.letter_grade,
    g.grade_points,
    g.is_final,
    i.last_name                              AS instructor_last
FROM students    s
JOIN enrollments e   ON e.student_id    = s.student_id
JOIN sections    sec ON sec.section_id  = e.section_id
JOIN courses     c   ON c.course_id     = sec.course_id
LEFT JOIN grades g   ON g.enrollment_id = e.enrollment_id
LEFT JOIN instructors i ON i.instructor_id = sec.instructor_id
WHERE  e.status IN ('enrolled','completed');

-- ============================================================
-- v_course_availability
-- ============================================================
CREATE OR REPLACE VIEW v_course_availability AS
SELECT
    sec.section_id,
    c.course_code,
    c.title,
    c.credit_hours,
    sec.semester,
    sec.section_num,
    sec.schedule_days,
    SEC_TO_TIME(TIME_TO_SEC(sec.start_time)) AS start_time,
    SEC_TO_TIME(TIME_TO_SEC(sec.end_time))   AS end_time,
    sec.room,
    sec.delivery_mode,
    sec.capacity,
    sec.enrolled_count,
    sec.capacity - sec.enrolled_count        AS seats_available,
    sec.status,
    CONCAT(i.first_name, ' ', i.last_name)   AS instructor_name
FROM sections   sec
JOIN courses    c ON c.course_id      = sec.course_id
LEFT JOIN instructors i ON i.instructor_id = sec.instructor_id
WHERE  sec.status != 'cancelled';

-- ============================================================
-- v_faculty_schedule
-- ============================================================
CREATE OR REPLACE VIEW v_faculty_schedule AS
SELECT
    i.instructor_id,
    CONCAT(i.first_name, ' ', i.last_name) AS instructor_name,
    i.email,
    d.dept_name,
    sec.semester,
    c.course_code,
    c.title,
    sec.section_num,
    sec.schedule_days,
    sec.start_time,
    sec.end_time,
    sec.room,
    sec.enrolled_count,
    sec.capacity,
    sec.delivery_mode
FROM instructors i
JOIN departments d   ON d.dept_id      = i.dept_id
JOIN sections    sec ON sec.instructor_id = i.instructor_id
JOIN courses     c   ON c.course_id    = sec.course_id
WHERE sec.status != 'cancelled';

-- ============================================================
-- v_department_stats
-- ============================================================
CREATE OR REPLACE VIEW v_department_stats AS
SELECT
    d.dept_id,
    d.dept_code,
    d.dept_name,
    COUNT(DISTINCT s.student_id)    AS declared_majors,
    COUNT(DISTINCT c.course_id)     AS active_courses,
    COUNT(DISTINCT i.instructor_id) AS instructors,
    ROUND(AVG(s.gpa), 3)            AS avg_student_gpa,
    SUM(CASE WHEN s.enrollment_status = 'active' THEN 1 ELSE 0 END) AS active_students
FROM   departments d
LEFT JOIN students     s ON s.dept_id = d.dept_id
LEFT JOIN courses      c ON c.dept_id = d.dept_id AND c.is_active = 1
LEFT JOIN instructors  i ON i.dept_id = d.dept_id AND i.is_active = 1
GROUP BY d.dept_id, d.dept_code, d.dept_name;
```

---

## 8. Index Strategy

### 8.1 Index Design and Justification

Every index carries a cost (write overhead, storage). Each must be justified by a concrete query pattern:

```sql title="FCRS index strategy with EXPLAIN justification"
-- INDEX 1: Enrollment lookup by student + status
-- Query: "Show all active enrollments for student 1001"
-- EXPLAIN without index: type=ALL (full scan on enrollments)
-- EXPLAIN with index: type=ref, rows=~8 (student's enrollments only)
CREATE INDEX idx_enroll_student_status ON enrollments (student_id, status);

-- INDEX 2: Section search by semester
-- Query: "Find all open sections in Fall2025"
-- Without: full scan of sections. With: range scan on semester column.
CREATE INDEX idx_section_semester_status ON sections (semester, status);

-- INDEX 3: Course search by department and level
-- Query: "List all 400-level ITEC courses"
-- Composite index matches both conditions in WHERE clause.
CREATE INDEX idx_course_dept_level ON courses (dept_id, level, is_active);

-- INDEX 4: Grade lookup for GPA calculation
-- Query: sp_calculate_gpa joins grades on enrollment_id; verify is_final
CREATE INDEX idx_grade_enrollment_final ON grades (enrollment_id, is_final);

-- INDEX 5: Audit log time-range queries
-- Query: "Show all grade changes in the last 30 days"
-- Already has idx_audit_ts in schema DDL — verify with EXPLAIN
EXPLAIN SELECT * FROM audit_log
WHERE event_type = 'GRADE_CHANGE'
  AND event_ts   >= NOW() - INTERVAL 30 DAY;
-- Uses idx_audit_table (table_name, event_ts) composite — efficient

-- INDEX 6: Full-text search on course titles and descriptions
-- Query: "Search courses containing 'database'"
ALTER TABLE courses ADD FULLTEXT INDEX ft_course_search (title, description);

-- ---- Verify index usage with EXPLAIN -----------------------
EXPLAIN
SELECT s.fsuid, s.first_name, s.last_name,
       sec.semester, c.course_code, g.letter_grade
FROM   enrollments e
JOIN   students    s   ON s.student_id   = e.student_id
JOIN   sections    sec ON sec.section_id = e.section_id
JOIN   courses     c   ON c.course_id    = sec.course_id
LEFT JOIN grades   g   ON g.enrollment_id = e.enrollment_id
WHERE  e.student_id = 1001
  AND  e.status     = 'enrolled'\G
-- Expected: ALL indexes used; no full scans; rows estimates < 50
```

---

## 9. Import/Export Scripts

### 9.1 Python CSV Enrollment Importer with Validation

```python title="import_enrollments.py"
#!/usr/bin/env python3
"""
import_enrollments.py
Import enrollment records from CSV into FCRS database.
Validates every row before inserting; reports errors with row numbers.

CSV format: student_fsuid,course_code,section_num,semester
"""
import csv
import sys
import logging
import mysql.connector
from mysql.connector import Error
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(f"import_{datetime.now():%Y%m%d_%H%M%S}.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

DB_CONFIG = {
    "host":     "127.0.0.1",
    "database": "fcrs",
    "user":     "import_user",
    "password": "import_pass",
    "charset":  "utf8mb4",
    "autocommit": False,
}

@dataclass
class ImportStats:
    total:   int = 0
    success: int = 0
    skipped: int = 0
    errors:  list = field(default_factory=list)


def validate_row(row: dict, row_num: int) -> list[str]:
    """Return list of validation error messages (empty = valid)."""
    errors = []
    if not row.get("student_fsuid", "").strip():
        errors.append(f"Row {row_num}: missing student_fsuid")
    elif not row["student_fsuid"].startswith("B") or len(row["student_fsuid"]) != 9:
        errors.append(f"Row {row_num}: invalid FSUID format '{row['student_fsuid']}'")

    if not row.get("course_code", "").strip():
        errors.append(f"Row {row_num}: missing course_code")

    if not row.get("section_num", "").strip().isdigit():
        errors.append(f"Row {row_num}: section_num must be numeric")

    semester = row.get("semester", "").strip()
    valid_terms = ("Fall", "Spring", "Summer")
    if not any(semester.startswith(t) for t in valid_terms):
        errors.append(f"Row {row_num}: invalid semester '{semester}'")

    return errors


def import_csv(filepath: str) -> ImportStats:
    stats = ImportStats()
    conn  = None

    try:
        conn   = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        # Lookup helpers
        cursor.execute("SELECT student_id, fsuid FROM students")
        fsuid_map = {r["fsuid"]: r["student_id"] for r in cursor.fetchall()}

        cursor.execute("""
            SELECT sec.section_id, c.course_code, sec.section_num, sec.semester
            FROM   sections sec JOIN courses c ON c.course_id = sec.course_id
        """)
        section_map = {
            (r["course_code"], str(r["section_num"]), r["semester"]): r["section_id"]
            for r in cursor.fetchall()
        }

        with open(filepath, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, start=2):
                stats.total += 1

                # Validation
                row_errors = validate_row(row, row_num)
                if row_errors:
                    stats.errors.extend(row_errors)
                    stats.skipped += 1
                    continue

                fsuid       = row["student_fsuid"].strip()
                course_code = row["course_code"].strip().upper()
                section_num = row["section_num"].strip()
                semester    = row["semester"].strip()

                student_id = fsuid_map.get(fsuid)
                if not student_id:
                    stats.errors.append(f"Row {row_num}: student not found: {fsuid}")
                    stats.skipped += 1
                    continue

                section_id = section_map.get((course_code, section_num, semester))
                if not section_id:
                    stats.errors.append(
                        f"Row {row_num}: section not found: "
                        f"{course_code} S{section_num} {semester}"
                    )
                    stats.skipped += 1
                    continue

                # Call stored procedure
                try:
                    cursor.callproc("sp_enroll_student",
                                    [student_id, section_id, 0, ""])
                    for res in cursor.stored_results():
                        pass  # consume result sets
                    conn.commit()
                    stats.success += 1
                    logger.info("Enrolled %s in %s S%s %s",
                                fsuid, course_code, section_num, semester)

                except Error as exc:
                    conn.rollback()
                    stats.errors.append(f"Row {row_num}: DB error — {exc}")
                    stats.skipped += 1

    except Error as exc:
        logger.error("Connection error: %s", exc)
        sys.exit(1)
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

    return stats


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python import_enrollments.py <enrollments.csv>")
        sys.exit(1)

    csv_path = sys.argv[1]
    if not Path(csv_path).exists():
        logger.error("File not found: %s", csv_path)
        sys.exit(1)

    stats = import_csv(csv_path)
    logger.info("=" * 50)
    logger.info("Import complete: %d total, %d enrolled, %d skipped",
                stats.total, stats.success, stats.skipped)
    if stats.errors:
        logger.warning("Errors encountered:")
        for err in stats.errors:
            logger.warning("  %s", err)
    sys.exit(0 if not stats.errors else 1)
```

### 9.2 Automated mysqldump Backup Script

```bash title="fcrs_backup.sh"
#!/usr/bin/env bash
set -euo pipefail
readonly DB_NAME="fcrs"
readonly BACKUP_DIR="/var/backups/mysql/fcrs"
readonly TS=$(date +%Y%m%d_%H%M%S)
readonly FILE="${BACKUP_DIR}/fcrs_${TS}.sql.gz"
mkdir -p "$BACKUP_DIR"
mysqldump \
  --defaults-file=/etc/mysql/backup.cnf \
  --single-transaction --flush-logs --master-data=2 \
  --routines --triggers --events --add-drop-table \
  "$DB_NAME" | gzip -9 > "$FILE"
echo "Backup: $FILE ($(du -sh "$FILE" | cut -f1))"
# Keep 7 days
ls -1t "${BACKUP_DIR}/"*.sql.gz | tail -n +8 | xargs -r rm -f
```

---

## 10. Event Scheduler — Nightly and Semester-End Automation

```sql title="FCRS scheduled events"
DELIMITER $$

-- ============================================================
-- e_nightly_waitlist_processing
-- Promotes waitlisted students if a seat opened (due to drops)
-- ============================================================
DROP EVENT IF EXISTS e_nightly_waitlist_processing$$
CREATE EVENT e_nightly_waitlist_processing
ON SCHEDULE EVERY 1 DAY
STARTS TIMESTAMP(CURRENT_DATE, '23:00:00')
ON COMPLETION PRESERVE ENABLE
DO
BEGIN
    DECLARE v_student_id  INT UNSIGNED;
    DECLARE v_section_id  INT UNSIGNED;
    DECLARE v_enroll_id   INT UNSIGNED;
    DECLARE v_seats_free  INT DEFAULT 0;
    DECLARE done          INT DEFAULT FALSE;

    DECLARE waitlist_cur CURSOR FOR
        SELECT e.student_id, e.section_id, e.enrollment_id
        FROM   enrollments e
        JOIN   sections    s ON s.section_id = e.section_id
        WHERE  e.status    = 'waitlisted'
          AND  s.enrolled_count < s.capacity
        ORDER  BY e.enrolled_at   -- FIFO
        LIMIT  100;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    OPEN waitlist_cur;
    wl_loop: LOOP
        FETCH waitlist_cur INTO v_student_id, v_section_id, v_enroll_id;
        IF done THEN LEAVE wl_loop; END IF;

        UPDATE enrollments
        SET    status = 'enrolled'
        WHERE  enrollment_id = v_enroll_id;

        INSERT INTO audit_log (event_type, table_name, record_id, user_name)
        VALUES ('WAITLIST_PROMOTED', 'enrollments', v_enroll_id, 'EVENT_SCHEDULER');
    END LOOP;
    CLOSE waitlist_cur;
END$$

-- ============================================================
-- e_semester_end_grade_finalization
-- Runs at end of each semester to finalise GPA calculations
-- ============================================================
DROP EVENT IF EXISTS e_semester_end_grade_finalization$$
CREATE EVENT e_semester_end_grade_finalization
ON SCHEDULE
    AT '2025-12-20 06:00:00'
ON COMPLETION PRESERVE ENABLE
DO
BEGIN
    DECLARE v_student_id INT UNSIGNED;
    DECLARE done INT DEFAULT FALSE;

    DECLARE student_cur CURSOR FOR
        SELECT DISTINCT e.student_id
        FROM   enrollments e
        JOIN   sections    s ON s.section_id = e.section_id
        WHERE  s.semester   = 'Fall2025'
          AND  e.status     = 'enrolled';

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    OPEN student_cur;
    stu_loop: LOOP
        FETCH student_cur INTO v_student_id;
        IF done THEN LEAVE stu_loop; END IF;

        -- Update enrollment status to completed
        UPDATE enrollments e
        JOIN   sections    s ON s.section_id = e.section_id
        SET    e.status    = 'completed'
        WHERE  e.student_id = v_student_id
          AND  s.semester   = 'Fall2025'
          AND  e.status     = 'enrolled';

        -- Recalculate GPA
        UPDATE students
        SET    gpa = fn_student_gpa(v_student_id)
        WHERE  student_id = v_student_id;
    END LOOP;
    CLOSE student_cur;

    INSERT INTO audit_log (event_type, table_name, user_name)
    VALUES ('SEMESTER_END_FINALIZATION', 'enrollments', 'EVENT_SCHEDULER');
END$$

DELIMITER ;
```

---

## 11. Monitoring — Health Check Stored Procedure

```sql title="sp_database_health_check — comprehensive"
DELIMITER $$
DROP PROCEDURE IF EXISTS sp_database_health_check$$
CREATE PROCEDURE sp_database_health_check()
BEGIN
    -- ---- 1. Buffer pool hit rate ---------------------------
    SELECT 'Buffer Pool Hit Rate %' AS metric,
        ROUND(100 * (1 - (
            (SELECT VARIABLE_VALUE FROM performance_schema.global_status
             WHERE VARIABLE_NAME = 'Innodb_buffer_pool_reads')
            /
            NULLIF((SELECT VARIABLE_VALUE FROM performance_schema.global_status
             WHERE VARIABLE_NAME = 'Innodb_buffer_pool_read_requests'), 0)
        )), 2) AS value;

    -- ---- 2. Active connections vs limit ---------------------
    SELECT 'Connections Used %' AS metric,
        ROUND(100 *
            (SELECT VARIABLE_VALUE FROM performance_schema.global_status
             WHERE VARIABLE_NAME = 'Threads_connected')
            /
            NULLIF(@@max_connections, 0),
        1) AS value;

    -- ---- 3. Slow queries (last hour) -----------------------
    SELECT 'Slow Queries (last 1hr)' AS metric,
        COUNT(*) AS value
    FROM   performance_schema.events_statements_history_long
    WHERE  TIMER_WAIT > 1000000000000;   -- > 1 second in picoseconds

    -- ---- 4. Long-running transactions ----------------------
    SELECT 'Long Transactions (> 5min)' AS metric,
        COUNT(*) AS value
    FROM information_schema.INNODB_TRX
    WHERE trx_started < NOW() - INTERVAL 5 MINUTE;

    -- ---- 5. Replication lag (if replica) -------------------
    SELECT 'Replication Lag (s)' AS metric,
        IFNULL(
            (SELECT VARIABLE_VALUE FROM performance_schema.global_status
             WHERE VARIABLE_NAME = 'Seconds_Behind_Source'),
            'N/A (not a replica)'
        ) AS value;

    -- ---- 6. Table fragmentation ----------------------------
    SELECT 'Fragmented Tables (>10% free)' AS metric,
        COUNT(*) AS value
    FROM information_schema.TABLES
    WHERE TABLE_SCHEMA = 'fcrs'
      AND DATA_FREE > DATA_LENGTH * 0.10
      AND ENGINE      = 'InnoDB';

    -- ---- 7. Deadlock count (since last restart) ------------
    SELECT 'Deadlocks Since Restart' AS metric,
        VARIABLE_VALUE AS value
    FROM performance_schema.global_status
    WHERE VARIABLE_NAME = 'Innodb_deadlocks';
END$$
DELIMITER ;

-- Run the health check
CALL sp_database_health_check();
```

---

## 12. Project Rubric

| Criterion | Weight | Excellent (90–100%) | Good (75–89%) | Needs Work (< 75%) |
|-----------|--------|---------------------|--------------|-------------------|
| **Schema Design** | 20% | All 8+ tables; correct PK/FK; appropriate data types; CHECK constraints; 3NF verified | 6–7 tables; minor FK omissions; data types mostly correct | < 6 tables; missing foreign keys; redundant data; denormalisation without justification |
| **Stored Procedures** | 20% | All 3 procedures; cursor iteration; error handling with SIGNAL; transaction management; edge cases tested | 2 procedures; basic error handling; transactions used | 1 procedure; no error handling; no transactions |
| **Triggers** | 15% | All 3 triggers; BEFORE and AFTER; correct SIGNAL in BEFORE; JSON audit log in AFTER | 2 triggers; correct logic; minor audit gaps | 1 trigger or incorrect trigger logic |
| **Functions** | 10% | All 3 functions; DETERMINISTIC declared correctly; used in views and procedures | 2 functions; used independently | 1 function; not integrated |
| **Security** | 10% | 4 roles; granular per-column GRANT; SSL required; MAX_USER_CONNECTIONS; DEFINER clauses reviewed | 3 roles; mostly correct grants; SSL optional | < 3 roles; overly broad grants (e.g., ALL on schema) |
| **Views** | 10% | All 4 views; used in security layer; tested with JOIN performance; no SELECT * | 3 views; functionally correct | < 3 views or views expose raw tables |
| **Indexing** | 10% | Every index justified with EXPLAIN output; no redundant indexes; full-text where appropriate | Indexes present; some unjustified; EXPLAIN used selectively | Indexes missing on FK columns; no EXPLAIN analysis |
| **Scripting & Automation** | 5% | Python importer with row-level validation; error report; backup script with retention; events tested | Python importer runs; backup script works; events defined | Import script only; no validation; no automation |
| **Documentation** | ___ | Schema diagram; procedure descriptions; security matrix; test queries with expected output | Schema diagram and key descriptions | Minimal or missing documentation |

---

## 13. Final Synthesis — Connecting 15 Weeks

### 13.1 The Complete Picture

Every topic in ITEC 445 forms one layer of a production database system. Here is how they connect:

```
WEEK  1-2:  Relational theory, normalisation, ER modelling
             ↓ Foundation for all schema design decisions

WEEK  3-4:  Advanced SQL — JOINs, subqueries, window functions
             ↓ Powers views, stored procedures, reporting

WEEK  5-6:  Stored procedures, functions, cursors, error handling
             ↓ Encapsulates business logic in the database

WEEK  7-8:  Triggers, events
             ↓ Automated enforcement and audit trail

WEEK  9-10: Security — users, roles, privileges, SSL
             ↓ Protects data; enables least-privilege access

WEEK 11:    Scripting & Automation
             ↓ Bridges DB and OS; enables DevOps practices

WEEK 12:    Backup, Recovery, Replication, HA
             ↓ Ensures data durability and service continuity

WEEK 13:    Monitoring & Performance Tuning
             ↓ Keeps the system fast and observable in production

WEEK 14:    NoSQL, NewSQL, Cloud
             ↓ Enables right-tool-for-right-job architecture

WEEK 15:    Capstone — integrates everything into a real system
```

### 13.2 Career Paths in Database Engineering

=== "Database Administrator"

    **Database Administrator (DBA)**
    
    The DBA owns the health, performance, security, and availability of the database server itself. This is the most operationally intensive database role.
    
    | Skill Area | ITEC 445 Coverage |
    |-----------|------------------|
    | Backup & Recovery | Week 12 — mysqldump, XtraBackup, PITR |
    | Replication & HA | Week 12 — GTID replication, InnoDB Cluster |
    | Performance Tuning | Week 13 — Performance Schema, buffer pool, deadlocks |
    | Security | Weeks 9–10, Week 15 — roles, SSL, audit |
    | Automation | Week 11 — scripting, Event Scheduler |
    
    **Typical tools:** MySQL, Percona XtraBackup, PMM, ProxySQL, Ansible  
    **Entry salary range (US):** $75,000–$110,000

=== "Database Developer"

    **Database Developer / SQL Developer**
    
    Focused on the application-facing database layer: schema design, stored procedures, views, and query optimisation.
    
    | Skill Area | ITEC 445 Coverage |
    |-----------|------------------|
    | Schema Design | Weeks 1–2, Week 15 capstone |
    | Stored Procedures | Weeks 5–6, Week 15 |
    | Triggers & Events | Weeks 7–8, Week 15 |
    | Indexing | Weeks 9–10, Week 15 |
    | Migration Tooling | Week 11 — Flyway, Liquibase |
    
    **Typical tools:** MySQL Workbench, DBeaver, Git, Flyway, Visual Studio Code  
    **Entry salary range (US):** $70,000–$100,000

=== "Data Engineer"

    **Data Engineer**
    
    Builds and maintains the pipelines that move, transform, and land data for analytics and machine learning.
    
    | Skill Area | ITEC 445 Coverage |
    |-----------|------------------|
    | Python + SQL scripting | Week 11 — mysql-connector, SQLAlchemy |
    | ETL / CSV import | Week 15 — Python importer with validation |
    | Cloud databases | Week 14 — AWS, GCP, Azure |
    | NoSQL systems | Week 14 — MongoDB, Redis |
    | Schema modelling | Weeks 1–2 (relational) + Week 14 (document) |
    
    **Typical tools:** Python, dbt, Apache Airflow, Spark, Kafka, Redshift  
    **Entry salary range (US):** $85,000–$125,000

=== "Cloud / SRE"

    **Cloud Database Engineer / Site Reliability Engineer (SRE)**
    
    Operates database infrastructure at cloud scale; combines DBA skills with DevOps and infrastructure-as-code expertise.
    
    | Skill Area | ITEC 445 Coverage |
    |-----------|------------------|
    | Cloud managed databases | Week 14 — RDS, Aurora, DynamoDB, Cloud SQL |
    | HA & failover | Week 12 — InnoDB Cluster, Multi-AZ |
    | Monitoring & alerting | Week 11 (health scripts), Week 13 (PMM, Prometheus) |
    | Automation & scripting | Week 11 — bash, Python, event scheduler |
    | Performance | Week 13 — tuning, OS-level optimisation |
    
    **Typical tools:** AWS/GCP/Azure, Terraform, Ansible, Prometheus, Grafana, PagerDuty  
    **Entry salary range (US):** $90,000–$135,000

!!! tip "Career Advice from the Database World"
    The most impactful database engineers are those who can communicate across boundaries — they speak SQL to developers, explain I/O patterns to sysadmins, and translate business requirements into schema decisions. Your SQL is a tool; your judgment is the skill.

---

## Key Vocabulary

| Term | Definition |
|------|-----------|
| **Capstone** | Integrative final project demonstrating mastery of all course objectives |
| **Normalisation** | Formal process of organising schema to reduce redundancy and dependency anomalies |
| **`SIGNAL SQLSTATE`** | MySQL statement to raise a user-defined error from a stored procedure or trigger |
| **`LEAVE`** | MySQL statement to exit a labelled loop or BEGIN…END block |
| **Cursor** | Server-side iterator over a result set, used in stored procedures |
| **BEFORE trigger** | Executes before the DML statement; can modify NEW row or cancel via SIGNAL |
| **AFTER trigger** | Executes after the DML statement succeeds; used for auditing side effects |
| **`DETERMINISTIC`** | Function attribute declaring output depends only on inputs (same inputs → same output) |
| **`READS SQL DATA`** | Function attribute declaring it reads data but does not modify it |
| **Role** | Named collection of privileges that can be assigned to users |
| **`REQUIRE SSL`** | User creation clause requiring encrypted connections |
| **`DEFINER`** | MySQL user whose security context is used when executing a stored object |
| **Generated column** | Column whose value is computed from an expression, optionally indexed |
| **`FULLTEXT` index** | Specialised MySQL index for efficient text search on VARCHAR/TEXT columns |
| **`ON COMPLETION PRESERVE`** | Event clause keeping a one-time event after it fires |
| **ETL** | Extract, Transform, Load — process of moving data between systems |
| **`arrayFilters`** | MongoDB update option for matching specific elements in an array |
| **RPO** | Recovery Point Objective — maximum acceptable data loss in time |
| **RTO** | Recovery Time Objective — maximum acceptable time to restore service |
| **Polyglot persistence** | Using multiple specialised databases within one application architecture |

---

## Self-Assessment

!!! question "Self-Assessment — Week 15 (Capstone)"

    **Question 1.** The `trg_enforce_capacity` trigger raises a SIGNAL to block an INSERT when the section is full. However, `sp_enroll_student` also checks capacity before inserting. Explain why both checks are necessary, and describe a race condition that the stored procedure check alone (without the trigger) would fail to prevent in a concurrent environment.

    **Question 2.** Review the `sp_generate_transcript` procedure. It calls `sp_calculate_gpa` inside a cursor loop — one call per semester. Identify the N+1 query problem this creates, estimate the performance impact for a student with 8 semesters, and rewrite the relevant section to eliminate the N+1 calls without changing the procedure's output.

    **Question 3.** The `registrar_role` is granted `SELECT, INSERT, UPDATE` on `enrollments` directly (not only via the stored procedure). Explain the security implication of this direct table grant, design a tighter privilege model that preserves registrar functionality without direct DML on enrollments, and describe how `SQL SECURITY DEFINER` on the stored procedure supports this model.

    **Question 4.** Your EXPLAIN output for the enrollment search query shows `type=ALL` on the `grades` table despite the `idx_grade_enrollment_final` composite index existing. List three reasons MySQL might ignore a composite index, and describe how you would diagnose which reason applies in this case.

    **Question 5.** You are presenting the FCRS architecture to the FSU IT steering committee. A committee member asks: "Why not just put all this data in MongoDB? It's more flexible." Write a 4–6 sentence technical argument for the relational model in the context of a course registration system, acknowledging one specific use case where adding MongoDB (in a polyglot architecture) would be justified.

---

## Further Reading

- [MySQL 8.0 Stored Programs](https://dev.mysql.com/doc/refman/8.0/en/stored-programs-views.html)
- [MySQL 8.0 Triggers](https://dev.mysql.com/doc/refman/8.0/en/triggers.html)
- [MySQL 8.0 Role-Based Access Control](https://dev.mysql.com/doc/refman/8.0/en/roles.html)
- [Percona Toolkit Documentation](https://docs.percona.com/percona-toolkit/)
- [Use The Index, Luke — SQL Indexing for Developers](https://use-the-index-luke.com/)
- Schwartz, Baron et al. *High Performance MySQL, 4th Ed.* — Chapter 6 (Schema Design)
- Kleppmann, Martin. *Designing Data-Intensive Applications* — Chapters 1–2 (Foundations)
- [Database Reliability Engineering (O'Reilly)](https://www.oreilly.com/library/view/database-reliability-engineering/9781491925935/)
- [MySQL Certification Study Guide](https://www.oracle.com/mysql/technologies/mysqlce.html)

---

## A Closing Note to Students

You have spent fifteen weeks building skills that most developers spend years accumulating through trial and error in production. You understand not just *how* to write SQL, but *why* an index makes a query fast, *what* happens inside InnoDB when you commit a transaction, and *how* to keep a database running reliably at 3 AM when things go wrong.

The database is the memory of every application that matters — the place where a hospital stores patient records, where a university records a student's achievement, where a business processes its transactions. The work of a database engineer is quiet, unglamorous, and absolutely essential.

Carry that responsibility seriously. Write code that future colleagues can read. Design schemas that survive requirements changes. Build systems that fail gracefully. And always, always test your backups.

Good luck on your capstone projects. — *Dr. Chen*

---

[← Week 14](week14.md) | [Course Index](index.md)
