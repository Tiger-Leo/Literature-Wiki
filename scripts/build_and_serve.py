#!/usr/bin/env python3
"""build_and_serve.py — one-shot, deterministic build+serve for the wiki web UI.

Replaces the CC-agent-driven web build/serve flow with a single, idempotent
Python entrypoint. Given a built `wiki/`, this script is fully automated
end-to-end: it installs deps, exports the frontend search index, builds the
Next.js frontend, boots the agentic FastAPI backend (health-polled), and serves
the frontend — or just verifies the whole pipeline and shuts down cleanly.

The backend is **agentic-search only**. There is NO embedding-index build step
(no `python -m rag.build_index`): retrieval is filesystem/agentic and needs no
prebuilt index. The script only needs a generation provider + a wiki root.

Stages
------
  1. preflight  — verify python/pnpm (+ health via stdlib urllib); resolve config
  2. install    — pip install rag reqs; pnpm install   (skip: --skip-install)
  3. export     — export_wiki.py → web/public/wiki-index.json (assert non-empty)
  4. build      — rm -rf web/.next; pnpm build            (skip: --skip-build)
  5. backend    — launch uvicorn (background), poll /health until ready
  6. frontend   — pnpm start | pnpm dev (foreground)      (skip: --no-serve)

Modes
-----
  default        run all stages, then serve the frontend in the foreground.
  --no-serve     run stages 1-6 (incl. boot backend), but don't keep serving;
                 print a JSON status and exit 0.
  --verify-only  run stages 1-5 + a backend /health check, shut everything down
                 cleanly, print a JSON status and exit 0/nonzero.

Usage
-----
  python scripts/build_and_serve.py                 # build + serve (prod)
  python scripts/build_and_serve.py --mode dev      # build + `pnpm dev`
  python scripts/build_and_serve.py --verify-only   # CI-style smoke check
  python scripts/build_and_serve.py --skip-install --skip-build --no-serve

Exit codes: 0 on success; nonzero on any stage failure (fail-fast).
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import shutil
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import NoReturn

# --- platform detection ----------------------------------------------------
IS_WINDOWS = sys.platform == "win32"

# --- repo layout -----------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
WEB_DIR = REPO_ROOT / "web"
INDEX_OUT = WEB_DIR / "public" / "wiki-index.json"

# Child processes we spawn, so the signal trap can reap them.
_CHILDREN: list[subprocess.Popen] = []


# ===========================================================================
# Logging
# ===========================================================================

def log(msg: str) -> None:
    print(f">> {msg}", flush=True)


def warn(msg: str) -> None:
    print(f"!! {msg}", file=sys.stderr, flush=True)


def die(msg: str, code: int = 1) -> NoReturn:
    warn(msg)
    _terminate_children()
    sys.exit(code)


# ===========================================================================
# .env loading (no external deps — mirrors scripts/serve.sh `source .env`)
# ===========================================================================

def load_dotenv(path: Path) -> dict[str, str]:
    """Parse a simple KEY=VALUE .env file. Existing os.environ wins (never
    overwrites an explicitly-set var), matching the RAG_* precedence rule."""
    loaded: dict[str, str] = {}
    if not path.is_file():
        return loaded
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if not key:
            continue
        loaded[key] = val
        os.environ.setdefault(key, val)
    return loaded


# ===========================================================================
# Config
# ===========================================================================

class Config:
    def __init__(self, args: argparse.Namespace) -> None:
        self.mode: str = args.mode               # dev | start
        self.web_port: int = args.port
        self.api_port: int = args.api_port
        self.api_host: str = os.environ.get("RAG_HOST", "0.0.0.0")
        # WIKI_DIR for the exporter is relative to the repo root.
        self.wiki_dir: str = args.wiki_dir or os.environ.get("WIKI_DIR", "wiki")
        self.python: str = os.environ.get("PYTHON", sys.executable or "python")
        self.skip_install: bool = args.skip_install
        self.skip_build: bool = args.skip_build
        self.verify_only: bool = args.verify_only
        self.no_serve: bool = args.no_serve
        self.ci: bool = args.ci
        self.health_url = f"http://127.0.0.1:{self.api_port}/health"

    def as_dict(self) -> dict:
        return {
            "mode": self.mode,
            "web_port": self.web_port,
            "api_port": self.api_port,
            "api_host": self.api_host,
            "wiki_dir": self.wiki_dir,
            "python": self.python,
            "skip_install": self.skip_install,
            "skip_build": self.skip_build,
            "verify_only": self.verify_only,
            "no_serve": self.no_serve,
            "ci": self.ci,
        }


# ===========================================================================
# Process helpers
# ===========================================================================

def run(cmd: list[str], *, cwd: Path | None = None, env: dict | None = None,
        stage: str = "") -> None:
    """Run a command to completion; die() on nonzero exit."""
    label = stage or " ".join(cmd[:2])
    log(f"[{label}] $ {' '.join(cmd)}")
    proc = subprocess.run(cmd, cwd=str(cwd) if cwd else None, env=env)
    if proc.returncode != 0:
        die(f"[{label}] command failed (exit {proc.returncode})", proc.returncode)


def spawn(cmd: list[str], *, cwd: Path | None = None, env: dict | None = None,
          log_path: Path | None = None) -> subprocess.Popen:
    """Launch a background process; track it for cleanup."""
    out = open(log_path, "w") if log_path else None
    kwargs: dict = {
        "cwd": str(cwd) if cwd else None,
        "env": env,
        "stdout": out,
        "stderr": subprocess.STDOUT if out else None,
    }
    if not IS_WINDOWS:
        kwargs["start_new_session"] = True  # own process group → clean group kill
    proc = subprocess.Popen(cmd, **kwargs)
    proc._log_fh = out  # type: ignore[attr-defined]
    _CHILDREN.append(proc)
    return proc


def _terminate_children() -> None:
    for proc in list(_CHILDREN):
        if proc.poll() is not None:
            continue
        if IS_WINDOWS:
            # Windows: terminate directly (no process groups)
            with contextlib.suppress(Exception):
                proc.terminate()
        else:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            except (ProcessLookupError, PermissionError, OSError):
                with contextlib.suppress(Exception):
                    proc.terminate()
    # grace period, then kill stragglers
    deadline = time.time() + 5
    for proc in list(_CHILDREN):
        remaining = max(0.0, deadline - time.time())
        with contextlib.suppress(Exception):
            proc.wait(timeout=remaining)
        if proc.poll() is None:
            if IS_WINDOWS:
                with contextlib.suppress(Exception):
                    proc.kill()
            else:
                with contextlib.suppress(Exception):
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    _CHILDREN.clear()


def _install_signal_trap() -> None:
    def _handler(signum, _frame):
        warn(f"received signal {signum}; shutting down child processes")
        _terminate_children()
        sys.exit(128 + signum)
    # SIGTERM is unavailable on Windows
    sigs = (signal.SIGINT, signal.SIGTERM) if not IS_WINDOWS else (signal.SIGINT,)
    for sig in sigs:
        with contextlib.suppress(Exception):
            signal.signal(sig, _handler)


# ===========================================================================
# Stage 1 — preflight
# ===========================================================================

def stage_preflight(cfg: Config) -> dict:
    log("Stage 1/6 — preflight")
    warnings: list[str] = []

    # python: we're already running under one; just verify uvicorn importable.
    if shutil.which(cfg.python) is None and not Path(cfg.python).exists():
        warn(f"python interpreter '{cfg.python}' not found on PATH")
    uvicorn_ok = subprocess.run(
        [cfg.python, "-c", "import uvicorn"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ).returncode == 0
    if not uvicorn_ok and cfg.skip_install:
        die("uvicorn not importable and --skip-install set. "
            "Run without --skip-install or activate your env.")
    if not uvicorn_ok:
        warnings.append("uvicorn not yet importable; install stage will add it")

    # pnpm is required for both install and build/serve.
    if shutil.which("pnpm") is None:
        die("pnpm not found. Install pnpm: https://pnpm.io/installation")

    # health checks use stdlib urllib (no curl dependency).
    if not WEB_DIR.is_dir():
        die(f"web/ directory not found at {WEB_DIR}")
    wiki_path = (REPO_ROOT / cfg.wiki_dir)
    if not wiki_path.is_dir():
        die(f"wiki dir not found: {wiki_path} (set --wiki-dir or WIKI_DIR)")

    log("Resolved config:")
    print(json.dumps(cfg.as_dict(), indent=2), flush=True)
    return {"warnings": warnings, "uvicorn_ok": uvicorn_ok}


# ===========================================================================
# Stage 2 — install
# ===========================================================================

def stage_install(cfg: Config) -> None:
    if cfg.skip_install:
        log("Stage 2/6 — install (SKIPPED via --skip-install)")
        return
    log("Stage 2/6 — install deps")
    reqs = REPO_ROOT / "rag" / "requirements.txt"
    if reqs.is_file():
        run([cfg.python, "-m", "pip", "install", "-r", str(reqs)],
            cwd=REPO_ROOT, stage="pip")
    else:
        warn(f"{reqs} missing — skipping pip install")
    pnpm_cmd = ["pnpm", "install"]
    if cfg.ci:
        pnpm_cmd.append("--frozen-lockfile")
    run(pnpm_cmd, cwd=WEB_DIR, stage="pnpm install")


# ===========================================================================
# Stage 3 — export search index
# ===========================================================================

def stage_export(cfg: Config) -> int:
    log("Stage 3/6 — export search index")
    run(
        [cfg.python, "scripts/export_wiki.py",
         "--wiki-dir", cfg.wiki_dir,
         "--out", str(INDEX_OUT.relative_to(REPO_ROOT))],
        cwd=REPO_ROOT, stage="export_wiki",
    )
    if not INDEX_OUT.is_file():
        die(f"search index not produced at {INDEX_OUT}")
    data: object = {}
    try:
        data = json.loads(INDEX_OUT.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        die(f"search index is not valid JSON: {exc}")
    pages = data.get("pages") if isinstance(data, dict) else None
    count = len(pages) if isinstance(pages, list) else 0
    if count == 0:
        die(f"search index is empty (0 pages) at {INDEX_OUT}")
    log(f"search index OK — {count} pages → {INDEX_OUT}")
    return count


# ===========================================================================
# Stage 4 — build frontend
# ===========================================================================

def _web_env(cfg: Config) -> dict:
    """Frontend env. WIKI_DIR for the web app is relative to web/, so translate
    a repo-root wiki dir into a web-relative path. NEXT_PUBLIC_* pass through
    from the loaded environment (branding/api), as does the build-time WIKI_DIR.
    """
    env = dict(os.environ)
    env.setdefault("NODE_OPTIONS", "")
    # repo-root wiki dir → web-relative (web/ is one level under repo root).
    repo_wiki = (REPO_ROOT / cfg.wiki_dir).resolve()
    try:
        rel = os.path.relpath(repo_wiki, WEB_DIR)
        # Node.js expects POSIX separators even on Windows
        env["WIKI_DIR"] = rel.replace(os.sep, "/")
    except ValueError:
        env["WIKI_DIR"] = str(repo_wiki).replace(os.sep, "/")
    env.setdefault("NEXT_PUBLIC_BACKEND_PORT", str(cfg.api_port))
    return env


def stage_build(cfg: Config) -> None:
    if cfg.skip_build:
        log("Stage 4/6 — build frontend (SKIPPED via --skip-build)")
        return
    log("Stage 4/6 — build frontend (fresh .next)")
    next_dir = WEB_DIR / ".next"
    if next_dir.exists():
        # Honor the rebuild→restart caveat: always start from a clean build dir.
        shutil.rmtree(next_dir, ignore_errors=True)
    run(["pnpm", "build"], cwd=WEB_DIR, env=_web_env(cfg), stage="pnpm build")


# ===========================================================================
# Stage 5 — start backend + health poll
# ===========================================================================

def _health_ok(url: str, timeout: float = 2.0) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:  # noqa: S310
            return 200 <= resp.status < 300
    except (urllib.error.URLError, OSError, ValueError):
        return False


def stage_backend(cfg: Config, log_path: Path) -> subprocess.Popen:
    log("Stage 5/6 — start agentic backend (uvicorn)")
    cmd = [
        cfg.python, "-m", "uvicorn", "rag.server:app",
        "--host", cfg.api_host, "--port", str(cfg.api_port),
    ]
    log(f"[uvicorn] $ {' '.join(cmd)}  (logs: {log_path})")
    proc = spawn(cmd, cwd=REPO_ROOT, env=dict(os.environ), log_path=log_path)

    timeout_s = 60
    deadline = time.time() + timeout_s
    print(f">> waiting for {cfg.health_url} ", end="", flush=True)
    while time.time() < deadline:
        if proc.poll() is not None:
            print("", flush=True)
            _dump_log(log_path)
            die(f"backend exited early (code {proc.returncode}) before becoming healthy")
        if _health_ok(cfg.health_url):
            print(" ok", flush=True)
            log("backend healthy")
            return proc
        print(".", end="", flush=True)
        time.sleep(1)
    print("", flush=True)
    _dump_log(log_path)
    die(f"backend did not become healthy at {cfg.health_url} within {timeout_s}s")


def _dump_log(path: Path, n: int = 30) -> None:
    if not path.is_file():
        return
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    warn(f"--- last {min(n, len(lines))} lines of {path} ---")
    for line in lines[-n:]:
        print(line, file=sys.stderr, flush=True)


# ===========================================================================
# Stage 6 — start frontend (foreground)
# ===========================================================================

def stage_frontend(cfg: Config) -> NoReturn:
    log(f"Stage 6/6 — start frontend (pnpm {cfg.mode}) on :{cfg.web_port}")
    script = "dev" if cfg.mode == "dev" else "start"
    env = _web_env(cfg)
    cmd = ["pnpm", script, "--port", str(cfg.web_port)]
    log(f"[pnpm {script}] $ {' '.join(cmd)}")
    # Foreground: replace our wait-loop with the frontend process. We still want
    # the signal trap to reap the backend, so run as a child and wait on it.
    proc = subprocess.Popen(cmd, cwd=str(WEB_DIR), env=env, start_new_session=True)
    _CHILDREN.append(proc)
    try:
        rc = proc.wait()
    except KeyboardInterrupt:
        rc = 130
    _terminate_children()
    sys.exit(rc)


# ===========================================================================
# Status emit
# ===========================================================================

def emit_status(cfg: Config, *, index_count: int, backend_pid: int | None,
                warnings: list[str]) -> None:
    web_url = f"http://localhost:{cfg.web_port}"
    api_url = f"http://localhost:{cfg.api_port}"
    status = {
        "ok": True,
        "mode": cfg.mode,
        "urls": {"web": web_url, "api": api_url, "health": cfg.health_url},
        "pids": {"backend": backend_pid},
        "index": {"path": str(INDEX_OUT), "pages": index_count},
        "warnings": warnings,
    }
    print("STATUS " + json.dumps(status), flush=True)


# ===========================================================================
# main
# ===========================================================================

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="build_and_serve.py",
        description="Deterministic one-shot build+serve for the wiki web UI "
                    "(agentic-search backend; NO embedding-index step).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--wiki-dir", default=None,
                   help="wiki source dir relative to repo root (default: ./wiki "
                        "or $WIKI_DIR).")
    p.add_argument("--mode", choices=["dev", "start"], default="start",
                   help="frontend mode: 'start' (prod build) or 'dev' (default: start).")
    p.add_argument("--port", type=int, default=3000, help="frontend port (default 3000).")
    p.add_argument("--api-port", type=int, default=8000, help="backend port (default 8000).")
    p.add_argument("--skip-install", action="store_true",
                   help="skip pip + pnpm install.")
    p.add_argument("--skip-build", action="store_true",
                   help="skip the frontend production build.")
    p.add_argument("--verify-only", action="store_true",
                   help="run stages 1-5 + health check, then shut down cleanly "
                        "and exit (no serving).")
    p.add_argument("--no-serve", action="store_true",
                   help="run all build stages and boot the backend, but do not "
                        "keep serving; print status and exit.")
    p.add_argument("--ci", action="store_true",
                   help="CI mode: pnpm install --frozen-lockfile.")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    cfg = Config(args)

    _install_signal_trap()
    load_dotenv(REPO_ROOT / ".env")
    # Re-resolve env-derived defaults now that .env is loaded (flags still win).
    if args.wiki_dir is None:
        cfg.wiki_dir = os.environ.get("WIKI_DIR", "wiki")

    pre = stage_preflight(cfg)
    warnings: list[str] = pre["warnings"]

    stage_install(cfg)
    index_count = stage_export(cfg)
    stage_build(cfg)

    api_log = REPO_ROOT / ".build_and_serve.api.log"

    if cfg.verify_only:
        backend = stage_backend(cfg, api_log)
        log("verify-only: backend healthy; shutting down cleanly")
        emit_status(cfg, index_count=index_count, backend_pid=backend.pid,
                    warnings=warnings)
        _terminate_children()
        return 0

    backend = stage_backend(cfg, api_log)

    if cfg.no_serve:
        log("no-serve: build complete and backend healthy; not serving frontend")
        emit_status(cfg, index_count=index_count, backend_pid=backend.pid,
                    warnings=warnings)
        _terminate_children()
        return 0

    emit_status(cfg, index_count=index_count, backend_pid=backend.pid,
                warnings=warnings)
    stage_frontend(cfg)  # never returns
    return 0  # pragma: no cover


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except KeyboardInterrupt:
        _terminate_children()
        sys.exit(130)
    except Exception as exc:  # noqa: BLE001
        warn(f"unexpected error: {exc}")
        _terminate_children()
        sys.exit(1)
