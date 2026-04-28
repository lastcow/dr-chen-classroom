---
title: "Lab 04: Database Authentication Hardening"
course: SCIA-340
topic: Database Authentication Mechanisms
week: 4
difficulty: ⭐⭐
estimated_time: 60 minutes
---

# Lab 04: Database Authentication Hardening

| Field | Details |
|---|---|
| **Course** | SCIA-340 — Database Security |
| **Week** | 4 |
| **Difficulty** | ⭐⭐ Foundational |
| **Estimated Time** | 60 minutes |
| **Topic** | Database Authentication Mechanisms |
| **Prerequisites** | Labs 01–03 complete; familiarity with PostgreSQL roles |
| **Deliverables** | Screenshots at each checkpoint + verification script output + service account audit |

---

## Overview

Authentication is the database's first security gate — it determines who is allowed in at all. In this lab you will:

1. Inspect the default authentication state of your Neon database.
2. Create **properly constrained** application service roles with connection limits, password expiry, and least-privilege flags.
3. Observe how PostgreSQL stores passwords as **SCRAM-SHA-256 hashes** — never plaintext.
4. Practice **account locking** (immediate incident response) and **forced password rotation**.
5. Audit the privilege flags that should never appear on a service account.

---

!!! warning "Branch Requirement"
    All SQL must be executed on your Neon branch. **Name your branch `lab-04` before starting.**
    Roles created on this branch are scoped to it — running on a different branch means the verification script will not find them.

