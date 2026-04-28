---
title: "Lab 02 — Process Security: Credentials, /proc Inspection & Signals"
course: SCIA-360
topic: Process Management Security
chapter: 2
difficulty: "⭐ Beginner"
duration: "45–60 minutes"
tags:
  - linux
  - proc
  - processes
  - credentials
  - namespaces
  - environment-variables
---

# Lab 02 — Process Security: Credentials, /proc Inspection & Signals

| Field | Details |
|---|---|
| **Course** | SCIA-360 — Operating System Security |
| **Topic** | Process Management Security |
| **Chapter** | 2 |
| **Difficulty** | ⭐ Beginner |
| **Estimated Time** | 45–60 minutes |
| **Environment** | Docker — `ubuntu:22.04` |

---

## Overview

Every running process on Linux carries a security context: real and effective UIDs, GIDs, supplementary groups, and capability sets. The kernel exposes all of this through `/proc/PID/status`. In this lab you will inspect process credentials directly from `/proc`, observe how credentials are inherited when a parent spawns a child, discover how environment variables passed to processes can be read by any root process via `/proc/PID/environ`, and verify that Docker's PID namespace isolation prevents containers from seeing each other's processes.

By the end of this lab you will understand:

- What fields in `/proc/PID/status` represent a process's security context
- How credential inheritance works and why it matters for privilege management
- Why passing secrets via environment variables is a security anti-pattern
- How Linux PID namespaces enforce process isolation between containers

!!! warning "Container environment"
    All commands run inside a throwaway Docker container unless explicitly noted as host commands. Do not skip the cleanup step at the end.

---

## Prerequisites

- Completed Lab 01
- Comfortable with basic bash: variable expansion, backgrounding (`&`), `su`
- Chapter 2 reading on process lifecycle and credentials

---

## Part 1 — Process Credentials via /proc

### Step 1.1 — Start the Container and Install Tools

```bash
docker run --rm -it ubuntu:22.04 bash
```

```bash
apt-get update -qq && apt-get install -y -qq procps 2>/dev/null
```

All remaining commands in Parts 1–3 run inside this container.

---

### Step 1.2 — Inspect Your Own Process Credentials

```bash
echo "My PID: $$"
cat /proc/$$/status | grep -E 'Name|Pid|PPid|Uid|Gid|VmRSS|Threads'
```

**Expected output:**

```
Name:   bash
Pid:    1
PPid:   0
Uid:    0    0    0    0
Gid:    0    0    0    0
VmRSS:  4096 kB
Threads: 1
```

**Uid field format:** `real  effective  saved-set  filesystem`

| UID Field | Meaning |
|---|---|
| Real UID | Who actually owns the process (who launched it) |
| Effective UID | Used for permission checks — can differ for SUID binaries |
| Saved-set UID | Stored during `exec()` to allow privilege dropping and restoration |
| Filesystem UID | Used for filesystem access checks (Linux-specific) |

!!! tip "Why four UIDs?"
    The distinction between real and effective UID is what makes SUID binaries work. A normal user (real UID 1000) running `/usr/bin/passwd` will have an effective UID of 0 (root) — allowing it to write `/etc/shadow` — while the real UID remains 1000.

📸 **Screenshot checkpoint 02a** — Capture `/proc/$$/status` output showing Name, Pid, PPid, Uid, and Gid fields.

---

### Step 1.3 — Create a Non-Root User and Compare Credentials

```bash
useradd -m alice
su alice -s /bin/bash -c 'echo "My UID:"; cat /proc/$$/status | grep -E "Uid|Gid"'
```

**Expected output:** All four Uid fields show `1000` — alice's UID. Compare this to the root shell where all four fields were `0`.

!!! tip "Default UID assignment"
    `useradd` assigns the next available UID starting at 1000 on most Linux distributions. UIDs 0–999 are reserved for system accounts. This is why the first manually created user is typically UID 1000.

📸 **Screenshot checkpoint 02b** — Capture alice's credential output showing UID=1000.

---

## Part 2 — Process Hierarchy and Inheritance

### Step 2.1 — Inspect a Background Process

```bash
sleep 300 &
SLEEP_PID=$!
echo "sleep PID: $SLEEP_PID"
cat /proc/$SLEEP_PID/status | grep -E 'Name|Pid|PPid|Uid'
ls -la /proc/$SLEEP_PID/exe
cat /proc/$SLEEP_PID/cmdline | tr '\0' ' ' && echo
```

