# Lab 06 — Firewall Rules with iptables

**Course:** SCIA-120 · Introduction to Secure Computing  
**Topic:** Network Security — Packet Filtering & Firewalls  
**Difficulty:** ⭐⭐ Beginner–Intermediate  
**Estimated Time:** 45–60 minutes  
**Related Reading:** Chapter 7 — Network Security Fundamentals

---

## Overview

A **firewall** is the first line of network defense — it controls which traffic is allowed in and out of a system based on rules. In this lab you will configure **iptables** firewall rules inside Docker containers, observe how rules block or allow traffic, and understand the logic behind packet filtering: default-deny vs. default-allow policies.

---

## Learning Objectives

1. Understand what iptables is and how it processes network packets.
2. List, add, and delete firewall rules.
3. Apply a default-deny (allowlist) policy vs. default-allow (blocklist) policy.
4. Block specific ports, IP addresses, and protocols.
5. Understand how Docker itself uses iptables internally.

---

## Prerequisites

- Docker Desktop installed and running.
- Lab 04 or 05 recommended.

---

## Part 1 — Understanding iptables Chains

iptables organizes rules into **chains**:

| Chain | When it runs |
|-------|-------------|
| `INPUT` | Packets destined for the local machine |
| `OUTPUT` | Packets originating from the local machine |
| `FORWARD` | Packets routed through the machine |

Each chain has a **default policy** (ACCEPT or DROP) that applies if no rule matches.

### Step 1.1 — Start a Privileged Container (iptables requires privileges)

```bash
docker run --rm -it \
  --name firewall-lab \
  --cap-add NET_ADMIN \
  --cap-add NET_RAW \
  ubuntu:22.04 bash
```

### Step 1.2 — Install iptables and Utilities

```bash
apt-get update -qq && apt-get install -y -qq iptables iputils-ping netcat-openbsd curl
```

### Step 1.3 — View Current Rules

```bash
iptables -L -v -n
```

**Expected output:**
```
Chain INPUT (policy ACCEPT)
target     prot opt source               destination

Chain FORWARD (policy ACCEPT)
...

Chain OUTPUT (policy ACCEPT)
...
```

By default, everything is ACCEPT — all traffic is allowed.

📸 **Screenshot checkpoint:** Take a screenshot of the default (empty) iptables rules.

---

## Part 2 — Adding Basic Rules

### Step 2.1 — Block All ICMP (Ping) Traffic

```bash
ping -c 2 8.8.8.8       # Test ping works BEFORE rule
```

Add the block rule:

```bash
iptables -A INPUT -p icmp --icmp-type echo-reply -j DROP
iptables -L -v -n
```

```bash
ping -c 2 8.8.8.8       # Now ping replies are blocked
```

📸 **Screenshot checkpoint:** Take a screenshot showing ping working before and blocked after the rule.

### Step 2.2 — Allow ICMP Again (Delete the Rule)

```bash
iptables -D INPUT -p icmp --icmp-type echo-reply -j DROP
ping -c 2 8.8.8.8       # Should work again
```

---

## Part 3 — Block a Specific Port

### Step 3.1 — Block Inbound Connections on Port 8080

```bash
iptables -A INPUT -p tcp --dport 8080 -j DROP
iptables -L -v -n
```

📸 **Screenshot checkpoint:** Take a screenshot of the rules list showing the port block.

### Step 3.2 — Test the Block

In one container window start a listener:

```bash
nc -l -p 9090 &      # 9090 is NOT blocked
nc -l -p 8080 &      # 8080 IS blocked
```

Try connecting to each from within the container:

```bash
echo "test" | nc -w 1 127.0.0.1 9090    # Should succeed
echo "test" | nc -w 1 127.0.0.1 8080    # Should be blocked/timeout
```

📸 **Screenshot checkpoint:** Take a screenshot showing the difference between the blocked and allowed port.

---

## Part 4 — Block a Specific IP Address

### Step 4.1 — Block Traffic from a Specific Source IP

```bash
iptables -A INPUT -s 1.2.3.4 -j DROP
iptables -L -v -n
```

This blocks all traffic from IP `1.2.3.4` — useful for blocking known malicious IPs.

### Step 4.2 — See the Rule Count Increment

```bash
iptables -L INPUT -v -n
```

After network activity, the "pkts" and "bytes" columns increment for matched rules — you can see which rules are being hit.

📸 **Screenshot checkpoint:** Take a screenshot of the rules list showing the IP block rule.

---

## Part 5 — Default-Deny Policy

The most secure firewall posture is **default-deny**: block everything, then explicitly allow only what is needed. This is the opposite of default-allow.

### Step 5.1 — Set a Default-Deny Policy

!!! warning "Important"
    This will block all incoming traffic. Only run this inside the container — not on your real system.

```bash
iptables -P INPUT DROP
iptables -L -v -n
```

### Step 5.2 — Verify Everything Is Now Blocked

```bash
# This should now fail — all INPUT traffic is dropped
echo "test" | nc -w 1 127.0.0.1 9090
```

### Step 5.3 — Selectively Allow SSH (Port 22) and HTTP (Port 80)

```bash
iptables -A INPUT -p tcp --dport 22 -j ACCEPT
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
iptables -L -v -n
```

The last rule is critical — it allows responses to connections you *initiated* (established connections) to come back in.

📸 **Screenshot checkpoint:** Take a screenshot of the full iptables ruleset with default DROP and specific ACCEPT rules.

---

## Part 6 — Allowlist vs. Blocklist Comparison

Fill in this table as part of your submission:

| Policy | How it works | Security level | Operational risk |
|--------|-------------|----------------|-----------------|
| Default-Allow (Blocklist) | Allow all; block known bad | Lower | Low — easy to maintain |
| Default-Deny (Allowlist) | Block all; allow known good | Higher | Higher — may block legitimate traffic |

---

## Part 7 — Flush All Rules

To reset to default (remove all rules):

```bash
iptables -F              # Flush all rules
iptables -P INPUT ACCEPT # Restore default ACCEPT
iptables -L -v -n
```

📸 **Screenshot checkpoint:** Take a screenshot of the clean (empty) state after flushing.

Type `exit` to leave the container.

---

## Cleanup

```bash
docker system prune -f
```

---

## Lab Assessment

### Screenshot Submission Checklist

- [ ] `screenshot-06a` — Default empty iptables rules
- [ ] `screenshot-06b` — Ping before and after ICMP block rule
- [ ] `screenshot-06c` — Port 8080 block rule in iptables list
- [ ] `screenshot-06d` — Difference between blocked (8080) and allowed (9090) ports
- [ ] `screenshot-06e` — IP address block rule
- [ ] `screenshot-06f` — Default-deny policy with selective ACCEPT rules
- [ ] `screenshot-06g` — Flushed (clean) iptables state

### Reflection Questions

1. What is the difference between a "default-allow" and "default-deny" firewall policy? Which is more secure, and what are the tradeoffs?
2. Why is the `ESTABLISHED,RELATED` iptables rule necessary? What would break without it?
3. A company's IT policy says: "The firewall should block all inbound traffic except ports 80, 443, and 22." Write out the iptables commands that would implement this policy.
4. A firewall blocks all traffic from a known-bad IP address. An attacker switches to a different IP. What does this tell you about the limitations of IP-based blocking?

---

!!! tip "Grading Rubric"
    - Screenshots complete and clearly labeled: **40 points**  
    - Allowlist vs. Blocklist table completed: **20 points**  
    - Reflection questions answered thoughtfully: **40 points**  
    - **Total: 100 points**
