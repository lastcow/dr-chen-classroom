---
title: "Lab 08 — chroot Jail: Filesystem Isolation the Old Way"
course: SCIA-360
topic: Sandboxing & Isolation
chapter: 8
difficulty: "⭐⭐"
time: "45–60 min"
reading: "Chapter 8 — Sandboxing and Isolation Primitives"
---

# Lab 08 — chroot Jail: Filesystem Isolation the Old Way

| | |
|---|---|
| **Course** | SCIA-360 OS Security |
| **Topic** | Sandboxing & Isolation |
| **Chapter** | 8 |
| **Difficulty** | ⭐⭐ Intermediate |
| **Estimated Time** | 45–60 minutes |
| **Prerequisites** | Labs 05–07 completed; Docker installed and running |

---

## Overview

`chroot` — *change root* — is the original Unix filesystem isolation mechanism. It changes what a process sees as `/`, preventing it from accessing paths outside the designated jail directory. Introduced in Unix Version 7 (1979), it predates containers by four decades and is still in active use today.

In this lab you will:

- Build a functional `chroot` jail from scratch, including shared library dependencies
- Enter the jail and verify filesystem isolation
- Attempt (and understand why you cannot succeed from inside) to escape
- Identify the fundamental limitations of `chroot` as a security boundary
- Compare `chroot` to modern container isolation and understand why Docker uses namespaces

!!! tip "Grading Rubric"
    | Component | Points |
    |-----------|--------|
    | Screenshots (08a – 08f) | 40 pts |
    | chroot vs. container comparison table (completed) | 20 pts |
    | Reflection questions (4 × 10 pts) | 40 pts |
    | **Total** | **100 pts** |

---

## Part 1 — Building the Jail

### Step 1.1 — Launch the Lab Container

```bash
docker run --rm -it ubuntu:22.04 bash
```

All steps in Parts 1–4 run **inside** this container. The Docker container is your "host" for purposes of this lab; the chroot jail will be constructed inside it.

---

### Step 1.2 — Create the Jail Directory Structure

```bash
mkdir -p /jail/{bin,lib,lib64,etc,tmp}
ls /jail/
```

**Expected output:** `bin  etc  lib  lib64  tmp`

The jail needs the same directory structure that a minimal Linux root filesystem requires. Programs expect to find libraries in `/lib` and `/lib64`, executables in `/bin`.

---

### Step 1.3 — Copy Binaries Into the Jail

```bash
cp /bin/bash /jail/bin/
cp /bin/ls   /jail/bin/
cp /bin/cat  /jail/bin/
cp /bin/pwd  /jail/bin/
```

We copy only four binaries. Anything not explicitly copied will be unavailable inside the jail — this is intentional. The minimal surface area is part of the security model.

---

### Step 1.4 — Resolve and Copy Shared Library Dependencies

ELF binaries on Linux are dynamically linked — they do not contain all their code. At runtime the dynamic linker (`ld-linux`) finds and loads shared libraries. Inside the jail, the library paths point to the jail's `/lib`, so those files must exist there.

```bash
ldd /bin/bash | grep -oP '/[^ ]+\.so[^ ]*' | sort -u | xargs -I{} cp {} /jail/lib/ 2>/dev/null
ldd /bin/ls   | grep -oP '/[^ ]+\.so[^ ]*' | sort -u | xargs -I{} cp {} /jail/lib/ 2>/dev/null
ldd /bin/cat  | grep -oP '/[^ ]+\.so[^ ]*' | sort -u | xargs -I{} cp {} /jail/lib/ 2>/dev/null
cp /lib64/ld-linux-x86-64.so.2 /jail/lib64/ 2>/dev/null
echo "Library count: $(ls /jail/lib/ | wc -l)"
```

**Expected output:** `Library count: 15` to `Library count: 25` depending on the Ubuntu version and library sharing between binaries.

`ldd` lists runtime library dependencies. The `grep -oP` extracts just the full filesystem paths. `xargs cp` copies each one into the jail.

!!! warning "The dynamic linker is critical"
    `/lib64/ld-linux-x86-64.so.2` is the dynamic linker itself — the first program that runs when you execute any dynamically linked binary. Without it in `lib64`, **none** of the copied binaries will execute inside the jail. The copy may silently fail if the path differs on your system — verify with `ls /jail/lib64/`.

---

### Step 1.5 — Add Content and Verify the Structure

