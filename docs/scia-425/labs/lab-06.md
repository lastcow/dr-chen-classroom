---
title: "Lab 06: Fuzzing & Dynamic Testing"
course: SCIA-425
topic: Dynamic Testing and Fuzzing
week: 7
difficulty: ⭐⭐⭐
estimated_time: 90 minutes
---

# Lab 06: Fuzzing & Dynamic Testing

| Field | Details |
|---|---|
| **Course** | SCIA-425 — Software Assurance and Quality |
| **Week** | 7 |
| **Difficulty** | ⭐⭐⭐ Advanced |
| **Estimated Time** | 90 minutes |
| **Topic** | Dynamic Testing and Fuzzing |
| **Prerequisites** | Python 3.10+, `pip install hypothesis pytest` |
| **Deliverables** | `test_fuzz_parser.py`, `fuzz_findings.md`, `test_properties.py` |

---

## Overview

Fuzzing automatically generates random, malformed, or adversarial inputs to find crashes, assertion failures, and unexpected behavior that manual testing misses. In this lab you will use **Hypothesis** (property-based fuzzing) to fuzz a custom configuration file parser, find real bugs in a deliberately buggy implementation, and document your findings.

---

## The System Under Test

```python
# config_parser.py — CONTAINS INTENTIONAL BUGS — FOR LAB USE ONLY
"""
A simple INI-style configuration parser.
Format:
  [section_name]
  key = value
  key2 = value2

Rules:
  - Section names must be alphanumeric + underscores only
  - Keys must be alphanumeric + underscores only
  - Values can be any string (trimmed of whitespace)
  - Comments start with # or ;
  - Empty lines are ignored
  - Duplicate keys within a section: last value wins
  - Duplicate sections: merged
"""

def parse_config(text: str) -> dict:
    """
    Parse INI-style config text.
    Returns: dict of {section: {key: value}}
    Raises: ValueError for invalid section/key names
    """
    result = {}
    current_section = None

    for line_num, line in enumerate(text.splitlines(), 1):
        line = line.strip()

        # Skip empty lines and comments
        if not line or line[0] in ('#', ';'):
            continue

        # Section header
        if line.startswith('['):
            if not line.endswith(']'):
                raise ValueError(f"Line {line_num}: Unclosed section bracket")
            section_name = line[1:-1]
            # BUG 1: Missing validation — allows empty section name ""
            # BUG 2: No check for whitespace-only section name
            if not all(c.isalnum() or c == '_' for c in section_name):
                raise ValueError(f"Line {line_num}: Invalid section name '{section_name}'")
            current_section = section_name
            if current_section not in result:
                result[current_section] = {}
            continue

        # Key = Value
        if '=' not in line:
            raise ValueError(f"Line {line_num}: Expected 'key = value', got: {line!r}")

        key, _, value = line.partition('=')
        key = key.strip()
        value = value.strip()

        # BUG 3: key validation uses wrong variable (validates value, not key)
        if not all(c.isalnum() or c == '_' for c in value):
            pass  # should validate key here

        if current_section is None:
            # BUG 4: Should raise an error, instead silently drops the key
            continue

        result[current_section][key] = value

    return result


def get_value(config: dict, section: str, key: str, default=None):
    """Get a value from parsed config, returning default if not found."""
    # BUG 5: KeyError instead of returning default when section missing
    return config[section].get(key, default)


def config_to_string(config: dict) -> str:
    """Serialize config dict back to INI format."""
    lines = []
    for section, keys in config.items():
        lines.append(f"[{section}]")
        for k, v in keys.items():
            lines.append(f"{k} = {v}")
        lines.append("")
    return "\n".join(lines)
```

Save as `config_parser.py`. **Do not modify it** — you are testing it, not fixing it.

---

## Part A — Manual Test Cases (15 pts)

Before fuzzing, write manual tests for the documented behavior in `test_fuzz_parser.py`:

```python
import pytest
from config_parser import parse_config, get_value, config_to_string

class TestBasicParsing:
    def test_simple_section_and_key(self):
        result = parse_config("[database]\nhost = localhost\nport = 5432")
        assert result["database"]["host"] == "localhost"
        assert result["database"]["port"] == "5432"

    def test_comments_ignored(self):
        result = parse_config("# this is a comment\n[app]\nname = test")
        assert "app" in result
        assert len(result) == 1

    def test_duplicate_keys_last_wins(self):
        result = parse_config("[app]\nkey = first\nkey = second")
        assert result["app"]["key"] == "second"

    def test_invalid_section_raises(self):
        with pytest.raises(ValueError):
            parse_config("[invalid-section]")

    # Add 6 more manual tests covering the spec
```

