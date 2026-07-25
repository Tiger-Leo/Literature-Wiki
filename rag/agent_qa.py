"""Agentic QA mode — no embeddings, no RAG retriever.

This path drives the local model (qwen3.6:35b-mlx via Ollama) with a tiny set of
sandboxed wiki-filesystem tools (``list_dir``, ``glob``, ``grep``, ``read_file``;
see :mod:`rag.agent_tools`). The model navigates the wiki the way the
``/wiki-query`` skill prescribes — entry ``_index.md`` → ``synthesis``/``concepts``
→ ``wiki/sources/<slug>.md`` → ``raw_markdown/papers/<slug>.md`` — gathers evidence
with tools, then writes ONE integrated encyclopedic answer with real ``[[slug]]``
citations.

Two tool protocols are implemented behind one protocol-agnostic loop:

* **native** — Ollama native tool-calling (``client.chat(..., tools=TOOL_SCHEMAS)``
  then read ``resp.message.tool_calls``).
* **react** — a text fallback: the model emits a fenced ```action {json}``` block
  with ``{"tool": ..., "args": {...}}``, which we parse and execute.

``config.AGENT_TOOL_BACKEND`` selects: ``auto`` (try native; fall back to react if
the first turn yields no tool_calls), ``native``, or ``react``.

Public API:
* ``agent_stream(query) -> Iterator[dict]`` — streaming events matching the
  server NDJSON shape (``status`` / ``sources`` / ``delta`` / ``done``).
* ``agent_answer(query) -> dict`` — blocking helper for tests.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterator
from functools import partial

from . import config as C
from . import agent_tools as T
from . import llm

_WIKILINK = re.compile(r"\[\[([^\]]+)\]\]")


def _slug_of(target: str) -> str:
    return target.split("|", 1)[0].split("#", 1)[0].strip()


def _delink_unknown(stream: Iterator[str], known: set[str]) -> Iterator[str]:
    """Stream-safe filter: turn any [[slug]] whose slug is NOT in the corpus into plain
    text (drop the brackets), so an occasionally-invented citation never reaches the user
    as a broken wikilink. Holds back only from an unclosed '[[' so streaming continues."""
    def fix(text: str) -> str:
        return _WIKILINK.sub(
            lambda m: m.group(0) if _slug_of(m.group(1)) in known else _slug_of(m.group(1)),
            text)
    buf = ""
    for piece in stream:
        buf += piece
        open_at = buf.rfind("[[")
        if open_at == -1 or "]]" in buf[open_at:]:
            yield fix(buf); buf = ""
        else:                                    # hold back the unclosed '[[...'
            yield fix(buf[:open_at]); buf = buf[open_at:]
    if buf:
        yield fix(buf)

# Dedicated chat calls use a generous, agent-only timeout: the agent's final-answer
# generation can run well past the shared client timeout. Streaming calls only need a
# gap-between-chunks < timeout, but the non-streaming tool-decision turns and any inline
# fallback also benefit from the headroom. The llm.chat facade picks a client (Ollama)
# or endpoint (OpenAI) honouring this timeout; the OpenAI provider ignores think/num_ctx.
_chat = partial(llm.chat, timeout=C.AGENT_TIMEOUT)

# --- Tool schemas (native Ollama tool-calling) -------------------------------
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "list_dir",
            "description": ("List the entries of a directory in the wiki "
                            "(directories marked with a trailing '/'). "
                            "Use this to discover what _index.md and subdirectories exist."),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string",
                             "description": "repo-relative dir, e.g. 'wiki/concepts' (default '.')"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "glob",
            "description": ("Find files by glob pattern, e.g. 'wiki/concepts/*.md' or "
                            "'raw_markdown/papers/*hart*'. Returns matching paths."),
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string",
                                "description": "glob pattern relative to the repo root"},
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "grep",
            "description": ("Regex-search files for a term and return path:line: text hits "
                            "with context. Use to locate where a concept/paper is discussed."),
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "regex to search for"},
                    "path_glob": {"type": "string",
                                  "description": "files to search (default 'wiki/**/*.md'); "
                                                 "use 'raw_markdown/papers/*.md' for paper text"},
                    "max_results": {"type": "integer",
                                    "description": f"max hits (default {C.AGENT_GREP_MAX})"},
                    "context": {"type": "integer", "description": "context lines (default 1)"},
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": ("Read a window of a markdown file. Returns numbered lines and the "
                            "total line count so you can page large raw papers with offset."),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "repo-relative file path"},
                    "offset": {"type": "integer", "description": "0-based start line (default 0)"},
                    "limit": {"type": "integer",
                              "description": f"lines to read (default {C.AGENT_READ_LIMIT})"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_answer",
            "description": ("Call this (with NO arguments) once you have read enough "
                            "sources and are ready to write the final answer. Do NOT write "
                            "any prose in the same turn — after you call it you will be "
                            "asked to write the full answer, which then streams to the user."),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]

# --- System prompt (encodes the /wiki-query methodology) ---------------------
_TOOL_LIST = (
    "- list_dir(path='.') — list a directory's entries.\n"
    "- glob(pattern) — find files, e.g. glob('raw_markdown/papers/*hart*').\n"
    "- grep(pattern, path_glob='wiki/**/*.md', max_results=40, context=1) — regex search.\n"
    "- read_file(path, offset=0, limit=400) — read a numbered line window of a file."
)

SYSTEM_PROMPT = f"""\
You are the agentic answer engine for {C.DOMAIN_DESC}. You answer literature \
questions by NAVIGATING the wiki's files with tools — there is no pre-built search \
index. Gather evidence with the tools first, THEN write one integrated encyclopedic \
answer.

