#!/usr/bin/env python3
"""Export a wiki directory into a single JSON index for the frontend.

Walks WIKI_DIR for `*.md` pages (excluding `_index.md` and the
`templates/`, `schema/`, `inbox/` directories) and emits one record per
page following the agreed frontend contract:

    {"slug","path","layer","title","type","status","tags":[],"papers":[],
     "headings":[],"wikilinks_out":[],"excerpt","text"}

The output wrapper carries `generated_at`, `wiki_title`, `count`, `pages`.

Pure stdlib; PyYAML is used for frontmatter parsing when available, with a
hand-rolled "yamlish" fallback that tolerates the simple list/scalar format
the repo's authors actually write.

CLI:
    python scripts/export_wiki.py \
        [--wiki-dir wiki] \
        [--out web/public/wiki-index.json] \
        [--also exports/wiki.json] \
        [--title "<wiki title>"]
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
from pathlib import Path

try:  # PyYAML is available in conda `sci`; fall back gracefully if not.
    import yaml as _yaml  # type: ignore
except Exception:  # pragma: no cover - exercised only without PyYAML
    _yaml = None


EXCLUDED_DIRS = {"templates", "schema", "inbox", "_raw", "scratch"}
EXCLUDED_FILENAMES = {"_index.md", "README.md"}

# Layers whose singular form differs from a naive "drop trailing s".
_LAYER_SINGULAR = {
    "concepts": "concept",
    "mechanisms": "mechanism",
    "debates": "debate",
    "methods": "method",
    "measures": "measure",
    "synthesis": "synthesis",
    "sources": "source",
}


# ---------------------------------------------------------------------------
# Frontmatter parsing
# ---------------------------------------------------------------------------

def split_frontmatter(text: str) -> tuple[str, str]:
    """Return (frontmatter_block, body). Empty frontmatter if none present."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return "", text
    for idx, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            fm = "\n".join(lines[1:idx])
            body = "\n".join(lines[idx + 1 :])
            return fm, body
    # Unterminated frontmatter: treat the whole thing as body.
    return "", text


def parse_yamlish(block: str) -> dict[str, object]:
    """Tolerant fallback parser for the repo's simple frontmatter format."""
    data: dict[str, object] = {}
    current_key: str | None = None
    for raw_line in block.splitlines():
        line = raw_line.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        stripped = line.lstrip()
        if stripped.startswith("- ") and current_key:
            data.setdefault(current_key, [])
            if isinstance(data[current_key], list):
                data[current_key].append(_clean_scalar(stripped[2:]))
            continue
        if ":" in line:
            key, _, value = line.partition(":")
            current_key = key.strip()
            value = value.strip()
            if value == "":
                data[current_key] = []  # may be filled by following `- ` items
            else:
                data[current_key] = _coerce_inline(value)
    # Collapse keys that ended up as empty lists but never got items: keep [].
    return data


def _clean_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        value = value[1:-1]
    return value.strip()


def _coerce_inline(value: str) -> object:
    """Coerce an inline scalar / inline list (`[a, b]`) value."""
    value = value.strip()
    # Inline flow list: [a, b, c]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_clean_scalar(item) for item in inner.split(",") if item.strip()]
    return _clean_scalar(value)


def parse_frontmatter(text: str) -> tuple[dict[str, object], str]:
    block, body = split_frontmatter(text)
    if not block.strip():
        return {}, body
    if _yaml is not None:
        try:
            loaded = _yaml.safe_load(block)
            if isinstance(loaded, dict):
                return loaded, body
        except Exception:
            pass  # fall through to yamlish
    return parse_yamlish(block), body


# ---------------------------------------------------------------------------
# Field helpers
# ---------------------------------------------------------------------------

