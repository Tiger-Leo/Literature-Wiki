"""FastAPI server: streaming agentic chat + thread/message persistence + export.

The Chat surface answers ONLY via agentic filesystem navigation (rag/agent_qa.py
drives the generation model with sandboxed list_dir/glob/grep/read_file tools over
wiki/ + raw_markdown/). There is no embedding index, vector store, or RAG retriever.

Run:  uvicorn rag.server:app --port 8000 --reload   (from the literature-wiki dir, sci env)

Endpoints (shaped for assistant-ui's adapters):
    POST   /api/chat                         streaming agentic answer (NDJSON)
    GET    /api/threads                      list threads
    POST   /api/threads                      create thread -> {id}
    GET    /api/threads/{id}                 fetch thread
    PATCH  /api/threads/{id}                 rename / archive
    DELETE /api/threads/{id}                 delete
    POST   /api/threads/{id}/title           generate a title from messages
    GET    /api/threads/{id}/messages        load message history
    POST   /api/threads/{id}/messages        append a message
    GET    /api/threads/{id}/export?format=  md | json
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, StreamingResponse
from starlette.concurrency import iterate_in_threadpool, run_in_threadpool

from . import config as C
from . import store
from .agent_tools import split_frontmatter


@asynccontextmanager
async def _lifespan(app: FastAPI):
    await store.init_db()
    yield


app = FastAPI(title="literature-wiki agentic chat", lifespan=_lifespan)
# CORS: comma-separated origins via RAG_CORS_ORIGINS. Default "*" for local dev;
# set e.g. RAG_CORS_ORIGINS=https://my-frontend.example before exposing the server.
_cors_origins = [o.strip() for o in C.CORS_ORIGINS.split(",") if o.strip()] or ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health() -> dict:
    return {"ok": True, "mode": "agentic", "gen_model": C.GEN_MODEL,
            "gen_endpoint": C.OPENAI_BASE_URL}


# --- message text extraction ----------------------------------------------
def _parts_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        out = []
        for p in content:
            if isinstance(p, dict):
                if p.get("type") in (None, "text") and p.get("text"):
                    out.append(p["text"])
            elif isinstance(p, str):
                out.append(p)
        return " ".join(out)
    if isinstance(content, dict) and content.get("text"):
        return str(content["text"])
    return ""


def _last_user_text(messages: list[dict]) -> str:
    for m in reversed(messages):
        if m.get("role") == "user":
            return _parts_to_text(m.get("content")).strip()
    # Fallback: only trust the last message if it is a user turn (or role unset);
    # never embed an assistant message as the query.
    if messages and messages[-1].get("role") in (None, "user"):
        return _parts_to_text(messages[-1].get("content")).strip()
    return ""


# --- chat ------------------------------------------------------------------
def _ndjson(obj: Any) -> str:
    """Serialise one event as a newline-terminated JSON object (UTF-8 preserved)."""
    return json.dumps(obj, ensure_ascii=False) + "\n"


def _agent_chat_events(query: str) -> Iterator[str]:
    """Sync generator of NDJSON chat events for the agentic QA path. Adapts
    rag.agent_qa.agent_stream (which yields status/sources/delta/done event dicts)
    into newline-terminated JSON lines for the frontend parser. Wrapped by
    iterate_in_threadpool so the blocking tool-loop never touches the event loop."""
    from .agent_qa import agent_stream
    for ev in agent_stream(query):
        yield _ndjson(ev)


@app.post("/api/chat")
async def chat(req: Request):
    """Answer a chat turn via agentic filesystem navigation (no embeddings/RAG).
    Always runs the agentic path; streams NDJSON status/sources/delta/done events."""
    body = await req.json()
    query = _last_user_text(body.get("messages", []))
    if not query:
        def _empty() -> Iterator[str]:
            yield _ndjson({"type": "status", "label": "Starting agentic search…"})
            yield _ndjson({"type": "sources", "sources": []})
            yield _ndjson({"type": "delta", "text": "(no question received)"})
            yield _ndjson({"type": "done"})
        return StreamingResponse(
            iterate_in_threadpool(_empty()),
            media_type="application/x-ndjson",
        )
    return StreamingResponse(
        iterate_in_threadpool(_agent_chat_events(query)),
        media_type="application/x-ndjson",
    )


# --- wiki page -------------------------------------------------------------
def _title_from(body: str, fm: dict, slug: str) -> str:
    if fm.get("title"):
        return str(fm["title"])
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return slug


@app.get("/api/page/{slug}")
async def page_get(slug: str):
    """Resolve a wikilink target to its markdown body (frontmatter stripped).

    Search order: wiki/{layer}/{slug}.md over C.TIER_A_DIRS, then
    raw_markdown/papers/{slug}.md. Missing -> found=false, HTTP 200."""
    # Defensive: accept path-style / .md / #anchor targets by reducing to the basename.
    slug = slug.split("#", 1)[0].strip().rsplit("/", 1)[-1]
    if slug.endswith(".md"):
        slug = slug[:-3]
    candidates = [(layer, C.WIKI_DIR / layer / f"{slug}.md") for layer in C.TIER_A_DIRS]
    candidates.append(("raw", C.RAW_DIR / f"{slug}.md"))
    for layer, path in candidates:
        if path.is_file():
            raw = path.read_text(encoding="utf-8", errors="replace")
            fm, body = split_frontmatter(raw)
            return {
                "slug": slug,
                "title": _title_from(body, fm, slug),
                "markdown": body,
                "found": True,
                "layer": layer,
            }
    return {"slug": slug, "title": slug, "markdown": "", "found": False, "layer": ""}


# --- threads ---------------------------------------------------------------
@app.get("/api/threads")
async def threads_list():
    return await store.list_threads()


@app.post("/api/threads")
async def threads_create(req: Request):
    body = await req.json() if await req.body() else {}
    return await store.create_thread(title=body.get("title"))


@app.get("/api/threads/{tid}")
async def threads_get(tid: str):
    t = await store.get_thread(tid)
    if not t:
        raise HTTPException(404, "thread not found")
    return t


@app.patch("/api/threads/{tid}")
async def threads_patch(tid: str, req: Request):
    body = await req.json()
    await store.update_thread(tid, title=body.get("title"), status=body.get("status"))
    return {"ok": True}


@app.delete("/api/threads/{tid}")
async def threads_delete(tid: str):
    await store.delete_thread(tid)
    return {"ok": True}


@app.post("/api/threads/{tid}/title")
async def threads_title(tid: str, req: Request):
    body = await req.json()
    first = _last_user_text(body.get("messages", []))
    title = await run_in_threadpool(_make_title, first)
    await store.update_thread(tid, title=title)
    return {"title": title}


def _make_title(text: str) -> str:
    text = text.strip()
    if not text:
        return "New chat"
    try:
        from . import llm
        resp = llm.chat(
            [{"role": "user", "content":
              f"Give a concise 3-6 word title (no quotes) for a chat that "
              f"begins: {text[:300]}"}],
            model=C.GEN_MODEL, temperature=0, num_predict=24, num_ctx=C.NUM_CTX,
        )
        title = resp["message"]["content"].strip().strip('"').splitlines()[0]
        return title[:80] or text[:60]
    except Exception:
        return text[:60]


# --- messages --------------------------------------------------------------
def _decode_stored_content(content: Any) -> Any:
    """Round-trip a stored message back to the original JSON value the frontend sent.
    Strings that are valid JSON are parsed; anything else is returned unchanged."""
    if isinstance(content, str):
        try:
            return json.loads(content)
        except (json.JSONDecodeError, ValueError):
            return content
    return content


@app.get("/api/threads/{tid}/messages")
async def messages_list(tid: str):
    rows = await store.list_messages(tid)
    return [{**r, "content": _decode_stored_content(r.get("content"))} for r in rows]


@app.post("/api/threads/{tid}/messages")
async def messages_append(tid: str, req: Request):
    m = await req.json()
    await store.append_message(
        tid, id=m.get("id") or store.new_id(), parent_id=m.get("parent_id"),
        role=m.get("role"), format=m.get("format"), content=_to_text(m.get("content")),
    )
    return {"ok": True}


def _to_text(content: Any) -> str:
    return content if isinstance(content, str) else json.dumps(content, ensure_ascii=False)


# --- export ----------------------------------------------------------------
@app.get("/api/threads/{tid}/export")
async def export(tid: str, format: str = "md"):
    thread = await store.get_thread(tid)
    if not thread:
        raise HTTPException(404, "thread not found")
    msgs = await store.list_messages(tid)

    if format == "json":
        return JSONResponse(
            {"thread": thread, "messages": msgs},
            headers={"Content-Disposition":
                     f'attachment; filename="{tid}.json"'},
        )

    lines = [f"# {thread.get('title') or 'Conversation'}", ""]
    for m in msgs:
        role = (m.get("role") or "message").capitalize()
        body = _decode_content(m.get("content"))
        lines.append(f"## {role}\n\n{body}\n")
    md = "\n".join(lines)
    return PlainTextResponse(
        md, media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{tid}.md"'},
    )


def _decode_content(content: Any) -> str:
    """Best-effort render of a stored (possibly JSON-encoded) message into text."""
    if not content:
        return ""
    if isinstance(content, str):
        try:
            parsed = json.loads(content)
        except (json.JSONDecodeError, TypeError):
            return content
    else:
        parsed = content
    text = _parts_to_text(parsed)
    if text:
        return text
    # walk nested structures for any 'text' fields
    found: list[str] = []

    def walk(o: Any) -> None:
        if isinstance(o, dict):
            if isinstance(o.get("text"), str):
                found.append(o["text"])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(parsed)
    return "\n".join(found) if found else json.dumps(parsed, ensure_ascii=False)


# --- optional direct runner -------------------------------------------------
# `uvicorn rag.server:app --port 8000` is the canonical command, but running this
# module directly honours RAG_PORT / RAG_HOST for convenience.
if __name__ == "__main__":
    import os

    import uvicorn

    uvicorn.run(
        "rag.server:app",
        host=os.environ.get("RAG_HOST", "127.0.0.1"),
        port=int(os.environ.get("RAG_PORT", "8000")),
    )
