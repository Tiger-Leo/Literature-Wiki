"""Agentic QA CLI: navigate the wiki with filesystem tools, stream a cited answer.

    python -m rag.query "what is the hold-up problem?"
    python -m rag.query "compare authority in Coase vs GHM"

There is no RAG/embedding path — the backend answers ONLY by agentic filesystem
navigation (list_dir/glob/grep/read_file over wiki/ + raw_markdown/). Status events
stream to stderr; the answer streams to stdout.
"""

from __future__ import annotations

import argparse
import sys


def _run_agentic(query: str) -> int:
    """Stream status events to stderr, answer deltas to stdout."""
    from .agent_qa import agent_stream

    backend_used = None
    steps = None
    for ev in agent_stream(query):
        et = ev.get("type")
        if et == "status":
            sys.stderr.write((ev.get("text") or ev.get("label") or "") + "\n")
            sys.stderr.flush()
        elif et == "sources":
            srcs = ", ".join(s["slug"] for s in ev.get("sources", []))
            sys.stderr.write(f"[sources: {srcs or '(none yet)'}]\n")
            sys.stderr.flush()
        elif et == "meta":
            backend_used = ev.get("backend_used")
            steps = ev.get("steps")
        elif et == "delta":
            sys.stdout.write(ev.get("text", ""))
            sys.stdout.flush()
        elif et == "done":
            sys.stdout.write("\n")
            sys.stdout.flush()
    if backend_used is not None:
        sys.stderr.write(f"[agentic: backend={backend_used} steps={steps}]\n")
        sys.stderr.flush()
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("query")
    args = ap.parse_args()
    return _run_agentic(args.query)


if __name__ == "__main__":
    raise SystemExit(main())
