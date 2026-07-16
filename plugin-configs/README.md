Per-plugin config overrides go here, one directory per plugin (e.g.
`AuthMe/config.yml`). Nothing here yet — AuthMeReloaded is running on its
defaults for now. To override a plugin's config:

1. Add the file under `plugin-configs/<Plugin>/...`.
2. Bind-mount it in `docker-compose.yml` under the `mc` service's
   `volumes:`, e.g.:
   ```yaml
   - ./plugin-configs/AuthMe/config.yml:/data/plugins/AuthMe/config.yml
   ```
