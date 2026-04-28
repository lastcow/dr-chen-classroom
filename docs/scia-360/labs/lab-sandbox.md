---
title: "Lab — Sandbox & Isolation: Containment Strategies for Malicious Code"
course: SCIA-360
topic: Sandbox & Isolation
chapter: "11"
difficulty: "⭐⭐"
estimated_time: "75–90 min"
tags:
  - sandbox
  - isolation
  - namespaces
  - seccomp
  - capabilities
  - cgroups
  - containment
---

# Lab — Sandbox & Isolation: Containment Strategies for Malicious Code

| Field | Details |
|-------|---------|
| **Course** | SCIA-360 OS Security |
| **Topic** | Sandbox & Isolation: Containment Strategies for Malicious Code |
| **Chapter** | 11 — Linux Security Architecture In Depth |
| **Difficulty** | ⭐⭐ Intermediate |
| **Estimated Time** | 75–90 minutes |
| **Requires** | Docker Desktop, terminal |

---

## Overview

When malicious code executes on a system it attempts to: read sensitive files, escalate privileges, communicate with attacker-controlled servers, persist via the filesystem, and exhaust resources to deny service. **Sandboxing and isolation** are the OS-level mechanisms that contain malicious code within strict boundaries so that even if it runs, it cannot cause catastrophic harm.

Docker containers are an ideal vehicle for studying these mechanisms because each `docker run` flag directly corresponds to a Linux kernel isolation primitive. In this lab you will observe — with live proof — how five layered containment strategies work together:

| Layer | Mechanism | Kernel Primitive |
|-------|-----------|-----------------|
| Process isolation | PID namespace | `clone(CLONE_NEWPID)` |
| Filesystem isolation | Overlay FS + read-only mounts | OverlayFS, `MS_RDONLY` |
| Syscall filtering | seccomp-BPF | `prctl(PR_SET_SECCOMP)` |
| Privilege restriction | Capabilities | `CAP_*` via `prctl` |
| Resource limits | Memory/CPU caps | cgroups v2 |
| Network isolation | Network namespace | `clone(CLONE_NEWNET)` |
| Privilege escalation prevention | NoNewPrivileges | `prctl(PR_SET_NO_NEW_PRIVS)` |

---

## Learning Objectives

By the end of this lab you will be able to:

1. Explain how Linux namespaces isolate containers from the host and from each other
2. Demonstrate that a container's writes do NOT persist to the host filesystem
3. Apply a custom seccomp profile to block specific dangerous syscalls
4. Show how `--cap-drop=ALL` restricts root inside a container
5. Prove that cgroup resource limits kill runaway processes (OOM scenario)
6. Use `--network=none` to air-gap a malware analysis sandbox
7. Verify that `--no-new-privileges` prevents setuid escalation

---

## Prerequisites

- Docker Desktop installed and running
- A terminal (PowerShell on Windows, Terminal on macOS/Linux)
- Basic Linux command familiarity

---

## Part 1 — PID Namespace Isolation

Linux **PID namespaces** give each container its own process tree starting at PID 1. A malicious process inside the container cannot see, signal, or kill processes on the host.

### Step 1.1 — Launch the sandbox container

```bash
docker run --rm -it ubuntu:22.04 bash
```

### Step 1.2 — Observe the isolated PID namespace

Inside the container, run:

```bash
echo "=== Container process tree ==="
ps aux
echo ""
echo "=== Total visible processes ==="
ps aux | wc -l
```

**Expected output:**
```
=== Container process tree ===
USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root           1  0.0  0.0   4372  3328 ?        Ss   17:58   0:00 bash
root           7  0.0  0.0   7072  3108 ?        R    17:58   0:00 ps aux

=== Total visible processes ===
4
```

The container sees **only 2 processes** (bash + ps) — not the hundreds of processes running on your host. Container PID 1 is the shell, not the host's `systemd` or `init`. A malicious process cannot enumerate host processes, inject into them, or signal them.

Exit the container with `exit` before moving to the next step.

📸 **Screenshot checkpoint Sa:** Capture the `ps aux` output showing only 2–4 processes with PID 1 being `bash`.

---

## Part 2 — Filesystem Isolation

