# Architecture

## How It Works

matrix-agent-room is a collection of components that work together to create a multi-model AI chat experience on Matrix.

## Components

### Matrix Synapse (Homeserver)

The backbone. Synapse handles:
- User accounts (you + each AI bot gets an account)
- Room management (who can see what)
- Message routing and storage
- E2E encryption key exchange
- Federation (optional — disabled by default for privacy)

### Element Web (Client)

A browser-based Matrix client. You interact with your AI team through this. Any Matrix client works (Element mobile, FluffyChat, nheko, etc.) — Element Web is just the default.

### Bot Runner (Python Service)

The brain. A Python service using [matrix-nio](https://github.com/matrix-nio/matrix-nio) that:
1. Connects to Synapse as multiple bot users simultaneously
2. Listens for `@mentions` in room messages
3. Routes the message to the correct AI backend
4. Posts the response back to the room as that bot

### AI Backends

The actual models. The bot runner supports:
- **Ollama** — for local models (Mistral, Llama, Qwen, etc.)
- **OpenAI-compatible APIs** — for cloud models or local servers that speak the OpenAI format (LM Studio, vLLM, text-generation-webui, LocalAI)

## Message Flow

```
┌────────┐    ┌─────────┐    ┌────────────┐    ┌──────────┐
│  You   │───▶│ Element  │───▶│  Synapse   │───▶│ Bot      │
│ (User) │    │  Web     │    │ Homeserver │    │ Runner   │
└────────┘    └─────────┘    └────────────┘    └────┬─────┘
                                                     │
                                          ┌──────────┴──────────┐
                                          │                     │
                                   ┌──────▼──────┐    ┌────────▼────────┐
                                   │   Ollama     │    │ OpenAI-compat   │
                                   │ (local GPU)  │    │   (API call)    │
                                   └──────┬───────┘    └────────┬────────┘
                                          │                     │
                                          └──────────┬──────────┘
                                                     │
                                              ┌──────▼──────┐
                                              │  Response    │
                                              │  → Synapse   │
                                              │  → Element   │
                                              │  → You       │
                                              └─────────────┘
```

**Step by step:**

1. You type a message in Element: `@mistral explain quicksort`
2. Element sends it to Synapse via the Matrix client-server API
3. Synapse stores the message and notifies all room members (including bots)
4. The bot runner receives the message event via matrix-nio sync
5. It parses the @mention and identifies which bot should respond (`mistral`)
6. The Mistral bot's handler sends the cleaned message to Ollama
7. Ollama runs inference on the local Mistral model
8. The response is sent back to Synapse as a new message from `@mistral`
9. Element displays it in the room
10. Other bots see the response — they could be mentioned to comment on it

## Design Decisions

### Why matrix-nio?

- Pure Python, async-native
- First-class E2E encryption support
- Active maintenance
- Simple callback-based API

### Why one service for all bots?

Instead of running separate containers per bot, the bot runner manages all bots in one process. This:
- Reduces resource overhead (one Python process vs many)
- Simplifies config (one YAML file)
- Makes inter-bot awareness easier (they share a process)
- Is perfectly adequate for most setups (async handles concurrency)

For massive scale, you could split bots into separate services.

### Why Ollama as the default local backend?

- Dead simple API (one POST endpoint)
- Manages model downloads and GPU allocation
- Supports virtually every popular open model
- Runs on Mac, Linux, Windows
- Active development, good community

### Why Synapse over Conduit/Dendrite?

Synapse is the most mature and battle-tested homeserver. For a private instance with a few users and some bots, it's more than adequate. If RAM is tight, Conduit is a solid alternative — the bot framework doesn't care which homeserver you use.

## Scaling

### Horizontal

- Run Ollama on a separate machine with a GPU — just change the `api_url`
- Run multiple Ollama instances for different models
- Use a load balancer in front of multiple inference servers

### Vertical

- More VRAM = bigger models
- More RAM = more concurrent conversations
- Synapse can handle thousands of users on modest hardware

### Federation

Federation is **off by default**. This is intentional — your AI conversations should stay private. If you want to federate (allow users from other Matrix servers), enable it in `homeserver.yaml`. But think carefully about whether you want your AI conversations visible to federated servers.
