# SCIA 120 Weekly Presentation Fix Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Fix the SCIA-120 presentation navigation, index layout, broken launch links, and regenerate richer weekly presentation content with slide-specific line-art/dialog visuals that match each slide’s topic.

**Architecture:** Keep the MkDocs source in `/home/john/wiki`. Presentation wrapper pages stay as Markdown under `docs/scia-120/presentations/`; full-screen HTML decks stay in `docs/scia-120/presentations/week-XX-deck/index.html`. Use a two-phase generator: first prepare structured PPT content from each weekly reading, then render the deck from that prepared content.

**Tech Stack:** MkDocs Material, static Markdown, standalone HTML/CSS/JS slide decks, generated SVG line art/dialog illustrations, Python content generation scripts, Playwright visual smoke testing.

---

## Acceptance Criteria

1. Navigation: **Presentations** appears immediately after **Reading Materials** under SCIA-120, not inside Reading Materials.
2. Presentation index layout: week title appears cleanly above/beside buttons; it must not merge into the button row.
3. Each weekly wrapper page launch button opens the correct deck.
4. Each deck has richer slide-specific content prepared from the week’s reading material before HTML generation.
5. Dialog/line-art visuals match the actual slide content, not only the weekly index/topic list.
6. Add a line-art/dialog visual block on every slide where it is pedagogically useful; the default target is every slide except purely transitional slides, with at least 26 of 30 slides per deck containing a slide-specific dialog or line-art concept visual.
7. Build passes with `mkdocs build --site-dir /tmp/wiki-site-test`.
8. At least Week 01, Week 02, and Week 15 wrapper/deck pages are visually smoke-tested.
9. Live URLs return HTTP 200 after deployment.

---

## Task 1: Restore SCIA-120 navigation hierarchy

**Objective:** Move `Presentations` out from under `Reading Materials` and place it after Reading Materials under SCIA-120.

**Files:**
- Modify: `/home/john/wiki/mkdocs.yml`

**Steps:**
1. Open the SCIA-120 section in `mkdocs.yml`.
2. Ensure the structure becomes:

```yaml
  - 🔐 SCIA-120:
    - Overview: entities/scia-120.md
    - Reading Materials:
      - Week 1 - Introduction to Information Security: scia-120/chapter-01.md
      # ... Week 15 ...
    - Presentations:
      - Presentations Overview: scia-120/presentations/index.md
      - Week 01 Presentation: scia-120/presentations/week-01.md
      # ... Week 15 ...
    - Labs:
      - Labs Overview: scia-120/labs/index.md
```

3. Remove any nested `Presentations:` block that appears under `Reading Materials`.

**Verification:**

```bash
cd /home/john/wiki
python3 - <<'PY'
from pathlib import Path
s = Path('mkdocs.yml').read_text()
assert '    - Reading Materials:\n' in s
assert '    - Presentations:\n' in s
assert s.index('    - Reading Materials:\n') < s.index('    - Presentations:\n') < s.index('    - Labs:\n')
print('nav hierarchy ok')
PY
```

---

## Task 2: Fix presentation index card layout

**Objective:** Prevent the week title from merging into the button section on `/scia-120/presentations/`.

**Files:**
- Modify: `/home/john/wiki/docs/scia-120/presentations/index.md`

**Implementation:**
Replace the current Markdown list/button layout with explicit HTML cards so MkDocs does not inline the title after the buttons.

Use this pattern for each week:

```html
<div class="presentation-card">
  <h3>Week 02: Physical Security</h3>
  <p>Brief description from the Week 02 reading material...</p>
  <div class="presentation-actions">
    <a class="md-button" href="week-02/">Open presentation page</a>
    <a class="md-button md-button--primary" href="week-02-deck/">Launch deck</a>
  </div>
</div>
```

Add page-local CSS near the top of `index.md`:

```html
<style>
.presentation-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 1.2rem;
  margin-top: 1.5rem;
}
.presentation-card {
  border: 1px solid rgba(63, 81, 181, .24);
  border-radius: 14px;
  padding: 1.1rem 1.2rem;
  background: var(--md-default-bg-color);
  box-shadow: 0 8px 24px rgba(0,0,0,.06);
}
.presentation-card h3 {
  margin: 0 0 .65rem 0 !important;
  line-height: 1.25;
}
.presentation-card p {
  margin: 0 0 1rem 0;
}
.presentation-actions {
  display: flex;
  flex-wrap: wrap;
  gap: .55rem;
  margin-top: .8rem;
}
.presentation-actions .md-button {
  margin: 0 !important;
}
</style>
```

