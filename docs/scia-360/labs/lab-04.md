---
title: "Lab 04 — File System Security: ACLs, SUID, SGID & Sticky Bit"
course: SCIA-360
topic: File System Security
chapter: 4
difficulty: "⭐ Beginner"
duration: "45–60 minutes"
tags:
  - linux
  - suid
  - sgid
  - sticky-bit
  - acl
  - permissions
  - privilege-escalation
---

# Lab 04 — File System Security: ACLs, SUID, SGID & Sticky Bit

| Field | Details |
|---|---|
| **Course** | SCIA-360 — Operating System Security |
| **Topic** | File System Security |
| **Chapter** | 4 |
| **Difficulty** | ⭐ Beginner |
| **Estimated Time** | 45–60 minutes |
| **Environment** | Docker — `ubuntu:22.04` |

---

## Overview

The standard Unix permission model — owner, group, and other with read/write/execute bits — is the foundation of Linux access control. But Linux extends this with three **special permission bits** (SUID, SGID, sticky) and **POSIX ACLs** that enable fine-grained access beyond the nine-bit `rwxrwxrwx` model.

In this lab you will:

1. Identify SUID, SGID, and sticky-bit binaries on a live system
2. Understand *why* `/usr/bin/passwd` is SUID root and why that is legitimate
3. **Demonstrate a privilege escalation** via a misconfigured SUID binary
4. Remediate the misconfiguration and verify access is blocked
5. Use POSIX ACLs to grant per-user permissions that basic `chmod` cannot express

!!! warning "Privilege escalation demonstration"
    Part 2 intentionally demonstrates a real privilege escalation technique using a misconfigured SUID binary. This is performed in an isolated container and is the exact type of finding you would look for in a penetration test or security audit. Never create SUID copies of general-purpose utilities (like `cat`, `cp`, or `bash`) on production systems.

---

## Prerequisites

- Completed Labs 01 and 02
- Chapter 4 reading on Unix permissions and ACLs
- Familiarity with `chmod`, `chown`, and basic user management commands

---

## Part 1 — Special Permission Bits

### Step 1.1 — Start the Container

```bash
docker run --rm -it ubuntu:22.04 bash
```

All commands in Parts 1–3 run inside this container.

---

### Step 1.2 — Identify SUID Binaries

```bash
ls -la /usr/bin/passwd /usr/bin/su /usr/bin/mount
```

**Expected output:**

```
-rwsr-xr-x 1 root root  59976 Mar 22 12:00 /usr/bin/mount
-rwsr-xr-x 1 root shadow 84512 Mar 22 12:00 /usr/bin/passwd
-rwsr-xr-x 1 root root  72072 Mar 22 12:00 /usr/bin/su
```

**The `s` in position 4 (owner execute) is the SUID bit.** Without SUID it would be `x`; with SUID it is `s`.

| Binary | Why It Needs SUID |
|---|---|
| `/usr/bin/passwd` | Must write to `/etc/shadow` (mode 640, owned by root:shadow) to update passwords |
| `/usr/bin/su` | Must call `setuid()` to become another user — requires root privilege |
| `/usr/bin/mount` | Must access block devices and write the mount table — root-only operations |

!!! tip "SUID: effective vs. real UID"
    When a SUID-root binary runs, the process's **effective UID** becomes `0` (root) regardless of who executed it. The **real UID** remains the caller's UID. The binary runs with root's privileges for the duration of its execution. This is why `passwd` can write `/etc/shadow` even when invoked by a user with UID 1000.

📸 **Screenshot checkpoint 04a** — Capture `ls -la` output showing all three binaries with the `s` bit in the owner execute position.

---

### Step 1.3 — Find All SUID Binaries on the System

```bash
find / -perm -4000 -type f 2>/dev/null
```

**Expected output:** A list of SUID binaries including `passwd`, `su`, `mount`, `umount`, `newgrp`, `chsh`, `gpasswd`, and `chfn`.

!!! tip "`-perm -4000` explained"
    The `-perm -4000` flag tells `find` to match any file where the octal permission `4000` (SUID bit) is set, regardless of the other permission bits. The leading `-` means "at least these bits" rather than "exactly these bits." `2>/dev/null` suppresses permission errors for directories we cannot read.

!!! warning "Auditing SUID binaries"
    On a production system, you should maintain a known-good inventory of all SUID binaries (e.g., via `find` output saved to a file, or a tool like `aide`). Any SUID binary not on the approved list is a potential indicator of compromise or misconfiguration.

📸 **Screenshot checkpoint 04b** — Capture the full `find` output listing all SUID binaries.

---

### Step 1.4 — The Sticky Bit on /tmp

```bash
ls -la / | grep tmp
```

**Expected output:**

```
drwxrwxrwt  1 root root 4096 Jan  1 00:00 tmp
```

The `t` at the end of the permission string (`drwxrwxrwt`) is the **sticky bit**.

