---
title: "Lab 05: Test Design — Coverage, Equivalence & Mutation"
course: SCIA-425
topic: Software Testing Fundamentals and Taxonomy
week: 6
difficulty: ⭐⭐⭐
estimated_time: 90 minutes
---

# Lab 05: Test Design — Coverage, Equivalence & Mutation

| Field | Details |
|---|---|
| **Course** | SCIA-425 — Software Assurance and Quality |
| **Week** | 6 |
| **Difficulty** | ⭐⭐⭐ Advanced |
| **Estimated Time** | 90 minutes |
| **Topic** | Software Testing Fundamentals and Taxonomy |
| **Prerequisites** | Python 3.10+, `pip install pytest pytest-cov mutmut` |
| **Deliverables** | `test_password_policy.py`, coverage report ≥80%, mutation score ≥60% |

---

## Overview

Knowing *how* to write a test is one thing. Knowing *how many tests are enough* — and whether your tests can actually catch real bugs — is the harder problem. In this lab you will practice **equivalence class partitioning**, **boundary value analysis**, achieve ≥80% statement coverage, and then use **mutation testing** to verify your tests are actually sensitive to code changes.

---

## The System Under Test

```python
# password_policy.py — DO NOT MODIFY
import re
import hashlib

COMMON_PASSWORDS = {
    "password", "123456", "password123", "qwerty", "letmein",
    "admin", "welcome", "monkey", "dragon", "master"
}

def validate_password(password: str) -> dict:
    """
    Validates a password against the security policy.

    Returns:
        dict with keys:
          - valid (bool): True if all rules pass
          - score (int): 0-100 strength score
          - failures (list[str]): list of failed rules
    """
    if not isinstance(password, str):
        raise TypeError("Password must be a string")

    failures = []
    score = 0

    # Rule 1: Length
    if len(password) < 8:
        failures.append("TOO_SHORT: minimum 8 characters")
    elif len(password) >= 16:
        score += 30
    else:
        score += 15

    # Rule 2: Uppercase
    if not re.search(r'[A-Z]', password):
        failures.append("NO_UPPERCASE: must contain at least one uppercase letter")
    else:
        score += 15

    # Rule 3: Lowercase
    if not re.search(r'[a-z]', password):
        failures.append("NO_LOWERCASE: must contain at least one lowercase letter")
    else:
        score += 15

    # Rule 4: Digit
    if not re.search(r'\d', password):
        failures.append("NO_DIGIT: must contain at least one digit")
    else:
        score += 15

    # Rule 5: Special character
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
        failures.append("NO_SPECIAL: must contain at least one special character")
    else:
        score += 15

    # Rule 6: Common password check
    if password.lower() in COMMON_PASSWORDS:
        failures.append("COMMON_PASSWORD: this password is too common")
        score = max(0, score - 50)

    # Rule 7: No repeating characters (3+ consecutive same character)
    if re.search(r'(.)\1{2,}', password):
        failures.append("REPEATING_CHARS: no 3+ consecutive identical characters")
        score = max(0, score - 10)

    # Rule 8: Max length
    if len(password) > 128:
        failures.append("TOO_LONG: maximum 128 characters")

    valid = len(failures) == 0
    return {"valid": valid, "score": min(100, score), "failures": failures}


def hash_password(password: str) -> str:
    """Returns SHA-256 hex digest of password (for demo only — use bcrypt in prod)."""
    validated = validate_password(password)
    if not validated["valid"]:
        raise ValueError(f"Invalid password: {validated['failures']}")
    return hashlib.sha256(password.encode()).hexdigest()
```

Save this file as-is. **Do not modify it.**

---

## Part A — Equivalence Class Partitioning (20 pts)

Before writing any code, document your test design in `test_design.md`.

**For the `validate_password()` function, identify equivalence classes for each rule:**

| Rule | Valid Class(es) | Invalid Class(es) |
|------|----------------|-------------------|
| Length | 8–128 characters | <8, >128, exactly 0 |
| Uppercase | Contains ≥1 [A-Z] | No uppercase letters |
| ... | | |

Then apply **Boundary Value Analysis** for the length rule:
- Identify all boundary values (exact boundary ± 1)
- List what you expect at each boundary

Complete the table for all 8 rules. This is submitted as part of `test_design.md`.

---