**Verification:**
- Build locally.
- Open `/tmp/wiki-site-test/scia-120/presentations/index.html` with Playwright.
- Screenshot and confirm week titles are separated from buttons.

---

## Task 3: Fix broken launch links on weekly presentation pages

**Objective:** Make the `Launch presentation` button on each weekly wrapper page open the matching deck.

**Files:**
- Modify: `/home/john/wiki/docs/scia-120/presentations/week-01.md` through `week-15.md`

**Likely Cause:** From `week-01.md`, the relative link `week-01-deck/` should build correctly only if the wrapper route is `/scia-120/presentations/week-01/`. If MkDocs rewrites links or the button is interpreted incorrectly, use a root-relative URL to remove ambiguity.

**Implementation:**
Use absolute site-root links in wrappers:

```html
<a class="md-button md-button--primary" href="/scia-120/presentations/week-01-deck/">Launch presentation</a>
<a class="md-button" href="/scia-120/chapter-01/">Open reading material</a>
```

For iframe preview:

```html
<iframe src="/scia-120/presentations/week-01-deck/" ...></iframe>
```

Repeat with the correct week number for all 15 pages.

**Verification:**

```bash
cd /home/john/wiki
mkdocs build --site-dir /tmp/wiki-site-test
python3 - <<'PY'
from pathlib import Path
for i in range(1, 16):
    html = Path(f'/tmp/wiki-site-test/scia-120/presentations/week-{i:02d}/index.html').read_text()
    assert f'/scia-120/presentations/week-{i:02d}-deck/' in html
print('wrapper launch links ok')
PY
```

---

## Task 4: Create structured content-prep JSON for each week

**Objective:** Prepare richer PPT content before deck generation instead of generating directly from headings.

**Files:**
- Create: `/home/john/wiki/scripts/prepare_scia120_presentations.py`
- Create: `/home/john/wiki/docs/scia-120/presentations/_content/week-01.json` through `week-15.json`

**Content Model:**

```json
{
  "week": 1,
  "title": "Introduction to Information Security and Information Assurance",
  "source": "scia-120/chapter-01.md",
  "author": "Dr. Zhijiang Chen",
  "institution": "Frostburg State University",
  "slides": [
    {
      "number": 1,
      "type": "cover",
      "title": "Introduction to Information Security and Information Assurance",
      "subtitle": "Week 01 Presentation",
      "speaker_goal": "Set the frame for the week."
    },
    {
      "number": 8,
      "type": "concept",
      "title": "The CIA Triad",
      "main_idea": "Confidentiality, integrity, and availability define the primary security goals.",
      "details": [
        "Confidentiality protects information from unauthorized disclosure.",
        "Integrity protects information from unauthorized or accidental modification.",
        "Availability keeps systems and data accessible when needed."
      ],
      "classroom_dialog": {
        "scenario": "A student portal is hit by ransomware during registration week.",
        "instructor_prompt": "Which part of the CIA triad is immediately harmed?",
        "student_response": "Availability, because students and staff cannot access the system when they need it.",
        "teaching_point": "Real incidents usually affect more than one CIA goal, but identifying the first failure helps prioritize response."
      },
      "visual_prompt": "Line-art scene: locked database, checksum shield, and uptime monitor connected as a triangle."
    }
  ]
}
```

**Content Rules:**
- Each deck should have exactly 30 slides.
- Every slide should include a `visual_mode` field: `dialog`, `line_art`, or `dialog_plus_line_art`.
- Every non-cover slide must include:
  - `main_idea`
  - 2–4 `details`
  - `classroom_dialog` tied to that slide’s concept
  - `visual_prompt` tied to that slide’s concept
- Cover slides must include at least a slide-specific line-art hero visual.
- Agenda/overall slides must include a line-art overview map plus short dialog prompt.
- The default target is **every slide** having either a dialog block, a line-art visual, or both; only allow exceptions for rare transitional slides, and keep exceptions under 4 slides per deck.
- Use the full weekly reading content, not only headings.
- Include scenario/application slides, not just definitions.

