# Contributing

Everything about this server — settings, admins, plugins, datapacks — is
defined in this repo. Open a PR, get it reviewed and merged, and it's live.
See `../SPEC.md` for the full design and reasoning; this doc is the
practical how-to.

## Accounts

The server runs in offline mode (no Mojang purchase required) with
[AuthMeReloaded](https://modrinth.com/plugin/authmereloaded) handling
accounts: `/register <password> <password>` the first time you join,
`/login <password>` on later joins. There's no whitelist — anyone can
connect and register a name, so pick a name you're OK sharing and don't
reuse a password from elsewhere.

## Becoming an admin

Edit the `OPS` block in `docker-compose.yml` — add your Minecraft username
(one per line) — and open a PR. Since this list is reviewed like any other
change, whoever merges the PR is effectively approving the new admin.

## Adding a plugin

Add a line to `MODRINTH_PROJECTS` in `docker-compose.yml`:

```
MODRINTH_PROJECTS: |
  authmereloaded:ID72cfmM
  your-plugin-slug:VERSION_ID
```

The version must be an exact version ID or number from the plugin's
Modrinth page — not "latest". Grab the version ID from the URL of the
specific version you want (e.g. `modrinth.com/plugin/foo/version/XXXXXXXX`
→ `XXXXXXXX`). `validate_config.py` rejects unpinned refs, so an exact
version isn't optional — see `SPEC.md` §6 for why (a bare "latest" ref
means the running server isn't fully determined by the git commit anymore).

If the plugin needs its own config, see `plugin-configs/README.md`.

## Adding a datapack

See `datapacks/README.md`.

## A gotcha worth knowing: world-gen settings are write-once

`SEED` and other world-generation settings only take effect the first time
a world is created. Since the world is intentionally stateful and never
touched by a deploy, a PR that changes `SEED` expecting new terrain will
merge cleanly, deploy cleanly, and do *nothing* to the existing world.
Don't spend a PR on this.

## What happens after you merge

Every push to `main` triggers an immediate restart of the live server —
there's no staging environment, so a merge is live within a minute or two.
Players online at the time get a warning, then get disconnected. The
pre-merge smoke test catches a config that fails to boot, but it can't
catch a plugin that boots fine and then misbehaves once real players are
on it — that class of bug only shows up after merge.
