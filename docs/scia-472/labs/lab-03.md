---
title: "Lab 03: Network Scanning & Enumeration with Nmap"
course: SCIA-472
topic: Network Scanning
week: 3
difficulty: ⭐⭐
estimated_time: 60-75 minutes
tags:
  - nmap
  - network-scanning
  - enumeration
  - nse
  - service-detection
  - dvwa
  - docker
---

# Lab 03: Network Scanning & Enumeration with Nmap

| Field | Details |
|---|---|
| **Course** | SCIA-472 — Hacking Exposed & Incident Response |
| **Topic** | Network Scanning & Enumeration |
| **Week** | 3 |
| **Difficulty** | ⭐⭐ Intermediate |
| **Estimated Time** | 60–75 minutes |
| **Tools** | Docker, `instrumentisto/nmap`, `vulnerables/web-dvwa`, Python 3.11 |
| **Target** | `vulnerables/web-dvwa` at `10.10.0.10` (isolated Docker network) |
| **Prerequisites** | Labs 01–02 complete; Docker installed and running |

---

!!! warning "Ethical Use"
    All attacks and scanning must ONLY target containers you create in this lab. Never scan or attack systems you do not own or have explicit written permission to test.

---

## Overview

Network scanning is **active reconnaissance** — you are sending packets to targets. This lab uses an isolated Docker network with a deliberately vulnerable target (DVWA — Damn Vulnerable Web Application). All scans are strictly contained within Docker. Students master Nmap's scanning modes, service detection, OS fingerprinting, and NSE scripts.

By the end of this lab you will be able to:

- Create isolated Docker networks for safe lab environments
- Perform host discovery with ping scans
- Execute TCP connect and SYN scans against target hosts
- Detect service versions and OS fingerprints with Nmap
- Run NSE (Nmap Scripting Engine) scripts for targeted enumeration
- Save and interpret scan output for attack planning

> **Docker images used:**
> - Scanner: `instrumentisto/nmap`
> - Target: `vulnerables/web-dvwa`

---

## Part 1 — Lab Setup

### Step 1.1 — Create Isolated Lab Network

This network is completely isolated from the internet and your host system's network.

```bash
docker network create --subnet=10.10.0.0/24 scanlab
```

---

### Step 1.2 — Start Target Container

```bash
docker run -d \
  --name target \
  --network scanlab \
  --ip 10.10.0.10 \
  vulnerables/web-dvwa
sleep 5
docker ps | grep target
```

**Expected output:** `target` container listed as running with status `Up`.

📸 **Screenshot checkpoint:** Capture `docker ps` showing the target container running — label this **03a**.

---

## Part 2 — Host Discovery

Before scanning ports, confirm which hosts are alive on the network segment.

### Step 2.1 — Ping Scan (Discover Live Hosts)

```bash
docker run --rm --network scanlab instrumentisto/nmap \
  nmap -sn 10.10.0.0/24
```

**Expected output:** Shows `10.10.0.10` alive, plus the scanner's own IP address assigned by Docker.

📸 **Screenshot checkpoint:** Capture the ping scan output showing discovered live hosts — label this **03b**.

---

### Step 2.2 — TCP Connect Scan (Most Reliable)

```bash
docker run --rm --network scanlab instrumentisto/nmap \
  nmap -sT 10.10.0.10
```

**Expected output:** `PORT 80/tcp open http` and `3306/tcp open mysql` — DVWA runs Apache and MySQL.

📸 **Screenshot checkpoint:** Capture the port scan results showing open ports — label this **03c**.

---

## Part 3 — Service & Version Detection

Knowing a port is open is not enough. Version detection reveals **which** software is running — and which CVEs apply.

### Step 3.1 — Service Version Detection

```bash
docker run --rm --network scanlab instrumentisto/nmap \
  nmap -sV 10.10.0.10
```

**Expected output:** Shows Apache httpd version number and MySQL version number.

📸 **Screenshot checkpoint:** Capture the service version detection output — label this **03d**.

---

### Step 3.2 — Aggressive Scan (OS + Version + Scripts)

The `-A` flag combines OS detection (`-O`), version detection (`-sV`), script scanning (`-sC`), and traceroute.

```bash
docker run --rm --network scanlab instrumentisto/nmap \
  nmap -A 10.10.0.10
```

**Expected output:** Full output including OS detection attempt, detailed service information, and default NSE script results.

📸 **Screenshot checkpoint:** Capture the aggressive scan output (scroll to show OS and script sections) — label this **03e**.

---

### Step 3.3 — Full Port Scan (All 65535 Ports)

Default Nmap only scans the top 1000 ports. Services on non-standard ports are missed.

```bash
docker run --rm --network scanlab instrumentisto/nmap \
  nmap -p- 10.10.0.10
```

**Expected output:** Scans all ports — may reveal additional services on non-standard ports.

📸 **Screenshot checkpoint:** Capture the full port scan results — append to **03e**.

---

## Part 4 — NSE (Nmap Scripting Engine)

NSE scripts extend Nmap with targeted checks for specific services and vulnerabilities. Over 600 scripts are included.