!!! tip "What the sticky bit does on directories"
    In a world-writable directory (like `/tmp` with `rwxrwxrwx`), any user could delete any other user's files — because write permission on a directory controls who can create and delete entries within it. The sticky bit (`+t`) adds a restriction: **only the file's owner** (or root) can delete or rename a file, even in a world-writable directory.

---

### Step 1.5 — The SGID Bit

```bash
ls -la /usr/bin/newgrp
```

**Expected output:**

```
-rwxr-sr-x 1 root shadow 39344 Mar 22 12:00 /usr/bin/newgrp
```

The `s` in position 7 (group execute) is the **SGID bit**. When set on an executable, the process runs with the **group's** GID rather than the user's primary GID. When set on a **directory**, new files created inside inherit the directory's group rather than the creator's primary group — useful for shared project directories.

---

## Part 2 — SUID Security Risk: Privilege Escalation Demo

### Step 2.1 — Create Users and a Protected File

```bash
useradd -m alice && useradd -m bob
echo 'alice:password' | chpasswd
echo 'bob:password' | chpasswd
echo 'ALICE_SECRET=s3cr3t_project_data' > /home/alice/private.txt
chown alice:alice /home/alice/private.txt
chmod 600 /home/alice/private.txt
```

Verify the permissions:

```bash
ls -la /home/alice/private.txt
```

**Expected:** `-rw------- 1 alice alice ... private.txt` — only alice can read it.

---

### Step 2.2 — Confirm Bob Cannot Read Alice's File

```bash
su bob -s /bin/bash -c 'cat /home/alice/private.txt' 2>&1
```

**Expected output:**

```
cat: /home/alice/private.txt: Permission denied
```

Access control is working correctly at baseline.

---

### Step 2.3 — Simulate an Administrator Mistake: Create a SUID Copy of `cat`

```bash
cp /bin/cat /tmp/suid_cat
chmod u+s /tmp/suid_cat
ls -la /tmp/suid_cat
```

**Expected output:**

```
-rwsr-xr-x 1 root root 43416 ... /tmp/suid_cat
```

!!! warning "This is the mistake"
    Copying a general-purpose file-reading utility (`cat`) and making it SUID root means **anyone** who executes it will have root's effective UID for the duration of the call — and root can read any file on the system. This type of misconfiguration happens in practice when administrators create SUID wrappers for convenience without understanding the security implication.

---

### Step 2.4 — Bob Exploits the Misconfiguration

```bash
su bob -s /bin/bash -c '/tmp/suid_cat /home/alice/private.txt' 2>&1
```

**Expected output:**

```
ALICE_SECRET=s3cr3t_project_data
```

Bob just read a file he had no permission to access. This is **privilege escalation via misconfigured SUID**.

!!! tip "Why this worked"
    When bob executed `/tmp/suid_cat`, the kernel set the process's effective UID to `0` (the file's owner) because the SUID bit was set. The `cat` process ran with root's permissions and could read `/home/alice/private.txt` (mode 600, owned by alice) because root bypasses standard DAC (Discretionary Access Control) checks.

📸 **Screenshot checkpoint 04d** — Capture bob reading alice's file via the SUID `cat` binary. This is the privilege escalation screenshot.

---

### Step 2.5 — Remediate: Remove the SUID Bit

```bash
chmod u-s /tmp/suid_cat
ls -la /tmp/suid_cat
su bob -s /bin/bash -c '/tmp/suid_cat /home/alice/private.txt' 2>&1
```

**Expected output:**

```
-rwxr-xr-x 1 root root 43416 ... /tmp/suid_cat
cat: /home/alice/private.txt: Permission denied
```

SUID removed → privilege escalation blocked.

📸 **Screenshot checkpoint 04e** — Capture the `ls -la` showing the bit removed AND the subsequent permission denied error.

---

## Part 3 — POSIX ACLs: Fine-Grained Access Control

### Step 3.1 — Install the ACL Tools

```bash
apt-get update -qq && apt-get install -y -qq acl 2>/dev/null
```

---

### Step 3.2 — Create a Directory with Restricted Permissions

```bash
mkdir /project
chmod 750 /project
echo 'Project data here' > /project/config.txt
```

Verify neither alice nor bob can access it:

```bash
su alice -s /bin/bash -c 'ls /project/' 2>&1
```

**Expected output:** `ls: cannot open directory '/project/': Permission denied`

!!! tip "Why alice can't access it"
    `/project` has permissions `750`: owner (root) has rwx, group (root) has r-x, others have nothing. Alice and bob are in the "other" category — zero permissions.

---

### Step 3.3 — Grant Alice Access via ACL

```bash
setfacl -m u:alice:rx /project
setfacl -m u:alice:r  /project/config.txt
getfacl /project
getfacl /project/config.txt
```

**Expected output from `getfacl /project`:**

```
# file: project
# owner: root
# group: root
user::rwx
user:alice:r-x
group::r-x
mask::r-x
other::---
```

