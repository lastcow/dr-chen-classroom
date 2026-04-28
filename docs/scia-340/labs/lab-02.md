---
title: "Lab 02: RDBMS Architecture — Mapping the Attack Surface"
course: SCIA-340
topic: RDBMS Architecture and Security Model
week: 2
difficulty: ⭐⭐
estimated_time: 60 minutes
---

# Lab 02: RDBMS Architecture — Mapping the Attack Surface

| Field | Details |
|---|---|
| **Course** | SCIA-340 — Database Security |
| **Week** | 2 |
| **Difficulty** | ⭐⭐ Foundational |
| **Estimated Time** | 60 minutes |
| **Topic** | RDBMS Architecture and Security Model |
| **Prerequisites** | Lab 01 complete; `psql` installed; Lab 01 schema (`lab01`) present |
| **Deliverables** | Screenshots at each checkpoint + verification script output + Security Inventory Report |

---

## Overview

Understanding what a database exposes is the first step in defending it. In this lab you will perform a complete security-oriented inventory of your Neon PostgreSQL instance — querying every schema, table, extension, function, and privilege grant. This is the same reconnaissance workflow an attacker or a professional security auditor executes when first encountering a database. By the end you will have a comprehensive picture of your attack surface and will have hardened one well-known PostgreSQL default misconfiguration.

---

!!! warning "Branch Requirement"
    All SQL must be executed on your Neon branch. **Name your branch `lab-02` before starting.**
    Create the branch from the Neon dashboard before opening your `psql` connection.