TOOLS (call them to read the wiki; never invent file contents):
{_TOOL_LIST}

NAVIGATION (the canonical /wiki-query read order — follow it, stop at the first \
layer that fully answers):
1. Start at the entry navigation: read CLAUDE.md and _index.md, then the relevant \
subdirectory index, e.g. read_file('wiki/concepts/_index.md').
2. Read the relevant Wikipedia-style synthesis pages — wiki/synthesis/*, \
wiki/concepts/*, wiki/mechanisms/*, wiki/debates/*, wiki/methods/*, wiki/measures/* \
— these are the PRIMARY answer layer, especially for cross-paper questions. Use \
grep to locate the right page (e.g. grep('hold-up', 'wiki/**/*.md')).
3. Read wiki/sources/<slug>.md only when a specific paper's detail is needed — \
treat source pages as navigation aids, not authority.
4. Read raw_markdown/papers/<slug>.md for exact propositions, model setup, numbers, \
or quotes. This is the AUTHORITATIVE text for any paper claim — drill here when the \
question asks for a formal proposition, a specific number, or when a synthesis \
claim is borderline. Page large papers with offset.

STOP SIGNAL: once you have read enough sources to write a complete, well-cited \
answer, call the `write_answer` tool with NO arguments and nothing else — do NOT \
write the answer in that turn. You will then be prompted to write the full answer, \
which streams live to the user. Begin that answer DIRECTLY with its first heading or \
sentence — do NOT preface it with meta-commentary (e.g. "Now I have enough \
evidence", "Let me write the answer") and do NOT open with a "---" separator.

ANSWER FORMAT — write ONE integrated encyclopedic article (not a per-file list), \
British spelling, precise and concise. Distinguish the three knowledge levels with \
these exact inline markers, using each at least once where the evidence supports it:
- "*Paper claim* —" for what a specific paper asserts (with its citation).
- "*Cross-paper pattern* —" for what several papers jointly suggest.
- A "> [!note] Current assessment" blockquote for the best current judgement, \
including what remains uncertain. Acknowledge gaps where the wiki is thin.

