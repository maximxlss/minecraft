# minecraft-server

A Paper Minecraft server defined entirely in this repo. Merging a pull
request is the only sysadmin action required — see `SPEC.md` for the full
design and `docs/CONTRIBUTING.md` for how to actually change something.

## Connecting

- Address: _domain TBD — static IP, DNS record not set up yet_
- Port: `25565` (default)
- No whitelist. Offline-mode accounts — first join, run
  `/register <password> <password>`; after that, `/login <password>`.

## First-time host setup (one-time, manual)

```
ssh minecraft
git clone <this repo> && cd minecraft-server
./provisioning/bootstrap.sh
```

Then copy `docker-compose.yml` (and `plugin-configs/` if non-empty) to
`/opt/minecraft/` and run `docker compose up -d` from there. After this,
`deploy.yml` takes over on every merge to `main`.

## Wiring up CI

`deploy.yml` needs, on the GitHub repo:

- Secret `DEPLOY_SSH_KEY` — private half of a deploy key whose public half
  is in the host's `~/.ssh/authorized_keys`.
- Variables `DEPLOY_HOST` and `DEPLOY_USER` — the host address and the SSH
  user to connect as.

## Repo layout

See `SPEC.md` §4.
