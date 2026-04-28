---
source_url: https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-22-04
ingested: 2026-04-28
sha256: 105c1991b6d70c2d28ee35b0faa8beed269464b1b3a6a2fe1fcbd69b401a8d1a
---

# DigitalOcean Tutorial: How to Install Docker on Ubuntu

Source URL: https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-22-04
Accessed: 2026-04-28

This source is used as the main installation reference for the course setup Docker lesson.

Key points captured from DigitalOcean's tutorial:

- Use an Ubuntu server with a non-root sudo user and a configured firewall.
- Install Docker from Docker's official APT repository rather than Ubuntu's default package repository, because the default package may be outdated.
- Install prerequisites such as `ca-certificates`, `curl`, and `gnupg`/GPG support.
- Add Docker's official GPG key and Docker's APT repository.
- Install Docker Engine / Community Edition packages.
- Verify that the Docker daemon is running with `systemctl status docker`.
- Optionally add the current user to the `docker` group so Docker commands can run without `sudo`.
- Validate installation with a test container such as `hello-world`.
- Learn basic commands such as `docker run`, `docker ps`, `docker images`, `docker stop`, `docker rm`, and `docker logs`.

The wiki lesson adapts these steps for classroom use and adds explicit student checkpoints, troubleshooting notes, and safety warnings.