**Expected output:**

- `Name: sleep`
- `PPid:` matches the bash shell's PID (`$$`)
- `Uid: 0 0 0 0` — inherited from parent bash (root)
- `exe -> /usr/bin/sleep`
- `cmdline: sleep 300`

!!! tip "Credential inheritance"
    When a process calls `fork()`, the child inherits an **exact copy** of the parent's credentials. This includes real UID, effective UID, all GIDs, and the full capability set. A privileged parent spawning an untrusted child inadvertently grants that child all its privileges unless it explicitly drops them with `setuid()` before executing untrusted code.

📸 **Screenshot checkpoint 02c** — Capture the sleep process inspection showing PPid, Uid, exe, and cmdline.

---

### Step 2.2 — File Descriptor Inheritance

```bash
ls -la /proc/$SLEEP_PID/fd
```

**Expected output:** File descriptors `0`, `1`, and `2` — stdin, stdout, and stderr — pointing to the same terminal as the parent shell. The child inherited the parent's open file table.

!!! tip "FD inheritance and security"
    A child process inherits all open file descriptors from its parent unless they are marked `O_CLOEXEC` (close-on-exec). This is why long-running daemons that `fork()` to spawn children should mark sensitive file descriptors (e.g., database connections, private keys) as `O_CLOEXEC` — otherwise every child process can read and write them.

---

### Step 2.3 — Kill the Process and Observe /proc Cleanup

```bash
kill $SLEEP_PID
ls /proc/$SLEEP_PID/ 2>&1 || echo "Process gone — /proc entry removed"
```

**Expected output:** An error message indicating no such file or directory, followed by "Process gone — /proc entry removed".

!!! tip "/proc is purely dynamic"
    `/proc` is a virtual filesystem backed entirely by kernel memory. There are no files on disk. When a process terminates, the kernel immediately removes its `/proc/PID` directory. This is why you cannot forensically analyze a dead process through `/proc` — the information is gone the moment the process exits.

📸 **Screenshot checkpoint 02d** — Capture the `ls /proc/$SLEEP_PID` error confirming the entry is gone.

---

## Part 3 — Environment Variables as a Security Risk

### Step 3.1 — Set Sensitive Environment Variables

```bash
export SECRET_TOKEN="api-key-abc123"
export DB_PASSWORD="supersecret"
env | grep -E 'SECRET|PASSWORD'
```

This simulates a common (but insecure) pattern: passing secrets to applications via environment variables.

---

### Step 3.2 — Read Environment Variables via /proc

```bash
cat /proc/$$/environ | tr '\0' '\n' | grep -E 'SECRET|PASSWORD|TOKEN'
```

**Expected output:**

```
SECRET_TOKEN=api-key-abc123
DB_PASSWORD=supersecret
```

!!! warning "Critical security finding"
    `/proc/PID/environ` exposes the **complete environment** of any process to:

    - The process owner itself
    - Any process running as **root**

    In a shared container environment where multiple services run as root, any service that is compromised can read the secrets of every other root-owned process through `/proc`. This makes environment variable secret injection fundamentally unsafe in multi-service or multi-tenant environments.

📸 **Screenshot checkpoint 02e** — Capture the `/proc/PID/environ` output revealing both secrets.

---

### Step 3.3 — Safer Secret Handling Alternatives

```bash
echo 'WORST:   ENV instructions in Dockerfile — visible in image layers and history'
echo 'BAD:     Passing secrets as -e flags to docker run — visible in /proc/PID/environ'
echo 'BETTER:  Mount secrets as files with chmod 600, readable only by target user'
echo 'BEST:    Use tmpfs-backed secret mounts (Docker Swarm secrets / Kubernetes Secrets)'
```

!!! tip "Docker secrets vs. environment variables"
    Docker Swarm and Kubernetes both provide a secrets mechanism that mounts the secret value as a file in a tmpfs (RAM-only) mount at a well-known path. The file is only readable by the container's designated user, is never written to disk, and does not appear in `/proc/PID/environ`.

---

## Part 4 — Process Isolation Between Containers

### Step 4.1 — Exit the First Container

Type `exit` to leave the container, returning to your host shell.

```bash
exit
```

