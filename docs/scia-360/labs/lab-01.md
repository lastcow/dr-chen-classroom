---
title: "Lab 01 — Exploring OS Security Layers: /proc, Kernel & User Space"
course: SCIA-360
topic: OS Security Introduction
chapter: 1
difficulty: "⭐ Beginner"
duration: "45–60 minutes"
tags:
  - linux
  - proc
  - kernel
  - aslr
  - containers
---

# Lab 01 — Exploring OS Security Layers: /proc, Kernel & User Space

| Field | Details |
|---|---|
| **Course** | SCIA-360 — Operating System Security |
| **Topic** | OS Security Introduction |
| **Chapter** | 1 |
| **Difficulty** | ⭐ Beginner |
| **Estimated Time** | 45–60 minutes |
| **Environment** | Docker — `ubuntu:22.04` |

---

## Overview

The Linux kernel exposes a real-time window into running system state through `/proc` — a virtual pseudo-filesystem that exists only in memory. In this lab you will use `/proc` to examine kernel version information, security-relevant kernel parameters, process state, memory layout, and network settings. You will also observe the fundamental relationship between containers and the host kernel, and see how `/proc` entries are created and destroyed dynamically as processes come and go.

By the end of this lab you will understand:

- What security parameters the kernel exposes via `/proc/sys`
- How process state (PID, UID, memory maps) is represented in `/proc`
- Why containers share the host kernel and what that means for security
- How to read and interpret memory permission flags in `/proc/PID/maps`

!!! warning "Container environment"
    All commands in this lab run inside a **throwaway Docker container**. No changes persist to your host system. Do not skip the cleanup step at the end.

---

## Prerequisites

- Docker installed and running on your workstation
- Basic familiarity with Linux shell commands
- Completed the Chapter 1 reading on OS security architecture

---

## Part 1 — Kernel Version and /proc Parameters

### Step 1.1 — Start the Container

Open a terminal on your host and launch an interactive Ubuntu 22.04 container:

```bash
docker run --rm -it ubuntu:22.04 bash
```

!!! tip "What `--rm` does"
    The `--rm` flag automatically removes the container when you exit. This keeps your Docker environment clean and reinforces that labs are ephemeral — no persistent state.

You should see a root prompt such as `root@<container-id>:/#`. All subsequent commands in Parts 1–4 run **inside this container**.

---

### Step 1.2 — Kernel Version Information

```bash
uname -r
uname -a
cat /proc/version
```

**Expected output:** The kernel version string (e.g., `6.x.x-generic`) and a full build string including the GCC version used to compile the kernel.

!!! tip "Why this matters"
    The kernel version determines which security features are available (e.g., certain ASLR modes, seccomp filters, namespace types). Knowing your kernel version is the first step in any security assessment.

---

### Step 1.3 — Security Kernel Parameters

```bash
cat /proc/sys/kernel/randomize_va_space
cat /proc/sys/kernel/dmesg_restrict
cat /proc/sys/fs/protected_symlinks
cat /proc/sys/fs/protected_hardlinks
```

**Expected output:** `2`, `1`, `1`, `1`

| Parameter | Value | Meaning |
|---|---|---|
| `randomize_va_space` | `2` | Full ASLR — randomizes stack, heap, mmap, and VDSO |
| `dmesg_restrict` | `1` | Non-root users cannot read kernel ring buffer (`dmesg`) |
| `protected_symlinks` | `1` | Prevents symlink-following TOCTOU attacks in world-writable dirs |
| `protected_hardlinks` | `1` | Prevents hard link attacks on files the user does not own |

!!! tip "Hardened defaults"
    Modern Ubuntu ships with all four of these set to their secure values. On older or minimally configured systems you may find `randomize_va_space=0` — a significant security regression.

📸 **Screenshot checkpoint 01a** — Capture the terminal showing all four kernel parameter values.

---

### Step 1.4 — Explore /proc Structure

```bash
ls /proc | head -20
ls /proc/sys/kernel | head -15
```

Notice that numeric entries (e.g., `1`, `7`, `23`) correspond to running process PIDs. The `sys/` subtree exposes tuneable kernel parameters.

📸 **Screenshot checkpoint 01b** — Capture the `/proc` directory listing.

---

## Part 2 — Process Inspection via /proc

### Step 2.1 — Install procps and List Processes

