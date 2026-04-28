---
title: "Lab 13 — Capstone: Build, Harden & Audit a Containerized System"
course: SCIA-360
topic: Capstone — All Chapters
chapter: "All"
difficulty: "⭐⭐⭐"
estimated_time: "90–120 minutes"
tags:
  - capstone
  - docker
  - hardening
  - suid
  - ssh
  - cis-benchmark
  - audit
  - defense-in-depth
---

# Lab 13 — Capstone: Build, Harden & Audit a Containerized System

| Field | Details |
|-------|---------|
| **Course** | SCIA-360 OS Security |
| **Topic** | Capstone — All Chapters |
| **Chapters** | Integrates Chapters 4, 5, 6, 8, 9, 12, 14 |
| **Difficulty** | ⭐⭐⭐ Advanced |
| **Estimated Time** | 90–120 minutes |
| **Requires** | Docker, `ubuntu:22.04` image, Python 3 |

---

## Overview

This capstone lab integrates all major OS security concepts from SCIA-360 into a single hands-on scenario. You will:

1. **Build** a containerized Ubuntu system that is deliberately misconfigured with six distinct vulnerabilities
2. **Assess** the system using both manual inspection and automated audit techniques
3. **Harden** the system by remediating each vulnerability in sequence
4. **Verify** the improvements with a final automated audit and calculate a hardening score

Each vulnerability maps to a specific course chapter, reinforcing how the individual topics form a coherent, layered security posture. By the end of this lab you will have hands-on experience with the complete security engineering lifecycle: **assess → remediate → verify**.

!!! warning "Time Management"
    This lab has more steps than previous labs. Read each part fully before executing commands. Budget **at least 90 minutes** — rushing through remediation steps without understanding them undermines the learning objective. The capstone essay is worth 30% of the grade and requires thoughtful reflection.

---

## Vulnerability Summary

The insecure system you will build contains six deliberate vulnerabilities. Keep this table as your remediation checklist:

| # | Vulnerability | Severity | Chapter | Fixed? |
|---|--------------|----------|---------|--------|
| 1 | Container runs as root (no `USER` directive) | High | Ch.6 — Capabilities | ☐ |
| 2 | SUID bit on `python3` | High | Ch.4 — FS Security | ☐ |
| 3 | World-writable `/var/www/html` (mode 777) | High | Ch.4 — FS Security | ☐ |
| 4 | SSH root login enabled | Critical | Ch.5 — Authentication | ☐ |
| 5 | Weak `webapp` user password (`abc`) | Critical | Ch.5 — Authentication | ☐ |
| 6 | IP forwarding enabled (default container behavior) | Medium | Ch.12 — Linux Architecture | ☐ |

---

## Part 1 — Build the Insecure System

### Step 1.1 — Create the Dockerfile

Each `# INSECURITY` comment in the Dockerfile identifies a deliberate misconfiguration. Study these comments carefully — you will reference them during assessment and remediation.

```bash
mkdir -p /tmp/scia360cap

cat > /tmp/scia360cap/Dockerfile << 'DEOF'
FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive

# INSECURITY 1: No non-root USER directive — container runs as root
# INSECURITY 2: Installs unnecessary services (attack surface)
RUN apt-get update -qq && apt-get install -y -qq nginx openssh-server python3 procps 2>/dev/null

# INSECURITY 3: Root SSH login enabled — allows direct root brute-force
RUN mkdir -p /run/sshd && \
    sed -i 's/#PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    echo 'root:password123' | chpasswd

# INSECURITY 4: World-writable web directory — any user can modify web content
RUN chmod 777 /var/www/html

# INSECURITY 5: SUID on python3 — trivial privilege escalation
RUN chmod u+s /usr/bin/python3.10 2>/dev/null || chmod u+s $(which python3) 2>/dev/null || true

# INSECURITY 6: Weak user password — trivially crackable
RUN useradd -m -s /bin/bash webapp && echo 'webapp:abc' | chpasswd

EXPOSE 80 22
CMD ["/bin/bash", "-c", "service nginx start 2>/dev/null; /usr/sbin/sshd -D"]
DEOF

docker build -t insecure-os-lab /tmp/scia360cap/ 2>&1 | tail -5
```

**Expected output:**
```
...
Successfully built a1b2c3d4e5f6
Successfully tagged insecure-os-lab:latest
```

📸 **Screenshot checkpoint 13a:** Capture the Docker build success output showing the image tag.

---

### Step 1.2 — Start the insecure container

```bash
docker run -d --name insecure-system -p 8080:80 -p 2222:22 insecure-os-lab
sleep 3
docker ps | grep insecure
```