```bash
echo 'JAILED: you are isolated from the main filesystem' > /jail/etc/message.txt
ls -la /jail/
```

**Expected output:** A listing showing `bin/`, `etc/`, `lib/`, `lib64/`, `tmp/` with appropriate sizes.

📸 **Screenshot checkpoint 08a:** Full `ls -la /jail/` output showing all five subdirectories and their sizes.

---

## Part 2 — Entering and Testing the Jail

### Step 2.1 — Enter the Jail

```bash
chroot /jail /bin/bash
```

You are now inside the jail. The shell prompt may change. From this point on, the process's root is `/jail` — it cannot see anything outside.

```bash
pwd
ls /
cat /etc/message.txt
```

**Expected output:**

```
/
bin  etc  lib  lib64  tmp
JAILED: you are isolated from the main filesystem
```

`ls /` shows only the jail contents. `/etc/passwd`, `/home`, `/proc`, `/sys` — none of the host filesystem is visible.

📸 **Screenshot checkpoint 08b:** Inside the jail: `ls /` output showing only the five jail directories, and `cat /etc/message.txt` output.

---

### Step 2.2 — Attempt to Escape with `../`

```bash
cd /
cd ../../../
pwd
```

**Expected output:** `pwd` still prints `/`. The kernel enforces the chroot boundary — `..` at the root of a chrooted process points back to the same root, so traversal is impossible at the kernel level.

---

### Step 2.3 — Observe the Limited Environment

```bash
id   2>/dev/null || echo 'id: not available in jail'
ps   2>/dev/null || echo 'ps: not available in jail'
ping 2>/dev/null || echo 'ping: not available in jail'
```

**Expected output:**

```
id: not available in jail
ps: not available in jail
ping: not available in jail
```

Only what we explicitly copied exists in the jail. `id`, `ps`, and `ping` were not copied, so they do not exist at `/bin/id` etc. within the jail's filesystem view.

📸 **Screenshot checkpoint 08c:** All three `not available in jail` lines in the same terminal output.

---

### Step 2.4 — Exit the Jail and Verify Host Access

```bash
exit
```

Back on the host (inside the Docker container):

```bash
pwd
ls /etc/passwd
cat /jail/etc/message.txt
```

**Expected output:** `pwd` shows a path outside the jail (e.g., `/`), `/etc/passwd` exists and is readable, and the jail's `message.txt` is readable from outside — confirming that the host sees everything, including jail contents.

📸 **Screenshot checkpoint 08d:** Post-exit terminal showing `ls /etc/passwd` (exists on host) and `cat /jail/etc/message.txt` readable from outside.

---

## Part 3 — chroot Limitations

### Step 3.1 — Root Can Escape (Conceptual Demonstration)

The most important limitation of `chroot` as a security boundary: **a root process can always escape**.

```bash
chroot /jail /bin/bash -c '
  echo "Inside jail: root is at / but..."
  echo "Key limitation: root (UID 0) can call chroot() again to escape"
  echo "Root inside chroot = not a real security boundary"
  echo "This is why Docker uses namespaces, not just chroot"
'
```

**The escape mechanism:** A root process inside a chroot can:

1. Create a new directory anywhere in the jail
2. Call `chroot()` again to enter that directory as the new root
3. Call `chdir("../../../../etc")` to navigate outside the original jail
4. Now have access to the original host filesystem

This is a documented kernel behaviour, not a bug — `chroot()` was never designed as a security primitive for root processes.

📸 **Screenshot checkpoint 08e:** The four `echo` lines confirming the root escape limitation.

---

### Step 3.2 — `/proc` Is Not Isolated in a Basic chroot

```bash
mkdir -p /jail/proc
chroot /jail /bin/bash -c \
  'ls /proc 2>/dev/null || echo "/proc not mounted — shared with host in real chroot"'
```

**Expected output:** Either an empty listing (proc not mounted) or the message about it not being mounted.

**The security implication:** In a real chroot deployment (not this Docker-within-Docker lab), if an administrator binds `/proc` into the jail for tools like `ps` to work, the chrooted process can **read `/proc/<pid>/` for every host process** — leaking PIDs, command lines, environment variables, and open file descriptors of processes it should not be able to see. chroot provides zero PID namespace isolation.

---

## Part 4 — chroot vs. Container Comparison

### Step 4.1 — Side-by-Side Isolation Comparison

