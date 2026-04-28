---
title: "Lab 09 — Linux Namespaces: The Building Blocks of Containers"
course: SCIA-360
topic: Sandboxing & Containerization
chapter: 8
difficulty: "⭐⭐"
estimated_time: "60–75 minutes"
tags:
  - namespaces
  - containers
  - unshare
  - linux-internals
  - sandboxing
---

# Lab 09 — Linux Namespaces: The Building Blocks of Containers

| Field | Details |
|-------|---------|
| **Course** | SCIA-360 OS Security |
| **Topic** | Sandboxing & Containerization |
| **Chapter** | 8 |
| **Difficulty** | ⭐⭐ Intermediate |
| **Estimated Time** | 60–75 minutes |
| **Requires** | Docker, `ubuntu:22.04` image |

---

## Overview

Linux **namespaces** are the foundational kernel technology behind every container runtime — Docker, Podman, and containerd all rely on them. Each namespace type isolates a different aspect of the operating system, creating the illusion that a process has its own private view of the system.

In this lab you will use the `unshare` utility to manually create isolated namespaces one at a time, observing exactly what each namespace type isolates. By the end you will understand precisely *why* Docker containers behave as isolated systems — because the kernel enforces each isolation boundary at the namespace level.

**Namespace types covered:**

| Namespace | Flag | Isolates |
|-----------|------|----------|
| UTS | `--uts` | Hostname and domain name |
| PID | `--pid` | Process ID number space |
| NET | `--net` | Network interfaces, routing, ports |
| MNT | `--mount` | Filesystem mount points |
| IPC | `--ipc` | Inter-process communication (semaphores, shared memory) |
| USER | `--user` | User and group ID mappings |
| CGROUP | `--cgroup` | cgroup root directory view |
| TIME | `--time` | System clock offsets |

!!! warning "Privileged containers required"
    Several `unshare` operations require `--privileged` on the Docker container. **Only run privileged containers in isolated lab environments — never in production.** The privilege is needed here so the container itself has sufficient capabilities to create sub-namespaces.

---

## Part 1 — Namespace Overview

### Step 1.1 — Inspect the namespace filesystem

Every Linux process has a directory at `/proc/<pid>/ns/` containing symbolic links — one per namespace — that identify which namespace instance the process belongs to. The number in brackets (e.g., `uts:[4026531838]`) is the inode of the namespace; two processes sharing the same inode are in the same namespace.

```bash
docker run --rm --privileged ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq util-linux iproute2 procps 2>/dev/null
echo '=== Namespaces for this process ==='
ls -la /proc/self/ns/"
```

**Expected output:** A listing of symlinks including `cgroup`, `ipc`, `mnt`, `net`, `pid`, `time`, `user`, and `uts`, each with a unique numeric ID such as `uts:[4026531838]`.

!!! tip "What to look for"
    Each symlink name corresponds to one namespace type. The number is an inode ID — if two processes share the same inode for a given namespace type, they share that namespace and can see each other's resources of that type.

📸 **Screenshot checkpoint 09a:** Capture the full `ls -la /proc/self/ns/` output showing all namespace symlinks and their inode IDs.

---

## Part 2 — UTS Namespace (Hostname Isolation)

The **UTS namespace** (Unix Time-Sharing) isolates the system hostname and NIS domain name. Changing the hostname inside a UTS namespace does not affect the host or any other namespace.

### Step 2.1 — Demonstrate hostname isolation

```bash
docker run --rm --privileged ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq util-linux 2>/dev/null
echo 'Before:' && hostname
unshare --uts bash -c 'hostname isolated-host && echo Inside: \$(hostname)'
echo 'After:' && hostname"
```

**Expected output:**
```
Before: <container-id>
Inside: isolated-host
After: <container-id>    ← unchanged
```

The `unshare --uts` command creates a new UTS namespace for the child process. The child can set its own hostname without any effect on the parent process or the host system.

📸 **Screenshot checkpoint 09b:** Capture the output showing "Before", "Inside: isolated-host", and "After" with the original hostname restored.

---

## Part 3 — PID Namespace (Process ID Isolation)

