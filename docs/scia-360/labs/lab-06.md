---
title: "Lab 06 — Linux Capabilities"
course: SCIA-360
topic: Access Control Models
chapter: 6
difficulty: "⭐⭐"
time: "45–60 min"
reading: "Chapter 6 — Principle of Least Privilege"
---

# Lab 06 — Linux Capabilities: Dropping Root, Principle of Least Privilege

| | |
|---|---|
| **Course** | SCIA-360 OS Security |
| **Topic** | Access Control Models |
| **Chapter** | 6 |
| **Difficulty** | ⭐⭐ Intermediate |
| **Estimated Time** | 45–60 minutes |
| **Prerequisites** | Lab 05 completed; Docker installed and running |

---

## Overview

Traditionally, Linux had a binary privilege model: either a process runs as **root (UID 0)** and can do anything, or it runs as an unprivileged user and can do almost nothing system-level. Linux capabilities break that monolith into **fine-grained privilege tokens** — a process can hold exactly the capabilities it needs and nothing more.

In this lab you will:

- Inspect the full capability set granted to a default Docker container
- Decode raw capability bitmasks from `/proc/self/status`
- Drop all capabilities and observe which operations fail
- Add back only `CAP_NET_BIND_SERVICE` and verify least-privilege behaviour
- Map real-world services to their minimum required capabilities

!!! tip "Grading Rubric"
    | Component | Points |
    |-----------|--------|
    | Screenshots (06a – 06g) | 40 pts |
    | Service-to-capability table (completed and submitted) | 20 pts |
    | Reflection questions (4 × 10 pts) | 40 pts |
    | **Total** | **100 pts** |

---

## Part 1 — Understanding Capabilities

### Step 1.1 — Full Capability Set (Default Container)

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq libcap2-bin 2>/dev/null
capsh --print"
```

**Expected output:** Three sets are displayed:

- **Current (effective):** capabilities the process can currently exercise
- **Bounding:** the ceiling — capabilities can never be added above this set
- **Ambient:** inherited automatically by child processes without `setuid`

Look for names like `cap_chown`, `cap_net_bind_service`, `cap_kill`, `cap_setuid`, `cap_setgid` in the Current set.

📸 **Screenshot checkpoint 06a:** Full `capsh --print` output showing all three capability sets.

---

### Step 1.2 — Decode the Raw Capability Bitmask

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq libcap2-bin 2>/dev/null
HEX=\$(cat /proc/self/status | grep CapEff | awk '{print \$2}')
echo \"CapEff hex: \$HEX\"
capsh --decode=\$HEX"
```

**Expected output:** A hex value like `00000000a80425fb` followed by a comma-separated list of named capabilities. The kernel stores capability sets as 64-bit bitmasks — each bit represents one capability. `capsh --decode` translates the bitmask to human-readable names.

📸 **Screenshot checkpoint 06b:** The `CapEff hex:` line and the decoded capability names beneath it.

---

### Step 1.3 — Per-Binary File Capabilities

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq libcap2-bin 2>/dev/null
getcap /usr/bin/ping 2>/dev/null || echo 'ping: no file capabilities'
ls -la /usr/bin/ping"
```

**Note:** In Ubuntu 22.04 containers `ping` may use `cap_net_raw` as a file capability, or it may rely on `setuid` permissions. Either approach avoids requiring a full root shell just to send ICMP packets — a classic capability use case.

📸 **Screenshot checkpoint 06c:** Output of `getcap /usr/bin/ping` and `ls -la /usr/bin/ping`.

---

## Part 2 — Dropping All Capabilities

### Step 2.1 — Default vs. `--cap-drop ALL`

Run both comparisons in the same terminal so the contrast is visible:

```bash
echo '=== Default capabilities ==='
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq libcap2-bin 2>/dev/null
capsh --print | grep '^Current:'"

echo ''
echo '=== After --cap-drop ALL ==='
docker run --rm --cap-drop ALL ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq libcap2-bin 2>/dev/null
capsh --print | grep '^Current:'"
```

**Expected output:**

```
=== Default capabilities ===
Current: = cap_chown,cap_dac_override,...

=== After --cap-drop ALL ===
Current: =
```

`Current: =` (with nothing after the equals sign) means the process holds **zero capabilities** — it cannot perform any privileged kernel operation.

📸 **Screenshot checkpoint 06c:** Both `Current:` lines visible in the same terminal window, demonstrating the empty set after `--cap-drop ALL`.

!!! warning "Package installation still works"
    Even with `--cap-drop ALL`, `apt-get` succeeds here because installing packages does not require kernel capabilities — it only writes files and runs scripts as root. Capabilities govern *kernel-level* privilege, not filesystem write access controlled by UID 0.

---

### Step 2.2 — `CAP_CHOWN` Removed: `chown` Fails

```bash
docker run --rm --cap-drop CHOWN ubuntu:22.04 bash -c "
touch /tmp/test.txt
chown daemon:daemon /tmp/test.txt 2>&1 || echo 'chown FAILED: no cap_chown'"
```

**Expected output:** `chown: changing ownership of '/tmp/test.txt': Operation not permitted`

Even though the process runs as **root (UID 0)**, without `CAP_CHOWN` the kernel rejects the `chown()` system call.

---

### Step 2.3 — `CAP_CHOWN` Present: `chown` Succeeds

```bash
docker run --rm ubuntu:22.04 bash -c "
touch /tmp/test.txt
chown daemon:daemon /tmp/test.txt && ls -la /tmp/test.txt"
```

**Expected output:** `-rw-r--r-- 1 daemon daemon` — the ownership change succeeded.

📸 **Screenshot checkpoint 06d:** Steps 2.2 and 2.3 results in the same terminal: `chown` failure without `CAP_CHOWN` and `chown` success with it.

---

## Part 3 — Adding Only the Capabilities You Need

### Step 3.1 — Single-Capability Container

```bash
docker run --rm \
  --cap-drop ALL \
  --cap-add NET_BIND_SERVICE \
  ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq libcap2-bin 2>/dev/null