**Verification:**

```bash
cd /home/john/wiki
python3 scripts/prepare_scia120_presentations.py
python3 - <<'PY'
import json
from pathlib import Path
for i in range(1, 16):
    data = json.loads(Path(f'docs/scia-120/presentations/_content/week-{i:02d}.json').read_text())
    assert len(data['slides']) == 30
    for slide in data['slides'][1:]:
        assert slide.get('main_idea')
        assert slide.get('details')
        assert slide.get('classroom_dialog')
        assert slide.get('visual_prompt')
        assert slide.get('visual_mode') in {'dialog','line_art','dialog_plus_line_art'}
print('content prep JSON ok')
PY
```

---

## Task 5: Regenerate decks from prepared content

**Objective:** Generate richer weekly HTML decks from `_content/week-XX.json`.

**Files:**
- Create: `/home/john/wiki/scripts/render_scia120_presentations.py`
- Modify: `/home/john/wiki/docs/scia-120/presentations/week-01-deck/index.html` through `week-15-deck/index.html`

**Rendering Requirements:**
- Keep tech-dark palette.
- Cover page includes:
  - course/week
  - presentation title
  - `Author: Dr. Zhijiang Chen (Frostburg State University)`
- Include an overall/agenda page.
- Slide visuals must use each slide’s `visual_prompt` and `classroom_dialog`, not only the week title.
- Put dialog/line-art on each page wherever possible. Implementation target: at least 26/30 slides per deck contain `.dialog-card`, `.visual`, or both, and most core concept slides use `dialog_plus_line_art`.
- Include classroom dialog blocks on concept/application slides:

```html
<div class="dialog-card">
  <div class="dialog-row instructor">
    <strong>Instructor:</strong> Which part of the CIA triad is harmed first?
  </div>
  <div class="dialog-row student">
    <strong>Student:</strong> Availability, because users cannot access the system.
  </div>
  <div class="teaching-point">
    Teaching point: Real incidents often affect multiple CIA goals.
  </div>
</div>
```

**SVG Visual Strategy:**
- Generate slide-specific SVGs using the `visual_prompt` and slide title.
- Include labels from the actual slide content.
- Avoid reusing the same generic concept map on every slide.

**Verification:**

```bash
cd /home/john/wiki
python3 scripts/render_scia120_presentations.py
python3 - <<'PY'
from pathlib import Path
for i in range(1,16):
    html = Path(f'docs/scia-120/presentations/week-{i:02d}-deck/index.html').read_text()
    assert html.count('class="slide') >= 30
    assert 'Dr. Zhijiang Chen' in html
    assert 'dialog-card' in html
    assert 'AI-generated' in html or 'Line Art' in html
    visual_count = html.count('dialog-card') + html.count('class="visual')
    assert visual_count >= 26, (i, visual_count)
print('deck render ok')
PY
```

---

## Task 6: Regenerate wrapper pages and index from metadata

**Objective:** Ensure the presentation index and each weekly wrapper page are generated consistently from the same metadata/content JSON.

**Files:**
- Modify: `/home/john/wiki/scripts/render_scia120_presentations.py`
- Modify: `/home/john/wiki/docs/scia-120/presentations/index.md`
- Modify: `/home/john/wiki/docs/scia-120/presentations/week-01.md` through `week-15.md`

**Implementation:**
The render script should also produce:
1. `index.md` with clean card grid.
2. `week-XX.md` with:
   - brief description
   - key concepts
   - root-relative launch link
   - root-relative reading link
   - iframe preview using root-relative deck URL

**Verification:**
- No hand-edited inconsistencies.
- Search for old relative launch links:

```bash
cd /home/john/wiki
python3 - <<'PY'
from pathlib import Path
bad=[]
for p in Path('docs/scia-120/presentations').glob('week-??.md'):
    s=p.read_text()
    if 'href="week-' in s or 'src="week-' in s:
        bad.append(str(p))
assert not bad, bad
print('no ambiguous weekly launch links')
PY
```

---

## Task 7: Build and inspect local output

