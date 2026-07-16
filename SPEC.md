# Minecraft-as-Code — Specification (Draft)

Goal: a Minecraft server whose entire configuration — server settings, admin
list, whitelist, plugins and their config — lives in a git repository.
Merging a pull request is the only sysadmin action required. The world save
itself is the one thing that stays stateful and is never touched by a deploy.

Target host: `minecraft` (currently `192.168.0.32` in SSH config), Ubuntu
26.04, 3.8GB RAM, 26GB disk, blank slate (verified 2026-07-16: no Docker,
Java, or existing server). SSH is already exposed to the internet; per your
call, CI will SSH into it directly rather than adding a VPN layer — simple
over defense-in-depth, accepted risk. Same goes for the host firewall: left
off, intentionally, and PRs are assumed non-malicious — this spec optimizes
for low maintenance over hardening. One more accepted tradeoff in the same
spirit: there's no staging/canary environment — one host, one world, so a
smoke-tested PR is "probably fine," not "provably safe." See §5 and §6 for
where that limit actually bites.

## 1. Decisions made so far

| Area | Decision | Why |
|---|---|---|
| Server platform | **Paper** | Vanilla-compatible, largest plugin ecosystem, best perf. Not Fabric/Forge — different ecosystem, revisit if you want mods later. |
| CI → host connectivity | **Direct SSH** to the host's public address using a dedicated deploy key stored in GitHub Secrets | Host is already internet-exposed; you chose simplicity over adding Tailscale/self-hosted-runner layers. |
| Runtime packaging | **Docker (`itzg/docker-minecraft-server`), no Ansible** — see §3 | No multi-host/network provisioning need justifies the extra layer; a one-time bootstrap script + `docker-compose.yml` covers everything. |
| Deploy trigger | **Immediate restart on merge to `main`** | Small/casual server, brief restart is acceptable. |
| Content scope | **Plugins + datapacks + resource pack**, all PR-editable | Datapacks (pure data — recipes/loot/structures) and a server resource-pack URL fit "as much as possible in code" the same way plugins do. |
| Pre-merge validation | **Smoke test**: `validate.yml` actually boots the PR's proposed config (throwaway world, never `/opt/minecraft/data`) and waits for a successful "Done" before passing | Catches a crash-on-load PR before merge instead of after. Will drop this if it proves flaky/too slow in practice — not committing to it past a first try. |
| Admin model | **`OPS` stays binary** (full admin or nothing) | Good enough for now; tiered roles (LuckPerms etc.) would be a later addition, not needed today. |
| Whitelist | **Off by default** | Your call — open server, no invite-list friction for now. |
| Player connectivity | **Static IP + a domain you'll assign** pointing at it | No DDNS machinery needed; README just documents the domain once it exists. |
| Container shutdown | **`stop_grace_period` raised well past Compose's 10s default** (e.g. 60s), so Paper gets real time to save the world before a redeploy's SIGTERM turns into a SIGKILL | A restart-on-merge model is only safe if the "restart" part is actually graceful — 10s isn't enough once there's a real world + players on it. |
| Authentication | **`online-mode=false`** (no Mojang account required) **+ a local register/login plugin** (AuthMeReloaded — password-protected usernames, its own local account DB) | Lets friends without a paid Minecraft account join, while still closing the impersonation gap offline mode opens up: without this, anyone could log in *as* an OP'd username and get full admin with zero auth. A password on each username fixes that without needing Mojang. |

Note on that last row: offline mode also means UUIDs for `OPS`/`WHITELIST` are generated locally from a hash of the username instead of looked up from Mojang — no external auth call happens at join time at all anymore.

## 2. Non-goals / what stays out of git

- **World data** (`world/`, `world_nether/`, `world_the_end/`, `playerdata/`,
  `stats/`) — lives in a bind-mounted directory on the host
  (`/opt/minecraft/data`), created once by the bootstrap script. Nothing in
  the deploy path ever touches its contents — deploys only ever
  add/update/remove the compose file and plugin-config files alongside it.
- **AuthMe's account database** (password hashes, registered usernames) —
  same rule as world data: it's player-generated state, lives under the
  same bind mount (`.../plugins/AuthMe/`), and a deploy never touches it.
  Losing it would force everyone to re-register, so it rides along with
  the world in whatever backs up `/opt/minecraft/data`.
- Secrets (SSH deploy key, RCON password) — GitHub Actions Secrets, never
  committed.

## 3. Why no Ansible

Ansible earns its keep when there's host-fleet state to converge repeatedly:
multiple machines, drifting config, OS packages that need to stay in a
specific state over time. This project is one box running one Docker Compose
stack — that reduces to two categories of work, and neither needs Ansible:

- **One-time host provisioning** (install Docker, create
  `/opt/minecraft/data` with the right owner/perms) — a short idempotent
  bash script (`provisioning/bootstrap.sh`) covers this in a few dozen
  lines, run once by hand over SSH. Safe to re-run if the host is ever
  rebuilt. Worth being explicit that this one step is manual — "merging a
  PR is the only sysadmin action" is true from day one *after* bootstrap,
  not before it.
- **Per-merge deploy** (apply config changes) — `docker compose up -d`
  already diffs the service definition against what's running and only
  recreates the container when something actually changed. That's the exact
  idempotency Ansible's handler pattern would have given us, for free,
  because Compose already owns that job. The itzg image separately caches
  plugin/mod downloads by reference (URL/version) against the persistent
  `/data` volume, so an unrelated config change doesn't re-fetch anything.

Net effect: `docker-compose.yml` (checked into git) *is* the config surface
now — no YAML-to-template rendering step, no `config/*.yml` → `.env`
indirection, no Jinja. Deploying a merged PR is just: copy the compose file
(and `plugin-configs/`) to the host, run `docker compose up -d`.

If the project ever grows into something Ansible is actually good at —
multiple hosts, more services needing host-level orchestration — nothing
here blocks adding it later. That's just not this project today.

## 4. Repository layout (proposed)

```
minecraft-server/
├── .github/
│   ├── workflows/
│   │   ├── validate.yml    # on PR: yamllint + `docker compose config` + smoke test — no secrets, safe for fork PRs
│   │   └── deploy.yml      # on push to main only: rsync + `docker compose up -d` over SSH
│   └── scripts/
│       └── validate_config.py  # actual bespoke logic: parses OPS/WHITELIST/PLUGINS out of the
│                                #   compose file, checks UUID/username shape + duplicate/"latest" refs
├── docker-compose.yml       # <- this IS the config surface: OPS/WHITELIST/PLUGINS/RESOURCE_PACK/
│                            #    server.properties as YAML block scalars; also defines `mc-backup`
├── plugin-configs/<Plugin>/*.yml   # per-plugin config overrides, bind-mounted in
│                            #    (AuthMe's config lives here too — it's "just a plugin,"
│                            #    but flagged in CONTRIBUTING.md as core/not-casually-removable)
├── datapacks/<name>/*        # vanilla datapacks (recipes/loot/structures/advancements), bind-mounted in
├── provisioning/
│   └── bootstrap.sh         # one-time, idempotent: install Docker, create data dir
├── docs/CONTRIBUTING.md     # how to open a PR to add a plugin / change a setting
└── README.md
```

Secrets (RCON password, etc.) are **not** in `docker-compose.yml` — Compose
supports `${VAR}` substitution, so those reference an untracked `.env` on
the host, populated once during provisioning (or overwritten from a GitHub
secret at deploy time). Everything else — the actual server settings,
`OPS`, `WHITELIST`, `PLUGINS` list — is plaintext in the committed compose
file, which is the whole point: contributors read a diff and immediately
see what changed, no Ansible/YAML-indirection knowledge required.

## 5. CI/CD flow

1. **PR opened/updated** (`validate.yml`, GitHub-hosted runner, **no
   secrets** — safe even for PRs from forks):
   - `yamllint` + `docker compose config` (parses, vars resolve, no Docker
     daemon needed).
   - `.github/scripts/validate_config.py` — a real (if small) piece of code,
     not just a lint rule: parses the `OPS`/`WHITELIST`/`PLUGINS` blocks out
     of the compose file and checks for malformed usernames/UUIDs,
     duplicate plugin entries, and bare "latest"-style plugin refs. This is
     the one part of the system that's bespoke rather than "just Docker
     Compose," and its rules depend on settling the plugin-pinning
     mechanism (§6) first.
   - **Smoke test**: `docker compose up` the PR's exact config against a
     throwaway volume (never the real `/opt/minecraft/data`), wait for the
     "Done" log line (or a timeout), then tear down. Confirms the proposed
     plugins/datapacks/config actually boot before anyone merges. First
     cut of this — if it turns out flaky or too slow in practice, we drop
     it back to lint-only rather than fight it. Note it does make real
     outbound calls (Modrinth/CurseForge to fetch plugin jars, including
     AuthMe) on every PR run — fine at this scale, just not fully
     sandboxed/offline. `OPS`/`WHITELIST` UUIDs resolve locally now (offline
     mode), so that particular external dependency is gone. This step only
     proves the config *boots*; it can't catch a plugin that starts fine
     but misbehaves once a real player interacts with it — see the
     no-staging tradeoff noted in the intro.
2. **You review and merge** — this is the human gate. There's no bot
   auto-merge; every change to the live server, including the `OPS` list,
   passes through your review because you're the one clicking merge.
