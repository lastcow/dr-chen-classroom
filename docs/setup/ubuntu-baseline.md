---
title: Ubuntu Server Baseline
created: 2026-04-28
updated: 2026-04-28
type: resource
tags: [technology, resource, lab]
sources: [raw/articles/digitalocean-initial-server-setup-ubuntu.md]
---

# Ubuntu Server Baseline

This page prepares a fresh Ubuntu Server for course labs. It follows the same basic direction as DigitalOcean's [Initial Server Setup with Ubuntu](https://www.digitalocean.com/community/tutorials/initial-server-setup-with-ubuntu): create a non-root user, enable `sudo`, configure SSH access, and turn on a firewall safely.

!!! abstract "Goal"
    Finish with a non-root administrative account, working SSH access, updated packages, and a basic firewall that allows SSH.

## 1. Confirm the Server Version

```bash
lsb_release -a
uname -a
```

Recommended: Ubuntu 22.04 LTS or Ubuntu 24.04 LTS.

## 2. Update Packages

```bash
sudo apt update
sudo apt upgrade -y
sudo apt autoremove -y
```

If this is a brand-new server and you are logged in as `root`, omit `sudo` until you create the regular user.

## 3. Create a Non-Root User

Replace `student` with your username:

```bash
adduser student
usermod -aG sudo student
```

Verify the user is in the `sudo` group:

```bash
groups student
```

Expected: the output includes `sudo`.

## 4. Test the New User

Open a second terminal and connect as the new user:

```bash
ssh student@SERVER_IP_ADDRESS
```

Then test administrative access:

```bash
sudo whoami
```

Expected output:

```text
root
```

!!! warning "Keep the original session open"
    Do not close the root or existing working session until the new user can log in and run `sudo`.

## 5. Install Core Utilities

```bash
sudo apt install -y curl wget ca-certificates gnupg lsb-release unzip zip nano vim tree htop ufw
```

These tools support later setup pages and common lab workflows.

## 6. Enable a Basic Firewall

Allow SSH first:

```bash
sudo ufw allow OpenSSH
```

Enable UFW:

```bash
sudo ufw enable
```

Check status:

```bash
sudo ufw status verbose
```

Expected: `OpenSSH` is allowed and the firewall status is active.

!!! danger "Avoid lockout"
    If you use a custom SSH port, allow that port before enabling UFW. Example: `sudo ufw allow 2222/tcp`.

## 7. Set the Time Zone Optional

List time zones:

```bash
timedatectl list-timezones | grep America
```

Set a time zone:

```bash
sudo timedatectl set-timezone America/New_York
```

Verify:

```bash
timedatectl
```

## 8. Classroom Checkpoint

Record these outputs:

```bash
lsb_release -a
groups $USER
sudo ufw status verbose
```

## Troubleshooting

| Problem | Check |
|---|---|
| `sudo: command not found` | Confirm you are on Ubuntu Server and install `sudo` as root. |
| User cannot run sudo | Run `usermod -aG sudo USERNAME` as root, then log out/in. |
| SSH stops working after firewall changes | Use the provider console and allow `OpenSSH` or the custom SSH port. |

## Next Step

Continue to [SSH and Terminal Workflow](ssh-terminal.md).
