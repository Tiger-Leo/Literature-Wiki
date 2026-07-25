"""Central configuration for the literature-wiki agentic-search chat backend.

This backend answers ONLY by agentic filesystem navigation — there is no
embedding index, vector store, BM25, or graph index. Every knob the agentic
loop, the generation provider, and the server need lives here. Settings are
env-overridable (RAG_*) so behaviour can be tuned without editing files.
"""

from __future__ import annotations

import os
from pathlib import Path


def _i(name: str, default: int) -> int:
    return int(os.environ.get(name, default))


def _f(name: str, default: float) -> float:
    return float(os.environ.get(name, default))


# --- Paths -----------------------------------------------------------------
# REPO_ROOT defaults to the directory that holds this rag/ package, so the original
# layout (rag/ sitting inside the wiki repo) works with no configuration. To point the
# backend at a wiki living elsewhere, set RAG_WIKI_ROOT to that wiki repo's root.
_DEFAULT_ROOT = Path(__file__).resolve().parents[1]      # default: rag/'s parent
WIKI_ROOT = Path(os.environ.get("RAG_WIKI_ROOT", str(_DEFAULT_ROOT))).resolve()
# REPO_ROOT == WIKI_ROOT: the agentic filesystem sandbox (rag/agent_tools.py) is
# rooted here, so it always reads the configured wiki tree.
REPO_ROOT = WIKI_ROOT
# Each corpus path derives from WIKI_ROOT by default but honors an independent env
# override, so arbitrary on-disk layouts (e.g. a wiki/ that is not under the repo root)
# work without symlink hacks.
WIKI_DIR = Path(os.environ.get("RAG_WIKI_DIR", WIKI_ROOT / "wiki"))
RAW_DIR = Path(os.environ.get("RAG_RAW_DIR", WIKI_ROOT / "raw_markdown" / "papers"))
SOURCES_DIR = Path(os.environ.get("RAG_SOURCES_DIR", WIKI_DIR / "sources"))

RAG_DIR = Path(__file__).resolve().parent
DB_PATH = RAG_DIR / "threads.db"

# Tier-A: curated wiki knowledge layers. Tier-B: raw papers. Used by the server's
# /api/page resolver and the agentic sources panel to classify a read file's layer.
# Override the taxonomy for a different wiki via RAG_TIER_A_DIRS (comma-separated).
_DEFAULT_TIER_A_DIRS = [
    "concepts", "mechanisms", "debates", "methods",
    "measures", "synthesis", "sources", "pipeline-notes",
]
TIER_A_DIRS = [
    d.strip() for d in os.environ.get("RAG_TIER_A_DIRS", "").split(",") if d.strip()
] or _DEFAULT_TIER_A_DIRS

# --- Domain description (de-hardcodes the wiki's subject from prompts) ------
# Used in the agentic system prompt. Set RAG_DOMAIN_DESC to your wiki's subject,
# e.g. "the economics of innovation".
DOMAIN_DESC = os.environ.get(
    "RAG_DOMAIN_DESC",
    "a curated research-literature wiki of Wikipedia-style synthesis pages",
)

