---
title: "Lab 12 — OS Hardening: CIS Benchmark Checks"
course: SCIA-360
topic: OS Hardening & Security Benchmarks
chapter: 14
difficulty: "⭐⭐"
estimated_time: "60–75 minutes"
tags:
  - cis-benchmark
  - hardening
  - ubuntu
  - compliance
  - remediation
  - sysctl
---

# Lab 12 — OS Hardening: CIS Benchmark Checks

| Field | Details |
|-------|---------|
| **Course** | SCIA-360 OS Security |
| **Topic** | OS Hardening & Security Benchmarks |
| **Chapter** | 14 |
| **Difficulty** | ⭐⭐ Intermediate |
| **Estimated Time** | 60–75 minutes |
| **Requires** | Docker, `ubuntu:22.04` image, Python 3 |

---

## Overview

The **CIS Benchmarks** (Center for Internet Security) are the gold standard for OS hardening configuration. Published by a consensus of hundreds of security professionals, vendors, and government agencies, they define specific, measurable configuration controls for every major operating system. Most compliance frameworks (PCI-DSS, HIPAA, FedRAMP, SOC 2) either reference CIS Benchmarks directly or use them as a baseline.

In this lab you will:

1. Understand the CIS Benchmark control categories for Ubuntu 22.04 Level 1
2. Run a Python-based automated CIS audit script against a default Ubuntu container
3. Observe which controls **fail** on a stock installation (and understand why)
4. Apply targeted remediations for the most critical failures
5. Re-run the audit to verify and quantify the improvement

!!! warning "Default ≠ Secure"
    A freshly installed Ubuntu system — even from an official image — will fail numerous CIS checks. This is expected. The CIS audit is a **starting point**, not a pass/fail grade on the OS itself. Your job as a security engineer is to identify failures, understand their risk, and apply appropriate remediations for your threat model.

---

## CIS Benchmark Overview

CIS Ubuntu 22.04 Level 1 controls are grouped into five categories:

| Category | Example Controls |
|----------|-----------------|
| **1. Filesystem** | Sticky bits, `nosuid`/`noexec` mounts, partition separation |
| **2. Authentication** | Password aging, minimum length, account lockout, root login |
| **3. Network** | IP forwarding, ICMP redirects, source routing, TCP wrappers |
| **4. Logging** | `rsyslog` configuration, `logrotate`, audit daemon |
| **5. System** | Package updates, cron permissions, SSH configuration |

**Level 1** controls are designed to be implementable on any system without significant performance impact or operational disruption. **Level 2** controls are more aggressive and may impact functionality.

---

## Part 1 — Running CIS Checks

### Step 1.1 — Introduce the check categories

```bash
docker run --rm ubuntu:22.04 bash -c "
echo 'CIS Ubuntu 22.04 Level 1 categories:'
echo '1. Filesystem: permissions, sticky bits, nosuid mounts'
echo '2. Authentication: password policy, account aging, sudo'
echo '3. Network: ip_forward, ICMP redirects, unused protocols'
echo '4. Logging: rsyslog, logrotate'
echo '5. System: patching, cron permissions, root login'"
```

This gives you the mental framework before running actual checks.

---

### Step 1.2 — Run the comprehensive CIS audit script

This script checks eight specific CIS controls across four categories. Each check reports its CIS control ID, a human-readable name, pass/fail status, and — for failures — the specific remediation command.

