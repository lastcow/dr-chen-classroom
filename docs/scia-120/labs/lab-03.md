# Lab 03 — Password Storage: Never Store Plaintext

**Course:** SCIA-120 · Introduction to Secure Computing  
**Topic:** Cryptography — Hashing & Password Security  
**Difficulty:** ⭐ Beginner  
**Estimated Time:** 45–60 minutes  
**Related Reading:** Chapter 6 — Cryptography Fundamentals

---

## Overview

One of the most common and damaging security failures in software development is storing user passwords in plaintext. In this lab you will explore how cryptographic hash functions work, compare weak vs strong hashing algorithms, understand salting, and see firsthand why weak passwords are trivially cracked even when hashed.

---

## Learning Objectives

1. Explain what a one-way hash function is and why it is used for passwords.
2. Generate MD5, SHA-1, SHA-256, and bcrypt hashes using command-line tools.
3. Understand why MD5 and SHA-1 are insufficient for password storage.
4. Demonstrate how salting defeats precomputed (rainbow table) attacks.
5. Crack a simple unsalted hash using a wordlist — and understand the lesson.

---

## Prerequisites

- Docker Desktop installed and running.

---

## Part 1 — What Is a Hash Function?

A **cryptographic hash function** takes any input and produces a fixed-length output (the *digest*). Key properties:

- **Deterministic:** Same input always gives same output.
- **One-way:** You cannot reverse the hash to get the original input.
- **Avalanche effect:** A tiny input change produces a completely different hash.

### Step 1.1 — Start a Working Container

```bash
docker run --rm -it ubuntu:22.04 bash
```

### Step 1.2 — Install Tools

```bash
apt-get update -qq && apt-get install -y -qq openssl hashcat
```

### Step 1.3 — Hash the Same String Multiple Ways

```bash
echo -n "password123" | md5sum
echo -n "password123" | sha1sum
echo -n "password123" | sha256sum
echo -n "password123" | sha512sum
```

📸 **Screenshot checkpoint:** Take a screenshot showing all four hash outputs.

**Observe:** Each algorithm produces a different length digest. SHA-512 is the longest and most collision-resistant.

### Step 1.4 — The Avalanche Effect

```bash
echo -n "password123" | sha256sum
echo -n "password124" | sha256sum
```

Even a one-character change produces a completely different hash.

📸 **Screenshot checkpoint:** Take a screenshot of both SHA-256 hashes side by side.

Type `exit` when done with Part 1.

---

## Part 2 — Why MD5 Is Dangerous for Passwords

MD5 is fast — which is a liability for password hashing. An attacker with a GPU can compute **billions** of MD5 hashes per second.

### Step 2.1 — Generate a Known Weak Hash

```bash
docker run --rm ubuntu:22.04 bash -c "echo -n 'letmein' | md5sum"
```

**Output:** `0d107d09f5bbe40cade3de5c71e9e9b7`

This exact hash appears in **every rainbow table and leaked hash database** on the internet. An attacker who steals this hash can Google it and immediately recover the password.

> Open a browser and search: `md5 0d107d09f5bbe40cade3de5c71e9e9b7`  
> You will instantly find it cracked on public sites.

📸 **Screenshot checkpoint:** Take a screenshot of the Google/search result showing the cracked hash.

---

## Part 3 — Salting: Defeating Rainbow Tables

A **salt** is a random value added to the password before hashing. This means two users with the same password get different hashes — and precomputed tables become useless.

### Step 3.1 — Hash With and Without a Salt

```bash
docker run --rm ubuntu:22.04 bash -c "
echo -n 'password123' | sha256sum
echo -n 'password123' | sha256sum
echo -n 'aX9z2kpassword123' | sha256sum
echo -n 'mQ3bRpassword123' | sha256sum
"
```

**Observe:**
- The first two lines (no salt) produce **identical** hashes — attacker only needs to crack once.
- The last two lines (different salts + same password) produce **completely different** hashes.

📸 **Screenshot checkpoint:** Take a screenshot showing all four hash outputs.