### Step 4.1 — HTTP Enumeration Scripts

```bash
docker run --rm --network scanlab instrumentisto/nmap \
  nmap --script=http-title,http-server-header,http-methods 10.10.0.10 -p 80
```

**Expected output:** Page title of the web application, server header (`Apache/2.4.x`), and allowed HTTP methods (`GET`, `POST`, `OPTIONS`, etc.).

📸 **Screenshot checkpoint:** Capture the HTTP NSE script results — label this **03f**.

---

### Step 4.2 — MySQL Information Scripts

```bash
docker run --rm --network scanlab instrumentisto/nmap \
  nmap --script=mysql-empty-password,mysql-info 10.10.0.10 -p 3306
```

**Expected output:** MySQL version banner and result of empty password authentication check.

📸 **Screenshot checkpoint:** Capture the MySQL NSE script results — append to **03f**.

---

## Part 5 — Saving Scan Results

In real engagements, scan output is evidence. Save it in structured formats.

### Step 5.1 — Save to File and Analyze

```bash
docker run --rm --network scanlab -v /tmp:/output instrumentisto/nmap \
  nmap -sV -oN /output/scan_report.txt 10.10.0.10
cat /tmp/scan_report.txt
```

📸 **Screenshot checkpoint:** Capture the saved scan report contents — label this **03g**.

---

### Step 5.2 — Interpret Scan Results for Attack Planning

```bash
docker run --rm python:3.11-slim python3 -c "
findings = [
    ('80/tcp',   'open', 'Apache httpd 2.4.25', 'HIGH',   'Outdated Apache - check CVE database for 2.4.25'),
    ('3306/tcp', 'open', 'MySQL 5.7.x',         'HIGH',   'Database exposed - attempt authentication, check for CVEs'),
]
print('=== VULNERABILITY ANALYSIS FROM SCAN ===')
print(f'{\"Port\":<12} {\"State\":<8} {\"Service\":<25} {\"Risk\":<8} {\"Finding\"}')
print('-' * 85)
for port, state, service, risk, finding in findings:
    print(f'{port:<12} {state:<8} {service:<25} {risk:<8} {finding}')
print()
print('Next steps: Check CVE database for identified versions')
print('CVE lookup: https://nvd.nist.gov/vuln/search')
print('Apache 2.4.25 CVEs: https://httpd.apache.org/security/vulnerabilities_24.html')
"
```

📸 **Screenshot checkpoint:** Capture the attack surface analysis table — label this **03h**.

---

## Cleanup

```bash
docker stop target && docker rm target
docker network rm scanlab
docker system prune -f
```

---

## Assessment

### Screenshot Checklist

| Label | Required Screenshot | Points |
|---|---|---|
| **03a** | `docker ps` showing target container running | 5 |
| **03b** | Ping scan output discovering live hosts | 5 |
| **03c** | TCP connect scan showing open ports (80, 3306) | 5 |
| **03d** | Service version detection (`-sV`) with version numbers | 5 |
| **03e** | Aggressive scan output (`-A`) including OS and scripts | 5 |
| **03f** | HTTP + MySQL NSE script results | 5 |
| **03g** | Saved scan report (`scan_report.txt` contents) | 5 |
| **03h** | Attack surface analysis table | 5 |
| **Total** | | **40** |

---

### Analysis (20 points)

Complete a **Scan Findings Analysis Table** for the DVWA target:

| Port | Protocol | Service | Version | Risk Rating | CVE Reference | Recommended Action |
|---|---|---|---|---|---|---|
| 80 | TCP | | | | | |
| 3306 | TCP | | | | | |

For each finding:

- Assign a risk rating (Critical / High / Medium / Low / Info)
- Look up at least one real CVE at [nvd.nist.gov](https://nvd.nist.gov/vuln/search)
- Provide a specific remediation recommendation

---

### Reflection Questions (40 points — 10 points each)

1. Nmap found **Apache 2.4.25** on DVWA. This version is from 2017 and has multiple known vulnerabilities. How would an attacker use this version number to find exploits? What database would they search and what would a typical search query look like?

2. The `-sT` (TCP connect) scan vs `-sS` (SYN stealth) scan: explain the technical difference at the packet level. Why is SYN scanning called "stealthy" and why does it require root/admin privileges?

3. Nmap NSE scripts can brute-force credentials, enumerate services, and detect vulnerabilities. Is running NSE scripts against a system you have **written authorization** to test ethical? What about running them against a production system during business hours — even with authorization?

4. You saved the scan report to a file. In a real engagement, scan reports are sensitive documents that contain detailed attack surface information. What information must be included in the final deliverable report, and what data retention and destruction policies should govern scan artifacts after the engagement ends?

---

!!! tip "Grading Rubric"
    | Component | Points |
    |---|---|
    | Screenshots (03a–03h, all visible and labeled) | 40 |
    | Scan findings analysis table (complete with CVEs and remediation) | 20 |
    | Reflection questions (4 × 10 pts, substantive answers) | 40 |
    | **Total** | **100** |
