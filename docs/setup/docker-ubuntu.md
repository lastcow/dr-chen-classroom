---
title: Docker Setup on Ubuntu Server
created: 2026-04-28
updated: 2026-04-28
type: resource
tags: [technology, resource, lab]
sources: [raw/articles/digitalocean-install-docker-ubuntu.md]
---

# Docker Setup on Ubuntu Server

This guide walks students through installing **Docker Engine** on an Ubuntu Server. It is adapted for course use from DigitalOcean's tutorial, [How to Install Docker on Ubuntu](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-22-04), with additional classroom checkpoints and security notes.

!!! abstract "Goal"
    By the end of this setup, your Ubuntu Server should be able to run Docker containers, pull images, and execute a basic test container.

## 1. Before You Start

You need:

- An Ubuntu Server, preferably Ubuntu 22.04 LTS or 24.04 LTS.
- A non-root user with `sudo` privileges.
- Internet access from the server.
- Terminal access through SSH, console, or a cloud provider terminal.

Check your Ubuntu version:

```bash
lsb_release -a
```

Expected result: the output should show Ubuntu and a release codename such as `jammy` for 22.04 or `noble` for 24.04.

!!! warning "Do not paste commands blindly"
    Read each command before running it. Docker installation changes system packages, adds an APT repository, and starts a privileged background service.

## 2. Update the Server

Start by refreshing the package list and applying available updates:

```bash
sudo apt update
sudo apt upgrade -y
```

Install required packages for repository access and certificate validation:

```bash
sudo apt install -y ca-certificates curl gnupg lsb-release
```

## 3. Remove Conflicting Docker Packages

If the server previously had Docker installed from Ubuntu's default repositories, remove conflicting packages first:

```bash
for pkg in docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc; do
  sudo apt remove -y "$pkg" 2>/dev/null || true
done
```

This does **not** delete Docker data under `/var/lib/docker`; it only removes conflicting packages.

## 4. Add Docker's Official GPG Key

Create the keyrings directory:

```bash
sudo install -m 0755 -d /etc/apt/keyrings
```

Download Docker's official GPG key:

```bash
curl -fsSL https://download.docker.com/linux/ubuntu/gpg   | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
```

Set readable permissions:

```bash
sudo chmod a+r /etc/apt/keyrings/docker.gpg
```

## 5. Add Docker's APT Repository

Add Docker's stable repository for your Ubuntu version:

```bash
echo   "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu   $(. /etc/os-release && echo "$VERSION_CODENAME") stable"   | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

Refresh package metadata again:

```bash
sudo apt update
```

Checkpoint: confirm Docker packages are coming from Docker's repository:

```bash
apt-cache policy docker-ce
```

Look for a candidate version from `https://download.docker.com/linux/ubuntu`.

## 6. Install Docker Engine

Install Docker Engine, the Docker CLI, containerd, Buildx, and Docker Compose plugin:

```bash
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

## 7. Verify Docker Service Status

Check whether Docker is running:

```bash
sudo systemctl status docker --no-pager
```

You should see:

```text
Active: active (running)
```

If it is not running, start it:

```bash
sudo systemctl enable --now docker
```

## 8. Run a Test Container

Run Docker's official test image:

```bash
sudo docker run hello-world
```

Expected result: Docker downloads the `hello-world` image and prints a message confirming that the installation appears to be working.

## 9. Optional: Run Docker Without `sudo`

By default, Docker commands require root-level access. To allow your current user to run Docker commands without `sudo`, add the user to the `docker` group:

```bash
sudo usermod -aG docker $USER
```

Apply the group change by logging out and back in. For SSH users, disconnect and reconnect.

Then test:

```bash
docker run hello-world
```

!!! danger "Docker group security warning"
    Membership in the `docker` group is effectively root-equivalent on the host. Only add trusted users. On shared servers, ask the instructor before changing group membership.

## 10. Useful Docker Commands

| Task | Command |
|---|---|
| Show running containers | `docker ps` |
| Show all containers | `docker ps -a` |
| List local images | `docker images` |
| Pull an image | `docker pull ubuntu:24.04` |
| Run an interactive Ubuntu container | `docker run -it ubuntu:24.04 bash` |
| Stop a container | `docker stop CONTAINER_ID` |
| Remove a stopped container | `docker rm CONTAINER_ID` |
| View container logs | `docker logs CONTAINER_ID` |
| Show Docker version | `docker version` |
| Show Docker system info | `docker info` |
| Check Docker Compose plugin | `docker compose version` |

## 11. Classroom Checkpoint

Submit or record the following evidence for your lab notes:

1. Output of:

    ```bash
    docker --version
    ```

2. Output of:

    ```bash
    docker compose version
    ```

3. Screenshot or copied text showing successful output from:

    ```bash
    docker run hello-world
    ```

4. One-sentence explanation of what a container is.

## 12. Troubleshooting

### Problem: `Cannot connect to the Docker daemon`

Check whether Docker is running:

```bash
sudo systemctl status docker --no-pager
```

Start it if needed:

```bash
sudo systemctl enable --now docker
```

### Problem: `permission denied while trying to connect to the Docker daemon socket`

Use `sudo` before Docker commands, or add your user to the `docker` group and log out/back in:

```bash
sudo usermod -aG docker $USER
```

### Problem: Repository or GPG key error

Re-check these files:

```bash
ls -l /etc/apt/keyrings/docker.gpg
cat /etc/apt/sources.list.d/docker.list
```

Then run:

```bash
sudo apt update
```

### Problem: Firewall behavior changes after Docker install

Docker modifies packet filtering rules for containers. On servers using `ufw`, exposed container ports may behave differently than expected. For production systems, review Docker's firewall documentation and use the `DOCKER-USER` chain for host-level filtering rules.

## 13. Clean Test Container Output

After testing, you can remove exited containers:

```bash
docker ps -a
```

Remove a specific stopped container:

```bash
docker rm CONTAINER_ID
```

Or remove all stopped containers:

```bash
docker container prune
```

## Reference

- DigitalOcean Community Tutorial: [How to Install Docker on Ubuntu](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-22-04)
- Docker Docs: [Install Docker Engine on Ubuntu](https://docs.docker.com/engine/install/ubuntu/)

## Next Step

Return to the [Setup Course welcome page](index.md). For now, Docker setup is the only active setup module.
