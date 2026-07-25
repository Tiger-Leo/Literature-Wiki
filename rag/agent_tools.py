"""Sandboxed wiki-filesystem tools for the agentic QA loop.

The agentic QA mode (see ``agent_qa.py``) does NOT use embeddings/RAG. Instead it
drives a local model with a tiny set of filesystem tools that let it navigate the
wiki the way the ``/wiki-query`` skill prescribes (entry ``_index.md`` → synthesis
/ concepts → ``wiki/sources/<slug>.md`` → ``raw_markdown/papers/<slug>.md``).

Every tool resolves paths under :data:`config.REPO_ROOT` and is restricted to the
read-only navigable surface ``{wiki/, raw_markdown/, CLAUDE.md, _index.md}``. Any
attempt to escape the sandbox (``..`` traversal, absolute paths outside the repo,
symlink escapes) is rejected. Each tool returns a compact, human-readable string
that the model can read directly as an observation.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import yaml

from . import config as C


def split_frontmatter(text: str) -> tuple[dict, str]:
    """Split YAML frontmatter from a markdown body. Returns (frontmatter, body).

    Strips a leading UTF-8 BOM and any leading blank lines so files with a BOM or a
    leading newline still get their frontmatter parsed. Used by the server's /api/page
    resolver to render a wiki page without its frontmatter."""
    text = text.lstrip("﻿").lstrip("\r\n")
    if text.startswith("---"):
        m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.DOTALL)
        if m:
            try:
                fm = yaml.safe_load(m.group(1)) or {}
            except yaml.YAMLError:
                fm = {}
            if isinstance(fm, dict):
                return fm, m.group(2)
    return {}, text

# --- Sandbox -----------------------------------------------------------------
# The navigable surface. Directories are walked recursively; files are exact.
_ALLOWED_DIRS = ("wiki", "raw_markdown")
_ALLOWED_FILES = ("CLAUDE.md", "_index.md")

_HAVE_RG = shutil.which("rg") is not None


class SandboxError(ValueError):
    """Raised when a requested path escapes the read-only wiki sandbox."""


def _rel(path: str) -> str:
    """Normalise a user/model-supplied path to a repo-relative POSIX string."""
    return str(path).strip().lstrip("/").replace("\\", "/") or "."


def _is_allowed(rel: Path) -> bool:
    parts = rel.parts
    if not parts:                                   # repo root itself
        return True
    if len(parts) == 1 and parts[0] in _ALLOWED_FILES:
        return True
    return parts[0] in _ALLOWED_DIRS


def resolve(path: str) -> Path:
    """Resolve a repo-relative path inside the sandbox, or raise SandboxError.

    Rejects ``..`` traversal, absolute paths that fall outside the repo, and
    symlinks that point outside the allowed surface (via ``Path.resolve``)."""
    rel = _rel(path)
    candidate = (C.REPO_ROOT / rel).resolve()
    try:
        rel_to_root = candidate.relative_to(C.REPO_ROOT.resolve())
    except ValueError as exc:                       # escaped the repo entirely
        raise SandboxError(f"path escapes the wiki sandbox: {path!r}") from exc
    if rel_to_root == Path(".") or str(rel_to_root) == ".":
        return candidate
    if not _is_allowed(rel_to_root):
        raise SandboxError(
            f"path is outside the allowed wiki surface "
            f"({'/, '.join(_ALLOWED_DIRS)}/, {', '.join(_ALLOWED_FILES)}): {path!r}"
        )
    return candidate


def _disp(p: Path) -> str:
    """Repo-relative display path."""
    try:
        return str(p.resolve().relative_to(C.REPO_ROOT.resolve()))
    except ValueError:
        return str(p)


# --- Layer / slug helpers (used by the sources event) ------------------------
def path_to_slug(path: str | Path) -> str:
    """Map a markdown file path to its slug (basename minus ``.md``).

    ``raw_markdown/papers/hart-and-moore-1990.md`` -> ``hart-and-moore-1990``;
    ``wiki/concepts/hold-up.md`` -> ``hold-up``. Non-``.md`` paths return the stem."""
    return Path(str(path)).stem


def classify_layer(path: str | Path) -> tuple[str, str]:
    """Return ``(layer, tier)`` for a path.

    ``tier`` is ``"A"`` for curated wiki pages (``wiki/*``) and ``"B"`` for raw
    paper text (``raw_markdown/*``). ``layer`` is the human-readable category:
    the wiki subdirectory (``concepts``, ``synthesis``, ``sources``, …) for tier A,
    ``raw_paper`` for tier B, and ``root`` for top-level files."""
    rel = Path(_rel(str(path)))
    parts = rel.parts
    if not parts or str(rel) == ".":
        return ("root", "A")
    if parts[0] == "wiki":
        layer = parts[1] if len(parts) >= 2 and "." not in parts[1] else "wiki"
        return (layer, "A")
    if parts[0] == "raw_markdown":
        return ("raw_paper", "B")
    return ("root", "A")


# --- Tools -------------------------------------------------------------------
def list_dir(path: str = ".") -> str:
    """List the entries of a directory inside the sandbox.

    Directories are marked with a trailing ``/``. Returns a compact newline list."""
    try:
        target = resolve(path)
    except SandboxError as exc:
        return f"ERROR: {exc}"
    if not target.exists():
        return f"ERROR: no such path: {path!r}"
    if target.is_file():
        return f"{_disp(target)} (file, {target.stat().st_size} bytes)"
    entries = []
    for child in sorted(target.iterdir(), key=lambda c: (c.is_file(), c.name.lower())):
        # only surface entries that are themselves inside the allowed surface
        try:
            resolve(_disp(child))
        except SandboxError:
            continue
        if child.name.startswith(".") and child.name not in _ALLOWED_FILES:
            continue
        entries.append(child.name + ("/" if child.is_dir() else ""))
    if not entries:
        return f"{_disp(target)}/ (empty)"
    return f"{_disp(target)}/ ({len(entries)} entries):\n" + "\n".join(entries)


def glob(pattern: str) -> str:
    """Glob for files matching a repo-relative pattern, e.g. ``wiki/concepts/*.md``
    or ``raw_markdown/papers/*hart*``. Returns matching repo-relative paths."""
    pat = _rel(pattern)
    matches = []
    for p in sorted(C.REPO_ROOT.glob(pat)):
        try:
            resolve(_disp(p))
        except SandboxError:
            continue
        if p.is_file() or p.is_dir():
            matches.append(_disp(p) + ("/" if p.is_dir() else ""))
    if not matches:
        return f"(no matches for {pattern!r})"
    head = matches[:200]
    extra = "" if len(matches) <= 200 else f"\n… (+{len(matches) - 200} more)"
    return f"{len(matches)} match(es) for {pattern!r}:\n" + "\n".join(head) + extra


def grep(pattern: str, path_glob: str = "wiki/**/*.md",
         max_results: int | None = None, context: int = 1) -> str:
    """Regex search across files matching ``path_glob``.

    Returns ``path:line: text`` hits with ±``context`` lines. Prefers the ``rg``
    binary when available, else falls back to Python ``re``. Capped at
    ``max_results`` (default :data:`config.AGENT_GREP_MAX`)."""
    cap = C.AGENT_GREP_MAX if max_results is None else int(max_results)
    pg = _rel(path_glob)
    # Validate the glob root is in-sandbox (use the part before any wildcard).
    root_probe = pg.split("*", 1)[0].rstrip("/") or "."
    try:
        resolve(root_probe)
    except SandboxError as exc:
        return f"ERROR: {exc}"

    if _HAVE_RG:
        out = _grep_rg(pattern, pg, cap, context)
        if out is not None:
            return out
    return _grep_python(pattern, pg, cap, context)


