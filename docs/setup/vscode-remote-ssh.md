---
title: VS Code Remote SSH
created: 2026-04-28
updated: 2026-04-28
type: resource
tags: [technology, resource, lab]
sources: [raw/articles/vscode-remote-ssh-docs.md]
---

# VS Code Remote SSH

VS Code Remote - SSH lets students edit files on an Ubuntu Server while using the local VS Code interface. The official VS Code documentation describes it as opening a remote folder on any machine with a running SSH server.

## 1. Requirements

On your local computer:

- Visual Studio Code installed.
- Remote - SSH extension installed.
- An OpenSSH-compatible SSH client.

On the remote Ubuntu Server:

- SSH server running.
- Your user can log in by terminal SSH.
- At least 1 GB RAM; 2 GB is better for a smooth experience.

## 2. Verify Terminal SSH First

Before using VS Code, confirm normal SSH works:

```bash
ssh course-server
```

If this fails, fix SSH first. VS Code Remote SSH depends on working terminal SSH.

## 3. Install the Extension

In VS Code:

1. Open Extensions.
2. Search for **Remote - SSH**.
3. Install the Microsoft extension.

Optional: install the **Remote Development** extension pack if you also plan to use containers later.

## 4. Connect to the Server

1. Open Command Palette: `Ctrl+Shift+P` or `F1`.
2. Run: `Remote-SSH: Connect to Host...`
3. Select your SSH alias, such as `course-server`, or enter `USERNAME@SERVER_IP_ADDRESS`.
4. Select Linux if VS Code asks for the server platform.
5. Wait while VS Code installs the VS Code Server on the remote host.

## 5. Open a Course Folder

On the server, create a workspace:

```bash
mkdir -p ~/course-work
```

In VS Code Remote window:

```text
File → Open Folder → /home/USERNAME/course-work
```

## 6. Recommended Extensions

Install these in the **remote** VS Code window when needed:

| Extension | Purpose |
|---|---|
| Markdown All in One | Better markdown editing. |
| Docker | View containers/images from VS Code. |
| Python | Python labs and scripts. |
| YAML | Docker Compose and configuration files. |

## 7. Classroom Checkpoint

Record:

1. A screenshot of VS Code connected to the server.
2. Output from the VS Code integrated terminal:

    ```bash
    hostname
    pwd
    whoami
    ```

## Troubleshooting

| Problem | Fix |
|---|---|
| VS Code hangs during connection | Confirm `ssh course-server` works in a normal terminal. |
| Password prompt repeats | Use SSH keys and check key permissions. |
| Remote server install fails | Check free disk space with `df -h` and shell type with `echo $SHELL`. |
| Extensions appear missing | Install them on the remote side, not only locally. |

## Next Step

Continue to [Docker Setup on Ubuntu Server](docker-ubuntu.md).