Docker uses **OverlayFS** to give each container an isolated copy-on-write layer over the base image. Writes inside the container never touch the host filesystem.

### Step 2.1 — Simulate malware writing to sensitive locations

This simulates what malware typically does after gaining code execution: modify credential files and plant persistence mechanisms.

```bash
docker run --rm ubuntu:22.04 bash -c '
echo "=== Malware writes inside container ==="
echo "PWNED" > /etc/malicious.txt
cat /etc/malicious.txt
echo ""
ls -la /etc/malicious.txt
echo "File exists and is writable inside the container"
'
```

**Expected output:**
```
=== Malware writes inside container ===
PWNED

-rw-r--r-- 1 root root 6 Apr 20 17:58 /etc/malicious.txt
File exists and is writable inside the container
```

### Step 2.2 — Verify the host is unaffected

After the container exits (it used `--rm`), check the host:

```bash
ls /etc/malicious.txt 2>/dev/null && echo "LEAKED TO HOST" || echo "/etc/malicious.txt does NOT exist on host — isolation works!"
```

**Expected output:**
```
/etc/malicious.txt does NOT exist on host — isolation works!
```

The container's write layer was **discarded on exit**. The host `/etc` is completely untouched.

📸 **Screenshot checkpoint Sb:** Capture both the container output (showing the file was written) and the host verification (showing the file does not exist on the host).

---

## Part 3 — Read-Only Filesystem Enforcement

For malware analysis sandboxes, `--read-only` mounts the entire container filesystem read-only. Even if malicious code runs, it **cannot modify any file** — persistence is structurally impossible.

### Step 3.1 — Run malware in a read-only sandbox

```bash
docker run --rm --read-only ubuntu:22.04 bash -c '
echo "=== Read-only root filesystem ==="
echo "Attempting to write to /etc/cron.d (persistence via cron)..."
echo "malware" > /etc/cron.d/evil 2>&1 || echo "/etc write BLOCKED — read-only filesystem"
echo ""
echo "Attempting to write to /tmp (staging area for malware)..."
echo "test" > /tmp/evil.sh 2>&1 || echo "/tmp write BLOCKED — read-only filesystem"
echo ""
echo "Read operations still work fine:"
cat /etc/os-release | head -3
'
```

**Expected output:**
```
=== Read-only root filesystem ===
Attempting to write to /etc/cron.d (persistence via cron)...
/etc write BLOCKED — read-only filesystem

Attempting to write to /tmp (staging area for malware)...
/tmp write BLOCKED — read-only filesystem

Read operations still work fine:
PRETTY_NAME="Ubuntu 22.04.5 LTS"
NAME="Ubuntu"
VERSION_ID="22.04"
```

### Step 3.2 — Production pattern: read-only root + ephemeral /tmp

Real applications need a writable scratch space. The standard pattern gives `--tmpfs /tmp` while keeping the rest immutable:

```bash
docker run --rm --read-only --tmpfs /tmp ubuntu:22.04 bash -c '
echo "=== Read-only root + tmpfs /tmp (production pattern) ==="
echo ""
echo "Writing to /etc (still blocked):"
echo "evil" > /etc/passwd_mod 2>&1 || echo "/etc write BLOCKED"
echo ""
echo "Writing to /tmp (allowed via ephemeral tmpfs):"
echo "safe scratch space" > /tmp/workfile.txt
cat /tmp/workfile.txt
echo "/tmp write allowed — ephemeral tmpfs, cleared on container stop"
'
```

**Expected output:**
```
=== Read-only root + tmpfs /tmp (production pattern) ===

Writing to /etc (still blocked):
/etc write BLOCKED

Writing to /tmp (allowed via ephemeral tmpfs):
safe scratch space
/tmp write allowed — ephemeral tmpfs, cleared on container stop
```

📸 **Screenshot checkpoint Sc:** Capture the output showing `/etc` writes blocked and `/tmp` writes allowed with `--tmpfs`.

---

## Part 4 — seccomp: Syscall-Level Filtering

**seccomp-BPF** (Secure Computing Mode with Berkeley Packet Filter) lets you define a policy that permits only specific system calls. Docker applies a default seccomp profile that blocks ~44 dangerous syscalls (including `ptrace`, `reboot`, `kexec_load`). You can write custom profiles to block additional calls.

