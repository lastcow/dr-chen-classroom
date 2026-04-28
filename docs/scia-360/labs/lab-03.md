---
title: "Lab 03 — Memory Protections: ASLR, Stack Canaries & NX"
course: SCIA-360
topic: Memory Security
chapter: 3
difficulty: "⭐⭐ Intermediate"
duration: "60–75 minutes"
tags:
  - linux
  - aslr
  - stack-canary
  - nx-bit
  - memory-security
  - exploitation-mitigations
---

# Lab 03 — Memory Protections: ASLR, Stack Canaries & NX

| Field | Details |
|---|---|
| **Course** | SCIA-360 — Operating System Security |
| **Topic** | Memory Security |
| **Chapter** | 3 |
| **Difficulty** | ⭐⭐ Intermediate |
| **Estimated Time** | 60–75 minutes |
| **Environment** | Docker — `python:3.11-slim` and `ubuntu:22.04` |

---

## Overview

Memory corruption vulnerabilities — buffer overflows, use-after-free, format string bugs — remain among the most dangerous classes of software defects. Modern operating systems deploy three complementary mitigations that dramatically raise the cost of exploiting these vulnerabilities: **ASLR** (Address Space Layout Randomization), **stack canaries**, and the **NX bit** (No-eXecute, also called DEP on Windows). In this lab you will observe each mitigation in action, disable them to see the difference, trigger a live stack canary detection, and examine binary metadata to confirm whether protections are enabled.

By the end of this lab you will understand:

- How ASLR randomizes the memory layout and why that matters for exploit reliability
- What a stack canary is, where it is placed, and how the runtime detects overflow
- How the NX bit prevents code injection by marking the stack non-executable
- Why layered defenses retain value even when each individual layer can be bypassed

!!! warning "Privileged container steps"
    Part 1, Step 1.4 requires `--privileged` to disable ASLR system-wide in the container. This is safe in an isolated lab container but would be a serious misconfiguration in production. Never run production containers with `--privileged`.

---

## Prerequisites

- Completed Labs 01 and 02
- Chapter 3 reading on memory layout and exploitation mitigations
- Basic understanding of what a stack is and what a return address does

---

## Part 1 — ASLR: Address Space Layout Randomization

### Step 1.1 — Check the ASLR Setting

```bash
docker run --rm python:3.11-slim bash -c "cat /proc/sys/kernel/randomize_va_space"
```

**Expected output:** `2`

| Value | Meaning |
|---|---|
| `0` | ASLR disabled — all addresses are static and predictable |
| `1` | Partial ASLR — randomizes mmap, stack, and VDSO but not the main executable |
| `2` | Full ASLR — randomizes everything including the main executable (PIE required) |

!!! tip "Why this is the default"
    Value `2` (full ASLR) has been the default on Ubuntu since 12.04. It ensures that even if an attacker knows the binary layout, the runtime addresses of stack, heap, libraries, and the executable itself change with every execution — making hardcoded return addresses in exploits useless.

📸 **Screenshot checkpoint 03a** — Capture the `randomize_va_space` value of `2`.

---

### Step 1.2 — Observe ASLR in Action

```bash
docker run --rm python:3.11-slim bash -c "
for i in 1 2 3; do
  python3 -c \"
import ctypes
buf = ctypes.create_string_buffer(16)
print(f'Run \$i: buffer_addr={hex(ctypes.addressof(buf))}')
\"
done"
```

**Expected output:** Three **different** hexadecimal addresses — one per iteration.

```
Run 1: buffer_addr=0x7f3a2c001b20
Run 2: buffer_addr=0x7f91d4000b40
Run 3: buffer_addr=0x7f5e88002a60
```

!!! tip "Why addresses change between processes"
    Each `python3 -c` invocation is a new process with a fresh virtual address space. With ASLR enabled, the kernel randomizes the base addresses of heap, stack, and mmap regions independently for each new process. An attacker who finds a buffer overflow and wants to overwrite the return address cannot predict where to jump without a separate **information leak** vulnerability.

📸 **Screenshot checkpoint 03b** — Capture all three run outputs showing three different addresses.

---

### Step 1.3 — Memory Map Shows Randomized Base Addresses

```bash
docker run --rm python:3.11-slim python3 -c "
with open('/proc/self/maps') as f:
    for line in list(f)[:8]:
        print(line.rstrip())
"
```

Run this command **twice** and compare the base addresses in both outputs. With ASLR enabled they will differ between runs.

!!! tip "Reading /proc/self/maps"
    Each line represents one memory region: `[start]-[end] [perms] [offset] [dev] [inode] [path]`. With full ASLR you will see different start addresses for `python3`, `libc`, and anonymous mmap regions between runs. This is the randomization that ASLR provides at the OS level.

📸 **Screenshot checkpoint 03c** — Capture `/proc/self/maps` output (run it twice if possible and show both — addresses should differ).

---

### Step 1.4 — Disable ASLR and Observe Predictable Addresses

