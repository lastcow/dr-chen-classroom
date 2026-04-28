# Lab 02 — Linux File Permissions & OS Hardening

**Course:** SCIA-120 · Introduction to Secure Computing  
**Topic:** Operating System Security  
**Difficulty:** ⭐ Beginner  
**Estimated Time:** 45–60 minutes  
**Related Reading:** Chapter 4 — Operating System Security Fundamentals

---

## Overview

Access control begins at the operating system level. In this lab you will explore Linux file permissions — the `rwx` permission model, user and group ownership, and the `chmod` command — entirely inside a Docker container. You will then practice hardening a container by removing unnecessary privileges.

---

## Learning Objectives

1. Read and interpret Linux file permission strings (`-rwxr-xr--`).
2. Create users and groups inside a Linux container.
3. Modify file permissions with `chmod` using symbolic and numeric notation.
4. Understand how the principle of **least privilege** maps to file permissions.
5. Run a container with restricted (non-root) privileges.

---

## Prerequisites

- Docker Desktop installed and running.
- Completion of Lab 01 recommended.

---

## Part 1 — Understanding Linux Permissions

### Step 1.1 — Start an Ubuntu Container

```bash
docker run --rm -it ubuntu:22.04 bash
```

### Step 1.2 — Install Utilities

```bash
apt-get update -qq && apt-get install -y -qq sudo
```

### Step 1.3 — Explore Default Permissions

```bash
ls -la /etc/passwd
ls -la /etc/shadow
ls -la /tmp
```

**Observe the permission strings:**

```
-rw-r--r--  /etc/passwd   (world-readable — usernames are public)
-rw-r-----  /etc/shadow   (only root and shadow group can read — passwords are private)
drwxrwxrwt  /tmp          (everyone can write, sticky bit set)
```

📸 **Screenshot checkpoint:** Take a screenshot of all three `ls -la` outputs.

### Step 1.4 — Decode a Permission String

The permission string `-rwxr-xr--` breaks down as:

```
- rwx r-x r--
│  │   │   └── Other:  read only
│  │   └─────── Group:  read + execute
│  └─────────── Owner:  read + write + execute
└────────────── File type: - = file, d = directory
```

---

## Part 2 — Creating Users and Groups

### Step 2.1 — Create Two Users

Still inside the container:

```bash
useradd -m alice
useradd -m bob
```

### Step 2.2 — Create a Group

```bash
groupadd secteam
usermod -aG secteam alice
```

### Step 2.3 — Create a Secret File as Root

```bash
echo "TOP SECRET: Server password is hunter2" > /root/secret.txt
chmod 600 /root/secret.txt
ls -la /root/secret.txt
```

**Expected output:**
```
-rw------- 1 root root  ... /root/secret.txt
```

📸 **Screenshot checkpoint:** Take a screenshot of the `ls -la` showing `600` permissions.

### Step 2.4 — Try to Read It as Alice

```bash
su - alice -c "cat /root/secret.txt"
```

**Expected output:**
```
cat: /root/secret.txt: Permission denied
```

This demonstrates **access control** — Alice cannot read root's private file.

📸 **Screenshot checkpoint:** Take a screenshot of the permission denied error.

---

## Part 3 — Changing Permissions with chmod

### Step 3.1 — Numeric (Octal) Notation

Create a test file:

```bash
echo "Shared report content" > /tmp/report.txt
ls -la /tmp/report.txt
```

Change to `644` (owner read/write, group read, others read):

```bash
chmod 644 /tmp/report.txt
ls -la /tmp/report.txt
```

Change to `660` (owner and group read/write, no access for others):

```bash
chmod 660 /tmp/report.txt
ls -la /tmp/report.txt
```

📸 **Screenshot checkpoint:** Take a screenshot showing the file permissions before and after each `chmod`.

### Step 3.2 — Symbolic Notation

```bash
chmod o-r /tmp/report.txt    # Remove read from others
ls -la /tmp/report.txt
chmod g+x /tmp/report.txt    # Add execute to group
ls -la /tmp/report.txt
```

