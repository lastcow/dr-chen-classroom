---
title: "Lab 09: Formal Verification & Model Checking"
course: SCIA-425
topic: Formal Methods and Correctness Verification
week: 11
difficulty: ⭐⭐⭐⭐
estimated_time: 100 minutes
---

# Lab 09: Formal Verification & Model Checking

| Field | Details |
|---|---|
| **Course** | SCIA-425 — Software Assurance and Quality |
| **Week** | 11 |
| **Difficulty** | ⭐⭐⭐⭐ Expert |
| **Estimated Time** | 100 minutes |
| **Topic** | Formal Methods and Correctness Verification |
| **Prerequisites** | Docker installed and running, `pip install z3-solver` |
| **Deliverables** | `verify_auth.py` Z3 proof, `verify_protocol.py` output, `formal_analysis.md` |

---

## Overview

Formal methods use mathematical logic to *prove* properties about software — not just test them. While testing can find bugs, formal verification can prove their absence. In this lab you will use the **Z3 theorem prover** to verify security properties of an access control policy and a simple authentication protocol, producing machine-checkable proofs.

---

## Part A — Z3 Basics: Access Control Verification (25 pts)

The Z3 SMT solver can verify that a policy is correct — or find a counterexample that violates it.

```bash
pip install z3-solver
```

Create `verify_access_control.py`:

```python
from z3 import *

# ── Domain Setup ──────────────────────────────────────────────────
# We model a Role-Based Access Control policy for a hospital system.
# Roles: NURSE, DOCTOR, ADMIN, AUDITOR
# Resources: PATIENT_RECORDS, BILLING, PRESCRIPTIONS, AUDIT_LOGS, ADMIN_CONFIG

Role = Datatype('Role')
Role.declare('NURSE')
Role.declare('DOCTOR')
Role.declare('ADMIN')
Role.declare('AUDITOR')
Role = Role.create()

Resource = Datatype('Resource')
Resource.declare('PATIENT_RECORDS')
Resource.declare('BILLING')
Resource.declare('PRESCRIPTIONS')
Resource.declare('AUDIT_LOGS')
Resource.declare('ADMIN_CONFIG')
Resource = Resource.create()

# Access function: can_access(role, resource) -> Bool
can_access = Function('can_access', Role, Resource, BoolSort())

# ── Policy Axioms ─────────────────────────────────────────────────
solver = Solver()

# Doctors can access patient records and prescriptions
solver.add(can_access(Role.DOCTOR, Resource.PATIENT_RECORDS) == True)
solver.add(can_access(Role.DOCTOR, Resource.PRESCRIPTIONS) == True)
solver.add(can_access(Role.DOCTOR, Resource.BILLING) == False)
solver.add(can_access(Role.DOCTOR, Resource.AUDIT_LOGS) == False)
solver.add(can_access(Role.DOCTOR, Resource.ADMIN_CONFIG) == False)

# Nurses can access patient records only
solver.add(can_access(Role.NURSE, Resource.PATIENT_RECORDS) == True)
solver.add(can_access(Role.NURSE, Resource.PRESCRIPTIONS) == False)
solver.add(can_access(Role.NURSE, Resource.BILLING) == False)
solver.add(can_access(Role.NURSE, Resource.AUDIT_LOGS) == False)
solver.add(can_access(Role.NURSE, Resource.ADMIN_CONFIG) == False)

# Admins can access billing and admin config, NOT patient records
solver.add(can_access(Role.ADMIN, Resource.PATIENT_RECORDS) == False)
solver.add(can_access(Role.ADMIN, Resource.BILLING) == True)
solver.add(can_access(Role.ADMIN, Resource.PRESCRIPTIONS) == False)
solver.add(can_access(Role.ADMIN, Resource.AUDIT_LOGS) == False)
solver.add(can_access(Role.ADMIN, Resource.ADMIN_CONFIG) == True)

# Auditors can access audit logs only
solver.add(can_access(Role.AUDITOR, Resource.PATIENT_RECORDS) == False)
solver.add(can_access(Role.AUDITOR, Resource.BILLING) == False)
solver.add(can_access(Role.AUDITOR, Resource.PRESCRIPTIONS) == False)
solver.add(can_access(Role.AUDITOR, Resource.AUDIT_LOGS) == True)
solver.add(can_access(Role.AUDITOR, Resource.ADMIN_CONFIG) == False)

# ── Property Verification ─────────────────────────────────────────

def verify_property(name: str, property_formula):
    """Try to find a counterexample to the property. If UNSAT, property holds."""
    s = Solver()
    for c in solver.assertions():
        s.add(c)
    # Add negation of property — if UNSAT, property is proven
    s.add(Not(property_formula))
    result = s.check()
    if result == unsat:
        print(f"PROVED ✓  {name}")
    elif result == sat:
        print(f"VIOLATED ✗  {name}")
        print(f"  Counterexample: {s.model()}")
    else:
        print(f"UNKNOWN   {name}")

r = Const('r', Role)

# Property 1: Separation of Duty — no role has access to both patient records AND admin config
verify_property(
    "SoD: No role accesses both PATIENT_RECORDS and ADMIN_CONFIG",
    ForAll([r], Not(And(can_access(r, Resource.PATIENT_RECORDS),
                        can_access(r, Resource.ADMIN_CONFIG))))
)

# Property 2: Least Privilege — nurses cannot access prescriptions
verify_property(
    "LeastPriv: NURSE cannot access PRESCRIPTIONS",
    can_access(Role.NURSE, Resource.PRESCRIPTIONS) == False
)

# Property 3: Auditors are read-only (can only access audit logs)
res = Const('res', Resource)
verify_property(
    "AuditOnly: AUDITOR can only access AUDIT_LOGS",
    ForAll([res], Implies(
        can_access(Role.AUDITOR, res),
        res == Resource.AUDIT_LOGS
    ))
)

# YOUR PROPERTIES (required for Part A credit):
# Add 3 more meaningful security properties and verify them.
# Examples: "no two roles share identical access", "admin cannot read PHI"
```