!!! info "Neon Setup — How to Connect"
    1. Log in to [https://neon.tech](https://neon.tech) and select your **`lab-04`** branch.
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

## Part 1 — Understanding Default Authentication

### Step 1.1 — Inspect Current Roles

The `pg_authid` system catalog contains the authoritative role information including hashed passwords and expiry dates. Note: only superusers can read `rolpassword` from `pg_authid`.

```sql
SELECT
  rolname,
  rolsuper,
  rolcreaterole,
  rolcreatedb,
  rolcanlogin,
  rolconnlimit,
  rolpassword,
  rolvaliduntil
FROM pg_authid
WHERE rolname NOT LIKE 'pg_%'
ORDER BY rolname;
```

Observe the existing roles provided by Neon (typically `neon_superuser` and your project user). Note which have `rolcanlogin = true` and what their `rolconnlimit` is set to.

📸 **Screenshot checkpoint:** Capture the full `pg_authid` output.

---

### Step 1.2 — Password Encryption Algorithm

```sql
SHOW password_encryption;
```

**Expected:** `scram-sha-256`

!!! danger "MD5 is Broken — Avoid It"
    If this returns `md5`, your database is using a cryptographically broken password hashing scheme. MD5 hashes can be cracked with pre-computed rainbow tables. Modern PostgreSQL uses SCRAM-SHA-256, which includes a random salt and iteration count, making pre-computation attacks infeasible.

📸 **Screenshot checkpoint:** Capture the `password_encryption` setting.

---

## Part 2 — Creating Hardened Application Roles

### Step 2.1 — Create Properly Constrained Roles

We create three roles demonstrating different security profiles:

```sql
-- Application service account:
--   minimal privileges, connection limit, expiry, no inheritance
CREATE ROLE app_service
  LOGIN
  PASSWORD 'AppService_Secure#2026'
  CONNECTION LIMIT 10
  VALID UNTIL '2027-06-30'
  NOSUPERUSER
  NOCREATEDB
  NOCREATEROLE
  NOINHERIT;

-- Read-only reporting account:
--   low connection limit, cannot escalate
CREATE ROLE reporting_user
  LOGIN
  PASSWORD 'Reporting_Secure#2026'
  CONNECTION LIMIT 3
  NOSUPERUSER
  NOCREATEDB
  NOCREATEROLE;

-- Group role for RBAC (never connects directly):
CREATE ROLE data_analyst
  NOLOGIN
  NOSUPERUSER;
```

**What each constraint does:**

| Constraint | Security Effect |
|---|---|
| `CONNECTION LIMIT n` | Prevents one account from exhausting all database connections (DoS protection) |
| `VALID UNTIL 'date'` | Forces credential rotation; expired accounts cannot connect |
| `NOSUPERUSER` | Cannot override any access control check |
| `NOCREATEDB` | Cannot create new databases (limits lateral movement) |
| `NOCREATEROLE` | Cannot create or modify other roles (prevents privilege escalation) |
| `NOINHERIT` | Does not automatically inherit permissions from group roles |
| `NOLOGIN` | Cannot be used to open a database connection directly |

---

### Step 2.2 — Verify Constraints

```sql
SELECT
  rolname,
  rolcanlogin,
  rolconnlimit,
  rolvaliduntil,
  rolsuper,
  rolcreaterole,
  rolcreatedb
FROM pg_roles
WHERE rolname IN ('app_service', 'reporting_user', 'data_analyst')
ORDER BY rolname;
```

Confirm each role has the expected flags. `app_service` should show `rolconnlimit = 10` and a future `rolvaliduntil`. `data_analyst` should show `rolcanlogin = false`.

📸 **Screenshot checkpoint:** Capture the three-row output confirming all constraints.

---

## Part 3 — Password Security

### Step 3.1 — How PostgreSQL Stores Passwords

```sql
-- View the SCRAM hash prefix (safe to display — this is not the plaintext password)
SELECT
  rolname,
  LEFT(rolpassword, 30) AS password_prefix,
  LENGTH(rolpassword)   AS password_hash_length
FROM pg_authid
WHERE rolname IN ('app_service', 'reporting_user');
```

**Expected:** The `password_prefix` column starts with `SCRAM-SHA-256$` — confirming passwords are stored as salted hashes, never as plaintext or reversibly encoded values.

!!! info "SCRAM-SHA-256 Hash Format"
    A PostgreSQL SCRAM-SHA-256 hash looks like:
    ```
    SCRAM-SHA-256$4096:<base64-salt>$<base64-stored-key>:<base64-server-key>
    ```
    The `4096` is the PBKDF2 iteration count. The salt and stored-key make every hash unique even for identical passwords. An attacker who steals this hash cannot determine the original password without brute-forcing it against the salt at 4096 iterations per attempt.

📸 **Screenshot checkpoint:** Capture the SCRAM hash prefix output for both roles.

---

### Step 3.2 — Lock an Account (Immediate Security Response)

When a credential is believed compromised, the first response is to lock the account immediately — before rotating credentials.

```sql
-- Simulate locking a compromised account
ALTER ROLE reporting_user NOLOGIN;

-- Verify locked
SELECT rolname, rolcanlogin
FROM pg_roles
WHERE rolname = 'reporting_user';
```

**Expected:** `rolcanlogin = false`

```sql
-- Restore access after investigation is complete
ALTER ROLE reporting_user LOGIN;

-- Verify restored
SELECT rolname, rolcanlogin
FROM pg_roles
WHERE rolname = 'reporting_user';
```

**Expected:** `rolcanlogin = true`

📸 **Screenshot checkpoint:** Capture both the locked (`false`) and restored (`true`) states.

---

### Step 3.3 — Force Password Rotation

Setting `VALID UNTIL 'NOW'` immediately expires the credential, causing the next connection attempt to fail until a new password is set.

```sql
-- Expire the account immediately (incident response or scheduled rotation)
ALTER ROLE app_service VALID UNTIL 'NOW';

SELECT rolname, rolvaliduntil
FROM pg_roles
WHERE rolname = 'app_service';
```

**Expected:** `rolvaliduntil` is set to the current timestamp or earlier.

```sql
-- Reset with new password and updated expiry
ALTER ROLE app_service
  PASSWORD 'AppService_NewPass#2026'
  VALID UNTIL '2027-12-31';

SELECT rolname, rolvaliduntil
FROM pg_roles
WHERE rolname = 'app_service';
```

**Expected:** `rolvaliduntil = 2027-12-31 00:00:00+00`

📸 **Screenshot checkpoint:** Capture both the expired and reset `rolvaliduntil` values.

---

## Part 4 — Privilege Principle Verification

### Step 4.1 — Confirm Absence of Dangerous Flags

A service account audit verifies that application roles do not hold any flags that could be used to escalate privileges or bypass access controls.

```sql
SELECT
  rolname,
  CASE WHEN rolsuper
    THEN 'DANGER: superuser!'
    ELSE 'OK: not superuser'
  END AS superuser_status,
  CASE WHEN rolcreaterole
    THEN 'RISK: can create roles'
    ELSE 'OK: cannot create roles'
  END AS createrole_status,
  CASE WHEN rolcreatedb
    THEN 'RISK: can create dbs'
    ELSE 'OK: cannot create dbs'
  END AS createdb_status
FROM pg_roles
WHERE rolname IN ('app_service', 'reporting_user')
ORDER BY rolname;
```

**Expected:** All status columns should show the `OK:` prefix for both roles.

📸 **Screenshot checkpoint:** Capture the privilege audit output.

---

## Cleanup / Reset

To remove all roles created in this lab:

```sql
-- Full reset for Lab 04
DROP ROLE IF EXISTS app_service;
DROP ROLE IF EXISTS reporting_user;
DROP ROLE IF EXISTS data_analyst;
```

!!! warning
    Dropping roles is permanent. Only run this block if explicitly resetting the lab.

---

## Assessment

### Verification Script

Dr. Chen will run the following script against your Neon `lab-04` branch connection string.

```sql
-- VERIFY LAB 04

SELECT
  -- app_service: can login, connection limit = 10, not superuser
  (SELECT COUNT(*)
   FROM pg_roles
   WHERE rolname      = 'app_service'
     AND rolcanlogin  = TRUE
     AND rolconnlimit = 10
     AND rolsuper     = FALSE)::INT                       AS app_service_ok,

  -- reporting_user: can login, not superuser
  (SELECT COUNT(*)
   FROM pg_roles
   WHERE rolname     = 'reporting_user'
     AND rolcanlogin = TRUE
     AND rolsuper    = FALSE)::INT                        AS reporting_user_ok,

  -- data_analyst: NOLOGIN group role
  (SELECT COUNT(*)
   FROM pg_roles
   WHERE rolname     = 'data_analyst'
     AND rolcanlogin = FALSE)::INT                        AS data_analyst_nologin,

  -- app_service password stored as SCRAM hash
  (SELECT rolpassword LIKE 'SCRAM-SHA-256%'
   FROM pg_authid
   WHERE rolname = 'app_service')                         AS using_scram;
```

**Expected results:**

| app_service_ok | reporting_user_ok | data_analyst_nologin | using_scram |
|---|---|---|---|
| 1 | 1 | 1 | true |

---

### Additional Requirement

**Service Account Audit Query** *(20 pts)*

Research and implement a **service account audit query** that identifies all roles in your database that violate the principle of least privilege for service accounts.

**Definition of a violation:** A role that has `rolcanlogin = TRUE` AND has any of the following dangerous flags: `rolsuper = TRUE`, `rolcreaterole = TRUE`, or `rolcreatedb = TRUE`.

Complete these steps:

1. Write the audit query:

```sql
-- Service Account Privilege Violation Audit
SELECT
  rolname,
  rolsuper,
  rolcreaterole,
  rolcreatedb,
  rolconnlimit,
  rolvaliduntil,
  ARRAY_REMOVE(ARRAY[
    CASE WHEN rolsuper     THEN 'SUPERUSER'     END,
    CASE WHEN rolcreaterole THEN 'CREATEROLE'   END,
    CASE WHEN rolcreatedb  THEN 'CREATEDB'      END
  ], NULL) AS violations
FROM pg_roles
WHERE rolcanlogin = TRUE
  AND (rolsuper = TRUE OR rolcreaterole = TRUE OR rolcreatedb = TRUE)
ORDER BY rolname;
```

2. **Explain** each dangerous flag (in your lab report, 2–3 sentences each):
    - What `rolsuper = TRUE` enables and why it is dangerous on a service account.
    - What `rolcreaterole = TRUE` enables and the specific privilege escalation it allows.
    - What `rolcreatedb = TRUE` enables and why lateral movement is a concern.

3. For any violations found, write and run `ALTER ROLE` statements to remediate them:

```sql
-- Example remediation template (run for each violating role found)
ALTER ROLE <rolname> NOSUPERUSER NOCREATEROLE NOCREATEDB;
```

4. Re-run the audit query after remediation to confirm it returns **zero rows**.

**Submit:** The audit query, its initial output, your remediation statements, and a screenshot of the empty result after remediation.

---

### Reflection Questions

Answer each question in **3–5 sentences** in your lab report.

1. **SCRAM-SHA-256 vs bcrypt** — PostgreSQL stores passwords as SCRAM-SHA-256 hashes rather than plaintext. If an attacker gains read access to `pg_authid`, what can they do with the SCRAM hash? How does SCRAM-SHA-256 differ architecturally from bcrypt (used in most web applications), and which provides stronger offline-attack resistance and why?

2. **VALID UNTIL and Availability** — The `VALID UNTIL` constraint causes a role's password to expire. If a database service account's credential expires and the application cannot connect, what is the business impact? How should organizations balance the security benefit of frequent credential rotation against the availability risk, and what operational controls help manage the trade-off?

3. **NOINHERIT and Least Privilege** — The `NOINHERIT` flag prevents an application role from automatically inheriting permissions from group roles it belongs to. Why might you want `NOINHERIT` on a service account even though it seems to make privilege management less convenient? Describe a specific scenario where `INHERIT` (the default) on an application service account creates an unintended privilege escalation that `NOINHERIT` would prevent.

---

!!! tip "Grading Rubric"
    | Component | Points |
    |---|---|
    | Lab steps completed with screenshots at all checkpoints | 50 |
    | Verification script — all 4 values correct | 30 |
    | Additional requirement — audit query written, violations explained, remediation shown | 20 |
    | **Total** | **100** |