CITATION RULE (binding): cite with Obsidian wikilinks [[slug]] where <slug> is the \
basename (without .md) of a file you ACTUALLY READ — e.g. after reading \
raw_markdown/papers/hart-and-moore-1990.md cite [[hart-and-moore-1990]]; after \
reading wiki/concepts/hold-up.md cite [[hold-up]]. NEVER invent a slug or cite a \
file you did not open. Every substantive claim should carry at least one [[slug]] \
citation. For cross-paper questions cite multiple sources.
"""

_USER_TEMPLATE = (
    "Question: {query}\n\n"
    "Navigate the wiki with the tools to gather evidence, then write the integrated "
    "answer following the citation and knowledge-level rules."
)

# Fenced ReAct action block: ```action\n{json}\n``` (language tag optional/loose).
_ACTION_RE = re.compile(
    r"```(?:action|json|tool)?\s*\n?(\{.*?\})\s*\n?```", re.DOTALL | re.IGNORECASE
)


# --- Corpus slug set (for citation validation) -------------------------------
def corpus_slugs() -> set[str]:
    """Real slug set: basenames (minus .md) of every wiki/**/*.md page plus
    every raw_markdown/papers/*.md paper. Used to de-link invented citations."""
    slugs: set[str] = set()
    for p in C.WIKI_DIR.rglob("*.md"):
        slugs.add(p.stem)
    for p in C.RAW_DIR.glob("*.md"):
        slugs.add(p.stem)
    return slugs


# --- Status formatting -------------------------------------------------------
_ICON = {"list_dir": "📂", "glob": "🔎", "grep": "🔎", "read_file": "📄"}


def _status_text(name: str, args: dict) -> str:
    a = args or {}
    if name == "read_file":
        path = a.get("path", "?")
        off = a.get("offset") or 0
        if off:
            lim = a.get("limit") or C.AGENT_READ_LIMIT
            return f"📄 read {path} (lines {off + 1}-{off + lim})"
        return f"📄 read {path}"
    if name == "grep":
        return f"🔎 grep {a.get('pattern', '?')!r} in {a.get('path_glob', 'wiki/**/*.md')}"
    if name == "glob":
        return f"🔎 glob {a.get('pattern', '?')}"
    if name == "list_dir":
        return f"📂 list {a.get('path', '.')}"
    return f"{_ICON.get(name, '•')} {name} {a}"


def _call_key(name: str, args: dict) -> str:
    """Stable key for a (tool, args) invocation, used to detect repeated calls.
    Args are JSON-serialised with sorted keys so equivalent dicts collapse."""
    try:
        a = json.dumps(args or {}, sort_keys=True, ensure_ascii=False)
    except (TypeError, ValueError):
        a = str(args)
    return f"{name}:{a}"


# When the SAME (tool, args) call is issued this many times, we stop executing it
# and feed back a nudge instead — so a stuck model can't burn the step budget.
_REPEAT_LIMIT = 3
_REPEAT_NUDGE = (
    "You already ran this exact call; its result is earlier in this transcript. "
    "Use a DIFFERENT tool/args, or stop and write the final answer now."
)


def _guarded_call(name: str, args: dict, call_counts: dict[str, int]) -> tuple[str, bool]:
    """Increment the repeat counter for this (tool, args) call and either run the
    tool or, once it has been seen ``_REPEAT_LIMIT`` times, skip execution and
    return the nudge observation. Returns ``(observation, skipped)``."""
    key = _call_key(name, args)
    call_counts[key] = call_counts.get(key, 0) + 1
    if call_counts[key] >= _REPEAT_LIMIT:
        return _REPEAT_NUDGE, True
    return T.call_tool(name, args), False


def _coerce_args(raw) -> dict:
    """Native tool-call args may arrive as a dict or a JSON string."""
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except (ValueError, TypeError):
            return {}
    return dict(raw) if raw else {}


def _parse_react(text: str):
    """Parse a fenced ```action {json}``` block. Returns (tool, args) or None."""
    if not text:
        return None
    m = _ACTION_RE.search(text)
    if not m:
        return None
    try:
        obj = json.loads(m.group(1))
    except (ValueError, TypeError):
        return None
    tool = obj.get("tool") or obj.get("name") or obj.get("action")
    args = obj.get("args") or obj.get("arguments") or obj.get("parameters") or {}
    if not tool:
        return None
    return (str(tool), _coerce_args(args))