### Step 4.1 — Observe Docker's default seccomp blocking dangerous syscalls

```bash
docker run --rm ubuntu:22.04 bash -c '
echo "=== Default seccomp: mount() is blocked ==="
mount --bind /tmp /mnt 2>&1 || echo "mount BLOCKED by seccomp/capabilities — as expected"
echo ""
echo "=== Kernel module loading is also blocked ==="
apt-get install -qq -y kmod 2>/dev/null
modprobe dummy 2>&1 || echo "modprobe BLOCKED — container cannot load kernel modules"
'
```

**Expected output:**
```
=== Default seccomp: mount() is blocked ===
mount: /mnt: permission denied.
mount BLOCKED by seccomp/capabilities — as expected

=== Kernel module loading is also blocked ===
modprobe BLOCKED — container cannot load kernel modules
```

### Step 4.2 — Write a custom seccomp profile to block chmod

Create a custom profile that blocks the `chmod` family of syscalls. This simulates a malware analysis sandbox where you want to prevent the sample from changing file permissions to execute dropped payloads.

First, exit any running containers. On your **host terminal**, create the profile file:

```bash
cat > /tmp/block-chmod.json << 'EOF'
{
  "defaultAction": "SCMP_ACT_ALLOW",
  "syscalls": [
    {
      "names": ["chmod", "fchmod", "fchmodat"],
      "action": "SCMP_ACT_ERRNO",
      "errnoRet": 1
    }
  ]
}
EOF
```

Now run the container with the custom profile:

```bash
docker run --rm --security-opt seccomp=/tmp/block-chmod.json ubuntu:22.04 bash -c '
echo "=== Custom seccomp: chmod family is blocked ==="
touch /tmp/test.txt
chmod 777 /tmp/test.txt 2>&1 || echo "chmod BLOCKED by custom seccomp profile — as expected!"
echo ""
echo "=== Other operations (write, read) still work ==="
echo "hello sandbox" > /tmp/test.txt
cat /tmp/test.txt
echo "read/write allowed!"
'
```

**Expected output:**
```
=== Custom seccomp: chmod family is blocked ===
chmod: changing permissions of '/tmp/test.txt': Operation not permitted
chmod BLOCKED by custom seccomp profile — as expected!

=== Other operations (write, read) still work ==="
hello sandbox
read/write allowed!
```

!!! info "How seccomp profiles work"
    - `"defaultAction": "SCMP_ACT_ALLOW"` — allow all syscalls by default (allowlist exceptions)
    - `"SCMP_ACT_ERRNO"` — return an error code instead of executing the syscall
    - This is **kernel-level enforcement** — it cannot be bypassed from user space, even by root inside the container

📸 **Screenshot checkpoint Sd:** Capture the seccomp output showing `chmod BLOCKED` and `read/write allowed`.

---

## Part 5 — Linux Capabilities: Least-Privilege Root

By default, Docker's root has a reduced but still significant capability set. The `--cap-drop=ALL` flag removes **every** capability, then `--cap-add` restores only what is needed. This implements the principle of least privilege even for root inside the container.

### Step 5.1 — Compare capability sets

```bash
echo "=== Default container capabilities (CapEff in hex) ==="
docker run --rm ubuntu:22.04 grep "^Cap" /proc/self/status

echo ""
echo "=== --cap-drop=ALL: zero capabilities ==="
docker run --rm --cap-drop=ALL ubuntu:22.04 grep "^Cap" /proc/self/status
```

**Expected output:**
```
=== Default container capabilities (CapEff in hex) ===
CapInh:	0000000000000000
CapPrm:	00000000a80425fb
CapEff:	00000000a80425fb    ← many capabilities active
CapBnd:	00000000a80425fb
CapAmb:	0000000000000000

=== --cap-drop=ALL: zero capabilities ===
CapInh:	0000000000000000
CapPrm:	0000000000000000
CapEff:	0000000000000000    ← no capabilities at all
CapBnd:	0000000000000000
CapAmb:	0000000000000000
```

`CapEff=0000000000000000` means even `root` inside this container has no special OS privileges.