**Objective:** Catch broken nav, Markdown, HTML, and link problems before deploy.

**Files:**
- No file changes expected.

**Commands:**

```bash
cd /home/john/wiki
mkdocs build --site-dir /tmp/wiki-site-test
```

Expected: `Documentation built` with return code 0.

**Additional checks:**

```bash
python3 - <<'PY'
from pathlib import Path
required = [
  '/tmp/wiki-site-test/scia-120/presentations/index.html',
  '/tmp/wiki-site-test/scia-120/presentations/week-01/index.html',
  '/tmp/wiki-site-test/scia-120/presentations/week-01-deck/index.html',
  '/tmp/wiki-site-test/scia-120/presentations/week-15/index.html',
  '/tmp/wiki-site-test/scia-120/presentations/week-15-deck/index.html',
]
for f in required:
    p=Path(f)
    assert p.exists() and p.stat().st_size > 10000, f
print('built presentation pages exist')
PY
```

---

## Task 8: Visual QA with Playwright screenshots

**Objective:** Verify the fixed index and launch pages visually.

**Files:**
- Create temporary QA script: `/tmp/qa_scia120_presentations_fix.js`
- Output screenshots:
  - `/tmp/scia120-presentations-index-fixed.png`
  - `/tmp/scia120-week01-wrapper-fixed.png`
  - `/tmp/scia120-week01-deck-fixed.png`
  - `/tmp/scia120-week02-deck-fixed.png`
  - `/tmp/scia120-week15-deck-fixed.png`

**Checks:**
- Index titles do not merge with buttons.
- Launch buttons are visible and link to correct decks.
- Wrapper preview iframe loads.
- Deck cover is readable.
- Dialog/line-art content appears on nearly every slide checked and matches each slide topic.
- No obvious overflow/cutoff.

**Verification:**
Use `vision_analyze` on at least:
1. index page screenshot
2. week 01 deck cover
3. one dialog slide screenshot

---

## Task 9: Deploy and push

**Objective:** Publish the corrected site and commit source changes.

**Commands:**

```bash
cd /home/john/wiki
mkdocs gh-deploy --force
git status --short
git add mkdocs.yml docs/log.md docs/scia-120/presentations scripts/prepare_scia120_presentations.py scripts/render_scia120_presentations.py
git commit -m "Improve SCIA 120 weekly presentations"
git push origin main
```

**Verification:**
- `mkdocs gh-deploy --force` exits 0.
- `git push origin main` exits 0.
- `git status --short` is clean after push.

---

## Task 10: Verify live URLs

**Objective:** Confirm the deployed pages work on `dr.chen.me`.

**Commands:**

```bash
for url in \
  https://dr.chen.me/scia-120/presentations/ \
  https://dr.chen.me/scia-120/presentations/week-01/ \
  https://dr.chen.me/scia-120/presentations/week-01-deck/ \
  https://dr.chen.me/scia-120/presentations/week-02/ \
  https://dr.chen.me/scia-120/presentations/week-02-deck/ \
  https://dr.chen.me/scia-120/presentations/week-15/ \
  https://dr.chen.me/scia-120/presentations/week-15-deck/
do
  curl -L -sS -H 'Cache-Control: no-cache' -o /tmp/live.html \
    -w "%{http_code} %{url_effective} %{size_download}\n" "$url"
done
```

Expected: all return `200` and non-trivial page sizes.

---

## Risk Notes

- The current generated decks are acceptable structurally but too generic in places. The fix should not simply patch CSS; it needs a content-preparation pass.
- Root-relative links are safer for MkDocs wrapper pages and iframe previews than relative links.
- The old `llm-wiki-sample` files may remain in the repository but should not be shown in SCIA-120 nav unless intentionally kept.
- Generating 15 × 30 richer slides can be done with deterministic templates and extracted reading content; avoid hallucinated extra topics.

---

## Final Report Format

When implementation finishes, report:

- Navigation fixed: yes/no
- Index layout fixed: yes/no + screenshot path
- Weekly launch buttons fixed: yes/no
- Deck content enriched: yes/no
- Dialog/line-art visuals appear on each page as much as possible: yes/no
- Dialog visuals match slide content: yes/no
- Build/deploy status
- Commit hash
- Verified live URLs
