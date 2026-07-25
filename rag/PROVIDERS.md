# 🔌 Generation Endpoint

The agentic chat backend talks to **one** generation endpoint over the OpenAI
chat-completions protocol, configured in [`config.py`](config.py) and called
through [`llm.py`](llm.py). There are **no embeddings** — the backend answers only
by agentic filesystem navigation, so the endpoint is generation-only, and there is
no provider switch.

> **Ollama is itself OpenAI-compatible.** Running fully local just means pointing
> the base URL at Ollama's `/v1` endpoint — the same client, same code path as any
> hosted model.

## Configuration

Three settings, resolved with this precedence (first non-empty wins):

| Setting | Explicit env | Friendly `.env` key | Default |
|---|---|---|---|
| Base URL | `RAG_OPENAI_BASE_URL` | `base_url` | `http://localhost:11434/v1` (local Ollama) |
| API key | `RAG_OPENAI_API_KEY` | `api_key` | `ollama` (dummy; local Ollama ignores it) |
| Model | `RAG_GEN_MODEL` | `model` | `qwen3.6:35b-mlx` |

`pip install openai` is required (it's in `rag/requirements.txt`).

## 🦙 Local via Ollama (zero-config default)

```bash
ollama pull qwen3.6:35b-mlx          # or any tool-capable model you prefer
# nothing else to set — config.py already points at http://localhost:11434/v1
```

Override the model with `RAG_GEN_MODEL=<name>` if you pulled a different one.

## 🤖 Hosted (any OpenAI-compatible endpoint)

Works with OpenAI, DeepSeek, vLLM, LM Studio, OpenRouter, … — anything speaking
the OpenAI API.

```bash
export RAG_OPENAI_BASE_URL=https://api.deepseek.com/v1   # or your endpoint
export RAG_OPENAI_API_KEY=sk-...                         # never commit this
export RAG_GEN_MODEL=deepseek-chat
```

Or, equivalently, a repo-root `.env` (git-ignored) with the friendly keys
(explicit `RAG_*` env vars always win):

```ini
base_url=https://api.deepseek.com/v1
api_key=sk-...
model=deepseek-chat
```

## ⚙️ Protocol behaviour

- `temperature` is passed through; `num_predict` maps to `max_tokens`.
- `num_ctx` has no analogue in the OpenAI chat protocol and is **ignored** (kept in
  the `chat()` signature only so call sites stay unchanged).
- The agentic loop uses the **ReAct** text tool protocol by default
  (`AGENT_TOOL_BACKEND=react`) — plain user/assistant turns that every
  OpenAI-compatible endpoint, Ollama's `/v1` included, handles cleanly without the
  `tool_call_id` bookkeeping native tool-calling requires. Set
  `RAG_AGENT_TOOL_BACKEND=native` to use the OpenAI tool-calling schema if your
  endpoint supports it well.
- `AGENT_DECIDE_MAX_TOKENS=4096` gives reasoning models room so their hidden
  reasoning plus the fenced action block always complete. Lower it (e.g. `256`) for
  a fast local model that emits the action block directly.
- Hosted reasoning models doing deep multi-hop navigation may also want a higher
  `RAG_AGENT_MAX_STEPS` (default `12`).

## 🛟 Graceful degradation

The `openai` package is imported lazily — a clear install error is raised only when
generation is actually invoked. A stuck model is nudged and, past
`RAG_AGENT_MAX_STEPS`, forced to answer from the evidence already gathered. If the
backend is down entirely, the frontend's Search and Browse surfaces still work; only
Chat is affected.
