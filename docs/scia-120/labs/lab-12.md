# Lab 12 — Log Analysis & Anomaly Detection

**Course:** SCIA-120 · Introduction to Secure Computing  
**Topic:** Security Practices — Log Analysis, SIEM Fundamentals & Incident Detection  
**Difficulty:** ⭐⭐ Beginner–Intermediate  
**Estimated Time:** 60–75 minutes  
**Related Reading:** Chapter 14 — Security Practices, Risk Management, and Compliance

---

## Overview

"You can't defend what you can't see." Logs are a security professional's primary forensic tool — they record what happened, when, and from where. In this lab you will generate and analyze web server logs, detect brute-force attack patterns, identify suspicious activity using command-line tools, and build a basic anomaly detection script — all using Docker.

---

## Learning Objectives

1. Understand what information web server access logs contain.
2. Use `grep`, `awk`, `sort`, and `uniq` to analyze log data.
3. Identify brute-force attack patterns in authentication logs.
4. Detect unusual activity such as high-frequency requests and 404 scan patterns.
5. Write a basic Python script to automate log anomaly detection.

---

## Prerequisites

- Docker Desktop installed and running.

---

## Part 1 — Generate a Web Server with Real Logs

### Step 1.1 — Start an Nginx Server

```bash
docker run -d \
  --name log-server \
  -p 8080:80 \
  nginx:alpine
```

### Step 1.2 — Generate Realistic Traffic

```bash
# Normal user browsing
for path in "/" "/about" "/contact" "/products" "/faq"; do
  docker run --rm curlimages/curl curl -s http://localhost:8080$path -o /dev/null
done

# 404 errors (scanner behavior — probing for common files)
for path in "/admin" "/.env" "/wp-login.php" "/phpmyadmin" "/.git/config" "/backup.zip"; do
  docker run --rm curlimages/curl curl -s http://localhost:8080$path -o /dev/null
done

# Simulated brute-force (many requests from same IP)
for i in $(seq 1 20); do
  docker run --rm curlimages/curl curl -s "http://localhost:8080/login?attempt=$i" -o /dev/null
done
```

### Step 1.3 — Extract the Logs

Nginx writes access logs to stdout. Filter out startup messages by keeping only lines that contain `HTTP/`:

```bash
docker logs log-server 2>&1 | grep 'HTTP/' > /tmp/nginx_access.log
wc -l /tmp/nginx_access.log
cat /tmp/nginx_access.log
```

📸 **Screenshot checkpoint:** Take a screenshot showing the log file created with a line count.

---

## Part 2 — Understanding Log Format

### Step 2.1 — View Raw Log Entries

```bash
docker logs log-server 2>&1 | head -20
```

**Nginx Combined Log Format:**
```
127.0.0.1 - - [17/Apr/2026:10:23:15 +0000] "GET / HTTP/1.1" 200 615 "-" "curl/7.x"
```

| Field | Meaning |
|-------|---------|
| `127.0.0.1` | Client IP address |
| `[date]` | Timestamp |
| `"GET / HTTP/1.1"` | HTTP method, path, protocol |
| `200` | Response code (200=OK, 404=Not Found, 401=Unauthorized) |
| `615` | Response size in bytes |
| `"-"` | Referrer |
| `"curl/7.x"` | User agent |

📸 **Screenshot checkpoint:** Take a screenshot of several raw log lines and annotate each field in your submission.

---

## Part 3 — Basic Log Analysis Commands

Run a container with the log file for analysis:

```bash
docker run --rm -it \
  -v /tmp/nginx_access.log:/logs/access.log \
  ubuntu:22.04 bash
```

### Step 3.1 — Count Requests by HTTP Status Code

```bash
awk '{print $9}' /logs/access.log | sort | uniq -c | sort -rn
```

📸 **Screenshot checkpoint:** Take a screenshot showing the HTTP status code distribution.

### Step 3.2 — Find the Most Requested URLs

```bash
awk '{print $7}' /logs/access.log | sort | uniq -c | sort -rn | head -15
```

📸 **Screenshot checkpoint:** Take a screenshot showing the top requested URLs.

### Step 3.3 — Count Requests by IP Address

```bash
awk '{print $1}' /logs/access.log | sort | uniq -c | sort -rn | head -10
```

### Step 3.4 — Find All 404 Errors (Scanner Behavior)

```bash
grep '" 404 ' /logs/access.log
```

📸 **Screenshot checkpoint:** Take a screenshot showing the 404 entries — these are paths a scanner probed.

### Step 3.5 — Find High-Frequency Requesters (Potential Brute-Force)

```bash
awk '{print $1}' /logs/access.log | sort | uniq -c | sort -rn | awk '$1 > 5'
```

Any IP with more than 5 requests is potentially suspicious (in a real environment the threshold would be much higher, like 100/min).

---

## Part 4 — Simulated SSH Brute-Force Log Analysis

### Step 4.1 — Create a Simulated Auth Log

