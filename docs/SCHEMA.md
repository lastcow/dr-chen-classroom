# Wiki Schema

## Domain
Dr. Chen's classroom at Frostburg State University — courses, students, assignments, assessments, curriculum, pedagogy, and teaching resources. Covers all courses taught by Dr. Chen, including course materials, learning objectives, student performance patterns, and instructional strategies.

## Conventions
- File names: lowercase, hyphens, no spaces (e.g., `scia-120-overview.md`, `lab-report-rubric.md`)
- Every wiki page starts with YAML frontmatter (see below)
- Use `[[wikilinks]]` to link between pages (minimum 2 outbound links per page)
- When updating a page, always bump the `updated` date
- Every new page must be added to `index.md` under the correct section
- Every action must be appended to `log.md`
- Course codes follow FSU convention: `SCIA-120`, `ITEC-442`, etc.

## Frontmatter
```yaml
---
title: Page Title
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: entity | concept | comparison | query | summary | assignment | rubric
tags: [from taxonomy below]
sources: [raw/articles/source-name.md]
---
```

## Tag Taxonomy

### Courses & Curriculum
- `course` — a specific course (e.g., SCIA-120, ITEC-442)
- `curriculum` — course design, learning outcomes, syllabus structure
- `assignment` — homework, projects, essays, labs
- `quiz` — in-class quizzes and short assessments
- `exam` — midterms and finals
- `rubric` — grading criteria and scoring guides
- `lab` — hands-on laboratory work
- `lecture` — lecture notes, slides, in-class content

### Students & Performance
- `student` — individual student records or profiles
- `performance` — grade patterns, score distributions, trends
- `at-risk` — students needing intervention or extra support
- `feedback` — instructor feedback, comments, annotations
- `participation` — attendance, engagement, discussion contributions

### Pedagogy & Strategy
- `pedagogy` — teaching approaches, instructional design
- `policy` — course policies, late work, academic integrity
- `resource` — external references, textbooks, links
- `technology` — tools used in class (Canvas, LMS, software)

### Meta
- `comparison` — side-by-side analyses
- `summary` — roll-up or synthesized views
- `timeline` — chronological records
- `template` — reusable formats

## Page Thresholds
- **Create a page** when an entity/concept appears in 2+ contexts OR is central to one course
- **Add to existing page** when new information updates something already covered
- **DON'T create a page** for passing mentions or one-time events
- **Split a page** when it exceeds ~200 lines
- **Archive a page** when a course ends and its content is no longer active — move to `_archive/`

## Entity Pages
One page per notable entity (course, student, assignment, instructor tool). Include:
- Overview / what it is
- Key facts and dates
- Relationships to other entities (`[[wikilinks]]`)
- Source references

## Concept Pages
One page per concept or teaching topic. Include:
- Definition / explanation
- How it applies in Dr. Chen's courses
- Related concepts (`[[wikilinks]]`)

## Update Policy
When new information conflicts with existing content:
1. Check the dates — newer sources generally supersede older ones
2. If genuinely contradictory, note both positions with dates and sources
3. Mark the contradiction in frontmatter: `contradictions: [page-name]`
4. Flag for user review in the lint report