3. **Push to `main`** (`deploy.yml`, only runs on `main`, so a fork PR never
   sees the deploy secret): loads the SSH deploy key from secrets, `rsync`s
   `docker-compose.yml` + `plugin-configs/` to `/opt/minecraft/` on the host
   (`rsync --delete` on `plugin-configs/` so a removed file in the repo is
   actually removed on the host), then runs `docker compose up -d
   --remove-orphans` over SSH. Idempotent per §3 — unrelated changes don't
   restart the server.

## 6. Open items I'm flagging (not blocking, but want your call)

These weren't part of the original question set but came up while designing
this — defaults below are what I'd ship unless you redirect:

- **Backups — revised**: rather than a hand-rolled tar+systemd-timer (which
  risks reading world files mid-write and capturing a corrupt snapshot),
  use [`itzg/mc-backup`](https://github.com/itzg/docker-mc-backup) as a
  second service in the same `docker-compose.yml` — same author/ecosystem
  as the server image, purpose-built for this: it drives RCON `save-off` →
  `save-all` → backup → `save-on` around every snapshot so the world is
  never captured half-written, supports tar/rsync/restic, and can push
  offsite via rclone. This is strictly better than what I originally
  proposed and keeps us at "just more Docker Compose," no custom script.
- **RCON**: only the `mc-backup` sidecar needs it, so it just stays on the
  Docker Compose internal network with no `ports:` entry — nothing external
  needs to reach it, so there's no reason to publish it either way.
- **JVM heap sizing**: host has 3.8GB total. I'd default to a 2.5G heap for
  Paper, leaving headroom for the OS + Docker daemon. Tunable via the
  `MEMORY` env var in `docker-compose.yml`.
- **Version bumps**: bumping the Minecraft/Paper version in
  `docker-compose.yml` triggers the same immediate-restart deploy. Paper
  handles in-place world upgrades on first boot (standard, well-supported
  path) — worth treating a version-changing PR as a cue to double check the
  latest backup is fresh, though the automated sidecar backup already runs
  independent of deploys.
- **Plugin/mod version pinning — needs to be pinned down before scaffolding
  `validate.yml`**: the itzg image has more than one plugin-source
  mechanism (raw `PLUGINS` URLs, `MODRINTH_PROJECTS`, `SPIGET_RESOURCES`,
  `CURSEFORGE_FILES`, each with its own "how do I pin an exact version"
  syntax), and `validate_config.py`'s "reject latest refs" rule can't be
  written until we know what a pinned reference looks like. Proposed
  default: standardize on **Modrinth, pinned to an exact version ID**
  (`MODRINTH_PROJECTS=<slug>:<version>`) as the primary source since most
  Paper plugins are there and it has the cleanest pin syntax, falling back
  to a directly pinned download URL via `PLUGINS` for anything not on
  Modrinth. I'll confirm exact env var syntax against current itzg docs
  during scaffolding rather than guess here — flagging the mechanism
  choice now since it changes what the validator and `CONTRIBUTING.md`
  both need to say.
- **Deploy health check + rollback path**: right now a merge that breaks
  something (bad plugin config, a typo'd RCON password) fails silently until
  a player notices. I'd add a post-`up -d` check in `deploy.yml` — poll the
  server (e.g. via `mc-monitor`, another itzg tool built for exactly this)
  for a few seconds to confirm it actually came up healthy, and fail the
  workflow loudly (red X, optionally a Discord/webhook ping) if not. Rollback
  itself is just "revert the commit and let the next merge redeploy" — no
  extra machinery needed, but worth having a `workflow_dispatch` trigger on
  `deploy.yml` so you can manually re-run a deploy without needing a new
  commit. One caveat: this assumes the old plugin version is still
  fetchable upstream, which is usually true but not guaranteed (a Modrinth
  version can be yanked) — not worth building around, just don't treat
  "revert" as an unconditional undo button.
- **`restart: unless-stopped`** on the `mc` service, so a host reboot brings
  the server back without you doing anything.
- **Standing uptime check**: the deploy-time health check only catches
  breakage introduced *by* a deploy. A 3am crash unrelated to any merge
  wouldn't trip it. A cheap standing check (a dead-man's-switch ping to
  something like healthchecks.io, or `mc-monitor` run periodically) closes
  that gap — worth it if "zero sysadmin" includes "I don't have to notice
  it's down myself," skippable if not.
- **Seed/world-gen settings are write-once — worth documenting**: `SEED` and
  other world-generation options only take effect the first time a world is
  created. Since the world is intentionally stateful and never touched by a
  deploy, a future PR that changes `SEED` expecting new terrain will merge
  cleanly, deploy cleanly, and do *nothing* — worth a line in
  `CONTRIBUTING.md` so nobody burns a PR on it.

## 7. Next steps

Once you're happy with this spec (or after edits), I'll scaffold the actual
repo: `docker-compose.yml`, `provisioning/bootstrap.sh`, both workflows, and
a starter `plugin-configs/` — then we do a first deploy together against
the `minecraft` host to confirm end-to-end before opening it up for PRs.