Run:
```bash
python verify_access_control.py
```

All three pre-written properties should show PROVED. Add and verify 3 more.

---

## Part B — Protocol Verification: Broken Authentication (35 pts)

We'll verify a simplified authentication protocol and prove (or disprove) its security properties.

Create `verify_protocol.py`:

```python
from z3 import *

# ── Authentication Protocol Model ────────────────────────────────
# Protocol: Client proves identity to Server using a token.
#
# Steps:
#   1. Client sends (username, token) to Server
#   2. Server checks: token == HMAC(secret, username + nonce)
#   3. Server checks: nonce not previously seen (replay protection)
#   4. Server grants access if both checks pass
#
# BUGGY VERSION: The nonce check is missing (replay attack possible)

# Sorts
Token, (valid_token, invalid_token) = EnumSort('Token', ['valid', 'invalid'])
Nonce, (fresh_nonce, replayed_nonce) = EnumSort('Nonce', ['fresh', 'replayed'])

# Protocol predicates
token_valid = Function('token_valid', Token, BoolSort())
nonce_fresh = Function('nonce_fresh', Nonce, BoolSort())
access_granted = Function('access_granted', Token, Nonce, BoolSort())

s = Solver()

# Token validity axioms
s.add(token_valid(valid_token) == True)
s.add(token_valid(invalid_token) == False)

# Nonce freshness axioms
s.add(nonce_fresh(fresh_nonce) == True)
s.add(nonce_fresh(replayed_nonce) == False)

# BUGGY protocol: grants access on valid token regardless of nonce
s.add(ForAll([Const('t', Token), Const('n', Nonce)],
    access_granted(Const('t', Token), Const('n', Nonce)) == token_valid(Const('t', Token))
))

t = Const('t', Token)
n = Const('n', Nonce)

# ── Verify Security Properties ────────────────────────────────────
def check(name, formula):
    chk = Solver()
    for c in s.assertions():
        chk.add(c)
    chk.add(Not(formula))
    result = chk.check()
    status = "PROVED ✓" if result == unsat else "VIOLATED ✗"
    print(f"{status}  {name}")
    if result == sat:
        print(f"  Counterexample: {chk.model()}")

# Property: Only valid tokens get access (should hold)
check("AuthN: Invalid token is always denied",
    ForAll([n], Not(access_granted(invalid_token, n))))

# Property: Replay attack is impossible (should be VIOLATED in buggy version)
check("Replay: Replayed nonce is always denied",
    ForAll([t], Not(access_granted(t, replayed_nonce))))

print()
print("--- FIXED PROTOCOL ---")

# Fix: add nonce check to access_granted
s2 = Solver()
s2.add(token_valid(valid_token) == True)
s2.add(token_valid(invalid_token) == False)
s2.add(nonce_fresh(fresh_nonce) == True)
s2.add(nonce_fresh(replayed_nonce) == False)

# Correct protocol: requires BOTH valid token AND fresh nonce
t2 = Const('t', Token)
n2 = Const('n', Nonce)
s2.add(ForAll([Const('t2', Token), Const('n2', Nonce)],
    access_granted(Const('t2', Token), Const('n2', Nonce)) ==
    And(token_valid(Const('t2', Token)), nonce_fresh(Const('n2', Nonce)))
))

def check2(name, formula):
    chk = Solver()
    for c in s2.assertions():
        chk.add(c)
    chk.add(Not(formula))
    result = chk.check()
    status = "PROVED ✓" if result == unsat else "VIOLATED ✗"
    print(f"{status}  {name}")

check2("Fixed: Invalid token denied", ForAll([n2], Not(access_granted(invalid_token, n2))))
check2("Fixed: Replayed nonce denied", ForAll([t2], Not(access_granted(t2, replayed_nonce))))
check2("Fixed: Valid token + fresh nonce grants access",
       access_granted(valid_token, fresh_nonce) == True)
```