def _react_system() -> str:
    """System prompt for the ReAct text protocol — adds the action-block contract."""
    return SYSTEM_PROMPT + (
        "\n\nTOOL-CALL PROTOCOL (IMPORTANT): you have no function-calling channel. To "
        "call a tool, emit EXACTLY ONE fenced block and nothing else:\n"
        "```action\n"
        '{\"tool\": \"read_file\", \"args\": {\"path\": \"wiki/concepts/_index.md\"}}\n'
        "```\n"
        "Wait for the observation (returned to you as the next user message), then "
        "decide your next step. When you have gathered enough evidence, emit the action "
        '```action\n{\"tool\": \"write_answer\", \"args\": {}}\n``` (and nothing else); '
        "you will then be asked to write the final prose answer with [[slug]] citations."
    )


# --- The agent loop ----------------------------------------------------------
def _run_loop(query: str) -> Iterator[dict]:
    """Internal generator yielding raw events; the public ``agent_stream`` wraps the
    final answer in the slug-validation filter. Events:
      {"type":"status",...} per tool call,
      {"type":"sources",...} once before the final answer,
      {"type":"_final_delta","text":...} for the final answer tokens (raw),
      {"type":"_meta", ...} loop metadata (backend_used, steps),
      {"type":"done"}.
    """
    # ---- empty/whitespace query guard: no model call ----------------------
    if not query or not query.strip():
        yield {"type": "_final_delta",
               "text": "Please ask a question about the literature."}
        yield {"type": "_meta", "backend_used": "none", "steps": 0, "sources": []}
        yield {"type": "done"}
        return

    backend = C.AGENT_TOOL_BACKEND
    use_native = backend in ("auto", "native")
    react_only = backend == "react"

    sys_prompt = _react_system() if react_only else SYSTEM_PROMPT
    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": _USER_TEMPLATE.format(query=query)},
    ]

    read_paths: list[str] = []          # files actually opened, in order, deduped
    seen_paths: set[str] = set()
    backend_used = "react" if react_only else ("native" if use_native else "react")
    steps = 0
    first_turn = True
    call_counts: dict[str, int] = {}    # (tool, json-args) → count, for repeat guard

    while steps < C.AGENT_MAX_STEPS:
        # ---- model turn ----------------------------------------------------
        if use_native and not react_only:
            try:
                resp = _chat(
                    messages, model=C.GEN_MODEL, tools=TOOL_SCHEMAS,
                    temperature=0.2, num_ctx=C.AGENT_NUM_CTX,
                    num_predict=C.AGENT_DECIDE_MAX_TOKENS,
                )
            except Exception as exc:                 # native unsupported → fall back
                if backend == "native":
                    yield {"type": "status", "text": f"⚠ native tool-calling failed: {exc}",
                           "label": "native tool-calling failed"}
                use_native = False
                react_only = backend != "native"
                messages[0]["content"] = _react_system()
                backend_used = "react"
                continue
            msg = resp.message
            content = (msg.content or "") if msg else ""
            tool_calls = list(getattr(msg, "tool_calls", None) or [])

            if tool_calls:
                backend_used = "native"
                first_turn = False
                # append the assistant turn (with its tool calls) to the transcript
                messages.append({"role": "assistant", "content": content,
                                 "tool_calls": [tc.model_dump() if hasattr(tc, "model_dump")
                                                else tc for tc in tool_calls]})
                ready = False
                for tc in tool_calls:
                    fn = tc.function
                    name = fn.name
                    args = _coerce_args(fn.arguments)
                    if name == "write_answer":
                        # sentinel: model is ready to answer. Honour it only after it has
                        # actually read something; otherwise nudge it to gather evidence.
                        if read_paths:
                            ready = True
                            messages.append({"role": "tool", "name": name,
                                             "content": "Acknowledged — now write the full final answer."})
                        else:
                            messages.append({"role": "tool", "name": name, "content": (
                                "You have not read any sources yet. Use read_file/grep to "
                                "gather evidence FIRST, then call write_answer.")})
                        continue
                    steps += 1
                    obs, skipped = _guarded_call(name, args, call_counts)
                    label = _status_text(name, args)
                    prefix = f"[{steps}] " + ("⤴ " if skipped else "")
                    yield {"type": "status", "text": prefix + label, "label": label}
                    if not skipped and name == "read_file" and not obs.startswith("ERROR"):
                        _record_read(args.get("path"), read_paths, seen_paths)
                    messages.append({"role": "tool", "name": name, "content": obs})
                if ready:
                    # stream the final answer LIVE (single generation, no tools)
                    yield {"type": "status", "text": "✍ Research done — generating the answer…",
                           "label": "generating the answer…"}
                    yield from _emit_sources(read_paths)
                    for piece in _stream_final(messages):
                        yield {"type": "_final_delta", "text": piece}
                    yield {"type": "_meta", "backend_used": backend_used, "steps": steps,
                           "sources": _sources_list(read_paths)}
                    yield {"type": "done"}
                    return
                continue

            # no tool calls on first auto turn → fall back to react
            if first_turn and backend == "auto":
                use_native = False
                react_only = True
                backend_used = "react"
                messages[0]["content"] = _react_system()
                # restart this turn under react protocol (don't consume the empty turn)
                first_turn = False
                continue

            # native, model wants to answer (no tool call). Its inline content is capped
            # by num_predict, so DISCARD it and stream the full answer via _stream_final.
            yield {"type": "status", "text": "✍ Research done — generating the answer…",
                   "label": "generating the answer…"}
            yield from _emit_sources(read_paths)
            for piece in _stream_final(messages):
                yield {"type": "_final_delta", "text": piece}
            yield {"type": "_meta", "backend_used": backend_used, "steps": steps,
                   "sources": _sources_list(read_paths)}
            yield {"type": "done"}
            return

        # ---- react text protocol ------------------------------------------
        text = ""
        for part in _chat(
            messages, model=C.GEN_MODEL, stream=True,
            temperature=0.2, num_ctx=C.AGENT_NUM_CTX,
            num_predict=C.AGENT_DECIDE_MAX_TOKENS,
        ):
            text += part.get("message", {}).get("content", "") or ""
        first_turn = False

        parsed = _parse_react(text)
        if parsed is None:
            # no action block → the model is answering (its inline text is num_predict-
            # capped, so discard it and stream the full answer via _stream_final).
            yield {"type": "status", "text": "✍ Research done — generating the answer…",
                   "label": "generating the answer…"}
            yield from _emit_sources(read_paths)
            for piece in _stream_final(messages):
                yield {"type": "_final_delta", "text": piece}
            yield {"type": "_meta", "backend_used": "react", "steps": steps,
                   "sources": _sources_list(read_paths)}
            yield {"type": "done"}
            return

        name, args = parsed
        if name == "write_answer":
            messages.append({"role": "assistant", "content": text})
            if read_paths:
                yield {"type": "status", "text": "✍ Research done — generating the answer…",
                       "label": "generating the answer…"}
                yield from _emit_sources(read_paths)
                for piece in _stream_final(messages):
                    yield {"type": "_final_delta", "text": piece}
                yield {"type": "_meta", "backend_used": "react", "steps": steps,
                       "sources": _sources_list(read_paths)}
                yield {"type": "done"}
                return
            messages.append({"role": "user", "content": (
                "You have not read any sources yet. Use read_file/grep to gather evidence "
                "FIRST, then emit the write_answer action.")})
            continue
        steps += 1
        obs, skipped = _guarded_call(name, args, call_counts)
        label = _status_text(name, args)
        prefix = f"[{steps}] " + ("⤴ " if skipped else "")
        yield {"type": "status", "text": prefix + label, "label": label}
        if not skipped and name == "read_file" and not obs.startswith("ERROR"):
            _record_read(args.get("path"), read_paths, seen_paths)
        messages.append({"role": "assistant", "content": text})
        messages.append({"role": "user", "content": f"Observation:\n{obs}"})

    # ---- step cap reached: force a final answer ---------------------------
    yield {"type": "status", "text": "⏱ step cap reached — writing answer from evidence",
           "label": "step cap reached"}
    messages.append({"role": "user", "content": (
        "Step budget exhausted. Stop calling tools now and write the final integrated "
        "answer from the evidence you have gathered, with [[slug]] citations.")})
    yield from _emit_sources(read_paths)
    final = ""
    for part in _chat(
        messages, model=C.GEN_MODEL, stream=True,
        temperature=0.2, num_ctx=C.AGENT_NUM_CTX,
    ):
        piece = part.get("message", {}).get("content", "") or ""
        if piece:
            final += piece
            yield {"type": "_final_delta", "text": piece}
    yield {"type": "_meta", "backend_used": backend_used, "steps": steps,
           "sources": _sources_list(read_paths)}
    yield {"type": "done"}


