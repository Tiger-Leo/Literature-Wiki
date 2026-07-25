/**
 * Server-only filesystem access to the wiki markdown layer. This decouples the
 * Browse (`/wiki`) and View (`/wiki/[slug]`) surfaces from the RAG backend — they
 * read `*.md` files directly, so they work with NO backend running.
 *
 * The wiki directory resolves from `process.env.WIKI_DIR` (default `../wiki`
 * relative to the `web/` cwd). For the template demo, set
 * `WIKI_DIR=../examples/demo-wiki/wiki`.
 *
 * Frontmatter-stripping and title logic mirror `scripts/export_wiki.py` so the
 * filesystem view and the exported search index agree.
 */
import "server-only";
import fs from "node:fs";
import path from "node:path";

/** Directories never treated as wiki content (mirrors the exporter). */
const EXCLUDED_DIRS = new Set(["templates", "schema", "inbox", "_raw", "scratch"]);
/** Filenames never treated as wiki pages (mirrors the exporter). */
const EXCLUDED_FILENAMES = new Set(["_index.md", "readme.md"]);

export type WikiPageMeta = {
  slug: string;
  path: string; // relative to the wiki dir, POSIX-style
  layer: string;
  title: string;
  type: string;
  status: string;
};

export type WikiPageFull = WikiPageMeta & {
  markdown: string; // frontmatter-stripped body
  found: boolean;
};

/** Absolute path to the wiki directory (resolved against the process cwd). */
export function wikiDir(): string {
  const configured = process.env.WIKI_DIR ?? "../wiki";
  return path.resolve(process.cwd(), configured);
}

/** Split a `---`-delimited YAML frontmatter block from the body. */
function splitFrontmatter(text: string): { block: string; body: string } {
  const lines = text.split(/\r?\n/);
  if (lines.length === 0 || lines[0].trim() !== "---") {
    return { block: "", body: text };
  }
  for (let i = 1; i < lines.length; i++) {
    if (lines[i].trim() === "---") {
      return {
        block: lines.slice(1, i).join("\n"),
        body: lines.slice(i + 1).join("\n"),
      };
    }
  }
  // Unterminated frontmatter: treat the whole thing as body.
  return { block: "", body: text };
}

function cleanScalar(value: string): string {
  let v = value.trim();
  if (
    (v.startsWith('"') && v.endsWith('"')) ||
    (v.startsWith("'") && v.endsWith("'"))
  ) {
    v = v.slice(1, -1);
  }
  return v.trim();
}

/** Tolerant top-level key:value frontmatter parser (string scalars only). */
function parseFrontmatter(block: string): Record<string, string> {
  const data: Record<string, string> = {};
  if (!block.trim()) return data;
  for (const raw of block.split(/\r?\n/)) {
    const line = raw.replace(/\s+$/, "");
    if (!line.trim() || line.trimStart().startsWith("#")) continue;
    if (line.startsWith(" ") || line.startsWith("\t")) continue; // skip nested
    const idx = line.indexOf(":");
    if (idx === -1) continue;
    const key = line.slice(0, idx).trim();
    const value = line.slice(idx + 1).trim();
    if (key && value) data[key] = cleanScalar(value);
  }
  return data;
}

/** First markdown H1 in the body, or "". */
function firstH1(body: string): string {
  for (const line of body.split(/\r?\n/)) {
    const m = /^#\s+(.*)$/.exec(line.trim());
    if (m) return m[1].trim();
  }
  return "";
}

/** "spaced-repetition" → "Spaced Repetition" */
function humanize(slug: string): string {
  return slug
    .replace(/[-_]+/g, " ")
    .split(" ")
    .filter(Boolean)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

/** Strip the leading H1 (and blank lines before it) from the body. */
function stripLeadingH1(body: string): string {
  const lines = body.split(/\r?\n/);
  let i = 0;
  while (i < lines.length && !lines[i].trim()) i++;
  if (i < lines.length && /^#\s+/.test(lines[i].trim())) {
    return lines.slice(i + 1).join("\n").replace(/^\s+/, "");
  }
  return body;
}

/** Recursively collect markdown files under `dir`, excluding the usual dirs. */
function walkMarkdown(root: string, dir: string, out: string[]): void {
  let entries: fs.Dirent[];
  try {
    entries = fs.readdirSync(dir, { withFileTypes: true });
  } catch {
    return;
  }
  for (const entry of entries) {
    if (entry.name.startsWith(".")) continue;
    const abs = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      // Skip meta/non-content dirs (templates, schema, inbox, scratch, _raw, any _-prefixed).
      if (entry.name.startsWith("_") || EXCLUDED_DIRS.has(entry.name)) continue;
      walkMarkdown(root, abs, out);
    } else if (entry.isFile() && entry.name.toLowerCase().endsWith(".md")) {
      // Meta files (_index.md, _template.md, README.md) are not content pages.
      if (entry.name.startsWith("_")) continue;
      if (EXCLUDED_FILENAMES.has(entry.name.toLowerCase())) continue;
      // Pages live in a layer subdir; skip top-level files (e.g. log.md, stray notes).
      if (dir === root) continue;
      out.push(abs);
    }
  }
}

function metaFromFile(root: string, abs: string): WikiPageMeta {
  const relPosix = path.relative(root, abs).split(path.sep).join("/");
  const segments = relPosix.split("/");
  const layer = segments.length > 1 ? segments[0] : "";
  const slug = path.basename(abs).replace(/\.md$/i, "");

  let text = "";
  try {
    text = fs.readFileSync(abs, "utf8");
  } catch {
    /* ignore */
  }
  const { block, body } = splitFrontmatter(text);
  const fm = parseFrontmatter(block);
  const title = fm.title || firstH1(body) || humanize(slug);

  return {
    slug,
    path: relPosix,
    layer,
    title,
    type: fm.type || "",
    status: fm.status || "",
  };
}

/** List every wiki page (metadata only), sorted by layer then title. */
export function listPages(): WikiPageMeta[] {
  const root = wikiDir();
  const files: string[] = [];
  walkMarkdown(root, root, files);
  const pages = files.map((abs) => metaFromFile(root, abs));
  pages.sort(
    (a, b) =>
      a.layer.localeCompare(b.layer) || a.title.localeCompare(b.title),
  );
  return pages;
}

/**
 * Fetch one page by slug from the filesystem. Searches every layer dir; returns
 * `found: false` (with empty markdown) when no matching `*.md` exists.
 */
export function getPage(slug: string): WikiPageFull {
  const root = wikiDir();
  const files: string[] = [];
  walkMarkdown(root, root, files);
  const match = files.find(
    (abs) => path.basename(abs).replace(/\.md$/i, "") === slug,
  );

  if (!match) {
    return {
      slug,
      path: "",
      layer: "",
      title: humanize(slug),
      type: "",
      status: "",
      markdown: "",
      found: false,
    };
  }

  const meta = metaFromFile(root, match);
  const text = fs.readFileSync(match, "utf8");
  const { body } = splitFrontmatter(text);
  // Keep the leading H1 out of the body — the viewer renders the title in its
  // own header. (stripLeadingH1 mirrors the exporter's excerpt source.)
  const markdown = stripLeadingH1(body);

  return { ...meta, markdown, found: true };
}
