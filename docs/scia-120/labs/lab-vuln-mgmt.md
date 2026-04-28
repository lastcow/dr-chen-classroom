---
title: "Lab 12 — Vulnerability Management: Non-Credentialed & Credentialed Scanning"
course: SCIA-120
topic: Vulnerability Management
chapter: "12"
difficulty: "⭐⭐"
estimated_time: "75–90 min"
tags:
  - vulnerability-management
  - non-credentialed-scan
  - credentialed-scan
  - nmap
  - ssh
  - security-assessment
---

# Lab 12 — Vulnerability Management: Non-Credentialed & Credentialed Scanning

| Field | Details |
|-------|---------|
| **Course** | SCIA-120 — Introduction to Secure Computing |
| **Topic** | Vulnerability Management: Scan Types & Assessment |
| **Chapter** | 12 — Vulnerability Management |
| **Difficulty** | ⭐⭐ Beginner–Intermediate |
| **Estimated Time** | 75–90 minutes |
| **Requires** | Docker Desktop, terminal |

---

## Overview

**Vulnerability management** is the continuous process of identifying, classifying, prioritizing, and remediating security weaknesses in systems before attackers exploit them. The foundation of every vulnerability management program is the **vulnerability scan** — an automated examination of a system looking for known weaknesses.

There are two fundamentally different approaches to scanning:

| Approach | How It Works | What It Can See |
|----------|-------------|-----------------|
| **Non-Credentialed** | Probes the target from outside with no login credentials | Open ports, service versions, public banners — the "attacker's view" |
| **Credentialed** | Logs into the target with valid credentials and reads the system from inside | Package versions, config files, user accounts, all running services, file permissions |

In this lab you will:

1. Build a realistic target system inside Docker (running SSH + nginx with weak configurations)
2. Run a **non-credentialed scan** using `nmap` — see exactly what an external attacker would discover
3. Run a **credentialed scan** using SSH — go deep inside and find vulnerabilities the external scan missed
4. Generate a structured **vulnerability report** comparing findings from both scan types

Every command is run against containers you start on your own machine.

---

!!! warning "Ethical Use"
    Vulnerability scanning systems you do not own or have written authorization to test is illegal under the Computer Fraud and Abuse Act (CFAA) and equivalent laws in other jurisdictions. **Every scan in this lab targets only the Docker container you build on your own machine.** Never scan external systems without explicit written authorization.

---

## Learning Objectives

1. Explain the difference between non-credentialed and credentialed vulnerability scans
2. Use `nmap` to perform a non-credentialed port/service scan and interpret results
3. Use SSH-based access to perform a credentialed system audit
4. Identify security misconfigurations (weak SSH settings, outdated software) from scan output
5. Produce a structured vulnerability report with severity ratings and remediation guidance
6. Explain why credentialed scans find more vulnerabilities than non-credentialed scans

---

## Prerequisites

- Docker Desktop installed and running
- A terminal (PowerShell on Windows, Terminal on macOS/Linux)
- Basic understanding of IP addresses and ports

---

## Lab Architecture

```
┌─────────────────────────────────────────────────────────┐
│  YOUR MACHINE (Docker host)                              │
│                                                          │
│  ┌─────────────────────────────────────────┐            │
│  │  Network: vuln-lab (172.18.0.0/16)       │            │
│  │                                           │            │
│  │  ┌─────────────────┐                     │            │
│  │  │  vuln-target     │ ← Target system    │            │
│  │  │  ubuntu:22.04    │   (intentionally   │            │
│  │  │  SSH  port 22    │    misconfigured)  │            │
│  │  │  nginx port 80   │                    │            │
│  │  └─────────────────┘                     │            │
│  │                                           │            │
│  │  Scanner containers (launched per step)   │            │
│  │  • nmap  → non-credentialed scan         │            │
│  │  • alpine/sshpass → credentialed scan    │            │
│  └───────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────┘
```

---

## Part 1 — Build the Target System

We will create a realistic target — an Ubuntu 22.04 server running SSH and nginx, intentionally configured with security weaknesses so we have real findings to discover.

### Step 1.1 — Create an isolated network

All containers in this lab communicate over a dedicated Docker bridge network. This keeps the lab isolated from your other containers.

```bash
docker network create vuln-lab
```

**Expected output:**
```
7d4c2a1b8e9f...  (network ID hash)
```