def _record_read(path, read_paths: list[str], seen: set[str]) -> None:
    if not path:
        return
    p = str(path)
    if p not in seen:
        seen.add(p)
        read_paths.append(p)


def _sources_list(read_paths: list[str]) -> list[dict]:
    out = []
    for p in read_paths:
        if T.path_to_slug(p) in ("_index", "CLAUDE"):   # navigation files: not sources
            continue
        layer, tier = T.classify_layer(p)
        out.append({"slug": T.path_to_slug(p), "path": p, "layer": layer, "tier": tier})
    return out


def _emit_sources(read_paths: list[str]) -> Iterator[dict]:
    yield {"type": "sources", "sources": _sources_list(read_paths)}


def _restream_final(messages: list[dict], already: str) -> Iterator[str]:
    """For native backend: re-ask the model (no tools) to stream the final answer
    token-by-token. If the non-streaming turn already produced content, just chunk it."""
    if already and already.strip():
        yield from _chunk_text(_strip_preamble(already))
        return
    msgs = messages + [{"role": "user", "content": (
        "Now write the final integrated answer from the evidence, with [[slug]] "
        "citations and the three knowledge-level markers.")}]
    for part in _chat(
        msgs, model=C.GEN_MODEL, stream=True,
        temperature=0.2, num_ctx=C.AGENT_NUM_CTX,
    ):
        piece = part.get("message", {}).get("content", "") or ""
        if piece:
            yield piece