```bash
docker run --rm ubuntu:22.04 python3 -c "
import os, subprocess, stat

results = []
def check(cis_id, name, passed, detail='', fix=''):
    results.append((cis_id, passed))
    icon = '✅' if passed else '❌'
    print(f'{icon} [{cis_id}] {name}')
    if detail: print(f'   Detail: {detail}')
    if not passed and fix: print(f'   Fix: {fix}')

print('--- Authentication ---')
r = subprocess.run(['grep','^root:','/etc/shadow'], capture_output=True, text=True)
entry = r.stdout.strip()
pw_field = entry.split(':')[1] if ':' in entry else ''
nopw = pw_field.startswith('*') or '!' in pw_field
check('5.4.2', 'Root no direct login', nopw, pw_field[:20])

r = subprocess.run(['grep','-E','^PASS_MAX_DAYS','/etc/login.defs'], capture_output=True, text=True)
val = int(r.stdout.split()[-1]) if r.stdout.strip() else 99999
check('5.4.1.1', 'Password max age <= 365', val <= 365, f'PASS_MAX_DAYS={val}', 'sed -i s/PASS_MAX_DAYS.*/PASS_MAX_DAYS 90/ /etc/login.defs')

print('--- Filesystem ---')
st = os.stat('/etc/passwd')
check('6.1.2', '/etc/passwd perms 644', oct(stat.S_IMODE(st.st_mode)) == '0o644', oct(stat.S_IMODE(st.st_mode)))

st = os.stat('/etc/shadow')
check('6.1.3', '/etc/shadow perms <= 640', stat.S_IMODE(st.st_mode) <= 0o640, oct(stat.S_IMODE(st.st_mode)))

st = os.stat('/tmp')
check('1.1.3.1', '/tmp sticky bit set', bool(st.st_mode & stat.S_ISVTX), oct(stat.S_IMODE(st.st_mode)))

print('--- Network ---')
fwd = open('/proc/sys/net/ipv4/ip_forward').read().strip()
check('3.2.1', 'IP forwarding disabled', fwd == '0', f'ip_forward={fwd}', 'echo 0 > /proc/sys/net/ipv4/ip_forward')

redir = open('/proc/sys/net/ipv4/conf/all/accept_redirects').read().strip()
check('3.2.2', 'ICMP redirects not accepted', redir == '0', f'accept_redirects={redir}', 'echo 0 > /proc/sys/net/ipv4/conf/all/accept_redirects')

sr = open('/proc/sys/net/ipv4/conf/all/send_redirects').read().strip()
check('3.2.3', 'ICMP send_redirects disabled', sr == '0', f'send_redirects={sr}', 'echo 0 > /proc/sys/net/ipv4/conf/all/send_redirects')

print('--- Logging ---')
check('4.2.1', 'rsyslog.conf exists', os.path.exists('/etc/rsyslog.conf'), '/etc/rsyslog.conf', 'apt install rsyslog')

print('--- Summary ---')
passed = sum(1 for _,p in results if p)
print(f'Passed: {passed}/{len(results)}')
print(f'Score: {int(passed/len(results)*100)}/100')
"
```

**Expected output (default Ubuntu 22.04 container):**
```
--- Authentication ---
✅ [5.4.2] Root no direct login
❌ [5.4.1.1] Password max age <= 365
   Detail: PASS_MAX_DAYS=99999
   Fix: sed -i s/PASS_MAX_DAYS.*/PASS_MAX_DAYS 90/ /etc/login.defs
--- Filesystem ---
✅ [6.1.2] /etc/passwd perms 644
✅ [6.1.3] /etc/shadow perms <= 640
✅ [1.1.3.1] /tmp sticky bit set
--- Network ---
❌ [3.2.1] IP forwarding disabled
   Detail: ip_forward=1
   Fix: echo 0 > /proc/sys/net/ipv4/ip_forward
❌ [3.2.2] ICMP redirects not accepted
   ...
❌ [3.2.3] ICMP send_redirects disabled
   ...
--- Logging ---
❌ [4.2.1] rsyslog.conf exists
   ...
--- Summary ---
Passed: 3/8
Score: 37/100
```

It is completely normal for a default container to score in the 30–50% range. The purpose of this audit is to **identify the gap** between default and hardened configurations.

📸 **Screenshot checkpoint 12a:** Capture the full CIS audit output including all PASS/FAIL results and the summary score.

---

## Part 2 — Applying Remediations

### Step 2.1 — Fix CIS 5.4.1.1: Password maximum age

`PASS_MAX_DAYS=99999` is effectively "never expires." CIS recommends 90–365 days maximum. Setting this to 90 days ensures passwords are rotated regularly, limiting the window of exposure for compromised credentials.

