---
title: Docker Compose Basics
created: 2026-04-28
updated: 2026-04-28
type: resource
tags: [technology, resource, lab]
sources: [raw/articles/digitalocean-install-docker-ubuntu.md]
---

# Docker Compose Basics

Docker Compose runs multi-container applications from a YAML file. In course labs, Compose is useful for starting a web app, database, and supporting services with one command.

!!! abstract "Goal"
    Confirm the Docker Compose plugin is available, then run a small web server from a `compose.yaml` file.

## 1. Prerequisite

Complete [Docker Setup on Ubuntu Server](docker-ubuntu.md) first.

Check Docker:

```bash
docker --version
docker compose version
```

If `docker compose version` fails, install the Compose plugin:

```bash
sudo apt update
sudo apt install -y docker-compose-plugin
```

## 2. Create a Compose Lab Folder

```bash
mkdir -p ~/course-work/compose-test
cd ~/course-work/compose-test
```

## 3. Create `compose.yaml`

```bash
nano compose.yaml
```

Paste:

```yaml
services:
  web:
    image: nginx:alpine
    ports:
      - "8080:80"
```

## 4. Start the Service

```bash
docker compose up -d
```

Check status:

```bash
docker compose ps
```

Test locally on the server:

```bash
curl http://localhost:8080
```

Expected: HTML from the Nginx welcome page.

## 5. Stop and Clean Up

```bash
docker compose down
```

Confirm no Compose containers remain:

```bash
docker ps
```

## 6. Common Compose Commands

| Task | Command |
|---|---|
| Start services in foreground | `docker compose up` |
| Start services in background | `docker compose up -d` |
| Stop and remove services | `docker compose down` |
| View logs | `docker compose logs` |
| Follow logs | `docker compose logs -f` |
| Show service status | `docker compose ps` |
| Rebuild images | `docker compose build` |

## 7. Classroom Checkpoint

Record:

```bash
docker compose version
docker compose ps
curl -I http://localhost:8080
```

## Troubleshooting

| Problem | Fix |
|---|---|
| `docker: permission denied` | Use `sudo` or complete the Docker group step from the Docker setup page. |
| Port 8080 already in use | Change `8080:80` to another host port, such as `8081:80`. |
| YAML parsing error | Check indentation. YAML uses spaces, not tabs. |

## Next Step

You are ready to run containerized course labs.
