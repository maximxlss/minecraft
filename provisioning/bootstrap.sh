#!/usr/bin/env bash
# One-time host provisioning. Safe to re-run (idempotent) — run once by
# hand over SSH, or again if the host is ever rebuilt (SPEC.md §3).
set -euo pipefail

DATA_DIR=/opt/minecraft/data
BACKUP_DIR=/opt/minecraft/backups
ENV_FILE=/opt/minecraft/.env

if ! command -v docker &>/dev/null; then
  echo "Installing Docker..."
  curl -fsSL https://get.docker.com | sh
  sudo usermod -aG docker "$USER"
  echo "Added $USER to the docker group — log out/in (or re-SSH) for it to take effect."
fi

sudo mkdir -p "$DATA_DIR" "$BACKUP_DIR"
sudo chown "$USER":"$USER" /opt/minecraft
sudo chown -R "$USER":"$USER" "$DATA_DIR" "$BACKUP_DIR"

if [ ! -f "$ENV_FILE" ]; then
  echo "Generating RCON password into $ENV_FILE"
  printf 'RCON_PASSWORD=%s\n' "$(openssl rand -hex 16)" | sudo tee "$ENV_FILE" >/dev/null
  sudo chown "$USER":"$USER" "$ENV_FILE"
  sudo chmod 600 "$ENV_FILE"
else
  echo "$ENV_FILE already exists, leaving it alone."
fi

echo "Done. /opt/minecraft is ready — copy docker-compose.yml there and run 'docker compose up -d'."