The **PID namespace** creates an independent numbering space for process IDs. The first process inside a new PID namespace gets PID 1 — regardless of its actual PID from the parent's perspective.

### Step 3.1 — Demonstrate PID remapping

```bash
docker run --rm --privileged ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq util-linux procps 2>/dev/null
echo 'Parent PID:' && echo \$\$
unshare --pid --fork bash -c 'echo Inside PID namespace: my PID is \$\$'"
```

**Expected output:**
```
Parent PID: 94          ← or some value from the container's PID space
Inside PID namespace: my PID is 2   ← low number, isolated space
```

📸 **Screenshot checkpoint 09c:** Capture the parent PID vs. the inside PID showing they are different numbers.

---

### Step 3.2 — Process visibility isolation

Inside a PID namespace with a private `/proc` mount, a process cannot see processes from the parent namespace — they simply do not exist from its perspective.

```bash
docker run --rm --privileged ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq util-linux procps 2>/dev/null
echo 'Parent sees:' && ps aux | wc -l && echo 'processes'
unshare --pid --fork --mount-proc bash -c 'echo Inside sees: && ps aux | wc -l && echo processes && ps aux'"
```

**Expected output:**
```
Parent sees:
12                 ← several processes visible
processes
Inside sees:
3                  ← only bash + ps (+ header line)
processes
USER  PID  ...
root    1  bash
root    2  ps aux
```

The `--mount-proc` flag mounts a fresh `/proc` filesystem inside the new PID namespace, reflecting only the processes visible in that namespace.

📸 **Screenshot checkpoint 09d:** Capture both process counts — the high number outside and the 2–3 processes visible inside.

---

## Part 4 — Network Namespace (Network Stack Isolation)

The **network namespace** provides each isolated environment with its own network interfaces, routing tables, firewall rules, and port number space. A process in a new network namespace starts with only a loopback interface — no external connectivity until explicitly configured.

### Step 4.1 — Demonstrate interface isolation

```bash
docker run --rm --privileged ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq util-linux iproute2 2>/dev/null
echo '=== Parent interfaces ==='
ip link show | grep -E '^[0-9]+:'
echo '=== Inside net namespace (only loopback) ==='
unshare --net bash -c 'ip link show | grep -E \"^[0-9]+:\"'
echo '=== Parent interfaces still intact ==='
ip link show | grep -c '^[0-9]'"
```

**Expected output:**
```
=== Parent interfaces ===
1: lo: ...
2: eth0: ...        ← or similar

=== Inside net namespace (only loopback) ===
1: lo: ...          ← only loopback — no eth0

=== Parent interfaces still intact ===
2                   ← parent still has both interfaces
```

📸 **Screenshot checkpoint 09e:** Capture the three sections showing parent interfaces, the isolated namespace with only `lo`, and confirmation that parent interfaces are untouched.

---

## Part 5 — Mount Namespace (Filesystem Isolation)

The **mount namespace** isolates the set of filesystem mount points visible to a process. Changes to mounts inside a namespace (mounting, unmounting) do not propagate to the parent namespace. This is how Docker gives each container its own root filesystem.

### Step 5.1 — Demonstrate mount isolation

```bash
docker run --rm --privileged ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq util-linux 2>/dev/null
echo 'Parent /tmp:' && ls /tmp
unshare --mount bash -c '
  mount -t tmpfs tmpfs /tmp
  echo namespace_secret > /tmp/secret.txt
  echo Inside /tmp: && ls /tmp
'
echo 'Parent /tmp (unchanged):' && ls /tmp"
```

**Expected output:**
```
Parent /tmp:
                        ← empty or system files only

Inside /tmp:
secret.txt              ← exists only inside the namespace

Parent /tmp (unchanged):
                        ← secret.txt NOT here
```

The child process mounted a fresh `tmpfs` over `/tmp` within its private mount namespace. From the parent's perspective, `/tmp` was never touched.

📸 **Screenshot checkpoint 09f:** Capture all three sections — parent before, inside with `secret.txt`, parent after with `/tmp` unchanged.

---

## Part 6 — All Namespaces Together (Docker)

Docker automatically creates all namespace types simultaneously when starting a container, giving it complete OS-level isolation. You can observe the unique namespace IDs assigned to any running container.

