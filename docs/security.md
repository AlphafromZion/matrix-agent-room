# Security

Your AI conversations are some of the most sensitive data you produce. They contain your thought patterns, your code, your strategies, your personal questions. This document covers how to keep them private.

## Why Self-Hosted Matters

When you use a cloud AI chat service:
- The provider sees every message
- Your conversation history lives on their servers
- They can train on your data (read the ToS carefully)
- They can be compelled to hand over data
- They can shut down or change terms at any time

With matrix-agent-room:
- **Everything runs on your hardware**
- **No data leaves your network** (unless you use cloud API backends)
- **You control encryption keys**
- **You control retention**
- **No telemetry, no analytics, no tracking**

## E2E Encryption

Matrix supports end-to-end encryption (E2EE). When enabled, messages are encrypted on the sender's device and can only be decrypted by verified recipients. Not even the homeserver can read them.

### Option 1: Native E2E via matrix-nio

matrix-nio supports E2E encryption natively using `libolm`. The bot framework includes E2E support when you install with `matrix-nio[e2e]`.

**Setup:**
1. Ensure `libolm` is installed (included in the Docker image)
2. Bot key/session data persists in the `bot_data` volume
3. Verify bot devices from your Element client

**Caveat:** Bot-side E2E means the bot process can read messages (it has to, to respond). The protection is in-transit and at-rest on the server — only verified devices can decrypt.

### Option 2: Pantalaimon (E2E Proxy)

[Pantalaimon](https://github.com/matrix-org/pantalaimon) acts as a reverse proxy that handles encryption/decryption transparently. The bot connects to Pantalaimon (unencrypted locally), and Pantalaimon handles all the E2E with Synapse.

**Pros:** Simpler bot code, battle-tested E2E implementation
**Cons:** Extra service to run, adds latency

## Network Isolation

### Recommended Setup

```
┌─────────────────────────────────────────────┐
│ Docker Network (matrix)                      │
│                                              │
│  Synapse ◄──► Bots ◄──► Ollama             │
│     ▲                                        │
│     │ Port 8008 (internal only)              │
│     │                                        │
│  Element Web                                 │
│     ▲                                        │
│     │ Port 8080                              │
└─────┼────────────────────────────────────────┘
      │
   Your browser (localhost only)
```

**Key principles:**
- Synapse only needs to be reachable by Element and the bots
- Ollama only needs to be reachable by the bots
- Element only needs to be reachable by your browser
- **Nothing needs to be exposed to the internet** for local-only use

### If Exposing Externally

If you need remote access (mobile client, etc.):
- Use a reverse proxy (nginx, Caddy) with TLS
- Consider a tunnel (Cloudflare Tunnel, Tailscale) instead of opening ports
- **Never expose Synapse directly to the internet without TLS**
- Rate limit external access

### Firewall Rules

```bash
# Only allow Element Web from localhost
iptables -A INPUT -p tcp --dport 8080 -s 127.0.0.1 -j ACCEPT
iptables -A INPUT -p tcp --dport 8080 -j DROP

# Block Synapse from external access (Docker handles internal routing)
iptables -A INPUT -p tcp --dport 8008 -s 127.0.0.1 -j ACCEPT
iptables -A INPUT -p tcp --dport 8008 -j DROP
```

## API Key Security

If you use cloud backends (OpenAI, Anthropic):

1. **Never put API keys in config files** — use environment variables (`api_key_env` in config.yaml)
2. **Never commit `.env` files** — the `.gitignore` already blocks this
3. **Use separate API keys** for this project — easy to revoke if compromised
4. **Monitor API usage** — set spending limits on your cloud accounts
5. **Consider a proxy** — route cloud API calls through a local proxy for logging/auditing

## Data Retention

Synapse stores messages indefinitely by default. You can configure retention policies:

```yaml
# In homeserver.yaml
retention:
  enabled: true
  default_policy:
    min_lifetime: 1d
    max_lifetime: 90d    # Auto-delete messages older than 90 days
```

For maximum privacy, consider:
- Short retention periods for sensitive rooms
- Regular database vacuuming
- Encrypted backups of the Synapse data volume

## What This Project Does NOT Do

- **No telemetry** — zero analytics, zero phone-home, zero tracking
- **No cloud dependencies** — works fully offline (with local models)
- **No account creation on external services** — everything is local
- **No data collection** — your data stays in your Docker volumes

## Threat Model

| Threat | Mitigation |
|--------|------------|
| Network eavesdropping | E2E encryption + TLS |
| Server compromise | E2E means server can't read messages |
| Physical access to server | Full disk encryption (OS level) |
| Cloud API provider logging | Use local models for sensitive conversations |
| Compromised bot process | Isolate with Docker, limit permissions |
| Data persistence after deletion | Retention policies + volume encryption |

## Recommendations

1. **Use local models for sensitive conversations.** Cloud APIs see your prompts.
2. **Enable E2E encryption.** It's one of Matrix's best features — use it.
3. **Run on hardware you physically control.** Not a VPS, not a cloud instance.
4. **Keep your stack updated.** `docker compose pull` regularly.
5. **Back up your encryption keys.** Lost keys = lost message history.
