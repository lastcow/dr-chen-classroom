# SCIA-340 Lab Overview

**SCIA-340 · Secure Databases · Frostburg State University · Spring 2026**

---

All thirteen SCIA-340 labs run on [Neon](https://neon.tech) — a serverless PostgreSQL platform. You write real SQL against a real PostgreSQL 16 database. Dr. Chen grades by connecting directly to your named branch and running the verification script. No local database installation is required.

---

!!! info "What You Need"
    Before Lab 01, have all three of these ready:

    | Requirement | Details |
    |-------------|---------|
    | **Neon account** | Free tier at [neon.tech](https://neon.tech) — no credit card required |
    | **psql client** | `psql --version` should return ≥ 14. Install: `brew install postgresql` (macOS) or `sudo apt install postgresql-client` (Linux/WSL) |
    | **Connection string** | From the Neon console → your project → **Connection Details** → copy the `psql` string |

    Your connection string looks like this:
    ```
    postgresql://username:password@ep-xxxx-xxxx.us-east-2.aws.neon.tech/neondb?sslmode=require
    ```
    Store it in an environment variable:
    ```bash
    export NEON_LAB_URL="postgresql://..."
    psql "$NEON_LAB_URL"
    ```

!!! success "Neon Free Tier Capabilities"
    Everything in this course fits within Neon's free tier:

    | Feature | Free Tier Limit |
    |---------|-----------------|
    | Projects | 10 |
    | Storage | 0.5 GB per project |
    | Branches | Unlimited |
    | Always-on TLS/SSL | ✅ Enforced on all connections |
    | PostgreSQL version | 16 (also supports 15) |
    | Branching | ✅ Create branch per lab for isolation |
    | SQL Editor | ✅ In-browser, no psql required |

---

## Lab Schedule

| Lab | Title | Week | Topic | Difficulty | Time |
|-----|-------|------|-------|------------|------|
| [Lab 01](lab-01.md) | Neon Setup & Database Security Baseline | 1 | Introduction | ⭐ | 60 min |
| [Lab 02](lab-02.md) | RDBMS Architecture — Mapping the Attack Surface | 2 | Architecture | ⭐⭐ | 60 min |
| [Lab 03](lab-03.md) | SQL Injection — Vulnerable vs Secure | 3 | SQL Security | ⭐⭐⭐ | 75 min |
| [Lab 04](lab-04.md) | Database Authentication Hardening | 4 | Authentication | ⭐⭐ | 60 min |
| [Lab 05](lab-05.md) | Role-Based Access Control (RBAC) | 5 | Access Control | ⭐⭐ | 75 min |
| [Lab 06](lab-06.md) | Row-Level Security — Multi-Tenant Isolation | 5 | RLS | ⭐⭐⭐ | 75 min |
| [Lab 07](lab-07.md) | Column-Level Encryption with pgcrypto | 6 | Encryption | ⭐⭐⭐ | 75 min |
| [Lab 08](lab-08.md) | Security Definer Views | 7 | Secure Design | ⭐⭐ | 60 min |
| [Lab 09](lab-09.md) | Database Auditing — Triggers & Logs | 8 | Auditing | ⭐⭐⭐ | 75 min |
| [Lab 10](lab-10.md) | Secure Schema Design & Data Classification | 10 | Design | ⭐⭐ | 60 min |
| [Lab 11](lab-11.md) | Cloud DB Security — Neon Branching | 11 | Cloud | ⭐⭐ | 60 min |
| [Lab 12](lab-12.md) | Compliance Controls — PCI-DSS & HIPAA | 13 | Compliance | ⭐⭐⭐ | 90 min |
| [Lab 13](lab-13.md) | Capstone — Harden & Audit a Complete DB | 15 | Capstone | ⭐⭐⭐⭐ | 120 min |

---

## Difficulty Guide

| Rating | Level | Description |
|--------|-------|-------------|
| ⭐ | Beginner | New concepts, guided step-by-step, no prior lab dependency |
| ⭐⭐ | Intermediate | Builds on previous labs, some independent problem-solving |
| ⭐⭐⭐ | Advanced | Combines multiple concepts, requires reading PostgreSQL docs |
| ⭐⭐⭐⭐ | Expert | Full integration, real-world complexity, open-ended design |

---

## Assessment Structure

Every lab uses the same grading model:

| Component | Points | Description |
|-----------|--------|-------------|
| **Lab Steps** | 50 | Complete all parts, run all SQL blocks, capture all 📸 screenshot checkpoints |
| **Verification Script** | 30 | Run the provided `VERIFY LAB XX` SQL; output must match expected values exactly |
| **Additional Requirement** | 20 | Open-ended extension task requiring independent design and implementation |
| **Total** | **100** | |

---

## Grading Model — Dr. Chen Direct Connection

SCIA-340 uses **live branch grading**: Dr. Chen connects directly to your Neon branch and runs the verification script. There is no "upload your SQL file" step.

### How It Works

```
Student workflow                        Dr. Chen workflow
─────────────────────────────           ──────────────────────────────
1. Create branch lab-XX                 1. Receive your connection string
   in Neon console                      2. Connect:
                                           psql "$STUDENT_CONNECTION_STRING"
2. Run all lab SQL on that branch       3. Run verify script:
                                           \i verify_lab-XX.sql
3. Run verification script,             4. Check output matches expected
   confirm expected output              5. Review screenshots
   matches
                                        6. Award points
4. Submit:
   • Your lab-XX connection string
   • Screenshots of all 📸 checkpoints
   • Additional requirement output
```

### Submission Checklist

- [ ] Branch named exactly `lab-XX` (e.g., `lab-11`, `lab-12`) or `lab-13-capstone`
- [ ] All SQL in the lab executed successfully on that branch
- [ ] Verification script output matches expected values
- [ ] All 📸 screenshot checkpoints captured
- [ ] Additional requirement completed and output screenshot submitted
- [ ] Reflection questions answered (submit as PDF or in the LMS text box)
- [ ] Connection string submitted to Dr. Chen via the LMS assignment

!!! warning "Branch Naming is Graded"
    Dr. Chen's grading script uses the branch name to find your work.
    If your branch is named `lab11` instead of `lab-11`, the automated check will fail.
    Use the exact branch name specified in each lab's warning box.

---

## Neon Branching Guide

Branching is a core SCIA-340 skill. Each lab runs on its own branch, giving you a clean, isolated environment.

### Create a Branch (Neon Console)

1. Log into [console.neon.tech](https://console.neon.tech)
2. Open your project
3. Click **Branches** in the left sidebar
4. Click **New Branch**
5. Set **Branch name** to `lab-XX` (e.g., `lab-11`)
6. Set **Branch from** → `main` (inherits main's schema state)
7. Click **Create Branch**
8. On the new branch page, click **Connection Details**
9. Copy the `psql` connection string

### Get the Connection String

```bash
# From Neon console → Branch → Connection Details → psql tab
# It looks like:
postgresql://john:AbCd1234@ep-calm-forest-123456.us-east-2.aws.neon.tech/neondb?sslmode=require

# Set it as an environment variable for the lab session:
export NEON_LAB11="postgresql://john:AbCd1234@ep-calm-forest-123456.us-east-2.aws.neon.tech/neondb?sslmode=require"
psql "$NEON_LAB11"
```

### Branch Lifecycle

```
main ──────────────────────────────────────── (production-equivalent)
  │
  ├── lab-01 ── (Lab 01 work, graded, then archived)
  ├── lab-02 ── (Lab 02 work, graded, then archived)
  │   ...
  ├── lab-11 ── (Lab 11 work — cloud security)
  ├── lab-12 ── (Lab 12 work — compliance)
  └── lab-13-capstone ── (FINAL — do not delete until grade posted)
```

> **Tip:** You can keep all branches — Neon free tier has no branch limit. Your capstone branch (`lab-13-capstone`) must remain active until your final grade is posted.

---

## Lab Prerequisites by Lab

Some labs build on artifacts created in earlier labs. Check this table before starting:

| Lab | Requires from Earlier Labs |
|-----|---------------------------|
| Labs 01–07 | No prior lab dependency |
| Lab 08 | Lab 05 RBAC roles helpful |
| Lab 09 | Lab 07 pgcrypto extension |
| Lab 10 | Lab 07 pgcrypto, Lab 09 audit schema |
| Lab 11 | Lab 04 authentication, Lab 07 encryption |
| Lab 12 | **Lab 07** pgcrypto, **Lab 09** `audit.capture_change()` function |
| Lab 13 | **All prior labs** — this is the integration capstone |

If you are starting a later lab on a fresh branch, recreate the prerequisite objects (pgcrypto extension, audit schema) on that branch first. The audit schema setup SQL is included in each lab that needs it.

---

## Troubleshooting FAQ

??? question "I get `SSL connection is required` — how do I fix it?"
    Neon requires SSL on all connections. Make sure your connection string includes `?sslmode=require` at the end. If you are using a GUI tool (DBeaver, DataGrip), find the SSL settings and set SSL mode to **require**.

    ```bash
    # Correct:
    psql "postgresql://user:pass@ep-xxxx.neon.tech/neondb?sslmode=require"

    # Missing sslmode — will fail:
    psql "postgresql://user:pass@ep-xxxx.neon.tech/neondb"
    ```

??? question "My verification script returns wrong values — everything looks right to me"
    Double-check:

    1. **Branch:** Are you connected to `lab-XX`? Run `SELECT current_database();` — the database name should match. More reliably, run Step 1.1's metadata query and compare the `server_ip` to what the Neon console shows for your `lab-XX` branch endpoint.
    2. **Schema names:** Verification scripts use exact schema names (e.g., `pci`, `hipaa`, `secure`). Check that you didn't accidentally create the table in `public` instead.
    3. **Rerun the setup:** If an INSERT failed silently, rerun the block. Most inserts use `ON CONFLICT DO NOTHING` so they are safe to rerun.

??? question "I get `function audit.capture_change() does not exist`"
    The audit schema from Lab 09 must be created on your current branch. Each branch is independent — objects from `lab-09` do not automatically exist on `lab-12`. Copy the Lab 09 audit setup SQL and run it on your current branch before attaching any audit triggers.

    The minimum you need:
    ```sql
    CREATE SCHEMA IF NOT EXISTS audit;
    CREATE TABLE IF NOT EXISTS audit.event_log ( /* ... Lab 09 DDL ... */ );
    CREATE OR REPLACE FUNCTION audit.capture_change() /* ... Lab 09 function ... */
    ```

??? question "I accidentally ran the insecure baseline SQL on `main` instead of `lab-13-capstone`"
    Do not try to undo it on `main`. Instead:

    1. Create a new branch from `main` before the bad SQL ran (use a timestamp-named branch like `main-backup-$(date +%Y%m%d)`)
    2. If you don't have a pre-breach snapshot, delete the insecure schema objects on `main` manually: `DROP SCHEMA insecure CASCADE;`
    3. Redo your work on `lab-13-capstone`
    4. This situation is exactly why we use branches for lab work

??? question "My `verify_capstone()` check #5 fails (password check) even though I hashed the passwords"
    Check #5 looks for the literal strings `'alice123'`, `'password'`, `'Password1'`, and `'letmein'` in `secure.customers.password_hash`. If the hash happened correctly, the column will contain a hex string like `2c624232cdd221771...`, not `alice123`. The check fails if the hash column still contains a plaintext password.

    Debug:
    ```sql
    SELECT id, LEFT(password_hash, 30) AS hash_preview
    FROM secure.customers;
    ```
    If you see `alice123` or `password` in the output, the `encode(digest(...))` in your migration query did not run. Re-run Step 2.2.

---

## Academic Integrity

Labs are **individual work** unless Dr. Chen explicitly designates a lab as a group assignment. You may:

- Discuss concepts and approach with classmates
- Reference PostgreSQL documentation, course slides, and Stack Overflow
- Use AI tools to understand concepts or debug error messages

You may **not**:

- Share your connection string with another student (it grants them write access to your branch)
- Copy another student's verification function output
- Submit work run by someone else on your behalf

Violations are subject to the Frostburg State University Academic Integrity Policy.

---

*SCIA-340 · Frostburg State University · Spring 2026*
