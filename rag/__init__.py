"""Agentic-search chat backend for the literature-wiki.

This backend answers literature questions ONLY by agentic filesystem navigation —
there is no embedding index, vector store, BM25, or graph index, and no index build.

Layers:
- agent_tools / agent_qa  — sandboxed wiki-filesystem tools + the agentic answer loop
- llm                     — provider-abstracted generation (ollama | openai)
- store / server          — FastAPI + SQLite thread/message persistence
- query                   — agentic QA CLI

Generation runs locally via Ollama by default, or any OpenAI-compatible endpoint.
See rag/config.py for knobs.
"""
