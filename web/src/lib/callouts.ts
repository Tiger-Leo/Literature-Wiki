/**
 * Obsidian-style callout support for react-markdown / MarkdownTextPrimitive.
 *
 * Obsidian writes admonitions as a blockquote whose first line carries a
 * `[!type]` marker and an optional title:
 *
 *   > [!note] Current assessment
 *   > The wiki's best current judgement…
 *
 * Without help, react-markdown renders the literal text "[!note] Current
 * assessment" as the first line of an ordinary blockquote. This remark (mdast)
 * plugin detects that marker on a `blockquote`, strips it, and rewrites the node
 * into a styled callout box: it sets the blockquote's hast output to a
 * `<div class="aui-callout aui-callout-{type}">` and prepends a
 * `<div class="aui-callout-title">…</div>` holding the title (the explicit title
 * after the marker, or a humanised default per type).
 *
 * Styling lives in `globals.css` (`.aui-callout*` rules), so the exact same
 * markup is produced for both chat answers and the `/wiki/{slug}` page and the
 * appearance is theme-aware. Ordinary blockquotes (no `[!type]` marker) are left
 * completely untouched, so normal quoting still works.
 */

// Minimal mdast/hast-ish node shape (avoid pulling @types/mdast).
type MdastNode = {
  type: string;
  value?: string;
  children?: MdastNode[];
  data?: {
    hName?: string;
    hProperties?: Record<string, unknown>;
    [key: string]: unknown;
  };
  [key: string]: unknown;
};

// `[!type]` optionally followed by a `+`/`-` fold marker, then an optional title
// on the SAME line. Applied only to the first physical line of the blockquote
// (we split off the marker line first), so it deliberately does NOT span
// newlines — anchoring with `$` against a multi-line string previously made the
// match fail and the marker leaked through as literal text.
const CALLOUT_RE = /^\s*\[!(\w+)\]([+-]?)[^\S\n]*(.*)$/;

// Callouts we explicitly style; anything else falls back to the generic "note".
const KNOWN_TYPES = new Set([
  "note",
  "tip",
  "hint",
  "info",
  "important",
  "warning",
  "caution",
  "danger",
  "error",
  "success",
  "question",
  "abstract",
  "example",
  "quote",
]);

function titleCase(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

/**
 * Find the first `text` node inside a node subtree (depth-first), returning it
 * and a setter that mutates its value. Used to read/strip the `[!type]` marker
 * which always sits at the very start of the blockquote's first text run.
 */
function firstTextNode(node: MdastNode): MdastNode | null {
  if (node.type === "text" && typeof node.value === "string") return node;
  if (node.children) {
    for (const child of node.children) {
      const found = firstTextNode(child);
      if (found) return found;
    }
  }
  return null;
}

function transformBlockquote(node: MdastNode): void {
  const firstChild = node.children?.[0];
  if (!firstChild) return;

  // The marker always sits at the very start of the blockquote's first text run.
  // Crucially, remark packs the marker line AND the following body lines into a
  // single `text` node separated by `\n` (e.g. "[!note] Title\nbody…"), so we
  // must split on the FIRST newline and match the marker against only that first
  // line — not the whole multi-line value.
  const textNode = firstTextNode(firstChild);
  if (!textNode || typeof textNode.value !== "string") return;

  const nlIndex = textNode.value.indexOf("\n");
  const markerLine =
    nlIndex === -1 ? textNode.value : textNode.value.slice(0, nlIndex);
  const restAfterMarkerLine =
    nlIndex === -1 ? "" : textNode.value.slice(nlIndex + 1);

  const match = markerLine.match(CALLOUT_RE);
  if (!match) return;

  const rawType = match[1].toLowerCase();
  const type = KNOWN_TYPES.has(rawType) ? rawType : "note";
  const explicitTitle = match[3].trim();
  const title = explicitTitle || titleCase(rawType);

  // Strip the marker line; keep any body text that shared the same text node.
  textNode.value = restAfterMarkerLine;

  // If stripping left the first paragraph's first text node empty AND it was the
  // paragraph's only child, drop that now-empty paragraph so the callout box does
  // not open with a blank line (covers the common "title line then body
  // paragraphs" shape). Inline siblings after the marker (rare) are preserved.
  if (
    textNode.value === "" &&
    firstChild.type === "paragraph" &&
    (firstChild.children?.length ?? 0) === 1 &&
    firstChild.children?.[0] === textNode
  ) {
    node.children?.shift();
  }

  // Rewrite the blockquote into a styled div + prepend a title element.
  node.data = node.data ?? {};
  node.data.hName = "div";
  node.data.hProperties = {
    ...(node.data.hProperties ?? {}),
    className: ["aui-callout", `aui-callout-${type}`],
    "data-callout": type,
  };

  const titleNode: MdastNode = {
    type: "paragraph",
    data: {
      hName: "div",
      hProperties: { className: ["aui-callout-title"] },
    },
    children: [{ type: "text", value: title }],
  };

  node.children = [titleNode, ...(node.children ?? [])];
}

function walk(node: MdastNode): void {
  if (node.type === "blockquote") {
    transformBlockquote(node);
    // Do not recurse into a converted callout's title; still walk its body for
    // nested blockquotes.
  }
  if (node.children) {
    for (const child of node.children) walk(child);
  }
}

/** remark plugin: `remarkPlugins={[remarkCallouts]}`. */
export function remarkCallouts() {
  return (tree: MdastNode) => {
    walk(tree);
  };
}
