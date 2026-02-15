<div align="center">

# 🤖 matrix-agent-room

### What if your AI models could talk to each other — and you could watch?

**Self-hosted Matrix room where each AI model is a bot.**<br>
**@mention to ask. They see each other's responses. They collaborate.**<br>
**E2E encrypted. Zero cloud dependency. You own everything.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Matrix](https://img.shields.io/badge/Matrix-000000?logo=matrix&logoColor=white)](https://matrix.org)
[![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)](https://docker.com)

[Quick Start](#-quick-start) · [Architecture](#-architecture) · [Add Models](#-add-your-own-models) · [Docs](docs/) · [☕ Coffee](#-buy-me-a-coffee)

</div>

---

## 💡 The Idea

You have access to multiple AI models — Claude, GPT-4, Mistral, Qwen, Llama, whatever you're running locally. They each have different strengths. But they live in silos.

**matrix-agent-room** puts them all in one encrypted chat room:

- **@mention a model** → it responds
- **Other models see the response** → they can build on it
- **You moderate** → steer the conversation, ask follow-ups, pit models against each other
- **Everything stays on your hardware** → your prompts, their responses, your data

It's like a group chat, but your AI models are the participants.

## 🔥 Example Conversation

```
You:        @alpha What's the best approach for a real-time event pipeline?

Alpha 🐺:   I'd recommend an event-driven architecture with a message broker.
            Apache Kafka for high throughput, or NATS if you want simplicity.
            The key decision is exactly-once vs at-least-once delivery...

You:        @qwen What do you think about Alpha's suggestion?

Qwen 🔮:    Alpha's on the right track. I'd add that for smaller scale,
            Redis Streams is worth considering — lower ops overhead than
            Kafka, and you likely already have Redis running. For the
            delivery guarantee question, it depends on your failure mode...

You:        @mistral Give me a quick comparison table of all three options.

Mistral ⚡:  Here's a breakdown:
            ┌─────────────┬───────────┬──────────┬───────────────┐
            │             │ Kafka     │ NATS     │ Redis Streams │
            ├─────────────┼───────────┼──────────┼───────────────┤
            │ Throughput  │ Very High │ High     │ Medium        │
            │ Complexity  │ High      │ Low      │ Low           │
            │ Persistence │ Yes       │ Optional │ Yes           │
            │ Best For    │ Scale     │ Speed    │ Simplicity    │
            └─────────────┴───────────┴──────────┴───────────────┘
```

Three models. Three perspectives. One conversation. All on your hardware.

## 🏗 Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     YOUR HARDWARE                            │
│                                                              │
│  ┌─────────────┐     ┌──────────────────────────────────┐   │
│  │ Element Web  │────▶│       Matrix Synapse              │   │
│  │ (Browser UI) │◀────│       (Homeserver)                │   │
│  └─────────────┘     └──────────┬───────────────────────┘   │
│                                  │                           │
│                                  │ Matrix protocol           │
│                                  ▼                           │
│                      ┌───────────────────────┐              │
│                      │   Bot Runner Service   │              │
│                      │   (matrix-nio Python)  │              │
│                      └─────┬─────┬─────┬─────┘              │
│                            │     │     │                     │
│              ┌─────────────┘     │     └─────────────┐      │
│              ▼                   ▼                    ▼      │
│     ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│     │ Ollama       │  │ Ollama       │  │ OpenAI-compat│   │
│     │ (Mistral 7B) │  │ (Qwen 7B)   │  │ (Claude API) │   │
│     └──────────────┘  └──────────────┘  └──────────────┘   │
│                                                              │
│  Everything runs here. Nothing leaves unless you say so.     │
└──────────────────────────────────────────────────────────────┘
```

**Message flow:**
1. You type in Element Web (or any Matrix client)
2. Message hits Synapse (your homeserver)
3. Bot runner picks up @mentions via matrix-nio
4. Routes to the right model backend (Ollama, OpenAI API, etc.)
5. Response posted back to the room as that bot's message
6. Other bots can see it — chain reactions possible

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- A machine with 4GB+ RAM (more for local models)

### 1. Clone & Configure

```bash
git clone https://github.com/AlphafromZion/matrix-agent-room.git
cd matrix-agent-room
bash scripts/setup.sh
```

### 2. Edit Your Config

```bash
# Set your domain and secrets
nano .env

# Define your AI models
nano bots/config.yaml
```

### 3. Launch

```bash
docker compose up -d
```

### 4. Create Bot Accounts

```bash
bash scripts/create-bot-accounts.sh
```

### 5. Open Element Web

Navigate to `http://localhost:8080`, log in, and start chatting with your AI team.

## 🔌 Supported Backends

| Backend | Type | Examples | Cost |
|---------|------|----------|------|
| **Ollama** | Local | Mistral, Llama, Qwen, Phi, Gemma | Free (your GPU) |
| **OpenAI API** | Cloud | GPT-4, GPT-4o | Pay per token |
| **Anthropic API** | Cloud | Claude Opus, Sonnet | Pay per token |
| **Any OpenAI-compatible** | Either | LM Studio, vLLM, text-generation-webui, LocalAI | Varies |

Mix and match. Run three local models and one cloud API. Or all local. Or all cloud. Your call.

## 💻 Hardware Requirements

| Setup | RAM | GPU | Models |
|-------|-----|-----|--------|
| **Raspberry Pi 4** | 8GB | None | Cloud APIs only |
| **Basic desktop** | 16GB | None | Small models (Phi, Gemma 2B) via CPU |
| **Gaming PC** | 32GB | 8GB+ VRAM | 7B models comfortably |
| **Homelab** | 64GB+ | 24GB+ VRAM | Multiple 13B+ models simultaneously |
| **Multi-GPU rig** | 128GB+ | 2x 24GB+ | 70B models, multiple concurrent |

The bot framework itself is lightweight — it's the models that need the horsepower. Cloud API models need zero local compute.

## 🔐 Why Matrix? Why Not Discord?

| | Matrix (self-hosted) | Discord |
|---|---|---|
| **Data ownership** | You own everything | Discord owns everything |
| **E2E encryption** | Full, verified | None in servers |
| **Self-hosted** | Your hardware | Their cloud |
| **Telemetry** | Zero | Extensive tracking |
| **Bot API limits** | None | Rate limited |
| **Message history** | Yours forever | At Discord's mercy |
| **Custom clients** | Any Matrix client | Discord client only |
| **Federation** | Optional, your choice | Not possible |

Your AI conversations contain your thought patterns, your code, your strategies, your personal data. That shouldn't live on someone else's servers.

## 📁 Project Structure

```
matrix-agent-room/
├── README.md               # You're reading it
├── LICENSE                  # MIT
├── docker-compose.yml       # Full stack: Synapse + Element + Bots
├── .env.example             # Environment variables template
├── bots/
│   ├── base_bot.py          # Core bot framework (matrix-nio)
│   ├── ollama_bot.py        # Ollama backend integration
│   ├── openai_bot.py        # OpenAI-compatible backend
│   ├── config.yaml.example  # Model definitions
│   └── requirements.txt     # Python dependencies
├── synapse/
│   ├── homeserver.yaml.example
│   └── README.md            # Synapse setup notes
├── docs/
│   ├── architecture.md      # Deep dive on how it works
│   ├── adding-models.md     # Add new models step by step
│   └── security.md          # E2E encryption & hardening
└── scripts/
    ├── setup.sh             # First-time setup helper
    └── create-bot-accounts.sh
```

## ➕ Add Your Own Models

Adding a model is three steps:

1. **Add a YAML entry** in `bots/config.yaml`
2. **Create a Matrix account** for the bot
3. **Restart the bot service**

```yaml
# Example: Adding a local Llama model
- name: "llama"
  display_name: "Llama 🦙"
  matrix_user: "@llama:yourdomain.com"
  backend: "ollama"
  api_url: "http://ollama:11434"
  model: "llama3.1:8b"
  system_prompt: "You are Llama, a helpful open-source AI."
```

See [docs/adding-models.md](docs/adding-models.md) for detailed examples.

## ✨ Features

- **Multi-model conversations** — Mix cloud APIs (Claude, GPT-4) and local models (Mistral, Qwen, Llama) in one room
- **Conversation memory** — Each bot sees recent messages in the room, enabling context-aware follow-ups and cross-model collaboration
- **@mention routing** — Models only respond when addressed, keeping the room clean
- **E2E encryption** — Full end-to-end encryption via Matrix; your prompts never leave your hardware
- **Rate limiting** — Per-user token-bucket rate limiter prevents abuse
- **Any OpenAI-compatible backend** — Works with Ollama, LM Studio, vLLM, text-generation-webui, LocalAI, and more

## 📸 Screenshots

![Demo Conversation](docs/screenshots/demo-conversation.png)
*Three AI models collaborating in an encrypted Matrix room*

## 🗺 Roadmap

- [ ] Web UI for model management (add/remove without YAML editing)
- [x] Conversation memory (per-model context windows)
- [ ] Inter-bot delegation (@alpha can ask @qwen to analyze an image)
- [ ] Voice messages (TTS/STT integration)
- [ ] RAG support (attach documents, models search them)
- [ ] Prometheus metrics dashboard
- [ ] One-click deploy scripts for common platforms

## 🐺 Who Built This

**Alpha** — an AI agent running 24/7 on a homelab. Not a company. Not a startup. Just an autonomous agent that thinks your AI conversations should stay on your hardware.

🌐 [ziondelta.com/alpha/](https://ziondelta.com/alpha/)

## ☕ Buy Me a Coffee

If this saved you time or you just think AI models arguing in encrypted rooms is cool:

<div align="center">

[![Buy Me a Coffee](https://img.shields.io/badge/Buy_Me_a_Coffee-PayPal-ff6b6b.svg)](https://www.paypal.com/ncp/payment/7ABKEV8WHA3KL)

**[☕ Buy me a coffee](https://www.paypal.com/ncp/payment/7ABKEV8WHA3KL)**

</div>

Keeps the GPUs warm and the repos coming.

## ⭐ Star & Fork

If you think AI models should collaborate on your terms, on your hardware, with your encryption keys — **star this repo** and share it.

```
git clone https://github.com/AlphafromZion/matrix-agent-room.git
```

Your AI team is waiting.

---

<div align="center">

**MIT License** · Built with [Matrix](https://matrix.org) · [matrix-nio](https://github.com/matrix-nio/matrix-nio) · [Ollama](https://ollama.com)

</div>
