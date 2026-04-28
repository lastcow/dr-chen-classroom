---
title: "Lab 11: Corporate Portal Design"
course: ITEC-442
topic: Corporate Portals & Knowledge Management
week: 11
difficulty: ⭐⭐
estimated_time: 75 minutes
---

# Lab 11: Corporate Portal Design

| Field | Details |
|---|---|
| **Course** | ITEC-442 — Electronic Commerce |
| **Week** | 11 |
| **Difficulty** | ⭐⭐ Intermediate |
| **Estimated Time** | 75 minutes |
| **Topic** | Corporate Portals & Knowledge Management |
| **Prerequisites** | None — design and analysis lab |
| **Deliverables** | `portal_design.md`, `information_architecture.md`, `governance_plan.md` |

---

## Overview

Corporate portals are mission-critical B2B infrastructure — employee intranets, supplier portals, dealer portals, and partner extranets handle billions of dollars in commerce. In this lab you will design a complete corporate portal for a realistic scenario: a multi-location retail franchise. You will create an information architecture, access control model, search strategy, and content governance plan.

---

## Scenario

**FrostBurger** is a fast-food franchise with 250 locations across 15 states. You have been hired to design their **Franchisee Portal** — a secure web portal where franchise owners and their managers access operational resources, place supply orders, submit reports, receive communications from corporate, and access training materials.

**Current state:** Franchisees email everything. Corporate sends PDF attachments. There is no central system.

---

## Part A — Stakeholder & Requirements Analysis (15 pts)

Document in `portal_design.md`:

**1. Stakeholder Map**

| Stakeholder | Role | Portal Needs | Pain Points Today |
|------------|------|-------------|------------------|
| Franchise Owner | Business owner, 1–3 locations | Financial reports, supply ordering, policy updates | Email overload, lost attachments |
| Store Manager | Day-to-day operations | Staff schedules, training, compliance checklists | No central training library |
| Corporate Operations | Policy, standards, support | Broadcast communications, compliance monitoring | No way to know if franchisees read updates |
| Corporate Supply Chain | Vendor management | Supply order management, inventory | Manual order processing via email |
| Training Team | Onboarding, compliance training | Course delivery, completion tracking | No LMS |
| IT/Admin | Portal management | User management, permissions | (new role) |

**2. Feature Priority Matrix**

Rank these features as **Must Have / Should Have / Could Have / Won't Have** for launch:

| Feature | Priority | Rationale |
|---------|---------|-----------|
| Supply ordering | | |
| Training library | | |
| Policy document library | | |
| Financial reporting dashboard | | |
| Compliance checklist submission | | |
| Announcements & news feed | | |
| Support ticket system | | |
| Discussion forums | | |
| Employee directory | | |
| Mobile app | | |

---

## Part B — Information Architecture (25 pts)

Design the portal's information architecture in `information_architecture.md`.

**1. Site Map**

```
FrostBurger Franchisee Portal
├── Dashboard (personalized home)
│   ├── My Announcements
│   ├── Pending Actions
│   ├── Quick Links
│   └── My Location Summary
│
├── Orders & Supply
│   ├── Place New Order
│   ├── Order History
│   ├── Approved Vendors
│   └── Inventory Levels
│
├── Training Center
│   ├── My Courses
│   ├── Course Catalog
│   ├── Certifications
│   └── Training Reports
│
├── Operations
│   ├── Policy Library
│   ├── Compliance Checklists
│   ├── Standard Operating Procedures
│   └── Brand Standards
│
├── Financials
│   ├── Sales Reports
│   ├── Royalty Statements
│   └── P&L Dashboard
│
├── Support
│   ├── Submit a Ticket
│   ├── Knowledge Base
│   └── Contact Corporate
│
└── Admin (corporate only)
    ├── User Management
    ├── Content Publishing
    └── Analytics
```

Extend this site map with 3 more sub-levels for the areas you think need the most depth.

**2. Navigation Design**

Decide on the navigation pattern (top nav, left sidebar, mega menu, breadcrumbs) and explain why for this specific user base (franchise owners are not tech-savvy; they visit 2–3 times per week from phones).

**3. Search Strategy**

