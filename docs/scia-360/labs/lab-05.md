---
title: "Lab 05 — PAM & Password Policy"
course: SCIA-360
topic: OS Authentication
chapter: 5
difficulty: "⭐⭐"
time: "60–75 min"
reading: "Chapter 5 — OS Authentication Hardening"
---

# Lab 05 — PAM & Password Policy: OS Authentication Hardening

| | |
|---|---|
| **Course** | SCIA-360 OS Security |
| **Topic** | OS Authentication |
| **Chapter** | 5 |
| **Difficulty** | ⭐⭐ Intermediate |
| **Estimated Time** | 60–75 minutes |
| **Prerequisites** | Lab 01–04 completed; Docker installed |

---

## Overview

PAM — **Pluggable Authentication Modules** — is the Linux authentication framework that sits between every login-aware application and the actual authentication logic. Instead of every program implementing its own password check, all authentication flows through a configurable PAM stack.

In this lab you will:

- Explore PAM configuration files and understand module types and control flags
- Install and configure `libpam-pwquality` to enforce strong password requirements
- Read and interpret every field in `/etc/shadow`
- Configure password aging with `chage`
- Lock and unlock accounts with `passwd -l` / `passwd -u`

!!! tip "Grading Rubric"
    | Component | Points |
    |-----------|--------|
    | Screenshots (05a – 05f) | 40 pts |
    | PAM module type explanation (auth / account / password / session + control flags) | 20 pts |
    | Reflection questions (4 × 10 pts) | 40 pts |
    | **Total** | **100 pts** |

---

## Part 1 — PAM Architecture

### Step 1.1 — Launch the Lab Container

```bash
docker run --rm -it ubuntu:22.04 bash
```

> All steps in Parts 1–4 run **inside** this container unless stated otherwise.

---

### Step 1.2 — Explore PAM Configuration Files

```bash
ls /etc/pam.d/
cat /etc/pam.d/common-auth
cat /etc/pam.d/common-password
```

**Expected output:** A directory listing of per-service PAM files (`login`, `su`, `sshd`, `common-auth`, `common-password`, etc.). `common-auth` will show lines referencing `pam_unix.so`.

**Key concepts — PAM module types:**

| Module Type | Purpose |
|-------------|---------|
| `auth` | Verifies who you are (password, MFA token, biometric) |
| `account` | Checks whether the account is permitted to log in (expiry, time restrictions) |
| `password` | Handles password changes and quality checks |
| `session` | Sets up or tears down the session environment (home directory mounting, logging) |

**Key concepts — PAM control flags:**

| Flag | Behaviour |
|------|-----------|
| `required` | Must succeed; failure continues processing but ultimately denies |
| `requisite` | Must succeed; failure immediately denies without continuing |
| `sufficient` | Success immediately grants access (if no prior `required` failed) |
| `optional` | Result is ignored unless it is the only module for this type |

📸 **Screenshot checkpoint 05a:** Full terminal showing `ls /etc/pam.d/` output AND `cat /etc/pam.d/common-auth` content in the same window.

---

### Step 1.3 — Inspect a Multi-Module PAM Stack

```bash
cat /etc/pam.d/su
```

**Expected output:** Several module lines in the format:

```
module_type   control_flag   module_path   [options]
```

Each line is one step in the authentication stack. PAM evaluates them top-to-bottom, and the combination of control flags determines the final allow/deny decision.

---

## Part 2 — Password Quality

### Step 2.1 — Install and Inspect `pwquality`

```bash
apt-get update -qq && apt-get install -y -qq libpam-pwquality 2>/dev/null
cat /etc/security/pwquality.conf
```

**Expected output:** A file that is almost entirely comments. The effective defaults include `minlen = 8` (minimum 8 characters). All other quality options are inactive until explicitly enabled.

---

### Step 2.2 — Test Default Password Quality

```bash
useradd -m testuser
echo 'testuser:abc' | chpasswd 2>&1
echo 'testuser:Str0ng!P@ss99' | chpasswd && echo 'Strong password accepted'
```

**Expected output:**

- `abc` → `BAD PASSWORD: The password is shorter than 8 characters`
- `Str0ng!P@ss99` → `Strong password accepted`

📸 **Screenshot checkpoint 05b:** Terminal showing the weak password rejection message (`BAD PASSWORD`).

!!! warning "chpasswd vs passwd"
    `chpasswd` reads `user:password` pairs from stdin and is useful for scripting. The PAM quality check is still applied — it is not bypassed just because you are root.

---

### Step 2.3 — Configure a Stricter Policy

```bash
cat > /etc/security/pwquality.conf << 'EOF'
minlen = 12
dcredit = -1
ucredit = -1
lcredit = -1
ocredit = -1
EOF
cat /etc/security/pwquality.conf
```

**Parameter reference:**

| Parameter | Meaning |
|-----------|---------|
| `minlen = 12` | Minimum 12 characters |
| `dcredit = -1` | Require at least 1 digit |
| `ucredit = -1` | Require at least 1 uppercase letter |
| `lcredit = -1` | Require at least 1 lowercase letter |
| `ocredit = -1` | Require at least 1 special (other) character |

📸 **Screenshot checkpoint 05c:** The `cat /etc/security/pwquality.conf` output showing all five directives.

---

### Step 2.4 — Test the New Policy

```bash
useradd -m user2 2>/dev/null || true
echo 'user2:Short1!' | chpasswd 2>&1
echo 'user2:Str0ng!P@ssw0rd99' | chpasswd && echo 'Policy-compliant password accepted'
```