```bash
docker run --rm --privileged python:3.11-slim bash -c "
echo 0 > /proc/sys/kernel/randomize_va_space
for i in 1 2 3; do
  python3 -c \"
import ctypes
buf = ctypes.create_string_buffer(16)
print(f'Run \$i: buffer_addr={hex(ctypes.addressof(buf))}')
\"
done"
```

**Expected output:** Three **identical** addresses.

```
Run 1: buffer_addr=0x55a3b4001b20
Run 2: buffer_addr=0x55a3b4001b20
Run 3: buffer_addr=0x55a3b4001b20
```

!!! warning "This is what attackers want"
    With ASLR disabled, an attacker who discovers a buffer overflow only needs to find the offset and the target address **once** — offline, in a lab — and the exploit will work reliably every time against any instance of the target process. This is why disabling ASLR (e.g., via `ulimit -s unlimited` or `personality(ADDR_NO_RANDOMIZE)`) can be a critical vulnerability in production.

📸 **Screenshot checkpoint 03d** — Capture all three identical addresses with ASLR disabled.

---

## Part 2 — Stack Canaries

### Step 2.1 — Compare Binaries With and Without Stack Canary

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq gcc binutils 2>/dev/null
printf '#include <stdio.h>\nvoid greet() { char buf[8]; }\nint main() { greet(); return 0; }\n' > /tmp/prog.c
gcc -o /tmp/with_canary /tmp/prog.c -fstack-protector-strong
gcc -o /tmp/no_canary   /tmp/prog.c -fno-stack-protector
echo '=== With stack canary: __stack_chk_fail references ==='
objdump -d /tmp/with_canary | grep -c 'stack_chk'
echo '=== Without canary: references ==='
objdump -d /tmp/no_canary | grep -c 'stack_chk' || echo '0'"
```

**Expected output:**

```
=== With stack canary: __stack_chk_fail references ===
2
=== Without canary: references ===
0
```

!!! tip "How the canary works in assembly"
    With `-fstack-protector-strong`, GCC inserts two code sequences around functions with local buffers:

    1. **Function prologue:** Reads a random value from `gs:[0x28]` (thread-local storage) and writes it to the stack just below the saved return address.
    2. **Function epilogue:** Reads the canary back from the stack and compares it to the original. If they differ, `__stack_chk_fail()` is called, which prints "stack smashing detected" and terminates with `SIGABRT`.

    `objdump` reveals these as references to `__stack_chk_guard` (read) and `__stack_chk_fail` (called on mismatch).

📸 **Screenshot checkpoint 03e** — Capture the `objdump` output showing the count difference (e.g., `2` vs. `0`).

---

### Step 2.2 — Trigger Live Stack Smashing Detection

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq gcc 2>/dev/null
printf '#include <string.h>\nvoid vuln() { char buf[8]; memset(buf,65,32); }\nint main() { vuln(); return 0; }\n' > /tmp/overflow.c
gcc -o /tmp/overflow /tmp/overflow.c -fstack-protector-strong
/tmp/overflow 2>&1 || echo 'Stack smashing detected — canary triggered!'"
```

**Expected output:**

```
*** stack smashing detected ***: terminated
Stack smashing detected — canary triggered!
```

!!! tip "What just happened"
    `memset(buf, 65, 32)` wrote 32 bytes of `'A'` into a buffer declared as only 8 bytes. This overflowed 24 bytes past the end of `buf`, overwriting the stack canary. When `vuln()` returned, the epilogue code compared the corrupted canary to the original value in thread-local storage — they didn't match — and called `__stack_chk_fail()`, which terminated the process with an error message.

!!! warning "What canaries do NOT prevent"
    Stack canaries only protect the **return address**. They do not prevent:

    - Overwriting other local variables on the stack (before the canary)
    - Overwriting function pointers stored on the heap
    - Use-after-free vulnerabilities
    - Format string attacks that leak the canary value

📸 **Screenshot checkpoint 03f** — Capture the "stack smashing detected" termination message.

---

## Part 3 — NX Bit (No-Execute)

### Step 3.1 — Compare Executable vs. Non-Executable Stack

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq gcc binutils 2>/dev/null
printf '#include <stdio.h>\nint main(){return 0;}\n' > /tmp/nx.c
gcc -o /tmp/nx_on  /tmp/nx.c
gcc -o /tmp/nx_off /tmp/nx.c -Wl,-z,execstack
echo '=== Default (NX enabled): stack NOT executable ==='
readelf -l /tmp/nx_on  | grep GNU_STACK
echo '=== execstack flag (NX disabled): stack EXECUTABLE ==='
readelf -l /tmp/nx_off | grep GNU_STACK"
```

**Expected output:**

```
=== Default (NX enabled): stack NOT executable ===
  GNU_STACK      0x000000 0x0000000000000000 0x0000000000000000 0x000000 0x000000 RW  0x10
=== execstack flag (NX disabled): stack EXECUTABLE ===
  GNU_STACK      0x000000 0x0000000000000000 0x0000000000000000 0x000000 0x000000 RWE 0x10