def _as_str(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _as_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [_as_str(v) for v in value if _as_str(v)]
    s = _as_str(value)
    return [s] if s else []


def humanize(slug: str) -> str:
    words = re.split(r"[-_]+", slug)
    return " ".join(w[:1].upper() + w[1:] for w in words if w)


def layer_of(rel_path: Path) -> str:
    parts = rel_path.parts
    if len(parts) > 1:
        return parts[0]
    return ""


def singular_of(layer: str) -> str:
    if not layer:
        return ""
    if layer in _LAYER_SINGULAR:
        return _LAYER_SINGULAR[layer]
    return layer[:-1] if layer.endswith("s") else layer


def first_h1(body: str) -> str:
    for line in body.splitlines():
        m = re.match(r"^#\s+(.*)$", line.strip())
        if m:
            return m.group(1).strip()
    return ""


def extract_headings(body: str) -> list[str]:
    headings: list[str] = []
    for line in body.splitlines():
        m = re.match(r"^(#{2,3})\s+(.*)$", line.strip())
        if m:
            headings.append(m.group(2).strip())
    return headings


_WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


def extract_wikilinks(body: str) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for raw in _WIKILINK_RE.findall(body):
        target = raw.split("|", 1)[0]          # strip alias
        target = target.split("#", 1)[0]       # strip anchor
        target = target.strip()
        if not target:
            continue
        # strip path + extension, take basename
        slug = target.replace("\\", "/").rstrip("/").split("/")[-1]
        if slug.lower().endswith(".md"):
            slug = slug[:-3]
        slug = slug.strip()
        if slug and slug not in seen:
            seen.add(slug)
            out.append(slug)
    return out


# ---------------------------------------------------------------------------
# Body -> plain-ish search text
# ---------------------------------------------------------------------------

def _strip_h1(body: str) -> str:
    """Remove the leading H1 (and blank lines before it) for excerpt source."""
    lines = body.splitlines()
    out: list[str] = []
    dropped_h1 = False
    for line in lines:
        if not dropped_h1:
            if not line.strip():
                continue
            if re.match(r"^#\s+", line.strip()):
                dropped_h1 = True
                continue
            # first non-blank line is not an H1: keep everything
            return body
        out.append(line)
    return "\n".join(out)


def flatten_text(body: str) -> str:
    """Flatten markdown body into plain-ish searchable text."""
    text = body

    # Flatten wikilinks: [[a|b]] -> b, [[a]] -> basename-ish a
    def _wl(m: re.Match[str]) -> str:
        inner = m.group(1)
        if "|" in inner:
            return inner.split("|", 1)[1].strip()
        inner = inner.split("#", 1)[0]
        return inner.replace("\\", "/").split("/")[-1].strip()

    text = _WIKILINK_RE.sub(_wl, text)

    # Markdown links [text](url) -> text
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)

    # Images ![alt](url) -> alt (handled by the link rule above after !)
    text = text.replace("![", "[")

    # Drop callout markers: lines/inline `> [!type]` and bare blockquote markers
    text = re.sub(r"(?m)^\s*>\s*\[!\w+\][-+]?\s*", "", text)
    text = re.sub(r"(?m)^\s*>\s?", "", text)

    # Drop heading hashes but keep heading text
    text = re.sub(r"(?m)^\s*#{1,6}\s+", "", text)

    # Strip fenced code fences (keep code content)
    text = re.sub(r"(?m)^\s*```.*$", "", text)

    # Collapse emphasis/markup characters
    text = text.replace("**", "").replace("__", "")
    text = re.sub(r"(?<!\w)[*_]+(?=\S)", "", text)
    text = re.sub(r"(?<=\S)[*_]+(?!\w)", "", text)
    text = text.replace("`", "")

    # Bullet / list markers at line start
    text = re.sub(r"(?m)^\s*[-*+]\s+", "", text)
    text = re.sub(r"(?m)^\s*\d+\.\s+", "", text)

    # Table pipes -> spaces
    text = text.replace("|", " ")

    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def make_excerpt(body: str, limit: int = 280) -> str:
    source = _strip_h1(body)
    flat = flatten_text(source)
    if len(flat) <= limit:
        return flat
    cut = flat[:limit]
    # avoid cutting mid-word
    if " " in cut:
        cut = cut[: cut.rfind(" ")]
    return cut.rstrip() + "…"


# ---------------------------------------------------------------------------
# Page building
# ---------------------------------------------------------------------------

def build_page(md_path: Path, wiki_dir: Path) -> dict[str, object]:
    text = md_path.read_text(encoding="utf-8", errors="replace")
    fm, body = parse_frontmatter(text)

    rel_path = md_path.relative_to(wiki_dir)
    slug = md_path.stem
    layer = layer_of(rel_path)

    title = _as_str(fm.get("title")) or first_h1(body) or humanize(slug)
    page_type = _as_str(fm.get("type")) or singular_of(layer)
    status = _as_str(fm.get("status"))

    tags = _as_list(fm.get("tags"))
    papers = _as_list(fm.get("papers"))
    if not papers and fm.get("authors") is not None:
        papers = _as_list(fm.get("authors"))

    return {
        "slug": slug,
        "path": str(rel_path).replace("\\", "/"),
        "layer": layer,
        "title": title,
        "type": page_type,
        "status": status,
        "tags": tags,
        "papers": papers,
        "headings": extract_headings(body),
        "wikilinks_out": extract_wikilinks(body),
        "excerpt": make_excerpt(body),
        "text": flatten_text(body),
    }


def is_excluded(md_path: Path, wiki_dir: Path) -> bool:
    rel_parts = md_path.relative_to(wiki_dir).parts
    # Pages live in a layer subdir; skip top-level files (e.g. log.md, stray notes).
    if len(rel_parts) == 1:
        return True
    # Meta files (_index.md, _template.md, README.md) are not content pages.
    if md_path.name in EXCLUDED_FILENAMES or md_path.name.startswith("_"):
        return True
    # Skip meta/non-content dirs (templates, schema, inbox, scratch, _raw, any _-prefixed).
    return any(
        part in EXCLUDED_DIRS or part.startswith("_") for part in rel_parts[:-1]
    )


def derive_wiki_title(wiki_dir: Path, override: str | None) -> str:
    if override:
        return override
    index = wiki_dir / "_index.md"
    if index.is_file():
        _, body = parse_frontmatter(index.read_text(encoding="utf-8", errors="replace"))
        h1 = first_h1(body)
        if h1:
            return h1
    return "Literature Wiki"


def export_wiki(wiki_dir: Path, title: str | None) -> dict[str, object]:
    pages: list[dict[str, object]] = []
    for md_path in sorted(wiki_dir.rglob("*.md")):
        if is_excluded(md_path, wiki_dir):
            continue
        pages.append(build_page(md_path, wiki_dir))

    pages.sort(key=lambda p: (p["layer"], p["slug"]))

    generated_at = (
        _dt.datetime.now(_dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )

    return {
        "generated_at": generated_at,
        "wiki_title": derive_wiki_title(wiki_dir, title),
        "count": len(pages),
        "pages": pages,
    }


def write_json(data: dict[str, object], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wiki-dir", default="wiki")
    parser.add_argument("--out", default="web/public/wiki-index.json")
    parser.add_argument("--also", default="exports/wiki.json")
    parser.add_argument("--title", default=None)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    wiki_dir = Path(args.wiki_dir).resolve()
    if not wiki_dir.is_dir():
        print(f"error: wiki dir not found: {wiki_dir}")
        return 1

    data = export_wiki(wiki_dir, args.title)

    for out in (args.out, args.also):
        if not out:
            continue
        write_json(data, Path(out))
        print(f"wrote {data['count']} pages -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