### Step 5.2 — Demonstrate capability enforcement

```bash
docker run --rm --cap-drop=ALL ubuntu:22.04 bash -c '
echo "=== --cap-drop=ALL: even root cannot use capabilities ==="
echo ""
echo "Attempt chown (needs CAP_CHOWN):"
touch /tmp/t.txt
chown nobody /tmp/t.txt 2>&1 || echo "chown BLOCKED - CAP_CHOWN dropped"
echo ""
echo "Attempt mount (needs CAP_SYS_ADMIN):"
mount --bind /tmp /mnt 2>&1 || echo "mount BLOCKED — CAP_SYS_ADMIN dropped"
'
```

**Expected output:**
```
=== --cap-drop=ALL: even root cannot use capabilities ===

Attempt chown (needs CAP_CHOWN):
chown: changing ownership of '/tmp/t.txt': Operation not permitted
chown BLOCKED - CAP_CHOWN dropped

Attempt mount (needs CAP_SYS_ADMIN):
mount: /mnt: permission denied.
mount BLOCKED — CAP_SYS_ADMIN dropped
```

📸 **Screenshot checkpoint Se:** Capture both `grep "^Cap"` outputs showing the hex capability values, and the blocked operations output.

---

## Part 6 — cgroups: Resource Containment

Linux **cgroups (control groups)** enforce hard limits on CPU, memory, and I/O. Malware commonly attempts denial-of-service by consuming all available memory or CPU (e.g., crypto-mining). cgroup limits contain this to the sandbox.

### Step 6.1 — Verify the memory limit is enforced

```bash
docker run --rm --memory=64m --memory-swap=64m ubuntu:22.04 bash -c '
echo "=== cgroup memory limit ==="
cat /sys/fs/cgroup/memory.max 2>/dev/null || cat /sys/fs/cgroup/memory/memory.limit_in_bytes
echo "bytes = 64 MB hard limit"
'
```

**Expected output:**
```
=== cgroup memory limit ===
67108864
bytes = 64 MB hard limit
```

### Step 6.2 — Simulate a memory bomb — OOM kill in action

This simulates malware attempting to exhaust system memory. The cgroup OOM killer terminates the process before it can impact the host.

```bash
docker run --rm --memory=64m --memory-swap=64m python:3.11-slim python3 -c "
data = []
for i in range(300):
    data.append(b'X' * 1024 * 1024)
    print(f'Allocated {i+1} MB', flush=True)
print('survived')
"
echo "Container exit code: $?"
```

**Expected output:**
```
Allocated 1 MB
Allocated 2 MB
...
Allocated 59 MB
Container exit code: 137
```

**Exit code 137 = 128 + 9 = SIGKILL.** The kernel's OOM killer sent `SIGKILL` at ~59 MB (slightly below the 64 MB limit due to interpreter overhead). The host system is completely unaffected — only the sandboxed container was terminated.

!!! warning "Why this matters"
    Without cgroup limits, a single compromised container could `malloc()` the host into a system-wide OOM condition, crashing every service running on the machine. cgroup limits contain the blast radius to one container.

📸 **Screenshot checkpoint Sf:** Capture the allocation output showing the last line printed and exit code 137.

---

## Part 7 — Network Isolation: Air-Gapped Sandbox

Malware almost always attempts to phone home — downloading additional payloads, exfiltrating data, or receiving commands from a C2 server. **Network namespace isolation** severs this channel entirely.

### Step 7.1 — Air-gapped container (--network=none)

```bash
docker run --rm --network=none ubuntu:22.04 bash -c '
echo "=== --network=none: container is air-gapped ==="
echo "Network interfaces visible:"
ls /sys/class/net/
echo ""
echo "Attempting outbound connection to 8.8.8.8 (Google DNS)..."
timeout 3 bash -c "echo > /dev/tcp/8.8.8.8/53" 2>&1 || echo "TCP connection BLOCKED — no network namespace"
echo ""
echo "Only loopback (lo) exists — no eth0, no internet access"
'
```