def _chunk_text(text: str, size: int = 24) -> Iterator[str]:
    """Yield text in small word-ish chunks so a pre-computed answer still streams."""
    for i in range(0, len(text), size):
        yield text[i:i + size]


def _chat_content_stream(msgs: list[dict]) -> Iterator[str]:
    """Stream just the assistant content of a tool-free chat call, piece by piece."""
    for part in _chat(
        msgs, model=C.GEN_MODEL, stream=True,
        temperature=0.2, num_ctx=C.AGENT_NUM_CTX,
    ):
        piece = part.get("message", {}).get("content", "") or ""
        if piece:
            yield piece


def _strip_preamble_stream(gen: Iterator[str], head: int = 180) -> Iterator[str]:
    """Buffer only the first ~head chars to strip a leading meta line / '---' separator,
    then pass the remainder through LIVE. Adds negligible latency (just the head)."""
    buf = ""
    started = False
    for piece in gen:
        if started:
            yield piece
            continue
        buf += piece
        if len(buf) >= head:
            cleaned = _strip_preamble(buf)
            if cleaned:
                yield cleaned
            buf = ""
            started = True
    if not started and buf:
        cleaned = _strip_preamble(buf)
        if cleaned:
            yield cleaned


def _stream_final(messages: list[dict]) -> Iterator[str]:
    """Stream the final answer LIVE (single generation, no tools), token-by-token, with a
    streaming-safe leading-preamble strip. Called after the model signals readiness via
    the write_answer sentinel — so the deciding turn stays short and the answer streams."""
    msgs = messages + [{"role": "user", "content": (
        "Write the final integrated encyclopedic answer now, as plain prose — do not call "
        "any tools. Follow the citation rule and use the three knowledge-level markers. "
        "Begin directly with the answer (a heading or first sentence); no preamble, no "
        "'---' separator.")}]
    yield from _strip_preamble_stream(_chat_content_stream(msgs))


# Leading meta-commentary the model sometimes emits before the real answer, e.g.
# "Now I have enough evidence. Let me write the integrated answer." followed by "---".
_META_LINE_RE = re.compile(
    r"^\s*[^\n]{0,200}?\b(?:let me write|i(?:'ll| will)(?: now)? write|now i have|"
    r"i now have|enough evidence|sufficient evidence|gathered (?:enough|sufficient)|"
    r"here(?:'s| is) (?:the|my)(?: integrated| final)? answer|"
    r"based on (?:the|my) (?:evidence|sources|reading)|"
    r"write the(?: integrated| final)? answer)\b[^\n]*\n+",
    re.IGNORECASE,
)


