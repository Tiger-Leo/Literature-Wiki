"""Async SQLite persistence for chat threads and messages.

Schemas mirror the shapes assistant-ui's RemoteThreadListAdapter and
ThreadHistoryAdapter expect, so the frontend adapters map onto these rows
directly. Messages store the adapter's encoded payload verbatim (id, parent_id,
format, content) so any assistant-ui message format round-trips losslessly.
"""

from __future__ import annotations

import time
import uuid
from typing import Any

import aiosqlite

from . import config as C

_SCHEMA = """
CREATE TABLE IF NOT EXISTS threads (
    id          TEXT PRIMARY KEY,
    title       TEXT,
    status      TEXT NOT NULL DEFAULT 'regular',
    created_at  REAL NOT NULL,
    updated_at  REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS messages (
    id          TEXT PRIMARY KEY,
    thread_id   TEXT NOT NULL,
    parent_id   TEXT,
    role        TEXT,
    format      TEXT,
    content     TEXT,
    created_at  REAL NOT NULL,
    seq         INTEGER,
    FOREIGN KEY (thread_id) REFERENCES threads(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_messages_thread ON messages(thread_id, seq);
"""


def _now() -> float:
    return time.time()


def new_id() -> str:
    return uuid.uuid4().hex


async def init_db() -> None:
    async with aiosqlite.connect(C.DB_PATH) as db:
        await db.executescript(_SCHEMA)
        await db.commit()


# --- threads ---------------------------------------------------------------
async def list_threads(include_archived: bool = True) -> list[dict[str, Any]]:
    q = "SELECT id, title, status FROM threads"
    if not include_archived:
        q += " WHERE status != 'archived'"
    q += " ORDER BY updated_at DESC"
    async with aiosqlite.connect(C.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        rows = await (await db.execute(q)).fetchall()
        return [dict(r) for r in rows]


async def create_thread(title: str | None = None) -> dict[str, Any]:
    tid, ts = new_id(), _now()
    async with aiosqlite.connect(C.DB_PATH) as db:
        await db.execute(
            "INSERT INTO threads (id, title, status, created_at, updated_at)"
            " VALUES (?, ?, 'regular', ?, ?)",
            (tid, title, ts, ts),
        )
        await db.commit()
    return {"id": tid, "title": title, "status": "regular"}


async def get_thread(tid: str) -> dict[str, Any] | None:
    async with aiosqlite.connect(C.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        row = await (await db.execute(
            "SELECT id, title, status FROM threads WHERE id = ?", (tid,)
        )).fetchone()
        return dict(row) if row else None


async def update_thread(tid: str, *, title: str | None = None,
                        status: str | None = None) -> None:
    sets, vals = [], []
    if title is not None:
        sets.append("title = ?"); vals.append(title)
    if status is not None:
        sets.append("status = ?"); vals.append(status)
    if not sets:
        return
    sets.append("updated_at = ?"); vals.append(_now())
    vals.append(tid)
    async with aiosqlite.connect(C.DB_PATH) as db:
        await db.execute(f"UPDATE threads SET {', '.join(sets)} WHERE id = ?", vals)
        await db.commit()


async def delete_thread(tid: str) -> None:
    async with aiosqlite.connect(C.DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        await db.execute("DELETE FROM messages WHERE thread_id = ?", (tid,))
        await db.execute("DELETE FROM threads WHERE id = ?", (tid,))
        await db.commit()


# --- messages --------------------------------------------------------------
async def list_messages(tid: str) -> list[dict[str, Any]]:
    async with aiosqlite.connect(C.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        rows = await (await db.execute(
            "SELECT id, parent_id, role, format, content FROM messages"
            " WHERE thread_id = ? ORDER BY seq ASC", (tid,)
        )).fetchall()
        return [dict(r) for r in rows]


async def append_message(tid: str, *, id: str, parent_id: str | None,
                         role: str | None, format: str | None,
                         content: str | None) -> None:
    ts = _now()
    async with aiosqlite.connect(C.DB_PATH) as db:
        # Compute seq inside the INSERT (single statement) so concurrent appends to the
        # same thread can't read the same MAX(seq) and collide. On an id collision
        # (edit / regenerate) UPDATE the editable fields but PRESERVE the original
        # created_at and seq so history order is not silently reshuffled.
        await db.execute(
            "INSERT INTO messages"
            " (id, thread_id, parent_id, role, format, content, created_at, seq)"
            " SELECT ?, ?, ?, ?, ?, ?, ?,"
            "        COALESCE(MAX(seq), 0) + 1 FROM messages WHERE thread_id = ?"
            " ON CONFLICT(id) DO UPDATE SET"
            "   parent_id = excluded.parent_id,"
            "   role      = excluded.role,"
            "   format    = excluded.format,"
            "   content   = excluded.content",
            (id, tid, parent_id, role, format, content, ts, tid),
        )
        await db.execute("UPDATE threads SET updated_at = ? WHERE id = ?", (ts, tid))
        await db.commit()