---

## Part 4 — bcrypt: The Right Way to Hash Passwords

`bcrypt` is designed specifically for password storage. It is intentionally **slow** (configurable work factor) and **automatically includes a salt**. Slowness is a feature — it makes brute-force attacks impractical.

### Step 4.1 — Install Python and bcrypt

```bash
docker run --rm -it python:3.11-slim bash
```

Inside the container:

```bash
pip install bcrypt -q
```

### Step 4.2 — Hash a Password with bcrypt

```bash
python3 -c "
import bcrypt

password = b'password123'
hashed = bcrypt.hashpw(password, bcrypt.gensalt())
print('bcrypt hash:', hashed.decode())
"
```

**Expected output (example):**
```
bcrypt hash: $2b$12$KIXjD3jHv0...
```

### Step 4.3 — Hash the Same Password Twice — Different Results!

```bash
python3 -c "
import bcrypt
pw = b'password123'
h1 = bcrypt.hashpw(pw, bcrypt.gensalt())
h2 = bcrypt.hashpw(pw, bcrypt.gensalt())
print('Hash 1:', h1.decode())
print('Hash 2:', h2.decode())
print('Same?', h1 == h2)
"
```

📸 **Screenshot checkpoint:** Take a screenshot showing two different bcrypt hashes from the same password.

### Step 4.4 — Verify a Password Against Its bcrypt Hash

```bash
python3 -c "
import bcrypt
pw = b'password123'
hashed = bcrypt.hashpw(pw, bcrypt.gensalt())

# Correct password
print('Correct:', bcrypt.checkpw(b'password123', hashed))
# Wrong password
print('Wrong:  ', bcrypt.checkpw(b'wrongpassword', hashed))
"
```

📸 **Screenshot checkpoint:** Take a screenshot showing True/False verification output.

Type `exit` to leave the container.

---

## Part 5 — Comparing Hash Speeds

Slowness is what makes bcrypt secure. Let's measure how long each algorithm takes.

```bash
docker run --rm python:3.11-slim bash -c "
pip install bcrypt -q 2>/dev/null
python3 -c \"
import hashlib, bcrypt, time

pw = b'password123'

# SHA-256 speed
start = time.time()
for _ in range(1000000):
    hashlib.sha256(pw).digest()
print(f'SHA-256 x 1,000,000: {time.time()-start:.2f}s')

# bcrypt speed
start = time.time()
for _ in range(3):
    bcrypt.hashpw(pw, bcrypt.gensalt())
print(f'bcrypt  x 3:         {time.time()-start:.2f}s')
\"
"
```

📸 **Screenshot checkpoint:** Take a screenshot showing the timing comparison. Note how bcrypt is dramatically slower per hash — that's by design.

---

## Cleanup

```bash
docker system prune -f
```

---

## Lab Assessment

### Screenshot Submission Checklist

- [ ] `screenshot-03a` — All four hash algorithms on "password123"
- [ ] `screenshot-03b` — Avalanche effect: one-character change
- [ ] `screenshot-03c` — Search result showing MD5 cracked online
- [ ] `screenshot-03d` — Salted vs unsalted hashes comparison
- [ ] `screenshot-03e` — Two different bcrypt hashes of same password
- [ ] `screenshot-03f` — bcrypt verify True/False
- [ ] `screenshot-03g` — Speed comparison (SHA-256 vs bcrypt)

### Reflection Questions

1. Why is it dangerous to store passwords as MD5 or SHA-256 hashes? Use what you observed in Part 2 to support your answer.
2. What is a "rainbow table attack"? How does salting defeat this attack?
3. Explain why bcrypt being *slow* is actually a **security feature**, not a bug.
4. If a website tells you "your password must be exactly 8 characters," what might that suggest about how they store passwords? Is this a red flag?

---

!!! tip "Grading Rubric"
    - Screenshots complete and clearly labeled: **40 points**  
    - Correct observations noted in each part: **20 points**  
    - Reflection questions answered thoughtfully: **40 points**  
    - **Total: 100 points**