```bash
docker run --rm ubuntu:22.04 bash -c "
echo 'BEFORE:' && grep PASS_MAX_DAYS /etc/login.defs
sed -i 's/^PASS_MAX_DAYS.*/PASS_MAX_DAYS\t90/' /etc/login.defs
echo 'AFTER:' && grep PASS_MAX_DAYS /etc/login.defs"
```

**Expected output:**
```
BEFORE:
PASS_MAX_DAYS   99999

AFTER:
PASS_MAX_DAYS   90
```

📸 **Screenshot checkpoint 12b:** Capture the BEFORE and AFTER `PASS_MAX_DAYS` values.

---

### Step 2.2 — Fix CIS 3.2.1–3.2.3: Network parameter hardening

These three kernel parameters control network behavior that creates attack surface even on servers that do not function as routers:

| Parameter | Risk When Enabled |
|-----------|------------------|
| `ip_forward` | Server can relay traffic between networks — useful only for routers/VPN gateways, dangerous on application servers |
| `accept_redirects` | ICMP redirect messages can manipulate the routing table — enables man-in-the-middle attacks |
| `send_redirects` | Server advertises itself as a router — network reconnaissance aid for attackers |

```bash
docker run --rm ubuntu:22.04 bash -c "
cat /proc/sys/net/ipv4/ip_forward
echo 0 > /proc/sys/net/ipv4/ip_forward
cat /proc/sys/net/ipv4/ip_forward

cat /proc/sys/net/ipv4/conf/all/accept_redirects
echo 0 > /proc/sys/net/ipv4/conf/all/accept_redirects
cat /proc/sys/net/ipv4/conf/all/accept_redirects

cat /proc/sys/net/ipv4/conf/all/send_redirects
echo 0 > /proc/sys/net/ipv4/conf/all/send_redirects
cat /proc/sys/net/ipv4/conf/all/send_redirects
echo 'Network parameters hardened'"
```

**Expected output:**
```
1          ← ip_forward before
0          ← ip_forward after
1          ← accept_redirects before
0          ← accept_redirects after
1          ← send_redirects before
0          ← send_redirects after
Network parameters hardened
```

!!! tip "Making sysctl changes persistent"
    Runtime changes to `/proc/sys/` are reset on reboot. To make them permanent, add them to `/etc/sysctl.d/99-cis-hardening.conf`:
    ```
    net.ipv4.ip_forward = 0
    net.ipv4.conf.all.accept_redirects = 0
    net.ipv4.conf.all.send_redirects = 0
    ```
    Then run `sysctl --system` to apply without rebooting.

📸 **Screenshot checkpoint 12c:** Capture all six parameter values (before and after for each of the three settings).

---

### Step 2.3 — Re-run the audit to verify improvement

This command applies all three remediations in a single container, then re-runs the simplified audit to demonstrate the improvement:

```bash
docker run --rm ubuntu:22.04 bash -c "
sed -i 's/^PASS_MAX_DAYS.*/PASS_MAX_DAYS\t90/' /etc/login.defs
echo 0 > /proc/sys/net/ipv4/ip_forward
echo 0 > /proc/sys/net/ipv4/conf/all/accept_redirects
echo 0 > /proc/sys/net/ipv4/conf/all/send_redirects
echo '=== After remediation ==='
python3 -c \"
import os,subprocess,stat

def check(name,passed,detail=''):
    print(f'{chr(9989) if passed else chr(10060)}  {name}' + (f': {detail}' if detail else ''))

r=subprocess.run(['grep','^root:','/etc/shadow'],capture_output=True,text=True)
pw=r.stdout.split(':')[1] if ':' in r.stdout else ''
check('Root no-login',pw.startswith('*') or '!' in pw,pw[:10])
r=subprocess.run(['grep','-E','^PASS_MAX_DAYS','/etc/login.defs'],capture_output=True,text=True)
val=int(r.stdout.split()[-1]) if r.stdout.strip() else 99999
check('PASS_MAX_DAYS<=365',val<=365,str(val))
check('/etc/passwd 644',oct(stat.S_IMODE(os.stat('/etc/passwd').st_mode))=='0o644')
check('/tmp sticky bit',bool(os.stat('/tmp').st_mode & stat.S_ISVTX))
check('ip_forward=0',open('/proc/sys/net/ipv4/ip_forward').read().strip()=='0')
check('accept_redirects=0',open('/proc/sys/net/ipv4/conf/all/accept_redirects').read().strip()=='0')
check('send_redirects=0',open('/proc/sys/net/ipv4/conf/all/send_redirects').read().strip()=='0')
\""
```

