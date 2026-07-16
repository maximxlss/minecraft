#!/usr/bin/env python3
"""Checks the OPS/WHITELIST/MODRINTH_PROJECTS blocks in docker-compose.yml.

`docker compose config` already confirms the file parses; this catches the
things that are syntactically valid YAML but still wrong: malformed
usernames/UUIDs, duplicate plugin entries, and unpinned ("latest") plugin
refs (SPEC.md §6, "Plugin/mod version pinning").
"""
import re
import sys

import yaml

USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,16}$")
UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{12}$"
)


def lines(block):
    if not block:
        return []
    return [line.strip() for line in block.splitlines() if line.strip()]


def check_players(name, block):
    errors = []
    for entry in lines(block):
        if not (USERNAME_RE.match(entry) or UUID_RE.match(entry)):
            errors.append(f"{name}: '{entry}' isn't a valid username or UUID")
    return errors


def check_plugins(block):
    errors = []
    seen = set()
    for entry in lines(block):
        if ":" not in entry:
            errors.append(
                f"MODRINTH_PROJECTS: '{entry}' has no pinned version "
                "(expected 'slug:version') — bare project refs float to "
                "whatever's newest at deploy time"
            )
            continue
        slug, version = entry.split(":", 1)
        if version.strip().lower() in ("latest", "*", ""):
            errors.append(f"MODRINTH_PROJECTS: '{entry}' pins to 'latest', not an exact version")
        if slug in seen:
            errors.append(f"MODRINTH_PROJECTS: duplicate entry for '{slug}'")
        seen.add(slug)
    return errors


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "docker-compose.yml"
    with open(path) as f:
        compose = yaml.safe_load(f)

    env = compose.get("services", {}).get("mc", {}).get("environment", {})
    errors = []
    errors += check_players("OPS", env.get("OPS", ""))
    errors += check_players("WHITELIST", env.get("WHITELIST", ""))
    errors += check_plugins(env.get("MODRINTH_PROJECTS", ""))

    if errors:
        print("validate_config.py found problems:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    print("validate_config.py: OK")


if __name__ == "__main__":
    main()
