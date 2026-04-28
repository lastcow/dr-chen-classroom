---
title: "Lab 03: SQL Injection — Vulnerable vs Secure Implementation"
course: SCIA-340
topic: SQL Security and SQL Injection
week: 3
difficulty: ⭐⭐⭐
estimated_time: 75 minutes
---

# Lab 03: SQL Injection — Vulnerable vs Secure Implementation

| Field | Details |
|---|---|
| **Course** | SCIA-340 — Database Security |
| **Week** | 3 |
| **Difficulty** | ⭐⭐⭐ Intermediate |
| **Estimated Time** | 75 minutes |
| **Topic** | SQL Security and SQL Injection |
| **Prerequisites** | Labs 01–02 complete; understanding of basic PL/pgSQL syntax |
| **Deliverables** | Screenshots at each checkpoint + verification script output + secure search function |

---

## Overview

SQL injection remains the #1 database attack vector in the OWASP Top 10. In this lab you will:

1. Build a realistic application database with users and products.
2. Write a **vulnerable** login function that uses string concatenation.
3. **Exploit** it — demonstrating authentication bypass and UNION-based data extraction.
4. Rewrite it **securely** using parameterized queries and prove the injection fails.
5. Encounter **second-order SQL injection** — the harder-to-find variant.

The act of exploiting your own vulnerable code before fixing it creates lasting intuition about why parameterized queries are non-negotiable.

---

!!! warning "Branch Requirement"
    All SQL must be executed on your Neon branch. **Name your branch `lab-03` before starting.**
    This lab creates schemas and functions — running on the wrong branch will cause the verification script to fail.