def _grep_rg(pattern: str, pg: str, cap: int, context: int) -> str | None:
    """Run ripgrep over the glob; return formatted hits, or None on launch failure."""
    cmd = [
        "rg", "--no-heading", "--line-number", "--color", "never",
        "--max-count", str(max(cap, 1)),
        "-C", str(max(int(context), 0)),
        "--glob", pg, "-e", pattern,
        str(C.REPO_ROOT),
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode not in (0, 1):               # 1 == no matches (fine)
        return None
    lines = []
    root_prefix = str(C.REPO_ROOT.resolve()) + "/"
    for ln in proc.stdout.splitlines():
        lines.append(ln.replace(root_prefix, "").replace(str(C.REPO_ROOT) + "/", ""))
    # rg counts max per file; trim total hit lines to keep observation compact.
    if not lines:
        return f"(no matches for /{pattern}/ in {pg})"
    trimmed = lines[: cap * (2 * max(int(context), 0) + 2)]
    note = "" if len(lines) <= len(trimmed) else f"\n… (truncated; raise max_results to see more)"
    return f"grep /{pattern}/ in {pg} (rg):\n" + "\n".join(trimmed) + note


def _grep_python(pattern: str, pg: str, cap: int, context: int) -> str:
    """Pure-Python regex fallback when ``rg`` is unavailable."""
    try:
        rx = re.compile(pattern)
    except re.error as exc:
        return f"ERROR: invalid regex {pattern!r}: {exc}"
    ctx = max(int(context), 0)
    hits: list[str] = []
    n_files = 0
    for p in sorted(C.REPO_ROOT.glob(pg)):
        if not p.is_file():
            continue
        try:
            resolve(_disp(p))
        except SandboxError:
            continue
        n_files += 1
        try:
            text = p.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        disp = _disp(p)
        per_file = 0
        for i, line in enumerate(text):
            if rx.search(line):
                lo, hi = max(0, i - ctx), min(len(text), i + ctx + 1)
                for j in range(lo, hi):
                    marker = ":" if j == i else "-"
                    hits.append(f"{disp}:{j + 1}{marker} {text[j].rstrip()}")
                per_file += 1
                if per_file >= cap or len(hits) >= cap * (2 * ctx + 2):
                    break
        if len(hits) >= cap * (2 * ctx + 2):
            break
    if not hits:
        return f"(no matches for /{pattern}/ in {pg})"
    return f"grep /{pattern}/ in {pg} (python):\n" + "\n".join(hits)


def read_file(path: str, offset: int = 0, limit: int | None = None) -> str:
    """Read a window of a markdown file inside the sandbox.

    Reads ``limit`` lines (default :data:`config.AGENT_READ_LIMIT`) starting at
    ``offset`` (0-based). Reports total line count so the model can page large raw
    papers. Lines are prefixed with their 1-based line number."""
    lim = C.AGENT_READ_LIMIT if limit is None else int(limit)
    try:
        target = resolve(path)
    except SandboxError as exc:
        return f"ERROR: {exc}"
    if not target.exists():
        return f"ERROR: no such file: {path!r}"
    if target.is_dir():
        return f"ERROR: {path!r} is a directory; use list_dir."
    try:
        lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as exc:
        return f"ERROR: cannot read {path!r}: {exc}"
    total = len(lines)
    off = max(int(offset), 0)
    window = lines[off: off + max(lim, 0)]
    body = "\n".join(f"{off + k + 1}\t{ln}" for k, ln in enumerate(window))
    end = off + len(window)
    more = "" if end >= total else (
        f"\n… [{total - end} more lines; call read_file('{_disp(target)}', "
        f"offset={end}) to continue]"
    )
    header = f"{_disp(target)} [lines {off + 1}-{end} of {total}]:\n"
    return header + body + more


# --- Tool dispatch table -----------------------------------------------------
TOOLS = {
    "list_dir": list_dir,
    "glob": glob,
    "grep": grep,
    "read_file": read_file,
}


def call_tool(name: str, args: dict) -> str:
    """Dispatch a tool by name with a kwargs dict; never raises (errors → string)."""
    fn = TOOLS.get(name)
    if fn is None:
        return f"ERROR: unknown tool {name!r}. Available: {', '.join(TOOLS)}."
    try:
        return fn(**(args or {}))
    except TypeError as exc:
        return f"ERROR: bad arguments for {name!r}: {exc}"
    except Exception as exc:                          # defensive: keep the loop alive
        return f"ERROR: tool {name!r} failed: {exc}"
