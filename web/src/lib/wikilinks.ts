/**
 * Wikilink support: turn Obsidian-style `[[slug]]` and `[[slug|alias]]` into
 * links to `/wiki/{slug}` inside markdown rendered by react-markdown.
 *
 * Implemented as a **remark (mdast) plugin** that splits `text` nodes on the
 * wikilink pattern and inserts `link` nodes. Operating on the mdast tree (rather
 * than a raw-string pre-pass) means inline code and fenced code blocks are left
 * untouched automatically — their contents live in `inlineCode` / `code` nodes,
 * never in `text` nodes — so `[[slug]]` written inside backticks stays literal.
 */

// Minimal mdast node shapes (avoid pulling @types/mdast as a dependency).
type MdastNode = {
  type: string;
  value?: string;
  url?: string;
  children?: MdastNode[];
  [key: string]: unknown;
};

// `[[ ... ]]` where the inner text has no newline and no nested brackets.
const WIKILINK_RE = /\[\[([^\]\n]+?)\]\]/g;

/** Normalise a raw slug/target into a clean URL slug segment.
 * Handles path-style targets (`raw_markdown/papers/foo`, `wiki/concepts/bar`,
 * `concepts/authority`), a trailing `.md`, and `#anchor` fragments — mirroring the
 * wiki's own link resolver, which keys on the bare basename slug. */
function toSlug(raw: string): string {
  let s = raw.trim().split("#")[0].trim(); // drop #anchor
  s = s.split("/").pop() ?? s; // basename: drop any path/ prefix
  s = s.replace(/\.md$/i, ""); // drop trailing .md
  return s.trim();
}

function splitTextNode(value: string): MdastNode[] | null {
  WIKILINK_RE.lastIndex = 0;
  if (!WIKILINK_RE.test(value)) return null;

  const out: MdastNode[] = [];
  let lastIndex = 0;
  WIKILINK_RE.lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = WIKILINK_RE.exec(value)) !== null) {
    const [full, inner] = match;
    const start = match.index;

    if (start > lastIndex) {
      out.push({ type: "text", value: value.slice(lastIndex, start) });
    }

    const pipe = inner.indexOf("|");
    const slug = toSlug(pipe === -1 ? inner : inner.slice(0, pipe));
    const alias = pipe === -1 ? slug : inner.slice(pipe + 1).trim();

    if (!slug) {
      // Malformed (e.g. `[[|x]]`) — keep the literal text.
      out.push({ type: "text", value: full });
    } else {
      out.push({
        type: "link",
        url: `/wiki/${encodeURIComponent(slug)}`,
        title: null,
        children: [{ type: "text", value: alias || slug }],
      });
    }

    lastIndex = start + full.length;
  }

  if (lastIndex < value.length) {
    out.push({ type: "text", value: value.slice(lastIndex) });
  }

  return out;
}

function transform(node: MdastNode): void {
  if (!node.children || node.children.length === 0) return;

  const next: MdastNode[] = [];
  for (const child of node.children) {
    // Never descend into code: its text is not a `text` node anyway, but be
    // explicit and skip `inlineCode` / `code` defensively.
    if (child.type === "inlineCode" || child.type === "code") {
      next.push(child);
      continue;
    }
    if (child.type === "text" && typeof child.value === "string") {
      const replaced = splitTextNode(child.value);
      if (replaced) {
        next.push(...replaced);
        continue;
      }
      next.push(child);
      continue;
    }
    // Recurse into containers (paragraphs, emphasis, list items, links, …).
    transform(child);
    next.push(child);
  }
  node.children = next;
}

/** remark plugin: `remarkPlugins={[remarkWikilinks]}`. */
export function remarkWikilinks() {
  return (tree: MdastNode) => {
    transform(tree);
  };
}