---

## Part B — Property-Based Fuzzing with Hypothesis (40 pts)

Hypothesis generates inputs that satisfy your property definitions, then tries to find values that violate them.

```python
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st
from config_parser import parse_config, config_to_string

# Strategy for valid section names
valid_name = st.text(alphabet=st.characters(whitelist_categories=('Lu','Ll','Nd'),
                     whitelist_characters='_'), min_size=1, max_size=20)

# Strategy for valid config dicts
valid_config = st.dictionaries(
    keys=valid_name,
    values=st.dictionaries(keys=valid_name, values=st.text(max_size=50), max_size=5),
    max_size=5
)

@given(valid_config)
@settings(max_examples=500, suppress_health_check=[HealthCheck.too_slow])
def test_roundtrip_property(config):
    """Property: serialize then parse should recover original config."""
    serialized = config_to_string(config)
    recovered = parse_config(serialized)
    assert recovered == config, f"Roundtrip failed:\nOriginal: {config}\nRecovered: {recovered}"

@given(st.text())
@settings(max_examples=1000)
def test_no_crash_on_arbitrary_input(text):
    """Property: parse_config should either return a dict or raise ValueError — never crash."""
    try:
        result = parse_config(text)
        assert isinstance(result, dict)
    except ValueError:
        pass  # acceptable
    except Exception as e:
        raise AssertionError(f"Unexpected exception on input {text!r}: {type(e).__name__}: {e}")

@given(valid_name, valid_name, st.text(max_size=50))
def test_get_value_never_raises_on_valid_config(section, key, value):
    """Property: get_value with a default should never raise KeyError."""
    config = {section: {key: value}}
    # This should return the value or the default — never raise
    result = get_value(config, section, key, default="MISSING")
    assert result == value

@given(valid_name, valid_name)
def test_get_value_missing_section_returns_default(section, key):
    """Property: get_value on a missing section returns default, not error."""
    config = {}
    result = get_value(config, section, key, default="DEFAULT")
    assert result == "DEFAULT"
```

Run:
```bash
pytest test_fuzz_parser.py -v --tb=short
```

Hypothesis will find the bugs. **Let it run and capture the failing examples.** Do not fix `config_parser.py`.

---

## Part C — Document Findings (30 pts)

Write `fuzz_findings.md` documenting every bug Hypothesis found:

```markdown
## Bug Report: config_parser.py

### BUG-001: [Title]

**Discovered by:** Hypothesis (`test_roundtrip_property`)

**Minimal reproducing input:**
```python
parse_config("[]")  # empty section name
```

**Expected behavior:** `ValueError: Invalid section name ''`

**Actual behavior:** Returns `{"": {}}` — empty string section silently accepted

**Root cause:** Line 30 — `if not all(c.isalnum() ... for c in section_name)` — `all()` on an empty string returns `True` vacuously

**CWE reference:** CWE-20 — Improper Input Validation

**Fix:** Add `if not section_name:` check before the `all()` validation

---
```

Document **each bug found** (expect 3–5). For each:
- Which property test found it
- Minimal reproducing input (Hypothesis shrinks to the simplest failing case)
- Expected vs actual behavior
- Root cause (line number)
- CWE reference
- Proposed fix

---

## Part D — Write Additional Properties (15 pts)

Add **3 more property tests** of your own to `test_fuzz_parser.py` that test behaviors not covered above. Each must:
- Have a clear property docstring explaining what invariant you're testing
- Use `@given` with appropriate strategies
- Potentially reveal a bug (or confirm correct behavior)

Ideas:
- Idempotency: parsing a valid config twice gives the same result
- Section count never exceeds input section headers
- Comments never appear in output dict keys

---

## Verification

```bash
# Run all tests, Hypothesis output shows found examples
pytest test_fuzz_parser.py -v 2>&1 | tee fuzz_output.txt

# Show Hypothesis database of found examples
ls .hypothesis/
```

---

## Submission Checklist

- [ ] `config_parser.py` — original, unmodified
- [ ] `test_fuzz_parser.py` — Part A manual tests + Part B properties + Part D new properties
- [ ] `fuzz_findings.md` — all bugs documented (3+ bugs)
- [ ] `fuzz_output.txt` — pytest run showing Hypothesis failures

---

## Grading

| Component | Points |
|-----------|--------|
| Part A — 10+ manual tests, all documented behaviors covered | 15 |
| Part B — 4 property tests implemented, Hypothesis finds bugs | 40 |
| Part C — fuzz_findings.md (3+ bugs, correct CWE, root cause) | 30 |
| Part D — 3 additional properties with clear invariants | 15 |
| **Total** | **100** |