!!! info "Neon Setup — How to Connect"
    1. Log in to [https://neon.tech](https://neon.tech) and select your **`lab-03`** branch.
    2. Copy the connection string from **Dashboard → Connection Details**.
    3. Connect:
       ```bash
       export DATABASE_URL="postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/scia340?sslmode=require"
       psql $DATABASE_URL
       ```
       ```
       \c scia340
       ```

---

## Part 1 — Build the Target Database

### Step 1.1 — Create Schema and Tables

We create a realistic application schema with a `users` table and a `products` table that contains a sensitive column (`internal_cost`) that should **never** be exposed to end users.

```sql
CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE app.users (
  id            SERIAL PRIMARY KEY,
  username      TEXT NOT NULL UNIQUE,
  email         TEXT NOT NULL,
  role          TEXT NOT NULL DEFAULT 'user'
                  CHECK (role IN ('user','admin','superadmin')),
  password_hash TEXT NOT NULL
);

CREATE TABLE app.products (
  id            SERIAL PRIMARY KEY,
  name          TEXT NOT NULL,
  price         NUMERIC(10,2) NOT NULL,
  internal_cost NUMERIC(10,2)   -- SENSITIVE: must never be exposed via API
);

INSERT INTO app.users (username, email, role, password_hash) VALUES
  ('alice',  'alice@corp.com',  'user',       'hash_alice'),
  ('bob',    'bob@corp.com',    'admin',      'hash_bob'),
  ('eve',    'eve@corp.com',    'user',       'hash_eve'),
  ('sysadm', 'admin@corp.com',  'superadmin', 'hash_sysadm');

INSERT INTO app.products (name, price, internal_cost) VALUES
  ('Widget A', 29.99,  4.50),
  ('Widget B', 49.99,  8.20),
  ('Gadget X', 99.99, 22.00);
```

Verify the data loaded correctly:

```sql
SELECT * FROM app.users;
SELECT * FROM app.products;
```

---

## Part 2 — Vulnerable Function

### Step 2.1 — Build the Vulnerable Login Function

This function simulates how many older applications authenticate users: by building a SQL string through concatenation. **This is the wrong way to do it.**

```sql
CREATE OR REPLACE FUNCTION app.login_vulnerable(
  p_username TEXT,
  p_password TEXT
) RETURNS TEXT AS $$
DECLARE
  v_result TEXT;
BEGIN
  -- VULNERABLE: user input concatenated directly into SQL string
  EXECUTE
    'SELECT username FROM app.users WHERE username = ''' || p_username ||
    ''' AND password_hash = ''' || p_password || ''''
  INTO v_result;

  RETURN COALESCE(v_result, 'Login failed');
END;
$$ LANGUAGE plpgsql;
```

---

### Step 2.2 — Normal Usage Works

Confirm the function behaves correctly with legitimate input:

```sql
SELECT app.login_vulnerable('alice', 'hash_alice');
```

**Expected:** `alice`

---

### Step 2.3 — SQL Injection: Bypass Authentication

The classic SQL injection: close the string, append `OR TRUE`, comment out the rest.

```sql
-- Inject: close the string, add OR TRUE, comment out the rest
SELECT app.login_vulnerable($$ ' OR '1'='1' -- $$, 'anything');
```

**Expected:** Returns a valid username even though `'anything'` is not a real password — **authentication is bypassed entirely**.

The SQL the function actually executes becomes:

```sql
SELECT username FROM app.users WHERE username = '' OR '1'='1' --' AND password_hash = 'anything'
```

The `WHERE` clause always evaluates `TRUE`, returning the first user in the table.

📸 **Screenshot checkpoint:** Capture the terminal output showing a username returned despite providing a wrong password.

---

### Step 2.4 — UNION Injection: Extract Data from Another Table

UNION-based injection reaches **beyond the intended table** to extract data the application never meant to expose.

```sql
-- Extract internal_cost from products — a column that should NEVER be visible
SELECT app.login_vulnerable(
  $$ ' UNION SELECT CAST(internal_cost AS TEXT) FROM app.products LIMIT 1 -- $$,
  'anything'
);
```

**Expected:** Returns a value like `4.5` — the `internal_cost` of the first product. This column was never intended to be visible through the login endpoint.

📸 **Screenshot checkpoint:** Capture the output showing an `internal_cost` value returned through the login function.

---

## Part 3 — Secure Parameterized Implementation

### Step 3.1 — Build the Secure Function

The fix is conceptually simple but architecturally fundamental: **never concatenate user input into SQL strings**. Use the variable directly as a query parameter.

```sql
CREATE OR REPLACE FUNCTION app.login_secure(
  p_username TEXT,
  p_password TEXT
) RETURNS TEXT AS $$
DECLARE
  v_result TEXT;
BEGIN
  -- SECURE: p_username and p_password are bound as data values,
  -- never parsed as SQL syntax. No injection possible.
  SELECT username INTO v_result
  FROM app.users
  WHERE username      = p_username
    AND password_hash = p_password;

  RETURN COALESCE(v_result, 'Login failed');
END;
$$ LANGUAGE plpgsql;
```

!!! info "Why This Works"
    In the secure version, `p_username` is used directly in a static `SELECT` statement. PostgreSQL parses and plans the query **before** substituting the parameter value. By the time the value is used, the query structure is already locked — there is no SQL left to inject into.

---

### Step 3.2 — Verify Normal Login Still Works

```sql
SELECT app.login_secure('alice', 'hash_alice');
```

**Expected:** `alice`

---

### Step 3.3 — Verify Injection Is Blocked

```sql
SELECT app.login_secure($$ ' OR '1'='1' -- $$, 'anything');
```

**Expected:** `Login failed` — the injection payload is treated as a literal string value, not SQL. PostgreSQL searches for a user whose username is literally `' OR '1'='1' --`, finds none, and returns the failure message.

📸 **Screenshot checkpoint:** Capture the terminal showing `Login failed` returned for the injection attempt against the secure function.

---

### Step 3.4 — Verify UNION Injection Is Also Blocked

```sql
SELECT app.login_secure(
  $$ ' UNION SELECT CAST(internal_cost AS TEXT) FROM app.products LIMIT 1 -- $$,
  'anything'
);
```

**Expected:** `Login failed` — the UNION payload is also treated as a literal string. No data from `app.products` is accessible.

📸 **Screenshot checkpoint:** Capture the output confirming `Login failed` for the UNION injection attempt.

---

## Part 4 — Second-Order SQL Injection Demo

Second-order (stored) SQL injection is the more insidious variant: malicious input is **stored safely** in the database, but later retrieved and fed into a **vulnerable** query — triggering the injection at that later point.

### Step 4.1 — Demonstrate Second-Order Injection Concept

```sql
-- Step 1: Store malicious data safely via a parameterized INSERT
-- The dollar-quoted literal is stored as-is — not executed at insert time
INSERT INTO app.users (username, email, role, password_hash)
VALUES (
  $$ admin'-- $$,       -- looks like SQL but stored safely as a string
  'attacker@evil.com',
  'user',
  'hash_attacker'
);

-- Step 2: Confirm the data was stored correctly (not executed)
SELECT id, username, email
FROM app.users
WHERE email = 'attacker@evil.com';
```

The username `admin'--` is stored verbatim. Safe so far.

```sql
-- Step 3: A later VULNERABLE query retrieves the stored value and injects it
-- This simulates a "change password" or "lookup by stored username" operation
SELECT app.login_vulnerable(
  (SELECT username FROM app.users WHERE email = 'attacker@evil.com'),
  'anything'
);
```

The retrieved username `admin'--` is now concatenated into the vulnerable function's SQL string, producing:

```sql
SELECT username FROM app.users WHERE username = 'admin'--' AND password_hash = 'anything'
```

The `--` comments out the password check, returning the `admin` account.

!!! danger "Why Second-Order Is Hard to Find"
    Input validation and parameterization at the **insertion** point cannot prevent this if a **different code path** later uses the stored value in a vulnerable query. Testing requires tracing data from storage back through every downstream usage — not just testing the input point.

📸 **Screenshot checkpoint:** Capture the output showing the second-order injection triggering on the stored malicious username.

---

## Cleanup / Reset

To remove all objects created in this lab:

```sql
-- Full reset for Lab 03
DROP SCHEMA IF EXISTS app CASCADE;
```

!!! warning
    This drops the `app` schema, all tables, and all functions. The verification script will fail if run after this reset. Only reset if explicitly re-doing the lab.

---

## Assessment

### Verification Script

Dr. Chen will run the following script against your Neon `lab-03` branch connection string.

```sql
-- VERIFY LAB 03

SELECT
  -- Vulnerable function exists in app schema
  (SELECT COUNT(*)
   FROM pg_proc p
   JOIN pg_namespace n ON n.oid = p.pronamespace
   WHERE n.nspname = 'app'
     AND p.proname = 'login_vulnerable')::INT          AS vuln_function_exists,

  -- Secure function exists in app schema
  (SELECT COUNT(*)
   FROM pg_proc p
   JOIN pg_namespace n ON n.oid = p.pronamespace
   WHERE n.nspname = 'app'
     AND p.proname = 'login_secure')::INT              AS secure_function_exists,

  -- Injection payload returns 'Login failed' from the secure function
  (SELECT app.login_secure($$ ' OR '1'='1' -- $$, 'x'))
                                                       AS injection_blocked,

  -- Legitimate login still works through the secure function
  (SELECT app.login_secure('alice', 'hash_alice'))     AS normal_login;
```

**Expected results:**

| vuln_function_exists | secure_function_exists | injection_blocked | normal_login |
|---|---|---|---|
| 1 | 1 | Login failed | alice |

---

### Additional Requirement

**Secure product search function** *(20 pts)*

Create a third function `app.search_products_secure(p_name TEXT)` that:

1. Searches `app.products` by name using a **parameterized query** (no string concatenation).
2. Returns **only** the public columns: `id`, `name`, `price` — **never** `internal_cost`.
3. Uses `ILIKE` or `LIKE` for partial-match searching (e.g., searching for `'Widget'` returns all Widget products).

```sql
CREATE OR REPLACE FUNCTION app.search_products_secure(p_name TEXT)
RETURNS TABLE(id INT, name TEXT, price NUMERIC) AS $$
BEGIN
  RETURN QUERY
    SELECT p.id, p.name, p.price
    FROM app.products p
    WHERE p.name ILIKE '%' || p_name || '%';
END;
$$ LANGUAGE plpgsql;
```

Then demonstrate both of these:

```sql
-- 1. Injection attempt returns no rows (cannot reach internal_cost)
SELECT * FROM app.search_products_secure(
  $$ ' UNION SELECT internal_cost::TEXT, NULL, NULL FROM app.products-- $$
);

-- 2. Legitimate search returns expected public data
SELECT * FROM app.search_products_secure('Widget');
```

**Submit:** Both queries and screenshots of their outputs. The injection attempt must return 0 rows; the legitimate search must return the Widget A and Widget B rows with **no `internal_cost` column visible**.

---

### Reflection Questions

Answer each question in **3–5 sentences** in your lab report.

1. **Why Parameterization Prevents Injection** — Explain in technical terms why string concatenation causes SQL injection while parameterized queries do not. What specifically does PostgreSQL do differently at the **parse and plan** stage when it encounters a parameter placeholder (`$1`) versus a concatenated string? At what point in query processing is the distinction made?

2. **Blast Radius of a Single Vulnerability** — The UNION injection extracted `internal_cost` from a completely different table (`app.products`) through a vulnerability in the login function. What does this tell you about the blast radius of a single SQL injection vulnerability? Beyond the table the vulnerable query targets, what else is potentially accessible to an attacker with UNION injection capability?

3. **Second-Order Injection and Testing** — Second-order SQL injection stores malicious input safely but triggers it through a later vulnerable query. Why is this significantly harder to detect than direct (first-order) injection? What specific testing approach — beyond standard input fuzzing — is required to reliably find second-order injection vulnerabilities in a large application?

---

!!! tip "Grading Rubric"
    | Component | Points |
    |---|---|
    | Lab steps completed with screenshots at all checkpoints | 50 |
    | Verification script — all 4 values correct | 30 |
    | Additional requirement — `search_products_secure` implemented, both demo queries shown | 20 |
    | **Total** | **100** |
