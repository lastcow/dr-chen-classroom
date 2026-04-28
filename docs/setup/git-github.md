---
title: Git and GitHub Setup
created: 2026-04-28
updated: 2026-04-28
type: resource
tags: [technology, resource, lab]
sources: [raw/articles/digitalocean-install-git-ubuntu.md]
---

# Git and GitHub Setup

Git tracks changes in code and lab files. GitHub hosts repositories so students can clone course material, submit work, and practice professional version control.

This page follows the practical APT-based installation path from DigitalOcean's [How To Install Git on Ubuntu](https://www.digitalocean.com/community/tutorials/how-to-install-git-on-ubuntu).

## 1. Install Git

```bash
sudo apt update
sudo apt install -y git
```

Verify:

```bash
git --version
```

## 2. Configure Git Identity

Use your real name or course-approved name:

```bash
git config --global user.name "Your Name"
git config --global user.email "your_email@example.com"
```

Use `main` as the default branch name:

```bash
git config --global init.defaultBranch main
```

Set a simple terminal editor:

```bash
git config --global core.editor "nano"
```

Review settings:

```bash
git config --global --list
```

## 3. Create a Lab Workspace

```bash
mkdir -p ~/course-work
cd ~/course-work
git init practice-repo
cd practice-repo
```

Create a first file:

```bash
echo "# Practice Repository" > README.md
git status
git add README.md
git commit -m "Initial commit"
```

## 4. GitHub SSH Key Setup Optional

If you will push to GitHub by SSH, create or reuse an SSH key:

```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
cat ~/.ssh/id_ed25519.pub
```

Copy the public key into GitHub:

```text
GitHub → Settings → SSH and GPG keys → New SSH key
```

Test:

```bash
ssh -T git@github.com
```

Expected: GitHub greets your username. It may also say shell access is not provided; that is normal.

## 5. Basic Git Commands

| Task | Command |
|---|---|
| Check repository status | `git status` |
| See changes | `git diff` |
| Stage a file | `git add FILE` |
| Commit staged changes | `git commit -m "Message"` |
| Show commit history | `git log --oneline --graph --decorate` |
| Clone a repository | `git clone URL` |
| Pull new changes | `git pull` |
| Push local commits | `git push` |

## 6. Classroom Checkpoint

Record:

```bash
git --version
git config --global --list
git log --oneline
```

## Troubleshooting

| Problem | Fix |
|---|---|
| Git asks for identity on commit | Run `git config --global user.name` and `git config --global user.email`. |
| GitHub rejects password authentication | Use SSH keys or a GitHub personal access token. |
| `fatal: not a git repository` | Run the command inside a repository folder or initialize one with `git init`. |

## Next Step

Continue to [VS Code Remote SSH](vscode-remote-ssh.md), or go directly to [Docker Setup on Ubuntu Server](docker-ubuntu.md).