### Step 3.3 — Make a Script Executable

```bash
echo '#!/bin/bash
echo "Security check complete!"' > /tmp/check.sh

ls -la /tmp/check.sh       # Not executable yet
chmod +x /tmp/check.sh
ls -la /tmp/check.sh       # Now executable
/tmp/check.sh              # Run it
```

📸 **Screenshot checkpoint:** Take a screenshot of the script execution.

Type `exit` to leave the container.

---

## Part 4 — Running Containers with Least Privilege

By default, processes inside Docker containers run as **root**, which is a security risk. A best practice is to run as a non-root user.

### Step 4.1 — See the Default (Root) User

```bash
docker run --rm ubuntu:22.04 whoami
```

**Output:** `root` — this is the default, insecure behavior.

### Step 4.2 — Run as a Non-Root User

```bash
docker run --rm --user 1000:1000 ubuntu:22.04 id
```

**Output:** `uid=1000 gid=1000` — not root (UID 0). This is the principle of **least privilege** in action.

> **Note:** `whoami` may display "cannot find name for user ID 1000" — that is expected, since the container has no named user at UID 1000. The important point is the UID is **not 0 (root)**.

📸 **Screenshot checkpoint:** Take a screenshot showing both `whoami` outputs — root vs non-root.

### Step 4.3 — Demonstrate That Non-Root Cannot Write to Root-Owned Directories

```bash
docker run --rm --user 1000:1000 ubuntu:22.04 bash -c "touch /root/evil.txt"
```

**Expected output:**
```
touch: cannot touch '/root/evil.txt': Permission denied
```

📸 **Screenshot checkpoint:** Take a screenshot of the permission denied error when running as non-root.

### Step 4.4 — Run with Read-Only Filesystem

```bash
docker run --rm --read-only ubuntu:22.04 bash -c "echo test > /tmp/hack.txt"
```

**Expected output:**
```
bash: /tmp/hack.txt: Read-only file system
```

This demonstrates another hardening technique — a read-only container filesystem prevents attackers from writing malicious files.

📸 **Screenshot checkpoint:** Take a screenshot of the read-only error.

---

## Part 5 — Reflection: Permissions Mapping

Fill in the table below as part of your submission:

| Scenario | Appropriate Permission | Why |
|----------|------------------------|-----|
| A public HTML file on a web server | `644` | |
| A private SSH key file | `600` | |
| A shared team directory | `770` | |
| An executable system script | `755` | |

---

## Cleanup

```bash
docker system prune -f
```

---

## Lab Assessment

### Screenshot Submission Checklist

- [ ] `screenshot-02a` — `ls -la` of `/etc/passwd`, `/etc/shadow`, `/tmp`
- [ ] `screenshot-02b` — `/root/secret.txt` with 600 permissions
- [ ] `screenshot-02c` — Permission denied when Alice reads root's file
- [ ] `screenshot-02d` — `chmod` changes on `/tmp/report.txt`
- [ ] `screenshot-02e` — Script execution after `chmod +x`
- [ ] `screenshot-02f` — `whoami` root vs UID 1000
- [ ] `screenshot-02g` — Permission denied writing as non-root
- [ ] `screenshot-02h` — Read-only filesystem error

### Reflection Questions

1. What does the permission string `rwxr-x---` mean for each of the three user categories? Who can do what?
2. Why is it a security risk for all processes inside a container to run as `root`? Give a real-world example of what could go wrong.
3. Explain the **principle of least privilege** in your own words. How did Part 4 of this lab demonstrate it?
4. A database server's configuration file contains credentials. What permission setting would you assign it, and why?

---

!!! tip "Grading Rubric"
    - Screenshots complete and clearly labeled: **40 points**  
    - Permissions mapping table completed: **20 points**  
    - Reflection questions answered thoughtfully: **40 points**  
    - **Total: 100 points**