**Expected output:**
```
=== --network=none: container is air-gapped ===
Network interfaces visible:
lo

Attempting outbound connection to 8.8.8.8 (Google DNS)...
bash: connect: Network is unreachable
bash: line 1: /dev/tcp/8.8.8.8/53: Network is unreachable
TCP connection BLOCKED — no network namespace

Only loopback (lo) exists — no eth0, no internet access
```

### Step 7.2 — Network segmentation between containers

Two containers on separate Docker bridge networks cannot communicate, even if they are both running. This prevents lateral movement: a compromised container in one segment cannot reach services in another.

```bash
# Create two isolated bridge networks
docker network create --driver bridge net-sandbox-a
docker network create --driver bridge net-sandbox-b

# Start a "victim" service on network A
docker run -d --rm --network=net-sandbox-a --name sandbox-a ubuntu:22.04 sleep 60

# Get victim's IP address
IP_A=$(docker inspect sandbox-a --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')
echo "Container A (victim) IP: $IP_A"

# Try to reach it from network B (attacker in different segment)
docker run --rm --network=net-sandbox-b ubuntu:22.04 bash -c "
echo '=== Container on net-sandbox-b cannot reach net-sandbox-a ==='
echo 'Attempting TCP connection to '$IP_A'...'
timeout 3 bash -c 'echo > /dev/tcp/'$IP_A'/53' 2>&1 || echo 'BLOCKED — network isolation between bridges works!'
"

# Cleanup
docker kill sandbox-a
docker network rm net-sandbox-a net-sandbox-b
```

**Expected output:**
```
Container A (victim) IP: 172.18.0.2
=== Container on net-sandbox-b cannot reach net-sandbox-a ===
Attempting TCP connection to 172.18.0.2...
BLOCKED — network isolation between bridges works!
```

📸 **Screenshot checkpoint Sg:** Capture the `--network=none` output showing only `lo` and the TCP connection blocked message.

---

## Part 8 — Privileged vs. Unprivileged: Understanding the Risk

Docker's `--privileged` flag disables virtually all isolation. It is the opposite of sandboxing. Seeing what `--privileged` enables makes clear why the default restrictions matter.

### Step 8.1 — Privileged container (for comparison — never use in production)

```bash
docker run --rm --privileged ubuntu:22.04 bash -c '
echo "=== PRIVILEGED container capabilities ==="
grep "^CapEff" /proc/self/status
echo "(nearly all bits set = full root equivalent)"
echo ""
echo "=== Can mount kernel filesystems ==="
mkdir -p /mnt/hostproc
mount -t proc proc /mnt/hostproc 2>&1 && echo "mount proc: SUCCESS — privileged is dangerous!" || echo "blocked"
ls /mnt/hostproc | head -5
'
```

**Expected output:**
```
=== PRIVILEGED container capabilities ===
CapEff:	000001ffffffffff
(nearly all bits set = full root equivalent)

=== Can mount kernel filesystems ===
mount proc: SUCCESS — privileged is dangerous!
1
11
12
acpi
bootconfig
```

### Step 8.2 — Default (unprivileged) container blocks the same actions

```bash
docker run --rm ubuntu:22.04 bash -c '
echo "=== Unprivileged container (default) capabilities ==="
grep "^CapEff" /proc/self/status
echo ""
echo "=== Attempting same mount (should fail) ==="
mkdir -p /mnt/testproc
mount -t proc proc /mnt/testproc 2>&1 || echo "mount BLOCKED — seccomp/capabilities protect the host"
echo ""
echo "=== PID 1 is the sandbox shell, not host init ==="
ps aux | head -5
'
```

**Expected output:**
```
=== Unprivileged container (default) capabilities ===
CapEff:	00000000a80425fb

=== Attempting same mount (should fail) ===
mount: /mnt/testproc: permission denied.
mount BLOCKED — seccomp/capabilities protect the host

=== PID 1 is the sandbox shell, not host init ===
USER         PID ...  COMMAND
root           1 ...  bash -c ...
root          11 ...  ps aux
```

📸 **Screenshot checkpoint Sh:** Capture side-by-side: privileged `CapEff` value vs. unprivileged `CapEff` value, and the mount success vs. mount blocked outputs.

---

## Part 9 — NoNewPrivileges: Blocking Setuid Escalation