**Expected output:**
```
CONTAINER ID   IMAGE             COMMAND      ...   PORTS
a1b2c3d4e5f6   insecure-os-lab   "/bin/bash..." ...   0.0.0.0:8080->80/tcp, 0.0.0.0:2222->22/tcp
```

The container is now running with two exposed ports: nginx on 8080 and SSH on 2222. Both services run as root inside the container.

📸 **Screenshot checkpoint 13b-start:** Capture `docker ps` output confirming the container is running with the exposed ports.

---

## Part 2 — Security Assessment

A systematic security assessment examines the running system across all vulnerability categories. The goal is to **document** every finding before touching anything — changes during an assessment can destroy forensic evidence or mask related vulnerabilities.

### Step 2.1 — Initial audit

```bash
docker exec insecure-system bash -c "
echo '=== 1. Process user ==='
id

echo '=== 2. SUID binaries (unexpected) ==='
find / -perm -4000 -type f 2>/dev/null | grep -v proc | grep -v '/usr/bin/passwd\|/usr/bin/su\|/usr/bin/mount\|/usr/bin/umount\|/usr/bin/newgrp\|/usr/bin/chsh\|/usr/bin/gpasswd\|/usr/bin/chfn'

echo '=== 3. World-writable dirs ==='
find /var/www -perm -0002 -type d 2>/dev/null

echo '=== 4. SSH root login ==='
grep PermitRootLogin /etc/ssh/sshd_config | grep -v '^#'

echo '=== 5. Weak password (webapp:abc hashed) ==='
grep webapp /etc/shadow | cut -d: -f2 | cut -c1-6

echo '=== 6. IP forwarding ==='
cat /proc/sys/net/ipv4/ip_forward

echo '=== 7. Network exposure ==='
ss -tlnp 2>/dev/null"
```

**Expected output (all vulnerabilities visible):**
```
=== 1. Process user ===
uid=0(root) gid=0(root) groups=0(root)    ← running as root

=== 2. SUID binaries (unexpected) ===
/usr/bin/python3.10                        ← SUID python3!

=== 3. World-writable dirs ===
/var/www/html                              ← world-writable

=== 4. SSH root login ===
PermitRootLogin yes                        ← root SSH enabled

=== 5. Weak password (webapp:abc hashed) ===
$y$j9T                                     ← short hash prefix

=== 6. IP forwarding ===
1                                          ← forwarding enabled

=== 7. Network exposure ===
tcp  LISTEN  0.0.0.0:80   sshd, nginx...  ← both services exposed
```

📸 **Screenshot checkpoint 13b:** Capture the complete initial audit output showing all six vulnerability categories.

---

## Part 3 — Apply Hardening

Remediate each vulnerability in sequence. After each fix, mark it off in your vulnerability table.

### Step 3.1 — Vulnerability #2: Remove SUID from python3

A SUID `python3` is a complete privilege escalation bypass — anyone who can run `python3` can trivially execute arbitrary code as root:

```python
python3 -c "import os; os.setuid(0); os.system('/bin/bash')"
```

```bash
docker exec insecure-system bash -c "
find /usr/bin -name 'python3*' -perm -4000 2>/dev/null
find /usr/bin -name 'python3*' -perm -4000 -exec chmod u-s {} \; 2>/dev/null
find /usr/bin -name 'python3*' -perm -4000 2>/dev/null || echo 'SUID removed from python3'"
```

**Expected output:**
```
/usr/bin/python3.10        ← found before
SUID removed from python3  ← gone after
```

📸 **Screenshot checkpoint 13c:** Capture the before (python3 found) and after (SUID removed) output.

---

### Step 3.2 — Vulnerability #3: Fix world-writable web directory

A world-writable web root (`chmod 777`) allows any process running on the server — regardless of user — to modify, replace, or delete web content. This enables web defacement and malicious file injection.

```bash
docker exec insecure-system bash -c "
ls -la /var/www/
chmod 755 /var/www/html
ls -la /var/www/"
```

**Expected output:**
```
drwxrwxrwx 2 root root 4096 ... html    ← world-writable before
drwxr-xr-x 2 root root 4096 ... html    ← 755 after (owner write only)
```

📸 **Screenshot checkpoint 13d:** Capture the `ls -la /var/www/` output before (777) and after (755).

---

### Step 3.3 — Vulnerability #4: Disable SSH root login

Allowing root to log in directly via SSH eliminates one layer of protection. Best practice is to require users to log in as themselves and then `sudo` — creating an audit trail of who performed which privileged actions.

```bash
docker exec insecure-system bash -c "
grep PermitRootLogin /etc/ssh/sshd_config
sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
grep PermitRootLogin /etc/ssh/sshd_config
kill -HUP \$(pgrep -f 'sshd -D') 2>/dev/null && echo 'SSH config reloaded'"
```

