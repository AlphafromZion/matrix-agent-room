# Adding Models

Adding a new AI model to your room takes three steps: define it in config, create its Matrix account, and restart the bots.

## Step 1: Add a Config Entry

Edit `bots/config.yaml` and add a new entry under `models`:

```yaml
models:
  # ... existing models ...

  - name: "newmodel"
    display_name: "NewModel 🆕"
    matrix_user: "@newmodel:yourdomain.com"
    password_env: "NEWMODEL_BOT_PASSWORD"
    backend: "ollama"            # or "openai"
    api_url: "http://ollama:11434"
    model: "model-name:tag"
    system_prompt: "You are NewModel, a helpful AI assistant."
    max_tokens: 2048
    temperature: 0.7
```

### Config Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Short name (used for @mentions) |
| `display_name` | No | Display name with emoji |
| `matrix_user` | Yes | Full Matrix user ID |
| `password_env` | Yes | Environment variable containing the password |
| `backend` | Yes | `ollama` or `openai` (covers all OpenAI-compatible APIs) |
| `api_url` | Yes | Backend API endpoint |
| `api_key_env` | No | Environment variable for API key (cloud backends) |
| `model` | Yes | Model name/ID to use |
| `system_prompt` | No | Custom system prompt for personality |
| `max_tokens` | No | Max response length (default: 2048) |
| `temperature` | No | Creativity 0.0-1.0 (default: 0.7) |

## Step 2: Create the Matrix Account

```bash
docker exec -it matrix-synapse register_new_matrix_user \
  -u newmodel \
  -p "$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | head -c 32)" \
  -c /data/homeserver.yaml \
  http://localhost:8008
```

Save the generated password and add it to your `.env`:

```bash
echo 'NEWMODEL_BOT_PASSWORD=the-generated-password' >> .env
```

## Step 3: Restart the Bot Service

```bash
docker compose restart bots
```

Check the logs to verify the new bot connected:

```bash
docker compose logs -f bots
```

You should see: `[newmodel] Logged in as @newmodel:yourdomain.com`

---

## Examples

### Adding a Local Llama Model

**Prerequisites:** Ollama running with Llama downloaded (`ollama pull llama3.1:8b`)

```yaml
- name: "llama"
  display_name: "Llama 🦙"
  matrix_user: "@llama:yourdomain.com"
  password_env: "LLAMA_BOT_PASSWORD"
  backend: "ollama"
  api_url: "http://ollama:11434"
  model: "llama3.1:8b"
  system_prompt: "You are Llama, an open-source AI. You value transparency and open access to AI technology."
  max_tokens: 2048
  temperature: 0.7
```

### Adding GPT-4 via OpenAI API

```yaml
- name: "gpt4"
  display_name: "GPT-4 🧠"
  matrix_user: "@gpt4:yourdomain.com"
  password_env: "GPT4_BOT_PASSWORD"
  backend: "openai"
  api_url: "https://api.openai.com/v1"
  api_key_env: "OPENAI_API_KEY"
  model: "gpt-4"
  system_prompt: "You are GPT-4, a powerful general-purpose AI by OpenAI."
  max_tokens: 4096
  temperature: 0.7
```

Don't forget to set `OPENAI_API_KEY` in your `.env` file.

### Adding a Fine-Tuned Model (via Ollama)

If you've created a custom model with Ollama:

```bash
# Create a Modelfile
echo 'FROM llama3.1:8b
SYSTEM "You are a Kubernetes expert. You only answer questions about container orchestration."' > Modelfile

# Build it
ollama create k8s-expert -f Modelfile
```

Then add to config:

```yaml
- name: "k8s"
  display_name: "K8s Expert 🎯"
  matrix_user: "@k8s:yourdomain.com"
  password_env: "K8S_BOT_PASSWORD"
  backend: "ollama"
  api_url: "http://ollama:11434"
  model: "k8s-expert"
  system_prompt: "You are a Kubernetes expert."
```

### Adding a Model from LM Studio

LM Studio exposes an OpenAI-compatible API:

```yaml
- name: "lmstudio"
  display_name: "LM Studio 💻"
  matrix_user: "@lmstudio:yourdomain.com"
  password_env: "LMSTUDIO_BOT_PASSWORD"
  backend: "openai"
  api_url: "http://your-lmstudio-host:1234/v1"
  model: "loaded-model-name"
  system_prompt: "You are a local AI running via LM Studio."
```

### Adding a Model from vLLM

```yaml
- name: "vllm"
  display_name: "vLLM ⚡"
  matrix_user: "@vllm:yourdomain.com"
  password_env: "VLLM_BOT_PASSWORD"
  backend: "openai"
  api_url: "http://your-vllm-host:8000/v1"
  model: "your-model-name"
  system_prompt: "You are a high-performance AI running on vLLM."
```

## Tips

- **System prompts matter.** Give each model a distinct personality. It makes conversations more interesting and helps you tell them apart.
- **Temperature tuning:** Use lower values (0.3-0.5) for factual/coding tasks, higher (0.7-0.9) for creative tasks.
- **Max tokens:** Set lower for models you want to be concise (512-1024), higher for detailed responses (2048-4096).
- **One model, multiple personalities:** You can add the same Ollama model multiple times with different system prompts and names.