```bash
apt-get update -qq && apt-get install -y -qq procps 2>/dev/null
ps aux
echo "My PID: $$"
echo "Parent PID: $PPID"
```

!!! tip "PID 1 in containers"
    Inside a container, PID 1 is `bash` (or whatever the container's entrypoint is) — **not** `systemd`. Containers use the host kernel's PID namespace with a shifted view. This means there is no init daemon managing services; the container lives and dies with its PID 1 process.

---

### Step 2.2 — Inspect PID 1 via /proc

```bash
cat /proc/1/status | head -15
cat /proc/1/cmdline | tr '\0' ' ' && echo
ls -la /proc/1/fd
ls -la /proc/1/exe
```

**Expected output:**

- `Name: bash` — the process name
- `Uid: 0 0 0 0` and `Gid: 0 0 0 0` — running as root
- Three file descriptors: `0` (stdin), `1` (stdout), `2` (stderr)
- `exe -> /bin/bash` — the executable symlink

!!! tip "/proc/PID/cmdline encoding"
    Arguments in `/proc/PID/cmdline` are separated by null bytes (`\0`). The `tr '\0' ' '` command replaces them with spaces so they are human-readable.

📸 **Screenshot checkpoint 01c** — Capture `/proc/1/status` output showing Name, Uid, and Gid fields.

---

### Step 2.3 — Memory Map of the Current Process

```bash
cat /proc/$$/maps | head -10
```

**Expected output format:**

```
5f3b1000-5f3b2000 r-xp 00000000 fd:01 123456  /bin/bash
7f8a000000-7f8a021000 r--p 00000000 fd:01 789012  /usr/lib/x86_64-linux-gnu/libc.so.6
```

**Column meanings:**

| Column | Description |
|---|---|
| `5f3b1000-5f3b2000` | Virtual address range of this mapping |
| `r-xp` | Permissions: **r**ead, no-**w**rite, e**x**ecute, **p**rivate |
| `00000000` | Offset into the file |
| `fd:01` | Device (major:minor) |
| `123456` | Inode number |
| `/bin/bash` | Backing file (blank = anonymous mapping) |

!!! tip "Permission flags"
    - `r` = readable, `w` = writable, `x` = executable, `-` = denied
    - `p` = private copy-on-write, `s` = shared mapping
    - Code sections are typically `r-x`; data sections `rw-`; stack is `rw-` (NX enforced)

📸 **Screenshot checkpoint 01d** — Capture the memory map with at least 5 lines visible, showing the permission columns.

---

## Part 3 — Network Security Parameters

### Step 3.1 — Read Network /proc Parameters

```bash
cat /proc/sys/net/ipv4/ip_forward
cat /proc/sys/net/ipv4/conf/all/accept_redirects
cat /proc/sys/net/ipv4/conf/all/send_redirects
```

**Expected output:** `0`, `1`, `1`

| Parameter | Value | Security Implication |
|---|---|---|
| `ip_forward` | `0` | Host is not acting as a router — correct for a workstation |
| `accept_redirects` | `1` | Accepts ICMP redirect messages — should be `0` on hardened systems |
| `send_redirects` | `1` | Sends ICMP redirects — should be `0` on hardened systems |

!!! warning "ICMP redirects"
    `accept_redirects=1` means an attacker on the local network could send forged ICMP redirect packets to reroute traffic through a malicious host. Hardened systems and CIS Benchmarks require setting this to `0`.

📸 **Screenshot checkpoint 01e** — Capture all three network parameter values.

---

### Step 3.2 — Modify a Kernel Parameter (Container-Safe)

```bash
cat /proc/sys/kernel/hostname
echo "lab-system" > /proc/sys/kernel/hostname
cat /proc/sys/kernel/hostname
```

**Expected output:** The hostname changes from the container ID to `lab-system`.

!!! tip "/proc is writable by root"
    Writing to `/proc/sys` entries is how `sysctl` works under the hood. This write affects only the running kernel's in-memory state — and because we are in a container, it is limited to this container's namespace. This change does **not** persist after the container exits.

📸 **Screenshot checkpoint 01f** — Capture the before and after hostname values.

---

## Part 4 — Container vs. Host Kernel Relationship

### Step 4.1 — Observe Shared Kernel and cgroup Membership

```bash
cat /proc/version
uname -r
cat /proc/self/cgroup
```

**Expected output:** The kernel version shown inside the container is **identical** to the host kernel version. The `cgroup` file reveals the container's resource control group hierarchy.

!!! warning "Shared kernel — critical security concept"
    Containers do **not** have their own kernel. Every container on a host runs on the **same** kernel. A kernel-level vulnerability (e.g., a privilege escalation CVE) affects all containers simultaneously. This is a fundamental difference from virtual machines, which have fully isolated kernels.

!!! tip "What cgroups control"
    Control groups (`cgroups`) limit and account for CPU, memory, and I/O usage per container. They are a resource management mechanism, not a security isolation mechanism — namespaces provide the security boundary.

📸 **Screenshot checkpoint 01g** — Capture `/proc/version`, `uname -r`, and the cgroup output together.

---

## Cleanup

Exit the container and clean up Docker resources:

```bash
exit
```

```bash
docker system prune -f
```

!!! tip "Always clean up"
    `docker system prune -f` removes stopped containers, dangling images, and unused networks. Running this after every lab keeps your environment tidy and prevents disk space issues.

---

## Assessment

### Screenshot Checklist

Submit all seven screenshots with your lab report. Label each file exactly as shown.

| ID | Description | Points |
|---|---|---|
| **01a** | `/proc` kernel security parameters (`randomize_va_space`, `dmesg_restrict`, `protected_symlinks`, `protected_hardlinks`) | 6 |
| **01b** | `/proc` directory listing (`ls /proc`) | 5 |
| **01c** | `/proc/1/status` showing Name, Uid, Gid fields | 6 |
| **01d** | `/proc/self/maps` memory layout with permission columns visible | 7 |
| **01e** | Network parameters (`ip_forward`, `accept_redirects`, `send_redirects`) | 6 |
| **01f** | Hostname changed via `/proc/sys/kernel/hostname` (before and after) | 5 |
| **01g** | cgroup information alongside kernel version | 5 |
| | **Screenshot Total** | **40** |

---

### Kernel Parameter Analysis Table

Complete the following table in your lab report (20 points):

| Parameter | Path in /proc | Your Observed Value | Secure Value | What It Protects Against |
|---|---|---|---|---|
| ASLR | `/proc/sys/kernel/randomize_va_space` | | `2` | |
| dmesg restrict | `/proc/sys/kernel/dmesg_restrict` | | `1` | |
| Protected symlinks | `/proc/sys/fs/protected_symlinks` | | `1` | |
| Protected hardlinks | `/proc/sys/fs/protected_hardlinks` | | `1` | |
| IP forwarding | `/proc/sys/net/ipv4/ip_forward` | | `0` | |
| Accept redirects | `/proc/sys/net/ipv4/conf/all/accept_redirects` | | `0` | |

---

### Reflection Questions

Answer each question in 3–5 sentences. Substantive, specific answers are required — vague answers receive no credit. (40 points — 10 points each)

**Question 1**

`/proc/sys/kernel/randomize_va_space` was set to `2` in your container. Describe what each of the three possible values (`0`, `1`, `2`) means in terms of which memory regions are randomized. Then explain specifically how full ASLR (value `2`) makes a return-address-overwrite exploit harder compared to a system with ASLR disabled.

---

**Question 2**

You ran `cat /proc/1/cmdline` and found `bash` as PID 1 inside the container. On a normal Linux system (not a container), what process occupies PID 1, and what is its role? Why is this different inside a container, and what security implication arises from not having a proper init process managing child reaping?

---

**Question 3**

The output of `cat /proc/version` showed the same kernel version inside the container as on the host. Suppose a critical kernel privilege-escalation vulnerability (CVE) is disclosed that affects your host's kernel version. Does this vulnerability also affect all containers running on that host? Explain the technical reason why, referencing the relationship between container isolation and the kernel.

---

**Question 4**

You were able to write `lab-system` to `/proc/sys/kernel/hostname` as root inside the container. What does this demonstrate about the boundary between container-level root and the host kernel's namespace for this parameter? How does this relate to the principle of container isolation, and what does it imply about the security posture of running containers as root?

---

### Grading Rubric

| Component | Points |
|---|---|
| Screenshots (7 × weighted) | 40 |
| Kernel parameter analysis table | 20 |
| Reflection questions (4 × 10) | 40 |
| **Total** | **100** |

!!! tip "Reflection grading criteria"
    Full credit requires: (1) a correct technical claim, (2) a specific explanation of the mechanism, and (3) a security implication or real-world consequence. Answers that only restate the lab instructions receive partial credit.
