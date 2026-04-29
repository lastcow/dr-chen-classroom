# SCIA 120 Week 01 Presentation Update Plan

> **For Hermes:** Implement this plan inside `/home/john/wiki` and verify with MkDocs before publishing.

**Goal:** Update the SCIA 120 Week 01 presentation so it matches the Week 01 reading material, is enriched with credible internet sources, removes classroom-dialog/teaching-tip content, and presents only student-facing useful content.

**Architecture:** Treat the reading material (`chapter-01.md`) as the primary source of truth. Use `_content/week-01.json` as the editable content model, regenerate or patch `week-01-deck/index.html`, then verify the wrapper page and MkDocs site. Slide visuals should be slide-specific technical line art only, not generic decorative images.

**Tech Stack:** MkDocs Material wiki, markdown, JSON content model, standalone HTML presentation, SVG/line-art visuals, browser/DOM QA, optional web source extraction.

---

## Source Files

**Primary reading source**
- `/home/john/wiki/docs/scia-120/chapter-01.md`

**Presentation files to update**
- `/home/john/wiki/docs/scia-120/presentations/_content/week-01.json`
- `/home/john/wiki/docs/scia-120/presentations/week-01-deck/index.html`
- `/home/john/wiki/docs/scia-120/presentations/week-01.md`

**Wiki bookkeeping**
- `/home/john/wiki/docs/log.md`
- `/home/john/wiki/mkdocs.yml` only if navigation breaks or names need adjustment

---

## Required Content Direction

1. **Student-facing only**
   - Remove all `classroom_dialog`, `instructor_prompt`, `teaching_point`, `speaker_goal`, and similar instructor-only fields/content.
   - Do not include “teaching tips,” “how to teach this,” or instructor notes.
   - Keep “student tasks,” “self-check,” “apply this,” and “what to remember” prompts because those help students.

2. **Match Week 01 reading key points**
   Cover these reading-material concepts in order:
   - Information security vs. cybersecurity
   - Information assurance and trustworthiness
   - CIA Triad: confidentiality, integrity, availability
   - DAD Triad: disclosure, alteration, denial
   - Why security matters: financial, national security, personal, legal/regulatory harm
   - Brief history of computer security
   - Threat actors: script kiddies, hacktivists, cybercriminals, insider threats, nation-states/APTs
   - Attack motivations: MICE — money, ideology, coercion, ego
   - Security mindset: adversarial thinking, skepticism, failure modes, defense in depth, proportionality
   - Risk: threat × vulnerability × impact
   - Risk treatment: avoid, mitigate, transfer, accept
   - Security controls: preventive, detective, corrective; administrative, technical, physical
   - Security lifecycle / NIST CSF: Govern, Identify, Protect, Detect, Respond, Recover
   - Cybersecurity careers and certifications

3. **Detailed explanations from credible sources / AI synthesis**
   Each key point must be explained in enough depth for students to understand the concept without needing the instructor to fill gaps verbally. Do not leave a slide at the level of a keyword list.

   Required treatment for every major key point:
   - Start from the Week 01 reading material.
   - Add a plain-language explanation.
   - Add a concrete example or mini-scenario.
   - Add why it matters in real systems.
   - Add at least one credible source-backed detail when available.
   - Use AI synthesis only to connect and simplify source-backed material, not to invent unsupported facts.

   Suggested credible enrichment sources:
   - NIST CSF 2.0 official page/PDF for Govern, Identify, Protect, Detect, Respond, Recover.
   - CISA Cyber Essentials / Cybersecurity Best Practices for beginner-friendly security actions.
   - IBM Cost of a Data Breach Report 2025 for current breach-cost context.
   - ISC2 Cybersecurity Workforce Study for career/workforce context.
   - CERT/CC or Carnegie Mellon references for Morris Worm / CERT origin if historical detail needs support.
   - NIST glossary, CNSSI, or official government/standards publications for definitions when needed.

4. **Code and shell command policy**
   Code or shell commands may be used only when they directly support the slide topic. Do not add commands just to make slides look technical.

   Appropriate examples:
   - Integrity slide: show a small checksum/hash command to demonstrate detecting file alteration.
   - Availability slide: show a simple `ping` or uptime/status example only if explaining service reachability.
   - Risk/control slide: show a tiny pseudocode or table-based risk scoring example if it improves understanding.
   - Security lifecycle slide: avoid code unless showing how evidence/logs support Detect or Respond.

   Not appropriate:
   - Adding shell commands to definition-only slides.
   - Adding code to career, history, motivation, or roadmap slides unless the slide specifically explains a technical demonstration.
   - Long scripts, exploit commands, or commands unrelated to SCIA 120 Week 01 fundamentals.

