Per-plugin config overrides go here, one directory per plugin.

- `BlueMap/core.conf` — sets `accept-download: true`, required for BlueMap
  to start its webserver/web map (without this it logs a WARN and disables
  the webserver). Everything else in that file is BlueMap's generated defaults.

Everything else is running on plugin defaults for now. To override a
plugin's config:

1. Add the file under `plugin-configs/<Plugin>/...`.
2. Bind-mount it in `docker-compose.yml` under the `mc` service's
   `volumes:`, e.g.:
   ```yaml
   - ./plugin-configs/AuthMe/config.yml:/data/plugins/AuthMe/config.yml
   ```