**Expected output:**
```
PermitRootLogin yes            ← before
PermitRootLogin no             ← after
SSH config reloaded
```

📸 **Screenshot checkpoint 13e:** Capture both `grep PermitRootLogin` outputs and the "SSH config reloaded" confirmation.

---

### Step 3.4 — Vulnerability #5: Strengthen the webapp password

The password `abc` is a single dictionary word that would be cracked in milliseconds by any password cracking tool. A strong password should be 12+ characters, mixing uppercase, lowercase, numbers, and symbols.

```bash
docker exec insecure-system bash -c "
echo 'webapp:Str0ng!P@ssw0rd99' | chpasswd
grep webapp /etc/shadow | cut -d: -f2 | cut -c1-8
echo 'Password strengthened'"
```

**Expected output:**
```
$y$j9T$L     ← longer, more complex hash prefix confirms new password
Password strengthened
```

📸 **Screenshot checkpoint 13f-password:** Capture the hash prefix change confirming the password update.

---

### Step 3.5 — Vulnerability #6: Network hardening

Disable IP forwarding and ICMP redirects per CIS controls 3.2.1–3.2.3, and enable martian packet logging as an additional detection control:

```bash
docker exec insecure-system bash -c "
echo 0 > /proc/sys/net/ipv4/ip_forward
echo 0 > /proc/sys/net/ipv4/conf/all/accept_redirects
echo 0 > /proc/sys/net/ipv4/conf/all/send_redirects
echo 1 > /proc/sys/net/ipv4/conf/all/log_martians
echo 'Network hardened:'
echo 'ip_forward:' && cat /proc/sys/net/ipv4/ip_forward
echo 'accept_redirects:' && cat /proc/sys/net/ipv4/conf/all/accept_redirects"
```

**Expected output:**
```
Network hardened:
ip_forward: 0
accept_redirects: 0
```

📸 **Screenshot checkpoint 13f:** Capture all network parameter values after hardening.

---

## Part 4 — Post-Hardening Audit

### Step 4.1 — Final automated verification

Run the final audit script to measure the outcome of your hardening work. This produces a quantitative hardening score.

```bash
docker exec insecure-system python3 -c "
import os, subprocess, stat

checks = []
def check(name, passed, detail=''):
    checks.append(passed)
    print(f'{chr(9989) if passed else chr(10060)}  {name}' + (f' ({detail})' if detail else ''))

# 1. SUID python3 removed
r = subprocess.run(['find','/usr/bin','-name','python3*','-perm','-4000'], capture_output=True, text=True)
check('SUID python3 removed', not r.stdout.strip(), r.stdout.strip()[:40] or 'none found')

# 2. Web dir not world-writable
st = os.stat('/var/www/html')
check('/var/www/html not world-writable', not bool(st.st_mode & stat.S_IWOTH), oct(stat.S_IMODE(st.st_mode)))

# 3. SSH root disabled
r = subprocess.run(['grep','PermitRootLogin','/etc/ssh/sshd_config'], capture_output=True, text=True)
check('SSH root login disabled', 'no' in r.stdout.lower(), r.stdout.strip())

# 4. IP forwarding off
fwd = open('/proc/sys/net/ipv4/ip_forward').read().strip()
check('IP forwarding disabled', fwd == '0', fwd)

# 5. ICMP redirects off
redir = open('/proc/sys/net/ipv4/conf/all/accept_redirects').read().strip()
check('ICMP redirects disabled', redir == '0', redir)

# 6. /tmp sticky bit
check('/tmp sticky bit', bool(os.stat('/tmp').st_mode & stat.S_ISVTX))

# 7. /etc/passwd permissions
check('/etc/passwd perms 644', oct(stat.S_IMODE(os.stat('/etc/passwd').st_mode)) == '0o644')

passed = sum(checks)
print(f'\nFinal: {passed}/{len(checks)} checks passed')
print(f'Hardening score: {int(passed/len(checks)*100)}/100')
"
```

**Expected output after hardening:**
```
✅  SUID python3 removed (none found)
✅  /var/www/html not world-writable (0o755)
✅  SSH root login disabled (PermitRootLogin no)
✅  IP forwarding disabled (0)
✅  ICMP redirects disabled (0)
✅  /tmp sticky bit
✅  /etc/passwd perms 644

Final: 7/7 checks passed
Hardening score: 100/100
```

📸 **Screenshot checkpoint 13g:** Capture the final audit output showing all checks passed and the hardening score.

---

### Step 4.2 — Cleanup

```bash
docker stop insecure-system && docker rm insecure-system
docker rmi insecure-os-lab
rm -rf /tmp/scia360cap
docker system prune -f
```

---

## Assessment

### Screenshot Checklist