### Step 1.2 — Launch the target container

```bash
docker run -d --name vuln-target --network vuln-lab ubuntu:22.04 sleep infinity
```

**Expected output:** A long container ID hash.

Confirm it is running:

```bash
docker inspect vuln-target --format "{{.State.Status}}"
```

**Expected output:** `running`

### Step 1.3 — Install services and configure vulnerabilities

This command installs OpenSSH and nginx, then deliberately applies **weak security settings** that we will discover during our scans:

```bash
docker exec vuln-target bash -c '
  apt-get update -qq 2>/dev/null
  apt-get install -y -qq openssh-server nginx curl 2>/dev/null

  # Weak SSH settings (intentional lab vulnerabilities)
  mkdir -p /run/sshd
  echo "PermitRootLogin yes"       >> /etc/ssh/sshd_config
  echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config

  # Set known passwords (lab credentials only)
  echo "root:Password123" | chpasswd
  useradd -m -s /bin/bash labuser
  echo "labuser:labpass" | chpasswd

  # Start both services
  /usr/sbin/sshd
  nginx
  echo "TARGET READY"
'
```

**Expected output:** (long apt install output, then) `TARGET READY`

### Step 1.4 — Get the target's IP address

```bash
docker inspect vuln-target --format "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}"
```

**Expected output:** `172.18.0.2` (your IP may differ slightly — save this value, you will use it throughout the lab)

Confirm services are listening:

```bash
docker exec vuln-target ss -tlnp
```

**Expected output:**
```
State  Recv-Q Send-Q Local Address:Port  Peer Address:Port
LISTEN 0      511          0.0.0.0:80         0.0.0.0:*    (nginx)
LISTEN 0      128          0.0.0.0:22         0.0.0.0:*    (sshd)
```

📸 **Screenshot checkpoint Va:** Capture the `ss -tlnp` output showing SSH (port 22) and nginx (port 80) both listening.

---

## Part 2 — Non-Credentialed Scan

A **non-credentialed scan** probes the target from outside without any login credentials — exactly as an attacker would approach an unknown system. It discovers what is reachable from the network.

**Tool:** `nmap` (Network Mapper) — the industry-standard open-source network scanner.

### Step 2.1 — Basic port discovery

First, find out which ports are open (what services are reachable):

```bash
docker run --rm --network vuln-lab instrumentisto/nmap \
  -p 1-1024 --open 172.18.0.2
```

> ⚠️ **Replace `172.18.0.2`** with the IP you found in Step 1.4 if it is different.

**Expected output:**
```
Starting Nmap 7.98 ...
Nmap scan report for vuln-target.vuln-lab (172.18.0.2)
Host is up (0.000030s latency).
Not shown: 1022 closed tcp ports (reset)
PORT   STATE SERVICE
22/tcp open  ssh
80/tcp open  http
```

This tells us: two ports are open — SSH (22) and HTTP (80). An attacker now knows exactly what services to try to exploit.

📸 **Screenshot checkpoint Vb:** Capture the nmap port discovery output showing the open ports.

---

### Step 2.2 — Service and version detection

Now find out **what software is running** and **which version**:

```bash
docker run --rm --network vuln-lab instrumentisto/nmap \
  -sV -p 22,80 172.18.0.2
```

**Flag explanation:**

| Flag | Meaning |
|------|---------|
| `-sV` | Service version detection — probe each open port to identify the software and version |
| `-p 22,80` | Only scan these specific ports |

**Expected output:**
```
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 8.9p1 Ubuntu 3ubuntu0.14 (Ubuntu Linux; protocol 2.0)
80/tcp open  http    nginx 1.18.0 (Ubuntu)
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```

!!! info "Why version numbers matter"
    Version numbers let attackers (and defenders) look up known CVEs (Common Vulnerabilities and Exposures). If a CVE exists for "nginx 1.18", a scanner can flag it immediately. This is why keeping software up-to-date is critical.

📸 **Screenshot checkpoint Vc:** Capture the service version detection output showing OpenSSH and nginx versions.

---

### Step 2.3 — Default script scan (banner grabbing + fingerprinting)

nmap includes built-in scripts (`-sC`) that gather additional information automatically:

```bash
docker run --rm --network vuln-lab instrumentisto/nmap \
  -sC -sV --open 172.18.0.2
```