### Step 4.2 — Launch Two Containers and Verify Isolation

Run these commands on your **host**:

```bash
docker run -d --name proc-b ubuntu:22.04 sleep 3600
docker run --rm ubuntu:22.04 bash -c 'ps aux'
docker stop proc-b && docker rm proc-b
```

**Expected output:** The second container's `ps aux` output shows **only its own process** (`ps` itself, or `bash` as PID 1). The `sleep 3600` process running in `proc-b` is completely invisible.

!!! tip "PID namespaces"
    Linux PID namespaces give each container a private PID number space. From inside a container, the namespace appears to contain only its own processes starting from PID 1. The host kernel manages all PIDs globally, but the namespace boundary prevents containers from enumerating or signaling each other's processes. This is the kernel mechanism that underpins Docker's process isolation guarantee.

!!! warning "Namespace ≠ security boundary alone"
    PID namespaces prevent *enumeration* of other containers' processes, but a container running with `--privileged` or with certain Linux capabilities can break out of the namespace boundary. Namespace isolation is one layer of defense, not the complete story.

📸 **Screenshot checkpoint 02f** — Capture the second container's `ps aux` output showing only its own process(es).

---

## Cleanup

```bash
docker system prune -f
```

---

## Assessment

### Screenshot Checklist

| ID | Description | Points |
|---|---|---|
| **02a** | `/proc/$$/status` output — Name, Pid, PPid, Uid, Gid fields visible | 7 |
| **02b** | alice's credentials — Uid and Gid showing `1000` | 6 |
| **02c** | sleep process inspection — PPid, Uid, exe symlink, cmdline | 7 |
| **02d** | `/proc` entry gone after kill — error message visible | 5 |
| **02e** | Secrets exposed via `/proc/PID/environ` — both variables visible | 8 |
| **02f** | Isolated process list — second container shows only its own processes | 7 |
| | **Screenshot Total** | **40** |

---

### /proc Field Annotation Exercise

Complete the following table based on your observations during the lab (20 points). For each `/proc` field, write one sentence describing what it contains and its security relevance.

| `/proc` File / Field | What It Contains | Security Relevance |
|---|---|---|
| `/proc/PID/status` → `Uid` | | |
| `/proc/PID/status` → `PPid` | | |
| `/proc/PID/exe` | | |
| `/proc/PID/cmdline` | | |
| `/proc/PID/fd/` | | |
| `/proc/PID/environ` | | |

---

### Reflection Questions

Answer each question in 3–5 sentences. (40 points — 10 points each)

**Question 1**

In Step 3.2, you read `SECRET_TOKEN` and `DB_PASSWORD` from `/proc/PID/environ` as root. What does this mean for the common practice of injecting database credentials into containerized applications via environment variables (e.g., `docker run -e DB_PASSWORD=...`)? Describe the specific threat scenario in a multi-service environment running as root, and name a safer alternative.

---

**Question 2**

The `sleep` process inherited UID 0 from its parent bash shell. Define "process credential inheritance" in your own words. What specific security risk does it create when a privileged parent process (e.g., a web server running as root) uses `fork()` to spawn an untrusted child process such as a user-supplied plugin or script? What system call should the parent use before executing untrusted code to mitigate this risk?

---

**Question 3**

After you killed the `sleep` process, its `/proc/PID` directory disappeared immediately — no cleanup was needed. Is `/proc` a real filesystem stored on disk? Explain what type of filesystem it is, where its data comes from, and what this tells you about the purpose and limitations of `/proc` as a forensic tool for investigating crashed or killed processes.

---

**Question 4**

In Part 4, a container running alongside yours could not see your processes via `ps aux`. Name the specific Linux kernel feature that provides this isolation. Then describe one concrete real-world scenario — for example in a cloud hosting or CI/CD environment — where this isolation is important for security, and explain what could go wrong if this isolation did not exist.

---

### Grading Rubric

| Component | Points |
|---|---|
| Screenshots (6 × weighted) | 40 |
| `/proc` field annotation exercise | 20 |
| Reflection questions (4 × 10) | 40 |
| **Total** | **100** |

!!! tip "Reflection grading criteria"
    Full credit requires: (1) a correct technical claim, (2) a specific explanation of the mechanism, and (3) a security implication or real-world consequence. Restating the lab procedure without explanation receives no more than 5/10.
