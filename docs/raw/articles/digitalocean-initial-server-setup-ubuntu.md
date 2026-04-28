---
source_url: https://www.digitalocean.com/community/tutorials/initial-server-setup-with-ubuntu
ingested: 2026-04-28
sha256: 4dca868b404b4db1cb08a6b03c3db57bb51cf3c4ddef8df240f832134cc0fb3b
---

# DigitalOcean Initial Server Setup with Ubuntu

Accessed: 2026-04-28

This source supports the Ubuntu baseline and SSH setup pages.

Key classroom-relevant points:

- Start from a new Ubuntu server and perform baseline security configuration before installing lab software.
- Create a non-root user for daily work rather than using `root` routinely.
- Add the non-root user to the `sudo` group.
- Configure SSH access, preferably with SSH keys.
- Enable UFW and allow OpenSSH before turning the firewall on, so students do not lock themselves out.
- Verify the new account can connect and use `sudo` before ending the root session.
- Use one firewall strategy carefully; cloud firewalls and UFW can overlap in confusing ways.