## Part B — Write Tests (40 pts)

Create `test_password_policy.py`. Use the equivalence classes from Part A to write **one test per class minimum**. Include:

```python
import pytest
from password_policy import validate_password, hash_password

# ── Length boundaries ──────────────────────────────────────────────
class TestLength:
    def test_empty_string_invalid(self):
        r = validate_password("")
        assert not r["valid"]
        assert "TOO_SHORT" in r["failures"][0]

    def test_7_chars_invalid(self):
        r = validate_password("Abc1!xx")
        assert not r["valid"]
        assert any("TOO_SHORT" in f for f in r["failures"])

    def test_8_chars_valid(self):
        r = validate_password("Abc1!xyz")
        assert "TOO_SHORT" not in str(r["failures"])

    def test_128_chars_valid(self):
        pwd = "Aa1!" + "x" * 124  # exactly 128
        r = validate_password(pwd)
        assert not any("TOO_LONG" in f for f in r["failures"])

    def test_129_chars_invalid(self):
        pwd = "Aa1!" + "x" * 125  # 129 chars
        r = validate_password(pwd)
        assert any("TOO_LONG" in f for f in r["failures"])

# ── YOUR TESTS ─────────────────────────────────────────────────────
# Add tests for: uppercase, lowercase, digit, special char,
# common password, repeating chars, type error, score values,
# hash_password valid/invalid paths

class TestUppercase:
    # implement...
    pass

class TestScore:
    def test_all_rules_pass_score_positive(self):
        r = validate_password("Str0ng!Pass#2024")
        assert r["valid"]
        assert r["score"] > 50

    def test_16_plus_chars_higher_score(self):
        short = validate_password("Abc1!xyz")        # 8 chars
        long  = validate_password("Abc1!xyzLonger##")  # 16 chars
        assert long["score"] > short["score"]
```

**Requirements:**
- At least **25 test functions** total
- Cover all 8 rules + `hash_password()` success + `hash_password()` failure paths
- Use `pytest.mark.parametrize` for at least one set of tests

---

## Part C — Coverage (20 pts)

Run pytest with coverage:

```bash
pip install pytest-cov
pytest test_password_policy.py -v --cov=password_policy --cov-report=term-missing --cov-report=html
```

**Target: ≥80% statement coverage**

Open `htmlcov/index.html` to see which lines are not covered. Add tests to cover uncovered branches until you reach 80%.

Screenshot the coverage summary line showing your percentage.

In `test_design.md`, note any branches that are genuinely impossible to cover and explain why.

---

## Part D — Mutation Testing (20 pts)

Mutation testing introduces small code changes (mutations) and checks whether your tests catch them. A high mutation score means your tests are actually sensitive to bugs.

```bash
pip install mutmut
mutmut run --paths-to-mutate password_policy.py --tests-dir .
mutmut results
```

**Target: ≥60% mutation score** (killed mutants / total mutants)

Check which mutants survived:
```bash
mutmut show <ID>   # view what the surviving mutant changed
```

For each surviving mutant, either:
1. Add a test that kills it, OR
2. Explain in `test_design.md` why this mutant represents an equivalent mutation (same behavior, different code)

Re-run after adding tests:
```bash
mutmut run --paths-to-mutate password_policy.py --tests-dir .
mutmut results
```

Screenshot the final mutation score.

---

## Verification

```bash
# Must all pass
pytest test_password_policy.py -v

# Coverage must be ≥80%
pytest test_password_policy.py --cov=password_policy --cov-fail-under=80

# Count your tests
pytest test_password_policy.py --collect-only -q | tail -5
```

---

## Submission Checklist

- [ ] `password_policy.py` — original, unmodified
- [ ] `test_design.md` — equivalence classes + BVA table, coverage gaps, surviving mutant analysis
- [ ] `test_password_policy.py` — 25+ tests, all passing
- [ ] Coverage screenshot ≥80%
- [ ] Mutation score screenshot ≥60%

---

## Grading

| Component | Points |
|-----------|--------|
| Part A — test_design.md (complete ECP + BVA tables) | 20 |
| Part B — 25+ test functions, all rules covered, parametrize used | 40 |
| Part C — ≥80% statement coverage (screenshot) | 20 |
| Part D — ≥60% mutation score, surviving mutants analyzed | 20 |
| **Total** | **100** |
