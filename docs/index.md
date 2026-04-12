---
title: Home
hide:
  - navigation
  - toc
---

<style>
/* ── Reset & Base ─────────────────────────────────────────── */
.md-content { max-width: 100% !important; padding: 0 !important; }
.md-content__inner { padding: 0 !important; margin: 0 !important; }

/* ── Hero Banner ──────────────────────────────────────────── */
.fsu-hero {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 40%, #0f3460 100%);
  border-bottom: 4px solid #c8a951;
  padding: 3rem 2rem 2.5rem;
  text-align: center;
  position: relative;
  overflow: hidden;
}
.fsu-hero::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23c8a951' fill-opacity='0.05'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
  opacity: 0.4;
}
.fsu-hero-content { position: relative; z-index: 1; }
.fsu-logo-link img {
  height: 72px;
  filter: brightness(0) invert(1);
  margin-bottom: 1.2rem;
  transition: opacity 0.2s;
}
.fsu-logo-link:hover img { opacity: 0.85; }
.fsu-hero h1 {
  color: #ffffff;
  font-size: 2.2rem;
  font-weight: 700;
  margin: 0 0 0.3rem;
  letter-spacing: 0.5px;
  text-shadow: 0 2px 8px rgba(0,0,0,0.4);
}
.fsu-hero h1 span { color: #c8a951; }
.fsu-hero .subtitle {
  color: #b0c4de;
  font-size: 1.05rem;
  margin: 0 0 0.5rem;
  font-style: italic;
}
.fsu-hero .instructor-badge {
  display: inline-block;
  background: rgba(200,169,81,0.15);
  border: 1px solid rgba(200,169,81,0.4);
  color: #c8a951;
  padding: 0.3rem 1rem;
  border-radius: 20px;
  font-size: 0.88rem;
  font-weight: 600;
  letter-spacing: 0.5px;
  margin-top: 0.6rem;
}
.fsu-uni-link {
  display: inline-block;
  margin-top: 1rem;
  color: #7eb8f7;
  font-size: 0.85rem;
  text-decoration: none;
  letter-spacing: 0.3px;
}
.fsu-uni-link:hover { color: #c8a951; text-decoration: underline; }
.fsu-uni-link::before { content: '🎓 '; }

/* ── Divider ──────────────────────────────────────────────── */
.fsu-divider {
  height: 3px;
  background: linear-gradient(90deg, transparent, #c8a951, transparent);
  margin: 0;
}

/* ── Info Strip ───────────────────────────────────────────── */
.fsu-infostrip {
  background: #f8f9fa;
  border-bottom: 1px solid #e0e0e0;
  padding: 0.75rem 2rem;
  display: flex;
  justify-content: center;
  gap: 2.5rem;
  flex-wrap: wrap;
  font-size: 0.85rem;
  color: #555;
}
.fsu-infostrip span { display: flex; align-items: center; gap: 0.4rem; }
.fsu-infostrip strong { color: #1a1a2e; }

/* ── Main Content ─────────────────────────────────────────── */
.fsu-main { max-width: 1100px; margin: 0 auto; padding: 2.5rem 1.5rem 3rem; }

/* ── Section Heading ──────────────────────────────────────── */
.fsu-section-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: #1a1a2e;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  border-left: 4px solid #c8a951;
  padding-left: 0.75rem;
  margin: 2.5rem 0 1.25rem;
}

/* ── Course Cards Grid ────────────────────────────────────── */
.fsu-courses {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.25rem;
  margin-bottom: 2rem;
}
.fsu-card {
  background: #fff;
  border: 1px solid #e0e4ec;
  border-radius: 8px;
  padding: 1.25rem 1.4rem;
  text-decoration: none;
  transition: box-shadow 0.2s, transform 0.2s, border-color 0.2s;
  display: block;
  position: relative;
  overflow: hidden;
}
.fsu-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0;
  width: 4px; height: 100%;
  background: #c8a951;
  border-radius: 8px 0 0 8px;
}
.fsu-card:hover {
  box-shadow: 0 6px 24px rgba(0,0,0,0.10);
  transform: translateY(-2px);
  border-color: #c8a951;
  text-decoration: none;
}
.fsu-card-code {
  font-size: 0.72rem;
  font-weight: 700;
  color: #0f3460;
  text-transform: uppercase;
  letter-spacing: 1.2px;
  background: #eef2f8;
  display: inline-block;
  padding: 0.18rem 0.6rem;
  border-radius: 4px;
  margin-bottom: 0.5rem;
}
.fsu-card-title {
  font-size: 0.97rem;
  font-weight: 600;
  color: #1a1a2e;
  margin: 0 0 0.4rem;
  line-height: 1.4;
}
.fsu-card-meta {
  font-size: 0.78rem;
  color: #888;
  margin: 0;
}
.fsu-card-meta span { margin-right: 0.8rem; }
.has-reading { border-top: none; }
.has-reading .fsu-card-code { background: #e8f4e8; color: #2d6a2d; }
.fsu-reading-badge {
  position: absolute;
  top: 0.6rem; right: 0.75rem;
  background: #0f3460;
  color: #c8a951;
  font-size: 0.65rem;
  font-weight: 700;
  padding: 0.15rem 0.5rem;
  border-radius: 10px;
  letter-spacing: 0.5px;
}

/* ── Quick Stats ──────────────────────────────────────────── */
.fsu-stats {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}
.fsu-stat {
  background: #fff;
  border: 1px solid #e0e4ec;
  border-radius: 8px;
  padding: 1.1rem 1rem;
  text-align: center;
}
.fsu-stat-number {
  font-size: 2rem;
  font-weight: 800;
  color: #0f3460;
  line-height: 1;
  margin-bottom: 0.3rem;
}
.fsu-stat-label {
  font-size: 0.75rem;
  color: #777;
  text-transform: uppercase;
  letter-spacing: 0.8px;
}

/* ── Welcome Box ──────────────────────────────────────────── */
.fsu-welcome {
  background: linear-gradient(135deg, #f0f4ff 0%, #fdf8ec 100%);
  border: 1px solid #dde3f0;
  border-left: 4px solid #0f3460;
  border-radius: 8px;
  padding: 1.5rem 1.75rem;
  margin-bottom: 2rem;
  font-size: 0.95rem;
  line-height: 1.75;
  color: #333;
}
.fsu-welcome strong { color: #0f3460; }

/* ── Footer Strip ─────────────────────────────────────────── */
.fsu-footer {
  background: #1a1a2e;
  border-top: 3px solid #c8a951;
  color: #aab;
  text-align: center;
  padding: 1.25rem 2rem;
  font-size: 0.8rem;
  margin-top: 1rem;
}
.fsu-footer a { color: #c8a951; text-decoration: none; }
.fsu-footer a:hover { text-decoration: underline; }
</style>

<!-- ═══════════════ HERO ════════════════ -->
<div class="fsu-hero">
  <div class="fsu-hero-content">
    <a class="fsu-logo-link" href="https://www.frostburg.edu" target="_blank">
      <img src="fsu-logo.png" alt="Frostburg State University">
    </a>
    <h1>Dr. Chen's <span>Classroom Wiki</span></h1>
    <p class="subtitle">Department of Computer Science &amp; Information Technology</p>
    <div class="instructor-badge">📚 Instructor: Dr. Chen &nbsp;|&nbsp; Frostburg State University</div>
    <br>
    <a class="fsu-uni-link" href="https://www.frostburg.edu" target="_blank">Visit Frostburg State University →</a>
  </div>
</div>

<div class="fsu-divider"></div>

<!-- ═══════════════ INFO STRIP ════════════════ -->
<div class="fsu-infostrip">
  <span>📅 <strong>Semester:</strong> Fall 2026</span>
  <span>🏛️ <strong>Institution:</strong> Frostburg State University</span>
  <span>📍 <strong>Location:</strong> Frostburg, Maryland</span>
  <span>🔒 <strong>Department:</strong> Computer Science &amp; IT</span>
</div>

<!-- ═══════════════ MAIN ════════════════ -->
<div class="fsu-main">

<!-- Welcome -->
<div class="fsu-welcome">
  Welcome to Dr. Chen's course knowledge base at <strong>Frostburg State University</strong>. This wiki contains comprehensive reading materials, course descriptions, and academic resources for all courses taught by Dr. Chen. Use the navigation above or the course cards below to explore weekly reading chapters, key concepts, and supplemental materials. Content is updated continuously throughout each semester.
</div>

<!-- Stats -->
<div class="fsu-section-title">At a Glance</div>
<div class="fsu-stats">
  <div class="fsu-stat"><div class="fsu-stat-number">7</div><div class="fsu-stat-label">Courses</div></div>
  <div class="fsu-stat"><div class="fsu-stat-number">30</div><div class="fsu-stat-label">Reading Chapters</div></div>
  <div class="fsu-stat"><div class="fsu-stat-number">2</div><div class="fsu-stat-label">Full Curricula</div></div>
  <div class="fsu-stat"><div class="fsu-stat-number">15</div><div class="fsu-stat-label">Weeks / Course</div></div>
  <div class="fsu-stat"><div class="fsu-stat-number">FSU</div><div class="fsu-stat-label">Since 1898</div></div>
</div>

<!-- Courses with Reading Materials -->
<div class="fsu-section-title">Courses with Reading Materials</div>
<div class="fsu-courses">

  <a class="fsu-card has-reading" href="scia-120/chapter-01/">
    <div class="fsu-reading-badge">15 CHAPTERS</div>
    <div class="fsu-card-code">SCIA 120</div>
    <div class="fsu-card-title">Introduction to Secure Computing and Information Assurance</div>
    <p class="fsu-card-meta">
      <span>📅 Every Semester</span>
      <span>🔓 No Prerequisite</span>
    </p>
  </a>

  <a class="fsu-card has-reading" href="scia-340/chapter-01/">
    <div class="fsu-reading-badge">15 CHAPTERS</div>
    <div class="fsu-card-code">SCIA 340</div>
    <div class="fsu-card-title">Secure Databases</div>
    <p class="fsu-card-meta">
      <span>📅 Fall</span>
      <span>📋 Prereq: COSC 240 &amp; SCIA 120</span>
    </p>
  </a>

</div>

<!-- All Courses -->
<div class="fsu-section-title">All Courses</div>
<div class="fsu-courses">

  <a class="fsu-card" href="entities/scia-120/">
    <div class="fsu-card-code">SCIA 120</div>
    <div class="fsu-card-title">Introduction to Secure Computing and Information Assurance</div>
    <p class="fsu-card-meta">
      <span>📅 Every Semester</span>
    </p>
  </a>

  <a class="fsu-card" href="entities/scia-340/">
    <div class="fsu-card-code">SCIA 340</div>
    <div class="fsu-card-title">Secure Databases</div>
    <p class="fsu-card-meta">
      <span>📅 Fall</span>
      <span>📋 COSC 240 &amp; SCIA 120</span>
    </p>
  </a>

  <a class="fsu-card" href="entities/scia-360/">
    <div class="fsu-card-code">SCIA 360</div>
    <div class="fsu-card-title">Operating System Security</div>
    <p class="fsu-card-meta">
      <span>📅 Spring</span>
      <span>📋 COSC 241 &amp; SCIA 120</span>
    </p>
  </a>

  <a class="fsu-card" href="entities/scia-425/">
    <div class="fsu-card-code">SCIA 425</div>
    <div class="fsu-card-title">Software Testing and Assurance</div>
    <p class="fsu-card-meta">
      <span>📅 Fall</span>
      <span>📋 SCIA 325</span>
    </p>
  </a>

  <a class="fsu-card" href="entities/scia-472/">
    <div class="fsu-card-code">SCIA 472</div>
    <div class="fsu-card-title">Hacking Exposed and Incident Response</div>
    <p class="fsu-card-meta">
      <span>📅 Spring</span>
      <span>📋 Co-req: COSC 331</span>
    </p>
  </a>

  <a class="fsu-card" href="entities/itec-442/">
    <div class="fsu-card-code">ITEC 442</div>
    <div class="fsu-card-title">Electronic Commerce</div>
    <p class="fsu-card-meta">
      <span>📅 Every Semester</span>
      <span>📋 ITEC 315 or COSC 241</span>
    </p>
  </a>

  <a class="fsu-card" href="entities/itec-445/">
    <div class="fsu-card-code">ITEC 445</div>
    <div class="fsu-card-title">Database Systems II</div>
    <p class="fsu-card-meta">
      <span>📅 Fall</span>
      <span>📋 ITEC 345</span>
    </p>
  </a>

</div>

</div><!-- /fsu-main -->

<!-- ═══════════════ FOOTER ════════════════ -->
<div class="fsu-footer">
  &copy; 2026 Dr. Chen &nbsp;|&nbsp;
  <a href="https://www.frostburg.edu" target="_blank">Frostburg State University</a> &nbsp;|&nbsp;
  Department of Computer Science &amp; Information Technology &nbsp;|&nbsp;
  Frostburg, Maryland 21532
</div>