```

| Flag | Meaning |
|---|---|
| `RW` | Stack is readable and writable — NX **enabled**, not executable |
| `RWE` | Stack is readable, writable, **and executable** — NX **disabled**, dangerous |

!!! tip "GNU_STACK and the kernel"
    The `GNU_STACK` segment in an ELF binary is a hint to the kernel's program loader. If the flags include `E` (executable), the kernel maps the stack as executable when loading the program. The `-Wl,-z,execstack` linker flag sets this bit — a legitimate use case is legacy code with trampolines, but it disables an important security mitigation.

!!! warning "Why RWE stacks are dangerous"
    The **shellcode injection** attack worked as follows: overflow a stack buffer → overwrite the return address to point back into the buffer → the buffer contains attacker-supplied machine code → when the function returns, the CPU executes the injected code. The NX bit defeats this by preventing the CPU from executing data on the stack (or heap). The kernel enforces this via the page table permission bits (`PTE_NX` on x86-64).

📸 **Screenshot checkpoint 03g** — Capture both `readelf` outputs showing `RW` vs. `RWE`.

---

### Step 3.2 — Observe Executable Memory Regions at Runtime

```bash
docker run --rm python:3.11-slim python3 -c "
with open('/proc/self/maps') as f:
    for line in f:
        if 'x' in line.split()[1]:
            print('EXEC:', line.rstrip())
" | head -8
```

**Expected output:** Only text sections of `python3` and linked libraries appear as executable. The `[stack]` and `[heap]` regions are **not** listed — they are `rw-` only.

!!! tip "What should be executable"
    Legitimate executable regions are: the `.text` section of each binary/library (machine code), the VDSO (virtual dynamic shared object — kernel-provided syscall acceleration), and any JIT-compiled code regions (Python's JIT, for example, maps anonymous executable pages). The stack and heap should never appear here on a correctly hardened system.

📸 **Screenshot checkpoint 03h** — Capture the executable memory regions output, confirming stack and heap are absent from the list.

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
| **03a** | `randomize_va_space` value = `2` | 4 |
| **03b** | Three **different** buffer addresses (ASLR enabled) | 6 |
| **03c** | `/proc/self/maps` output showing memory layout | 4 |
| **03d** | Three **identical** addresses (ASLR disabled with `--privileged`) | 6 |
| **03e** | `objdump` stack_chk count: with canary vs. without | 5 |
| **03f** | "stack smashing detected" termination message | 6 |
| **03g** | `readelf` GNU_STACK comparison: `RW` vs. `RWE` | 5 |
| **03h** | Executable memory regions — stack/heap absent | 4 |
| | **Screenshot Total** | **40** |

---

### Memory Protection Comparison Table

Complete the following table in your lab report (20 points):

| Mitigation | What It Randomizes / Protects | Where the Check Happens | What Attack It Defeats | Known Bypass Technique |
|---|---|---|---|---|
| ASLR (value 2) | | | | |
| Stack canary | | | | |
| NX bit | | | | |

For each row, fill in all four columns based on your lab observations and the Chapter 3 reading.

---

### Reflection Questions

Answer each question in 3–5 sentences. (40 points — 10 points each)

**Question 1**

ASLR randomizes the memory layout of each new process. Explain how this defeats a **return-address-overwrite** exploit that works without ASLR — specifically, what does the attacker no longer know, and why does that matter? Then explain what a **brute-force against ASLR** attack is, and why it is much more practical against a 32-bit address space than a 64-bit one. (Hint: calculate the approximate number of possible base addresses in each case.)

---

**Question 2**

A stack canary is a random value inserted between the local variables and the saved return address on the stack. Describe precisely **where** the canary value is stored at runtime (both the "template" copy and the stack copy), **when** the comparison happens in program execution, and **what happens** if the comparison fails. Why is the canary random rather than a fixed value like `0xDEADBEEF`?

---

**Question 3**

The NX bit marks the stack segment as non-executable (`RW` instead of `RWE`). Name the classic exploit technique that this directly defeats, and briefly describe how that technique worked before NX was available. Then name the bypass technique attackers developed in response to NX — explain what ROP (Return-Oriented Programming) is and why it does not require injecting new code.

---

**Question 4**

ASLR, stack canaries, and NX are three independent layers of defense. A skilled attacker with (a) an information-leak vulnerability to defeat ASLR, (b) a ROP chain to defeat NX, and (c) a way to avoid triggering the canary can theoretically defeat all three simultaneously. Does this mean these mitigations are useless? Explain the concrete security value of layered defenses even when each layer can be individually bypassed — consider the attacker's cost in time, expertise, and reliability.

---

### Grading Rubric

| Component | Points |
|---|---|
| Screenshots (8 × weighted) | 40 |
| Memory protection comparison table | 20 |
| Reflection questions (4 × 10) | 40 |
| **Total** | **100** |

!!! tip "Reflection grading criteria"
    Full credit requires demonstrating understanding of the **mechanism** (how the mitigation works technically), the **threat model** (what specific attack it defeats), and the **limitations** (how it can be bypassed or what it does not cover). One-sentence answers receive a maximum of 3/10 regardless of correctness.