`setuid` binaries (like `su`, `passwd`, `ping`) are owned by root and gain elevated privileges when executed — regardless of who runs them. The `--no-new-privileges` flag uses `prctl(PR_SET_NO_NEW_PRIVS)` to make this impossible.

### Step 9.1 — Verify NoNewPrivileges is set in the kernel

```bash
docker run --rm --security-opt no-new-privileges:true ubuntu:22.04 bash -c '
echo "=== no-new-privileges flag verification ==="
grep "NoNewPrivs" /proc/self/status
echo ""
echo "NoNewPrivs: 1 = setuid/setgid/capabilities CANNOT be gained via exec"
echo "This prevents setuid-based privilege escalation attacks"
'
```

**Expected output:**
```
=== no-new-privileges flag verification ===
NoNewPrivs:	1

NoNewPrivs: 1 = setuid/setgid/capabilities CANNOT be gained via exec
This prevents setuid-based privilege escalation attacks
```

### Step 9.2 — Confirm setuid binaries are visible but cannot escalate

```bash
docker run --rm --user 1000:1000 ubuntu:22.04 bash -c '
echo "=== Setuid binaries exist in the container ==="
ls -la /usr/bin/passwd /usr/bin/su 2>/dev/null || apt-get install -qq -y passwd 2>/dev/null && ls -la /usr/bin/passwd
echo ""
echo "These have the setuid bit (s in permissions)"
echo "Without --no-new-privileges, executing them would grant CAP_SETUID/SETGID"
echo "With --no-new-privileges, exec cannot raise privilege — the setuid bit is ignored"
'
```

**Expected output:**
```
=== Setuid binaries exist in the container ===
-rwsr-xr-x 1 root root 59976 Feb  6  2024 /usr/bin/passwd
-rwsr-xr-x 1 root root 55680 Mar  6 16:10 /usr/bin/su

These have the setuid bit (s in permissions)
```

📸 **Screenshot checkpoint Si:** Capture the `NoNewPrivs: 1` output from `/proc/self/status` and the `ls -la` showing the setuid binaries (`rwsr-xr-x`).

---

## Part 10 — The Hardened Sandbox: All Layers Combined

This final step assembles all isolation layers into a single hardened sandbox command — the kind used in production malware analysis pipelines and security scanners.

### Step 10.1 — Run the fully hardened sandbox

```bash
docker run --rm \
  --read-only \
  --tmpfs /tmp:size=32m,noexec \
  --network=none \
  --cap-drop=ALL \
  --security-opt no-new-privileges:true \
  --security-opt seccomp=/tmp/block-chmod.json \
  --memory=64m \
  --memory-swap=64m \
  --cpus=0.5 \
  ubuntu:22.04 bash -c '
echo "=== Fully hardened sandbox — verification ==="
echo ""
echo "1. PID namespace:"
ps aux | wc -l
echo "   (only 3-4 processes visible — isolated PID namespace)"
echo ""
echo "2. Capabilities:"
grep "^CapEff" /proc/self/status
echo "   (0000000000000000 = zero capabilities)"
echo ""
echo "3. NoNewPrivileges:"
grep "NoNewPrivs" /proc/self/status
echo "   (1 = escalation impossible)"
echo ""
echo "4. Read-only filesystem:"
echo "evil" > /etc/evil.txt 2>&1 || echo "   /etc write BLOCKED"
echo ""
echo "5. Network isolation:"
ls /sys/class/net/
echo "   (lo only — air-gapped)"
echo ""
echo "6. seccomp (chmod blocked):"
touch /tmp/test.txt && chmod 777 /tmp/test.txt 2>&1 || echo "   chmod BLOCKED"
echo ""
echo "7. Memory limit:"
cat /sys/fs/cgroup/memory.max 2>/dev/null || cat /sys/fs/cgroup/memory/memory.limit_in_bytes
echo "   bytes = 64MB hard limit"
echo ""
echo "All containment layers active. Malicious code is fully sandboxed."
'
```