**Expected output:** `Short1!` is rejected (too short / missing character classes); `Str0ng!P@ssw0rd99` is accepted.

---

## Part 3 — Account Lockout and `/etc/login.defs`

### Step 3.1 — Install and Inspect `faillock`

```bash
apt-get update -qq && apt-get install -y -qq libpam-faillock 2>/dev/null
faillock --user testuser
```

`faillock` tracks failed authentication attempts per user. After a configurable threshold (default 3 failures in 15 minutes in `/etc/security/faillock.conf`), the account is temporarily locked.

---

### Step 3.2 — System-Wide Password Aging Defaults

```bash
grep -E '^PASS_MAX_DAYS|^PASS_MIN_DAYS|^PASS_WARN_AGE|^LOGIN_RETRIES' /etc/login.defs
```

**Expected output:**

```
PASS_MAX_DAYS   99999
PASS_MIN_DAYS   0
PASS_WARN_AGE   7
LOGIN_RETRIES   5
```

These are **defaults for new accounts**. They do not retroactively change existing accounts — use `chage` for that.

---

### Step 3.3 — Apply Password Aging to `testuser`

```bash
chage -M 90 -W 14 testuser
chage -l testuser
```

**Expected output:** `Maximum number of days between password change: 90` and `Number of days of warning before password expires: 14`.

📸 **Screenshot checkpoint 05d:** The full `chage -l testuser` output clearly showing the 90-day maximum and 14-day warning period.

---

## Part 4 — `/etc/shadow` Deep Dive

### Step 4.1 — Read and Annotate the Shadow Entry

```bash
grep testuser /etc/shadow
```

**Expected output** (example):

```
testuser:$y$j9T$...:19900:0:90:14:::
```

**The nine colon-separated fields:**

| Field | Example | Meaning |
|-------|---------|---------|
| 1 | `testuser` | Username |
| 2 | `$y$j9T$...` | Hashed password (`$y$` = yescrypt, `$6$` = SHA-512) |
| 3 | `19900` | Days since 1970-01-01 that the password was last changed |
| 4 | `0` | Minimum days between password changes (0 = change anytime) |
| 5 | `90` | Maximum days before password must be changed (`chage -M 90`) |
| 6 | `14` | Warning days before expiry (`chage -W 14`) |
| 7 | *(empty)* | Days of inactivity after expiry before account is disabled |
| 8 | *(empty)* | Absolute account expiry date (empty = never expires) |
| 9 | *(empty)* | Reserved for future use |

📸 **Screenshot checkpoint 05e:** The raw `/etc/shadow` entry for `testuser`. Annotate each field in your screenshot (draw arrows or add labels).

---

### Step 4.2 — Lock and Unlock the Account

```bash
passwd -l testuser
grep testuser /etc/shadow | cut -d: -f2 | head -c 5
echo '(! prefix = locked)'
passwd -u testuser
grep testuser /etc/shadow | cut -d: -f2 | head -c 5
echo '(hash restored = unlocked)'
```

**Expected output:**

```
!$y$j                  ← first 5 chars of locked hash
(! prefix = locked)
$y$j9                  ← first 5 chars of unlocked hash
(hash restored = unlocked)
```

`passwd -l` prepends `!` to the hash. PAM sees that `!` and refuses to authenticate — the stored hash can never match any password the user supplies. `passwd -u` removes the `!`, restoring the original hash.

📸 **Screenshot checkpoint 05f:** Both the locked state (`!` prefix visible) and the unlocked state in the same terminal session.

---

## Cleanup

Exit the container (type `exit` if still inside), then prune Docker resources:

```bash
docker system prune -f
```

---

## Assessment

### Screenshot Checklist

| ID | Required Content |
|----|-----------------|
| **05a** | `ls /etc/pam.d/` listing **and** `cat /etc/pam.d/common-auth` output |
| **05b** | Weak password (`abc`) rejected with `BAD PASSWORD` message |
| **05c** | `/etc/security/pwquality.conf` showing all five directives |
| **05d** | `chage -l testuser` output with 90-day max and 14-day warning |
| **05e** | Raw `/etc/shadow` entry for `testuser` with all nine fields annotated |
| **05f** | Account locked (`!` prefix) and then unlocked in the same session |

---

### Reflection Questions

!!! warning "Submission requirement"
    Answer each question in **complete paragraphs** (minimum 4–6 sentences each). Single-sentence answers will not receive full credit.

**Q1.** PAM stands for Pluggable Authentication Modules. What does *pluggable* mean in this context? Give a concrete example of how an organisation could add multi-factor authentication to the Linux `login` command without changing any application source code.

**Q2.** In Step 2.2, the password `abc` was rejected as too short. Why is minimum password length the single most impactful password policy control? Quantify how increasing minimum length from 8 to 12 characters affects the time required to exhaust all possible passwords through brute force (assume a modest 10 billion guesses per second).

**Q3.** `/etc/shadow` stores hashed passwords rather than plaintext. Why does this matter even though the file is only readable by root? Describe the specific steps an attacker would take after gaining read access to `/etc/shadow` — what tools would they use and what would they look for?

**Q4.** You locked `testuser`'s account with `passwd -l` and observed `!` prepended to the password hash. What class of attack does account locking defend against? Why might a security incident response team choose to lock a compromised account rather than immediately delete it?