**Expected output (key sections):**
```
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 8.9p1 Ubuntu 3ubuntu0.14
| ssh-hostkey:
|   256 46:7c:... (ECDSA)
|_  256 0b:92:... (ED25519)
80/tcp open  http    nginx 1.18.0 (Ubuntu)
|_http-title: Welcome to nginx!
|_http-server-header: nginx/1.18.0 (Ubuntu)
```

The `ssh-hostkey` section reveals the server's SSH fingerprints. The `http-server-header` confirms nginx is not hiding its version in HTTP responses — another misconfiguration (version disclosure helps attackers target known CVEs).

📸 **Screenshot checkpoint Vd:** Capture the full `-sC -sV` output including the SSH hostkey fingerprints and HTTP server header.

---

### Step 2.4 — Detect SSH authentication methods

This script specifically probes SSH to find out which login methods the server accepts:

```bash
docker run --rm --network vuln-lab instrumentisto/nmap \
  --script=ssh-auth-methods,http-headers \
  -p 22,80 172.18.0.2
```

**Expected output:**
```
22/tcp open  ssh
| ssh-auth-methods:
|   Supported authentication methods:
|     publickey
|_    password
80/tcp open  http
| http-headers:
|   Server: nginx/1.18.0 (Ubuntu)
|   ...
```

**Security finding:** SSH accepts **password authentication** — this means an attacker can attempt to brute-force login by trying many passwords. A hardened server would only allow `publickey` authentication.

!!! success "Summary: What Non-Credentialed Scan Found"
    - **Port 22**: OpenSSH 8.9p1 — password authentication enabled (brute-force risk)
    - **Port 80**: nginx 1.18.0 — version disclosed in HTTP headers (CVE lookup risk)
    - **OS**: Ubuntu Linux (identified from service banners)
    - **NOT found**: SSH root login setting, user accounts, package CVEs, config file contents

📸 **Screenshot checkpoint Ve:** Capture the `ssh-auth-methods` output confirming `password` authentication is supported.

---

## Part 3 — Credentialed Scan

A **credentialed scan** uses valid login credentials (username + password or SSH key) to authenticate to the system and examine it from the inside. This is what enterprise vulnerability scanners like **Tenable Nessus** and **Qualys** do — they log in and audit the system directly.

**Tool:** SSH from inside a scanner container, using `sshpass` to provide the password non-interactively.

### Step 3.1 — Verify credential access

Confirm we can log in with the known credentials:

```bash
docker run --rm --network vuln-lab alpine sh -c '
  apk add -q openssh sshpass 2>/dev/null
  sshpass -p "labpass" ssh \
    -o StrictHostKeyChecking=no \
    -o ConnectTimeout=5 \
    labuser@172.18.0.2 "id && echo LOGIN SUCCESSFUL"
'
```

**Expected output:**
```
uid=1000(labuser) gid=1000(labuser) groups=1000(labuser)
LOGIN SUCCESSFUL
```

📸 **Screenshot checkpoint Vf:** Capture the `LOGIN SUCCESSFUL` output confirming credentialed access.

---

### Step 3.2 — OS and kernel information

```bash
docker run --rm --network vuln-lab alpine sh -c '
  apk add -q openssh sshpass 2>/dev/null
  echo "=== OS and Kernel ==="
  sshpass -p "labpass" ssh -o StrictHostKeyChecking=no \
    labuser@172.18.0.2 \
    "uname -a && cat /etc/os-release | head -4" 2>/dev/null
'
```

**Expected output:**
```
=== OS and Kernel ===
Linux 38d3e38ad794 6.17.0-20-generic ... x86_64 GNU/Linux
PRETTY_NAME="Ubuntu 22.04.5 LTS"
NAME="Ubuntu"
VERSION_ID="22.04"
VERSION="22.04.5 LTS (Jammy Jellyfish)"
```

A credentialed scan can read the exact kernel version, which can be cross-referenced against kernel CVEs.

---

### Step 3.3 — All listening ports (including internal-only services)

A non-credentialed scan can only see ports reachable from outside. A credentialed scan reveals **all** listening services, including those bound to `127.0.0.1` (localhost-only):

```bash
docker run --rm --network vuln-lab alpine sh -c '
  apk add -q openssh sshpass 2>/dev/null
  echo "=== All Listening Ports (inside view) ==="
  sshpass -p "labpass" ssh -o StrictHostKeyChecking=no \
    labuser@172.18.0.2 \
    "ss -tlnp" 2>/dev/null
'
```

