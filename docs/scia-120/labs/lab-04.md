# Lab 04 — Network Reconnaissance with Nmap

**Course:** SCIA-120 · Introduction to Secure Computing  
**Topic:** Network Security — Port Scanning & Service Discovery  
**Difficulty:** ⭐ Beginner  
**Estimated Time:** 45–60 minutes  
**Related Reading:** Chapter 7 — Network Security Fundamentals

---

## Overview

Before an attacker can exploit a system, they must first discover what is running on it. **Network reconnaissance** is the process of mapping open ports and identifying services. Security professionals use the same tools to assess their own networks. In this lab you will run real network scans using **Nmap** entirely within an isolated Docker network — no external targets, no ethical concerns.

---

## Learning Objectives

1. Understand what TCP ports are and why open ports represent an attack surface.
2. Use Nmap to discover hosts on a network.
3. Perform a basic port scan and interpret the output.
4. Perform a service version scan and OS detection scan.
5. Understand the difference between attacker reconnaissance and defensive scanning.

---

## Prerequisites

- Docker Desktop installed and running.

---

## Part 1 — Set Up the Lab Network

You will create an isolated Docker network with a target machine and a scanner machine.

### Step 1.1 — Create an Isolated Docker Network

```bash
docker network create --subnet=172.20.0.0/24 labnet
```

### Step 1.2 — Start a Target Machine (runs multiple services)

```bash
docker run -d \
  --name target \
  --network labnet \
  --ip 172.20.0.10 \
  vulnerables/web-dvwa
```

### Step 1.3 — Verify the Target Is Running

```bash
docker ps | grep target
```

📸 **Screenshot checkpoint:** Take a screenshot of `docker ps` showing the target container running.

---

## Part 2 — Basic Host Discovery

### Step 2.1 — Start the Scanner Container

```bash
docker run --rm -it \
  --name scanner \
  --network labnet \
  instrumentisto/nmap bash
```

You are now inside the scanner container.

### Step 2.2 — Ping Scan (Host Discovery)

```bash
nmap -sn 172.20.0.0/24
```

**Expected output (example):**
```
Nmap scan report for 172.20.0.10
Host is up (0.00017s latency).
Nmap done: 256 IP addresses (1 host up)
```

This tells us which hosts are alive on the network without scanning ports.

📸 **Screenshot checkpoint:** Take a screenshot of the host discovery scan output.

---

## Part 3 — Port Scanning

### Step 3.1 — Default Port Scan (Top 1000 Ports)

```bash
nmap 172.20.0.10
```

**Expected output (example):**
```
PORT     STATE SERVICE
80/tcp   open  http
3306/tcp open  mysql
```

📸 **Screenshot checkpoint:** Take a screenshot of the default scan output.

### Step 3.2 — Scan All Ports

```bash
nmap -p- 172.20.0.10
```

This scans all 65,535 TCP ports. It takes a little longer but reveals services running on non-standard ports.

📸 **Screenshot checkpoint:** Take a screenshot of the full port scan output.

### Step 3.3 — UDP Scan (Select Common Ports)

```bash
nmap -sU -p 53,161,500 172.20.0.10
```

UDP ports are often overlooked. DNS (53), SNMP (161), and VPN (500) are common UDP attack surfaces.

---

## Part 4 — Service Version Detection

Simply knowing port 80 is open tells you it's HTTP — but which web server? Version detection finds out.

### Step 4.1 — Version Detection Scan

```bash
nmap -sV 172.20.0.10
```

**Expected output (example):**
```
PORT     STATE SERVICE VERSION
80/tcp   open  http    Apache httpd 2.4.38
3306/tcp open  mysql   MySQL 5.7.x
```

📸 **Screenshot checkpoint:** Take a screenshot showing service versions.

**Observe:** Now you know the exact software and version. An attacker would search CVE databases for known vulnerabilities in these exact versions.

### Step 4.2 — Aggressive Scan (Version + OS Detection + Scripts)

```bash
nmap -A 172.20.0.10
```

This combines version detection, OS fingerprinting, and default Nmap scripts. It's loud and would be detected by an IDS, but shows the full picture.

📸 **Screenshot checkpoint:** Take a screenshot of the aggressive scan output. Note the OS detection section.

---

## Part 5 — Reading an Nmap Report

### Step 5.1 — Save Scan Results to a File

```bash
nmap -sV -oN /tmp/scan_report.txt 172.20.0.10
cat /tmp/scan_report.txt
```

In a real engagement, scan reports are saved and reviewed. Security teams use these reports to identify unneeded open ports and patch vulnerable services.

📸 **Screenshot checkpoint:** Take a screenshot of the saved scan report.

---

## Part 6 — Understanding Port States

Nmap reports ports in these states:

| State | Meaning |
|-------|---------|
| `open` | Port is actively accepting connections — a service is running |
| `closed` | Port responds but no service is listening |
| `filtered` | A firewall is blocking the probe — Nmap cannot determine the state |
| `open\|filtered` | Cannot distinguish between open and filtered |

### Step 6.1 — See "filtered" in Action

From your scanner, try to reach the Docker host itself (which is firewalled from our network):

```bash
nmap -p 22,80 172.20.0.1
```

Some ports may show as `filtered`, meaning a firewall is blocking the scan probe.

📸 **Screenshot checkpoint:** Take a screenshot showing `filtered` or `closed` port states.

Type `exit` to leave the scanner container.

---

## Cleanup

```bash
docker stop target
docker rm target
docker network rm labnet
docker system prune -f
```

---

## Lab Assessment

### Screenshot Submission Checklist

- [ ] `screenshot-04a` — `docker ps` showing target container running
- [ ] `screenshot-04b` — Host discovery scan (`-sn`)
- [ ] `screenshot-04c` — Default port scan results
- [ ] `screenshot-04d` — Full port scan (`-p-`)
- [ ] `screenshot-04e` — Service version detection (`-sV`)
- [ ] `screenshot-04f` — Aggressive scan (`-A`) output
- [ ] `screenshot-04g` — Saved scan report
- [ ] `screenshot-04h` — Filtered/closed port states

### Reflection Questions

1. What is a TCP port, and why does having many open ports increase the "attack surface" of a system?
2. In this lab, you found an Apache web server running. If an attacker knows the exact version, what would their next step likely be?
3. What is the difference between a **port scan** done by an attacker and the same scan done by a security professional? Is the tool itself ethical or unethical?
4. Why might a security professional save Nmap scan results and compare them monthly? What would a change in the report indicate?

---

!!! tip "Grading Rubric"
    - Screenshots complete and clearly labeled: **40 points**  
    - Port state table understood (short written explanation): **20 points**  
    - Reflection questions answered thoughtfully: **40 points**  
    - **Total: 100 points**
