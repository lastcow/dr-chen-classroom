---
title: SSH and Terminal Workflow
created: 2026-04-28
updated: 2026-04-28
type: resource
tags: [technology, resource, lab]
sources: [raw/articles/digitalocean-initial-server-setup-ubuntu.md]
---

# SSH and Terminal Workflow

SSH is how students connect to remote Ubuntu servers for labs. This page covers key-based login, a simple SSH config file, and terminal habits that reduce mistakes.

## 1. Verify SSH Works

From your local computer:

```bash
ssh USERNAME@SERVER_IP_ADDRESS
```

If this works, exit the server:

```bash
exit
```

## 2. Generate an SSH Key If Needed

On your local computer:

```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
```

Accept the default file path unless your instructor tells you otherwise. Use a passphrase when possible.

## 3. Copy the Public Key to the Server

Preferred method:

```bash
ssh-copy-id USERNAME@SERVER_IP_ADDRESS
```

If `ssh-copy-id` is not available, print your public key:

```bash
cat ~/.ssh/id_ed25519.pub
```

Then add it to this file on the server:

```bash
mkdir -p ~/.ssh
nano ~/.ssh/authorized_keys
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

## 4. Create an SSH Config Entry

On your local computer, edit:

```bash
nano ~/.ssh/config
```

Add:

```text
Host course-server
    HostName SERVER_IP_ADDRESS
    User USERNAME
    IdentityFile ~/.ssh/id_ed25519
```

Connect with:

```bash
ssh course-server
```

## 5. Terminal Habits for Labs

| Habit | Why it matters |
|---|---|
| Run `pwd` before editing files | Confirms where you are. |
| Run `ls` or `tree` before deleting files | Avoids accidental deletion. |
| Use `mkdir -p labs/week01` | Creates repeatable folder structure. |
| Keep one terminal for notes/output | Makes screenshots and submissions easier. |
| Copy exact error messages | Troubleshooting depends on exact text. |

## 6. Useful Commands

```bash
pwd
ls -la
mkdir -p ~/labs
cd ~/labs
history | tail -20
```

## 7. Classroom Checkpoint

Submit or record:

1. A successful SSH login using your short host alias, such as `ssh course-server`.
2. Output of:

    ```bash
    whoami
    hostname
    pwd
    ```

## Troubleshooting

| Error | Likely Cause | Fix |
|---|---|---|
| `Permission denied (publickey)` | Server does not have your public key | Re-run `ssh-copy-id` or check `authorized_keys`. |
| `Connection timed out` | Firewall, wrong IP, server off | Verify IP, cloud firewall, and UFW rules. |
| `REMOTE HOST IDENTIFICATION HAS CHANGED` | Server was rebuilt or IP reused | Confirm this is expected, then remove the old key from `~/.ssh/known_hosts`. |

## Next Step

Continue to [Git and GitHub Setup](git-github.md).