**Expected output:**
```
=== Fully hardened sandbox — verification ===

1. PID namespace:
3
   (only 3-4 processes visible — isolated PID namespace)

2. Capabilities:
CapEff:	0000000000000000
   (0000000000000000 = zero capabilities)

3. NoNewPrivileges:
NoNewPrivs:	1
   (1 = escalation impossible)

4. Read-only filesystem:
   /etc write BLOCKED

5. Network isolation:
lo
   (lo only — air-gapped)

6. seccomp (chmod blocked):
   chmod BLOCKED

7. Memory limit:
67108864
   bytes = 64MB hard limit

All containment layers active. Malicious code is fully sandboxed.
```

!!! tip "Real-World Use"
    This is the pattern used by security tools like **VirusTotal**, **Any.run**, **Cuckoo Sandbox**, and cloud CI/CD pipelines. Each untrusted artifact runs in an isolated container with all layers enforced — even if malicious code executes, it cannot touch the host, reach the network, escalate privileges, or exhaust resources.

📸 **Screenshot checkpoint Sj:** Capture the full hardened sandbox output showing all 7 verification checks passing.

---

## Cleanup

```bash
docker system prune -f
rm -f /tmp/block-chmod.json
```

---

## Assessment

### Screenshot Checklist

| ID | Description | Points |
|----|-------------|--------|
| **Sa** | `ps aux` inside container showing only 2–4 processes with PID 1 = bash | 4 |
| **Sb** | Container write to `/etc/malicious.txt` + host verification showing file absent | 5 |
| **Sc** | `--read-only` blocking `/etc` write + `--tmpfs` allowing `/tmp` write | 5 |
| **Sd** | Custom seccomp: `chmod BLOCKED` + `read/write allowed` | 5 |
| **Se** | Capability hex values (default `a80425fb` vs `cap-drop=ALL` = `0`) + blocked chown | 5 |
| **Sf** | Memory bomb output: allocation lines + exit code 137 | 5 |
| **Sg** | `--network=none` showing only `lo` + TCP connection blocked | 4 |
| **Sh** | Privileged `CapEff` vs unprivileged `CapEff` + mount success vs blocked | 4 |
| **Si** | `/proc/self/status` `NoNewPrivs: 1` + setuid binary `ls -la` | 4 |
| **Sj** | Full hardened sandbox — all 7 verification checks passing | 9 |
| | **Screenshot subtotal** | **50** |

!!! tip "Grading Rubric"
    | Component | Points |
    |-----------|--------|
    | Screenshots (checklist above) | 50 |
    | Isolation analysis (written — see below) | 10 |
    | Reflection questions (4 × 10 pts each) | 40 |
    | **Total** | **100** |

---

### Isolation Analysis *(complete and submit)*

In **200–250 words**, analyze the hardened sandbox command from Part 10. Your analysis must cover:

- Which flag addresses which threat vector (list all 7 flags and their threat model)
- What can malicious code still do inside this sandbox? (hint: read its own files, use the CPU, make loopback connections — what else?)
- Give one real-world example of a security product that uses this pattern and explain why Docker-based sandboxing is preferred over VM-based sandboxing for high-throughput malware scanning

---

### Reflection Questions

Answer each question in **150–200 words**.

1. **Defense in depth:** This lab used 7 distinct isolation mechanisms simultaneously. Explain why each layer is necessary even though the others exist. Pick **two specific** layers and construct a realistic attack scenario that would succeed if that layer were removed, but fails when all layers are present.

2. **Containment failure — escape vectors:** A `--privileged` container with the host `/var/run/docker.sock` mounted is considered equivalent to root on the host. Explain *why* mounting the Docker socket is dangerous. What two actions could an attacker inside such a container take to escape to the host? What does this tell you about the principle of least surface area?

3. **seccomp policy design:** You are writing a seccomp profile for a Python-based static analysis tool that reads files but makes no network connections and should not spawn child processes. List the syscalls it legitimately needs and the syscalls that should be blocked. Explain why `execve` would be particularly dangerous to allow and what attacker technique it enables.

4. **Resource exhaustion as a weapon:** Crypto-mining malware and ransomware both abuse resources — one for computational gain, one to encrypt files as fast as possible. Explain how `--memory`, `--cpus`, and `--pids-limit` each limit a different dimension of resource abuse. What happens to the host system if none of these limits are applied and malware performs a fork bomb (`:(){ :|:& };:`) inside the container?
