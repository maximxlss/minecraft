Vanilla datapacks go here, one directory per pack. Nothing here yet.

To add one:

1. Add the pack under `datapacks/<name>/` (must contain `pack.mcmeta` etc.,
   standard datapack layout).
2. Bind-mount it in `docker-compose.yml` under the `mc` service's
   `volumes:`, e.g.:
   ```yaml
   - ./datapacks/<name>:/data/world/datapacks/<name>
   ```

Note: `world/` is the default level name — if `LEVEL` is ever changed in
`docker-compose.yml`, update this path to match.