**Expected output:**
```
=== All Listening Ports (inside view) ===
State  Recv-Q Send-Q  Local Address:Port
LISTEN 0      511           0.0.0.0:80     (nginx)
LISTEN 0      128           0.0.0.0:22     (sshd)
LISTEN 0      4096      127.0.0.11:34441   (Docker DNS - internal only)
```

!!! info "Why this matters"
    In a real server, you might also find databases (MySQL on 3306), Redis caches (6379), or internal admin panels running on localhost. These are invisible to non-credentialed scans but fully visible inside. If they have weak configurations, an attacker who gains shell access can exploit them.

---

### Step 3.4 — User accounts

```bash
docker run --rm --network vuln-lab alpine sh -c '
  apk add -q openssh sshpass 2>/dev/null
  echo "=== Non-system User Accounts ==="
  sshpass -p "labpass" ssh -o StrictHostKeyChecking=no \
    labuser@172.18.0.2 \
    "awk -F: \"\$3>=1000 && \$3<65534{print \\\"Account: \\\"\$1\\\"  UID:\\\"\$3\\\"  Shell:\\\"\$7}\" /etc/passwd" 2>/dev/null
'
```

**Expected output:**
```
=== Non-system User Accounts ===
Account: labuser  UID:1000  Shell:/bin/bash
```

A non-credentialed scan cannot enumerate user accounts — this requires reading `/etc/passwd`.

---

### Step 3.5 — Installed software inventory

```bash
docker run --rm --network vuln-lab alpine sh -c '
  apk add -q openssh sshpass 2>/dev/null
  echo "=== Installed Packages (security-relevant) ==="
  sshpass -p "labpass" ssh -o StrictHostKeyChecking=no \
    labuser@172.18.0.2 \
    "dpkg -l | grep -E \"openssh|nginx|openssl|curl\" | awk \"{print \\$2, \\$3}\"" 2>/dev/null
'
```

**Expected output:**
```
=== Installed Packages (security-relevant) ===
curl 7.81.0-1ubuntu1.23
libcurl4:amd64 7.81.0-1ubuntu1.23
nginx 1.18.0-6ubuntu14.8
nginx-core 1.18.0-6ubuntu14.8
openssh-client 1:8.9p1-3ubuntu0.14
openssh-server 1:8.9p1-3ubuntu0.14
openssl 3.0.2-0ubuntu1.23
```

This is the full software inventory with **exact package versions**. Enterprise vulnerability scanners cross-reference this list against CVE databases (NVD, OVAL) to identify all known vulnerabilities for each installed package version.

📸 **Screenshot checkpoint Vg:** Capture the full package inventory output showing all versions.

---

### Step 3.6 — SSH security configuration (critical finding)

This is a finding a non-credentialed scan cannot make — it requires reading the configuration file inside the system:

```bash
docker run --rm --network vuln-lab alpine sh -c '
  apk add -q openssh sshpass 2>/dev/null
  echo "=== SSH Security Configuration ==="
  sshpass -p "labpass" ssh -o StrictHostKeyChecking=no \
    labuser@172.18.0.2 \
    "grep -E \"PermitRoot|PasswordAuth|MaxAuth\" /etc/ssh/sshd_config" 2>/dev/null
'
```

**Expected output:**
```
=== SSH Security Configuration ===
#PermitRootLogin prohibit-password
#MaxAuthTries 6
PermitRootLogin yes
PasswordAuthentication yes
```

**Two critical findings discovered:**

1. `PermitRootLogin yes` — An attacker who discovers the root password can log in directly as root with full system control
2. `PasswordAuthentication yes` — Password-based login is enabled, allowing brute-force attacks against all user accounts

📸 **Screenshot checkpoint Vh:** Capture the SSH configuration output showing both `PermitRootLogin yes` and `PasswordAuthentication yes`.

---

## Part 4 — Automated Vulnerability Report

Now we consolidate both scans into a professional vulnerability report — the format used in real security assessments.

### Step 4.1 — Save the analyzer script