```bash
echo ''
echo '=== What chroot isolates ==='
echo '✓ Filesystem: process sees jail root as /'
echo ''
echo '=== What chroot does NOT isolate ==='
echo '✗ PID namespace: can see host processes via /proc'
echo '✗ Network: same interfaces as host'
echo '✗ IPC: same message queues and semaphores'
echo '✗ User IDs: same UIDs/GIDs as host'
echo '✗ Root escape: root inside can chroot() out'
echo ''
echo '=== What containers add on top of chroot ==='
echo '+ PID namespace: isolated process table'
echo '+ Network namespace: isolated interfaces'
echo '+ Mount namespace: isolated mounts'
echo '+ User namespace: UID remapping'
echo '+ seccomp: syscall filtering'
echo '+ capabilities: privilege reduction'
echo '+ cgroups: resource limits'
```

📸 **Screenshot checkpoint 08f:** Full comparison output with all three sections visible.

---

### Step 4.2 — Where chroot Is Still Used Today

```bash
echo 'Real use cases for chroot in modern systems:'
echo '1. dpkg/apt build environments (debootstrap creates chroot build roots)'
echo '2. System rescue (boot from live CD, chroot into broken OS to repair)'
echo '3. FTP server isolation (vsftpd --chroot_local_user option)'
echo '4. DNS servers (BIND can chroot to /var/named for log/config isolation)'
echo '5. Base layer concept in Docker (mount namespaces extend the chroot idea)'
```

chroot is not obsolete — it is still a valid tool for its original purpose of **filesystem path isolation in trusted environments**. The key is understanding what it does not protect against.

---

### chroot vs. Container Isolation Table

Complete and submit this table with your lab report:

| Isolation Property | chroot Jail | Docker Container |
|-------------------|-------------|-----------------|
| Filesystem root (`/`) isolation | ✅ Yes | ✅ Yes (mount namespace) |
| PID namespace — process visibility | ❌ No | ✅ Yes |
| Network namespace — interface isolation | ❌ No | ✅ Yes |
| IPC namespace — semaphores, message queues | ❌ No | ✅ Yes |
| User namespace — UID remapping | ❌ No | ✅ Yes (optional) |
| Root process escape prevention | ❌ No | ✅ Partial (capabilities + seccomp) |
| Syscall filtering | ❌ No | ✅ Yes (seccomp) |
| Resource limits (CPU, memory) | ❌ No | ✅ Yes (cgroups) |
| Capability reduction | ❌ No | ✅ Yes |

---

## Cleanup

Exit the Docker container (type `exit` if still inside), then prune Docker resources:

```bash
docker system prune -f
```

---

## Assessment

### Screenshot Checklist

| ID | Required Content |
|----|-----------------|
| **08a** | `ls -la /jail/` showing all five subdirectories with sizes |
| **08b** | Inside jail: `ls /` showing only jail contents + `cat /etc/message.txt` output |
| **08c** | All three `not available in jail` messages for `id`, `ps`, `ping` |
| **08d** | After `exit`: `ls /etc/passwd` confirming host filesystem accessible |
| **08e** | The four root-escape limitation echo lines |
| **08f** | Full three-section chroot vs. container comparison output |

---

### Reflection Questions

!!! warning "Submission requirement"
    Answer each question in **complete paragraphs** (minimum 4–6 sentences each). Reference specific commands, system calls, or kernel mechanisms where relevant.

**Q1.** What does `chroot` literally do at the system call level? Explain in terms of the process's view of the filesystem hierarchy. Why did you need to copy shared library files (`.so` files) into the jail in Step 1.4 — why couldn't the jail binaries just use the libraries already present on the host filesystem?

**Q2.** `chroot` does **not** provide network namespace isolation. If you ran a web server inside a chroot jail listening on port 8080, could a process on the host connect to it? Why does the absence of network isolation matter for security sandboxing — what kinds of attacks remain possible against a chrooted service that would be prevented by a full container with network namespace isolation?

**Q3.** Why is `chroot` not a security boundary for root processes? Describe the **specific mechanism** — the sequence of system calls — that allows a root process inside a chroot jail to break out of it. Why does this attack not work for non-root processes?

**Q4.** Docker uses Linux **mount namespaces** to give each container its own filesystem view, which is conceptually similar to `chroot` but substantially more powerful. Based on what you observed in this lab and your knowledge from Labs 06–07, list and explain **three specific security properties** that mount namespaces provide that a plain `chroot` jail cannot.