| ID | Description | Points |
|----|-------------|--------|
| **13a** | Docker build success with image tag | 3 |
| **13b** | Initial audit showing all 6+ vulnerability categories | 6 |
| **13c** | SUID removed from `python3` (before and after) | 4 |
| **13d** | `/var/www/html` permission fixed (777 → 755) | 4 |
| **13e** | `PermitRootLogin` changed from `yes` to `no` | 4 |
| **13f** | Network parameters hardened (ip_forward, accept_redirects = 0) | 4 |
| **13g** | Final audit with score (ideally 100/100) | 5 |
| | **Screenshot subtotal** | **30** |

!!! tip "Grading Rubric"
    | Component | Points |
    |-----------|--------|
    | Screenshots + vulnerability table (complete all 6 rows) | 30 |
    | Hardening correctly applied (verified by instructor replication) | 20 |
    | Final audit score (pro-rated: 100/100 = 20pts, 85/100 = 17pts, etc.) | 20 |
    | Final reflection essay (400–500 words, all 4 prompts addressed) | 30 |
    | **Total** | **100** |

---

### Vulnerability Table *(complete and submit)*

Complete the "Fixed?" column and add a one-sentence explanation of how each fix reduces risk:

| # | Vulnerability | Severity | Chapter | Fixed? | How the Fix Reduces Risk |
|---|--------------|----------|---------|--------|--------------------------|
| 1 | Runs as root (no `USER` directive) | High | Ch.6 Capabilities | ☐ | |
| 2 | SUID `python3` | High | Ch.4 FS Security | ☐ | |
| 3 | World-writable `/var/www/html` | High | Ch.4 FS Security | ☐ | |
| 4 | SSH root login enabled | Critical | Ch.5 Authentication | ☐ | |
| 5 | Weak `webapp` password (`abc`) | Critical | Ch.5 Authentication | ☐ | |
| 6 | IP forwarding enabled | Medium | Ch.12 Linux Architecture | ☐ | |

---

### Final Reflection Essay

Write a **400–500 word essay** addressing **all four** of the following prompts. This essay demonstrates your ability to synthesize SCIA-360 concepts rather than simply execute commands.

---

**Prompt 1 — Vulnerability Ranking**

Rank the six vulnerabilities from most to least severe and justify your ranking. Consider: which vulnerability is most likely to be discovered and exploited by an external attacker with no prior access? Which vulnerability would cause the greatest damage if exploited? Which single remediation provides the biggest security improvement per effort invested?

---

**Prompt 2 — Defense in Depth**

Describe how the OS security concepts from SCIA-360 — **namespaces, capabilities, seccomp, file permissions, authentication hardening, and logging** — work together as complementary layers of defense. Define *defense in depth* as a security architecture principle. Explain why a single strong control (e.g., "the container is behind a firewall") is insufficient if inner layers are misconfigured, using the vulnerabilities in this lab as examples.

---

**Prompt 3 — Hardened Docker Run Command**

This container currently runs with default Docker security settings and as the root user inside the container. Using the Docker security options below, write a **complete hardened `docker run` command** that would significantly reduce the attack surface. Briefly explain what each option does.

Options to use (minimum — use all of them):

| Option | Purpose |
|--------|---------|
| `--user 1000:1000` | Run as non-root user |
| `--cap-drop ALL` | Drop all Linux capabilities |
| `--cap-add NET_BIND_SERVICE` | Re-add only what nginx needs |
| `--read-only` | Mount root filesystem read-only |
| `--tmpfs /tmp:rw,nosuid,noexec` | Writable tmp without SUID/exec |
| `--security-opt no-new-privileges` | Prevent privilege escalation |
| `--security-opt seccomp=/path/to/profile.json` | Restrict system calls |

---

**Prompt 4 — Professional Recommendations**

You have been hired as a security consultant by a startup that is deploying their first containerized web application to AWS. Based on everything you learned in SCIA-360, provide your **top three OS-level security recommendations** for their deployment. For each recommendation:

- State the recommendation clearly
- Explain the threat it mitigates
- Describe how they would implement it
- Identify one metric or check they could use to verify compliance

Your recommendations should reflect real-world priorities — things a reasonable security budget and engineering team can actually accomplish — not a wish list of perfect security.

---

!!! tip "Essay Grading Criteria"
    | Criterion | Description | Points |
    |-----------|-------------|--------|
    | **Completeness** | All four prompts addressed with sufficient depth | 10 |
    | **Technical accuracy** | Concepts correctly explained with appropriate terminology | 10 |
    | **Synthesis** | Demonstrates integration of SCIA-360 topics rather than isolated recall | 5 |
    | **Professionalism** | Clear writing, logical structure, appropriate length (400–500 words) | 5 |
    | **Total essay** | | **30** |