def _strip_preamble(text: str) -> str:
    """Drop a leading meta sentence ('Now I have enough evidence. Let me write…')
    and any leading '---' separator, so the answer starts at its real content.
    Conservative: only strips a first line that clearly reads as meta-commentary."""
    t = text.lstrip()
    m = _META_LINE_RE.match(t)
    if m:
        t = t[m.end():].lstrip()
    t = re.sub(r"^-{3,}[ \t]*\n+", "", t).lstrip()
    return t or text


# --- Public API --------------------------------------------------------------
def agent_stream(query: str) -> Iterator[dict]:
    """Stream agentic-QA events LIVE. Yields:
      {"type":"status","text":...}     — one per tool call (human-readable),
      {"type":"sources","sources":[{slug,path,layer,tier}...]} — files actually read,
      {"type":"delta","text":...}      — final-answer tokens, streamed token-by-token,
      {"type":"meta","backend_used":...,"steps":...} — for the CLI (UI ignores it),
      {"type":"done"}.
    The final answer is piped through the corpus slug-validation filter AS IT STREAMS
    (the filter only holds back an unclosed '[[' ), so a wrong/invented [[slug]] is
    de-linked without buffering the whole answer — the user sees tokens as they arrive."""
    # Emit an immediate status so the NDJSON stream produces a byte before the
    # first (potentially slow, cold-model) tool-decision inference. Without this
    # the browser sees a long silent stream and reports "could not reach the server".
    yield {"type": "status", "text": "🧭 Starting agentic search…", "label": "Starting agentic search…"}
    known = corpus_slugs()
    gen = _run_loop(query)
    trailing: list[dict] = []

    # Phase 1 — forward status/sources until the first final-answer token arrives.
    first_final: str | None = None
    for ev in gen:
        t = ev["type"]
        if t == "status":
            yield {"type": "status", "text": ev.get("text", ""), "label": ev.get("label", "")}
        elif t == "sources":
            yield ev
        elif t == "_final_delta":
            first_final = ev["text"]
            break
        elif t in ("_meta", "meta"):
            trailing.append(ev)
        elif t == "done":
            yield {"type": "done"}
            return

    # Phase 2 — stream the final answer live through the slug-validation filter.
    if first_final is not None:
        def _src() -> Iterator[str]:
            yield first_final
            for ev in gen:
                t = ev["type"]
                if t == "_final_delta":
                    yield ev["text"]
                else:
                    trailing.append(ev)
                    if t == "done":
                        return
        for piece in _delink_unknown(_src(), known):
            if piece:
                yield {"type": "delta", "text": piece}

    # Phase 3 — passthrough lightweight meta (backend_used/steps) then done. The
    # frontend NDJSON parser ignores unknown event types (default branch).
    for ev in trailing:
        if ev["type"] in ("_meta", "meta"):
            yield {"type": "meta", "backend_used": ev.get("backend_used"),
                   "steps": ev.get("steps")}
            break
    yield {"type": "done"}


def agent_answer(query: str) -> dict:
    """Blocking helper for tests. Returns
    {"answer", "steps", "sources", "backend_used"}."""
    known = corpus_slugs()
    pending_final: list[str] = []
    sources: list[dict] = []
    backend_used = C.AGENT_TOOL_BACKEND
    steps = 0
    for ev in _run_loop(query):
        et = ev["type"]
        if et == "sources":
            sources = ev["sources"]
        elif et == "_final_delta":
            pending_final.append(ev["text"])
        elif et == "_meta":
            backend_used = ev.get("backend_used", backend_used)
            steps = ev.get("steps", steps)
            if ev.get("sources"):
                sources = ev["sources"]
    answer = "".join(_delink_unknown(iter(pending_final), known))
    return {"answer": answer, "steps": steps, "sources": sources,
            "backend_used": backend_used}