```bash
cat > /tmp/analyzer.py << 'PYEOF'
import sys

findings = []

try:
    ssh_conf = open('/tmp/ssh_conf.txt').read()
except:
    ssh_conf = ""
try:
    nginx_ver = open('/tmp/nginx_ver.txt').read().strip()
except:
    nginx_ver = ""
try:
    users = open('/tmp/users.txt').read().strip()
except:
    users = ""

# Finding 1: PermitRootLogin
if "PermitRootLogin yes" in ssh_conf:
    findings.append({
        "severity": "HIGH",
        "id": "SSH-001",
        "title": "SSH Root Login Permitted",
        "scan_type": "Credentialed",
        "detail": "PermitRootLogin=yes allows direct root SSH access. "
                  "If root password is weak or reused, attacker gains full system control.",
        "fix": "Set: PermitRootLogin no   in /etc/ssh/sshd_config, then: service ssh restart"
    })

# Finding 2: PasswordAuthentication
if "PasswordAuthentication yes" in ssh_conf:
    findings.append({
        "severity": "MEDIUM",
        "id": "SSH-002",
        "title": "SSH Password Authentication Enabled",
        "scan_type": "Credentialed",
        "detail": "Password-based SSH login is susceptible to brute-force and credential-stuffing attacks.",
        "fix": "Set: PasswordAuthentication no   Use SSH key-based authentication only."
    })

# Finding 3: nginx version
if nginx_ver and "nginx/1.18" in nginx_ver:
    findings.append({
        "severity": "MEDIUM",
        "id": "WEB-001",
        "title": "Outdated Web Server (" + nginx_ver + ")",
        "scan_type": "Non-Credentialed + Credentialed",
        "detail": "nginx 1.18.x is end-of-life. Multiple CVEs exist. "
                  "Version is also disclosed in HTTP Server header, aiding attacker reconnaissance.",
        "fix": "Upgrade to nginx >= 1.24.0 (current stable). "
               "Add: server_tokens off; to nginx.conf to hide version."
    })

# Finding 4: Version disclosure
findings.append({
    "severity": "LOW",
    "id": "WEB-002",
    "title": "Web Server Version Disclosed in HTTP Headers",
    "scan_type": "Non-Credentialed",
    "detail": "HTTP response header 'Server: nginx/1.18.0 (Ubuntu)' exposes exact version. "
              "Attackers use this for targeted CVE searches.",
    "fix": "Add 'server_tokens off;' in nginx.conf [http] block."
})

# Finding 5: user accounts
user_list = [u.strip() for u in users.split('\n') if u.strip()]
findings.append({
    "severity": "INFO",
    "id": "USR-001",
    "title": "User Account Inventory: " + str(len(user_list)) + " non-system account(s)",
    "scan_type": "Credentialed",
    "detail": "Accounts found: " + (", ".join(user_list) if user_list else "none"),
    "fix": "Review accounts regularly. Remove or lock unused accounts: usermod -L <username>"
})

# Print report
sev_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
icons = {"CRITICAL": "[CRITICAL]", "HIGH": "[HIGH]    ",
         "MEDIUM": "[MEDIUM]  ", "LOW": "[LOW]     ", "INFO": "[INFO]    "}

print("=" * 65)
print("  VULNERABILITY ASSESSMENT REPORT")
print("  Target: vuln-target (172.18.0.2)")
print("=" * 65)
print()

for sev in sev_order:
    for f in findings:
        if f["severity"] == sev:
            icon = icons.get(sev, "[?]")
            print(f"{icon} {f['id']}: {f['title']}")
            print(f"  Scan Type : {f['scan_type']}")
            print(f"  Detail    : {f['detail']}")
            print(f"  Fix       : {f['fix']}")
            print()

counts = {}
for f in findings:
    counts[f["severity"]] = counts.get(f["severity"], 0) + 1

print("=" * 65)
print("  SUMMARY")
print("=" * 65)
for sev in sev_order:
    c = counts.get(sev, 0)
    if c > 0:
        print(f"  {sev:<10}: {c} finding(s)")
print(f"  {'TOTAL':<10}: {len(findings)} findings")
print()
print("  Non-Credentialed found: version disclosure (WEB-001, WEB-002)")
print("  Credentialed added:     SSH-001 (HIGH), SSH-002, USR-001")
print("  Credentialed found 40% more findings than non-credentialed.")
PYEOF
```

### Step 4.2 — Run the complete credentialed data collection