# --- Generation: a single OpenAI-compatible endpoint -----------------------
# Generation (agentic QA + chat titles) goes through ONE endpoint speaking the
# OpenAI chat-completions protocol (rag/llm.py). There are NO embeddings — the
# provider is generation-only. Ollama is itself OpenAI-compatible, so running
# fully local just means pointing the base URL at Ollama's /v1 endpoint (the
# default below). A hosted model (OpenAI, DeepSeek, vLLM, LM Studio, OpenRouter,
# …) is the same endpoint with a different base_url + api_key + model.
#
# Optional convenience: a repo-root `.env` with friendly keys lets you configure
# the endpoint without exporting RAG_* vars (explicit RAG_* always wins):
#   base_url=https://api.deepseek.com/v1   api_key=sk-...   model=deepseek-chat
def _load_env_file(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            data[key.strip()] = val.strip().strip('"').strip("'")
    return data


_ENV_FILE = _load_env_file(REPO_ROOT / ".env")

# OpenAI-compatible endpoint config. Precedence (first non-empty wins):
#   1. explicit env:  RAG_OPENAI_BASE_URL / RAG_OPENAI_API_KEY / RAG_GEN_MODEL
#   2. friendly .env: base_url / api_key / model
#   3. the local-Ollama defaults below (Ollama serves the OpenAI protocol at /v1).
OPENAI_BASE_URL = (os.environ.get("RAG_OPENAI_BASE_URL")
                   or _ENV_FILE.get("base_url")
                   or "http://localhost:11434/v1")    # Ollama's OpenAI-compatible endpoint
OPENAI_API_KEY = (os.environ.get("RAG_OPENAI_API_KEY")
                  or _ENV_FILE.get("api_key")
                  or "ollama")                          # dummy key; local Ollama ignores it
GEN_MODEL = (os.environ.get("RAG_GEN_MODEL")
             or _ENV_FILE.get("model")
             or "qwen3.6:35b-mlx")                      # default local model

# --- Server ----------------------------------------------------------------
# CORS allowed origins (comma-separated). Default "*" is convenient for local dev;
# restrict it (e.g. "https://my-frontend.example") before exposing the server.
CORS_ORIGINS = os.environ.get("RAG_CORS_ORIGINS", "*")
# Context window hint. The OpenAI chat protocol has no num_ctx knob, so this is
# ignored over the wire; kept so call sites stay unchanged (and so a future
# native-Ollama path could honor it). Covers a long agentic transcript + answer.
NUM_CTX = _i("RAG_NUM_CTX", 32768)

# --- Agentic QA (filesystem-tool navigation; no embeddings) ----------------
# The answer path (rag/agent_qa.py) drives the generation model with a tiny set of
# sandboxed wiki-filesystem tools (list_dir/glob/grep/read_file), replicating the
# /wiki-query read order.
AGENT_MAX_STEPS = _i("RAG_AGENT_MAX_STEPS", 12)           # max tool-call turns
AGENT_NUM_CTX = _i("RAG_AGENT_NUM_CTX", NUM_CTX)          # context window for agent chat
AGENT_GREP_MAX = _i("RAG_AGENT_GREP_MAX", 40)            # default grep hit cap
AGENT_READ_LIMIT = _i("RAG_AGENT_READ_LIMIT", 400)        # default read_file line window
# Tool protocol: react (fenced ```action {json}``` text protocol) | native
# (OpenAI tool-calling schema) | auto (try native, fall back to react). Default
# is `react`: plain user/assistant turns that every OpenAI-compatible endpoint —
# including Ollama's /v1 — handles cleanly, without the tool_call_id bookkeeping
# native tool-calling needs. Set RAG_AGENT_TOOL_BACKEND=native if your endpoint
# supports OpenAI tool-calling well and you prefer it.
AGENT_TOOL_BACKEND = os.environ.get("RAG_AGENT_TOOL_BACKEND") or "react"  # react|native|auto
# Agent model calls can run long (the final-answer generation streams hundreds of
# words). Use a generous, agent-only timeout so a slow generation never trips the
# shared 120s client timeout. Applies to the dedicated client in rag/agent_qa.py.
AGENT_TIMEOUT = _f("RAG_AGENT_TIMEOUT", 900.0)
# Cap the OUTPUT of each tool-decision turn so the model cannot generate a long answer
# inline (which would block, then dump all at once). A tool call / write_answer fits
# easily; an attempted inline answer is truncated -> we then route to the dedicated
# streaming final-answer call. Keeps deciding turns short and the answer always streamed.
# Hosted reasoning models spend tokens on hidden reasoning BEFORE emitting visible
# content, so a tight cap can exhaust the budget mid-reasoning and leave the action
# block empty. Default gives ample room; lower it (e.g. 256) for a fast local model
# that emits the action block directly without hidden reasoning.
AGENT_DECIDE_MAX_TOKENS = _i("RAG_AGENT_DECIDE_MAX_TOKENS", 4096)