!!! tip "ACL mask"
    The `mask` entry in a POSIX ACL is the maximum effective permissions for any named user or group entry. It acts as a ceiling — if `mask::r-x`, then no named user or group ACL can grant write access. The mask is automatically calculated when you set ACLs; you can adjust it with `setfacl -m m:rx /project`.

📸 **Screenshot checkpoint 04f** — Capture both `getfacl` outputs showing the `user:alice:r-x` ACL entry.

---

### Step 3.4 — Verify Granular Access: Alice Can, Bob Cannot

```bash
su alice -s /bin/bash -c 'ls /project/ && cat /project/config.txt'
su bob   -s /bin/bash -c 'ls /project/' 2>&1
```

**Expected output:**

```
config.txt
Project data here
ls: cannot open directory '/project/': Permission denied
```

Alice's access was granted via ACL without changing the directory's owner, group, or traditional permission bits. Bob remains blocked because he has no ACL entry and falls into the "other" category (which has `---`).

!!! tip "ACL evaluation order"
    The kernel evaluates ACL entries in this order: (1) owner, (2) named user ACEs, (3) named group ACEs (intersected with mask), (4) owning group, (5) other. The first matching entry wins. This is why alice gets access from her named user entry even though she is not the owner and not in the owning group.

📸 **Screenshot checkpoint 04g** — Capture both `su` commands: alice succeeding and bob being denied.

---

## Cleanup

Exit the container and clean up:

```bash
exit
```

```bash
docker system prune -f
```

---

## Assessment

### Screenshot Checklist

| ID | Description | Points |
|---|---|---|
| **04a** | SUID binaries — `passwd`, `su`, `mount` with `s` in owner execute position | 6 |
| **04b** | `find` output listing all SUID binaries on the system | 5 |
| **04c** | `/tmp` sticky bit — `drwxrwxrwt` visible in `ls -la /` output | 5 |
| **04d** | Bob reads alice's file via SUID cat — privilege escalation demonstrated | 8 |
| **04e** | SUID removed — `ls -la` shows `-rwxr-xr-x` AND subsequent permission denied | 6 |
| **04f** | `getfacl` output showing `user:alice:r-x` ACL entry | 5 |
| **04g** | alice succeeds, bob denied — ACL granularity verified | 5 |
| | **Screenshot Total** | **40** |

!!! tip "Screenshot 04c"
    Screenshot 04c (sticky bit) is captured during Step 1.4. You may go back and capture it as part of your lab walkthrough — it does not require a separate command run.

---

### Special Permission Bits Explanation Table

Complete the following table in your lab report (20 points):

| Bit | Octal | Symbol in `ls` | Where It Appears | Effect on Execution | Security Risk if Misapplied |
|---|---|---|---|---|---|
| SUID | `4000` | `s` (owner exec) | Executables | Process runs as file owner's UID | Any binary that reads/writes/execs can be abused for privilege escalation |
| SGID | `2000` | `s` (group exec) | Executables & directories | Process runs as file's GID / new files inherit directory's group | |
| Sticky | `1000` | `t` (other exec) | Directories | Only file owner can delete their own files | |

Fill in the missing cells for SGID and Sticky, and add one example binary for each from your `find` output.

---

### Reflection Questions

Answer each question in 3–5 sentences. (40 points — 10 points each)

**Question 1**

Explain the SUID bit in your own words. When a regular user (UID 1000) runs `/usr/bin/passwd`, what happens to the process's **effective UID** during execution? Why does `passwd` specifically **require** SUID root to function — name the exact file it must write to and explain why that file has the permissions it does.

---

**Question 2**

In Part 2, you demonstrated privilege escalation via a misconfigured SUID binary. This is a classic attack pattern with a formal name in penetration testing methodology — what is it called? How does a security defender detect unauthorized SUID binaries on a production Linux system? Name at least two methods (e.g., specific commands, file integrity tools, or monitoring approaches).

---

**Question 3**

The sticky bit on `/tmp` prevents a specific attack that would otherwise be possible in a world-writable directory. Describe the attack it prevents: what could a malicious user do to other users' files in `/tmp` if the sticky bit were not set, and give a concrete example scenario (e.g., involving a temporary file created by a script or application). What would the consequence be?

---

**Question 4**

Traditional Unix permissions allow exactly one owner and one owning group per file, with three permission sets (user, group, other). Describe a practical scenario where this model is insufficient — for example, a project directory where alice needs read-write access, bob needs read-only, and charlie needs no access, and none of them share a group. Explain precisely how POSIX ACLs solve this limitation, referencing the specific `setfacl` commands you used and the ACL evaluation order.

---

### Grading Rubric

| Component | Points |
|---|---|
| Screenshots (7 × weighted) | 40 |
| Special permission bits explanation table | 20 |
| Reflection questions (4 × 10) | 40 |
| **Total** | **100** |

!!! tip "Reflection grading criteria"
    Full credit requires: (1) a correct technical claim about the mechanism, (2) a specific real-world example or consequence, and (3) evidence that you understand **why** the feature exists — not just what it does. Copying definitions from man pages without explanation receives partial credit only.