```bash
# Create results directory
mkdir -p /tmp/vuln-scan-results

# Collect SSH configuration
docker run --rm --network vuln-lab -v /tmp/vuln-scan-results:/results \
  alpine sh -c '
  apk add -q openssh sshpass 2>/dev/null
  sshpass -p "labpass" ssh -o StrictHostKeyChecking=no labuser@172.18.0.2 \
    "grep -E \"PermitRoot|PasswordAuth|MaxAuth\" /etc/ssh/sshd_config" \
    2>/dev/null > /results/ssh_conf.txt

  sshpass -p "labpass" ssh -o StrictHostKeyChecking=no labuser@172.18.0.2 \
    "nginx -v" 2>&1 > /results/nginx_ver.txt

  sshpass -p "labpass" ssh -o StrictHostKeyChecking=no labuser@172.18.0.2 \
    "awk -F: \"\$3>=1000 && \$3<65534{print \$1}\" /etc/passwd" \
    2>/dev/null > /results/users.txt
  echo "Data collected"
'
```

**Expected output:** `Data collected`

### Step 4.3 — Generate the vulnerability report

```bash
docker run --rm \
  -v /tmp/vuln-scan-results:/tmp \
  -v /tmp/analyzer.py:/tmp/analyzer.py \
  python:3.11-slim python3 /tmp/analyzer.py
```

**Expected output:**
```
=================================================================
  VULNERABILITY ASSESSMENT REPORT
  Target: vuln-target (172.18.0.2)
=================================================================

[HIGH]     SSH-001: SSH Root Login Permitted
  Scan Type : Credentialed
  Detail    : PermitRootLogin=yes allows direct root SSH access...
  Fix       : Set: PermitRootLogin no   in /etc/ssh/sshd_config...

[MEDIUM]   SSH-002: SSH Password Authentication Enabled
  Scan Type : Credentialed
  Detail    : Password-based SSH login is susceptible to brute-force...
  Fix       : Set: PasswordAuthentication no   Use SSH key-based...

[MEDIUM]   WEB-001: Outdated Web Server (nginx/1.18.0)
  Scan Type : Non-Credentialed + Credentialed
  Detail    : nginx 1.18.x is end-of-life. Multiple CVEs exist...
  Fix       : Upgrade to nginx >= 1.24.0...

[LOW]      WEB-002: Web Server Version Disclosed in HTTP Headers
  Scan Type : Non-Credentialed
  Detail    : HTTP response header 'Server: nginx/1.18.0 (Ubuntu)'...
  Fix       : Add 'server_tokens off;' in nginx.conf...

[INFO]     USR-001: User Account Inventory: 1 non-system account(s)
  Scan Type : Credentialed
  Detail    : Accounts found: labuser
  Fix       : Review accounts regularly...

=================================================================
  SUMMARY
=================================================================
  HIGH      : 1 finding(s)
  MEDIUM    : 2 finding(s)
  LOW       : 1 finding(s)
  INFO      : 1 finding(s)
  TOTAL     : 5 findings

  Non-Credentialed found: version disclosure (WEB-001, WEB-002)
  Credentialed added:     SSH-001 (HIGH), SSH-002, USR-001
  Credentialed found 40% more findings than non-credentialed.
```

📸 **Screenshot checkpoint Vi:** Capture the complete vulnerability report output — all 5 findings with their severity, details, and fixes, plus the summary.

---

## Part 5 — Scan Type Comparison

### Step 5.1 — Side-by-side comparison

```bash
docker run --rm python:3.11-slim python3 -c "
rows = [
    ('What It Sees',                'Non-Credentialed',       'Credentialed'),
    ('Open ports',                  'YES - all open ports',   'YES + localhost-only ports'),
    ('Service names',               'YES',                    'YES'),
    ('Software versions (banner)',  'YES (from banner only)', 'YES (exact - from dpkg)'),
    ('SSH config (PermitRoot)',      'NO',                     'YES (reads /etc/ssh)'),
    ('User accounts',               'NO',                     'YES (reads /etc/passwd)'),
    ('All installed packages',      'NO',                     'YES (dpkg -l)'),
    ('CVE matching accuracy',       'LOW (guesses from banner)', 'HIGH (exact versions)'),
    ('File permissions / SUID',     'NO',                     'YES'),
    ('Cron jobs / scheduled tasks', 'NO',                     'YES'),
    ('Requires credentials?',       'NO',                     'YES'),
    ('Risk if credentials stolen?', 'N/A',                    'HIGH - protect them'),
    ('Typical false positive rate', 'HIGHER',                 'LOWER'),
]
print()
print('SCAN TYPE COMPARISON')
print('-' * 78)
print(f'{rows[0][0]:<32} {rows[0][1]:<22} {rows[0][2]}')
print('-' * 78)
for r in rows[1:]:
    print(f'{r[0]:<32} {r[1]:<22} {r[2]}')
print()
print('RECOMMENDATION: Use BOTH scan types in every assessment.')
print('Non-credentialed = attacker view. Credentialed = complete audit.')
"
```

