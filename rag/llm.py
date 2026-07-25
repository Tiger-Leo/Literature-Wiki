"""Generation for the agentic-search backend — one OpenAI-compatible endpoint.

Generation (agentic QA, chat titles) talks to a single endpoint speaking the
OpenAI chat-completions protocol, configured by ``config.OPENAI_BASE_URL`` /
``config.OPENAI_API_KEY`` / ``config.GEN_MODEL``. There are NO embeddings in this
backend — generation only.

Ollama is itself OpenAI-compatible, so "fully local" is just this same client
pointed at Ollama's ``/v1`` endpoint (the default ``base_url``). A hosted model
(OpenAI, DeepSeek, vLLM, LM Studio, OpenRouter, …) is the same client with a
different base_url + api_key + model. There is no provider switch.

The rest of the backend uses one stable entry point:

* ``chat(messages, *, model=None, tools=None, stream=False, num_ctx=None,
        temperature=0.2, num_predict=None, timeout=None)``

``chat`` returns ollama-style objects that support BOTH mapping access
(``resp["message"]["content"]``) and attribute access (``resp.message.content`` /
``resp.message.tool_calls`` for native tool-calling), so call sites are unchanged.
``num_ctx`` has no analogue in the OpenAI protocol and is accepted-but-ignored;
``num_predict`` maps to ``max_tokens``; ``temperature`` is passed through.
"""

from __future__ import annotations

from typing import Any, Iterable

from . import config as C


# --- ollama-compatible response shapes (dict + attribute access) -------------
class _AttrDict(dict):
    """A dict that also supports attribute access, so a single response object
    satisfies both ``resp["message"]`` and ``resp.message`` call sites."""

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError as exc:                       # pragma: no cover - defensive
            raise AttributeError(name) from exc

    def model_dump(self) -> dict:
        return _plain(self)


def _plain(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _plain(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_plain(v) for v in obj]
    return obj


# =============================================================================
# OpenAI-compatible provider (the only generation path)
# =============================================================================
class _OpenAIProvider:
    def __init__(self) -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError(
                "The generation backend requires the `openai` package "
                "(`pip install openai`)."
            ) from exc
        self._client = OpenAI(
            base_url=C.OPENAI_BASE_URL or None,
            api_key=C.OPENAI_API_KEY or "not-needed",
            # Generous ceiling so long agent/synthesis generations never trip the
            # SDK's default per-request timeout.
            timeout=C.AGENT_TIMEOUT,
        )

    def chat(self, messages, *, model=None, tools=None, stream=False,
             num_ctx=None, temperature=0.2, num_predict=None, timeout=None):
        # num_ctx has no analogue in the OpenAI chat protocol → accepted, ignored.
        kwargs: dict[str, Any] = dict(
            model=model or C.GEN_MODEL,
            messages=_to_openai_messages(messages),
            temperature=temperature,
            stream=stream,
        )
        if num_predict is not None:
            kwargs["max_tokens"] = num_predict
        if tools is not None:
            kwargs["tools"] = tools                   # already an OpenAI tool schema
        resp = self._client.chat.completions.create(**kwargs)
        if stream:
            return _openai_stream(resp)
        return _openai_to_ollama(resp)


def _to_openai_messages(messages: Iterable[dict]) -> list[dict]:
    """Translate the pipeline's ollama-style messages into OpenAI chat messages.

    system/user/assistant turns are identical across both protocols. Ollama tool
    results use role ``tool`` with a ``name`` field; OpenAI also wants a
    ``tool_call_id`` — we map best-effort so the agentic transcript keeps flowing."""
    out: list[dict] = []
    for m in messages:
        role = m.get("role")
        if role == "tool":
            out.append({"role": "tool", "content": m.get("content", ""),
                        "tool_call_id": m.get("tool_call_id") or m.get("name") or "tool",
                        "name": m.get("name", "tool")})
        else:
            msg: dict[str, Any] = {"role": role, "content": m.get("content", "")}
            if m.get("tool_calls"):
                msg["tool_calls"] = m["tool_calls"]
            out.append(msg)
    return out


def _openai_to_ollama(resp) -> _AttrDict:
    """Wrap a non-streaming OpenAI completion as an ollama-style response object."""
    choice = resp.choices[0]
    omsg = choice.message
    tool_calls = []
    for tc in (getattr(omsg, "tool_calls", None) or []):
        tool_calls.append(_AttrDict({
            "function": _AttrDict({
                "name": tc.function.name,
                "arguments": tc.function.arguments,   # JSON string; _coerce_args handles it
            }),
        }))
    message = _AttrDict({"role": "assistant", "content": omsg.content or ""})
    if tool_calls:
        message["tool_calls"] = tool_calls
    return _AttrDict({"message": message})


def _openai_stream(resp):
    """Adapt an OpenAI streaming completion into ollama-style chunk dicts
    (so ``part["message"]["content"]`` keeps working)."""
    for chunk in resp:
        if not chunk.choices:
            continue
        piece = getattr(chunk.choices[0].delta, "content", None) or ""
        yield _AttrDict({"message": _AttrDict({"content": piece})})


# =============================================================================
# Module-level facade
# =============================================================================
_provider: _OpenAIProvider | None = None


def get_provider() -> _OpenAIProvider:
    """Cached, lazily-constructed OpenAI-compatible generation provider."""
    global _provider
    if _provider is None:
        _provider = _OpenAIProvider()
    return _provider


def chat(messages, *, model=None, tools=None, stream=False, num_ctx=None,
         temperature=0.2, num_predict=None, timeout=None):
    """Chat completion on the generation endpoint. Returns an ollama-style
    response (non-stream) or an iterator of ollama-style chunks (stream=True)."""
    return get_provider().chat(
        messages, model=model, tools=tools, stream=stream, num_ctx=num_ctx,
        temperature=temperature, num_predict=num_predict, timeout=timeout,
    )