5. **Visual policy**
   - Any generated or embedded picture must directly match the slide’s topic.
   - Style: technical line-art design, consistent with cyber/assurance theme.
   - No generic “people talking in class,” no professor/student dialog scenes.
   - Prefer inline SVG diagrams where possible: CIA triangle, DAD mirror, risk equation, security lifecycle loop, threat actor map, controls matrix.

---

## Proposed Slide Structure

Keep the deck around 24–30 slides. Recommended 28-slide sequence:

1. Title — Introduction to Information Security and Information Assurance
2. Week 01 roadmap — what students will learn
3. Learning outcomes — explain, compare, classify, apply
4. The big question — what are we defending and why?
5. Information security — definition and scope
6. Cybersecurity vs. information security — digital subset vs broader information protection
7. Information assurance — trust, usability, reliability, authentication, non-repudiation
8. Security vs. assurance — protect vs prove-and-sustain
9. CIA Triad overview — confidentiality, integrity, availability
10. Confidentiality — examples, threats, controls
11. Integrity — examples, threats, controls
12. Availability — examples, threats, controls
13. DAD Triad — attacker goals mapped to CIA failures
14. Why security matters — financial, personal, national, legal/regulatory impacts
15. Short history timeline — mainframes, PC malware, internet, cybercrime, cloud/ransomware
16. Threat actors overview — capability, intent, motivation
17. Threat actor profiles — script kiddies, hacktivists, cybercriminals
18. Threat actor profiles — insiders, nation-states/APTs
19. Attack motivations — MICE model
20. Security mindset — adversarial thinking and failure modes
21. Risk formula — threat × vulnerability × impact
22. Risk treatment — avoid, mitigate, transfer, accept
23. Control functions — preventive, detective, corrective
24. Control layers — administrative, technical, physical
25. Security lifecycle / NIST CSF 2.0 — Govern, Identify, Protect, Detect, Respond, Recover
26. Student scenario — classify asset, threat, CIA impact, control, evidence
27. Career paths — analyst, pentester, engineer, responder, architect, CISO, GRC
28. Week 01 takeaway / self-check — key terms and review questions

---

## Implementation Tasks

### Task 1: Baseline the current deck

**Objective:** Capture what exists before editing.

**Files:**
- Read: `/home/john/wiki/docs/scia-120/presentations/_content/week-01.json`
- Read: `/home/john/wiki/docs/scia-120/presentations/week-01-deck/index.html`
- Read: `/home/john/wiki/docs/scia-120/presentations/week-01.md`

**Steps:**
1. Count slides in `_content/week-01.json`.
2. Search all Week 01 presentation files for forbidden strings:
   - `classroom_dialog`
   - `dialog`
   - `teaching_point`
   - `teaching tips`
   - `instructor_prompt`
   - `speaker_goal`
3. Extract current slide titles and compare them to the proposed slide sequence.
4. Save a short baseline note in the work log or implementation notes.

**Verification:** Baseline report lists current slide count, forbidden-content hits, and missing reading-material topics.

---

### Task 2: Build the Week 01 content map

**Objective:** Ensure every slide traces to the reading material and/or an external source.

**Files:**
- Read: `/home/john/wiki/docs/scia-120/chapter-01.md`
- Create/update implementation note if needed: `/tmp/scia120-week01-content-map.md`

**Steps:**
1. Map each reading section `1.1` through `1.13` to one or more slides.
2. Mark which slides need external enrichment and what kind of detail each needs: definition, source-backed fact, real-world example, risk implication, or student self-check.
3. Identify exact source URLs for NIST, CISA, IBM, ISC2, and any history/career support.
4. For every proposed slide, write a one-line evidence note: `Reading section + external source/AI synthesis + example used`.
5. Decide where to place citations: slide footer, notes area, or final references slide.

**Verification:** Every major reading section appears in the map; no slide is content-free or only decorative.

---

### Task 3: Rewrite `_content/week-01.json` as student-facing content

**Objective:** Replace instructor-oriented/generated boilerplate with student-facing slide content.

**Files:**
- Modify: `/home/john/wiki/docs/scia-120/presentations/_content/week-01.json`

**Steps:**
1. Keep metadata: week, title, source, author, institution.
2. Update `summary` to describe a student-facing Week 01 deck.
3. Update `key_concepts` to align with the reading key terms.
4. Replace the `slides` array with the proposed 28-slide structure.
5. For each slide, write detailed student-facing content, not just labels:
   - one clear main explanation,
   - 3–5 concise supporting points,
   - one concrete example or mini-scenario when appropriate,
   - why it matters,
   - source references or source notes.
6. For each slide include only student-facing fields, for example:
   - `number`
   - `type`
   - `title`
   - `main_idea`
   - `details`
   - `student_activity` or `self_check` where useful
   - `visual_prompt`
   - `visual_mode: line_art`
   - `visual_kind`
   - `sources`