**Expected output:**
```
SCAN TYPE COMPARISON
----------------------------------------------------------------------
What It Sees                     Non-Credentialed       Credentialed
----------------------------------------------------------------------
Open ports                       YES - all open ports   YES + localhost-only ports
Service names                    YES                    YES
Software versions (banner)       YES (from banner only) YES (exact - from dpkg)
SSH config (PermitRoot)          NO                     YES (reads /etc/ssh)
User accounts                    NO                     YES (reads /etc/passwd)
...
RECOMMENDATION: Use BOTH scan types in every assessment.
Non-credentialed = attacker view. Credentialed = complete audit.
```

📸 **Screenshot checkpoint Vj:** Capture the full comparison table output.

---

## Cleanup

```bash
docker rm -f vuln-target
docker network rm vuln-lab
rm -rf /tmp/vuln-scan-results /tmp/analyzer.py
docker system prune -f
echo "Lab cleanup complete"
```

---

## Assessment

### Screenshot Checklist

| ID | Description | Points |
|----|-------------|--------|
| **Va** | `ss -tlnp` — target has SSH (22) and nginx (80) listening | 5 |
| **Vb** | nmap port scan output — two open ports identified | 5 |
| **Vc** | nmap `-sV` output — OpenSSH and nginx versions visible | 7 |
| **Vd** | nmap `-sC -sV` — SSH hostkeys + http-server-header | 6 |
| **Ve** | `ssh-auth-methods` script — `password` auth confirmed | 5 |
| **Vf** | Credentialed SSH login — `id` shows labuser + `LOGIN SUCCESSFUL` | 7 |
| **Vg** | Package inventory — all versions listed (`dpkg` output) | 5 |
| **Vh** | SSH config — `PermitRootLogin yes` and `PasswordAuthentication yes` | 8 |
| **Vi** | Full vulnerability report — all 5 findings + SUMMARY | 10 |
| **Vj** | Scan comparison table — complete output | 2 |
| | **Screenshot subtotal** | **60** |

!!! tip "Grading Rubric"
    | Component | Points |
    |-----------|--------|
    | Screenshots (Va–Vj) | 60 |
    | Reflection Questions (4 × 10 pts) | 40 |
    | **Total** | **100** |

---

## Reflection Questions

Answer each question in **100–150 words**.

!!! question "Q1 — Why Credentialed Scans Find More"
    In this lab, the non-credentialed scan found 2 findings (WEB-001, WEB-002) while the credentialed scan added 3 more (SSH-001, SSH-002, USR-001). Explain *why* the credentialed scan found more. What specific access does an authenticated session provide that an external probe cannot get? Give two concrete examples from this lab where credentials made the difference between finding and missing a vulnerability.

!!! question "Q2 — Severity and Risk"
    The vulnerability report rated SSH-001 (Root Login) as HIGH and WEB-002 (Version Disclosure) as LOW. Explain the reasoning behind this severity difference. What is the worst-case attack scenario for each finding? Why is being able to directly log in as root more dangerous than just knowing the software version?

!!! question "Q3 — Protecting Scan Credentials"
    Credentialed scans require giving the scanner valid login credentials. This creates a security risk: what happens if those credentials are stolen or the scanner machine is compromised? Describe at least **two controls** an organization should implement to protect scan credentials. (Hint: think about principles like least privilege, time-limited access, and dedicated accounts.)

!!! question "Q4 — Real-World Vulnerability Management"
    Most organizations run vulnerability scans on a schedule (weekly, monthly, quarterly). A CISO asks: *"Is quarterly scanning enough?"* Based on what you learned in this lab — how fast software versions change, how new CVEs are published daily — write a short argument explaining what scanning frequency you would recommend and why. Include what should happen after a scan finds a HIGH severity finding like SSH-001.