**Expected output after remediation:**
```
=== After remediation ===
✅  Root no-login: *
✅  PASS_MAX_DAYS<=365: 90
✅  /etc/passwd 644
✅  /tmp sticky bit
✅  ip_forward=0
✅  accept_redirects=0
✅  send_redirects=0
```

Seven out of seven checks now pass for the controls we remediatedrsyslog and other checks that require package installation remain as further work.

📸 **Screenshot checkpoint 12d:** Capture the post-remediation audit output showing the improved pass rate.

---

## Cleanup

```bash
docker system prune -f
```

---

## Assessment

### Screenshot Checklist

| ID | Description | Points |
|----|-------------|--------|
| **12a** | Initial CIS audit showing all PASS/FAIL results and summary score | 12 |
| **12b** | `PASS_MAX_DAYS` before (99999) and after (90) | 10 |
| **12c** | All three network parameters before (1) and after (0) | 10 |
| **12d** | Post-remediation audit showing the improved pass count | 8 |
| | **Screenshot subtotal** | **40** |

!!! tip "Grading Rubric"
    | Component | Points |
    |-----------|--------|
    | Screenshots (checklist above) | 40 |
    | Before/after remediation comparison table (complete all columns) | 20 |
    | Reflection questions (4 × 10 pts each) | 40 |
    | **Total** | **100** |

---

### Before/After Remediation Comparison Table *(complete and submit)*

| CIS ID | Control Name | Before (Default) | After (Remediated) | Risk of Leaving Unremediated |
|--------|-------------|-----------------|-------------------|------------------------------|
| 5.4.2 | Root direct login | | | |
| 5.4.1.1 | Password max age | | | |
| 6.1.2 | `/etc/passwd` permissions | | | |
| 6.1.3 | `/etc/shadow` permissions | | | |
| 1.1.3.1 | `/tmp` sticky bit | | | |
| 3.2.1 | IP forwarding | | | |
| 3.2.2 | ICMP accept redirects | | | |
| 3.2.3 | ICMP send redirects | | | |
| 4.2.1 | `rsyslog.conf` exists | | | |

---

### Reflection Questions

Answer each question in **150–200 words**.

1. **Default configuration philosophy:** A freshly installed Ubuntu container fails multiple CIS checks — not because Ubuntu is poorly engineered, but because default configurations optimize for a different goal than hardened security. Why does a default OS configuration **prioritize usability and compatibility over security**? Which classic security design principle (think Saltzer and Schroeder, 1975) explains this phenomenon? Name the principle and define it.

2. **Consensus-based standards:** CIS Benchmarks are developed through a consensus process involving hundreds of security professionals, vendors, and government agencies. Why is this **collaborative, community-driven approach** more valuable for defining security baselines than having each organization write its own internal hardening standard? What are the advantages in terms of auditor recognition, vendor support, and accumulated expertise?

3. **Password expiration tradeoffs:** The audit found `PASS_MAX_DAYS=99999` — effectively "passwords never expire." What specific attack scenario does **periodic password expiration** help limit the damage of? At the same time, what are the well-documented **negative security side effects** of very frequent expiration (e.g., 30-day cycles)? What does NIST SP 800-63B say about password expiration policies?

4. **Attack surface and operational risk:** The CIS "attack surface reduction" principle drives disabling IP forwarding, ICMP redirects, and unused protocols. Explain the **security reasoning** for each of these three controls. Then argue the other side: what is the **operational risk** of blindly applying all CIS Level 1 controls to a production server without evaluating your specific environment? Give a concrete example where a CIS control could break a legitimate business function.