**In `formal_analysis.md` explain:**
1. Why does the BUGGY protocol fail the replay property? (Cite the specific axiom)
2. What real-world attack does a replayed token enable?
3. How does the FIXED protocol axiom differ? Why does it now satisfy both properties?

---

## Part C — Write Your Own Formal Specification (25 pts)

Model and verify the following policy using Z3. You define the sorts, functions, axioms, and properties:

**Policy:** A file system access control policy for a multi-tenant SaaS application:
- Each file belongs to exactly one tenant
- Users belong to exactly one tenant
- Users can only access files belonging to their own tenant
- Admin users can access files from any tenant
- No user (even admin) can delete a file owned by another tenant

Requirements:
- Define at least 3 Z3 sorts (User, Tenant, File, or similar)
- Define at least 4 functions (belongs_to, can_read, can_write, can_delete, etc.)
- State at least 5 policy axioms
- Verify at least 4 security properties (prove or disprove)

Save as `verify_filesystem.py`.

---

## Part D — Formal Analysis Report (15 pts)

Write `formal_analysis.md` covering:

1. **What does PROVED mean?** (in terms of Z3's SAT/UNSAT)
2. **Limitations** — what can Z3 NOT prove about real software?
3. **Access Control results** — which of your 3 custom properties held and which (if any) revealed a policy bug?
4. **Protocol vulnerability** — explain the replay attack in plain English for a non-technical audience
5. **Industry use** — where are formal methods used in real security-critical software? (1 real-world example)

---

## Submission Checklist

- [ ] `verify_access_control.py` — runs, all properties print PROVED or VIOLATED
- [ ] `verify_protocol.py` — runs, buggy shows VIOLATED, fixed shows PROVED
- [ ] `verify_filesystem.py` — your policy model (5+ axioms, 4+ properties)
- [ ] `formal_analysis.md` — all 5 sections

---

## Grading

| Component | Points |
|-----------|--------|
| Part A — verify_access_control.py (3 pre-written PROVED + 3 custom properties) | 25 |
| Part B — verify_protocol.py (correct output, replay bug identified) | 35 |
| Part C — verify_filesystem.py (complete model, 4+ properties verified) | 25 |
| Part D — formal_analysis.md (all 5 sections, clear explanations) | 15 |
| **Total** | **100** |