```bash
cat > /tmp/auth.log << 'EOF'
Apr 17 10:00:01 server sshd[1234]: Failed password for invalid user admin from 203.0.113.15 port 54321 ssh2
Apr 17 10:00:02 server sshd[1234]: Failed password for invalid user admin from 203.0.113.15 port 54322 ssh2
Apr 17 10:00:03 server sshd[1234]: Failed password for invalid user root from 203.0.113.15 port 54323 ssh2
Apr 17 10:00:04 server sshd[1234]: Failed password for invalid user oracle from 203.0.113.15 port 54324 ssh2
Apr 17 10:00:05 server sshd[1234]: Failed password for invalid user postgres from 203.0.113.15 port 54325 ssh2
Apr 17 10:00:06 server sshd[1234]: Failed password for invalid user user from 203.0.113.15 port 54326 ssh2
Apr 17 10:00:07 server sshd[1234]: Failed password for invalid user test from 203.0.113.15 port 54327 ssh2
Apr 17 10:00:08 server sshd[1234]: Failed password for invalid user ubuntu from 203.0.113.15 port 54328 ssh2
Apr 17 10:15:01 server sshd[5678]: Accepted publickey for alice from 10.0.0.5 port 44444 ssh2
Apr 17 10:30:00 server sshd[9012]: Failed password for bob from 198.51.100.99 port 12345 ssh2
Apr 17 10:30:01 server sshd[9012]: Failed password for bob from 198.51.100.99 port 12346 ssh2
Apr 17 10:30:02 server sshd[9013]: Accepted password for alice from 10.0.0.5 port 44445 ssh2
Apr 17 11:00:00 server sshd[1235]: Invalid user pi from 203.0.113.15 port 54329
Apr 17 11:00:01 server sshd[1235]: Failed password for invalid user pi from 203.0.113.15 port 54329 ssh2
EOF
```

### Step 4.2 — Analyze the Auth Log

```bash
docker run --rm \
  -v /tmp/auth.log:/logs/auth.log \
  ubuntu:22.04 bash -c "
echo '=== Failed login attempts by IP ==='
grep 'Failed password' /logs/auth.log | awk '{print \$(NF-3)}' | sort | uniq -c | sort -rn

echo ''
echo '=== Usernames being targeted ==='
grep 'Failed password' /logs/auth.log | awk '{print \$9}' | sort | uniq -c | sort -rn

echo ''
echo '=== Successful logins ==='
grep 'Accepted' /logs/auth.log
"
```

📸 **Screenshot checkpoint:** Take a screenshot showing the brute-force analysis results — which IP, which usernames, and successful logins.

---

## Part 5 — Automated Anomaly Detection Script

### Step 5.1 — Write a Python Anomaly Detector

```bash
docker run --rm -v /tmp:/data python:3.11-slim bash -c "
cat > /data/detect_anomalies.py << 'PYEOF'
import re
from collections import defaultdict

BRUTE_FORCE_THRESHOLD = 3  # flag IPs with >3 failed attempts
SCAN_404_THRESHOLD = 2      # flag IPs with >2 404 errors

failed_logins = defaultdict(int)
errors_404 = defaultdict(list)
suspicious_paths = ['/.env', '/wp-login.php', '/.git', '/phpmyadmin', '/admin', '/backup']

print('=== SECURITY ANOMALY REPORT ===\n')

# Analyze auth log
print('--- Brute Force Detection (auth.log) ---')
try:
    with open('/data/auth.log') as f:
        for line in f:
            if 'Failed password' in line:
                m = re.search(r'from (\d+\.\d+\.\d+\.\d+)', line)
                if m:
                    failed_logins[m.group(1)] += 1

    for ip, count in sorted(failed_logins.items(), key=lambda x: -x[1]):
        if count >= BRUTE_FORCE_THRESHOLD:
            print(f'  ⚠️  ALERT: {ip} had {count} failed login attempts — possible brute force')
        else:
            print(f'  ℹ️  {ip}: {count} failed attempt(s)')
except FileNotFoundError:
    print('  (auth.log not found)')

# Summary
print(f'\n--- Summary ---')
print(f'  IPs flagged for brute force: {sum(1 for c in failed_logins.values() if c >= BRUTE_FORCE_THRESHOLD)}')
print(f'  Total failed login sources: {len(failed_logins)}')
print('\n=== END OF REPORT ===')
PYEOF
python3 /data/detect_anomalies.py
"
```

📸 **Screenshot checkpoint:** Take a screenshot of the automated anomaly detection report output.

Type `exit` when done.

---

## Cleanup

```bash
docker stop log-server && docker rm log-server
rm -f /tmp/nginx_access.log /tmp/auth.log /tmp/detect_anomalies.py
docker system prune -f
```

---

## Lab Assessment

### Screenshot Submission Checklist

- [ ] `screenshot-12a` — Log file created with line count
- [ ] `screenshot-12b` — Raw log lines with fields annotated
- [ ] `screenshot-12c` — HTTP status code distribution
- [ ] `screenshot-12d` — Top requested URLs
- [ ] `screenshot-12e` — 404 entries showing scanner probing
- [ ] `screenshot-12f` — Brute-force IP and username analysis from auth.log
- [ ] `screenshot-12g` — Automated anomaly detection script output

### Reflection Questions

1. Looking at the 404 patterns in Part 3, what is an attacker likely trying to do by probing paths like `/.env`, `/wp-login.php`, and `/.git/config`?
2. In the auth log analysis, IP `203.0.113.15` tried multiple different usernames. What type of attack is this? How is it different from a brute-force attack on a known username?
3. Why is it important to correlate logs from multiple sources (web server + authentication + firewall)? What might you miss if you only looked at one log?
4. A company is breached on a Tuesday. The attackers are discovered on Friday. Why are logs critically important to the incident response team investigating the breach?

---

!!! tip "Grading Rubric"
    - Screenshots complete and clearly labeled: **40 points**  
    - Log pattern analysis notes accompanying each screenshot: **20 points**  
    - Reflection questions answered thoughtfully: **40 points**  
    - **Total: 100 points**