6. Remove every `classroom_dialog` object and every instructor-only key.

**Verification:** JSON parses successfully and forbidden strings return zero hits except if a source title legitimately contains one.

---

### Task 4: Update the HTML presentation deck

**Objective:** Regenerate or patch the launchable HTML deck using the revised content model.

**Files:**
- Modify: `/home/john/wiki/docs/scia-120/presentations/week-01-deck/index.html`

**Steps:**
1. Preserve the existing visual style if it is working: tech-dark, readable cards, FSU/SCIA 120 identity.
2. Replace slide content with the revised student-facing copy.
3. Remove dialog/persona/classroom sections entirely.
4. Add slide-specific technical diagrams or line-art visuals:
   - CIA triangle
   - DAD mirror-image diagram
   - Risk equation cards
   - Threat actor map
   - Control matrix
   - NIST CSF lifecycle loop
5. Add code/shell snippets only on slides where they directly illustrate the concept. Keep snippets short, safe, and beginner-readable. Do not include unrelated commands or exploit-style commands.
6. Keep images aligned with slide content. Do not reuse generic visuals across unrelated slides.
7. Add concise references where external facts are used.

**Verification:** HTML contains updated slide titles, no forbidden instructional/dialog content, and visuals are topic-specific.

---

### Task 5: Update the wrapper page

**Objective:** Make the MkDocs wrapper accurately describe the revised deck.

**Files:**
- Modify: `/home/john/wiki/docs/scia-120/presentations/week-01.md`

**Steps:**
1. Update the `updated:` date to `2026-04-29`.
2. Rewrite the brief to remove “classroom dialog.”
3. Mention student-facing concepts, applied scenarios, self-check prompts, and line-art visuals.
4. Keep the launch and reading-material buttons.
5. Update key concepts if needed.

**Verification:** Wrapper page has no mention of classroom dialog or teaching tips.

---

### Task 6: Validate site and content

**Objective:** Catch broken HTML, broken wiki navigation, and leftover unwanted content.

**Files:**
- Check: `/home/john/wiki/docs/scia-120/presentations/week-01-deck/index.html`
- Check: `/home/john/wiki/docs/scia-120/presentations/week-01.md`

**Commands:**
```bash
cd /home/john/wiki
python3 -m json.tool docs/scia-120/presentations/_content/week-01.json >/tmp/week01.json.valid
python3 - <<'PY'
from pathlib import Path
forbidden = ['classroom_dialog','teaching_point','teaching tips','instructor_prompt','speaker_goal','Class dialog']
for path in [
  Path('docs/scia-120/presentations/_content/week-01.json'),
  Path('docs/scia-120/presentations/week-01-deck/index.html'),
  Path('docs/scia-120/presentations/week-01.md'),
]:
    text = path.read_text(errors='ignore')
    hits = [f for f in forbidden if f.lower() in text.lower()]
    print(path, hits)
PY
mkdocs build --strict
```

**Expected:** JSON valid, forbidden hit lists empty, MkDocs build passes.

---

### Task 7: Visual QA in browser

**Objective:** Verify the deck is readable and student-ready.

**Steps:**
1. Serve or open the MkDocs/site page.
2. Use browser screenshots/contact sheets to inspect slides.
3. Check for:
   - clipped text
   - overlapping cards
   - unreadable small fonts
   - low contrast
   - generic or mismatched visuals
   - missing citations for enriched facts
   - any teaching-tip/dialog content
4. Fix issues and recheck affected slides.

**Verification:** Full visual pass finds no major slide layout/content issues.

---

### Task 8: Update wiki log

**Objective:** Keep the wiki’s append-only action log current.

**Files:**
- Modify: `/home/john/wiki/docs/log.md`

**Log entry:**
```markdown
## [2026-04-29] update | SCIA 120 Week 01 presentation revised
- Updated `scia-120/presentations/_content/week-01.json` with student-facing content aligned to Chapter 1.
- Updated `scia-120/presentations/week-01-deck/index.html` to remove classroom dialog/teaching tips and add topic-matched technical line-art visuals.
- Updated `scia-120/presentations/week-01.md` wrapper brief.
- Enriched Week 01 concepts with credible external references including NIST CSF, CISA, IBM, and ISC2 where appropriate.
```

**Verification:** Log entry appended once; no duplicate entries.

---

## Acceptance Criteria

- Week 01 deck matches the reading material’s key concepts.
- No class dialog, instructor prompt, teaching tip, or speaker-goal content remains.
- Content is useful directly to students: definitions, examples, models, scenarios, self-checks, career relevance.
- Internet enrichment is credible and relevant, not filler.
- Every visual is slide-specific, technical, and line-art styled.
- Wrapper page accurately describes the revised student-facing deck.
- `mkdocs build --strict` passes.
- Browser/visual QA confirms readability and no major layout defects.
