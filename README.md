# mc.xls.msk.ru

_[Русская версия](README.ru.md)_

A Minecraft server that anyone can help build. There's no admin sitting at
a console making changes by hand — the whole thing (plugins, settings,
even who's an admin) lives in this repository, and merging a pull request
is what actually changes the live server.

## Play

- **Address:** `mc.xls.msk.ru`, default port (`25565`) — just paste the
  address in, no port needed.
- **Version:** Paper **26.1.2** (build 74), pinned exactly in
  `docker-compose.yml` — it only changes via a deliberate PR, not on its
  own. You still don't need to keep your client version in exact lockstep:
  [ViaVersion](https://modrinth.com/plugin/viaversion) +
  [ViaBackwards](https://modrinth.com/plugin/viabackwards) are installed so
  slightly older or newer clients still connect.
- **No whitelist, no Mojang account needed.** First time you join, run
  `/register <password> <password>`; every time after, `/login <password>`.
  Pick a password you're fine reusing for a Minecraft server, not one from
  anywhere that actually matters — accounts here are local to this server,
  not tied to Mojang. [SkinsRestorer](https://modrinth.com/plugin/skinsrestorer)
  is installed so you still show up with your real skin despite that.
- **Grief protection:** [CoreProtect](https://modrinth.com/plugin/coreprotect)
  logs every block change, so a troll (there's no whitelist, remember) is a
  quick rollback, not lost work. Automatic backups run every 24h on top of
  that, for anything CoreProtect can't fix.
- **QoL commands** via [EssentialsX](https://modrinth.com/plugin/essentialsx)
  — `/home`, `/tpa`, `/spawn`, `/kit`, and the rest of the usual set.
- **Live map:** [BlueMap](https://modrinth.com/plugin/bluemap) at
  [https://xls.msk.ru/minecraft_map/](https://xls.msk.ru/minecraft_map/) —
  browse the world from outside the game.

## Contribute

Want to add a plugin, change a setting, or nominate someone as admin?
Open a pull request. Once it's reviewed and merged, it's live on the real
server within a minute or two — that's the entire deploy process. See
[`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) for the how-to, or
[`SPEC.md`](SPEC.md) if you want the full design and the reasoning behind
it.

---

## Maintaining this server

### First-time host setup (one-time, manual)

```
ssh minecraft
git clone <this repo> && cd minecraft-server
./provisioning/bootstrap.sh
```

Then copy `docker-compose.yml` (and `plugin-configs/` if non-empty) to
`/opt/minecraft/` and run `docker compose up -d` from there. After this,
`deploy.yml` takes over on every merge to `main`.

The router needs to forward two ports to the host: `25565` (the game) and
`8100` (BlueMap's web map).

### Wiring up CI

`deploy.yml` needs, on the GitHub repo:

- Secret `DEPLOY_SSH_KEY` — private half of a deploy key whose public half
  is in the host's `~/.ssh/authorized_keys`.
- Variables `DEPLOY_HOST` and `DEPLOY_USER` — the host address and the SSH
  user to connect as.

Also set up branch protection on `main` (`Settings → Branches → Add branch
ruleset`): require the `Validate / lint` and `Validate / smoke-test` checks
to pass, and require the branch be up to date before merging. GitHub only
lets you pick a check as required after it's run at least once, so this
has to happen after the first PR (this one works).

### Repo layout

See `SPEC.md` §4.
