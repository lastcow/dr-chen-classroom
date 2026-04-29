# Wiki Log

> Chronological record of all wiki actions. Append-only.
> Format: `## [YYYY-MM-DD] action | subject`
> Actions: ingest, update, query, lint, create, archive, delete
> When this file exceeds 500 entries, rotate: rename to log-YYYY.md, start fresh.

## [2026-04-12] create | Course pages added
- Created 7 course entity pages: scia-120, scia-340, scia-360, scia-425, scia-472, itec-442, itec-445
- Updated index.md (7 pages), mkdocs.yml nav

## [2026-04-12] create | Wiki initialized
- Domain: Dr. Chen's Classroom — Frostburg State University
- Structure created with SCHEMA.md, index.md, log.md
- Directories: raw/articles, raw/papers, raw/transcripts, raw/assets, entities/, concepts/, comparisons/, queries/

## [2026-04-28] create | Setup course and Docker setup module
- Created `setup/index.md` welcome page for the Setup course.
- Created `setup/docker-ubuntu.md` with Docker Engine installation steps for Ubuntu Server, adapted from DigitalOcean's tutorial.
- Added Docker setup under the Setup menu in `mkdocs.yml`.
- Added raw provenance source: `raw/articles/digitalocean-install-docker-ubuntu.md`.
- Updated homepage course count and added Setup course card.

## [2026-04-28] update | Basic setup course expanded
- Updated `setup/index.md` welcome page with the full basic setup sequence.
- Created `setup/ubuntu-baseline.md` for non-root sudo user, package updates, utilities, and UFW.
- Created `setup/ssh-terminal.md` for SSH keys, SSH config, and terminal workflow.
- Created `setup/git-github.md` for Git installation, identity configuration, and GitHub SSH readiness.
- Created `setup/vscode-remote-ssh.md` for VS Code Remote SSH workflow.
- Created `setup/docker-compose.md` for Docker Compose plugin verification and first Compose lab.
- Updated Setup menu navigation in `mkdocs.yml`.
- Added raw provenance notes for DigitalOcean initial server setup, DigitalOcean Git setup, and VS Code Remote SSH docs.
## [2026-04-29] create | SCIA 120 presentation sample
- Installed `guizang-ppt-skill` with the `skills` CLI into `~/.agents/skills/guizang-ppt-skill` and symlinked it for Claude Code/OpenClaw.
- Created `scia-120/presentations/index.md` as a dedicated Presentations section.
- Created `scia-120/presentations/llm-wiki-sample.md` wrapper page.
- Created `scia-120/presentations/llm-wiki-sample-deck/index.html` as a magazine-style HTML presentation sample on LLM Wiki.
- Updated `mkdocs.yml` navigation under SCIA-120.
## [2026-04-29] create | SCIA 120 weekly presentations generated
- Moved the SCIA-120 Presentations navigation under the Reading Materials section.
- Generated 15 weekly tech-dark HTML presentations from SCIA-120 reading materials, one per week.
- Each deck has 30 slides, cover author line for Dr. Zhijiang Chen (Frostburg State University), an overall page, AI-generated SVG line-art concept visuals, review prompts, and launchable HTML.
- Updated `scia-120/presentations/index.md` as the overall presentation page with links to all 15 presentations.
- Created 15 wrapper pages with brief descriptions, launch links, reading links, and iframe previews.
## [2026-04-29] update | SCIA 120 Week 01 presentation revised
- Updated `scia-120/presentations/_content/week-01.json` with detailed student-facing content aligned to Chapter 1.
- Updated `scia-120/presentations/week-01-deck/index.html` to remove dialog/teaching-tip material and add topic-matched technical line-art visuals.
- Updated `scia-120/presentations/week-01.md` wrapper brief.
- Enriched Week 01 concepts with credible references including NIST CSF 2.0, CISA Cyber Essentials, IBM Cost of a Data Breach Report 2025, and ISC2 Cybersecurity Workforce Study 2025.