### Step 6.1 — Inspect a container's namespace IDs

```bash
docker run --rm ubuntu:22.04 bash -c "
echo '=== This container has its own namespace IDs ==='
ls -la /proc/self/ns/ | awk '{print \$11, \$12, \$13}' | grep -v '^$'
echo 'Each ID is unique - Docker created new namespaces for this container'"
```

📸 **Screenshot checkpoint 09g-part1:** Capture the namespace listing for this container.

---

### Step 6.2 — Two containers: separate network namespaces

Each container gets its own network namespace, which means its own IP address space. Observe that two containers on the same Docker network receive different IPs, proving they inhabit different network namespaces.

```bash
docker network create ns-demo

docker run -d --name ns-a --network ns-demo ubuntu:22.04 sleep 60
docker run -d --name ns-b --network ns-demo ubuntu:22.04 sleep 60

IP_A=$(docker inspect ns-a --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')
IP_B=$(docker inspect ns-b --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')

echo "Container A IP: $IP_A"
echo "Container B IP: $IP_B"

docker stop ns-a ns-b && docker rm ns-a ns-b
docker network rm ns-demo
```

**Expected output:**
```
Container A IP: 172.18.0.2
Container B IP: 172.18.0.3    ← different IPs — separate network namespaces
```

📸 **Screenshot checkpoint 09g:** Capture both container IPs confirming they are in separate network namespaces.

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
| **09a** | `/proc/self/ns/` listing showing all namespace symlinks with inode IDs | 6 |
| **09b** | UTS hostname isolation — "Inside: isolated-host" vs. unchanged outside hostname | 6 |
| **09c** | PID isolation — parent high PID vs. inside low PID | 6 |
| **09d** | Process count isolation — many outside vs. 2–3 inside | 6 |
| **09e** | Network namespace — `eth0` outside, only `lo` inside | 6 |
| **09f** | Mount namespace — `secret.txt` inside, `/tmp` clean outside | 6 |
| **09g** | Two containers with different IP addresses | 4 |
| | **Screenshot subtotal** | **40** |

!!! tip "Grading Rubric"
    | Component | Points |
    |-----------|--------|
    | Screenshots (checklist above) | 40 |
    | Namespace type comparison table (complete all 8 types with: flag, what it isolates, real-world Docker use) | 20 |
    | Reflection questions (4 × 10 pts each) | 40 |
    | **Total** | **100** |

---

### Namespace Type Table *(complete and submit)*

Fill in this table as part of your lab submission:

| Namespace | `unshare` Flag | What It Isolates | Docker Use Case |
|-----------|---------------|------------------|-----------------|
| UTS | `--uts` | | |
| PID | `--pid` | | |
| NET | `--net` | | |
| MNT | `--mount` | | |
| IPC | `--ipc` | | |
| USER | `--user` | | |
| CGROUP | `--cgroup` | | |
| TIME | `--time` | | |

---

### Reflection Questions

Answer each question in **150–200 words**.

1. **Namespace completeness:** List the six main Linux namespace types and what each isolates. Why must a container runtime use **all** of them together (not just one) to achieve proper container-level isolation? Give a concrete example of what could go wrong if only the network namespace were used without the PID namespace.

2. **PID 1 and init:** In the PID namespace demo, the shell inside the namespace received PID 1. What is special about PID 1 in Linux (the `init` process)? If PID 1 inside a container crashes or exits, what happens to all other processes running inside that container? What does this mean for container design — specifically, why should long-running containers use a proper init process?

3. **Overlay filesystems:** The mount namespace demo showed that creating a file in `/tmp` inside a namespace did not appear outside. How does Docker extend this concept — using mount namespaces together with **overlay filesystems** (`overlayfs`) — to give each container its own complete root filesystem that is copy-on-write layered on top of a shared image?

4. **Namespaces vs. cgroups:** Namespaces provide isolation (visibility boundaries) but do **not** enforce resource limits. What Linux mechanism works alongside namespaces to prevent one container from consuming all CPU or RAM on the host? Explain how these two technologies — namespaces and cgroups — combine to create the complete container security and resource model used by Docker.