echo 'Capabilities (only NET_BIND_SERVICE):'
capsh --print | grep '^Current:'"
```

**Expected output:**

```
Current: = cap_net_bind_service
```

One capability. Nothing else. This is the principle of least privilege in machine-readable form.

📸 **Screenshot checkpoint 06e:** `Current: = cap_net_bind_service` clearly visible.

---

### Step 3.2 — Port Binding Allowed, File Ownership Still Blocked

```bash
docker run --rm \
  --cap-drop ALL \
  --cap-add NET_BIND_SERVICE \
  ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq netcat-openbsd 2>/dev/null
nc -l -p 1024 &
sleep 0.5 && kill %1 2>/dev/null
echo 'Port 1024: allowed with NET_BIND_SERVICE'
nc -l -p 80 &
sleep 0.5 && kill %1 2>/dev/null
echo 'Port 80: also allowed with NET_BIND_SERVICE'
touch /tmp/t && chown daemon:daemon /tmp/t 2>&1 || echo 'chown: still blocked (no CAP_CHOWN)'"
```

**Expected output:**

```
Port 1024: allowed with NET_BIND_SERVICE
Port 80: also allowed with NET_BIND_SERVICE
chown: still blocked (no CAP_CHOWN)
```

`CAP_NET_BIND_SERVICE` grants the right to bind to **any** port (including privileged ports < 1024) but grants nothing else.

📸 **Screenshot checkpoint 06f:** All three output lines visible — two port-binding successes and the `chown` failure.

---

## Part 4 — Capabilities vs. Root: The Key Insight

### Step 4.1 — What Docker Drops From Full Root by Default

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq libcap2-bin 2>/dev/null
echo '=== Dropped from full root in Docker default: ==='
echo 'CAP_SYS_ADMIN  - mount, ioctl, kernel params (most dangerous)'
echo 'CAP_SYS_BOOT   - reboot system'
echo 'CAP_NET_ADMIN  - iptables, change network interfaces'
echo 'CAP_SYS_MODULE - load/unload kernel modules'
echo ''
echo '=== Present in Docker default container: ==='
capsh --print | grep '^Current:'"
```

📸 **Screenshot checkpoint 06g:** The dropped capabilities list and the `Current:` line of Docker's default set — both visible together.

---

### Step 4.2 — Service-to-Capability Reference Table

Study the table below. You will reference it in your reflection and may be asked to extend it on a quiz.

| Service | Minimum Required Capability | Why It Is Needed |
|---------|----------------------------|-----------------|
| nginx (HTTPS on port 443) | `CAP_NET_BIND_SERVICE` | Bind to privileged port < 1024 |
| syslog daemon | `CAP_SYS_ADMIN` (or none with modern API) | Read kernel ring buffer log |
| cron daemon | `CAP_SETUID`, `CAP_SETGID` | Switch effective UID/GID before running user jobs |
| NTP client (chronyd) | `CAP_SYS_TIME` | Adjust the hardware and system clock |
| Container runtime (runc) | `CAP_SYS_ADMIN` + many | Create namespaces, mount filesystems, `pivot_root` |

!!! tip "Lab deliverable"
    Submit this table with your screenshots. On the assessment you may be asked to add two additional services and justify their capability requirements.

---

## Cleanup

```bash
docker system prune -f
```

---

## Assessment

### Screenshot Checklist

| ID | Required Content |
|----|-----------------|
| **06a** | `capsh --print` showing full Current, Bounding, and Ambient sets |
| **06b** | `CapEff hex:` value and decoded capability names |
| **06c** | `Current: =` (empty) after `--cap-drop ALL` alongside default `Current:` |
| **06d** | `chown` failing without `CAP_CHOWN` and succeeding with it |
| **06e** | `Current: = cap_net_bind_service` — single capability container |
| **06f** | Port 1024 and port 80 allowed; `chown` still blocked |
| **06g** | Dropped capabilities list and Docker default `Current:` line |

---

### Reflection Questions

!!! warning "Submission requirement"
    Answer each question in **complete paragraphs** (minimum 4–6 sentences each). Bullet-point-only answers will not receive full credit.

**Q1.** Before Linux capabilities, programs like `ping` and web servers needed to run as full root (UID 0) to perform privileged operations such as binding to port 80 or sending raw packets. Explain how Linux capabilities improve security compared to that binary root/non-root model. What specific risk does each individual capability grant, and why does granularity matter?

**Q2.** `CAP_SYS_ADMIN` is sometimes called the *root of capabilities* — it grants so many kernel privileges that possessing it is nearly equivalent to having full root. Why does Docker drop `CAP_SYS_ADMIN` from containers by default? Describe at least two concrete attacks an adversary could execute inside a container if `CAP_SYS_ADMIN` were available.

**Q3.** In Step 3.2, a container holding only `CAP_NET_BIND_SERVICE` could listen on port 80 but could not change file ownership. How does this outcome demonstrate the principle of least privilege? Describe a realistic production web-server deployment that would benefit from this capability isolation — what would be in the container, what capabilities would it hold, and what would be explicitly dropped?

**Q4.** An attacker exploits a buffer overflow in an nginx process running in a container launched with `--cap-drop ALL --cap-add NET_BIND_SERVICE`. Using your knowledge from this lab, list and explain **three** specific privileged actions the attacker **cannot** perform — actions that would be available to them if the container were running with the default Docker capability set or full root.
