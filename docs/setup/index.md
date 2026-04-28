---
title: Setup Course
created: 2026-04-28
updated: 2026-04-28
type: course
tags: [course, curriculum, technology, resource]
sources: [raw/articles/digitalocean-initial-server-setup-ubuntu.md, raw/articles/digitalocean-install-docker-ubuntu.md, raw/articles/digitalocean-install-git-ubuntu.md, raw/articles/vscode-remote-ssh-docs.md]
---

# Setup Course

Welcome to the **Setup** course area. This section prepares students for hands-on cybersecurity, secure computing, database, and software assurance labs.

The setup sequence now covers the full basic environment: Ubuntu Server baseline, SSH workflow, Git/GitHub, VS Code Remote SSH, Docker Engine, and Docker Compose.

<div class="grid cards" markdown>

-   :material-server: **Ubuntu Server Baseline**

    Create a non-root sudo user, update the server, install core utilities, and enable a safe SSH firewall rule.

    [Start Ubuntu Baseline →](ubuntu-baseline.md)

-   :material-console-network: **SSH and Terminal Workflow**

    Connect to a server with SSH keys, create an SSH config alias, and practice safe terminal habits.

    [Open SSH Setup →](ssh-terminal.md)

-   :fontawesome-brands-git-alt: **Git and GitHub Setup**

    Install Git, configure identity, create a practice repository, and prepare for GitHub-based coursework.

    [Open Git Setup →](git-github.md)

-   :material-microsoft-visual-studio-code: **VS Code Remote SSH**

    Use VS Code as a remote editor for files and terminals on the Ubuntu Server.

    [Open VS Code Setup →](vscode-remote-ssh.md)

-   :material-docker: **Docker Setup**

    Install Docker Engine on Ubuntu Server, verify the service, configure non-root usage, and run a test container.

    [Start Docker Setup →](docker-ubuntu.md)

-   :material-layers-triple: **Docker Compose Basics**

    Run a simple multi-container-style lab workflow from a `compose.yaml` file.

    [Open Docker Compose →](docker-compose.md)

</div>

## What Basic Setup Covers

| Area | Purpose | Status |
|---|---|---|
| Ubuntu Server baseline | Prepare a clean Linux server for course labs | **Ready** |
| SSH and terminal workflow | Connect to remote lab machines safely | **Ready** |
| Git and GitHub | Clone course materials and submit lab work | **Ready** |
| VS Code / remote editing | Edit files on a server from a local workstation | **Ready** |
| Docker Engine | Run isolated containers for labs and demonstrations | **Ready** |
| Docker Compose | Run multi-service lab environments | **Ready** |

!!! tip "Recommended order"
    Complete the modules in the order shown above. Docker depends on a working Ubuntu baseline, and VS Code Remote SSH depends on working terminal SSH.

## Setup Menu

1. [Ubuntu Server Baseline](ubuntu-baseline.md)
2. [SSH and Terminal Workflow](ssh-terminal.md)
3. [Git and GitHub Setup](git-github.md)
4. [VS Code Remote SSH](vscode-remote-ssh.md)
5. [Docker Setup on Ubuntu Server](docker-ubuntu.md)
6. [Docker Compose Basics](docker-compose.md)

## Student Outcomes

After completing the basic setup course, students should be able to:

- Securely access an Ubuntu Server using a non-root `sudo` account.
- Use SSH keys and an SSH config alias for repeatable logins.
- Install and configure Git for coursework.
- Edit remote files through VS Code Remote SSH.
- Install Docker Engine from Docker's official Ubuntu repository.
- Run single-container and Compose-based Docker labs.
- Capture command output for lab evidence and troubleshooting.

## Instructor Notes

These pages are intentionally tool-focused rather than course-specific. They can support SCIA, ITEC, and other lab-based courses that require a repeatable Linux/Docker environment.