Design the search experience:
- What content types should be searchable?
- How should results be ranked (recency? relevance? content type?)
- What metadata/tags should content authors be required to enter?
- How do you handle misspellings and synonyms? (e.g., "franchise agreement" = "FA" = "operating agreement")

---

## Part C — Access Control Model (20 pts)

Design the role-based access model:

```markdown
## Portal Access Control Matrix

| Content / Feature | Franchise Owner | Store Manager | Corporate Ops | Supply Chain | Training | IT Admin |
|------------------|:---:|:---:|:---:|:---:|:---:|:---:|
| Own location orders | R/W | R | R | R/W | — | R |
| All locations orders | — | — | R | R/W | — | R |
| Financial reports (own) | R | — | R | — | — | R |
| Financial reports (all) | — | — | R/W | — | — | R |
| Training content (take) | R/W | R/W | — | — | — | R |
| Training content (create) | — | — | — | — | R/W | R |
| Policy library | R | R | R/W | — | — | R |
| Compliance submissions | R/W | R/W | R | — | — | R |
| User management (own) | R | — | — | — | — | R/W |
| User management (all) | — | — | — | — | — | R/W |
| Announcements (view) | R | R | R | R | R | R |
| Announcements (create) | — | — | R/W | — | — | R |

R=Read, W=Write, R/W=Read+Write, —=No Access
```

Extend this table to cover all features from your Part A priority matrix.

Then answer:
1. How do you handle a franchise owner who sells their franchise? (account transition)
2. How do you grant temporary elevated access (e.g., a store manager covering while owner is away)?
3. How do you audit who accessed which document and when?

---

## Part D — Knowledge Management Strategy (25 pts)

Write a 600-word knowledge management strategy in `portal_design.md`:

**1. Taxonomy Design**
Design a 3-level taxonomy for the FrostBurger policy library:
```
Level 1: Domain (Operations, HR, Marketing, Finance, Legal)
  Level 2: Sub-domain (e.g., Operations → Food Safety, Customer Service, Equipment)
    Level 3: Document type (Policy, Procedure, Form, Template, Reference)
```

**2. Content Lifecycle**
Define the lifecycle for a policy document:
- Draft → Review → Approve → Publish → Periodic Review (how often?) → Archive/Retire

**3. Content Governance**
Answer these governance questions:
- Who owns each content area? (content owner = accountable for accuracy)
- What is the review cadence for different content types?
- What happens when a policy changes — how do franchisees get notified?
- How do you handle translated content for Spanish-speaking managers?

**4. Search & Discovery**
- What metadata must every document have? (title, owner, effective date, expiry, tags)
- How do you prevent outdated content from appearing in search?
- What is the process for a franchisee to request a missing document?

---

## Part E — Portal Success Metrics (15 pts)

Define how you will measure the portal's success in `governance_plan.md`:

| Metric | Definition | Target | Measurement |
|--------|-----------|--------|-------------|
| Active users (WAU) | Unique users in a week | ≥80% of franchise owners | Analytics |
| Training completion rate | % of required courses complete | ≥90% | LMS report |
| Order digitization rate | Online orders / total orders | ≥95% | Supply system |
| Policy acknowledgment rate | % who acknowledge new policies | ≥98% | Portal tracking |
| Support ticket resolution | Avg hours to resolution | ≤48h | Ticketing system |
| Search success rate | Searches ending without refinement | ≥70% | Analytics |
| Mobile usage % | Sessions from mobile/tablet | Track trend | Analytics |

For each metric, add:
- **Why it matters** (1 sentence)
- **Leading indicator** that predicts this metric
- **What you'd do** if it drops below target

---

## Submission Checklist

- [ ] `portal_design.md` — Parts A, D complete
- [ ] `information_architecture.md` — Parts B, C complete
- [ ] `governance_plan.md` — Part E complete (metrics table with rationale)

---

## Grading

| Component | Points |
|-----------|--------|
| Part A — Stakeholder map + feature priority matrix | 15 |
| Part B — Information architecture (site map + navigation + search) | 25 |
| Part C — Access control matrix (complete + 3 scenario answers) | 20 |
| Part D — Knowledge management strategy (600 words, all 4 sections) | 25 |
| Part E — Success metrics (7 KPIs with leading indicators) | 15 |
| **Total** | **100** |
