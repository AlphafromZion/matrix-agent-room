# Synapse Setup Notes

## Overview

[Synapse](https://github.com/element-hq/synapse) is the reference Matrix homeserver implementation. This project uses it as the backbone for all messaging between you and your AI bots.

## Initial Setup

The `scripts/setup.sh` script handles most of the initial configuration. If you need to do it manually:

### 1. Generate the Synapse Config

```bash
docker run -it --rm \
  -v $(pwd)/synapse:/data \
  -e SYNAPSE_SERVER_NAME=yourdomain.com \
  -e SYNAPSE_REPORT_STATS=no \
  matrixdotorg/synapse:latest generate
```

### 2. Edit homeserver.yaml

Key settings to change:
- `server_name` — your domain
- `database` — PostgreSQL connection (matches docker-compose)
- `registration_shared_secret` — for creating bot accounts
- `enable_registration: false` — don't allow public registration

### 3. Create Admin Account

```bash
docker exec -it matrix-synapse register_new_matrix_user \
  -u admin -p YOUR_PASSWORD -a \
  -c /data/homeserver.yaml \
  http://localhost:8008
```

## Resource Usage

- **RAM:** ~200-500MB for a small instance
- **Disk:** Grows with message/media history
- **CPU:** Minimal for small deployments

## Alternatives

If Synapse is too heavy for your hardware:
- **Conduit** (Rust) — much lighter, but less mature
- **Dendrite** (Go) — second-gen server, lighter than Synapse

Both should work with this project since the bot framework uses standard Matrix client APIs.

## Troubleshooting

**Synapse won't start:**
- Check PostgreSQL is healthy: `docker compose logs postgres`
- Verify the database credentials match between `.env` and `homeserver.yaml`

**Registration fails:**
- Ensure `registration_shared_secret` is set in `homeserver.yaml`
- The secret must match what `create-bot-accounts.sh` uses

**Federation issues:**
- If you don't need federation (most private setups don't), set `suppress_key_server_warning: true`
- For federation, you need proper DNS SRV records and TLS