!!! info "Neon Setup — How to Connect"
    1. Log in to [https://neon.tech](https://neon.tech) and select your **`lab-02`** branch.
    2. Copy the connection string from **Dashboard → Connection Details**.
    3. Connect and switch databases:
       ```bash
       export DATABASE_URL="postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/scia340?sslmode=require"
       psql $DATABASE_URL
       ```
       ```
       \c scia340
       ```

---

## Part 1 — Complete Database Inventory

A full database inventory enumerates every object in every schema. Attackers run exactly these queries after gaining any authenticated foothold.

### Step 1.1 — All Schemas

```sql
SELECT nspname AS schema_name,
       pg_get_userbyid(nspowner) AS owner
FROM pg_namespace
ORDER BY nspname;
```

Note every schema present — including `pg_catalog`, `information_schema`, and any user-created schemas from previous labs. Each schema is a potential target namespace.

📸 **Screenshot checkpoint:** Capture the full schema list.

---

### Step 1.2 — All Tables and Their Security Flags

```sql
SELECT
  schemaname,
  tablename,
  tableowner,
  hasindexes,
  hasrules,
  hastriggers,
  rowsecurity
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog','information_schema')
ORDER BY schemaname, tablename;
```

Pay particular attention to the `rowsecurity` column — tables with `rowsecurity = false` expose all rows to any role with `SELECT`. This will be examined again in Step 3.2.

📸 **Screenshot checkpoint:** Capture the full table inventory including `rowsecurity` values.

---

### Step 1.3 — All Installed Extensions (Attack Surface Enumeration)

```sql
SELECT extname,
       extversion,
       pg_get_userbyid(extowner) AS owner
FROM pg_extension
ORDER BY extname;
```

!!! warning "Extensions Expand Attack Surface"
    Every installed extension adds new functions, operators, and sometimes system-level capabilities to your database. An extension like `dblink` allows outbound network connections from within SQL queries. `pg_cron` can schedule arbitrary SQL execution. Even `uuid-ossp` adds external C code to the PostgreSQL process. **Know every extension installed in your database.**

---

### Step 1.4 — All Functions and Their Security Model

```sql
SELECT
  n.nspname AS schema,
  p.proname AS function_name,
  CASE p.prosecdef
    WHEN TRUE THEN 'SECURITY DEFINER'
    ELSE            'SECURITY INVOKER'
  END AS security,
  pg_get_userbyid(p.proowner) AS owner
FROM pg_proc p
JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE n.nspname NOT IN ('pg_catalog','information_schema')
ORDER BY schema, function_name;
```

!!! danger "SECURITY DEFINER = Privilege Escalation Risk"
    A function marked `SECURITY DEFINER` executes with the **owner's privileges**, not the caller's. If a superuser owns a `SECURITY DEFINER` function that can be called by a low-privilege user, that user effectively gains superuser power for the duration of the function call. Always audit these functions carefully.

📸 **Screenshot checkpoint:** Capture the function list showing the `security` column for each function.

---

## Part 2 — Privilege Inventory

Knowing *who can do what* is the core of access control auditing.

### Step 2.1 — Which Roles Have Which Table Privileges

```sql
SELECT
  grantee,
  table_schema,
  table_name,
  string_agg(privilege_type, ', ' ORDER BY privilege_type) AS privileges
FROM information_schema.role_table_grants
WHERE table_schema NOT IN ('pg_catalog','information_schema')
GROUP BY grantee, table_schema, table_name
ORDER BY grantee, table_schema, table_name;
```

This query collapses all individual grants into one row per (grantee, table), making it easy to scan for over-privileged roles.

📸 **Screenshot checkpoint:** Capture the privilege summary.

---

### Step 2.2 — Schema-Level Privileges

```sql
SELECT
  n.nspname AS schema,
  pg_get_userbyid(n.nspowner) AS owner,
  array_to_string(n.nspacl, ', ') AS access_control_list
FROM pg_namespace n
WHERE n.nspname NOT IN ('pg_catalog','information_schema')
ORDER BY schema;
```

The `nspacl` column (Access Control List) encodes schema-level `USAGE` and `CREATE` grants in PostgreSQL's internal ACL format. An entry like `=UC` means the `PUBLIC` pseudo-role has both `USAGE` and `CREATE` on that schema.

📸 **Screenshot checkpoint:** Capture the schema ACL output.

---

## Part 3 — Security Misconfigurations

### Step 3.1 — Find and Fix the PUBLIC Schema Risk

PostgreSQL versions prior to 15 granted `CREATE` on the `public` schema to `PUBLIC` (every authenticated user) by default. This allowed any user to inject objects — including malicious functions — into the search path of other users.

```sql
-- Check current state before hardening
SELECT has_schema_privilege('PUBLIC', 'public', 'CREATE') AS public_can_create_in_public;
```

```sql
-- Revoke the dangerous default (security hardening)
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
```

```sql
-- Verify the revocation took effect
SELECT has_schema_privilege('PUBLIC', 'public', 'CREATE') AS public_can_create_in_public;
```

**Expected:** First query returns `true`; after the revoke it returns `false`.

!!! info "CVE-2018-1058 Context"
    This default was documented as CVE-2018-1058. Any authenticated user could create a function named `lower()` in the public schema, and because `public` appears first in the default `search_path`, their malicious function would be called instead of the real `pg_catalog.lower()`. PostgreSQL 15+ changed this default — but many older databases and cloud instances may still have the vulnerability.

📸 **Screenshot checkpoint:** Capture both the before (`true`) and after (`false`) query results.

---

### Step 3.2 — Find Tables Without Row-Level Security

```sql
SELECT schemaname, tablename, rowsecurity
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog','information_schema')
  AND rowsecurity = FALSE
ORDER BY schemaname, tablename;
```

!!! warning "Tables Without RLS"
    Every table listed here is one where any role with `SELECT` privilege can read **every row** — regardless of whether those rows belong to them. For multi-tenant databases or tables with per-user data, this is a serious data isolation failure. RLS policies (covered in a later lab) solve this problem.

📸 **Screenshot checkpoint:** Capture the full list of tables lacking RLS.

---

## Cleanup / Reset

To remove all objects created in this lab and return to the Lab 01 baseline:

```sql
-- Nothing was created in this lab — only read and one revoke.
-- To restore the PUBLIC CREATE grant if needed for other testing:
GRANT CREATE ON SCHEMA public TO PUBLIC;
```

!!! warning
    Do **not** restore the `PUBLIC CREATE` grant unless explicitly instructed. The revoke performed in Step 3.1 is a security improvement that should remain in place.

---

## Assessment

### Verification Script

Dr. Chen will run the following script against your Neon `lab-02` branch connection string. All three checks must pass.

```sql
-- VERIFY LAB 02
SELECT
  has_schema_privilege('PUBLIC', 'public', 'CREATE')    AS public_create_revoked_false,

  (SELECT COUNT(*) FROM pg_extension)                   AS extension_count,

  (SELECT COUNT(*)
   FROM pg_proc p
   JOIN pg_namespace n ON n.oid = p.pronamespace
   WHERE n.nspname NOT IN ('pg_catalog','information_schema'))
                                                        AS user_function_count;
```

**Expected results:**

| public_create_revoked_false | extension_count | user_function_count |
|---|---|---|
| false | ≥ 1 | ≥ 0 |

!!! note
    `extension_count` must be at least 1 (PostgreSQL always installs `plpgsql` as an extension). `user_function_count` will be 0 on a clean Lab 02 branch unless you created functions in the additional requirement — either value is accepted.

---

### Additional Requirement

**Security Inventory Report** *(20 pts)*

Write a single SQL query that produces a unified **Security Inventory Report** for your Neon database. The result set must have exactly these columns: `category`, `item`, `risk_level`.

Requirements:

- At least one row of `category = 'Extension'` for **each** installed extension.
- At least one row of `category = 'SECURITY DEFINER Function'` for **each** `SECURITY DEFINER` function found (if none exist, include a single row with `item = 'None found'` and `risk_level = 'LOW'`).
- One row per table that **lacks RLS**, with `category = 'Table — No RLS'`.
- Assign `risk_level` values of `'HIGH'`, `'MEDIUM'`, or `'LOW'` based on your security judgment. Be prepared to defend your assignments.
- Use `UNION ALL` to combine the three (or more) SELECT statements into one result set.

**Starter scaffold:**

```sql
-- Security Inventory Report
SELECT
  'Extension'            AS category,
  extname || ' v' || extversion AS item,
  'MEDIUM'               AS risk_level   -- adjust based on extension
FROM pg_extension

UNION ALL

SELECT
  'SECURITY DEFINER Function' AS category,
  n.nspname || '.' || p.proname AS item,
  'HIGH'                AS risk_level
FROM pg_proc p
JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE p.prosecdef = TRUE
  AND n.nspname NOT IN ('pg_catalog','information_schema')

UNION ALL

SELECT
  'Table — No RLS'      AS category,
  schemaname || '.' || tablename AS item,
  'HIGH'                AS risk_level
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog','information_schema')
  AND rowsecurity = FALSE

ORDER BY risk_level, category, item;
```

Customize the `risk_level` values and add additional `UNION ALL` blocks as you see fit. **Submit:** the final query and a screenshot of its output with at least 3 rows.

---

### Reflection Questions

Answer each question in **3–5 sentences** in your lab report.

1. **SECURITY DEFINER Escalation** — You found that `SECURITY DEFINER` functions execute as the function owner, not the caller. Why is this a privilege escalation risk? Construct a concrete attack scenario: a low-privilege `app_user` role, a `SECURITY DEFINER` function owned by a superuser, and describe exactly what `app_user` can do that they should not be able to do.

2. **Extensions as Attack Surface** — The `pg_extension` catalog revealed every extension installed in your database. Why is an extension like `dblink` or `pg_cron` a security concern in a production database? Which security principle does keeping unnecessary extensions installed violate, and what is the correct remediation?

3. **CVE-2018-1058 and the Public Schema** — Before you ran `REVOKE CREATE ON SCHEMA public FROM PUBLIC`, any authenticated user could create objects in the public schema. Explain the specific attack this enables: how does a malicious user exploit PostgreSQL's `search_path` behavior to hijack legitimate function calls made by privileged users? Why was this rated as a significant vulnerability rather than a configuration choice?

---

!!! tip "Grading Rubric"
    | Component | Points |
    |---|---|
    | Lab steps completed with screenshots at all checkpoints | 50 |
    | Verification script — all three checks pass | 30 |
    | Additional requirement — Security Inventory Report with ≥ 3 rows, correct columns, risk assignments justified | 20 |
    | **Total** | **100** |
